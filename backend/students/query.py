"""Semantic translation layer for Student queries."""

import logging
from llm.query_engine import validate_cypher, generate_query, execute_query
from llm.spec_engine import execute_spec, is_enabled_for, run_spec
from students.models import StudentSummary

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
9. For department-based queries on courses, use case-insensitive matching with toLower() or CONTAINS on c.department.
10. For queries about specific courses, match on c.code or c.name using CONTAINS.
11. For primary_focus queries, use case-insensitive matching: toLower(s.primary_focus) CONTAINS toLower('...').

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

Question: "Students specializing in 'construction technology'"
MATCH (s:Student)-[:ENROLLED_IN]->(:Course {college: $college})
WITH DISTINCT s
WHERE toLower(s.primary_focus) CONTAINS 'construction'
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

Question: "Honor-roll Engineering students who took Calculus"
MATCH (s:Student)-[:ENROLLED_IN]->(c:Course {college: $college})
WITH DISTINCT s, c
WHERE toLower(s.primary_focus) CONTAINS 'engineering'
  AND s.gpa >= 3.5
  AND (toLower(c.name) CONTAINS 'calculus' OR c.code CONTAINS 'MATH 1')
WITH DISTINCT s
RETURN s.uuid AS uuid, s.gpa AS gpa, s.primary_focus AS primary_focus, s.courses_completed AS courses_completed
ORDER BY s.gpa DESC, s.courses_completed DESC

Question: "Students who completed at least 20 courses with GPA above 3.0"
MATCH (s:Student)-[:ENROLLED_IN]->(:Course {college: $college})
WITH DISTINCT s
WHERE s.courses_completed >= 20 AND s.gpa > 3.0
RETURN s.uuid AS uuid, s.gpa AS gpa, s.primary_focus AS primary_focus, s.courses_completed AS courses_completed
ORDER BY s.gpa DESC, s.courses_completed DESC

Question: "Top 10 students by GPA in the Nursing program"
MATCH (s:Student)-[:ENROLLED_IN]->(:Course {college: $college})
WITH DISTINCT s
WHERE toLower(s.primary_focus) CONTAINS 'nursing'
RETURN s.uuid AS uuid, s.gpa AS gpa, s.primary_focus AS primary_focus, s.courses_completed AS courses_completed
ORDER BY s.gpa DESC
LIMIT 10

Respond with a JSON object containing two fields:
1. "cypher": the Cypher query as a string
2. "interpretation": a single sentence explaining what this query does in plain English, written for a non-technical workforce development coordinator. Clarify the specific filtering logic — e.g., "students whose primary academic focus is Computer Science" or "students who have completed at least one course that develops Programming skills". Be specific about what criteria define the result set.

No markdown code fences. Just the raw JSON object."""


async def run_student_query(question: str, college: str) -> tuple[list[StudentSummary], str, str]:
    """Translate a natural language question into a Cypher query, execute it, and return results.

    Spec-engine path is off by default for students (feature-flagged
    via `SPEC_ENGINE_STUDENT=1`). When the flag is off, the legacy
    Sonnet path generates Cypher directly. Students has the most
    architecturally complex spec (three valid base traversals), so it
    rolls out after the other features have validated in production.
    """
    logger.info(f"Student query: {question!r} for college: {college!r}")

    if is_enabled_for("student"):
        result = run_spec(question, college, "student")
        if result.unsupported:
            reason = result.unsupported_reason or ""
            raise ValueError(
                "This question doesn't fit our student query patterns. "
                f"{reason} Try one of the example queries shown above the search box."
            )
        records = execute_spec(result)
        cypher = result.cypher
        interpretation = result.interpretation
    else:
        cypher, interpretation = generate_query(
            question, college, STUDENT_QUERY_PROMPT, view="student",
        )
        cypher = validate_cypher(cypher)
        records = execute_query(cypher, college)
    logger.info(f"Cypher: {cypher!r}")
    students = [
        StudentSummary(
            uuid=r["uuid"],
            gpa=r.get("gpa", 0.0),
            primary_focus=r.get("primary_focus", "Undeclared"),
            courses_completed=r.get("courses_completed", 0),
        )
        for r in records
    ]

    count = len(students)
    count_text = f"{count} student{'s' if count != 1 else ''} found."
    message = f"{count_text} {interpretation}" if interpretation else count_text
    logger.info(f"Query complete: {message}")

    return students, message, cypher
