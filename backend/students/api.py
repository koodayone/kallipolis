from collections import defaultdict

from fastapi import APIRouter, HTTPException, Query
from ontology.schema import get_driver
from ontology.crosswalks import load_top_titles
from students.models import (
    StudentSummary,
    StudentSummaryPage,
    StudentDetail,
    StudentEnrollment,
    OccupationAlignment,
    TopGroup,
    CourseRef,
    StudentQueryRequest,
    StudentQueryResponse,
)
from students.helpers import compute_gpa
from students.query import run_student_query

router = APIRouter()

DEFAULT_LIMIT = 100
MAX_LIMIT = 5000


@router.get("/", response_model=StudentSummaryPage)
def get_students(
    college: str,
    limit: int = Query(DEFAULT_LIMIT, ge=1, le=MAX_LIMIT),
    offset: int = Query(0, ge=0),
):
    """Paginated bulk student list for a college, ordered by courses_completed DESC.

    The earlier shape returned every student at a college as a flat list;
    at 14K students for Foothill that produced a ~3 MB payload and 153 ms
    first-paint TTFB. The endpoint now returns a page slice plus
    `total_count` so callers can render "showing N of M" and request
    further pages by offset.
    """
    # Query shape: `MATCH (s:Student)-[:ENROLLED_IN]->(:Course {college})`
    # with DISTINCT then ORDER BY then SKIP/LIMIT. An EXISTS-subquery
    # rewrite was attempted (see commit history); PROFILE on the
    # 99K-student / 14K-foothill graph showed it was 5.4x slower
    # (1706ms vs 314ms) and used 17x more DbHits — the planner did a
    # NodeByLabelScan + per-row EXISTS check instead of using the
    # `student_courses_completed` index for the ORDER BY. The join
    # shape lets the planner index-seek into Course via `course_college`,
    # walk ENROLLED_IN backward to gather ~14K candidate students,
    # then DISTINCT + sort + page. 13MB transient memory for the
    # DISTINCT materialization is acceptable at this scale.
    driver = get_driver()
    try:
        with driver.session() as session:
            count_record = session.run(
                """
                MATCH (s:Student)-[:ENROLLED_IN]->(:Course {college: $college})
                RETURN count(DISTINCT s) AS total
                """,
                college=college,
            ).single()
            total_count = count_record["total"] if count_record else 0

            result = session.run(
                """
                MATCH (s:Student)-[:ENROLLED_IN]->(:Course {college: $college})
                WITH DISTINCT s
                RETURN s.uuid AS uuid, s.gpa AS gpa,
                       s.primary_focus AS primary_focus,
                       s.courses_completed AS courses_completed
                ORDER BY s.courses_completed DESC
                SKIP $offset LIMIT $limit
                """,
                college=college,
                offset=offset,
                limit=limit,
            )
            records = result.data()

        students = [
            StudentSummary(
                uuid=r["uuid"],
                primary_focus=r.get("primary_focus", "Undeclared"),
                courses_completed=r.get("courses_completed", 0),
                gpa=r.get("gpa", 0.0),
            )
            for r in records
        ]
        return StudentSummaryPage(
            students=students,
            total_count=total_count,
            has_more=offset + len(students) < total_count,
        )
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
                       e.grade AS grade,
                       e.term AS term,
                       e.status AS status
                ORDER BY e.term
            """, uuid=student_uuid, college=college)
            records = result.data()

            if not records:
                raise HTTPException(status_code=404, detail="Student not found")

            # Competency profile grounded in the institutional TOP-SOC
            # crosswalk (PREPARES_FOR edges). Top 10 SOCs by matched-
            # course count. No depth threshold: a student early in
            # their academic career has shallow alignment everywhere,
            # and rendering "no profile" for them when the truth is
            # "still building" was dishonest. The cap keeps the surface
            # scannable; the rank tells the truth at every stage.
            # Matched courses are grouped by TOP6 in Python after the
            # query so the rendering layer can visualize the program-
            # area structure of each alignment.
            alignment_records = session.run("""
                MATCH (s:Student {uuid: $uuid})-[e:ENROLLED_IN]->(c:Course {college: $college})
                WHERE e.status = 'Completed'
                WITH collect(DISTINCT c) AS completed_courses
                UNWIND completed_courses AS sc
                MATCH (sc)-[:PREPARES_FOR]->(occ:Occupation)
                WITH occ, collect(DISTINCT sc) AS matched_courses
                RETURN occ.soc_code AS soc_code,
                       occ.title AS title,
                       [m IN matched_courses | {
                           code: m.code,
                           name: m.name,
                           top_code: m.top_code
                       }] AS matched_courses
                ORDER BY size(matched_courses) DESC, occ.title ASC
                LIMIT 10
            """, uuid=student_uuid, college=college).data()

        enrollments = []
        all_grades = []
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

        primary_focus = max(dept_counts, key=dept_counts.get) if dept_counts else "Undeclared"

        top_titles = load_top_titles()

        def build_alignment(a: dict) -> OccupationAlignment:
            # Group matched courses by their institutional TOP6 — the
            # program-area pivot the crosswalk used to mediate each
            # course→occupation pathway.
            by_top: dict[str, list[dict]] = defaultdict(list)
            for c in a["matched_courses"]:
                by_top[c.get("top_code") or ""].append(c)

            groups = [
                TopGroup(
                    top_code=top_code,
                    top_title=top_titles.get(top_code, ""),
                    courses=sorted(
                        [CourseRef(code=c["code"], name=c["name"]) for c in courses],
                        key=lambda cr: cr.code,
                    ),
                )
                for top_code, courses in by_top.items()
            ]
            # Strongest program-area concentration first within each SOC.
            groups.sort(key=lambda g: (-len(g.courses), g.top_code))

            return OccupationAlignment(
                soc_code=a["soc_code"],
                title=a["title"],
                matched_course_count=len(a["matched_courses"]),
                matched_top_groups=groups,
            )

        occupation_alignment = [build_alignment(a) for a in alignment_records]

        return StudentDetail(
            uuid=student_uuid,
            primary_focus=primary_focus,
            courses_completed=len(all_grades),
            gpa=compute_gpa(all_grades),
            enrollments=enrollments,
            occupation_alignment=occupation_alignment,
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
