"""TOP6 code assignment audit across loaded colleges.

Answers six questions per college:

  1. Coverage         — % of courses with `top_code` populated
  2. Expected gap     — how much of the unassigned set is structurally
                        non-credit (0800/0900-series), which legitimately
                        carry no TOP code
  3. Unexpected gap   — courses without TOP6 that don't fit the non-credit
                        pattern. These are the suspicious cases (typically
                        MCF column-name mismatches or catalog code drift).
  4. PREPARES_FOR     — fraction of the college's distinct top_codes that
                        actually produce ≥1 PREPARES_FOR edge. Low
                        coverage signals a broken TOP→CIP→SOC chain
                        (e.g., the TOP6 isn't in the crosswalk, or the
                        target Occupations aren't loaded).
  5. Calibration drop — fraction of calibration TOP6 weight that has no
                        matching course in the catalog (the laketahoe
                        16.9% case). High drop = calibration/catalog
                        mismatch.
  6. MCF column check — verify the College→MCF-key mapping in
                        `_NEO4J_TO_SUPPLY` resolves to a key that exists
                        in the MCF "College" column. Catches the Imperial
                        Valley / LA Valley class of bug at audit time.

Cross-college consistency is reported separately: for each course-code
prefix occurring at ≥3 colleges, the modal top_code should be consistent
across those colleges (within tolerance).

Usage:
    python tools/courses-audit/top_code_audit.py
    python tools/courses-audit/top_code_audit.py --college shasta
    python tools/courses-audit/top_code_audit.py --json   # machine-readable
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

from ontology.supply import _NEO4J_TO_SUPPLY  # noqa: E402
from pipeline.mcf_key_map import _PDF_TO_MCF  # noqa: E402

MCF_DIR = REPO / "backend" / "ontology" / "mastercoursefiles"
CALIBRATION_TOP6_DIR = REPO / "backend" / "ontology" / "calibrations" / "top6"

# Featured colleges + name resolution
COLLEGES = [
    ("shasta", "Shasta College"),
    ("siskiyous", "College of the Siskiyous"),
    ("lassen", "Lassen College"),
    ("mendocino", "Mendocino College"),
    ("butte", "Butte College"),
    ("sacramentocity", "Sacramento City College"),
    ("laketahoe", "Lake Tahoe Community College"),
    ("foothill", "Foothill College"),
    ("berkeleycc", "Berkeley City College"),
    ("napavalley", "Napa Valley College"),
    ("hartnell", "Hartnell College"),
    ("sequoias", "College of the Sequoias"),
    ("merced", "Merced College"),
    ("cerrocoso", "Cerro Coso Community College"),
    ("sbcc", "Santa Barbara City College"),
    ("oxnard", "Oxnard College"),
    ("compton", "Compton College"),
    ("lavalley", "Los Angeles Valley College"),
    ("irvinevalley", "Irvine Valley College"),
    ("desert", "College of the Desert"),
    ("sandiegocity", "San Diego City College"),
    ("imperialvalley", "Imperial Valley College"),
]

# Coverage threshold below which the auditor flags the college.
COVERAGE_FLOOR = 0.85
# Calibration-drop threshold above which the auditor flags the college.
CALIBRATION_DROP_CEILING = 0.05
# PREPARES_FOR coverage threshold (fraction of top_codes that produce ≥1 edge).
PREPARES_FOR_FLOOR = 0.90
# Cross-college consistency threshold for prefix→top_code agreement.
PREFIX_AGREEMENT_FLOOR = 0.70


def cypher(q: str) -> list[dict]:
    """Run a Cypher read-only query against the running Neo4j and parse rows.

    Uses CSV format with Python's csv.reader so empty/null fields parse
    correctly (the previous regex-split approach merged empty fields)."""
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
        if len(fields) == len(header):
            # cypher-shell quirks:
            # - emits the literal string "NULL" for null values
            # - leaves outer double-quotes around string values that csv.reader
            #   doesn't strip (its quoting style isn't standard CSV)
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


def _is_non_credit_code(code: str) -> bool:
    """Heuristic: 0800/0900-series courses are CCC non-credit / community-ed.
    Detects code numeric component starting with 08 or 09."""
    m = re.search(r"\b(\d{3,4})", code)
    if not m:
        return False
    n = m.group(1)
    return n.startswith("8") or n.startswith("9") or n.startswith("08") or n.startswith("09")


def _verify_mcf_column(college: str, college_key: str) -> tuple[bool, str]:
    """Confirm `_NEO4J_TO_SUPPLY[college]` (or its heuristic fallback)
    matches some MCF file's College column.

    The runtime lookup in `mcf_lookup.py` reads all `MasterCourseFile_*.csv`
    files and indexes them by the value of the inner "College" column, so
    filename is not load-bearing — what matters is whether the normalized
    college name appears as a College column value somewhere."""
    expected = _NEO4J_TO_SUPPLY.get(college)
    if expected is None:
        # Heuristic fallback in supply.py
        expected = (
            college.replace(" Community College", "")
            .replace(" College", "")
            .replace("College of the ", "")
            .replace("College of ", "")
            .strip()
        )
    # Scan all MCF files for the expected College column value
    for mcf_path in MCF_DIR.glob("MasterCourseFile_*.csv"):
        try:
            with open(mcf_path) as f:
                reader = csv.reader(f)
                next(reader)  # header
                first_row = next(reader, None)
            if first_row and first_row[0].strip() == expected:
                return (True, "")
        except (StopIteration, OSError):
            continue
    return (False, f"_NEO4J_TO_SUPPLY -> {expected!r} not found in any MCF College column")


def _calibration_drop(key: str, course_top6s: set[str]) -> tuple[float, int]:
    """For a college, what fraction of its TOP6 calibration weight maps to
    TOP6 codes that don't appear in the catalog? Returns (drop_fraction, n_dropped_codes)."""
    p = CALIBRATION_TOP6_DIR / f"{key}.json"
    if not p.exists():
        return (0.0, 0)
    cal = json.loads(p.read_text())
    codes = cal.get("top6_codes", {})
    total_w = sum((c.get("enrollment") or 0) for c in codes.values())
    if total_w == 0:
        return (0.0, 0)
    dropped_w = sum(
        (c.get("enrollment") or 0)
        for code, c in codes.items()
        if code not in course_top6s
    )
    n_dropped = sum(1 for code in codes if code not in course_top6s)
    return (dropped_w / total_w, n_dropped)


def audit_college(key: str, name: str) -> dict:
    """Run all per-college checks. Returns a flat dict of results."""
    out = {"key": key, "name": name, "flags": []}
    rows = cypher(
        f"MATCH (c:Course {{college: '{name}'}}) "
        "RETURN c.code AS code, c.top_code AS top_code"
    )
    total = len(rows)
    out["total_courses"] = total
    if total == 0:
        out["flags"].append("not-loaded")
        return out
    with_top = sum(1 for r in rows if r.get("top_code"))
    coverage = with_top / total
    out["coverage_pct"] = round(100 * coverage, 1)
    out["with_top_code"] = with_top
    out["unmapped_courses"] = total - with_top
    expected_gap = sum(
        1 for r in rows
        if not r.get("top_code") and _is_non_credit_code(r.get("code", ""))
    )
    out["expected_gap"] = expected_gap
    out["unexpected_gap"] = total - with_top - expected_gap

    # Distinct top_codes + PREPARES_FOR linkage
    top6s = {r["top_code"] for r in rows if r.get("top_code")}
    out["distinct_top6s"] = len(top6s)
    pf_rows = cypher(
        f"MATCH (c:Course {{college: '{name}'}}) "
        "WHERE c.top_code IS NOT NULL AND c.top_code <> '' "
        "OPTIONAL MATCH (c)-[r:PREPARES_FOR]->() "
        "WITH c.top_code AS top6, count(r) AS edges "
        "RETURN top6, sum(edges) AS edges"
    )
    pf_by_top = {r["top6"]: int(r["edges"]) for r in pf_rows}
    pf_with_edges = sum(1 for n in pf_by_top.values() if n > 0)
    out["top6s_with_prepares_for"] = pf_with_edges
    out["prepares_for_coverage_pct"] = round(
        100 * pf_with_edges / max(1, len(top6s)), 1
    )

    # Calibration drop
    drop_frac, n_dropped = _calibration_drop(key, top6s)
    out["calibration_drop_pct"] = round(100 * drop_frac, 1)
    out["calibration_dropped_codes"] = n_dropped

    # MCF column check
    ok, msg = _verify_mcf_column(name, key)
    out["mcf_column_ok"] = ok
    out["mcf_column_msg"] = msg

    # Flags
    if coverage < COVERAGE_FLOOR:
        out["flags"].append(f"coverage<{COVERAGE_FLOOR:.0%}")
    if not ok:
        out["flags"].append("mcf-column-mismatch")
    if drop_frac > CALIBRATION_DROP_CEILING:
        out["flags"].append(f"calib-drop>{CALIBRATION_DROP_CEILING:.0%}")
    if len(top6s) and pf_with_edges / len(top6s) < PREPARES_FOR_FLOOR:
        out["flags"].append(f"prepares_for<{PREPARES_FOR_FLOOR:.0%}")

    return out


def cross_college_consistency() -> list[tuple[str, dict[str, int]]]:
    """For each course-code prefix occurring at ≥3 colleges, check the modal
    top_code is consistent. Returns list of (prefix, {top4: count, ...}) for
    flagged inconsistencies (modal share < PREFIX_AGREEMENT_FLOOR)."""
    rows = cypher(
        "MATCH (c:Course) "
        "WHERE c.top_code IS NOT NULL AND c.top_code <> '' "
        "RETURN c.college AS college, c.code AS code, c.top_code AS top_code"
    )
    PREFIX_RE = re.compile(r"^([A-Z][A-Z]{0,7}(?: [A-Z][A-Z]{0,3})?)\s")
    by_prefix: dict[str, dict[str, Counter]] = defaultdict(
        lambda: defaultdict(Counter)
    )
    for r in rows:
        m = PREFIX_RE.match(r["code"])
        if not m:
            continue
        prefix = m.group(1)
        college = r["college"]
        top4 = r["top_code"][:4]
        by_prefix[prefix][college][top4] += 1

    flagged = []
    for prefix, college_to_top4 in by_prefix.items():
        # Take the modal top4 per college, then check cross-college agreement
        if len(college_to_top4) < 3:
            continue
        modal_top4_per_college = {
            college: tc.most_common(1)[0][0]
            for college, tc in college_to_top4.items()
        }
        c = Counter(modal_top4_per_college.values())
        most_common, n = c.most_common(1)[0]
        if n / len(modal_top4_per_college) < PREFIX_AGREEMENT_FLOOR:
            flagged.append((prefix, dict(c)))
    return sorted(flagged, key=lambda x: -sum(x[1].values()))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    ap.add_argument("--college", help="audit just one college key")
    ap.add_argument("--json", action="store_true", help="emit JSON only")
    args = ap.parse_args()

    targets = [(k, n) for k, n in COLLEGES if not args.college or k == args.college]
    if not targets:
        print(f"unknown college key: {args.college}", file=sys.stderr)
        return 2

    results = [audit_college(k, n) for k, n in targets]
    cross = cross_college_consistency() if not args.college else []

    if args.json:
        print(json.dumps({"colleges": results, "cross_college": cross}, indent=2))
        return 0 if all(not r["flags"] for r in results) and not cross else 1

    # Human-readable report
    print(f"{'key':18s} {'cov%':>5s} {'unmap':>5s} {'expGap':>6s} {'unxGap':>6s} "
          f"{'pf%':>5s} {'cdrop%':>6s} {'mcf':>4s}  flags")
    print("-" * 100)
    for r in results:
        flags = " ".join(r["flags"]) if r["flags"] else ""
        print(
            f"{r['key']:18s} {r.get('coverage_pct',0):>5.1f} "
            f"{r.get('unmapped_courses',0):>5d} {r.get('expected_gap',0):>6d} "
            f"{r.get('unexpected_gap',0):>6d} {r.get('prepares_for_coverage_pct',0):>5.1f} "
            f"{r.get('calibration_drop_pct',0):>6.1f} "
            f"{'OK' if r.get('mcf_column_ok') else 'BAD':>4s}  {flags}"
        )
        if not r.get("mcf_column_ok") and r.get("mcf_column_msg"):
            print(f"  {r['key']:18s} ({r['mcf_column_msg']})")

    if cross:
        print(f"\nCross-college prefix→top4 inconsistencies (modal agreement < {PREFIX_AGREEMENT_FLOOR:.0%}):")
        for prefix, dist in cross[:20]:
            print(f"  {prefix:12s} {dist}")

    any_flag = any(r["flags"] for r in results) or bool(cross)
    return 1 if any_flag else 0


if __name__ == "__main__":
    sys.exit(main())
