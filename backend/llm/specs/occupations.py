"""Occupation query spec, Cypher template, and NL renderer."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

from .base import NumericFilter, render_op_label

OrderField = Literal[
    "aligned_course_count", "annual_wage", "employment",
    "growth_rate", "annual_openings",
]


class OccupationSpec(BaseModel):
    """Structured intent of an occupation NL query."""
    title_contains: list[str] | None = None
    education_level: str | None = None
    order_by: OrderField = "aligned_course_count"
    order_dir: Literal["asc", "desc"] = "desc"
    limit: int | None = None


# ── Cypher template ─────────────────────────────────────────────────
#
# The occupation list is grounded in PREPARES_FOR — the institutional
# Course→Occupation crosswalk — rather than the retired skill-overlap
# bridge. count(DISTINCT course) measures institutional curriculum
# depth at this college for each SOC.

_BASE_TRAVERSAL = (
    "MATCH (col:College {name: $college})-[:IN_MARKET]->(r:Region)"
    "-[d:DEMANDS]->(occ:Occupation)"
    "<-[:PREPARES_FOR]-(course:Course {college: $college})"
    "<-[:CONTAINS]-(dept:Department)"
)

_RETURN_CLAUSE = (
    "RETURN occ.soc_code AS soc_code, occ.title AS title,\n"
    "       occ.description AS description, d.annual_wage AS annual_wage,\n"
    "       d.employment AS employment, d.growth_rate AS growth_rate,\n"
    "       d.annual_openings AS annual_openings,\n"
    "       occ.education_level AS education_level,\n"
    "       count(DISTINCT course) AS aligned_course_count,\n"
    "       count(DISTINCT dept) AS aligned_department_count"
)

_ORDER_FIELD_TO_CYPHER = {
    "aligned_course_count": "aligned_course_count",
    "annual_wage": "d.annual_wage",
    "employment": "d.employment",
    "growth_rate": "d.growth_rate",
    "annual_openings": "d.annual_openings",
}


def _ors(prop_access: str, terms: list[str], param_prefix: str, params: dict) -> str:
    """Build (toLower(prop) CONTAINS $p_0 [OR ...])."""
    ors = []
    for i, term in enumerate(terms):
        key = f"{param_prefix}_{i}"
        params[key] = term.lower()
        ors.append(f"toLower({prop_access}) CONTAINS ${key}")
    return ors[0] if len(ors) == 1 else f"({' OR '.join(ors)})"


def render_cypher(spec: OccupationSpec) -> tuple[str, dict]:
    """Render spec → Cypher + parameter dict."""
    where_clauses: list[str] = []
    params: dict[str, object] = {}

    if spec.title_contains:
        where_clauses.append(_ors("occ.title", spec.title_contains, "title_q", params))
    if spec.education_level:
        where_clauses.append("occ.education_level = $education_level")
        params["education_level"] = spec.education_level

    where_clause = ""
    if where_clauses:
        where_clause = "WHERE " + " AND ".join(where_clauses) + "\n"

    order = f"ORDER BY {_ORDER_FIELD_TO_CYPHER[spec.order_by]} {spec.order_dir.upper()}"
    cypher = f"{_BASE_TRAVERSAL}\n{where_clause}{_RETURN_CLAUSE}\n{order}"
    if spec.limit:
        cypher += f"\nLIMIT {spec.limit}"
    return cypher, params


# ── Interpretation (deterministic NL from spec) ──────────────────────

def interpret_spec(spec: OccupationSpec) -> str:
    """Render the spec as a sentence the user can audit."""
    parts = []
    if spec.title_contains:
        parts.append(f"with title containing {_quote_list(spec.title_contains)}")
    if spec.education_level:
        parts.append(f"with entry education {spec.education_level!r}")

    sort_descriptions = {
        "aligned_course_count": "ranked by institutional curriculum alignment with the college (TOP-SOC crosswalk)",
        "annual_wage": "ranked by regional median annual wage",
        "employment": "ranked by regional employment count",
        "growth_rate": "ranked by projected 5-year growth rate",
        "annual_openings": "ranked by annual openings in the region",
    }
    sort_desc = sort_descriptions[spec.order_by]
    if spec.order_dir == "asc":
        sort_desc = sort_desc.replace("ranked by", "ranked by lowest")

    filter_clause = " " + " and ".join(parts) if parts else ""
    limit_clause = f", showing top {spec.limit}" if spec.limit else ""
    return f"Showing occupations{filter_clause}, {sort_desc}{limit_clause}."


def _quote_list(terms: list[str]) -> str:
    quoted = [f"'{t}'" for t in terms]
    if len(quoted) == 1:
        return quoted[0]
    if len(quoted) == 2:
        return f"{quoted[0]} or {quoted[1]}"
    return ", ".join(quoted[:-1]) + f", or {quoted[-1]}"


# ── Flash extractor configuration ────────────────────────────────────

EXTRACTOR_PROMPT = """\
You extract structured filter parameters from a user's question about labor-market occupations at a California community college.

The user is asking about occupations: their wages, employment counts, growth rates, regional openings, education requirements, or institutional curriculum alignment with the college. Translate the question into a JSON spec.

Spec fields (all optional unless noted):

title_contains: list of substrings to match against occupation titles. Routing rules:
- A SPECIFIC ROLE NAME (e.g., "software developers") -> ONE substring of the FULL PHRASE LOWERCASED. Example: "software developers" -> ["soft"] (use a short root that captures the title family).
- A FUZZY CONCEPT (e.g., "healthcare jobs") -> a small list of 2-4 root substrings: ["health", "medical", "nurs"].
- Always prefer SHORT ROOT SUBSTRINGS (3-8 chars) — "soft" beats "software development", "manufactur" beats "manufacturing".

education_level: exact match for entry-level education. Allowed values: "Bachelor's degree", "Associate's degree", "High school diploma or equivalent", "Postsecondary nondegree award", "Some college, no degree", "Master's degree", "Doctoral or professional degree". Use only when education is explicitly mentioned.

order_by: one of "aligned_course_count", "annual_wage", "employment", "growth_rate", "annual_openings". Default "aligned_course_count". Routing:
- "highest wages" / "highest paying" / "best paying" -> annual_wage
- "most jobs" / "biggest employer" -> employment
- "fastest growing" / "growing the most" -> growth_rate
- "most openings" / "most yearly openings" -> annual_openings
- "best aligned with curriculum" / "best institutional fit" / no explicit sort -> aligned_course_count

order_dir: "asc" or "desc". Default "desc". For "lowest" use "asc".

limit: integer if user asks for "top N".

Rules:
- Always use SHORT root substrings to maximize matches.
- Don't invent constraints not in the question.
- If the question can't be expressed in this schema, set unsupported=true and provide a short unsupported_reason. Specifically unsupported:
    - Skill-based filters ("occupations requiring X skill") — the bridge to occupations is now via the institutional TOP-SOC crosswalk, not a skill index. Suggest the user filter by title or order by curriculum alignment instead.
    - Cross-occupation comparisons ("which occupations match each other most")
    - Aggregations or rankings not expressible by order_by alone ("the top 10% by something")
    - References to properties not in the schema (region intersections, time-series questions, etc.)

Respond with a JSON object matching the schema exactly. No prose."""


SPEC_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "title_contains": {"type": "ARRAY", "nullable": True, "items": {"type": "STRING"}},
        "education_level": {"type": "STRING", "nullable": True},
        "order_by": {"type": "STRING", "enum": [
            "aligned_course_count", "annual_wage", "employment",
            "growth_rate", "annual_openings",
        ]},
        "order_dir": {"type": "STRING", "enum": ["asc", "desc"]},
        "limit": {"type": "INTEGER", "nullable": True},
        "unsupported": {"type": "BOOLEAN", "nullable": True},
        "unsupported_reason": {"type": "STRING", "nullable": True},
    },
    "required": ["order_by", "order_dir"],
}
