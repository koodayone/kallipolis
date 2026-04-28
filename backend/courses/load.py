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

from ontology.mcf_lookup import lookup_top6_per_course
from ontology.prepares_for import materialize_prepares_for
from ontology.crosswalks import is_cte_top6
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
    courses_with_top_code: int = 0
    prepares_for_edges_created: int = 0


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

    # ── Set Course.top_code from MCF (per-course TOP6) ────────────────────
    # The Master Course File is the Chancellor's-Office authoritative
    # course-to-TOP6 assignment (one TOP per course per college). Storing
    # it as a property on Course nodes is the precondition for
    # materialize_prepares_for, which derives Course→Occupation edges
    # from this property + the TOP6→SOC crosswalk. Idempotent via SET.
    code_to_top6 = lookup_top6_per_course(
        [c.get("code", "").strip() for c in courses if c.get("code")],
        config.name,
    )
    # Build a single batch with both top_code (where MCF has a value) and
    # is_cte (computed for every course). is_cte uses set membership in the
    # PCAH "TOP Codes to Sectors" file — the authoritative institutional
    # definition of CTE scope; see ontology.crosswalks.is_cte_top6.
    course_meta_batch = [
        {
            "code": code,
            "top_code": top6 or "",
            "is_cte": is_cte_top6(top6),
        }
        for code, top6 in code_to_top6.items()
    ]
    stats.courses_with_top_code = sum(1 for r in course_meta_batch if r["top_code"])
    if course_meta_batch:
        with driver.session() as session:
            # Two SET operations so courses without a TOP6 still get is_cte=false
            # (set unconditionally) without overwriting top_code with empty string.
            session.run(
                """
                UNWIND $batch AS row
                MATCH (c:Course {code: row.code, college: $college})
                SET c.is_cte = row.is_cte
                """,
                batch=course_meta_batch,
                college=config.name,
            )
            session.run(
                """
                UNWIND $batch AS row
                MATCH (c:Course {code: row.code, college: $college})
                WHERE row.top_code <> ''
                SET c.top_code = row.top_code
                """,
                batch=course_meta_batch,
                college=config.name,
            )

    # ── Stale edge + orphan cleanup ───────────────────────────────────────
    # The loader MERGEs nodes but is additive on relationships — it never
    # deletes old CONTAINS or OFFERS edges. When Stage 2.5 renames a
    # department (e.g., "Dance (DANC)" → "Dance") the Course node's
    # `department` property updates in place, but the old CONTAINS edge
    # from the stale "Dance (DANC)" Department node to that Course is
    # still there, which keeps the stale Department from being detected
    # as an orphan. This three-step sweep repairs the drift on every
    # load:
    #   1. Drop CONTAINS edges where Department.name disagrees with the
    #      Course's current `department` property (for this college's
    #      courses only — other colleges' edges are out of scope).
    #   2. Drop OFFERS edges from this College to any Department that no
    #      longer has courses from this college.
    #   3. DETACH DELETE any Department now left with no CONTAINS-out
    #      edges at all (globally — safe because step 1 was college-scoped
    #      but orphan status is a graph-wide property).
    #
    # The graph-state correctness this provides matters more than the
    # per-load cost: the Department catalog displayed in the atlas UI is
    # derived directly from these edges, and stale names are exactly the
    # fragmentation bug Stage 2.5 exists to fix.
    with driver.session() as session:
        stale_contains = session.run(
            """
            MATCH (col:College {name: $inst_name})
            MATCH (c:Course {college: col.name})
            MATCH (d:Department)-[rel:CONTAINS]->(c)
            WHERE d.name <> c.department
            DELETE rel
            RETURN count(rel) AS n
            """,
            inst_name=config.name,
        ).single()["n"]

        stale_offers = session.run(
            """
            MATCH (col:College {name: $inst_name})-[rel:OFFERS]->(d:Department)
            WHERE NOT EXISTS { MATCH (d)-[:CONTAINS]->(:Course {college: col.name}) }
            DELETE rel
            RETURN count(rel) AS n
            """,
            inst_name=config.name,
        ).single()["n"]

        orphans = session.run(
            """
            MATCH (d:Department)
            WHERE NOT (d)-[:CONTAINS]->(:Course)
            DETACH DELETE d
            RETURN count(d) AS n
            """
        ).single()["n"]

        if stale_contains or stale_offers or orphans:
            logger.info(
                "Department cleanup: %d stale CONTAINS edge(s), "
                "%d stale OFFERS edge(s), %d orphan Department node(s) removed",
                stale_contains,
                stale_offers,
                orphans,
            )

    # ── Materialize PREPARES_FOR edges from Course.top_code ──────────────
    # Course→Occupation gating used by partnerships replaces the prior
    # skills-overlap matching. Depends on (a) Course.top_code being set
    # (above) and (b) Occupation nodes existing (created by
    # occupations/load_industry). When Occupation nodes are missing the
    # call writes zero edges and logs the gap rather than failing — the
    # college load remains self-sufficient.
    try:
        prepares_stats = materialize_prepares_for(driver, config.name)
        stats.prepares_for_edges_created = prepares_stats["edges_created"]
    except Exception as e:
        # The crosswalk depends on external CSV files (cc_dataset). On
        # dev machines without that directory, log and continue rather
        # than fail the whole course load.
        logger.warning(
            f"materialize_prepares_for failed for {config.name}: {e}; "
            f"PREPARES_FOR edges not written"
        )

    logger.info(
        f"Loaded {config.name}: "
        f"{stats.courses_created} courses, "
        f"{stats.departments_created} departments, "
        f"{stats.courses_with_top_code} courses tagged with TOP6, "
        f"{stats.prepares_for_edges_created} PREPARES_FOR edges"
    )
    return stats
