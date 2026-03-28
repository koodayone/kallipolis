"""Shared NL-to-Cypher query engine used by all leaf view translation layers."""

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


def generate_query(question: str, college: str, system_prompt: str) -> tuple[str, str]:
    """Call Claude to translate a natural language question into Cypher with interpretation."""
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        system=system_prompt,
        messages=[{"role": "user", "content": f"[College: {college}]\n\n{question}"}],
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
