"""Employer query spec, Cypher template, and NL renderer."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel


class EmployerSpec(BaseModel):
    """Structured intent of an employer NL query."""
    sector_contains: list[str] | None = None
    name_contains: str | None = None
    hires_for_title_contains: list[str] | None = None
    swp_priority_only: bool = False
    limit: int | None = None


# The base traversal joins (college, region, employer, occupation) and
# joins each occupation against the college's institutionally-aligned
# courses through the PREPARES_FOR edge — the Chancellor's Office
# TOP-CIP-SOC crosswalk. Ranking is by aligned_course_count: the count
# of distinct courses the college offers that prepare students for any
# of this employer's hires occupations.
_BASE_TRAVERSAL = (
    "MATCH (col:College {name: $college})-[:IN_MARKET]->(r:Region)"
    "<-[:IN_MARKET]-(emp:Employer)-[:HIRES_FOR]->(occ:Occupation)\n"
    "OPTIONAL MATCH (course:Course {college: $college})-[:PREPARES_FOR]->(occ)"
)

_RETURN_CLAUSE = (
    "RETURN emp.name AS name, emp.sector AS sector,\n"
    "       emp.description AS description, emp.website AS website,\n"
    "       count(DISTINCT occ) AS roles_count,\n"
    "       count(DISTINCT course) AS aligned_course_count"
)


def _ors(prop_access: str, terms: list[str], param_prefix: str, params: dict) -> str:
    ors = []
    for i, term in enumerate(terms):
        key = f"{param_prefix}_{i}"
        params[key] = term.lower()
        ors.append(f"toLower({prop_access}) CONTAINS ${key}")
    return ors[0] if len(ors) == 1 else f"({' OR '.join(ors)})"


def render_cypher(spec: EmployerSpec) -> tuple[str, dict]:
    where_clauses: list[str] = []
    params: dict[str, object] = {}

    if spec.sector_contains:
        where_clauses.append(_ors("emp.sector", spec.sector_contains, "sector_q", params))
    if spec.name_contains:
        where_clauses.append("toLower(emp.name) CONTAINS $name_q")
        params["name_q"] = spec.name_contains.lower()
    if spec.hires_for_title_contains:
        where_clauses.append(_ors("occ.title", spec.hires_for_title_contains, "title_q", params))
    if spec.swp_priority_only:
        where_clauses.append("ANY(s IN emp.swp_sectors WHERE s IN r.priority_sectors)")

    where_clause = ""
    if where_clauses:
        where_clause = "WHERE " + " AND ".join(where_clauses) + "\n"

    cypher = f"{_BASE_TRAVERSAL}\n{where_clause}{_RETURN_CLAUSE}\nORDER BY aligned_course_count DESC"
    if spec.limit:
        cypher += f"\nLIMIT {spec.limit}"
    return cypher, params


def interpret_spec(spec: EmployerSpec) -> str:
    parts = []
    if spec.sector_contains:
        parts.append(f"in sectors containing {_quote_list(spec.sector_contains)}")
    if spec.name_contains:
        parts.append(f"with name containing '{spec.name_contains}'")
    if spec.hires_for_title_contains:
        parts.append(f"hiring for roles containing {_quote_list(spec.hires_for_title_contains)}")
    if spec.swp_priority_only:
        parts.append("in regional Strong Workforce priority sectors")

    filter_clause = " " + " and ".join(parts) if parts else ""
    limit_clause = f", showing top {spec.limit}" if spec.limit else ""
    return (
        f"Showing employers{filter_clause}, ranked by institutional curriculum "
        f"alignment with the college (TOP-SOC crosswalk){limit_clause}."
    )


def _quote_list(terms: list[str]) -> str:
    quoted = [f"'{t}'" for t in terms]
    if len(quoted) == 1:
        return quoted[0]
    if len(quoted) == 2:
        return f"{quoted[0]} or {quoted[1]}"
    return ", ".join(quoted[:-1]) + f", or {quoted[-1]}"


EXTRACTOR_PROMPT = """\
You extract structured filter parameters from a user's question about employers in a California community college's regional labor market.

The base query joins (college, region, employer, occupation, course) and ranks employers by the count of college courses that PREPARES_FOR (institutionally crosswalks to) any of the employer's hires occupations.

Spec fields (all optional):

sector_contains: list of substrings to match against employer.sector. Routing rules:
- A SPECIFIC SECTOR NAME (e.g., "advanced manufacturing", "information and communication technologies") -> ONE substring of the full phrase, lowercased.
- A FUZZY CONCEPT (e.g., "healthcare", "tech") -> small list of 2-4 root substrings: "healthcare" -> ["health", "medical", "hospital"]; "tech" -> ["tech", "softw", "inform"].
- A SINGLE NOUN (e.g., "manufacturing", "construction") -> ONE root: ["manufactur"], ["construct"].

name_contains: substring of the employer's name (lowercased). Use when the user names a specific employer.

hires_for_title_contains: list of substrings to match against occupation titles. Use when user asks "Employers hiring for [role]" or "[role] employers". Same routing as sector_contains: specific role -> single substring; fuzzy concept -> list.

swp_priority_only: true when user mentions Strong Workforce Program priority sectors / regional priority sectors.

limit: integer for "top N".

Routing rules:
- "Employers in X" / "X companies" -> sector_contains
- "Employers hiring for X" / "X employers" (X is a role) -> hires_for_title_contains
- "Top N employers by alignment" / no filter, just sort -> empty filters; default sort by aligned_course_count DESC handles it
- "Employers in regional priority sectors" -> swp_priority_only: true

UNSUPPORTED — set unsupported=true when the question cannot be expressed as a single base traversal with WHERE/ORDER BY/LIMIT. Specifically:
- Skill-based filters ("employers requiring X skills") — the bridge to occupations is now via the institutional TOP-SOC crosswalk, not a skill index. Suggest filtering by sector or hiring role instead.
- "Employers hiring for high-demand occupations" -> unsupported. ("high-demand" is not a literal title substring; it requires first ranking occupations by demand and then filtering.) unsupported_reason: "Identifying high-demand occupations requires a separate ranking step."
- "Employers hiring for fast-growing roles" -> unsupported. Same shape.
- "Employers most likely to partner with us" -> unsupported. Subjective ranking.
- Any question that requires a sub-query, cross-employer comparison, or properties not in the schema -> unsupported.

When unsupported, do NOT extract filter values. Set unsupported=true and provide a short unsupported_reason explaining the limitation.

Respond with a JSON object matching the schema exactly. No prose."""


SPEC_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "sector_contains": {"type": "ARRAY", "nullable": True, "items": {"type": "STRING"}},
        "name_contains": {"type": "STRING", "nullable": True},
        "hires_for_title_contains": {"type": "ARRAY", "nullable": True, "items": {"type": "STRING"}},
        "swp_priority_only": {"type": "BOOLEAN"},
        "limit": {"type": "INTEGER", "nullable": True},
        "unsupported": {"type": "BOOLEAN", "nullable": True},
        "unsupported_reason": {"type": "STRING", "nullable": True},
    },
}
