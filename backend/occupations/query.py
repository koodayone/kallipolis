"""Semantic translation layer for Occupation queries."""

import logging
from llm.query_engine import validate_cypher, generate_query, execute_query
from llm.spec_engine import execute_spec, is_enabled_for, run_spec
from occupations.models import OccupationMatch

logger = logging.getLogger(__name__)

OCCUPATION_QUERY_PROMPT = """You are a Cypher query generator for a Neo4j graph database containing California community college labor market data. You translate natural language questions about occupations into valid Cypher queries.

SCHEMA:

Nodes:
- College (properties: name)
- Region (properties: name)
- Occupation (properties: soc_code, title, description, education_level)
  education_level: string, typical entry-level education (e.g. "Bachelor's degree", "Associate's degree"). This is a property on the Occupation NODE, not on the DEMANDS edge.
- Course (properties: code, college, name, department, top_code)
- Department (properties: name)

Relationships:
- (College)-[:IN_MARKET]->(Region)
- (Region)-[DEMANDS {employment, annual_wage, growth_rate, annual_openings}]->(Occupation)
  employment: integer, number of jobs in the region for this occupation
  annual_wage: integer, regional median annual salary in dollars
  growth_rate: float, projected 5-year growth rate 2024-2029 (e.g. 0.05 = 5% growth)
  annual_openings: integer, average annual job openings (new + replacement)
- (Course)-[:PREPARES_FOR {via_top}]->(Occupation)  // institutional Chancellor's Office TOP-CIP-SOC crosswalk
- (Department)-[:CONTAINS]->(Course)

IMPORTANT: employment, annual_wage, growth_rate, and annual_openings are properties on the DEMANDS relationship (d.employment, d.annual_wage, etc.), NOT on the Occupation node. Conversely, education_level is a property on the Occupation NODE (occ.education_level), NOT on the DEMANDS edge.

RULES:
1. Every query MUST use this full traversal as the base MATCH to count institutional curriculum alignment between occupations and the college's catalog:
     MATCH (col:College {name: $college})-[:IN_MARKET]->(r:Region)-[d:DEMANDS]->(occ:Occupation)<-[:PREPARES_FOR]-(course:Course {college: $college})<-[:CONTAINS]-(dept:Department)
   Add WHERE clauses after this MATCH to filter further.
2. ONLY use MATCH, OPTIONAL MATCH, WITH, WHERE, RETURN, ORDER BY, LIMIT, UNWIND, count, collect, DISTINCT, AND, OR, NOT, IN, CONTAINS, STARTS WITH, ENDS WITH, size, toLower, toUpper.
3. NEVER use CREATE, DELETE, SET, MERGE, REMOVE, DROP, DETACH, CALL, FOREACH, LOAD, or any write/mutation clause.
4. Always return results in this exact shape:
     RETURN occ.soc_code AS soc_code, occ.title AS title,
            occ.description AS description, d.annual_wage AS annual_wage,
            d.employment AS employment,
            d.growth_rate AS growth_rate, d.annual_openings AS annual_openings,
            occ.education_level AS education_level,
            count(DISTINCT course) AS aligned_course_count,
            count(DISTINCT dept) AS aligned_department_count
     ORDER BY aligned_course_count DESC
5. Do NOT add a LIMIT clause unless the user asks for a specific number.
6. If the question cannot be answered with the schema above, respond with: {"cypher": "CANNOT_TRANSLATE", "interpretation": ""}
7. The current college is provided in the user message. The $college parameter is always set to that college. If the user references a DIFFERENT college by name, respond with CANNOT_TRANSLATE.
8. For wage sorting ("highest paying"): use ORDER BY d.annual_wage DESC
9. For employment sorting ("most jobs"): use ORDER BY d.employment DESC
10. For growth sorting ("fastest growing"): use ORDER BY d.growth_rate DESC
11. For openings sorting ("most openings"): use ORDER BY d.annual_openings DESC
12. For education filtering ("associate's degree jobs"): add WHERE occ.education_level = "Associate's degree"
13. For title/role queries: add WHERE toLower(occ.title) CONTAINS '...'
14. Skill-based queries are NO LONGER supported — the bridge from courses to occupations is now via the institutional TOP-SOC crosswalk (PREPARES_FOR), not a skill index. Respond with CANNOT_TRANSLATE for "occupations requiring X skills"-style questions.

EXAMPLES:

Question: "Highest paying occupations"
MATCH (col:College {name: $college})-[:IN_MARKET]->(r:Region)-[d:DEMANDS]->(occ:Occupation)<-[:PREPARES_FOR]-(course:Course {college: $college})<-[:CONTAINS]-(dept:Department)
RETURN occ.soc_code AS soc_code, occ.title AS title,
       occ.description AS description, d.annual_wage AS annual_wage,
       d.employment AS employment, d.growth_rate AS growth_rate,
       d.annual_openings AS annual_openings, occ.education_level AS education_level,
       count(DISTINCT course) AS aligned_course_count,
       count(DISTINCT dept) AS aligned_department_count
ORDER BY d.annual_wage DESC

Question: "Software development roles"
MATCH (col:College {name: $college})-[:IN_MARKET]->(r:Region)-[d:DEMANDS]->(occ:Occupation)<-[:PREPARES_FOR]-(course:Course {college: $college})<-[:CONTAINS]-(dept:Department)
WHERE toLower(occ.title) CONTAINS 'software'
RETURN occ.soc_code AS soc_code, occ.title AS title,
       occ.description AS description, d.annual_wage AS annual_wage,
       d.employment AS employment, d.growth_rate AS growth_rate,
       d.annual_openings AS annual_openings, occ.education_level AS education_level,
       count(DISTINCT course) AS aligned_course_count,
       count(DISTINCT dept) AS aligned_department_count
ORDER BY aligned_course_count DESC

Question: "Most jobs available"
MATCH (col:College {name: $college})-[:IN_MARKET]->(r:Region)-[d:DEMANDS]->(occ:Occupation)<-[:PREPARES_FOR]-(course:Course {college: $college})<-[:CONTAINS]-(dept:Department)
RETURN occ.soc_code AS soc_code, occ.title AS title,
       occ.description AS description, d.annual_wage AS annual_wage,
       d.employment AS employment, d.growth_rate AS growth_rate,
       d.annual_openings AS annual_openings, occ.education_level AS education_level,
       count(DISTINCT course) AS aligned_course_count,
       count(DISTINCT dept) AS aligned_department_count
ORDER BY d.employment DESC

Question: "Healthcare occupations"
MATCH (col:College {name: $college})-[:IN_MARKET]->(r:Region)-[d:DEMANDS]->(occ:Occupation)<-[:PREPARES_FOR]-(course:Course {college: $college})<-[:CONTAINS]-(dept:Department)
WHERE toLower(occ.title) CONTAINS 'health' OR toLower(occ.title) CONTAINS 'nurse' OR toLower(occ.title) CONTAINS 'medical'
RETURN occ.soc_code AS soc_code, occ.title AS title,
       occ.description AS description, d.annual_wage AS annual_wage,
       d.employment AS employment, d.growth_rate AS growth_rate,
       d.annual_openings AS annual_openings, occ.education_level AS education_level,
       count(DISTINCT course) AS aligned_course_count,
       count(DISTINCT dept) AS aligned_department_count
ORDER BY aligned_course_count DESC

Respond with a JSON object containing two fields:
1. "cypher": the Cypher query as a string
2. "interpretation": a single sentence explaining what this query does in plain English, written for a non-technical workforce development coordinator. Be specific about the filtering criteria and mention curriculum alignment or regional demand where relevant.

No markdown code fences. Just the raw JSON object."""


async def run_occupation_query(question: str, college: str) -> tuple[list[OccupationMatch], str, str]:
    """Translate a natural language question into a Cypher query and return occupation results.

    When the spec-engine feature flag is enabled for this view (default
    on for occupations), the question is classified by Gemini Flash
    into a structured spec and rendered into Cypher by a deterministic
    template. Otherwise the legacy Sonnet path generates Cypher
    directly. Both paths produce equivalent OccupationMatch rows.
    """
    logger.info(f"Occupation query: {question!r} for college: {college!r}")

    if is_enabled_for("occupation"):
        result = run_spec(question, college, "occupation")
        if result.unsupported:
            logger.info(
                f"Unsupported occupation query: question={question!r} "
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
            question, college, OCCUPATION_QUERY_PROMPT, view="occupation",
        )
        cypher = validate_cypher(cypher)
        records = execute_query(cypher, college)
    logger.info(f"Cypher: {cypher!r}")
    occupations = [
        OccupationMatch(
            soc_code=r["soc_code"],
            title=r["title"],
            description=r.get("description"),
            annual_wage=r.get("annual_wage"),
            employment=r.get("employment"),
            growth_rate=r.get("growth_rate"),
            annual_openings=r.get("annual_openings"),
            education_level=r.get("education_level"),
            aligned_course_count=r.get("aligned_course_count", 0),
            aligned_department_count=r.get("aligned_department_count", 0),
        )
        for r in records
    ]

    count = len(occupations)
    count_text = f"{count} occupation{'s' if count != 1 else ''} found."
    message = f"{count_text} {interpretation}" if interpretation else count_text
    logger.info(f"Query complete: {message}")

    return occupations, message, cypher
