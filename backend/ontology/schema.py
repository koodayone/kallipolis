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

    # Verify student enrollments still resolve
    student_count = session.run(
        "MATCH (s:Student)-[:ENROLLED_IN]->(c:Course) RETURN count(c) AS cnt"
    ).single()["cnt"]
    logger.info(f"Migration complete. Student enrollments verified: {student_count}")


def init_schema():
    driver = get_driver()
    with driver.session() as session:
        _migrate_curriculum_to_course(session)
        _create_constraints(session)
        if _is_empty(session):
            logger.info("Neo4j is empty. Run the ingestion pipeline to load college data:")
            logger.info("  python -m pipeline.run --college foothill")
        else:
            logger.info("Neo4j already contains data.")


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

    constraints = [
        "CREATE CONSTRAINT college_name IF NOT EXISTS FOR (n:College) REQUIRE n.name IS UNIQUE",
        "CREATE CONSTRAINT course_code_college IF NOT EXISTS FOR (n:Course) REQUIRE (n.code, n.college) IS UNIQUE",
        "CREATE CONSTRAINT department_name IF NOT EXISTS FOR (n:Department) REQUIRE n.name IS UNIQUE",
        "CREATE CONSTRAINT skill_name IF NOT EXISTS FOR (n:Skill) REQUIRE n.name IS UNIQUE",
        "CREATE CONSTRAINT student_uuid IF NOT EXISTS FOR (n:Student) REQUIRE n.uuid IS UNIQUE",
        "CREATE CONSTRAINT region_name IF NOT EXISTS FOR (n:Region) REQUIRE n.name IS UNIQUE",
        "CREATE CONSTRAINT occupation_soc IF NOT EXISTS FOR (n:Occupation) REQUIRE n.soc_code IS UNIQUE",
        "CREATE CONSTRAINT employer_name IF NOT EXISTS FOR (n:Employer) REQUIRE n.name IS UNIQUE",
    ]
    for constraint in constraints:
        session.run(constraint)

    # Range indexes for non-unique properties used as predicate filters in
    # hot-path queries. Uniqueness constraints already auto-create indexes
    # for their target properties; this list is the additional non-unique
    # set.
    #
    # student_primary_focus: speeds equality / IN-list filters on
    # Student.primary_focus, used by compute.py's pipeline_size
    # precompute (per-college, runs during ingestion) and by the
    # proposal-flow student-pipeline queries in partnerships/gather.py.
    # Without it, those reads do a NodeByLabelScan over all Student
    # nodes plus a property filter; with it they're a NodeIndexSeek.
    # Measured impact on a 99K-student graph:
    #   - compute.py pipeline_size: 15.6s -> 7.4s (2.1x)
    #   - gather.py student stats: 71ms -> 25ms (2.8x)
    # The LLM vocabulary-resolution query for primary_focus does
    # `toLower(...) CONTAINS '...'` and so cannot use a RANGE index;
    # it would benefit from a TEXT index instead, which we have not
    # added here.
    #
    # course_college: speeds the `MATCH (c:Course {college: $college})`
    # filter that appears in essentially every read endpoint and in
    # most LLM-generated queries (students, courses, employers,
    # occupations, partnerships, vocab resolver). The existing
    # `course_code_college` uniqueness constraint creates a composite
    # index keyed on (code, college); that index is only usable when
    # `code` is also bound. Filtering by college alone falls back to
    # NodeByLabelScan + property filter over all Course nodes
    # (~thousands per college × ~125 colleges in the full graph).
    # Adding a standalone RANGE index turns the per-college filter
    # into a NodeIndexSeek. Impact not yet measured; will be once the
    # neo4j_queries.jsonl instrumentation is deployed.
    # student_courses_completed: added speculatively to enable an
    # EXISTS-subquery rewrite of the /students/ pagination query that
    # would scan this index in DESC order. PROFILE showed the planner
    # didn't use it that way (NodeByLabelScan + per-row EXISTS won
    # the cost estimate), so the rewrite was reverted. The index is
    # kept because it's cheap, may be picked by future queries that
    # sort or range-filter on courses_completed, and incurs only
    # marginal write overhead at student generation time.
    indexes = [
        "CREATE INDEX student_primary_focus IF NOT EXISTS FOR (n:Student) ON (n.primary_focus)",
        "CREATE INDEX course_college IF NOT EXISTS FOR (n:Course) ON (n.college)",
        "CREATE INDEX student_courses_completed IF NOT EXISTS FOR (n:Student) ON (n.courses_completed)",
    ]
    for index in indexes:
        session.run(index)


def _is_empty(session) -> bool:
    result = session.run("MATCH (n:College) RETURN count(n) AS cnt")
    return result.single()["cnt"] == 0
