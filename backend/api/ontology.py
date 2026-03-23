from collections import Counter
from fastapi import APIRouter, HTTPException
from ontology.schema import get_driver
from models import InstitutionSummary, ProgramSummary, StudentSummary, StudentDetail, StudentEnrollment

router = APIRouter()


@router.get("/institution", response_model=InstitutionSummary)
def get_institution():
    driver = get_driver()
    try:
        with driver.session() as session:
            result = session.run("""
                MATCH (i:Institution)-[:OFFERS]->(p:Program)-[:CONTAINS]->(c:Curriculum)
                RETURN i.name AS institution_name, i.region AS region,
                       p.name AS program, collect(c.name) AS curricula
                ORDER BY p.name
            """)
            records = result.data()

        if not records:
            raise HTTPException(status_code=404, detail="No institution data found")

        programs: list[ProgramSummary] = []
        for record in records:
            programs.append(ProgramSummary(
                program_name=record["program"],
                curricula=sorted(record["curricula"]),
            ))

        return InstitutionSummary(
            institution_name=records[0]["institution_name"],
            region=records[0]["region"],
            programs=programs,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/programs")
def get_programs():
    driver = get_driver()
    try:
        with driver.session() as session:
            result = session.run("""
                MATCH (p:Program)-[:CONTAINS]->(c:Curriculum)
                RETURN p.name AS program, collect(c.name) AS curricula
                ORDER BY p.name
            """)
            records = result.data()

        return [
            {"program_name": r["program"], "curricula": sorted(r["curricula"])}
            for r in records
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def _compute_performance(grades: list[str]) -> str:
    if not grades:
        return "Incomplete"
    counts = Counter(grades)
    total = len(grades)
    strong = counts.get("A", 0) + counts.get("B", 0)
    weak = counts.get("D", 0) + counts.get("F", 0) + counts.get("W", 0)
    if strong / total >= 0.6:
        return "Strong"
    if weak / total >= 0.4:
        return "Incomplete"
    return "Developing"


def _compute_primary_focus(enrollments: list[dict]) -> str:
    completed = [e["department"] for e in enrollments if e["status"] == "Completed" and e.get("department")]
    if not completed:
        return "Undeclared"
    return Counter(completed).most_common(1)[0][0]


@router.get("/students", response_model=list[StudentSummary])
def get_students():
    driver = get_driver()
    try:
        with driver.session() as session:
            result = session.run("""
                MATCH (s:Student)-[e:ENROLLED_IN]->(c:Curriculum)
                WITH s, collect({
                    name: c.name,
                    department: c.department,
                    grade: e.grade,
                    term: e.term,
                    status: e.status
                }) AS enrollments
                RETURN s.uuid AS uuid, enrollments
            """)
            records = result.data()

        students = []
        for record in records:
            enrollments = record["enrollments"]
            completed = [e for e in enrollments if e["status"] == "Completed"]
            grades = [e["grade"] for e in completed]

            students.append(StudentSummary(
                uuid=record["uuid"],
                primary_focus=_compute_primary_focus(enrollments),
                courses_completed=len(completed),
                avg_performance=_compute_performance(grades),
            ))

        students.sort(key=lambda s: s.courses_completed, reverse=True)
        return students
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/students/{student_uuid}", response_model=StudentDetail)
def get_student(student_uuid: str):
    driver = get_driver()
    try:
        with driver.session() as session:
            result = session.run("""
                MATCH (s:Student {uuid: $uuid})-[e:ENROLLED_IN]->(c:Curriculum)
                RETURN s.uuid AS uuid,
                       c.name AS course_name,
                       c.department AS department,
                       c.skill_mappings AS skill_mappings,
                       e.grade AS grade,
                       e.term AS term,
                       e.status AS status
                ORDER BY e.term
            """, uuid=student_uuid)
            records = result.data()

        if not records:
            raise HTTPException(status_code=404, detail="Student not found")

        enrollments = []
        all_grades = []
        all_skills: set[str] = set()
        dept_counts: dict[str, int] = {}

        for r in records:
            enrollments.append(StudentEnrollment(
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
            avg_performance=_compute_performance(all_grades),
            enrollments=enrollments,
            skills=sorted(all_skills),
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
