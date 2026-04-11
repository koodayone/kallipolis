"""
One-time migration: compute and materialize gpa, primary_focus, and courses_completed
on all existing Student nodes in Neo4j.

Usage:
    cd backend
    python -m scripts.materialize_student_fields
"""

import logging
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ontology.schema import get_driver
from students.helpers import compute_gpa, compute_primary_focus

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

BATCH_SIZE = 500


def materialize():
    driver = get_driver()

    # Get all colleges first
    with driver.session() as session:
        colleges = [r["college"] for r in session.run(
            "MATCH (c:College) RETURN c.name AS college"
        ).data()]

    logger.info(f"Found {len(colleges)} colleges to process")

    total_written = 0
    for college in colleges:
        # Fetch students per college to avoid memory issues
        with driver.session() as session:
            result = session.run("""
                MATCH (s:Student)-[e:ENROLLED_IN]->(c:Course {college: $college})
                WITH s, collect({department: c.department, grade: e.grade, status: e.status}) AS enrollments
                RETURN s.uuid AS uuid, enrollments
            """, college=college)
            records = result.data()

        if not records:
            continue

        # Compute derived fields for each student
        updates = []
        for record in records:
            enrollments = record["enrollments"]
            completed = [e for e in enrollments if e.get("status") == "Completed"]
            grades = [e["grade"] for e in completed if e.get("grade")]

            updates.append({
                "uuid": record["uuid"],
                "gpa": compute_gpa(grades),
                "primary_focus": compute_primary_focus(enrollments),
                "courses_completed": len(completed),
            })

        # Batch SET on Student nodes
        with driver.session() as session:
            for i in range(0, len(updates), BATCH_SIZE):
                batch = updates[i : i + BATCH_SIZE]
                session.run("""
                    UNWIND $batch AS row
                    MATCH (s:Student {uuid: row.uuid})
                    SET s.gpa = row.gpa,
                        s.primary_focus = row.primary_focus,
                        s.courses_completed = row.courses_completed
                """, batch=batch)

        total_written += len(updates)
        logger.info(f"  {college}: materialized {len(updates)} students ({total_written} total)")

    logger.info(f"Migration complete: materialized fields on {total_written} students")


if __name__ == "__main__":
    materialize()
