"""Semantic translation layer for Course queries."""

import logging
from workflows.query_engine import validate_cypher, generate_query, execute_query
from models import CourseSummary

logger = logging.getLogger(__name__)

COURSE_QUERY_PROMPT = """You are a Cypher query generator for a Neo4j graph database containing California community college course catalog data. You translate natural language questions about courses into valid Cypher queries.

SCHEMA:

Nodes:
- Course (properties: code, college, name, department, units, description, prerequisites, skill_mappings, learning_outcomes, course_objectives, transfer_status)
  transfer_status: one of "CSU/UC", "CSU Only", "UC Only", "Non-Transferable"
  skill_mappings: list of skill name strings
  learning_outcomes: list of strings
  course_objectives: list of strings
- Department (properties: name)
- Skill (properties: name)

Relationships:
- (Department)-[CONTAINS]->(Course)
- (Course)-[DEVELOPS]->(Skill)

RULES:
1. Every query MUST scope to the college: use {college: $college} on Course nodes.
2. ONLY use MATCH, OPTIONAL MATCH, WITH, WHERE, RETURN, ORDER BY, LIMIT, UNWIND, count, collect, DISTINCT, AND, OR, NOT, IN, CONTAINS, STARTS WITH, ENDS WITH, size, toLower, toUpper.
3. NEVER use CREATE, DELETE, SET, MERGE, REMOVE, DROP, DETACH, CALL, FOREACH, LOAD, or any write/mutation clause.
4. Always return results in this exact shape:
     RETURN c.name AS name, c.code AS code, c.description AS description,
            c.learning_outcomes AS learning_outcomes, c.course_objectives AS course_objectives,
            c.skill_mappings AS skill_mappings
5. Do NOT add a LIMIT clause unless the user asks for a specific number.
6. If the question cannot be answered with the schema above, respond with: {"cypher": "CANNOT_TRANSLATE", "interpretation": ""}
7. The current college is provided in the user message. The $college parameter is always set to that college. If the user references a DIFFERENT college by name, respond with CANNOT_TRANSLATE.
8. If the question asks about departments (e.g. "which departments have the most courses") rather than individual courses, respond with CANNOT_TRANSLATE and set interpretation to suggest rephrasing (e.g. "Try asking about courses in a specific department, like 'Computer Science courses'").
9. For skill-based queries, traverse: MATCH (c:Course {college: $college})-[:DEVELOPS]->(sk:Skill) WHERE toLower(sk.name) CONTAINS '...'
10. For department queries, filter: WHERE toLower(c.department) CONTAINS '...'

EXAMPLES:

Question: "Computer Science courses"
MATCH (c:Course {college: $college})
WHERE toLower(c.department) CONTAINS 'computer science'
RETURN c.name AS name, c.code AS code, c.description AS description,
       c.learning_outcomes AS learning_outcomes, c.course_objectives AS course_objectives,
       c.skill_mappings AS skill_mappings
ORDER BY c.code

Question: "Courses that develop Programming skills"
MATCH (c:Course {college: $college})-[:DEVELOPS]->(sk:Skill)
WHERE toLower(sk.name) CONTAINS 'programming'
WITH DISTINCT c
RETURN c.name AS name, c.code AS code, c.description AS description,
       c.learning_outcomes AS learning_outcomes, c.course_objectives AS course_objectives,
       c.skill_mappings AS skill_mappings
ORDER BY c.code

Question: "Transfer-eligible courses"
MATCH (c:Course {college: $college})
WHERE c.transfer_status IN ['CSU/UC', 'CSU Only', 'UC Only']
RETURN c.name AS name, c.code AS code, c.description AS description,
       c.learning_outcomes AS learning_outcomes, c.course_objectives AS course_objectives,
       c.skill_mappings AS skill_mappings
ORDER BY c.code

Question: "Courses with more than 3 units"
MATCH (c:Course {college: $college})
WHERE c.units > 3
RETURN c.name AS name, c.code AS code, c.description AS description,
       c.learning_outcomes AS learning_outcomes, c.course_objectives AS course_objectives,
       c.skill_mappings AS skill_mappings
ORDER BY c.code

Question: "Nursing courses"
MATCH (c:Course {college: $college})
WHERE toLower(c.department) CONTAINS 'nursing'
RETURN c.name AS name, c.code AS code, c.description AS description,
       c.learning_outcomes AS learning_outcomes, c.course_objectives AS course_objectives,
       c.skill_mappings AS skill_mappings
ORDER BY c.code

Respond with a JSON object containing two fields:
1. "cypher": the Cypher query as a string
2. "interpretation": a single sentence explaining what this query does in plain English, written for a non-technical workforce development coordinator. Be specific about the filtering criteria.

No markdown code fences. Just the raw JSON object."""


async def run_course_query(question: str, college: str) -> tuple[list[CourseSummary], str, str]:
    """Translate a natural language question into a Cypher query and return course results."""
    logger.info(f"Course query: {question!r} for college: {college!r}")

    cypher, interpretation = generate_query(question, college, COURSE_QUERY_PROMPT)
    cypher = validate_cypher(cypher)
    logger.info(f"Validated Cypher: {cypher!r}")

    records = execute_query(cypher, college)
    courses = [
        CourseSummary(
            name=r["name"],
            code=r.get("code", ""),
            description=r.get("description", ""),
            learning_outcomes=r.get("learning_outcomes") or [],
            course_objectives=r.get("course_objectives") or [],
            skill_mappings=r.get("skill_mappings") or [],
        )
        for r in records
    ]

    count = len(courses)
    count_text = f"{count} course{'s' if count != 1 else ''} found."
    message = f"{count_text} {interpretation}" if interpretation else count_text
    logger.info(f"Query complete: {message}")

    return courses, message, cypher
