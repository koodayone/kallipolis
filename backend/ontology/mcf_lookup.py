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

from pipeline.industry.coe_supply import _normalize_college

logger = logging.getLogger(__name__)

_MCF_DIR = Path(__file__).parent / "mastercoursefiles"


def _normalize_course_code(code: str) -> str:
    """Normalize a course code by stripping spaces between prefix and number.

    Examples:
        "CT 221"    → "CT221"
        "ARCH 100"  → "ARCH100"
        "ACCT 101A" → "ACCT101A"
        "D H 063A"  → "DH063A"
    """
    code = code.strip().upper()
    # Remove spaces between alphabetic and numeric/alphanumeric portions
    code = re.sub(r"\s+", "", code)
    return code


def _normalize_mcf_course_id(course_id: str) -> str:
    """Normalize an MCF course ID by stripping trailing dots, whitespace, and spaces."""
    course_id = course_id.strip().rstrip(".").strip().upper()
    course_id = re.sub(r"\s+", "", course_id)
    return course_id


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
    mcf = _load_mcf_index()
    college_norm = _normalize_college(college).lower()

    top6_codes: set[str] = set()

    for code in course_codes:
        normalized = _normalize_course_code(code)
        if not normalized:
            continue

        # Try exact match
        top6 = mcf.get((normalized, college_norm))
        if top6:
            top6_codes.add(top6)
            continue

        # Fallback: prefix match (handles CT100 matching CT100AB)
        prefix_index = _build_prefix_scan_index()
        college_courses = prefix_index.get(college_norm, [])
        for mcf_id, mcf_top6 in college_courses:
            if mcf_id.startswith(normalized):
                top6_codes.add(mcf_top6)
                break  # Take first match

    return top6_codes
