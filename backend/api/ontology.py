from fastapi import APIRouter, HTTPException
from ontology.schema import get_driver
from ontology.utils import compute_gpa
from models import CollegeSummary, CollegeDepartment, StudentSummary, StudentDetail, StudentEnrollment, DepartmentSummary, CourseSummary, StudentQueryRequest, StudentQueryResponse, CourseQueryRequest, CourseQueryResponse
from workflows.student_query import run_student_query
from workflows.course_query import run_course_query

router = APIRouter()


@router.get("/college", response_model=CollegeSummary)
def get_college(college: str):
    driver = get_driver()
    try:
        with driver.session() as session:
            result = session.run("""
                MATCH (col:College {name: $college})-[:OFFERS]->(d:Department)-[:CONTAINS]->(c:Course {college: $college})
                RETURN col.name AS college_name, col.region AS region,
                       d.name AS department, collect(c.name) AS curricula
                ORDER BY d.name
            """, college=college)
            records = result.data()

        if not records:
            raise HTTPException(status_code=404, detail="No college data found")

        departments: list[CollegeDepartment] = []
        for record in records:
            departments.append(CollegeDepartment(
                department_name=record["department"],
                curricula=sorted(record["curricula"]),
            ))

        return CollegeSummary(
            college_name=records[0]["college_name"],
            region=records[0]["region"],
            departments=departments,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/departments")
def get_departments_with_courses(college: str):
    driver = get_driver()
    try:
        with driver.session() as session:
            result = session.run("""
                MATCH (col:College {name: $college})-[:OFFERS]->(d:Department)-[:CONTAINS]->(c:Course {college: $college})
                RETURN d.name AS department, collect(c.name) AS curricula
                ORDER BY d.name
            """, college=college)
            records = result.data()

        return [
            {"department_name": r["department"], "curricula": sorted(r["curricula"])}
            for r in records
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))




@router.get("/students", response_model=list[StudentSummary])
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


@router.get("/students/{student_uuid}", response_model=StudentDetail)
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


@router.get("/courses/departments", response_model=list[DepartmentSummary])
def get_departments(college: str):
    driver = get_driver()
    try:
        with driver.session() as session:
            result = session.run("""
                MATCH (d:Department)-[:CONTAINS]->(c:Course {college: $college})
                RETURN d.name AS department, count(c) AS course_count
                ORDER BY department
            """, college=college)
            return [
                DepartmentSummary(department=r["department"], course_count=r["course_count"])
                for r in result.data()
            ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/courses/list", response_model=list[CourseSummary])
def get_courses(department: str, college: str):
    driver = get_driver()
    try:
        with driver.session() as session:
            result = session.run("""
                MATCH (d:Department {name: $department})-[:CONTAINS]->(c:Course {college: $college})
                RETURN c.name AS name, c.code AS code,
                       c.description AS description,
                       c.learning_outcomes AS learning_outcomes,
                       c.course_objectives AS course_objectives,
                       c.skill_mappings AS skill_mappings
                ORDER BY c.name
            """, department=department, college=college)
            return [
                CourseSummary(
                    name=r["name"],
                    code=r["code"] or "",
                    description=r["description"] or "",
                    learning_outcomes=r["learning_outcomes"] or [],
                    course_objectives=r["course_objectives"] or [],
                    skill_mappings=r["skill_mappings"] or [],
                )
                for r in result.data()
            ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/students/query", response_model=StudentQueryResponse)
async def query_students(req: StudentQueryRequest):
    try:
        students, message, cypher = await run_student_query(req.query, req.college)
        return StudentQueryResponse(students=students, message=message, cypher=cypher)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/courses/query", response_model=CourseQueryResponse)
async def query_courses(req: CourseQueryRequest):
    try:
        courses, message, cypher = await run_course_query(req.query, req.college)
        return CourseQueryResponse(courses=courses, message=message, cypher=cypher)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
