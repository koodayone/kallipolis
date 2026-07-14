import os
import logging
from neo4j import GraphDatabase

from ontology.timing import TimedDriver

logger = logging.getLogger(__name__)

_driver = None


def get_driver():
    global _driver
    if _driver is None:
        raw = GraphDatabase.driver(
            os.environ["NEO4J_URI"],
            auth=(os.environ["NEO4J_USERNAME"], os.environ["NEO4J_PASSWORD"]),
        )
        _driver = TimedDriver(raw) if os.environ.get("NEO4J_QUERY_TIMING", "1") != "0" else raw
    return _driver


def close_driver():
    global _driver
    if _driver is not None:
        _driver.close()
        _driver = None


def _migrate_curriculum_to_course(session):
    """Idempotent migration: rename Curriculum→Course, create Department nodes."""
    # Check if any Curriculum nodes exist
    count = session.run("MATCH (n:Curriculum) RETURN count(n) AS cnt").single()["cnt"]
    if count == 0:
        return  # Already migrated or fresh DB

    logger.info(f"Migrating {count} Curriculum nodes to Course nodes...")

    # Drop old constraint if it exists
    try:
        session.run("DROP CONSTRAINT curriculum_name IF EXISTS")
    except Exception:
        pass

    # Rename labels
    session.run("MATCH (c:Curriculum) REMOVE c:Curriculum SET c:Course")

    # Create Department nodes from distinct department values
    session.run("""
        MATCH (c:Course)
        WHERE c.department IS NOT NULL
        WITH DISTINCT c.department AS dept
        MERGE (d:Department {name: dept})
    """)

    # Create Department→Course relationships
    session.run("""
        MATCH (c:Course)
        WHERE c.department IS NOT NULL
        MATCH (d:Department {name: c.department})
        MERGE (d)-[:CONTAINS]->(c)
    """)

    # Verify the migration produced Course nodes
    course_count = session.run(
        "MATCH (c:Course) RETURN count(c) AS cnt"
    ).single()["cnt"]
    logger.info(f"Migration complete. Courses: {course_count}")


def init_schema():
    driver = get_driver()
    with driver.session() as session:
        _migrate_curriculum_to_course(session)
        _create_constraints(session)
        empty = _is_empty(session)
    if empty:
        logger.info("Neo4j is empty. Run the ingestion pipeline to load college data:")
        logger.info("  python -m pipeline.run --college foothill")
        return
    logger.info("Neo4j already contains data.")
    # Ensure the institutional hierarchy (college → CCCCO district) that the
    # member×sector landscape engine aggregates over. Idempotent and cheap;
    # the region tier already rides on the IN_MARKET edge written at load time.
    from ontology.districts import load_college_districts

    load_college_districts(driver)


def _create_constraints(session):
    # Drop legacy single-field course name constraint (breaks with multi-college data)
    try:
        session.run("DROP CONSTRAINT course_name IF EXISTS")
    except Exception:
        pass

    # Drop legacy Program constraint
    try:
        session.run("DROP CONSTRAINT program_name IF EXISTS")
    except Exception:
        pass

    # Drop legacy Institution constraint
    try:
        session.run("DROP CONSTRAINT institution_name IF EXISTS")
    except Exception:
        pass

    # Drop stale constraints for removed node types
    for old in ["jobrole_title"]:
        try:
            session.run(f"DROP CONSTRAINT {old} IF EXISTS")
        except Exception:
            pass

    # Drop the legacy Skill constraint (the Skill abstraction was retired
    # when the TOP-SOC institutional crosswalk replaced it as the bridge
    # between curriculum and labor market).
    try:
        session.run("DROP CONSTRAINT skill_name IF EXISTS")
    except Exception:
        pass

    constraints = [
        "CREATE CONSTRAINT college_name IF NOT EXISTS FOR (n:College) REQUIRE n.name IS UNIQUE",
        "CREATE CONSTRAINT district_name IF NOT EXISTS FOR (n:District) REQUIRE n.name IS UNIQUE",
        "CREATE CONSTRAINT course_code_college IF NOT EXISTS FOR (n:Course) REQUIRE (n.code, n.college) IS UNIQUE",
        "CREATE CONSTRAINT department_name IF NOT EXISTS FOR (n:Department) REQUIRE n.name IS UNIQUE",
        "CREATE CONSTRAINT region_name IF NOT EXISTS FOR (n:Region) REQUIRE n.name IS UNIQUE",
        "CREATE CONSTRAINT occupation_soc IF NOT EXISTS FOR (n:Occupation) REQUIRE n.soc_code IS UNIQUE",
        "CREATE CONSTRAINT employer_name IF NOT EXISTS FOR (n:Employer) REQUIRE n.name IS UNIQUE",
        # Program: the TOP6 program, per-college (mirrors Course's (code, college)
        # compound key). AcademicYear / Term are shared time-dimension nodes that
        # award / enrollment measures hang off of (measure-on-edge, like DEMANDS).
        "CREATE CONSTRAINT program_college_top6 IF NOT EXISTS FOR (n:Program) REQUIRE (n.college, n.top6) IS UNIQUE",
        "CREATE CONSTRAINT academic_year IF NOT EXISTS FOR (n:AcademicYear) REQUIRE n.year IS UNIQUE",
        "CREATE CONSTRAINT term_label IF NOT EXISTS FOR (n:Term) REQUIRE n.term IS UNIQUE",
        # ProgramWageOutcome: a statewide, pooled graduate-wage cohort for a TOP6
        # program — one node per (top6, recipient_type), NOT per-college (the DataMart
        # wage export carries no college dimension). Every per-college Program of that
        # top6 shares the ONE node via HAS_WAGE_OUTCOME, so the statewide pooling is
        # visible in structure and no per-college wage precision is manufactured.
        "CREATE CONSTRAINT program_wage_outcome_top6_recipient IF NOT EXISTS FOR (n:ProgramWageOutcome) REQUIRE (n.top6, n.recipient_type) IS UNIQUE",
    ]
    for constraint in constraints:
        session.run(constraint)

    # Range indexes for non-unique properties used as predicate filters in
    # hot-path queries. Uniqueness constraints already auto-create indexes
    # for their target properties; this list is the additional non-unique
    # set.
    #
    # course_college: speeds the `MATCH (c:Course {college: $college})`
    # filter that appears in essentially every read endpoint and in
    # most LLM-generated queries (courses, employers, occupations,
    # partnerships, vocab resolver). The existing
    # `course_code_college` uniqueness constraint creates a composite
    # index keyed on (code, college); that index is only usable when
    # `code` is also bound. Filtering by college alone falls back to
    # NodeByLabelScan + property filter over all Course nodes
    # (~thousands per college × ~125 colleges in the full graph).
    # Adding a standalone RANGE index turns the per-college filter
    # into a NodeIndexSeek. Impact not yet measured; will be once the
    # neo4j_queries.jsonl instrumentation is deployed.
    indexes = [
        "CREATE INDEX course_college IF NOT EXISTS FOR (n:Course) ON (n.college)",
    ]
    for index in indexes:
        session.run(index)


def _is_empty(session) -> bool:
    result = session.run("MATCH (n:College) RETURN count(n) AS cnt")
    return result.single()["cnt"] == 0
