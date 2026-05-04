"""Course query spec, Cypher template, and NL renderer."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

from .base import NumericFilter, NUMERIC_FILTER_SCHEMA, render_op_label

TransferStatus = Literal["CSU/UC", "CSU Only", "UC Only", "Non-Transferable"]


class CourseSpec(BaseModel):
    department_contains: list[str] | None = None
    topic_contains: list[str] | None = None  # OR over (department OR course name)
    name_contains: str | None = None
    code_contains: str | None = None
    units: NumericFilter | None = None
    is_cte: bool | None = None
    transfer_status_in: list[TransferStatus] | None = None
    no_prerequisites: bool | None = None
    limit: int | None = None


_RETURN_CLAUSE = (
    "RETURN c.name AS name, c.code AS code, c.description AS description,\n"
    "       c.learning_outcomes AS learning_outcomes,\n"
    "       c.course_objectives AS course_objectives,\n"
    "       c.top_code AS top_code"
)


def _ors(prop_access: str, terms: list[str], param_prefix: str, params: dict) -> str:
    ors = []
    for i, term in enumerate(terms):
        key = f"{param_prefix}_{i}"
        params[key] = term.lower()
        ors.append(f"toLower({prop_access}) CONTAINS ${key}")
    return ors[0] if len(ors) == 1 else f"({' OR '.join(ors)})"


def render_cypher(spec: CourseSpec) -> tuple[str, dict]:
    params: dict[str, object] = {}
    where_clauses: list[str] = []

    if spec.department_contains:
        where_clauses.append(_ors("c.department", spec.department_contains, "dept_q", params))

    if spec.topic_contains:
        # OR across two properties: department, course name. (Skills are
        # no longer in the schema; the institutional bridge is via
        # PREPARES_FOR/Course.top_code.)
        sub_clauses = []
        for i, term in enumerate(spec.topic_contains):
            key = f"topic_q_{i}"
            params[key] = term.lower()
            sub_clauses.append(f"toLower(c.department) CONTAINS ${key}")
            sub_clauses.append(f"toLower(c.name) CONTAINS ${key}")
        where_clauses.append(f"({' OR '.join(sub_clauses)})")

    if spec.name_contains:
        where_clauses.append("toLower(c.name) CONTAINS $name_q")
        params["name_q"] = spec.name_contains.lower()

    if spec.code_contains:
        where_clauses.append("c.code CONTAINS $code_q")
        params["code_q"] = spec.code_contains

    if spec.units is not None:
        where_clauses.append(f"c.units {spec.units.op} $units_v")
        params["units_v"] = spec.units.value

    if spec.is_cte is not None:
        where_clauses.append(f"c.is_cte = {'true' if spec.is_cte else 'false'}")

    if spec.transfer_status_in:
        where_clauses.append("c.transfer_status IN $transfer_statuses")
        params["transfer_statuses"] = list(spec.transfer_status_in)

    if spec.no_prerequisites:
        where_clauses.append("(c.prerequisites IS NULL OR c.prerequisites = '')")

    match_clause = "MATCH (c:Course {college: $college})"

    where_clause = ""
    if where_clauses:
        where_clause = "WHERE " + " AND ".join(where_clauses) + "\n"

    cypher = f"{match_clause}\n{where_clause}{_RETURN_CLAUSE}\nORDER BY c.code"

    if spec.limit:
        cypher += f"\nLIMIT {spec.limit}"
    return cypher, params


def interpret_spec(spec: CourseSpec) -> str:
    parts = []
    if spec.department_contains:
        parts.append(f"in departments containing {_quote_list(spec.department_contains)}")
    if spec.topic_contains:
        parts.append(f"related to {_quote_list(spec.topic_contains)} (department or course name)")
    if spec.name_contains:
        parts.append(f"with name containing '{spec.name_contains}'")
    if spec.code_contains:
        parts.append(f"with code containing '{spec.code_contains}'")
    if spec.units is not None:
        parts.append(f"with units {render_op_label(spec.units.op)} {spec.units.value}")
    if spec.is_cte is True:
        parts.append("classified as career and technical education (CTE)")
    elif spec.is_cte is False:
        parts.append("NOT classified as CTE")
    if spec.transfer_status_in:
        parts.append(f"transferable as {', '.join(spec.transfer_status_in)}")
    if spec.no_prerequisites:
        parts.append("with no prerequisites")

    filter_clause = " " + " and ".join(parts) if parts else ""
    limit_clause = f", showing the first {spec.limit}" if spec.limit else ""
    return f"Showing courses{filter_clause}, ordered by course code{limit_clause}."


def _quote_list(terms: list[str]) -> str:
    quoted = [f"'{t}'" for t in terms]
    if len(quoted) == 1:
        return quoted[0]
    if len(quoted) == 2:
        return f"{quoted[0]} or {quoted[1]}"
    return ", ".join(quoted[:-1]) + f", or {quoted[-1]}"


EXTRACTOR_PROMPT = """\
You extract structured filter parameters from a user's question about courses in a California community college catalog.

Spec fields (all optional):

department_contains: list of substrings to match against course.department. Routing:
- A SPECIFIC DEPARTMENT NAME (e.g., "computer science") -> ONE substring of the full phrase, lowercased: ["computer science"].
- A FUZZY CONCEPT WORD (e.g., "healthcare") -> list of 2-4 root substrings: ["health", "medical", "nursing"].
- A SINGLE NOUN -> ONE root: "biology" -> ["biolog"], "manufacturing" -> ["manufactur"].

topic_contains: list of substrings searched ACROSS department names AND course names. Use this for BARE-NOUN QUERIES where the user doesn't specify department vs. course-name match — the topic search catches either. Examples:
- "Welding courses" -> topic_contains: ["weld"]
- "Programming courses" -> topic_contains: ["program"]
PREFER topic_contains over department_contains for bare nouns. Use department_contains only when the user explicitly says "[X] department".

name_contains: substring of course name (lowercased). Use when user mentions a specific course by name keyword (e.g., "calculus", "anatomy").

code_contains: substring of course code (uppercase, e.g., "MATH 1A").

units: numeric filter on course units. Format: {"op": ">" | ">=" | "<" | "<=" | "=" | "!=", "value": <number>}. Examples: "at least 4 units" -> {"op": ">=", "value": 4}, "5-unit courses" -> {"op": "=", "value": 5}.

is_cte: true if user asks for CTE / "career and technical education" courses.

transfer_status_in: array. Allowed values: "CSU/UC", "CSU Only", "UC Only", "Non-Transferable". Mappings:
- "transferable" / "transfer-eligible" -> ["CSU/UC", "CSU Only", "UC Only"]
- "transferable to UC" -> ["CSU/UC", "UC Only"]
- "transferable to CSU" -> ["CSU/UC", "CSU Only"]
- "non-transferable" -> ["Non-Transferable"]

no_prerequisites: true if user asks for courses with no prerequisites.

limit: integer for "top N".

COMPOUND QUESTIONS: when the user combines multiple constraints ("Transferable nursing courses", "5-unit math courses with no prerequisites"), extract ALL applicable filters. Don't drop any.

Routing examples:
- "Computer Science courses" -> department_contains: ["computer science"]
- "Welding courses" -> topic_contains: ["weld"]
- "Healthcare department courses" -> department_contains: ["health", "medical", "nursing"]
- "CTE courses" -> is_cte: true
- "Transferable nursing courses" -> transfer_status_in: [...] AND topic_contains: ["nurs"]
- "5-unit math courses" -> department_contains: ["math"], units: {"op": "=", "value": 5}

If the question can't be expressed, set unsupported=true with unsupported_reason. In particular, queries that ask about "skills" are no longer supported — courses now bridge to occupations through the institutional TOP-SOC crosswalk, not through a skill index.

Respond with a JSON object matching the schema exactly. No prose."""


SPEC_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "department_contains": {"type": "ARRAY", "nullable": True, "items": {"type": "STRING"}},
        "topic_contains": {"type": "ARRAY", "nullable": True, "items": {"type": "STRING"}},
        "name_contains": {"type": "STRING", "nullable": True},
        "code_contains": {"type": "STRING", "nullable": True},
        "units": {**NUMERIC_FILTER_SCHEMA, "nullable": True},
        "is_cte": {"type": "BOOLEAN", "nullable": True},
        "transfer_status_in": {
            "type": "ARRAY", "nullable": True,
            "items": {"type": "STRING", "enum": ["CSU/UC", "CSU Only", "UC Only", "Non-Transferable"]},
        },
        "no_prerequisites": {"type": "BOOLEAN", "nullable": True},
        "limit": {"type": "INTEGER", "nullable": True},
        "unsupported": {"type": "BOOLEAN", "nullable": True},
        "unsupported_reason": {"type": "STRING", "nullable": True},
    },
}
