"""Student query spec, Cypher template, and NL renderer.

The student template now has two valid base traversals depending on
the spec:

  1. Plain anchor — `(s)-[:ENROLLED_IN]->(:Course {college: $college})`
     used when no course-property filter is set.
  2. Course-property-anchored — when course_code, course_name, term,
     or status filters are set, MATCH on the enrollment edge with
     filter on the course/edge properties.

The skill-anchored path was retired with the Skill abstraction; the
TOP-SOC institutional crosswalk now bridges curriculum to occupations.
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

from .base import NumericFilter, NUMERIC_FILTER_SCHEMA, render_op_label


class StudentSpec(BaseModel):
    """Structured intent of a student NL query."""
    primary_focus_contains: list[str] | None = None
    gpa: NumericFilter | None = None
    courses_completed: NumericFilter | None = None
    course_code_contains: str | None = None
    course_name_contains: str | None = None
    enrollment_term: str | None = None
    enrollment_status: Literal["Completed", "Withdrawn"] | None = None
    order_by: Literal["gpa", "courses_completed"] = "courses_completed"
    order_dir: Literal["asc", "desc"] = "desc"
    limit: int | None = None


_RETURN_CLAUSE = (
    "RETURN s.uuid AS uuid, s.gpa AS gpa, "
    "s.primary_focus AS primary_focus, "
    "s.courses_completed AS courses_completed"
)


def _ors(prop_access: str, terms: list[str], param_prefix: str, params: dict) -> str:
    ors = []
    for i, term in enumerate(terms):
        key = f"{param_prefix}_{i}"
        params[key] = term.lower()
        ors.append(f"toLower({prop_access}) CONTAINS ${key}")
    return ors[0] if len(ors) == 1 else f"({' OR '.join(ors)})"


def render_cypher(spec: StudentSpec) -> tuple[str, dict]:
    params: dict[str, object] = {}
    has_course_filter = bool(
        spec.course_code_contains or spec.course_name_contains
        or spec.enrollment_term or spec.enrollment_status
    )

    student_filters: list[str] = []
    if spec.primary_focus_contains:
        student_filters.append(_ors("s.primary_focus", spec.primary_focus_contains, "pf_q", params))
    if spec.gpa:
        student_filters.append(f"s.gpa {spec.gpa.op} $gpa_v")
        params["gpa_v"] = spec.gpa.value
    if spec.courses_completed:
        student_filters.append(f"s.courses_completed {spec.courses_completed.op} $cc_v")
        params["cc_v"] = spec.courses_completed.value

    if has_course_filter:
        course_filters: list[str] = []
        if spec.course_code_contains:
            # OR fallback: code substring also matched against name.
            course_filters.append(
                "(c.code CONTAINS $code_q OR toLower(c.name) CONTAINS toLower($code_q))"
            )
            params["code_q"] = spec.course_code_contains
        if spec.course_name_contains:
            course_filters.append("toLower(c.name) CONTAINS $name_q")
            params["name_q"] = spec.course_name_contains.lower()
        if spec.enrollment_term:
            course_filters.append("e.term = $term_v")
            params["term_v"] = spec.enrollment_term
        if spec.enrollment_status:
            course_filters.append("e.status = $status_v")
            params["status_v"] = spec.enrollment_status

        all_filters = course_filters + student_filters
        cypher_lines = ["MATCH (s:Student)-[e:ENROLLED_IN]->(c:Course {college: $college})"]
        if all_filters:
            cypher_lines.append(f"WHERE {' AND '.join(all_filters)}")
        cypher_lines.append("WITH DISTINCT s")
    else:
        cypher_lines = [
            "MATCH (s:Student)-[:ENROLLED_IN]->(:Course {college: $college})",
            "WITH DISTINCT s",
        ]
        if student_filters:
            cypher_lines.append(f"WHERE {' AND '.join(student_filters)}")

    cypher_lines.append(_RETURN_CLAUSE)
    order_field = "s.gpa" if spec.order_by == "gpa" else "s.courses_completed"
    cypher_lines.append(f"ORDER BY {order_field} {spec.order_dir.upper()}")
    if spec.limit:
        cypher_lines.append(f"LIMIT {spec.limit}")

    return "\n".join(cypher_lines), params


def interpret_spec(spec: StudentSpec) -> str:
    parts = []
    if spec.primary_focus_contains:
        parts.append(f"with primary focus containing {_quote_list(spec.primary_focus_contains)}")
    if spec.gpa:
        parts.append(f"with GPA {render_op_label(spec.gpa.op)} {spec.gpa.value}")
    if spec.courses_completed:
        parts.append(
            f"with courses completed {render_op_label(spec.courses_completed.op)} "
            f"{int(spec.courses_completed.value)}"
        )
    if spec.course_code_contains:
        parts.append(f"enrolled in courses matching code/name '{spec.course_code_contains}'")
    if spec.course_name_contains:
        parts.append(f"enrolled in courses with name containing '{spec.course_name_contains}'")
    if spec.enrollment_term:
        parts.append(f"in term '{spec.enrollment_term}'")
    if spec.enrollment_status:
        parts.append(f"with enrollment status {spec.enrollment_status!r}")

    sort_field = "GPA" if spec.order_by == "gpa" else "courses completed"
    sort_dir = "ascending" if spec.order_dir == "asc" else "descending"
    filter_clause = " " + " and ".join(parts) if parts else ""
    limit_clause = f", showing top {spec.limit}" if spec.limit else ""
    return f"Showing students{filter_clause}, ranked by {sort_field} ({sort_dir}){limit_clause}."


def _quote_list(terms: list[str]) -> str:
    quoted = [f"'{t}'" for t in terms]
    if len(quoted) == 1:
        return quoted[0]
    if len(quoted) == 2:
        return f"{quoted[0]} or {quoted[1]}"
    return ", ".join(quoted[:-1]) + f", or {quoted[-1]}"


EXTRACTOR_PROMPT = """\
You extract structured filter parameters from a user's question about students at a California community college.

Spec fields (all optional):

primary_focus_contains: list of substrings to match against student.primary_focus. Routing:
- A SPECIFIC PROGRAM NAME (e.g., "Construction Technology", "Early Childhood Education") -> ONE substring of the full phrase, lowercased. Don't split compound program names.
- A FUZZY CONCEPT WORD (e.g., "healthcare", "tech") -> small list of 2-4 root substrings: "healthcare" -> ["health", "medical", "nursing"]; "tech" -> ["tech", "comput", "engineer"].
- A SINGLE NOUN that's also a program-name root -> ONE root: "biology" -> ["biolog"], "engineering" -> ["engineer"], "accounting" -> ["account"].

gpa, courses_completed: numeric filters. Format: {"op": ">" | ">=" | "<" | "<=" | "=" | "!=", "value": <number>}. "above 3.0" -> {">", 3.0}; "honor roll" -> {">=", 3.5}; "more than 15 courses" -> {">", 15}.

course_code_contains: substring of a course code (uppercase). Use when user mentions a specific course code (e.g., "MATH 1A"). The system will also check course name with the same string.

course_name_contains: substring of course name (lowercased). Use when user mentions a course by name keyword (e.g., "calculus") and not a code.

enrollment_term: exact term string (e.g., "Fall 2024", "Spring 2023").

enrollment_status: "Completed" or "Withdrawn".

order_by: "gpa" or "courses_completed". Default "courses_completed". Use "gpa" only when the user signals it ("highest GPA", "best students by grade").

order_dir: "asc" or "desc". Default "desc". Use "asc" for "lowest" or "least".

limit: integer for "top N".

Routing examples:
- "Students specializing in 'X'" -> primary_focus_contains
- "Students who took X" -> course_code_contains or course_name_contains
- "Engineering students with GPA above 3.5" -> primary_focus_contains: ["engineer"], gpa: {">", 3.5}
- "Honor-roll Engineering students who took Calculus" -> primary_focus_contains: ["engineer"], gpa: {">=", 3.5}, course_name_contains: "calculus"

If the question can't be expressed, set unsupported=true with unsupported_reason. In particular, queries that ask about students' "skills" are no longer supported — student preparation is now expressed via completed courses and the institutional TOP-SOC crosswalk that maps those courses to occupations.

Respond with a JSON object matching the schema exactly. No prose."""


SPEC_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "primary_focus_contains": {"type": "ARRAY", "nullable": True, "items": {"type": "STRING"}},
        "gpa": {**NUMERIC_FILTER_SCHEMA, "nullable": True},
        "courses_completed": {**NUMERIC_FILTER_SCHEMA, "nullable": True},
        "course_code_contains": {"type": "STRING", "nullable": True},
        "course_name_contains": {"type": "STRING", "nullable": True},
        "enrollment_term": {"type": "STRING", "nullable": True},
        "enrollment_status": {"type": "STRING", "nullable": True, "enum": ["Completed", "Withdrawn"]},
        "order_by": {"type": "STRING", "enum": ["gpa", "courses_completed"]},
        "order_dir": {"type": "STRING", "enum": ["asc", "desc"]},
        "limit": {"type": "INTEGER", "nullable": True},
        "unsupported": {"type": "BOOLEAN", "nullable": True},
        "unsupported_reason": {"type": "STRING", "nullable": True},
    },
}
