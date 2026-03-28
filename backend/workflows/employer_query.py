"""Semantic translation layer for Employer queries."""

import logging
from workflows.query_engine import validate_cypher, generate_query, execute_query
from models import EmployerMatch

logger = logging.getLogger(__name__)

EMPLOYER_QUERY_PROMPT = """You are a Cypher query generator for a Neo4j graph database containing California community college labor market data. You translate natural language questions about employers into valid Cypher queries.

SCHEMA:

Nodes:
- College (properties: name)
- Region (properties: name)
- Employer (properties: name, sector, description)
- Occupation (properties: soc_code, title, description, annual_wage)
- Skill (properties: name)
- Course (properties: code, college, name)

Relationships:
- (College)-[:IN_MARKET]->(Region)
- (Employer)-[:IN_MARKET]->(Region)
- (Employer)-[:HIRES_FOR]->(Occupation)
- (Occupation)-[:REQUIRES_SKILL]->(Skill)
- (Course)-[:DEVELOPS]->(Skill)

RULES:
1. Every query MUST use this full traversal as the base MATCH to compute skill alignment between the employer and the college's curriculum:
     MATCH (col:College {name: $college})-[:IN_MARKET]->(r:Region)<-[:IN_MARKET]-(emp:Employer)-[:HIRES_FOR]->(occ:Occupation)-[:REQUIRES_SKILL]->(sk:Skill)<-[:DEVELOPS]-(course:Course {college: $college})
   Add WHERE clauses after this MATCH to filter further.
2. ONLY use MATCH, OPTIONAL MATCH, WITH, WHERE, RETURN, ORDER BY, LIMIT, UNWIND, count, collect, DISTINCT, AND, OR, NOT, IN, CONTAINS, STARTS WITH, ENDS WITH, size, toLower, toUpper.
3. NEVER use CREATE, DELETE, SET, MERGE, REMOVE, DROP, DETACH, CALL, FOREACH, LOAD, or any write/mutation clause.
4. Always return results in this exact shape:
     RETURN emp.name AS name, emp.sector AS sector, emp.description AS description,
            collect(DISTINCT occ.title) AS occupations,
            count(DISTINCT sk) AS matching_skills,
            collect(DISTINCT sk.name) AS skills
     ORDER BY matching_skills DESC
5. Do NOT add a LIMIT clause unless the user asks for a specific number.
6. If the question cannot be answered with the schema above, respond with: {"cypher": "CANNOT_TRANSLATE", "interpretation": ""}
7. The current college is provided in the user message. The $college parameter is always set to that college. If the user references a DIFFERENT college by name, respond with CANNOT_TRANSLATE.
8. For sector-based queries: add WHERE toLower(emp.sector) CONTAINS '...'
9. For employer name queries: add WHERE toLower(emp.name) CONTAINS '...'
10. For skill-based queries ("who hires for X"): add WHERE toLower(sk.name) CONTAINS '...'

EXAMPLES:

Question: "Healthcare employers"
MATCH (col:College {name: $college})-[:IN_MARKET]->(r:Region)<-[:IN_MARKET]-(emp:Employer)-[:HIRES_FOR]->(occ:Occupation)-[:REQUIRES_SKILL]->(sk:Skill)<-[:DEVELOPS]-(course:Course {college: $college})
WHERE toLower(emp.sector) CONTAINS 'health'
RETURN emp.name AS name, emp.sector AS sector, emp.description AS description,
       collect(DISTINCT occ.title) AS occupations,
       count(DISTINCT sk) AS matching_skills,
       collect(DISTINCT sk.name) AS skills
ORDER BY matching_skills DESC

Question: "Technology companies"
MATCH (col:College {name: $college})-[:IN_MARKET]->(r:Region)<-[:IN_MARKET]-(emp:Employer)-[:HIRES_FOR]->(occ:Occupation)-[:REQUIRES_SKILL]->(sk:Skill)<-[:DEVELOPS]-(course:Course {college: $college})
WHERE toLower(emp.sector) CONTAINS 'technology'
RETURN emp.name AS name, emp.sector AS sector, emp.description AS description,
       collect(DISTINCT occ.title) AS occupations,
       count(DISTINCT sk) AS matching_skills,
       collect(DISTINCT sk.name) AS skills
ORDER BY matching_skills DESC

Question: "Who hires for Programming?"
MATCH (col:College {name: $college})-[:IN_MARKET]->(r:Region)<-[:IN_MARKET]-(emp:Employer)-[:HIRES_FOR]->(occ:Occupation)-[:REQUIRES_SKILL]->(sk:Skill)<-[:DEVELOPS]-(course:Course {college: $college})
WHERE toLower(sk.name) CONTAINS 'programming'
RETURN emp.name AS name, emp.sector AS sector, emp.description AS description,
       collect(DISTINCT occ.title) AS occupations,
       count(DISTINCT sk) AS matching_skills,
       collect(DISTINCT sk.name) AS skills
ORDER BY matching_skills DESC

Question: "Employers with the most skill alignment"
MATCH (col:College {name: $college})-[:IN_MARKET]->(r:Region)<-[:IN_MARKET]-(emp:Employer)-[:HIRES_FOR]->(occ:Occupation)-[:REQUIRES_SKILL]->(sk:Skill)<-[:DEVELOPS]-(course:Course {college: $college})
RETURN emp.name AS name, emp.sector AS sector, emp.description AS description,
       collect(DISTINCT occ.title) AS occupations,
       count(DISTINCT sk) AS matching_skills,
       collect(DISTINCT sk.name) AS skills
ORDER BY matching_skills DESC

Respond with a JSON object containing two fields:
1. "cypher": the Cypher query as a string
2. "interpretation": a single sentence explaining what this query does in plain English, written for a non-technical workforce development coordinator. Be specific about the filtering criteria and mention skill alignment where relevant.

No markdown code fences. Just the raw JSON object."""


async def run_employer_query(question: str, college: str) -> tuple[list[EmployerMatch], str, str]:
    """Translate a natural language question into a Cypher query and return employer results."""
    logger.info(f"Employer query: {question!r} for college: {college!r}")

    cypher, interpretation = generate_query(question, college, EMPLOYER_QUERY_PROMPT)
    cypher = validate_cypher(cypher)
    logger.info(f"Validated Cypher: {cypher!r}")

    records = execute_query(cypher, college)
    employers = [
        EmployerMatch(
            name=r["name"],
            sector=r.get("sector"),
            description=r.get("description"),
            occupations=r.get("occupations", []),
            matching_skills=r.get("matching_skills", 0),
            skills=r.get("skills", []),
        )
        for r in records
    ]

    count = len(employers)
    count_text = f"{count} employer{'s' if count != 1 else ''} found."
    message = f"{count_text} {interpretation}" if interpretation else count_text
    logger.info(f"Query complete: {message}")

    return employers, message, cypher
