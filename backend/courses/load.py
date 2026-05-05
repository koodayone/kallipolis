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
from ontology.crosswalks import is_cte_top6, top_to_department_name
from ontology.regions import ensure_college_region_link

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

        # ── Resolve TOP6 first so `department` can be derived from it ─────
        # The Department a Course belongs to is sourced from the
        # Chancellor's Office Taxonomy of Programs Manual (TOP4 → name),
        # not from Gemini's catalog-section guess or a per-college
        # overlay. See `ontology.crosswalks.top_to_department_name` and
        # `ontology/data/top4_names.json` (parsed from the manual).
        # Courses without a MCF TOP6 (real MCF lag, ~5%) get
        # `department = ""` — the API layer filters them out of the
        # visible course list.
        code_to_top6 = lookup_top6_per_course(
            [c.get("code", "").strip() for c in courses if c.get("code")],
            config.name,
        )

        # The catalog-section header Gemini extracted is preserved on
        # `Course.catalog_section` for traceability; it is NOT used for
        # grouping or display.
        course_records = []
        for course in courses:
            code = course.get("code", "").strip()
            name = course.get("name", "").strip()
            if not code or not name:
                continue
            top6 = code_to_top6.get(code) or ""
            dept = top_to_department_name(top6) or ""
            course_records.append({
                "code": code,
                "name": name,
                "top_code": top6,
                "department": dept,
                "is_cte": is_cte_top6(top6) if top6 else False,
                "catalog_section": course.get("department", "").strip(),
                "units": course.get("units", ""),
                "description": course.get("description", ""),
                "prerequisites": course.get("prerequisites", ""),
                "transfer_status": course.get("transfer_status", ""),
                "learning_outcomes": course.get("learning_outcomes", []),
                "course_objectives": course.get("course_objectives", []),
                "url": course.get("url", ""),
            })

        # ── Create Departments & link to College ──────────────────────────
        departments = {r["department"] for r in course_records if r["department"]}
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

        # ── Create/Update Courses (single MERGE writes all properties) ────
        # All Course properties — including the manual-grounded
        # `department`, the `top_code` from MCF lookup, and the `is_cte`
        # flag from the PCAH TOP-to-Sectors mapping — are written in one
        # MERGE so the node is fully populated by the time the
        # CONTAINS edge to its Department node is created. `top_code` is
        # the empty string when MCF lookup returned None (real MCF lag);
        # callers that filter on it should test for "" and NULL alike.
        for r in course_records:
            session.run(
                """
                MERGE (c:Course {code: $code, college: $college})
                SET
                    c.name = $name,
                    c.department = $department,
                    c.catalog_section = $catalog_section,
                    c.top_code = $top_code,
                    c.is_cte = $is_cte,
                    c.units = $units,
                    c.description = $description,
                    c.prerequisites = $prerequisites,
                    c.transfer_status = $transfer_status,
                    c.learning_outcomes = $learning_outcomes,
                    c.course_objectives = $course_objectives,
                    c.url = $url
                """,
                name=r["name"],
                code=r["code"],
                department=r["department"],
                catalog_section=r["catalog_section"],
                top_code=r["top_code"],
                is_cte=r["is_cte"],
                units=r["units"],
                description=r["description"],
                prerequisites=r["prerequisites"],
                transfer_status=r["transfer_status"],
                learning_outcomes=r["learning_outcomes"],
                course_objectives=r["course_objectives"],
                college=config.name,
                url=r["url"],
            )
            stats.courses_created += 1
            if r["top_code"]:
                stats.courses_with_top_code += 1

            # Link Course → Department (only when the course has a TOP6
            # and therefore a manual-grounded department).
            if r["department"]:
                session.run(
                    """
                    MATCH (d:Department {name: $dept})
                    MATCH (c:Course {code: $code, college: $inst})
                    MERGE (d)-[:CONTAINS]->(c)
                    """,
                    dept=r["department"],
                    code=r["code"],
                    inst=config.name,
                )
                stats.relationships_created += 1

    # Link the College to its COE Region. This helper owns the MERGE
    # and is also called from occupations/load.py::load_industry, so
    # running either loader produces the edge consistently.
    ensure_college_region_link(driver, config.name)

    # ── Stale edge + orphan cleanup ───────────────────────────────────────
    # The loader MERGEs nodes but is additive on relationships — it never
    # deletes old CONTAINS or OFFERS edges. A course's `department`
    # property can change between loads (e.g., when its TOP6 is updated
    # by a fresh MCF, or when the Taxonomy of Programs Manual is
    # reissued), leaving a stale CONTAINS edge from the old Department
    # node to the Course. This three-step sweep repairs the drift on
    # every load:
    #   1. Drop CONTAINS edges where Department.name disagrees with the
    #      Course's current `department` property (for this college's
    #      courses only — other colleges' edges are out of scope).
    #   2. Drop OFFERS edges from this College to any Department that no
    #      longer has courses from this college.
    #   3. DETACH DELETE any Department now left with no CONTAINS-out
    #      edges at all (globally — safe because step 1 was college-scoped
    #      but orphan status is a graph-wide property).
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
