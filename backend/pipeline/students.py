"""
Stage 4: Synthetic student data generator.

Generates anonymous students with realistic aggregate distributions:
enrollment by department, course popularity, grade distributions,
retention curves, and department-affine skill profiles.

Usage:
    from pipeline.students import generate_and_load_students
    stats = generate_and_load_students("foothill", num_students=3000, seed=42)
"""

from __future__ import annotations

import json
import logging
import math
import os
import random as _random_mod
import re
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Tuple, Optional

from neo4j import Driver

logger = logging.getLogger(__name__)

# ── Deterministic UUID namespace ───────────────────────────────────────────────
NAMESPACE = uuid.UUID("a1b2c3d4-e5f6-7890-abcd-ef1234567890")

# ── Default parameters (Foothill College, overridable per college) ─────────────

DEFAULT_STUDENT_COUNT = 3000
FT_RATIO = 0.31
RETENTION_RATE = 0.67
SUMMER_ENROLLMENT_RATE = 0.15
PRIMARY_DEPT_AFFINITY = 0.65
RETAKE_RATE = 0.05
ACADEMIC_YEARS = [2022, 2023, 2024]

# Grade distribution (sums to 1.0)
GRADE_DIST = {"A": 0.28, "B": 0.26, "C": 0.17, "D": 0.05, "F": 0.04, "W": 0.12, "P": 0.08}
GRADE_CHOICES = list(GRADE_DIST.keys())
GRADE_WEIGHTS = list(GRADE_DIST.values())

# Pass/No Pass grade distribution
PNP_DIST = {"P": 0.85, "NP": 0.15}

# Course load per term (number of courses)
PT_LOADS = [1, 2, 3]
PT_LOAD_WEIGHTS = [0.10, 0.40, 0.50]
FT_LOADS = [4, 5, 6]
FT_LOAD_WEIGHTS = [0.55, 0.35, 0.10]

# Unit caps per quarter
PT_UNIT_CAP = 11.0
FT_UNIT_CAP = 20.0

# Starting term distribution (most start in Fall)
START_TERM_WEIGHTS = {"Fall": 0.60, "Winter": 0.15, "Spring": 0.20, "Summer": 0.05}

# Boost multipliers for known high-enrollment departments
HIGH_ENROLLMENT_BOOST = {
    "Computer Science": 2.5,
    "Mathematics": 2.0,
    "English": 2.5,
    "Biology": 1.8,
    "Business": 2.0,
    "Psychology": 1.5,
    "Economics": 1.5,
    "Communication Studies": 1.5,
    "Chemistry": 1.3,
    "Kinesiology": 1.3,
    "History": 1.2,
    "Sociology": 1.2,
}

# Course number → popularity weight
COURSE_NUM_WEIGHTS = [(1, 9, 10), (10, 49, 5), (50, 99, 3), (100, 199, 2), (200, 9999, 1)]

# Department affinity clusters
DEPT_CLUSTERS = {
    "Computer Science": ["Computer Science", "Mathematics", "Engineering"],
    "Mathematics": ["Mathematics", "Computer Science", "Physics", "Statistics"],
    "Engineering": ["Engineering", "Computer Science", "Mathematics", "Physics"],
    "Business": ["Business", "Accounting", "Economics"],
    "Accounting": ["Accounting", "Business", "Economics"],
    "Economics": ["Economics", "Business", "Mathematics"],
    "Respiratory Therapy": ["Respiratory Therapy", "Biology", "Allied Health Sciences"],
    "Dental Hygiene": ["Dental Hygiene", "Dental Assisting", "Biology", "Allied Health Sciences"],
    "Dental Assisting": ["Dental Assisting", "Dental Hygiene", "Allied Health Sciences"],
    "Radiologic Technology": ["Radiologic Technology", "Biology", "Allied Health Sciences"],
    "Diagnostic Medical Sonography": ["Diagnostic Medical Sonography", "Biology", "Allied Health Sciences"],
    "Allied Health Sciences": ["Allied Health Sciences", "Biology", "Respiratory Therapy"],
    "Pharmacy Technology": ["Pharmacy Technology", "Biology", "Chemistry", "Allied Health Sciences"],
    "Emergency Medical Services (EMT/EMR/Paramedic)": ["Emergency Medical Services (EMT/EMR/Paramedic)", "Allied Health Sciences", "Biology"],
    "Psychology": ["Psychology", "Sociology", "Anthropology", "Child Development"],
    "Sociology": ["Sociology", "Psychology", "Anthropology", "Ethnic Studies"],
    "Anthropology": ["Anthropology", "Sociology", "History", "Geography"],
    "Political Science": ["Political Science", "History", "Economics", "Global Studies"],
    "History": ["History", "Political Science", "Humanities", "Ethnic Studies"],
    "Physics": ["Physics", "Mathematics", "Chemistry", "Astronomy", "Engineering"],
    "Chemistry": ["Chemistry", "Biology", "Physics", "Mathematics"],
    "Biology": ["Biology", "Chemistry", "Environmental Horticulture & Design"],
    "Astronomy": ["Astronomy", "Physics", "Mathematics"],
    "English": ["English", "Humanities", "Creative Writing", "Communication Studies"],
    "Humanities": ["Humanities", "English", "Philosophy", "History"],
    "Philosophy": ["Philosophy", "Humanities", "English"],
    "Communication Studies": ["Communication Studies", "English", "Media Studies", "Journalism"],
    "Media Studies": ["Media Studies", "Communication Studies", "Photography", "Music Technology"],
    "Art": ["Art", "Photography", "Graphics & Interactive Design"],
    "Photography": ["Photography", "Art", "Graphics & Interactive Design"],
    "Theatre Arts": ["Theatre Arts", "Dance", "Music", "English"],
    "Music": ["Music", "Music Technology", "Theatre Arts"],
    "Music Technology": ["Music Technology", "Music", "Computer Science"],
    "Dance": ["Dance", "Theatre Arts", "Kinesiology"],
    "Child Development": ["Child Development", "Psychology", "Education"],
}

# Non-credit department prefixes to exclude
NON_CREDIT_PREFIXES = ["Non-Credit"]


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


# ── Helpers ────────────────────────────────────────────────────────────────────


def _parse_course_number(code: str) -> int:
    """Extract numeric portion from course code. 'C S 1A' → 1, 'MATH 105' → 105."""
    match = re.search(r"(\d+)", code)
    return int(match.group(1)) if match else 50


def _course_popularity(code: str) -> float:
    """Return popularity weight based on course number."""
    num = _parse_course_number(code)
    for lo, hi, weight in COURSE_NUM_WEIGHTS:
        if lo <= num <= hi:
            return float(weight)
    return 1.0


def _is_honors_variant(code: str, base_code: str) -> bool:
    """Check if code is an honors variant of base_code. 'MATH 1AH' vs 'MATH 1A'."""
    return code != base_code and code.rstrip("H").rstrip("P") == base_code


def _parse_units(units_str: str) -> float:
    """Parse units string to float. '4.5' → 4.5, '1-2' → 1.5."""
    if not units_str:
        return 0.0
    try:
        if "-" in units_str:
            parts = units_str.split("-")
            return (float(parts[0]) + float(parts[1])) / 2
        return float(units_str.split()[0])
    except (ValueError, IndexError):
        return 0.0


def _build_term_sequence() -> List[str]:
    """Build ordered list of term strings."""
    terms = []
    for year in ACADEMIC_YEARS:
        terms.append(f"{year}-Fall")
        terms.append(f"{year}-Winter")
        # Winter is in the next calendar year for quarter system
        terms.append(f"{year + 1}-Spring")
    return terms


# ── Core generation ────────────────────────────────────────────────────────────


def _prepare_catalog(courses: List[dict]) -> Tuple[
    Dict[str, List[dict]],  # dept → courses
    Dict[str, float],  # dept → enrollment weight
    List[dict],  # GE courses
]:
    """Prepare course catalog for enrollment generation."""
    # Filter to credit-bearing courses only
    credit_courses = []
    for c in courses:
        dept = c.get("department", "")
        if any(dept.startswith(prefix) for prefix in NON_CREDIT_PREFIXES):
            continue
        units = _parse_units(c.get("units", "0"))
        if units <= 0:
            continue
        c["_units"] = units
        c["_popularity"] = _course_popularity(c.get("code", ""))
        credit_courses.append(c)

    logger.info(f"Credit-bearing courses: {len(credit_courses)} / {len(courses)}")

    # Group by department
    dept_courses: Dict[str, List[dict]] = {}
    for c in credit_courses:
        dept = c["department"]
        dept_courses.setdefault(dept, []).append(c)

    # Compute department enrollment weights
    dept_weights: Dict[str, float] = {}
    for dept, courses_list in dept_courses.items():
        boost = HIGH_ENROLLMENT_BOOST.get(dept, 1.0)
        dept_weights[dept] = math.sqrt(len(courses_list)) * boost

    # Normalize
    total = sum(dept_weights.values())
    for dept in dept_weights:
        dept_weights[dept] /= total

    # Identify GE courses (transferable)
    ge_courses = [c for c in credit_courses if c.get("transfer_status") in ("CSU/UC", "CSU")]

    logger.info(f"Departments: {len(dept_courses)}, GE courses: {len(ge_courses)}")
    return dept_courses, dept_weights, ge_courses


def _select_course(
    rng: _random_mod.Random,
    course_pool: List[dict],
    taken_codes: set,
    allow_retake: bool = False,
) -> Optional[dict]:
    """Select a course from pool by popularity weight, avoiding duplicates."""
    available = []
    weights = []
    for c in course_pool:
        code = c["code"]
        base = code.rstrip("H").rstrip("P")
        if base in taken_codes and not (allow_retake and rng.random() < RETAKE_RATE):
            continue
        available.append(c)
        weights.append(c["_popularity"])

    if not available:
        return None

    return rng.choices(available, weights=weights, k=1)[0]


def generate_students(
    college_key: str,
    courses: List[dict],
    num_students: int = DEFAULT_STUDENT_COUNT,
    seed: int = 42,
    config: Optional[dict] = None,
) -> Tuple[List[GeneratedStudent], GenerationStats]:
    """
    Generate synthetic students with realistic distributions.

    Args:
        college_key: College identifier (e.g., "foothill")
        courses: Enriched course data (from cached JSON)
        num_students: Number of students to generate
        seed: Random seed for determinism
        config: Optional per-college overrides

    Returns:
        Tuple of (students list, generation stats)
    """
    cfg = config or {}
    ft_ratio = cfg.get("ft_ratio", FT_RATIO)
    retention = cfg.get("retention_rate", RETENTION_RATE)
    dept_affinity = cfg.get("dept_affinity", PRIMARY_DEPT_AFFINITY)

    rng = _random_mod.Random(seed)
    dept_courses, dept_weights, ge_courses = _prepare_catalog(courses)

    dept_names = list(dept_weights.keys())
    dept_probs = list(dept_weights.values())
    all_terms = _build_term_sequence()

    start_terms_list = list(START_TERM_WEIGHTS.keys())
    start_terms_weights = list(START_TERM_WEIGHTS.values())

    students: List[GeneratedStudent] = []
    total_enrollments = 0
    grade_counts: Dict[str, int] = {}
    depts_seen: set = set()

    for i in range(num_students):
        student_uuid = str(uuid.uuid5(NAMESPACE, f"{college_key}-student-{i}"))
        student = GeneratedStudent(uuid=student_uuid)

        # Profile
        is_ft = rng.random() < ft_ratio
        primary_dept = rng.choices(dept_names, weights=dept_probs, k=1)[0]
        start_season = rng.choices(start_terms_list, weights=start_terms_weights, k=1)[0]

        # Find starting term index
        start_idx = 0
        for idx, term in enumerate(all_terms):
            if term.endswith(start_season):
                start_idx = idx
                break

        # Determine how many terms this student persists
        max_terms = 1
        while max_terms < len(all_terms) - start_idx:
            if rng.random() > retention:
                break
            max_terms += 1

        # Build cluster pool for this student's primary department
        cluster_depts = DEPT_CLUSTERS.get(primary_dept, [primary_dept])
        cluster_courses = []
        for dept in cluster_depts:
            cluster_courses.extend(dept_courses.get(dept, []))

        taken_codes: set = set()
        unit_cap = FT_UNIT_CAP if is_ft else PT_UNIT_CAP

        active_terms = all_terms[start_idx: start_idx + max_terms]
        # Filter out summer terms probabilistically
        active_terms = [
            t for t in active_terms
            if not t.endswith("-Summer") or rng.random() < SUMMER_ENROLLMENT_RATE
        ]

        for term in active_terms:
            # Determine course load
            if is_ft:
                num_courses = rng.choices(FT_LOADS, weights=FT_LOAD_WEIGHTS, k=1)[0]
            else:
                num_courses = rng.choices(PT_LOADS, weights=PT_LOAD_WEIGHTS, k=1)[0]

            term_units = 0.0
            for _ in range(num_courses):
                # Decide: primary cluster or GE
                if rng.random() < dept_affinity and cluster_courses:
                    course = _select_course(rng, cluster_courses, taken_codes, allow_retake=True)
                else:
                    course = _select_course(rng, ge_courses, taken_codes)

                if course is None:
                    continue

                # Check unit cap
                course_units = course["_units"]
                if term_units + course_units > unit_cap:
                    continue

                term_units += course_units
                code = course["code"]
                base_code = code.rstrip("H").rstrip("P")
                taken_codes.add(base_code)

                # Assign grade
                grading = course.get("grading", "")
                if "Pass/No Pass Only" in grading:
                    grade = rng.choices(
                        list(PNP_DIST.keys()),
                        weights=list(PNP_DIST.values()),
                        k=1
                    )[0]
                    status = "Completed" if grade == "P" else "Not Passed"
                else:
                    grade = rng.choices(GRADE_CHOICES, weights=GRADE_WEIGHTS, k=1)[0]
                    if grade == "W":
                        status = "Withdrawn"
                    elif grade == "P":
                        status = "Completed"
                    else:
                        status = "Completed"

                enrollment = Enrollment(
                    course_code=code,
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
            for g in GRADE_CHOICES + ["NP"]
        },
    )

    logger.info(
        f"Generated {stats.students_generated} students, "
        f"{stats.enrollments_created} enrollments, "
        f"success rate: {stats.success_rate:.1%}, "
        f"avg courses/student: {stats.avg_courses_per_student:.1f}"
    )
    return students, stats


# ── Neo4j loader ───────────────────────────────────────────────────────────────

BATCH_SIZE = 500


def load_students(driver: Driver, institution: str, students: List[GeneratedStudent]) -> int:
    """
    Load generated students into Neo4j. Replaces existing synthetic students
    for the institution (full replace strategy for synthetic data).
    """
    with driver.session() as session:
        # Clear existing students for this institution
        result = session.run(
            "MATCH (s:Student)-[:ENROLLED_IN]->(c:Course {institution: $inst}) "
            "DETACH DELETE s RETURN count(s) as cnt",
            inst=institution,
        )
        deleted = result.single()["cnt"]
        if deleted:
            logger.info(f"Cleared {deleted} existing students for {institution}")

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
        return loaded


def _write_batch(session, institution: str, batch: List[dict]):
    """Write a batch of enrollments to Neo4j."""
    session.run(
        """
        UNWIND $batch AS row
        MERGE (s:Student {uuid: row.uuid})
        WITH s, row
        MATCH (c:Course {code: row.course_code, institution: $inst})
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
    num_students: int = DEFAULT_STUDENT_COUNT,
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

    load_students(driver, institution_name, students)
    return stats
