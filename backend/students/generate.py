"""
Stage 4: Synthetic student data generator.

Generates anonymous students with enrollment distributions calibrated to
DataMart 6-digit TOP code grade distributions. Each student is assigned a
primary TOP6 (weighted by real enrollment share), with 60% stickiness
to that area and 40% random draws from the full distribution.

Per-course TOP6 assignment flows through `ontology.mcf_lookup`, which
reads the 125 MCFs bundled in the backend source tree at
`backend/ontology/mastercoursefiles/`. College-key ↔ MCF-filename
translation goes through `pipeline.mcf_key_map.pdf_to_mcf_key`.

Grade sampling uses a tier-ladder fallback when a specific TOP6's grade
distribution is suppressed: exact TOP6 -> parent TOP4 rollup (first four
digits) -> college-wide DEFAULT_GRADES.

Usage:
    from students.generate import generate_and_load_students
    stats = generate_and_load_students("foothill", num_students=3000, seed=42)
"""

from __future__ import annotations

import json
import logging
import uuid
from dataclasses import dataclass, field
from itertools import accumulate
from pathlib import Path
from random import Random
from typing import List, Dict, Tuple, Optional

from neo4j import Driver

from students.helpers import compute_gpa, compute_primary_focus, course_order_key
from ontology.crosswalks import top_to_department_name
from ontology.mcf_lookup import _normalize_course_code
from pipeline.mcf_key_map import pdf_to_mcf_key

import csv as _csv
import re as _re

# Catalog codes use natural numbers ("HLTH 20") but the MCF uses
# zero-padded forms ("HLTH020"). This regex strips the leading zero run
# between the alphabetic prefix and the first non-zero digit so both
# sides collapse to the same canonical form (HLTH20) during MCF lookup.
_LEADING_ZERO_RE = _re.compile(r"([A-Z])(0+)(\d)")


def _canonical_course_id(code: str) -> str:
    """Canonicalize a course code for MCF matching — uppercase, strip
    internal whitespace, collapse leading zeros in the numeric portion.
    """
    s = _LEADING_ZERO_RE.sub(r"\1\3", _normalize_course_code(code))
    return s

logger = logging.getLogger(__name__)

# ── Deterministic UUID namespace ───────────────────────────────────────────────
NAMESPACE = uuid.UUID("a1b2c3d4-e5f6-7890-abcd-ef1234567890")

# ── Default parameters ─────────────────────────────────────────────────────────
DEFAULT_STUDENT_COUNT = 3000
FT_RATIO = 0.31
RETENTION_RATE = 0.67
PRIMARY_STICKINESS = 0.60
DEPT_CAP = 6  # Max courses per department per student
ACADEMIC_YEARS = [2022, 2023, 2024]

# Course load per term
PT_LOADS = [1, 2, 3]
PT_LOAD_WEIGHTS = [0.10, 0.40, 0.50]
FT_LOADS = [4, 5, 6]
FT_LOAD_WEIGHTS = [0.55, 0.35, 0.10]

# Unit caps per quarter
PT_UNIT_CAP = 11.0
FT_UNIT_CAP = 20.0

# Starting term distribution (season-only; year is spread uniformly across
# ACADEMIC_YEARS when the per-student start term is sampled).
START_TERM_WEIGHTS = {"Fall": 0.60, "Winter": 0.15, "Spring": 0.25}

# Non-credit prefixes to exclude
NON_CREDIT_PREFIXES = ["Non-Credit"]

# Pass/No Pass grade distribution
PNP_DIST = {"P": 0.85, "NP": 0.15}

# Default grade distribution (fallback when no calibrated data available)
DEFAULT_GRADES = {"A": 0.55, "B": 0.18, "C": 0.08, "D": 0.02, "F": 0.07, "W": 0.07, "P": 0.01}

# Sentinel TOP6 for courses that can't be mapped via the MCF. These are
# bucketed separately rather than silently dropped; the generation summary
# reports a per-college count so orphans are visible.
UNMAPPED_TOP6 = "000000"


# ── Data classes ───────────────────────────────────────────────────────────────


@dataclass
class Enrollment:
    course_code: str
    course_name: str
    department: str
    term: str
    grade: str
    status: str


@dataclass
class GeneratedStudent:
    uuid: str
    primary_top6: str = ""
    enrollments: List[Enrollment] = field(default_factory=list)


@dataclass
class GenerationStats:
    institution: str
    students_generated: int = 0
    enrollments_created: int = 0
    terms_covered: int = 0
    departments_covered: int = 0
    avg_courses_per_student: float = 0.0
    success_rate: float = 0.0
    grade_distribution: Dict[str, float] = field(default_factory=dict)
    top6_to_dept: Dict[str, str] = field(default_factory=dict)
    unmapped_courses: int = 0
    fallback_grade_samples: int = 0


# ── Calibration loading ──────────────────────────────────────────────────────


_METRICS_DIR = Path(__file__).parent.parent / "ontology" / "college_metrics"


def _load_college_metrics(college_key: str) -> Optional[dict]:
    """Load DataMart-sourced institutional metrics for the college:
    enrollment, ft_ratio, retention_rate. Built from
    StudentHeadcount, UnitLoadSumm, and CourseRetSuccessSumm by
    `pipeline.build_college_metrics`.
    """
    path = _METRICS_DIR / f"{college_key}.json"
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return None


def _load_top6_calibration(college_key: str) -> Optional[dict]:
    """Load 6-digit TOP code calibration: per-college TOP6 grade
    distributions plus parent-TOP4 rollup used by the grade sampler's
    fallback tier.
    """
    path = _METRICS_DIR / "top6" / f"{college_key}.json"
    if path.exists():
        with open(path) as f:
            cal = json.load(f)
        logger.info(
            f"Loaded TOP6 calibration for {college_key}: "
            f"{len(cal.get('top6_codes', {}))} codes, "
            f"{cal.get('total_enrollments', 0):,} enrollments"
        )
        return cal
    logger.warning(f"No TOP6 calibration for {college_key}")
    return None


# ── Per-course TOP6 lookup via the bundled MCFs ─────────────────────────────


_MCF_DIR = Path(__file__).parent.parent / "ontology" / "mastercoursefiles"


def _build_course_to_top6(courses: List[dict], college_key: str) -> Dict[str, str]:
    """Map each catalog course code to its 6-digit TOP code.

    Reads the college's MCF file directly from the bundled MCF directory
    rather than routing through `ontology.mcf_lookup._load_mcf_index`.
    The bundled filenames use the backend college key
    (`MasterCourseFile_sandiegocity.csv`, `MasterCourseFile_irvinevalley.csv`)
    but the `College` column inside those files uses the human-readable
    form ("San Diego City"), which is the mismatch that makes an
    index-level lookup unreliable. Reading the file directly bypasses
    the column entirely.

    When the same course appears multiple times in the MCF (across
    Issue/Update Dates reflecting TOP-code reclassifications), the
    latest-dated entry wins. This avoids the staleness seen on Foothill
    where HLTH020 went 040100 -> 120100 -> 126000 over the years — the
    most recent classification is the one the calibration expects.

    Courses without an MCF entry are mapped to UNMAPPED_TOP6 so they
    remain visible in the generation summary rather than being silently
    dropped.
    """
    # Try backend-key filename first; fall back to pdf_to_mcf_key form.
    mcf_path = _MCF_DIR / f"MasterCourseFile_{college_key}.csv"
    if not mcf_path.exists():
        alt = pdf_to_mcf_key(college_key)
        alt_path = _MCF_DIR / f"MasterCourseFile_{alt}.csv"
        if alt_path.exists():
            mcf_path = alt_path
        else:
            logger.warning(
                f"No MCF file for {college_key} at {mcf_path.name} or "
                f"{alt_path.name}; all courses will be UNMAPPED_TOP6"
            )
            return {c.get("code", ""): UNMAPPED_TOP6 for c in courses if c.get("code")}

    # canonical_course_id -> (top6, issue_date). Latest date wins.
    college_index: Dict[str, Tuple[str, str]] = {}
    with open(mcf_path, encoding="utf-8", errors="replace") as f:
        reader = _csv.DictReader(f)
        for row in reader:
            course_id = row.get("Course ID", "") or ""
            top_code = (row.get("TOP Code", "") or "").strip()
            date = (row.get("Issue/Update Date", "") or "").strip()
            if not course_id or not top_code:
                continue
            canon = _canonical_course_id(course_id.strip().rstrip("."))
            if not canon:
                continue
            if len(top_code) == 6:
                top6 = top_code
            elif len(top_code) == 4:
                top6 = top_code + "00"
            else:
                continue
            existing = college_index.get(canon)
            if existing is None or date > existing[1]:
                college_index[canon] = (top6, date)

    canon_to_top6: Dict[str, str] = {k: v[0] for k, v in college_index.items()}

    mapping: Dict[str, str] = {}
    for c in courses:
        code = c.get("code", "")
        if not code:
            continue
        canon = _canonical_course_id(code)
        top6 = canon_to_top6.get(canon)
        if not top6:
            # Prefix fallback: catalog "CT100" against MCF "CT100AB".
            for mcf_id, mcf_top6 in canon_to_top6.items():
                if mcf_id.startswith(canon):
                    top6 = mcf_top6
                    break
        mapping[code] = top6 or UNMAPPED_TOP6
    return mapping


# ── Per-student prefix ordering ──────────────────────────────────────────────


def _course_prefix(code: str) -> str:
    """Extract the letter prefix from a course code. 'CS 1A' -> 'CS'."""
    import re as _re
    match = _re.match(r"([A-Z ]+)", code)
    return match.group(1).strip() if match else ""


def _ordering_ok(code: str, prefix_max: Dict[str, Tuple[int, str]]) -> bool:
    """True iff this course may be taken next given the student's history
    in its prefix. Within a single prefix, order keys must be
    non-decreasing (equality permits retakes). First enrollment in a new
    prefix is unconstrained.
    """
    prefix = _course_prefix(code)
    if not prefix or prefix not in prefix_max:
        return True
    return course_order_key(code) >= prefix_max[prefix]


def _record_prefix(code: str, prefix_max: Dict[str, Tuple[int, str]]) -> None:
    """Update the student's per-prefix max order key after an enrollment."""
    prefix = _course_prefix(code)
    if not prefix:
        return
    key = course_order_key(code)
    current = prefix_max.get(prefix)
    if current is None or key > current:
        prefix_max[prefix] = key


# ── Course pool building ────────────────────────────────────────────────────


def _parse_units(units_str: str) -> float:
    """Parse units string to float. '4.5' -> 4.5, '1-2' -> 1.5, '3unit(s)' -> 3.0."""
    import re as _re
    if not units_str:
        return 0.0
    m = _re.match(r"([\d.]+)", units_str.strip())
    if not m:
        return 0.0
    try:
        if "-" in units_str:
            parts = _re.findall(r"[\d.]+", units_str)
            if len(parts) >= 2:
                return (float(parts[0]) + float(parts[1])) / 2
        return float(m.group(1))
    except (ValueError, IndexError):
        return 0.0


def _build_top6_course_pools(
    courses: List[dict],
    top6_cal: dict,
    course_to_top6: Dict[str, str],
) -> Tuple[Dict[str, List[dict]], int]:
    """Group courses into pools keyed by 6-digit TOP code.

    Returns (pools, unmapped_count). Pools only include TOP6 codes that
    are both present in `course_to_top6` and have a calibration entry —
    courses whose TOP6 is not calibrated are counted as unmapped so
    calibration gaps are visible, not silent.
    """
    valid_top6s = set(top6_cal.get("top6_codes", {}).keys())
    pools: Dict[str, List[dict]] = {code: [] for code in valid_top6s}
    unmapped = 0

    for c in courses:
        dept = c.get("department", "")
        if any(dept.startswith(p) for p in NON_CREDIT_PREFIXES):
            continue
        units = _parse_units(c.get("units", "0"))
        if units <= 0:
            continue

        top6 = course_to_top6.get(c["code"], UNMAPPED_TOP6)
        if top6 == UNMAPPED_TOP6 or top6 not in valid_top6s:
            unmapped += 1
            continue

        c["_units"] = units
        pools[top6].append(c)

    populated = sum(1 for p in pools.values() if p)
    total_courses = sum(len(p) for p in pools.values())
    logger.info(
        f"Course pools: {total_courses} courses across {populated}/{len(pools)} "
        f"TOP6 codes ({unmapped} unmapped)"
    )
    return pools, unmapped


# ── Term sequence ──────────────────────────────────────────────────────────────


def _build_term_sequence() -> List[str]:
    """Build ordered list of term strings."""
    terms = []
    for year in ACADEMIC_YEARS:
        terms.append(f"{year}-Fall")
        terms.append(f"{year}-Winter")
        terms.append(f"{year + 1}-Spring")
    return terms


# ── Grade sampling with tier-ladder fallback ────────────────────────────────


def _sample_grade(
    top6: str,
    top6_data: Dict[str, dict],
    top4_rollup: Dict[str, dict],
    default_grades: Dict[str, float],
    rng: Random,
) -> Tuple[str, str, int]:
    """Sample a grade for a TOP6 using the tier ladder:
        1. exact TOP6 grade distribution
        2. parent TOP4 rollup (first 4 digits of TOP6)
        3. DEFAULT_GRADES

    Returns (grade, status, fallback_level). fallback_level is 0 for
    exact, 1 for parent rollup, 2 for default.
    """
    grades = top6_data.get(top6, {}).get("grades")
    fallback = 0
    if not grades:
        grades = top4_rollup.get(top6[:4], {}).get("grades")
        fallback = 1
    if not grades:
        grades = default_grades
        fallback = 2

    labels = list(grades.keys())
    weights = list(grades.values())
    grade = rng.choices(labels, weights=weights, k=1)[0]
    status = "Withdrawn" if grade == "W" else "Completed"
    return grade, status, fallback


# ── Core generation ────────────────────────────────────────────────────────────


def generate_students(
    college_key: str,
    courses: List[dict],
    num_students: Optional[int] = None,
    seed: int = 42,
    config: Optional[dict] = None,
) -> Tuple[List[GeneratedStudent], GenerationStats]:
    """Generate synthetic students with TOP6-calibrated distributions."""
    cfg = config or {}

    # Load calibrations
    top6_cal = _load_top6_calibration(college_key)
    metrics = _load_college_metrics(college_key)

    ft_ratio = cfg.get("ft_ratio", (metrics or {}).get("ft_ratio", FT_RATIO))
    retention = cfg.get("retention_rate", (metrics or {}).get("retention_rate", RETENTION_RATE))

    if num_students is None:
        if metrics and "enrollment" in metrics:
            num_students = metrics["enrollment"]
        else:
            num_students = DEFAULT_STUDENT_COUNT
    logger.info(f"Generating {num_students} students for {college_key}")

    # Per-course TOP6 mapping via MCF
    course_to_top6 = _build_course_to_top6(courses, college_key)

    # Build course pools by TOP6
    top6_data: Dict[str, dict] = {}
    top4_rollup: Dict[str, dict] = {}
    top6_courses: Dict[str, List[dict]] = {}
    top6_to_dept: Dict[str, str] = {}
    valid_codes: List[str] = []
    top6_weights: List[float] = []
    unmapped_count = 0

    if top6_cal:
        top6_courses, unmapped_count = _build_top6_course_pools(courses, top6_cal, course_to_top6)
        top6_data = top6_cal["top6_codes"]
        top4_rollup = top6_cal.get("top4_rollup", {})

        valid_codes = [code for code in top6_data if top6_courses.get(code)]
        top6_weights = [top6_data[code]["enrollment"] for code in valid_codes]

        # Build TOP6 -> department mapping from the Chancellor's Office
        # Taxonomy of Programs Manual via top_to_department_name. This
        # gives Student.primary_focus the canonical TOP4 program name
        # (e.g., "English", "Mathematics, General") that the courses
        # loader uses for Course.department, keeping the two consistent
        # by construction. Earlier versions tallied the modal Gemini-
        # extracted department string from enriched.json, which carried
        # pre-canonicalization noise like "ENGLISH" or "BIOLOGICAL
        # SCIENCE" and required a post-load rederive pass to clean up.
        for code in valid_codes:
            name = top_to_department_name(code)
            if name:
                top6_to_dept[code] = name

        if not valid_codes:
            logger.warning("No valid TOP6 codes with courses — falling back to flat generation")
            top6_cal = None

    top6_cum_weights = list(accumulate(top6_weights)) if top6_weights else []

    rng = Random(seed)
    all_terms = _build_term_sequence()

    # Flat weighted candidates for student start terms
    start_candidates: List[int] = []
    start_cand_weights: List[float] = []
    for idx, term in enumerate(all_terms):
        _, season = term.split("-", 1)
        weight = START_TERM_WEIGHTS.get(season, 0.0)
        if weight > 0:
            start_candidates.append(idx)
            start_cand_weights.append(weight)
    start_cum_weights = list(accumulate(start_cand_weights)) if start_cand_weights else []

    # Flat course list fallback (if no TOP6 calibration at all)
    flat_courses: List[dict] = []
    if not top6_cal:
        flat_courses = [c for c in courses if _parse_units(c.get("units", "0")) > 0]
        for c in flat_courses:
            c["_units"] = _parse_units(c.get("units", "0"))

    students: List[GeneratedStudent] = []
    total_enrollments = 0
    grade_counts: Dict[str, int] = {}
    depts_seen: set = set()
    top6_enrollment_counts: Dict[str, int] = {}
    fallback_grade_samples = 0

    for i in range(num_students):
        student_uuid = str(uuid.uuid5(NAMESPACE, f"{college_key}-student-{i}"))
        primary_top6 = (
            rng.choices(valid_codes, cum_weights=top6_cum_weights, k=1)[0]
            if valid_codes else ""
        )
        student = GeneratedStudent(uuid=student_uuid, primary_top6=primary_top6)

        is_ft = rng.random() < ft_ratio

        start_idx = (
            rng.choices(start_candidates, cum_weights=start_cum_weights, k=1)[0]
            if start_candidates else 0
        )

        max_terms = 1
        while max_terms < len(all_terms) - start_idx:
            if rng.random() > retention:
                break
            max_terms += 1

        active_terms = all_terms[start_idx: start_idx + max_terms]

        taken_codes: set = set()
        dept_counts: Dict[str, int] = {}
        # Per-prefix max order key — enforces same-subject numeric ordering.
        prefix_max: Dict[str, Tuple[int, str]] = {}
        unit_cap = FT_UNIT_CAP if is_ft else PT_UNIT_CAP

        for term in active_terms:
            if is_ft:
                num_courses = rng.choices(FT_LOADS, weights=FT_LOAD_WEIGHTS, k=1)[0]
            else:
                num_courses = rng.choices(PT_LOADS, weights=PT_LOAD_WEIGHTS, k=1)[0]

            term_units = 0.0
            for _ in range(num_courses):
                if top6_cal and primary_top6:
                    if rng.random() < PRIMARY_STICKINESS:
                        chosen_top6 = primary_top6
                    else:
                        chosen_top6 = rng.choices(valid_codes, cum_weights=top6_cum_weights, k=1)[0]

                    pool = top6_courses.get(chosen_top6, [])
                    if not pool:
                        continue

                    available = [c for c in pool
                                 if c["code"] not in taken_codes
                                 and dept_counts.get(c.get("department", ""), 0) < DEPT_CAP
                                 and _ordering_ok(c["code"], prefix_max)]
                    if not available:
                        chosen_top6 = rng.choices(valid_codes, cum_weights=top6_cum_weights, k=1)[0]
                        pool = top6_courses.get(chosen_top6, [])
                        if not pool:
                            continue
                        available = [c for c in pool
                                     if c["code"] not in taken_codes
                                     and dept_counts.get(c.get("department", ""), 0) < DEPT_CAP
                                     and _ordering_ok(c["code"], prefix_max)]
                        if not available:
                            continue

                    course = rng.choices(available, k=1)[0]

                    course_units = course.get("_units", 3.0)
                    if term_units + course_units > unit_cap:
                        continue
                    term_units += course_units
                    taken_codes.add(course["code"])
                    _record_prefix(course["code"], prefix_max)
                    dept = course.get("department", "")
                    dept_counts[dept] = dept_counts.get(dept, 0) + 1
                    top6_enrollment_counts[chosen_top6] = top6_enrollment_counts.get(chosen_top6, 0) + 1

                    # Grade sampling with tier-ladder fallback.
                    grading = course.get("grading", "")
                    if "Pass/No Pass Only" in grading:
                        grade = rng.choices(list(PNP_DIST.keys()), weights=list(PNP_DIST.values()), k=1)[0]
                        status = "Completed" if grade == "P" else "Not Passed"
                    else:
                        grade, status, fallback_level = _sample_grade(
                            chosen_top6, top6_data, top4_rollup, DEFAULT_GRADES, rng,
                        )
                        if fallback_level > 0:
                            fallback_grade_samples += 1

                else:
                    # No calibration path: flat sampling with ordering rule.
                    available = [c for c in flat_courses
                                 if c["code"] not in taken_codes
                                 and _ordering_ok(c["code"], prefix_max)]
                    if not available:
                        continue
                    course = rng.choices(available, k=1)[0]
                    course_units = course.get("_units", 3.0)
                    if term_units + course_units > unit_cap:
                        continue
                    term_units += course_units
                    taken_codes.add(course["code"])
                    _record_prefix(course["code"], prefix_max)
                    grade = rng.choices(list(DEFAULT_GRADES.keys()), weights=list(DEFAULT_GRADES.values()), k=1)[0]
                    status = "Withdrawn" if grade == "W" else "Completed"

                enrollment = Enrollment(
                    course_code=course["code"],
                    course_name=course.get("name", ""),
                    department=course.get("department", ""),
                    term=term,
                    grade=grade,
                    status=status,
                )
                student.enrollments.append(enrollment)
                total_enrollments += 1
                grade_counts[grade] = grade_counts.get(grade, 0) + 1
                depts_seen.add(course.get("department", ""))

        if student.enrollments:
            students.append(student)

    # Stats
    success_grades = {"A", "B", "C", "P"}
    total_graded = sum(grade_counts.values())
    success_count = sum(grade_counts.get(g, 0) for g in success_grades)

    stats = GenerationStats(
        institution=college_key,
        students_generated=len(students),
        enrollments_created=total_enrollments,
        terms_covered=len(all_terms),
        departments_covered=len(depts_seen),
        avg_courses_per_student=total_enrollments / len(students) if students else 0,
        success_rate=success_count / total_graded if total_graded else 0,
        grade_distribution={
            g: grade_counts.get(g, 0) / total_graded if total_graded else 0
            for g in ["A", "B", "C", "P", "D", "F", "W", "NP"]
        },
        top6_to_dept=top6_to_dept if top6_cal else {},
        unmapped_courses=unmapped_count,
        fallback_grade_samples=fallback_grade_samples,
    )

    logger.info(
        f"Generated {stats.students_generated} students, "
        f"{stats.enrollments_created} enrollments, "
        f"success rate: {stats.success_rate:.1%}, "
        f"avg courses/student: {stats.avg_courses_per_student:.1f}"
    )
    if unmapped_count:
        logger.warning(f"{unmapped_count} courses were unmapped (no MCF/TOP6 match) — excluded from pools")
    if fallback_grade_samples:
        pct = fallback_grade_samples / total_enrollments if total_enrollments else 0
        logger.info(
            f"Grade-sampling fallback tier used {fallback_grade_samples} times "
            f"({pct:.1%} of enrollments) — TOP6 missing, fell back to parent TOP4 or default"
        )

    if top6_cal:
        target_success = sum(
            sum(d["grades"].get(g, 0) for g in success_grades) * d["enrollment"]
            for d in top6_data.values()
        ) / sum(d["enrollment"] for d in top6_data.values()) if top6_data else 0
        diff = abs(stats.success_rate - target_success)
        logger.info(
            f"Calibration check — success rate: "
            f"synthetic={stats.success_rate:.1%}, "
            f"target={target_success:.1%}, "
            f"diff={diff:.1%}"
        )

        total_cal = sum(top6_data[c]["enrollment"] for c in valid_codes)
        total_synth = sum(top6_enrollment_counts.values())
        if total_cal and total_synth:
            deltas = []
            for code in valid_codes:
                target = top6_data[code]["enrollment"] / total_cal
                actual = top6_enrollment_counts.get(code, 0) / total_synth
                deltas.append((code, top6_data[code].get("name", code), actual - target))
            deltas.sort(key=lambda row: abs(row[2]), reverse=True)
            top5 = "; ".join(
                f"{code} {name}: {delta:+.1%}" for code, name, delta in deltas[:5]
            )
            logger.info(f"Top-5 TOP6 share deltas (synthetic − target): {top5}")

            all_cal_total = sum(d["enrollment"] for d in top6_data.values())
            dropped = all_cal_total - total_cal
            if all_cal_total and dropped:
                logger.info(
                    f"Dropped share (TOP6s with no courses): "
                    f"{dropped / all_cal_total:.1%} of calibration weight redistributed"
                )

    return students, stats


# ── Neo4j loader ───────────────────────────────────────────────────────────────

BATCH_SIZE = 2000


def _derive_student_fields(
    students: List[GeneratedStudent],
    top6_to_dept: Dict[str, str],
) -> List[dict]:
    """Compute gpa, primary_focus, courses_completed from in-memory state."""
    rows: List[dict] = []
    for st in students:
        completed = [e for e in st.enrollments if e.status == "Completed"]
        grades = [e.grade for e in completed if e.grade]

        primary_focus = top6_to_dept.get(st.primary_top6, "")
        if not primary_focus:
            primary_focus = compute_primary_focus(
                [{"department": e.department, "status": e.status} for e in st.enrollments]
            )

        rows.append({
            "uuid": st.uuid,
            "gpa": compute_gpa(grades),
            "primary_focus": primary_focus,
            "primary_top6": st.primary_top6,
            "courses_completed": len(completed),
        })
    return rows


def load_students(
    driver: Driver,
    institution: str,
    students: List[GeneratedStudent],
    top6_to_dept: Optional[Dict[str, str]] = None,
) -> int:
    """Load generated students into Neo4j. Full replace strategy."""
    student_rows = _derive_student_fields(students, top6_to_dept or {})

    with driver.session() as session:
        total_deleted = 0
        while True:
            result = session.run(
                "MATCH (s:Student)-[:ENROLLED_IN]->(c:Course {college: $inst}) "
                "WITH s LIMIT 1000 DETACH DELETE s RETURN count(s) as cnt",
                inst=institution,
            )
            cnt = result.single()["cnt"]
            total_deleted += cnt
            if cnt == 0:
                break
        if total_deleted:
            logger.info(f"Cleared {total_deleted} existing students for {institution}")

        for i in range(0, len(student_rows), BATCH_SIZE):
            chunk = student_rows[i:i + BATCH_SIZE]
            session.run(
                """
                UNWIND $batch AS row
                MERGE (s:Student {uuid: row.uuid})
                SET s.gpa = row.gpa,
                    s.primary_focus = row.primary_focus,
                    s.primary_top6 = row.primary_top6,
                    s.courses_completed = row.courses_completed,
                    s.college = $inst
                """,
                inst=institution,
                batch=chunk,
            )
        logger.info(f"Pre-created {len(student_rows)} Student nodes with derived fields")

        batch: List[dict] = []
        loaded = 0
        for student in students:
            for enrollment in student.enrollments:
                batch.append({
                    "uuid": student.uuid,
                    "course_code": enrollment.course_code,
                    "grade": enrollment.grade,
                    "term": enrollment.term,
                    "status": enrollment.status,
                })
                if len(batch) >= BATCH_SIZE:
                    _write_batch(session, institution, batch)
                    loaded += len(batch)
                    batch = []

        if batch:
            _write_batch(session, institution, batch)
            loaded += len(batch)

        logger.info(f"Loaded {loaded} enrollments for {len(students)} students")

        return loaded


def _write_batch(session, institution: str, batch: List[dict]):
    """Write a batch of enrollments against pre-existing Student nodes."""
    session.run(
        """
        UNWIND $batch AS row
        MATCH (s:Student {uuid: row.uuid})
        MATCH (c:Course {code: row.course_code, college: $inst})
        CREATE (s)-[:ENROLLED_IN {
            grade: row.grade,
            term: row.term,
            status: row.status
        }]->(c)
        """,
        batch=batch,
        inst=institution,
    )


# ── Orchestration ──────────────────────────────────────────────────────────────


def generate_and_load_students(
    college_key: str,
    courses: List[dict],
    institution_name: str,
    driver: Driver,
    num_students: Optional[int] = None,
    seed: int = 42,
    config: Optional[dict] = None,
) -> GenerationStats:
    """Generate synthetic students and load them into Neo4j."""
    students, stats = generate_students(
        college_key=college_key,
        courses=courses,
        num_students=num_students,
        seed=seed,
        config=config,
    )

    load_students(driver, institution_name, students, top6_to_dept=stats.top6_to_dept)
    return stats
