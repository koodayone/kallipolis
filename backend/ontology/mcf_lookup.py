"""
Per-college course→TOP6 lookup using Master Course Files (MCFs).

The Chancellor's Office assigns a 6-digit TOP code to every course at every
college via the MIS Master Course File submissions. This module loads those
assignments and provides exact TOP6 lookups for specific course codes,
eliminating the fan-out caused by 4-digit TOP code approximation.
"""
from __future__ import annotations

import csv
import re
import logging
from pathlib import Path
from functools import lru_cache

from ontology.supply import _normalize_college

logger = logging.getLogger(__name__)

_MCF_DIR = Path(__file__).parent / "mastercoursefiles"


def _strip_punctuation(code: str) -> str:
    """Strip punctuation that varies arbitrarily across MCF formats and
    catalog-scraper artifacts.

    Three distinct phenomena collapse here:

      1. MCF separator drift: some colleges' MCFs separate the alpha
         prefix from the numeric body with hyphens ("ACR-20", "ENGL-129"),
         others run them together ("ACR1", "ENGL101A"). Within a single
         MCF the convention can be inconsistent (Shasta: "ANTH-5" alongside
         "ANTH10"). Hyphens carry no semantic content — they're a typing
         convention — so stripping them lets one canonical key cover both
         shapes.

      2. Catalog-scrape artifacts: PDF extractors sometimes pick up
         footnote markers ("ENGL C1000*", "MATH 1A†") or trailing dots
         ("MATH 1A.") that aren't part of the course code. The trailing
         dot is already handled by _normalize_mcf_course_id; stripping
         "*" and a few peers here closes the symmetric gap on the
         catalog side.

      3. Cross-listing slashes: catalogs render multi-discipline
         cross-listed courses with an inline slash ("M/LAT 030A",
         "MM/AN 001A", "SOC/ETHS 107"). The corresponding MCF row
         uses a fused prefix with no slash ("MLAT030A", "MMAN001A",
         "SOC107" / "ETHS107"). Stripping the slash lets the catalog's
         shape collapse to whichever fused/single-prefix variant the
         MCF chose. This was 90% of berkeleycc's unmapped courses
         and 31 at sbcc.

      4. Articulation markers: some catalogs append `#` to flag
         courses that articulate to the CSU/UC GE pattern (Shasta's
         "ASL 2#", "ASL 3#"). The `#` is a display flag, not part
         of the course code.

    The character set is intentionally narrow — only punctuation that
    has been observed as either an MCF separator or a scrape artifact.
    Periods are left to the caller's existing rstrip pass; alphanumerics
    and whitespace pass through.
    """
    return re.sub(r"[\-*†§¶/#]", "", code)


def _strip_numeric_padding(code: str) -> str:
    """Strip leading zeros from the numeric portion that follows the
    alphabetic prefix.

    The Master Course File submissions use per-college conventions for
    course-id padding. Foothill's MCF zero-pads the numeric portion to
    three digits ("ATHL004", "ART003L", "PHED010A", "C S 001A"), while
    most peer colleges and the catalog scrapers use the un-padded
    integer form ("ATHL 4", "ART 3L", "PHED 10A", "C S 1A"). Without
    canonicalizing this difference, two-thirds of Foothill's catalog
    courses fail to match their MCF entries — the gap that surfaced as
    32% TOP6 coverage versus peers' 95-99%.

    Strategy: identify the boundary between the alphabetic prefix and
    the first numeric block, strip leading zeros from that block, and
    leave any trailing alpha suffix intact. Codes without an alpha
    prefix (pure numeric, hyphenated remainders, etc.) pass through
    unchanged so the function is safe to apply to every college's
    lookup keys.

    Examples:
        "ATHL004"     → "ATHL4"
        "ATHL004A"    → "ATHL4A"
        "CS001A"      → "CS1A"
        "ART003"      → "ART3"
        "PHED010A"    → "PHED10A"
        "ATHL4"       → "ATHL4"      (no zeros to strip)
        "ART3L"       → "ART3L"      (no zeros to strip)
        "055"         → "055"        (no alpha prefix; pass through)
    """
    m = re.match(r"^([A-Z]+)0+(\d+[A-Z]*)$", code)
    return m.group(1) + m.group(2) if m else code


# English-name-prefix → MCF short-prefix candidates.
#
# Lassen's catalog renders course codes with the full English subject
# name as the prefix ("Administration of Justice 12", "Biology 1",
# "Music 6") while the MCF uses the short alpha prefix ("AJ12", "BIOL1",
# "MUS6"). Without a translation step, every Lassen GE course misses
# its TOP6.
#
# Each entry is a list of plausible short-prefix candidates because the
# MCF convention varies across colleges: some use BIO, others BIOL;
# some COMM, some COMMC for the C-ID-aligned variant. The lookup tries
# each candidate in order and accepts the first MCF hit. If none match,
# the original (whitespace-stripped) form is used and will fall through
# to whatever the rest of the lookup chain produces.
_FULLNAME_TO_SHORT_PREFIXES: dict[str, tuple[str, ...]] = {
    "ADMINISTRATIONOFJUSTICE": ("AJ",),
    "AGRICULTURE":              ("AGR", "AGRI"),
    "ANTHROPOLOGY":             ("ANTH", "ANTHR"),
    "ASTRONOMY":                ("ASTR",),
    "BIOLOGY":                  ("BIOL", "BIO"),
    "CHEMISTRY":                ("CHEM",),
    "CHILDDEVELOPMENT":         ("CD", "CHDEV"),
    "COMMUNICATION":            ("COMM", "COMMC", "SPCH"),
    "ECONOMICS":                ("ECON", "ECONC"),
    "ENGLISH":                  ("ENGL", "ENGLC", "ENG"),
    "ETHNICSTUDIES":            ("ES", "ETHST", "ETHS"),
    "GEOGRAPHY":                ("GEOG",),
    "GEOLOGY":                  ("GEOL",),
    "HISTORY":                  ("HIST", "HISTC"),
    "HUMANITIES":               ("HUM", "HUMAN"),
    "MATHEMATICS":              ("MATH",),
    "MUSIC":                    ("MUS", "MUSIC"),
    "PHILOSOPHY":               ("PHIL",),
    "PHYSICALSCIENCE":          ("PHSC", "PHYSC"),
    "PHYSICS":                  ("PHYS",),
    "POLITICALSCIENCE":         ("POLSC", "PLSC", "POSCI", "POLS"),
    "PSYCHOLOGY":               ("PSY", "PSYC", "PSYCC", "PSYCH"),
    "SOCIOLOGY":                ("SOC", "SOCSC"),
    "SPEECH":                   ("SPCH", "COMM", "COMMC"),
    "STATISTICS":               ("MATH", "STATC"),
}


def _expand_fullname_prefix(code: str) -> tuple[str, ...]:
    """Return short-prefix variants if the (whitespace-stripped) code starts
    with an English subject name; an empty tuple otherwise.

    The catalog form is "Biology 1"; after `re.sub(r"\\s+", "", code)`
    that's "BIOLOGY1". For each known English prefix, build the candidate
    code by replacing the English prefix with each short candidate and
    return the list. The caller (mcf_lookup) tries each candidate against
    its MCF index until one matches.
    """
    upper = code.upper()
    for english, shorts in _FULLNAME_TO_SHORT_PREFIXES.items():
        if upper.startswith(english):
            tail = upper[len(english):]
            return tuple(s + tail for s in shorts)
    return ()


def _normalize_course_code(code: str) -> str:
    """Normalize a course code by stripping internal whitespace, uppercasing,
    and canonicalizing the numeric-padding convention so the catalog scrape
    and the MCF index agree on a single key shape.

    Examples:
        "CT 221"     → "CT221"
        "ARCH 100"   → "ARCH100"
        "ACCT 101A"  → "ACCT101A"
        "D H 063A"   → "DH63A"   (zero-padding stripped)
        "ATHL 4"     → "ATHL4"
        "ATHL 004"   → "ATHL4"   (zero-padding stripped)
    """
    code = code.strip().upper()
    code = re.sub(r"\s+", "", code)
    code = _strip_punctuation(code)
    return _strip_numeric_padding(code)


def _normalize_mcf_course_id(course_id: str) -> str:
    """Normalize an MCF course ID into the same canonical key shape
    `_normalize_course_code` produces, so a graph lookup hits the
    indexed MCF row regardless of which college's padding convention
    the row was filed under.
    """
    course_id = course_id.strip().rstrip(".").strip().upper()
    course_id = re.sub(r"\s+", "", course_id)
    course_id = _strip_punctuation(course_id)
    return _strip_numeric_padding(course_id)


@lru_cache(maxsize=1)
def _load_mcf_index() -> dict[tuple[str, str], str]:
    """Load all MCFs into an index: (normalized_course_id, college_lower) → top6.

    For duplicate entries (same course, same college, different TOP codes),
    the last entry wins. MCFs are authoritative per-college assignments.
    """
    index: dict[tuple[str, str], str] = {}
    files = sorted(_MCF_DIR.glob("MasterCourseFile_*.csv"))

    if not files:
        logger.warning(f"No MasterCourseFile_*.csv found in {_MCF_DIR}")
        return index

    for f in files:
        try:
            with open(f, encoding="utf-8", errors="replace") as fh:
                reader = csv.DictReader(fh)
                for row in reader:
                    college = row.get("College", "").strip().lower()
                    course_id = row.get("Course ID", "")
                    top_code = row.get("TOP Code", "").strip()

                    if not college or not course_id or not top_code:
                        continue

                    normalized = _normalize_mcf_course_id(course_id)
                    if not normalized:
                        continue

                    # Ensure TOP code is 6 digits
                    if len(top_code) == 6:
                        index[(normalized, college)] = top_code
                    elif len(top_code) == 4:
                        index[(normalized, college)] = top_code + "00"
        except Exception as e:
            logger.warning(f"Error reading {f.name}: {e}")

    logger.info(f"Loaded MCF index: {len(index)} (course, college) entries from {len(files)} files")
    return index


@lru_cache(maxsize=1)
def _build_prefix_scan_index() -> dict[str, list[tuple[str, str]]]:
    """Build a reverse index for prefix matching: college_lower → list of (normalized_course_id, top6).

    Used as fallback when exact match fails (e.g., Neo4j has "CT 100" but MCF has "CT100AB").
    """
    mcf = _load_mcf_index()
    by_college: dict[str, list[tuple[str, str]]] = {}
    for (course_id, college), top6 in mcf.items():
        if college not in by_college:
            by_college[college] = []
        by_college[college].append((course_id, top6))
    return by_college


# Alternate alpha-prefix variants: when the catalog uses one prefix
# (PSY, COMM) but the MCF stores the same subject under a related
# variant (PSYC/PSYCC, COMMC), the lookup should try the alternates
# before giving up. Mapping is symmetric — the lookup attempts each
# alternate in order and accepts the first MCF hit.
_ALTERNATE_PREFIX_VARIANTS: dict[str, tuple[str, ...]] = {
    "PSY":   ("PSYC", "PSYCC", "PSYCH"),
    "PSYC":  ("PSY", "PSYCC", "PSYCH"),
    "PSYCH": ("PSYCC", "PSYC", "PSY"),
    "COMM":  ("COMMC", "SPCH"),
    "COMMC": ("COMM", "SPCH"),
    "SPCH":  ("COMM", "COMMC"),
    "ECON":  ("ECONC",),
    "ECONC": ("ECON",),
    "ENGL":  ("ENGLC", "ENG"),
    "ENGLC": ("ENGL", "ENG"),
    "HIST":  ("HISTC",),
    "HISTC": ("HIST",),
    "MATH":  ("MATHC", "STATC"),
    "STAT":  ("STATC", "MATH"),
    "POLS":  ("POLSC", "POSCI", "PLSC"),
    "POLSC": ("POLS", "POSCI", "PLSC"),
    "BIO":   ("BIOL",),
    "BIOL":  ("BIO",),
    "CS":    ("COMSC", "CIS"),
    "ART":   ("ARTHC", "ARTNC"),
    "MUS":   ("MUSIC", "MUSNC"),
}


def _alternate_prefix_candidates(normalized: str) -> tuple[str, ...]:
    """Build candidate codes by swapping the alpha prefix for each known
    alternate. Returns empty if the prefix has no registered alternates."""
    m = re.match(r"^([A-Z]+)(\d.*)$", normalized)
    if not m:
        return ()
    prefix, rest = m.group(1), m.group(2)
    alts = _ALTERNATE_PREFIX_VARIANTS.get(prefix, ())
    return tuple(alt + rest for alt in alts)


def _slash_split_candidates(raw_code: str) -> tuple[str, ...]:
    """For an "X/Y N" cross-listed catalog code, return the per-prefix
    candidates ("XN", "YN") in normalized form.

    Two MCF conventions exist for cross-listings:

      - Fused prefix: berkeley city files "M/LAT 030A" as "MLAT030A".
        The slash-strip in `_strip_punctuation` produces this form
        directly, so the exact-match lookup already handles it.
      - Per-prefix: santa barbara files "SOC/ETHS 107" as TWO rows:
        one under "SOC107" and one under "ETHS107", with the same
        TOP code. The fused form "SOCETHS107" is absent. The
        per-prefix candidates from this helper close that gap.

    Returns an empty tuple if the raw code has no slash.
    """
    m = re.match(r"^([A-Z]+)/([A-Z]+)\s*(\d+[A-Z]*)$", raw_code.upper().strip())
    if not m:
        return ()
    a, b, num = m.group(1), m.group(2), m.group(3)
    return (
        _strip_numeric_padding(a + num),
        _strip_numeric_padding(b + num),
    )


def _decimal_suffix_parent(normalized: str) -> str | None:
    """If the normalized code carries a decimal sub-numbering (Lassen's
    "FS60.1" Cal Fire modules, "PEAC5A.02" athletic-team sections),
    return the parent code without the decimal suffix; None otherwise.

    The decimal in these catalogs marks a section/module of the parent
    course, which is what carries the institutional TOP code in the MCF.
    """
    m = re.match(r"^([A-Z]+\d+[A-Z]*)\.\d+", normalized)
    return m.group(1) if m else None


def lookup_top6(course_codes: list[str], college: str) -> set[str]:
    """Look up exact TOP6 codes for a list of course codes at a specific college.

    Returns deduplicated set of TOP6 codes found in the MCF.
    """
    return {t for t in lookup_top6_per_course(course_codes, college).values() if t}


def lookup_top6_per_course(
    course_codes: list[str], college: str
) -> dict[str, str | None]:
    """Look up TOP6 codes per course code at a specific college.

    Per-course variant of lookup_top6. Used by the loader to set the
    Course.top_code property and (downstream) materialize PREPARES_FOR
    edges from each course to the occupations its TOP6 crosswalks to.

    Returns: {course_code: top6 or None} for every input code. None
    indicates the MCF has no row for that course at that college, which
    is normal for non-credit / general-education entries that fall outside
    the institutional CTE catalog.
    """
    mcf = _load_mcf_index()
    college_norm = _normalize_college(college).lower()
    prefix_index = _build_prefix_scan_index()
    college_courses = prefix_index.get(college_norm, [])

    out: dict[str, str | None] = {}
    for code in course_codes:
        normalized = _normalize_course_code(code)
        if not normalized:
            out[code] = None
            continue

        # 1. Exact match
        top6 = mcf.get((normalized, college_norm))
        if top6:
            out[code] = top6
            continue

        # 1b. Slash-split fallback for catalogs that file cross-listed
        # courses under each prefix separately ("SOC/ETHS 107" → both
        # "SOC107" and "ETHS107" are MCF rows; the slash-strip already
        # handled the fused-form variant in step 1).
        hit: str | None = None
        for cand in _slash_split_candidates(code):
            t = mcf.get((cand, college_norm))
            if t:
                hit = t
                break
        if hit:
            out[code] = hit
            continue

        # 2. Fullname-prefix fallback. Lassen's catalog renders codes as
        # "Biology 1"; whitespace-strip yields "BIOLOGY1". Translate the
        # English subject prefix to MCF short-prefix candidates and try
        # each. Each candidate is re-normalized (zero-padding pass) so
        # "MUSIC6" → "MUS6" matches MCF entries.
        hit = None
        for cand in _expand_fullname_prefix(re.sub(r"\s+", "", code.upper())):
            cand_norm = _strip_numeric_padding(_strip_punctuation(cand))
            t = mcf.get((cand_norm, college_norm))
            if t:
                hit = t
                break
        if hit:
            out[code] = hit
            continue

        # 3. Alternate-prefix fallback. Catalog has "PSY 18" but Lassen's
        # MCF files it as "PSYC18"; swap the alpha prefix and retry.
        hit = None
        for cand in _alternate_prefix_candidates(normalized):
            t = mcf.get((cand, college_norm))
            if t:
                hit = t
                break
        if hit:
            out[code] = hit
            continue

        # 4. Decimal-suffix parent fallback. "FS 60.1" → look up "FS60";
        # the parent course in the MCF carries the institutional TOP6.
        parent = _decimal_suffix_parent(normalized)
        if parent:
            t = mcf.get((parent, college_norm))
            if t:
                out[code] = t
                continue

        # 5. Prefix-startswith fallback (catalog "CT100" → MCF "CT100AB").
        matched: str | None = None
        for mcf_id, mcf_top6 in college_courses:
            if mcf_id.startswith(normalized):
                matched = mcf_top6
                break
        out[code] = matched

    return out
