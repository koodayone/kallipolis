import os
import re
import json
import logging
import anthropic
from ontology.schema import get_driver
from models import StudentSummary

logger = logging.getLogger(__name__)

STUDENT_QUERY_PROMPT = """You are a Cypher query generator for a Neo4j graph database containing California community college student data. You translate natural language questions about students into valid Cypher queries.

SCHEMA:

Nodes:
- Student (properties: uuid, gpa, primary_focus, courses_completed)
  gpa: float, grade point average (4.0 scale)
  primary_focus: string, the department where the student completed the most courses (e.g. "Computer Science", "Biology")
  courses_completed: integer, total number of completed courses
- Course (properties: code, college, name, department, units, description, prerequisites, skill_mappings, transfer_status)
- Department (properties: name)
- Skill (properties: name)

Relationships:
- (Student)-[ENROLLED_IN {grade, term, status}]->(Course)
  grade: one of "A", "B", "C", "D", "F", "W", "P", "NP"
  term: string like "Fall 2023", "Spring 2024"
  status: "Completed" or "Withdrawn"
- (Student)-[HAS_SKILL]->(Skill)
- (Department)-[CONTAINS]->(Course)
- (Course)-[DEVELOPS]->(Skill)

RULES:
1. Every query MUST scope to the college. Use this anchor pattern to establish college scope:
     MATCH (s:Student)-[:ENROLLED_IN]->(:Course {college: $college})
     WITH DISTINCT s
   Then add additional MATCH/WHERE clauses as needed.
2. ONLY use MATCH, OPTIONAL MATCH, WITH, WHERE, RETURN, ORDER BY, LIMIT, UNWIND, count, collect, DISTINCT, AND, OR, NOT, IN, CONTAINS, STARTS WITH, ENDS WITH, size, toLower, toUpper.
3. NEVER use CREATE, DELETE, SET, MERGE, REMOVE, DROP, DETACH, CALL, FOREACH, LOAD, or any write/mutation clause.
4. Always return results in this exact shape:
     RETURN s.uuid AS uuid, s.gpa AS gpa, s.primary_focus AS primary_focus, s.courses_completed AS courses_completed
5. Do NOT add a LIMIT clause unless the user asks for a specific number (e.g. "top 10").
6. If the question cannot be answered with the schema above, respond with: {"cypher": "CANNOT_TRANSLATE", "interpretation": ""}
7. The current college is provided in the user message. The $college parameter is always set to that college. If the user references a DIFFERENT college by name, respond with CANNOT_TRANSLATE and set interpretation to explain that queries are scoped to the current college.
8. For skill-based queries, use case-insensitive matching with toLower() or CONTAINS on Skill.name.
8. For department-based queries on courses, use case-insensitive matching with toLower() or CONTAINS on c.department.
9. For queries about specific courses, match on c.code or c.name using CONTAINS.
10. For primary_focus queries, use case-insensitive matching: toLower(s.primary_focus) CONTAINS toLower('...').

EXAMPLES:

Question: "Students with highest GPA"
MATCH (s:Student)-[:ENROLLED_IN]->(:Course {college: $college})
WITH DISTINCT s
RETURN s.uuid AS uuid, s.gpa AS gpa, s.primary_focus AS primary_focus, s.courses_completed AS courses_completed
ORDER BY s.gpa DESC

Question: "Computer Science students with GPA above 3.0"
MATCH (s:Student)-[:ENROLLED_IN]->(:Course {college: $college})
WITH DISTINCT s
WHERE toLower(s.primary_focus) CONTAINS 'computer science' AND s.gpa > 3.0
RETURN s.uuid AS uuid, s.gpa AS gpa, s.primary_focus AS primary_focus, s.courses_completed AS courses_completed
ORDER BY s.gpa DESC

Question: "Students whose primary focus is Biology"
MATCH (s:Student)-[:ENROLLED_IN]->(:Course {college: $college})
WITH DISTINCT s
WHERE toLower(s.primary_focus) CONTAINS 'biology'
RETURN s.uuid AS uuid, s.gpa AS gpa, s.primary_focus AS primary_focus, s.courses_completed AS courses_completed
ORDER BY s.courses_completed DESC

Question: "Students who completed more than 15 courses"
MATCH (s:Student)-[:ENROLLED_IN]->(:Course {college: $college})
WITH DISTINCT s
WHERE s.courses_completed > 15
RETURN s.uuid AS uuid, s.gpa AS gpa, s.primary_focus AS primary_focus, s.courses_completed AS courses_completed
ORDER BY s.courses_completed DESC

Question: "Students who have Programming skills"
MATCH (s:Student)-[:HAS_SKILL]->(sk:Skill)
WHERE toLower(sk.name) CONTAINS 'programming'
WITH DISTINCT s
MATCH (s)-[:ENROLLED_IN]->(:Course {college: $college})
WITH DISTINCT s
RETURN s.uuid AS uuid, s.gpa AS gpa, s.primary_focus AS primary_focus, s.courses_completed AS courses_completed
ORDER BY s.courses_completed DESC

Question: "Who withdrew from courses in Fall 2024?"
MATCH (s:Student)-[e:ENROLLED_IN]->(c:Course {college: $college})
WHERE e.status = 'Withdrawn' AND e.term = 'Fall 2024'
WITH DISTINCT s
RETURN s.uuid AS uuid, s.gpa AS gpa, s.primary_focus AS primary_focus, s.courses_completed AS courses_completed
ORDER BY s.courses_completed DESC

Question: "Show me students enrolled in MATH 1A"
MATCH (s:Student)-[e:ENROLLED_IN]->(c:Course {college: $college})
WHERE c.code CONTAINS 'MATH 1A' OR toLower(c.name) CONTAINS 'math 1a'
WITH DISTINCT s
RETURN s.uuid AS uuid, s.gpa AS gpa, s.primary_focus AS primary_focus, s.courses_completed AS courses_completed
ORDER BY s.courses_completed DESC

Question: "Which students have both Critical Thinking and Mathematics skills?"
MATCH (s:Student)-[:HAS_SKILL]->(sk1:Skill), (s)-[:HAS_SKILL]->(sk2:Skill)
WHERE toLower(sk1.name) CONTAINS 'critical thinking' AND toLower(sk2.name) CONTAINS 'mathematics'
WITH DISTINCT s
MATCH (s)-[:ENROLLED_IN]->(:Course {college: $college})
WITH DISTINCT s
RETURN s.uuid AS uuid, s.gpa AS gpa, s.primary_focus AS primary_focus, s.courses_completed AS courses_completed
ORDER BY s.courses_completed DESC

Respond with a JSON object containing two fields:
1. "cypher": the Cypher query as a string
2. "interpretation": a single sentence explaining what this query does in plain English, written for a non-technical workforce development coordinator. Clarify the specific filtering logic — e.g., "students whose primary academic focus is Computer Science" or "students who have completed at least one course that develops Programming skills". Be specific about what criteria define the result set.

No markdown code fences. Just the raw JSON object."""


DISALLOWED_KEYWORDS = {
    "CREATE", "DELETE", "SET", "MERGE", "REMOVE", "DROP",
    "DETACH", "CALL", "FOREACH", "LOAD",
}


def _validate_cypher(cypher: str) -> str:
    """Validate generated Cypher is read-only and college-scoped. Returns cleaned Cypher or raises ValueError."""
    stripped = cypher.strip()

    if "CANNOT_TRANSLATE" in stripped:
        raise ValueError("I couldn't translate that question into a query. Try rephrasing — for example, ask about students by department, skills, GPA, courses, or enrollment status.")

    # Strip markdown code fences if present
    stripped = re.sub(r"^```(?:cypher)?\s*", "", stripped)
    stripped = re.sub(r"\s*```$", "", stripped)
    stripped = stripped.strip().rstrip(";")

    # Tokenize and check for disallowed write keywords
    tokens = re.findall(r"[A-Z_]+", stripped.upper())
    found = DISALLOWED_KEYWORDS.intersection(tokens)
    if found:
        raise ValueError(f"Generated query contains disallowed operations: {', '.join(found)}")

    # Verify college scoping
    if "$college" not in stripped and "college:" not in stripped.lower():
        raise ValueError("Generated query is missing college scope.")

    return stripped


def _parse_llm_response(raw: str) -> tuple[str, str]:
    """Parse the LLM response JSON to extract cypher and interpretation."""
    # Strategy 1: direct JSON parse
    try:
        data = json.loads(raw)
        return data["cypher"], data.get("interpretation", "")
    except (json.JSONDecodeError, KeyError):
        pass

    # Strategy 2: extract from ```json code fences
    match = re.search(r"```json\s*([\s\S]*?)\s*```", raw)
    if match:
        try:
            data = json.loads(match.group(1))
            return data["cypher"], data.get("interpretation", "")
        except (json.JSONDecodeError, KeyError):
            pass

    # Strategy 3: find JSON object via regex
    match = re.search(r"\{[\s\S]*\}", raw)
    if match:
        try:
            data = json.loads(match.group(0))
            return data["cypher"], data.get("interpretation", "")
        except (json.JSONDecodeError, KeyError):
            pass

    # Fallback: treat entire response as raw Cypher (backward-compatible)
    logger.warning(f"Could not parse JSON from LLM response, treating as raw Cypher: {raw[:200]!r}")
    return raw, ""


def _generate_query(question: str, college: str) -> tuple[str, str]:
    """Call Claude to translate a natural language question into Cypher with interpretation."""
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        system=STUDENT_QUERY_PROMPT,
        messages=[{"role": "user", "content": f"[College: {college}]\n\n{question}"}],
    )
    raw = message.content[0].text.strip()
    logger.info(f"LLM response (first 300 chars): {raw[:300]!r}")
    return _parse_llm_response(raw)


def _execute(cypher: str, college: str) -> list[StudentSummary]:
    """Execute validated Cypher and map results directly to StudentSummary."""
    driver = get_driver()
    with driver.session() as session:
        result = session.execute_read(
            lambda tx: tx.run(cypher, college=college).data()
        )

    return [
        StudentSummary(
            uuid=r["uuid"],
            gpa=r.get("gpa", 0.0),
            primary_focus=r.get("primary_focus", "Undeclared"),
            courses_completed=r.get("courses_completed", 0),
        )
        for r in result
    ]


async def run_student_query(question: str, college: str) -> tuple[list[StudentSummary], str, str]:
    """Translate a natural language question into a Cypher query, execute it, and return results."""
    logger.info(f"Student query: {question!r} for college: {college!r}")

    cypher, interpretation = _generate_query(question, college)
    cypher = _validate_cypher(cypher)

    logger.info(f"Validated Cypher: {cypher!r}")

    students = _execute(cypher, college)

    count = len(students)
    count_text = f"{count} student{'s' if count != 1 else ''} found."
    message = f"{count_text} {interpretation}" if interpretation else count_text
    logger.info(f"Query complete: {message}")

    return students, message, cypher
