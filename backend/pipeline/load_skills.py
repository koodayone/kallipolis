"""
Migrate skill_mappings from Course properties into first-class Skill nodes.

Creates Skill nodes from all unique skill_mappings values across all courses,
then creates Course -[DEVELOPS]-> Skill relationships.

Usage:
    python -m pipeline.load_skills
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ontology.schema import get_driver, close_driver

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("load_skills")


def load_skill_nodes(driver):
    """Extract Skill nodes from Course.skill_mappings and create DEVELOPS relationships."""
    with driver.session() as s:
        # Ensure constraint exists
        s.run("CREATE CONSTRAINT skill_name IF NOT EXISTS FOR (n:Skill) REQUIRE n.name IS UNIQUE")

        # Step 1: Create Skill nodes from all unique skill_mappings
        logger.info("Creating Skill nodes from course skill_mappings...")
        result = s.run("""
            MATCH (c:Course)
            WHERE c.skill_mappings IS NOT NULL AND size(c.skill_mappings) > 0
            UNWIND c.skill_mappings AS skill_name
            WITH DISTINCT skill_name
            MERGE (s:Skill {name: skill_name})
            RETURN count(s) AS skills_created
        """)
        skills = result.single()["skills_created"]
        logger.info(f"Created {skills} Skill nodes")

        # Step 2: Create DEVELOPS relationships
        logger.info("Creating Course -[DEVELOPS]-> Skill relationships...")
        result = s.run("""
            MATCH (c:Course)
            WHERE c.skill_mappings IS NOT NULL AND size(c.skill_mappings) > 0
            UNWIND c.skill_mappings AS skill_name
            MATCH (s:Skill {name: skill_name})
            MERGE (c)-[:DEVELOPS]->(s)
            RETURN count(*) AS relationships_created
        """)
        rels = result.single()["relationships_created"]
        logger.info(f"Created {rels} DEVELOPS relationships")

        # Verify
        skill_count = s.run("MATCH (s:Skill) RETURN count(s) AS c").single()["c"]
        rel_count = s.run("MATCH ()-[:DEVELOPS]->() RETURN count(*) AS c").single()["c"]
        courses_with = s.run("""
            MATCH (c:Course)-[:DEVELOPS]->()
            RETURN count(DISTINCT c) AS c
        """).single()["c"]

        logger.info(f"Verification:")
        logger.info(f"  Skill nodes: {skill_count}")
        logger.info(f"  DEVELOPS relationships: {rel_count}")
        logger.info(f"  Courses linked to skills: {courses_with}")


def main():
    env_path = Path(__file__).resolve().parent.parent.parent / ".env"
    load_dotenv(env_path)

    driver = get_driver()
    try:
        load_skill_nodes(driver)
    finally:
        close_driver()


if __name__ == "__main__":
    main()
