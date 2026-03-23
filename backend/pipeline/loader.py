"""
Stage 3: Neo4j loader.

Takes enriched course data and persists it into the Neo4j graph database,
creating Institution, Program, Department, and Course nodes with relationships.

Usage:
    from pipeline.loader import load_college
    stats = load_college(driver, college_config, enriched_courses)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import List, Optional

from neo4j import Driver

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
    programs_created: int = 0
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
        # Drop the old single-field constraint and add code-based one
        try:
            session.run("DROP CONSTRAINT course_name IF EXISTS")
        except Exception:
            pass
        session.run(
            "CREATE CONSTRAINT course_code_inst IF NOT EXISTS "
            "FOR (c:Course) REQUIRE (c.code, c.institution) IS UNIQUE"
        )

        # ── Institution & Region ──────────────────────────────────────────
        session.run(
            """
            MERGE (r:LaborMarketRegion {name: $region})
            MERGE (i:Institution {name: $name})
            ON CREATE SET i.city = $city, i.state = $state, i.region = $region
            ON MATCH SET i.city = $city, i.state = $state, i.region = $region
            MERGE (i)-[:LOCATED_IN]->(r)
            """,
            name=config.name,
            region=config.region,
            city=config.city,
            state=config.state,
        )

        # ── Collect unique departments and programs ───────────────────────
        departments: set[str] = set()
        programs: set[str] = set()

        for course in courses:
            dept = course.get("department", "").strip()
            if dept:
                departments.add(dept)
            if dept:
                programs.add(dept)

        # ── Create Departments ────────────────────────────────────────────
        for dept_name in departments:
            session.run(
                "MERGE (d:Department {name: $name}) RETURN d",
                name=dept_name,
            )
            stats.departments_created += 1

        # ── Create Programs & link to Institution ─────────────────────────
        for prog_name in programs:
            session.run(
                """
                MATCH (i:Institution {name: $inst_name})
                MERGE (p:Program {name: $prog_name})
                MERGE (i)-[:OFFERS]->(p)
                """,
                inst_name=config.name,
                prog_name=prog_name,
            )
            stats.programs_created += 1

        # ── Create/Update Courses ─────────────────────────────────────────
        for course in courses:
            code = course.get("code", "").strip()
            name = course.get("name", "").strip()
            dept = course.get("department", "").strip()

            if not code or not name:
                continue

            # MERGE on (code, institution) — unique per college
            result = session.run(
                """
                MERGE (c:Course {code: $code, institution: $institution})
                ON CREATE SET
                    c.name = $name,
                    c.department = $department,
                    c.program = $program,
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
                    c.program = $program,
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
                program=dept,
                units=course.get("units", ""),
                description=course.get("description", ""),
                prerequisites=course.get("prerequisites", ""),
                transfer_status=course.get("transfer_status", ""),
                learning_outcomes=course.get("learning_outcomes", []),
                course_objectives=course.get("course_objectives", []),
                skill_mappings=course.get("skill_mappings", []),
                institution=config.name,
                url=course.get("url", ""),
            )
            stats.courses_created += 1

            # Link Course → Department
            if dept:
                session.run(
                    """
                    MATCH (d:Department {name: $dept})
                    MATCH (c:Course {code: $code, institution: $inst})
                    MERGE (d)-[:CONTAINS]->(c)
                    """,
                    dept=dept,
                    code=code,
                    inst=config.name,
                )

            # Link Course → Program
            if dept:
                session.run(
                    """
                    MATCH (p:Program {name: $prog})
                    MATCH (c:Course {code: $code, institution: $inst})
                    MERGE (p)-[:CONTAINS]->(c)
                    """,
                    prog=dept,
                    code=code,
                    inst=config.name,
                    name=name,
                )
                stats.relationships_created += 1

    logger.info(
        f"Loaded {config.name}: "
        f"{stats.courses_created} courses, "
        f"{stats.departments_created} departments, "
        f"{stats.programs_created} programs"
    )
    return stats
