"""
Stage 4: Synthetic student data generator.

Generates anonymous students with enrollment distributions calibrated to
DataMart 4-digit TOP code grade distributions. Each student is assigned a
primary TOP code (weighted by real enrollment share), with 60% stickiness
to that area and 40% random draws from the full distribution.

Usage:
    from pipeline.students import generate_and_load_students
    stats = generate_and_load_students("foothill", num_students=3000, seed=42)
"""

from __future__ import annotations

import csv
import json
import logging
import os
import re
import uuid
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from random import Random
from typing import List, Dict, Tuple, Optional

from neo4j import Driver

logger = logging.getLogger(__name__)

# ── Deterministic UUID namespace ───────────────────────────────────────────────
NAMESPACE = uuid.UUID("a1b2c3d4-e5f6-7890-abcd-ef1234567890")

# ── Default parameters ─────────────────────────────────────────────────────────
DEFAULT_STUDENT_COUNT = 3000
FT_RATIO = 0.31
RETENTION_RATE = 0.67
SUMMER_ENROLLMENT_RATE = 0.15
PRIMARY_STICKINESS = 0.60
DEPT_CAP = 6  # Max courses per department per student
RETAKE_RATE = 0.05
ACADEMIC_YEARS = [2022, 2023, 2024]

# Course load per term
PT_LOADS = [1, 2, 3]
PT_LOAD_WEIGHTS = [0.10, 0.40, 0.50]
FT_LOADS = [4, 5, 6]
FT_LOAD_WEIGHTS = [0.55, 0.35, 0.10]

# Unit caps per quarter
PT_UNIT_CAP = 11.0
FT_UNIT_CAP = 20.0

# Starting term distribution
START_TERM_WEIGHTS = {"Fall": 0.60, "Winter": 0.15, "Spring": 0.20, "Summer": 0.05}

# Non-credit prefixes to exclude
NON_CREDIT_PREFIXES = ["Non-Credit"]

# Known prefix aliases (catalog prefix → DataMart prefix)
PREFIX_ALIASES = {
    "CS": "C S", "DA": "D A", "DH": "D H", "RT": "R T", "VT": "V T",
    "LA": "L A", "ENGL C": "ENGL", "COMM C": "COMM", "PSYC C": "PSYC",
    "POLS C": "POLI", "STAT C": "MATH",
}

# Pass/No Pass grade distribution
PNP_DIST = {"P": 0.85, "NP": 0.15}

# Default grade distribution (fallback when TOP4 data unavailable)
DEFAULT_GRADES = {"A": 0.55, "B": 0.18, "C": 0.08, "D": 0.02, "F": 0.07, "W": 0.07, "P": 0.01}


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
    primary_top4: str = ""
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
    top4_to_dept: Dict[str, str] = field(default_factory=dict)


# ── Calibration loading ──────────────────────────────────────────────────────


def _load_calibration(college_key: str) -> Optional[dict]:
    """Load the old 2-digit calibration for ft_ratio and retention_rate."""
    path = Path(__file__).parent / "calibrations" / f"{college_key}.json"
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return None


def _load_top4_calibration(college_key: str) -> Optional[dict]:
    """Load 4-digit TOP code calibration data."""
    path = Path(__file__).parent / "calibrations" / "top4" / f"{college_key}.json"
    if path.exists():
        with open(path) as f:
            cal = json.load(f)
        logger.info(f"Loaded TOP4 calibration for {college_key}: {len(cal.get('top4_codes', {}))} codes, {cal.get('total_enrollments', 0):,} enrollments")
        return cal
    logger.info(f"No TOP4 calibration for {college_key}")
    return None


# ── Prefix → TOP4 mapping ─────────────────────────────────────────────────────

_MCF_DIR = Path(os.environ.get("MCF_DIR", Path.home() / "Desktop" / "cc_dataset" / "mastercoursefiles"))

# System-wide fallback (only used when a college has no MCF)
_FALLBACK_PREFIX_TOP4: Dict[str, str] = {}
_FALLBACK_PREFIX_PATH = Path(__file__).parent / "calibrations" / "prefix_to_top4.json"


def _get_fallback_prefix_map() -> Dict[str, str]:
    """Load system-wide prefix → TOP4 fallback mapping."""
    global _FALLBACK_PREFIX_TOP4
    if _FALLBACK_PREFIX_TOP4:
        return _FALLBACK_PREFIX_TOP4
    if _FALLBACK_PREFIX_PATH.exists():
        with open(_FALLBACK_PREFIX_PATH) as f:
            _FALLBACK_PREFIX_TOP4 = json.load(f)
        return _FALLBACK_PREFIX_TOP4
    return {}


def _course_prefix(code: str) -> str:
    """Extract the letter prefix from a course code. 'CS 1A' → 'CS'."""
    match = re.match(r"([A-Z ]+)", code)
    return match.group(1).strip() if match else ""


def _resolve_prefix(prefix: str, prefix_map: Dict[str, str]) -> str:
    """Resolve a prefix through aliases and concurrent-enrollment variants."""
    if prefix in PREFIX_ALIASES:
        return PREFIX_ALIASES[prefix]
    # "ENGL C" → "ENGL" (concurrent enrollment variant, space required)
    # but NOT "AGTC" → "AGT"
    if prefix.endswith(" C"):
        base = prefix[:-2]
        if base in prefix_map and prefix not in prefix_map:
            return base
    return prefix


def _load_college_prefix_map(college_key: str) -> Dict[str, str]:
    """Build prefix → TOP4 mapping from a college's own master course file.

    Each college's MCF is authoritative for its prefix assignments.
    Falls back to system-wide mapping only if no MCF exists.
    """
    mcf_path = _MCF_DIR / f"MasterCourseFile_{college_key}.csv"
    if not mcf_path.exists():
        logger.info(f"No MCF for {college_key}, using system-wide fallback")
        return _get_fallback_prefix_map()

    from collections import Counter
    prefix_votes: Dict[str, Counter] = {}
    try:
        with open(mcf_path, encoding="utf-8", errors="replace") as f:
            reader = csv.DictReader(f)
            for row in reader:
                course_id = row.get("Course ID", "").strip()
                top_code = row.get("TOP Code", "").strip()
                if not course_id or not top_code:
                    continue
                prefix = _course_prefix(course_id)
                if not prefix:
                    continue
                top4 = top_code[:4] if len(top_code) >= 4 else top_code
                if top4 and top4 != "0000":
                    prefix_votes.setdefault(prefix, Counter())[top4] += 1
    except Exception as e:
        logger.warning(f"Could not read MCF for {college_key}: {e}")
        return _get_fallback_prefix_map()

    # Resolve each prefix to its most common TOP4 within this college
    mapping = {prefix: votes.most_common(1)[0][0] for prefix, votes in prefix_votes.items()}
    logger.info(f"Loaded {len(mapping)} prefix mappings from {college_key} MCF")
    return mapping


def _build_top4_course_pools(
    courses: List[dict],
    top4_cal: dict,
    college_key: str = "",
) -> Dict[str, List[dict]]:
    """Group courses into pools by 4-digit TOP code."""
    prefix_map = _load_college_prefix_map(college_key) if college_key else _get_fallback_prefix_map()
    valid_top4s = set(top4_cal.get("top4_codes", {}).keys())

    pools: Dict[str, List[dict]] = {code: [] for code in valid_top4s}
    unmapped = 0

    for c in courses:
        # Skip non-credit
        dept = c.get("department", "")
        if any(dept.startswith(p) for p in NON_CREDIT_PREFIXES):
            continue
        units = _parse_units(c.get("units", "0"))
        if units <= 0:
            continue

        prefix = _course_prefix(c["code"])
        resolved = _resolve_prefix(prefix, prefix_map)

        top4 = prefix_map.get(resolved) or prefix_map.get(prefix)
        if top4 and top4 in valid_top4s:
            c["_units"] = units
            pools[top4].append(c)
        else:
            unmapped += 1

    populated = sum(1 for p in pools.values() if p)
    total_courses = sum(len(p) for p in pools.values())
    logger.info(f"Course pools: {total_courses} courses across {populated}/{len(pools)} TOP4 codes ({unmapped} unmapped)")
    return pools


def _parse_units(units_str: str) -> float:
    """Parse units string to float. '4.5' → 4.5, '1-2' → 1.5, '3unit(s)' → 3.0."""
    if not units_str:
        return 0.0
    # Extract leading number from any format
    m = re.match(r"([\d.]+)", units_str.strip())
    if not m:
        return 0.0
    try:
        if "-" in units_str:
            parts = re.findall(r"[\d.]+", units_str)
            if len(parts) >= 2:
                return (float(parts[0]) + float(parts[1])) / 2
        return float(m.group(1))
    except (ValueError, IndexError):
        return 0.0


# ── Term sequence ──────────────────────────────────────────────────────────────


def _build_term_sequence() -> List[str]:
    """Build ordered list of term strings."""
    terms = []
    for year in ACADEMIC_YEARS:
        terms.append(f"{year}-Fall")
        terms.append(f"{year}-Winter")
        terms.append(f"{year + 1}-Spring")
    return terms


# ── Core generation ────────────────────────────────────────────────────────────


def generate_students(
    college_key: str,
    courses: List[dict],
    num_students: Optional[int] = None,
    seed: int = 42,
    config: Optional[dict] = None,
) -> Tuple[List[GeneratedStudent], GenerationStats]:
    """Generate synthetic students with 4-digit TOP code calibrated distributions."""
    cfg = config or {}

    # Load calibrations
    top4_cal = _load_top4_calibration(college_key)
    old_cal = _load_calibration(college_key)

    ft_ratio = cfg.get("ft_ratio", (old_cal or {}).get("ft_ratio", FT_RATIO))
    retention = cfg.get("retention_rate", (old_cal or {}).get("retention_rate", RETENTION_RATE))

    if num_students is None:
        if old_cal and "enrollment" in old_cal:
            num_students = old_cal["enrollment"]
        else:
            num_students = DEFAULT_STUDENT_COUNT
    logger.info(f"Generating {num_students} students for {college_key}")

    # Build course pools by TOP4
    if top4_cal:
        top4_courses = _build_top4_course_pools(courses, top4_cal, college_key)
        top4_data = top4_cal["top4_codes"]

        # Only include TOP4 codes that have both calibration data AND courses
        valid_codes = [code for code in top4_data if top4_courses.get(code)]
        top4_weights = [top4_data[code]["enrollment"] for code in valid_codes]

        # Build TOP4 → department mapping from course pools (authoritative)
        top4_to_dept: Dict[str, str] = {}
        for code, pool in top4_courses.items():
            if pool:
                dept_counter: Dict[str, int] = {}
                for c in pool:
                    d = c.get("department", "")
                    if d:
                        dept_counter[d] = dept_counter.get(d, 0) + 1
                if dept_counter:
                    top4_to_dept[code] = max(dept_counter, key=dept_counter.get)

        if not valid_codes:
            logger.warning("No valid TOP4 codes with courses — falling back to flat generation")
            top4_cal = None
    else:
        valid_codes = []
        top4_weights = []

    rng = Random(seed)
    all_terms = _build_term_sequence()
    start_terms_list = list(START_TERM_WEIGHTS.keys())
    start_terms_weights = list(START_TERM_WEIGHTS.values())

    # Flat course list fallback (if no TOP4 calibration)
    if not top4_cal:
        flat_courses = [c for c in courses if _parse_units(c.get("units", "0")) > 0]
        for c in flat_courses:
            c["_units"] = _parse_units(c.get("units", "0"))

    students: List[GeneratedStudent] = []
    total_enrollments = 0
    grade_counts: Dict[str, int] = {}
    depts_seen: set = set()

    for i in range(num_students):
        student_uuid = str(uuid.uuid5(NAMESPACE, f"{college_key}-student-{i}"))
        primary_top4 = rng.choices(valid_codes, weights=top4_weights, k=1)[0] if valid_codes else ""
        student = GeneratedStudent(uuid=student_uuid, primary_top4=primary_top4)

        is_ft = rng.random() < ft_ratio
        start_season = rng.choices(start_terms_list, weights=start_terms_weights, k=1)[0]

        # Find starting term
        start_idx = 0
        for idx, term in enumerate(all_terms):
            if term.endswith(start_season):
                start_idx = idx
                break

        # Determine persistence
        max_terms = 1
        while max_terms < len(all_terms) - start_idx:
            if rng.random() > retention:
                break
            max_terms += 1

        active_terms = all_terms[start_idx: start_idx + max_terms]
        active_terms = [
            t for t in active_terms
            if not t.endswith("-Summer") or rng.random() < SUMMER_ENROLLMENT_RATE
        ]

        taken_codes: set = set()
        dept_counts: Dict[str, int] = {}  # Track per-department enrollment count
        unit_cap = FT_UNIT_CAP if is_ft else PT_UNIT_CAP

        for term in active_terms:
            if is_ft:
                num_courses = rng.choices(FT_LOADS, weights=FT_LOAD_WEIGHTS, k=1)[0]
            else:
                num_courses = rng.choices(PT_LOADS, weights=PT_LOAD_WEIGHTS, k=1)[0]

            term_units = 0.0
            for _ in range(num_courses):
                # Choose TOP4: 60% primary, 40% random
                if top4_cal and primary_top4:
                    if rng.random() < PRIMARY_STICKINESS:
                        chosen_top4 = primary_top4
                    else:
                        chosen_top4 = rng.choices(valid_codes, weights=top4_weights, k=1)[0]

                    pool = top4_courses.get(chosen_top4, [])
                    if not pool:
                        continue

                    # Pick course, avoid duplicates and enforce department cap
                    available = [c for c in pool
                                 if c["code"] not in taken_codes
                                 and dept_counts.get(c.get("department", ""), 0) < DEPT_CAP]
                    if not available:
                        # Try a random TOP4 instead
                        chosen_top4 = rng.choices(valid_codes, weights=top4_weights, k=1)[0]
                        pool = top4_courses.get(chosen_top4, [])
                        if not pool:
                            continue
                        available = [c for c in pool
                                     if c["code"] not in taken_codes
                                     and dept_counts.get(c.get("department", ""), 0) < DEPT_CAP]
                        if not available:
                            continue

                    course = rng.choices(available, k=1)[0]

                    # Check unit cap
                    course_units = course.get("_units", 3.0)
                    if term_units + course_units > unit_cap:
                        continue
                    term_units += course_units
                    taken_codes.add(course["code"])
                    dept = course.get("department", "")
                    dept_counts[dept] = dept_counts.get(dept, 0) + 1

                    # Grade from TOP4-specific distribution
                    grading = course.get("grading", "")
                    if "Pass/No Pass Only" in grading:
                        grade = rng.choices(list(PNP_DIST.keys()), weights=list(PNP_DIST.values()), k=1)[0]
                        status = "Completed" if grade == "P" else "Not Passed"
                    else:
                        grades = top4_data.get(chosen_top4, {}).get("grades", DEFAULT_GRADES)
                        g_labels = list(grades.keys())
                        g_weights = list(grades.values())
                        grade = rng.choices(g_labels, weights=g_weights, k=1)[0]
                        status = "Withdrawn" if grade == "W" else "Completed"

                else:
                    # Fallback: flat course selection
                    available = [c for c in flat_courses if c["code"] not in taken_codes]
                    if not available:
                        continue
                    course = rng.choices(available, k=1)[0]
                    course_units = course.get("_units", 3.0)
                    if term_units + course_units > unit_cap:
                        continue
                    term_units += course_units
                    taken_codes.add(course["code"])
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

    # Compute stats
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
        top4_to_dept=top4_to_dept if top4_cal else {},
    )

    logger.info(
        f"Generated {stats.students_generated} students, "
        f"{stats.enrollments_created} enrollments, "
        f"success rate: {stats.success_rate:.1%}, "
        f"avg courses/student: {stats.avg_courses_per_student:.1f}"
    )

    # Validation: compare against TOP4 calibration
    if top4_cal:
        target_success = sum(
            sum(d["grades"].get(g, 0) for g in success_grades) * d["enrollment"]
            for d in top4_data.values()
        ) / sum(d["enrollment"] for d in top4_data.values()) if top4_data else 0
        diff = abs(stats.success_rate - target_success)
        logger.info(
            f"Calibration check — success rate: "
            f"synthetic={stats.success_rate:.1%}, "
            f"target={target_success:.1%}, "
            f"diff={diff:.1%}"
        )

    return students, stats


# ── Neo4j loader ───────────────────────────────────────────────────────────────

BATCH_SIZE = 500


def load_students(driver: Driver, institution: str, students: List[GeneratedStudent], top4_to_dept: Optional[Dict[str, str]] = None) -> int:
    """Load generated students into Neo4j. Full replace strategy."""
    with driver.session() as session:
        # Clear existing students in batches
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

        # Batch create students and enrollments
        batch = []
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

        # Materialize Student -[HAS_SKILL]-> Skill from completed enrollments
        result = session.run("""
            MATCH (st:Student)-[e:ENROLLED_IN]->(c:Course)-[:DEVELOPS]->(s:Skill)
            WHERE e.status = 'Completed'
            MERGE (st)-[:HAS_SKILL]->(s)
            RETURN count(*) AS created
        """)
        skills_created = result.single()["created"]
        logger.info(f"Materialized {skills_created} HAS_SKILL relationships")

        # Use the authoritative TOP4 → department mapping from course pools
        dept_lookup = top4_to_dept or {}

        # Materialize gpa, primary_focus, courses_completed on Student nodes
        logger.info("Materializing derived student fields (gpa, primary_focus, courses_completed)...")
        student_records = session.run("""
            MATCH (st:Student)-[e:ENROLLED_IN]->(c:Course {college: $inst})
            WITH st, collect({department: c.department, grade: e.grade, status: e.status}) AS enrollments
            RETURN st.uuid AS uuid, enrollments
        """, inst=institution).data()

        # Build uuid → primary_top4 lookup
        uuid_to_top4 = {s.uuid: s.primary_top4 for s in students}

        from ontology.utils import compute_gpa, compute_primary_focus
        field_batch = []
        for rec in student_records:
            enrollments = rec["enrollments"]
            completed = [e for e in enrollments if e.get("status") == "Completed"]
            grades = [e["grade"] for e in completed if e.get("grade")]

            # Primary focus from declared TOP4, fallback to enrollment-derived
            student_top4 = uuid_to_top4.get(rec["uuid"], "")
            primary_focus = dept_lookup.get(student_top4, "") or compute_primary_focus(enrollments)

            field_batch.append({
                "uuid": rec["uuid"],
                "gpa": compute_gpa(grades),
                "primary_focus": primary_focus,
                "courses_completed": len(completed),
            })

        for i in range(0, len(field_batch), 500):
            batch = field_batch[i : i + 500]
            session.run("""
                UNWIND $batch AS row
                MATCH (s:Student {uuid: row.uuid})
                SET s.gpa = row.gpa,
                    s.primary_focus = row.primary_focus,
                    s.courses_completed = row.courses_completed
            """, batch=batch)

        logger.info(f"Materialized derived fields on {len(field_batch)} students")

        return loaded


def _write_batch(session, institution: str, batch: List[dict]):
    """Write a batch of enrollments to Neo4j."""
    session.run(
        """
        UNWIND $batch AS row
        MERGE (s:Student {uuid: row.uuid})
        WITH s, row
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

    load_students(driver, institution_name, students, top4_to_dept=stats.top4_to_dept)
    return stats
