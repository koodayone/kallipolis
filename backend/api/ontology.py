from fastapi import APIRouter, HTTPException
from ontology.schema import get_driver
from models import InstitutionSummary, ProgramSummary

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
