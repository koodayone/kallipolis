"""Grounded classification for courses without TOP6 codes.

For every unmapped Course node at a college, look up the corresponding MCF
file and classify with evidence. The output is defensible per row, and
aggregates into hard counts per category.

Categories (mutually exclusive, evaluated in order):

  EXACT_MATCH_BUG
    The normalized course code IS present in the college's MCF. The current
    `lookup_top6_per_course` should have found it. If this is non-empty,
    something in the normalization or lookup path is broken.

  HONORS_VARIANT
    The code has a trailing "H" (honors) or "X" (experimental) suffix. The
    same code without the suffix IS in the MCF. The honors offering shares
    the parent course's TOP6.

  ALTERNATE_PREFIX
    The catalog uses one prefix variant (PSY, COMM) but the MCF stores
    the same course under a related variant (PSYC/PSYCC, COMMC). A
    candidate built from the alternate prefix matches an MCF entry.

  DECIMAL_SUFFIX_PARENT
    The catalog uses a decimal sub-numbering scheme for course modules
    or sections ("FS 60.1", "PEAC 5A.02"). The parent course (without
    the decimal) IS in the MCF and carries the institutional TOP code.

  FULLNAME_PREFIX
    The catalog code uses an English-name prefix ("Biology 10", "Music 6")
    rather than the MCF's short-prefix ("BIOL 10", "MUS 6"). The numeric
    body matches an entry under a known short-prefix in the same MCF.
    This is a Lassen-style scrape gap.

  MULTI_PREFIX_CROSS_LISTED
    The code uses an "X/Y" double-prefix pattern (M/LAT, MM/AN, SOC/ETHS).
    The MCF stores it as a fused prefix (MLAT, MMAN). The numeric body
    matches an entry under that fused prefix.

  EXTRACTION_ARTIFACT_NO_PREFIX
    The code is purely numeric ("104"), just a prefix with no number
    ("THEA"), or contains scrape garbage ("????", "C1000m"). No real
    course code shape — the catalog scraper picked up program/certificate
    listings or fragments.

  EXTRACTION_ARTIFACT_DEGREE_NAME
    The "course" name contains program-level vocabulary ("Certificate of
    Completion", "Associate in Arts", "AA-T", "Skills Competency Award",
    "Department Award"). The row is a credential listing, not a course.

  TRANSFER_CID
    The code matches CSU/UC C-ID transfer-course pattern (e.g., "C1000",
    "PSY C1000H"). C-IDs are inter-segmental aliases, not local MCF codes.

  NON_CCC_PREFIX
    The prefix doesn't exist in any California Community College MCF
    (e.g., "UNR ENG" for Univ. of Nevada-Reno cross-enrollment). The
    course is legitimately not classifiable via CCC TOP codes.

  PREFIX_NOT_IN_COLLEGE_MCF
    The prefix exists in some CCC's MCF but not this college's. Possible
    cross-listed transfer offering or a recent program addition.

  MCF_GAP_PREFIX_KNOWN
    The prefix IS in this college's MCF, but the specific (prefix, num)
    pair is not. Two underlying causes mix here without further evidence:
    (a) MCF lag — the catalog has a real course (often a transferable GE)
    that the college hasn't submitted to MIS yet, or the MCF dataset
    pre-dates a renumbering; (b) Catalog credential extraction — the PDF
    scraper picked up a programs/credentials table whose rows carry
    sequential IDs that look like course codes under the issuing
    department's prefix (SBCC's ACCT 101–117, BUS 104–118 patterns).
    Drill in with `--show MCF_GAP_PREFIX_KNOWN` to inspect.

  UNCLASSIFIED
    None of the above patterns match. Inspect manually.

Usage:
    python tools/courses-audit/classify_unmapped.py --college sbcc
    python tools/courses-audit/classify_unmapped.py --college sbcc --json
    python tools/courses-audit/classify_unmapped.py --college sbcc --show UNCLASSIFIED
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO / "backend"))

from courses.extraction_filter import (  # noqa: E402
    DEGREE_NAME_MARKERS,
    NON_CCC_PREFIX_PATTERNS,
)
from ontology.mcf_lookup import (  # noqa: E402
    _normalize_course_code,
    _normalize_mcf_course_id,
)
from ontology.supply import _NEO4J_TO_SUPPLY  # noqa: E402

MCF_DIR = REPO / "backend" / "ontology" / "mastercoursefiles"

# Resolve audit-key (e.g. "sbcc") → Neo4j name (e.g. "Santa Barbara City College")
COLLEGE_KEY_TO_NAME = {
    "shasta": "Shasta College",
    "siskiyous": "College of the Siskiyous",
    "lassen": "Lassen College",
    "mendocino": "Mendocino College",
    "butte": "Butte College",
    "sacramentocity": "Sacramento City College",
    "laketahoe": "Lake Tahoe Community College",
    "foothill": "Foothill College",
    "berkeleycc": "Berkeley City College",
    "napavalley": "Napa Valley College",
    "hartnell": "Hartnell College",
    "sequoias": "College of the Sequoias",
    "merced": "Merced College",
    "cerrocoso": "Cerro Coso Community College",
    "sbcc": "Santa Barbara City College",
    "oxnard": "Oxnard College",
    "compton": "Compton College",
    "lavalley": "Los Angeles Valley College",
    "irvinevalley": "Irvine Valley College",
    "desert": "College of the Desert",
    "sandiegocity": "San Diego City College",
    "imperialvalley": "Imperial Valley College",
}

# Degree-name and non-CCC-prefix patterns are imported from the shared
# `courses.extraction_filter` module so filter-time and audit-time stay
# in sync — adding a new credential marker once propagates to both.

# C-ID (intersegmental transfer course IDs) take the shape "C1000",
# optionally with a trailing letter for honors variants. They appear
# either alone ("C1000") or after an English prefix ("Communication C1000").
CID_PATTERN = re.compile(r"\bC\d{4}[A-Z]?\b", re.IGNORECASE)

# An English-name prefix: capitalized word(s) followed by a number,
# e.g. "Administration of Justice 12", "Music 6", "Physical Science 1".
FULLNAME_PREFIX_RE = re.compile(
    r"^([A-Z][a-z]+(?: [A-Za-z][a-z]*)*)\s+(\d+[A-Z\.\d]*)$"
)


def cypher(q: str) -> list[dict]:
    """Run Cypher against the running Neo4j; mirror top_code_audit's parser."""
    r = subprocess.run(
        ["docker", "exec", "kallipolis-neo4j-1", "cypher-shell",
         "-u", "neo4j", "-p", "kallipolis_dev", "--format", "plain", q],
        capture_output=True, text=True, timeout=60,
    )
    if r.returncode != 0:
        raise RuntimeError(f"cypher failed: {r.stderr.strip()[:200]}")
    import io
    reader = csv.reader(io.StringIO(r.stdout))
    try:
        header = [h.strip() for h in next(reader)]
    except StopIteration:
        return []
    rows = []
    for fields in reader:
        if len(fields) != len(header):
            continue
        row = {}
        for h, f in zip(header, fields):
            v = f.strip()
            if v == "NULL":
                v = ""
            elif len(v) >= 2 and v[0] == '"' and v[-1] == '"':
                v = v[1:-1]
            row[h] = v
        rows.append(row)
    return rows


def cypher_delim(q: str, fields: list[str], delim: str = "|||") -> list[dict]:
    """Run a Cypher query that returns ONE column built by concatenating the
    requested fields with `delim`, then split locally. Avoids cypher-shell's
    non-standard CSV quoting which drops rows whose string values contain
    commas."""
    # Caller is responsible for building the RETURN clause to use the delim
    r = subprocess.run(
        ["docker", "exec", "kallipolis-neo4j-1", "cypher-shell",
         "-u", "neo4j", "-p", "kallipolis_dev", "--format", "plain", q],
        capture_output=True, text=True, timeout=60,
    )
    if r.returncode != 0:
        raise RuntimeError(f"cypher failed: {r.stderr.strip()[:200]}")
    out: list[dict] = []
    lines = r.stdout.splitlines()
    if not lines:
        return out
    # Skip header line (single column, e.g. "line")
    for line in lines[1:]:
        s = line.strip()
        if not s or s == "NULL":
            continue
        # Strip outer quotes left by cypher-shell
        if len(s) >= 2 and s[0] == '"' and s[-1] == '"':
            s = s[1:-1]
        parts = s.split(delim)
        if len(parts) != len(fields):
            continue
        out.append({f: p for f, p in zip(fields, parts)})
    return out


def load_college_mcf(college_lower: str) -> tuple[set[str], set[str]]:
    """Return (set of normalized course IDs, set of distinct prefixes) for one
    college's MCF rows. Reads every MCF file in the directory, since filename
    isn't load-bearing — the College column is."""
    code_set: set[str] = set()
    prefix_set: set[str] = set()
    for f in MCF_DIR.glob("MasterCourseFile_*.csv"):
        with open(f, encoding="utf-8", errors="replace") as fh:
            for row in csv.DictReader(fh):
                if row.get("College", "").strip().lower() != college_lower:
                    continue
                cid = row.get("Course ID", "").strip()
                if not cid:
                    continue
                norm = _normalize_mcf_course_id(cid)
                code_set.add(norm)
                m = re.match(r"^([A-Z][A-Z]*)", norm)
                if m:
                    prefix_set.add(m.group(1))
    return code_set, prefix_set


def load_global_prefix_set() -> set[str]:
    """All prefixes appearing in any CCC MCF. Used to detect non-CCC codes."""
    prefixes: set[str] = set()
    for f in MCF_DIR.glob("MasterCourseFile_*.csv"):
        with open(f, encoding="utf-8", errors="replace") as fh:
            for row in csv.DictReader(fh):
                cid = row.get("Course ID", "").strip()
                if not cid:
                    continue
                norm = _normalize_mcf_course_id(cid)
                m = re.match(r"^([A-Z][A-Z]*)", norm)
                if m:
                    prefixes.add(m.group(1))
    return prefixes


def normalize_college_for_mcf(neo4j_name: str) -> str:
    """Replicate the runtime college-name normalization used at lookup time."""
    short = _NEO4J_TO_SUPPLY.get(neo4j_name)
    if short is None:
        short = (
            neo4j_name
            .replace(" Community College", "")
            .replace(" College", "")
            .replace("College of the ", "")
            .replace("College of ", "")
            .strip()
        )
    return short.lower()


# Alternate short-prefix variants. The MCF sometimes uses two different
# alpha prefixes for the same subject area (Lassen has both PSY and PSYC;
# Berkeley City has both COMM and COMMC where the C-suffix denotes the
# C-ID-aligned variant). When the catalog code's prefix doesn't match,
# fall back through these alternates.
ALTERNATE_PREFIX_MAP = {
    "PSY":   ["PSYC", "PSYCC", "PSYCH"],
    "PSYC":  ["PSY", "PSYCC", "PSYCH"],
    "COMM":  ["COMMC", "SPCH"],
    "ECON":  ["ECONC"],
    "ENGL":  ["ENGLC", "ENG"],
    "HIST":  ["HISTC"],
    "MATH":  ["MATHC", "STATC"],
    "PSYCH": ["PSYCC", "PSYC", "PSY"],
    "STAT":  ["STATC", "MATH"],
    "SPCH":  ["COMM", "COMMC"],
    "POLS":  ["POLSC", "POSCI", "PLSC"],
    "BIO":   ["BIOL"],
    "BIOL":  ["BIO"],
    "CS":    ["COMSC", "CIS"],
    "ART":   ["ARTHC", "ARTNC"],
    "MUS":   ["MUSIC", "MUSNC"],
    "ESL":   ["ESL NC", "ESLNC"],
}

# Mapping from English-name prefix to plausible MCF short-prefix variants.
# Built from the Lassen unmapped data + the MCF prefix list. We only assert
# a match if the resulting (short_prefix + numeric_body) is in the MCF.
ENGLISH_TO_SHORT = {
    "Administration of Justice": ["AJ"],
    "Agriculture":                ["AGR", "AGRI"],
    "Anthropology":               ["ANTH", "ANTHR"],
    "Astronomy":                  ["ASTR"],
    "Biology":                    ["BIOL", "BIO"],
    "Chemistry":                  ["CHEM"],
    "Child Development":          ["CD", "CHDEV"],
    "Communication":              ["COMM", "COMMC", "SPCH"],
    "Economics":                  ["ECON", "ECONC"],
    "English":                    ["ENGL", "ENGLC", "ENG"],
    "Ethnic Studies":             ["ES", "ETHST", "ETHS"],
    "Geography":                  ["GEOG"],
    "Geology":                    ["GEOL"],
    "History":                    ["HIST", "HISTC"],
    "Humanities":                 ["HUM", "HUMAN"],
    "Mathematics":                ["MATH"],
    "Music":                      ["MUS", "MUSIC"],
    "Philosophy":                 ["PHIL"],
    "Physical Science":           ["PHSC", "PHYSC"],
    "Physics":                    ["PHYS"],
    "Political Science":          ["POLSC", "PLSC", "POSCI", "POLS"],
    "Psychology":                 ["PSY", "PSYC", "PSYCC", "PSYCH"],
    "Sociology":                  ["SOC", "SOCSC"],
    "Speech":                     ["SPCH", "COMM", "COMMC"],
    "Statistics":                 ["MATH", "STATC"],
}


def classify(
    code: str,
    name: str,
    college_codes: set[str],
    college_prefixes: set[str],
    global_prefixes: set[str],
) -> tuple[str, str]:
    """Classify one unmapped course. Returns (category, evidence)."""
    raw = code.strip()

    # ── 0a. Extraction-artifact: clearly broken shapes ─────────────────
    # Pure numeric codes (no prefix at all)
    if re.fullmatch(r"\d{2,4}", raw):
        return ("EXTRACTION_ARTIFACT_NO_PREFIX",
                f"pure-numeric code {raw!r} has no prefix")
    # Prefix-only codes (no number)
    if re.fullmatch(r"[A-Z]{2,8}", raw):
        return ("EXTRACTION_ARTIFACT_NO_PREFIX",
                f"prefix-only code {raw!r} (no number)")
    # Codes with literal '?' question marks (scrape garbage)
    if "?" in raw:
        return ("EXTRACTION_ARTIFACT_NO_PREFIX",
                f"contains '?' — scrape garbage")

    # ── 1. Extraction-artifact: name is a degree/credential listing ───
    for marker in DEGREE_NAME_MARKERS:
        if marker in name:
            return ("EXTRACTION_ARTIFACT_DEGREE_NAME",
                    f"name contains {marker!r}")

    # ── 2. Non-CCC prefix (UNR, CSU, UC) ──────────────────────────────
    for pat in NON_CCC_PREFIX_PATTERNS:
        if pat.match(raw):
            return ("NON_CCC_PREFIX",
                    f"matches non-CCC pattern {pat.pattern}")

    # ── 3. C-ID transfer code ──────────────────────────────────────────
    # Either the code IS just a C-ID, or starts with one as the alpha part
    if CID_PATTERN.fullmatch(raw):
        return ("TRANSFER_CID", f"matches C-ID pattern (full)")
    # English-prefix + C-ID, e.g. "Communication C1000"
    m = re.fullmatch(r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+C\d{4}[A-Z]?", raw)
    if m:
        return ("TRANSFER_CID", f"english-prefix + C-ID ({raw!r})")

    # ── 4. Exact match in MCF (lookup-logic bug) ──────────────────────
    norm = _normalize_course_code(raw)
    if norm in college_codes:
        return ("EXACT_MATCH_BUG",
                f"{raw!r} normalizes to {norm!r}, present in MCF")

    # ── 5. Honors variant ──────────────────────────────────────────────
    # Trailing H stripped; check parent code
    if re.search(r"H$", norm):
        parent = norm[:-1]
        if parent in college_codes:
            return ("HONORS_VARIANT",
                    f"{raw!r} → strip trailing H → {parent!r} in MCF")

    # ── 5b. Alternate-prefix variant (PSY ↔ PSYC, COMM ↔ COMMC) ───────
    m = re.match(r"^([A-Z]+)(\d.*)$", norm)
    if m:
        prefix, rest = m.group(1), m.group(2)
        for alt in ALTERNATE_PREFIX_MAP.get(prefix, []):
            cand = alt + rest
            if cand in college_codes:
                return ("ALTERNATE_PREFIX",
                        f"{raw!r} → {prefix!r}→{alt!r}; "
                        f"{cand!r} in MCF")

    # ── 5c. Decimal-suffix → parent course ─────────────────────────────
    # FS 60.1, FS 98.18 → FS60, FS98 (parent course in MCF). The decimal
    # suffix in lassen's catalog is a sub-numbering scheme for course
    # modules / sections; the parent carries the institutional TOP code.
    m = re.match(r"^([A-Z]+\d+)\.\d+", norm)
    if m:
        parent = m.group(1)
        if parent in college_codes:
            return ("DECIMAL_SUFFIX_PARENT",
                    f"{raw!r} → strip decimal suffix → {parent!r} in MCF")

    # ── 6. Multi-prefix cross-listing (e.g. "M/LAT 030A" → "MLAT30A") ──
    # The catalog uses an "X/Y NUM" form for cross-listed courses;
    # the MCF stores them under a fused prefix (X+Y). Normalize the
    # FULL candidate code (so leading-zero stripping applies to the
    # numeric body).
    m = re.match(r"^([A-Z]+)/([A-Z]+)\s*(\d+[A-Z]*)$", raw)
    if m:
        a, b, num = m.group(1), m.group(2), m.group(3)
        for combo in (a + b, a, b):
            cand = _normalize_course_code(f"{combo} {num}")
            if cand in college_codes:
                return ("MULTI_PREFIX_CROSS_LISTED",
                        f"{raw!r} → {cand!r} in MCF (fused prefix {combo!r})")
        # No exact match. Report based on what's in the MCF.
        fused = a + b
        if fused in college_prefixes:
            return ("MULTI_PREFIX_CROSS_LISTED",
                    f"{raw!r} fused prefix {fused!r} in MCF, "
                    f"but normalized {cand!r} not present (MCF gap)")
        if a in college_prefixes or b in college_prefixes:
            return ("MULTI_PREFIX_CROSS_LISTED",
                    f"{raw!r} double-prefix; one of {a},{b} is in MCF "
                    f"but no fused-form ({fused!r}) match")
        return ("MULTI_PREFIX_CROSS_LISTED",
                f"{raw!r} double-prefix; "
                f"neither {a},{b}, nor {fused!r} in MCF prefixes")

    # ── 7. English-name-prefix variant (Lassen pattern) ────────────────
    # Must come before the "lowercase fragment" garbage check, since
    # English-name prefixes legitimately contain lowercase letters.
    m = FULLNAME_PREFIX_RE.match(raw)
    if m:
        english, num = m.group(1), m.group(2)
        candidates = ENGLISH_TO_SHORT.get(english, [])
        for short in candidates:
            cand = short + _normalize_course_code(num)
            if cand in college_codes:
                return ("FULLNAME_PREFIX",
                        f"{english!r} → {short!r}; "
                        f"{raw!r} → {cand!r} in MCF")
        # No mapping or no match — but it IS a fullname-prefix shape
        return ("FULLNAME_PREFIX",
                f"{english!r} fullname-prefix; "
                f"no MCF match across {candidates or ['<no mapping>']}")

    # ── 7b. Mid-code lowercase fragment (scrape garbage) ───────────────
    # Catches "PSYC C1000mtroduction" — fullname-prefix already excluded.
    if re.search(r"[a-z]{3,}", raw):
        return ("EXTRACTION_ARTIFACT_NO_PREFIX",
                f"lowercase fragment in code: {raw!r}")

    # ── 8. Course prefix exists somewhere, but not at this college ────
    m = re.match(r"^([A-Z][A-Z]*)", norm)
    if m:
        prefix = m.group(1)
        if prefix not in college_prefixes:
            if prefix in global_prefixes:
                return ("PREFIX_NOT_IN_COLLEGE_MCF",
                        f"prefix {prefix!r} not in this college's MCF "
                        f"(but exists in some CCC MCF)")
            else:
                return ("NON_CCC_PREFIX",
                        f"prefix {prefix!r} not in any CCC MCF")

        # Prefix IS in college MCF, but exact code is not. Two
        # underlying causes mix here:
        #
        #   (a) MCF lag — the catalog has a real course (often a
        #       transferable GE course like ENGL 001A or HIST 007A)
        #       that the college simply hasn't submitted to MIS yet,
        #       or the MCF dataset on disk pre-dates a renumbering.
        #   (b) Catalog credential extraction — the PDF scraper
        #       picked up a programs/credentials table whose rows
        #       carry sequential IDs that look like course codes
        #       under the issuing department's prefix (SBCC's
        #       ACCT 101–117 pattern, with names like "Accounting
        #       Basics for Small Business" or "Advanced Green
        #       Gardener" mis-attributed to ACCT).
        #
        # Distinguishing (a) from (b) deterministically requires
        # cross-referencing the catalog source PDF / enriched.json
        # with the MCF rows. That's a follow-up step. For now,
        # report this as a single category that the operator can
        # drill into per-college with --show.
        return ("MCF_GAP_PREFIX_KNOWN",
                f"prefix {prefix!r} in MCF but {norm!r} not present")

    # ── 9. Fallthrough ─────────────────────────────────────────────────
    return ("UNCLASSIFIED", f"{raw!r} → norm {norm!r}; needs manual review")


def fetch_unmapped(neo4j_name: str) -> list[tuple[str, str]]:
    """Pull (code, name) using a delimiter-joined column to avoid cypher-shell
    CSV quoting bugs that drop rows whose name field contains commas."""
    rows = cypher_delim(
        f"MATCH (c:Course {{college: '{neo4j_name}'}}) "
        "WHERE c.top_code IS NULL OR c.top_code = '' "
        "RETURN c.code + '|||' + coalesce(c.name, '') AS line "
        "ORDER BY c.code",
        fields=["code", "name"],
    )
    return [(r["code"], r["name"]) for r in rows]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    ap.add_argument("--college", required=True,
                    help="audit key (e.g., sbcc, lassen, berkeleycc)")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--show", help="show all rows in this category")
    args = ap.parse_args()

    if args.college not in COLLEGE_KEY_TO_NAME:
        print(f"unknown college key: {args.college}", file=sys.stderr)
        return 2
    neo4j_name = COLLEGE_KEY_TO_NAME[args.college]

    college_lower = normalize_college_for_mcf(neo4j_name)
    college_codes, college_prefixes = load_college_mcf(college_lower)
    global_prefixes = load_global_prefix_set()

    unmapped = fetch_unmapped(neo4j_name)

    classifications: list[dict] = []
    counts: Counter = Counter()
    examples: dict[str, list[str]] = defaultdict(list)
    for code, name in unmapped:
        cat, ev = classify(
            code, name, college_codes, college_prefixes, global_prefixes
        )
        classifications.append({
            "code": code,
            "name": name,
            "category": cat,
            "evidence": ev,
        })
        counts[cat] += 1
        if len(examples[cat]) < 3:
            examples[cat].append(f"{code!r} → {ev}")

    if args.json:
        print(json.dumps({
            "college": args.college,
            "neo4j_name": neo4j_name,
            "mcf_college_lower": college_lower,
            "total_unmapped": len(unmapped),
            "counts": dict(counts),
            "rows": classifications,
        }, indent=2))
        return 0

    if args.show:
        for r in classifications:
            if r["category"] == args.show:
                print(f"  {r['code']:30s}  {r['evidence']}")
                print(f"    name: {r['name']!r}")
        return 0

    print(f"=== {args.college} ({neo4j_name}) — {len(unmapped)} unmapped ===")
    print(f"MCF college key: {college_lower!r}")
    print(f"MCF: {len(college_codes)} courses across {len(college_prefixes)} prefixes")
    print()
    print(f"  {'category':35s} {'count':>5s}  examples")
    print("-" * 100)
    # Three buckets, plus an UNCLASSIFIED catch-all if the classifier
    # rules ever miss a row.
    fixable_cats = {
        "EXACT_MATCH_BUG", "HONORS_VARIANT", "ALTERNATE_PREFIX",
        "DECIMAL_SUFFIX_PARENT", "FULLNAME_PREFIX",
        "MULTI_PREFIX_CROSS_LISTED",
    }
    not_classifiable_cats = {
        "EXTRACTION_ARTIFACT_NO_PREFIX", "EXTRACTION_ARTIFACT_DEGREE_NAME",
        "TRANSFER_CID", "NON_CCC_PREFIX", "PREFIX_NOT_IN_COLLEGE_MCF",
    }
    mixed_cats = {"MCF_GAP_PREFIX_KNOWN"}

    fixable_total = sum(counts[c] for c in fixable_cats)
    not_classifiable_total = sum(counts[c] for c in not_classifiable_cats)
    mixed_total = sum(counts[c] for c in mixed_cats)
    unclassified_total = counts.get("UNCLASSIFIED", 0)

    print("FIXABLE — clear path to a TOP6 (lookup logic / normalization):")
    for cat in sorted(fixable_cats, key=lambda c: -counts[c]):
        if counts[cat]:
            ex = examples[cat][0] if examples[cat] else ""
            print(f"  {cat:35s} {counts[cat]:>5d}  {ex[:60]}")
    print(f"  {'subtotal':35s} {fixable_total:>5d}")
    print()

    print("NOT CCC-CLASSIFIABLE (legitimate, not a fix target):")
    for cat in sorted(not_classifiable_cats, key=lambda c: -counts[c]):
        if counts[cat]:
            ex = examples[cat][0] if examples[cat] else ""
            print(f"  {cat:35s} {counts[cat]:>5d}  {ex[:60]}")
    print(f"  {'subtotal':35s} {not_classifiable_total:>5d}")
    print()

    if mixed_total:
        print("MCF GAP, prefix in MCF but code missing — mix of two causes:")
        print("  (a) MCF lag (real course not yet submitted to MIS), or")
        print("  (b) catalog scraper extracted a credentials table as courses")
        for cat in mixed_cats:
            if counts[cat]:
                ex = examples[cat][0] if examples[cat] else ""
                print(f"  {cat:35s} {counts[cat]:>5d}  {ex[:60]}")
        print(f"  {'subtotal':35s} {mixed_total:>5d}")
        print(f"  (drill in with: --show MCF_GAP_PREFIX_KNOWN)")
        print()

    if unclassified_total:
        print("UNCLASSIFIED (manual review):")
        print(f"  {'UNCLASSIFIED':35s} {unclassified_total:>5d}")
        for ex in examples.get("UNCLASSIFIED", [])[:5]:
            print(f"      {ex}")
        print()

    print(f"  {'TOTAL':35s} {len(unmapped):>5d}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
