from fastapi import APIRouter, HTTPException
from ontology.schema import get_driver
from students.models import (
    StudentSummary,
    StudentDetail,
    StudentEnrollment,
    StudentQueryRequest,
    StudentQueryResponse,
)
from students.helpers import compute_gpa
from students.query import run_student_query

router = APIRouter()


@router.get("/", response_model=list[StudentSummary])
def get_students(college: str):
    driver = get_driver()
    try:
        with driver.session() as session:
            result = session.run("""
                MATCH (s:Student)-[:ENROLLED_IN]->(:Course {college: $college})
                WITH DISTINCT s
                RETURN s.uuid AS uuid, s.gpa AS gpa,
                       s.primary_focus AS primary_focus,
                       s.courses_completed AS courses_completed
                ORDER BY s.courses_completed DESC
            """, college=college)
            records = result.data()

        return [
            StudentSummary(
                uuid=r["uuid"],
                primary_focus=r.get("primary_focus", "Undeclared"),
                courses_completed=r.get("courses_completed", 0),
                gpa=r.get("gpa", 0.0),
            )
            for r in records
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{student_uuid}", response_model=StudentDetail)
def get_student(student_uuid: str, college: str):
    driver = get_driver()
    try:
        with driver.session() as session:
            result = session.run("""
                MATCH (s:Student {uuid: $uuid})-[e:ENROLLED_IN]->(c:Course {college: $college})
                RETURN s.uuid AS uuid,
                       c.code AS course_code,
                       c.name AS course_name,
                       c.department AS department,
                       c.skill_mappings AS skill_mappings,
                       e.grade AS grade,
                       e.term AS term,
                       e.status AS status
                ORDER BY e.term
            """, uuid=student_uuid, college=college)
            records = result.data()

        if not records:
            raise HTTPException(status_code=404, detail="Student not found")

        enrollments = []
        all_grades = []
        all_skills: set[str] = set()
        dept_counts: dict[str, int] = {}

        for r in records:
            enrollments.append(StudentEnrollment(
                course_code=r["course_code"] or "",
                course_name=r["course_name"],
                department=r["department"] or "Unknown",
                grade=r["grade"],
                term=r["term"],
                status=r["status"],
            ))
            if r["status"] == "Completed":
                all_grades.append(r["grade"])
                dept = r["department"] or "Unknown"
                dept_counts[dept] = dept_counts.get(dept, 0) + 1
                if r["skill_mappings"]:
                    all_skills.update(r["skill_mappings"])

        primary_focus = max(dept_counts, key=dept_counts.get) if dept_counts else "Undeclared"

        return StudentDetail(
            uuid=student_uuid,
            primary_focus=primary_focus,
            courses_completed=len(all_grades),
            gpa=compute_gpa(all_grades),
            enrollments=enrollments,
            skills=sorted(all_skills),
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/query", response_model=StudentQueryResponse)
async def query_students(req: StudentQueryRequest):
    try:
        students, message, cypher = await run_student_query(req.query, req.college)
        return StudentQueryResponse(students=students, message=message, cypher=cypher)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
