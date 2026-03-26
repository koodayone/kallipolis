import os
import logging
from neo4j import GraphDatabase

logger = logging.getLogger(__name__)

_driver = None


def get_driver():
    global _driver
    if _driver is None:
        _driver = GraphDatabase.driver(
            os.environ["NEO4J_URI"],
            auth=(os.environ["NEO4J_USERNAME"], os.environ["NEO4J_PASSWORD"]),
        )
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


def _is_empty(session) -> bool:
    result = session.run("MATCH (n:College) RETURN count(n) AS cnt")
    return result.single()["cnt"] == 0
