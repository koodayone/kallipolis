"""
Stage 3: Neo4j loader.

Takes enriched course data and persists it into the Neo4j graph database,
creating College, Department, and Course nodes with relationships.

Usage:
    from courses.load import load_college
    stats = load_college(driver, college_config, enriched_courses)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import List, Optional

from neo4j import Driver

from ontology.regions import ensure_college_region_link
from ontology.skills import UNIFIED_TAXONOMY

logger = logging.getLogger(__name__)


@dataclass
class CollegeConfig:
    """Configuration for a college to load into Neo4j."""

    name: str
    region: str
    city: str
    state: str = "California"


@dataclass
class LoadStats:
    """Statistics from a load operation."""

    institution: str
    departments_created: int = 0
    courses_created: int = 0
    courses_updated: int = 0
    relationships_created: int = 0


def load_college(
    driver: Driver,
    config: CollegeConfig,
    courses: list[dict],
) -> LoadStats:
    """
    Load enriched course data for a single college into Neo4j.

    All operations are idempotent via MERGE. Re-running updates existing
    nodes rather than creating duplicates.
    """
    stats = LoadStats(institution=config.name)

    with driver.session() as session:
        # ── Update constraints for multi-college support ──────────────────
        for legacy in ["course_name", "course_code_inst"]:
            try:
                session.run(f"DROP CONSTRAINT {legacy} IF EXISTS")
            except Exception:
                pass
        session.run(
            "CREATE CONSTRAINT course_code_college IF NOT EXISTS "
            "FOR (c:Course) REQUIRE (c.code, c.college) IS UNIQUE"
        )

        # ── College ────────────────────────────────────────────────────────
        # College.region is a scalar display string for informational use.
        # The load-bearing (College)-[:IN_MARKET]->(Region) edge is
        # written after this session closes via ensure_college_region_link
        # so that loading a college is self-sufficient for the
        # partnership traversal.
        session.run(
            """
            MERGE (col:College {name: $name})
            ON CREATE SET col.city = $city, col.state = $state, col.region = $region
            ON MATCH SET col.city = $city, col.state = $state, col.region = $region
            """,
            name=config.name,
            region=config.region,
            city=config.city,
            state=config.state,
        )

        # ── Collect unique departments ────────────────────────────────────
        departments: set[str] = set()

        for course in courses:
            dept = course.get("department", "").strip()
            if dept:
                departments.add(dept)

        # ── Create Departments & link to College ──────────────────────────
        for dept_name in departments:
            session.run(
                """
                MATCH (col:College {name: $inst_name})
                MERGE (d:Department {name: $dept_name})
                MERGE (col)-[:OFFERS]->(d)
                """,
                inst_name=config.name,
                dept_name=dept_name,
            )
            stats.departments_created += 1

        # ── Create/Update Courses ─────────────────────────────────────────
        for course in courses:
            code = course.get("code", "").strip()
            name = course.get("name", "").strip()
            dept = course.get("department", "").strip()

            if not code or not name:
                continue

            # MERGE on (code, institution) — unique per college
            session.run(
                """
                MERGE (c:Course {code: $code, college: $college})
                ON CREATE SET
                    c.name = $name,
                    c.department = $department,
                    c.units = $units,
                    c.description = $description,
                    c.prerequisites = $prerequisites,
                    c.transfer_status = $transfer_status,
                    c.learning_outcomes = $learning_outcomes,
                    c.course_objectives = $course_objectives,
                    c.skill_mappings = $skill_mappings,
                    c.url = $url
                ON MATCH SET
                    c.name = $name,
                    c.department = $department,
                    c.units = $units,
                    c.description = $description,
                    c.prerequisites = $prerequisites,
                    c.transfer_status = $transfer_status,
                    c.learning_outcomes = $learning_outcomes,
                    c.course_objectives = $course_objectives,
                    c.skill_mappings = $skill_mappings,
                    c.url = $url
                RETURN c
                """,
                name=name,
                code=code,
                department=dept,
                units=course.get("units", ""),
                description=course.get("description", ""),
                prerequisites=course.get("prerequisites", ""),
                transfer_status=course.get("transfer_status", ""),
                learning_outcomes=course.get("learning_outcomes", []),
                course_objectives=course.get("course_objectives", []),
                skill_mappings=course.get("skill_mappings", []),
                college=config.name,
                url=course.get("url", ""),
            )
            stats.courses_created += 1

            # Link Course → Department
            if dept:
                session.run(
                    """
                    MATCH (d:Department {name: $dept})
                    MATCH (c:Course {code: $code, college: $inst})
                    MERGE (d)-[:CONTAINS]->(c)
                    """,
                    dept=dept,
                    code=code,
                    inst=config.name,
                )
                stats.relationships_created += 1

            # Link Course → Skill
            for skill_name in course.get("skill_mappings", []):
                if skill_name not in UNIFIED_TAXONOMY:
                    logger.warning(f"Off-taxonomy skill skipped: '{skill_name}' on {code}")
                    continue
                session.run(
                    """
                    MERGE (s:Skill {name: $skill_name})
                    WITH s
                    MATCH (c:Course {code: $code, college: $inst})
                    MERGE (c)-[:DEVELOPS]->(s)
                    """,
                    skill_name=skill_name,
                    code=code,
                    inst=config.name,
                )
                stats.relationships_created += 1

    # Link the College to its COE Region. This helper owns the MERGE
    # and is also called from occupations/load.py::load_industry, so
    # running either loader produces the edge consistently.
    ensure_college_region_link(driver, config.name)

    logger.info(
        f"Loaded {config.name}: "
        f"{stats.courses_created} courses, "
        f"{stats.departments_created} departments"
    )
    return stats
