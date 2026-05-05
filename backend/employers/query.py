"""Semantic translation layer for Employer queries."""

import logging
from llm.query_engine import validate_cypher, generate_query, execute_query
from llm.spec_engine import execute_spec, is_enabled_for, run_spec
from employers.models import EmployerMatch

logger = logging.getLogger(__name__)

EMPLOYER_QUERY_PROMPT = """You are a Cypher query generator for a Neo4j graph database containing California community college labor market data. You translate natural language questions about employers into valid Cypher queries.

SCHEMA:

Nodes:
- College (properties: name)
- Region (properties: name, priority_sectors)
  priority_sectors: list of strings. The 5 Strong Workforce Program (SWP) priority sector names this region has selected from the 12 Doing-What-MATTERS sector clusters. Authoritative per the Chancellor's Office regional consortia.
- Employer (properties: name, sector, description, website, swp_sectors)
  swp_sectors: list of strings. The SWP sector(s) the employer's NAICS classification maps to under the PCAH NAICS-to-Sector composition.
- Occupation (properties: soc_code, title, description, annual_wage)
- Course (properties: code, college, name, top_code)
- Department (properties: name)

Relationships:
- (College)-[:IN_MARKET]->(Region)
- (Employer)-[:IN_MARKET]->(Region)
- (Employer)-[:HIRES_FOR]->(Occupation)
- (Course)-[:PREPARES_FOR {via_top}]->(Occupation)  // institutional Chancellor's Office TOP-CIP-SOC crosswalk
- (Department)-[:CONTAINS]->(Course)

RULES:
1. Every query MUST use this full traversal as the base MATCH to compute institutional curriculum alignment between the employer and the college:
     MATCH (col:College {name: $college})-[:IN_MARKET]->(r:Region)<-[:IN_MARKET]-(emp:Employer)-[:HIRES_FOR]->(occ:Occupation)
     OPTIONAL MATCH (course:Course {college: $college})-[:PREPARES_FOR]->(occ)
   Add WHERE clauses after these MATCHes to filter further.
2. ONLY use MATCH, OPTIONAL MATCH, WITH, WHERE, RETURN, ORDER BY, LIMIT, UNWIND, count, collect, DISTINCT, AND, OR, NOT, IN, CONTAINS, STARTS WITH, ENDS WITH, size, toLower, toUpper.
3. NEVER use CREATE, DELETE, SET, MERGE, REMOVE, DROP, DETACH, CALL, FOREACH, LOAD, or any write/mutation clause.
4. Always return results in this exact shape:
     RETURN emp.name AS name, emp.sector AS sector, emp.description AS description,
            emp.website AS website,
            collect(DISTINCT occ.title) AS occupations,
            count(DISTINCT course) AS aligned_course_count
     ORDER BY aligned_course_count DESC
5. Do NOT add a LIMIT clause unless the user asks for a specific number.
6. If the question cannot be answered with the schema above, respond with: {"cypher": "CANNOT_TRANSLATE", "interpretation": ""}
7. The current college is provided in the user message. The $college parameter is always set to that college. If the user references a DIFFERENT college by name, respond with CANNOT_TRANSLATE.
8. For sector-based queries: add WHERE toLower(emp.sector) CONTAINS '...'
9. For employer name queries: add WHERE toLower(emp.name) CONTAINS '...'
10. Skill-based queries are NO LONGER supported — the bridge from courses to occupations is now via the institutional TOP-SOC crosswalk (PREPARES_FOR), not a skill index. Respond with CANNOT_TRANSLATE for "employers requiring X skills"-style questions.
11. For "regional priority sectors" / "SWP priority sectors" queries: filter to employers whose swp_sectors intersect the region's priority_sectors. Use: WHERE ANY(s IN emp.swp_sectors WHERE s IN r.priority_sectors).

EXAMPLES:

Question: "Healthcare employers"
MATCH (col:College {name: $college})-[:IN_MARKET]->(r:Region)<-[:IN_MARKET]-(emp:Employer)-[:HIRES_FOR]->(occ:Occupation)
OPTIONAL MATCH (course:Course {college: $college})-[:PREPARES_FOR]->(occ)
WHERE toLower(emp.sector) CONTAINS 'health'
RETURN emp.name AS name, emp.sector AS sector, emp.description AS description,
       emp.website AS website,
       collect(DISTINCT occ.title) AS occupations,
       count(DISTINCT course) AS aligned_course_count
ORDER BY aligned_course_count DESC

Question: "Technology companies"
MATCH (col:College {name: $college})-[:IN_MARKET]->(r:Region)<-[:IN_MARKET]-(emp:Employer)-[:HIRES_FOR]->(occ:Occupation)
OPTIONAL MATCH (course:Course {college: $college})-[:PREPARES_FOR]->(occ)
WHERE toLower(emp.sector) CONTAINS 'technology'
RETURN emp.name AS name, emp.sector AS sector, emp.description AS description,
       emp.website AS website,
       collect(DISTINCT occ.title) AS occupations,
       count(DISTINCT course) AS aligned_course_count
ORDER BY aligned_course_count DESC

Question: "Employers with the most curriculum alignment"
MATCH (col:College {name: $college})-[:IN_MARKET]->(r:Region)<-[:IN_MARKET]-(emp:Employer)-[:HIRES_FOR]->(occ:Occupation)
OPTIONAL MATCH (course:Course {college: $college})-[:PREPARES_FOR]->(occ)
RETURN emp.name AS name, emp.sector AS sector, emp.description AS description,
       emp.website AS website,
       collect(DISTINCT occ.title) AS occupations,
       count(DISTINCT course) AS aligned_course_count
ORDER BY aligned_course_count DESC

Question: "Employers in regional priority sectors"
MATCH (col:College {name: $college})-[:IN_MARKET]->(r:Region)<-[:IN_MARKET]-(emp:Employer)-[:HIRES_FOR]->(occ:Occupation)
OPTIONAL MATCH (course:Course {college: $college})-[:PREPARES_FOR]->(occ)
WHERE ANY(s IN emp.swp_sectors WHERE s IN r.priority_sectors)
RETURN emp.name AS name, emp.sector AS sector, emp.description AS description,
       emp.website AS website,
       collect(DISTINCT occ.title) AS occupations,
       count(DISTINCT course) AS aligned_course_count
ORDER BY aligned_course_count DESC

Respond with a JSON object containing two fields:
1. "cypher": the Cypher query as a string
2. "interpretation": a single sentence explaining what this query does in plain English, written for a non-technical workforce development coordinator. Be specific about the filtering criteria and mention curriculum alignment where relevant.

No markdown code fences. Just the raw JSON object."""


async def run_employer_query(question: str, college: str) -> tuple[list[EmployerMatch], str, str]:
    """Translate a natural language question into a Cypher query and return employer results.

    Spec-engine path is on by default for employers. See
    `llm/spec_engine.py` for the rationale and feature flag.
    """
    logger.info(f"Employer query: {question!r} for college: {college!r}")

    if is_enabled_for("employer"):
        result = run_spec(question, college, "employer")
        if result.unsupported:
            logger.info(
                f"Unsupported employer query: question={question!r} "
                f"reason={result.unsupported_reason!r}"
            )
            raise ValueError(
                "Sorry, I couldn't translate that question. "
                "Try one of the example queries, or rephrase your question."
            )
        records = execute_spec(result)
        cypher = result.cypher
        interpretation = result.interpretation
    else:
        cypher, interpretation = generate_query(
            question, college, EMPLOYER_QUERY_PROMPT, view="employer",
        )
        cypher = validate_cypher(cypher)
        records = execute_query(cypher, college)
    logger.info(f"Cypher: {cypher!r}")
    employers = [
        EmployerMatch(
            name=r["name"],
            sector=r.get("sector"),
            description=r.get("description"),
            website=r.get("website"),
            occupations=r.get("occupations", []),
            aligned_course_count=r.get("aligned_course_count", 0),
        )
        for r in records
    ]

    count = len(employers)
    count_text = f"{count} employer{'s' if count != 1 else ''} found."
    message = f"{count_text} {interpretation}" if interpretation else count_text
    logger.info(f"Query complete: {message}")

    return employers, message, cypher
