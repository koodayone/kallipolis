from fastapi import APIRouter, HTTPException
from ontology.schema import get_driver
from courses.models import (
    CollegeSummary,
    CollegeDepartment,
    DepartmentSummary,
    CourseSummary,
    CourseQueryRequest,
    CourseQueryResponse,
)
from courses.query import run_course_query

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


@router.get("/departments-full")
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


@router.get("/departments", response_model=list[DepartmentSummary])
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


@router.get("/", response_model=list[CourseSummary])
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
                       c.top_code AS top_code
                ORDER BY c.name
            """, department=department, college=college)
            return [
                CourseSummary(
                    name=r["name"],
                    code=r["code"] or "",
                    description=r["description"] or "",
                    learning_outcomes=r["learning_outcomes"] or [],
                    course_objectives=r["course_objectives"] or [],
                    top_code=r["top_code"] or None,
                )
                for r in result.data()
            ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{course_code}/occupations")
def get_course_occupations(course_code: str, college: str):
    """Returns the institutional pathway from a course to occupations:
    the course's TOP6 code with its program-area title, and the full
    set of SOC-coded occupations the course PREPARES_FOR via the
    Chancellor's Office TOP-CIP and BLS/NCES CIP-SOC crosswalks.
    Sorted alphabetically by occupation title for human scannability.
    Powers the Occupational Pathways section on the course detail view.
    """
    from ontology.crosswalks import load_top_titles

    driver = get_driver()
    try:
        with driver.session() as session:
            course_row = session.run(
                "MATCH (c:Course {code: $code, college: $college}) "
                "RETURN c.top_code AS top_code",
                code=course_code, college=college,
            ).single()
            top_code = (course_row["top_code"] if course_row else None) or None

            occupations = session.run("""
                MATCH (c:Course {code: $code, college: $college})-[:PREPARES_FOR]->(occ:Occupation)
                RETURN occ.soc_code AS soc_code, occ.title AS title
                ORDER BY occ.title
            """, code=course_code, college=college).data()

        top_titles = load_top_titles()
        return {
            "top_code": top_code,
            "top_title": top_titles.get(top_code or "", ""),
            "occupations": [
                {"soc_code": r["soc_code"], "title": r["title"]} for r in occupations
            ],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/query", response_model=CourseQueryResponse)
async def query_courses(req: CourseQueryRequest):
    try:
        courses, message, cypher = await run_course_query(req.query, req.college)
        return CourseQueryResponse(courses=courses, message=message, cypher=cypher)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
