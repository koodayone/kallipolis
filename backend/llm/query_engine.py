"""Shared NL-to-Cypher query engine used by all leaf view translation layers."""

from __future__ import annotations

import os
import re
import json
import logging
import anthropic
from ontology.schema import get_driver

logger = logging.getLogger(__name__)

DISALLOWED_KEYWORDS = {
    "CREATE", "DELETE", "SET", "MERGE", "REMOVE", "DROP",
    "DETACH", "CALL", "FOREACH", "LOAD",
}


# ── Vocabulary resolution ──────────────────────────────────────────────
#
# Before Sonnet generates Cypher, Gemini Flash extracts search intent from
# the user's question and Neo4j resolves those terms against actual data.
# This closes the gap between user phrasing ("healthcare") and graph
# values ("Patient Care", "Clinical Assessment").

RESOLUTION_PROMPT = """\
You extract search terms from a user's question about a college workforce database.

The database has these views, each with TEXT properties that support substring matching:

employer: sector, employer_name, skill
occupation: title, skill
course: department, skill
student: primary_focus, skill, course_code, course_name
partnership: sector, employer_name, skill

Given the view and question, identify which TEXT properties (if any) the user is filtering on. For each, produce 1-4 SHORT ROOT SUBSTRINGS (3-8 chars) that maximize case-insensitive CONTAINS matches. Use roots, not full words: "health" not "healthcare", "manufactur" not "manufacturing", "nurs" not "nursing".

Apply semantic bridging: "draw blood" -> "phlebotom", "clinical", "patient". "fix cars" -> "automot", "mechanic", "vehicle".

If the question has NO text filters (e.g. "show me all employers", "highest paying occupations"), return empty filters.

Return JSON: {"filters": [{"property": "<name>", "terms": ["<root1>", "<root2>"]}]}"""

RESOLUTION_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "filters": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "property": {"type": "STRING"},
                    "terms": {"type": "ARRAY", "items": {"type": "STRING"}},
                },
                "required": ["property", "terms"],
            },
        },
    },
    "required": ["filters"],
}

_RESOLUTION_QUERIES = {
    "skill":         "MATCH (n:Skill) WHERE {where} RETURN DISTINCT n.name AS val LIMIT 30",
    "sector":        "MATCH (n:Employer) WHERE {where} RETURN DISTINCT n.sector AS val LIMIT 30",
    "employer_name": "MATCH (n:Employer) WHERE {where} RETURN DISTINCT n.name AS val LIMIT 30",
    "title":         "MATCH (n:Occupation) WHERE {where} RETURN DISTINCT n.title AS val LIMIT 30",
    "department":    "MATCH (n:Course {{college: $college}}) WHERE {where} RETURN DISTINCT n.department AS val LIMIT 30",
    "primary_focus": "MATCH (n:Student)-[:ENROLLED_IN]->(:Course {{college: $college}}) WHERE {where} RETURN DISTINCT n.primary_focus AS val LIMIT 30",
    "course_code":   "MATCH (n:Course {{college: $college}}) WHERE {where} RETURN DISTINCT n.code AS val LIMIT 30",
    "course_name":   "MATCH (n:Course {{college: $college}}) WHERE {where} RETURN DISTINCT n.name AS val LIMIT 30",
}

_PROPERTY_ACCESS = {
    "skill": "n.name", "sector": "n.sector", "employer_name": "n.name",
    "title": "n.title", "department": "n.department",
    "primary_focus": "n.primary_focus", "course_code": "n.code",
    "course_name": "n.name",
}


def _flash_classify(question: str, view: str) -> list[dict]:
    """Call Gemini Flash to extract search term filters from the question."""
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
    config = types.GenerateContentConfig(
        response_mime_type="application/json",
        response_schema=RESOLUTION_SCHEMA,
        temperature=0.0,
    )
    response = client.models.generate_content(
        model=os.environ.get("GEMINI_MODEL", "gemini-2.5-flash"),
        contents=f"{RESOLUTION_PROMPT}\n\nView: {view}\nQuestion: {question}",
        config=config,
    )
    result = json.loads(response.text)
    return [f for f in result.get("filters", [])
            if f.get("property") and f.get("terms")]


def _neo4j_resolve(filters: list[dict], college: str) -> dict[str, list[str]]:
    """Resolve Flash search terms against Neo4j. Returns {property: [matched_values]}."""
    driver = get_driver()
    resolved: dict[str, list[str]] = {}

    with driver.session() as session:
        for f in filters:
            prop = f["property"]
            terms = f["terms"]
            if prop not in _RESOLUTION_QUERIES:
                logger.warning(f"Unknown resolution property: {prop}")
                continue

            prop_access = _PROPERTY_ACCESS[prop]
            sanitized = [t.lower().replace("'", "") for t in terms if t.strip()]
            if not sanitized:
                continue
            conditions = [f"toLower({prop_access}) CONTAINS '{t}'" for t in sanitized]
            where_clause = " OR ".join(conditions)

            cypher = _RESOLUTION_QUERIES[prop].format(where=where_clause)
            try:
                records = session.execute_read(
                    lambda tx, q=cypher: tx.run(q, college=college).data()
                )
                values = [r["val"] for r in records if r.get("val")]
                if values:
                    resolved[prop] = values
            except Exception:
                logger.warning(f"Resolution query failed for {prop}", exc_info=True)

    return resolved


def _format_hint(resolved: dict[str, list[str]]) -> str:
    """Format resolved vocabulary as a hint for Sonnet."""
    lines = ["[Matching values in the database — use in WHERE clauses:]"]
    for prop, values in resolved.items():
        quoted = ", ".join(f'"{v}"' for v in values)
        lines.append(f"  {prop}: {quoted}")
    return "\n".join(lines)


def resolve_vocabulary(question: str, college: str, view: str) -> str:
    """Best-effort vocabulary resolution. Returns a hint string for Sonnet, or empty string."""
    try:
        filters = _flash_classify(question, view)
        if not filters:
            return ""
        resolved = _neo4j_resolve(filters, college)
        if not resolved:
            return ""
        return _format_hint(resolved)
    except Exception:
        logger.warning("Vocabulary resolution failed, proceeding without", exc_info=True)
        return ""


# ── Core pipeline ──────────────────────────────────────────────────────

def validate_cypher(cypher: str) -> str:
    """Validate generated Cypher is read-only and college-scoped. Returns cleaned Cypher or raises ValueError."""
    stripped = cypher.strip()

    if "CANNOT_TRANSLATE" in stripped:
        raise ValueError("I couldn't translate that question into a query. Try rephrasing your question.")

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


def parse_llm_response(raw: str) -> tuple[str, str]:
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

    # Fallback: treat entire response as raw Cypher
    logger.warning(f"Could not parse JSON from LLM response, treating as raw Cypher: {raw[:200]!r}")
    return raw, ""


def generate_query(question: str, college: str, system_prompt: str, view: str = "") -> tuple[str, str]:
    """Call Claude to translate a natural language question into Cypher with interpretation.

    The per-form system prompt is identical across every query for that form;
    only the user message varies. We mark it with `cache_control: ephemeral`
    so Anthropic caches the tokenized prefix — warm calls skip prefix
    tokenization entirely (~1.5–2s saved per call) and pay 10% of the
    input-token cost.

    Sonnet 4-6's caching minimum is empirically ~2000 tokens (higher than the
    1024 documented for older Sonnet versions). All four prompts (Course,
    Student, Employer, Occupation) are sized above that threshold; verified
    by direct cache_creation/cache_read measurement against the model. The
    5-minute default TTL fits an interactive atlas where a coordinator clicks
    through multiple queries on the same form.
    """
    user_message = f"[College: {college}]\n\n{question}"
    if view:
        hint = resolve_vocabulary(question, college, view)
        if hint:
            user_message += f"\n\n{hint}"

    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        system=[
            {
                "type": "text",
                "text": system_prompt,
                "cache_control": {"type": "ephemeral"},
            }
        ],
        messages=[{"role": "user", "content": user_message}],
    )
    raw = message.content[0].text.strip()
    logger.info(f"LLM response (first 300 chars): {raw[:300]!r}")
    return parse_llm_response(raw)


def execute_query(cypher: str, college: str) -> list[dict]:
    """Execute validated Cypher via read transaction and return raw records."""
    driver = get_driver()
    with driver.session() as session:
        result = session.execute_read(
            lambda tx: tx.run(cypher, college=college).data()
        )
    return result
