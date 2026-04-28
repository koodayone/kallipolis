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
    prefix (pure numeric, hyphenated, etc.) pass through unchanged so
    the function is safe to apply to every college's lookup keys.

    Examples:
        "ATHL004"     → "ATHL4"
        "ATHL004A"    → "ATHL4A"
        "CS001A"      → "CS1A"
        "ART003"      → "ART3"
        "PHED010A"    → "PHED10A"
        "ATHL4"       → "ATHL4"      (no zeros to strip)
        "ART3L"       → "ART3L"      (no zeros to strip)
        "055"         → "055"        (no alpha prefix; pass through)
        "ACR-20"      → "ACR-20"     (hyphenated; pass through)
    """
    m = re.match(r"^([A-Z]+)0+(\d+[A-Z]*)$", code)
    return m.group(1) + m.group(2) if m else code


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
    return _strip_numeric_padding(code)


def _normalize_mcf_course_id(course_id: str) -> str:
    """Normalize an MCF course ID into the same canonical key shape
    `_normalize_course_code` produces, so a graph lookup hits the
    indexed MCF row regardless of which college's padding convention
    the row was filed under.
    """
    course_id = course_id.strip().rstrip(".").strip().upper()
    course_id = re.sub(r"\s+", "", course_id)
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

        # Exact match
        top6 = mcf.get((normalized, college_norm))
        if top6:
            out[code] = top6
            continue

        # Prefix fallback (handles catalog "CT100" matching MCF "CT100AB")
        matched: str | None = None
        for mcf_id, mcf_top6 in college_courses:
            if mcf_id.startswith(normalized):
                matched = mcf_top6
                break
        out[code] = matched

    return out
