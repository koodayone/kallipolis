"""
Assign skills to occupations from the unified taxonomy via Gemini Flash.

Reads occupations.json, batches occupations, sends the batches to Gemini Flash
with the closed vocabulary, validates responses against the taxonomy, and
retries any occupation whose validated skill count falls below the floor.

The pipeline has two passes:
  1. Initial pass: every occupation goes through in a standard batch.
  2. Retry pass: any occupation whose post-validation skill count is below
     the MIN_SKILLS floor is resubmitted with a prompt that names the
     dropped off-taxonomy terms and asks for in-vocabulary replacements.

Usage:
    python -m occupations.assign_skills
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
from pathlib import Path

from google import genai
from google.genai import types

logger = logging.getLogger(__name__)

OCCUPATIONS_PATH = Path(__file__).parent / "occupations.json"
BATCH_SIZE = 20
CONCURRENCY = 10
MAX_RETRIES = 5
MIN_SKILLS = 6
MAX_RETRY_PASSES = 2

SYSTEM_INSTRUCTION = """You are a workforce analyst assigning standardized skills to occupations.

For each occupation, select at least 6 skills from the vocabulary below that the occupation requires or regularly uses. Include every additional skill that applies. Be thorough — include both primary technical skills and secondary professional skills.
Use EXACT names from the vocabulary. Do NOT invent new skill names.

Return a JSON object mapping each SOC code to its skill array.
Example: {{"11-2011": ["Administration & Management", "Strategic Planning", "Budgeting"]}}

VOCABULARY:
{taxonomy}"""

RETRY_SYSTEM_INSTRUCTION = """You are a workforce analyst assigning standardized skills to occupations.

You previously assigned skills to these occupations but some of your selections were not in the controlled vocabulary and were dropped, leaving the occupation with fewer than the required minimum of 6 skills.

For each occupation below, the user message lists:
  - the occupation title and description
  - the currently accepted skills (already in the vocabulary)
  - the terms you proposed that were rejected because they are not in the vocabulary

Select replacement skills from the vocabulary so that the total accepted skill count for each occupation is AT LEAST 6. Include the currently accepted skills in your response — return the full final list, not just the additions.

Use EXACT names from the vocabulary. Do NOT invent new skill names.

Return a JSON object mapping each SOC code to its skill array.

VOCABULARY:
{taxonomy}"""


def _filter_to_taxonomy(
    skills: list[str], taxonomy: set[str]
) -> tuple[list[str], list[str]]:
    """Partition a proposed skill list into (valid, invalid) against the taxonomy.

    Deduplicates valid skills while preserving the order they were proposed in,
    so that the caller's downstream logic does not depend on hash ordering.
    """
    valid: list[str] = []
    invalid: list[str] = []
    seen: set[str] = set()
    for skill in skills:
        if skill in taxonomy:
            if skill not in seen:
                valid.append(skill)
                seen.add(skill)
        else:
            invalid.append(skill)
    return valid, invalid


def _below_floor(occupations: list[dict], floor: int = MIN_SKILLS) -> list[str]:
    """Return SOC codes whose current skill count is strictly below the floor."""
    return [o["soc_code"] for o in occupations if len(o.get("skills", [])) < floor]


def _format_initial_line(occ: dict) -> list[str]:
    """Render an occupation as prompt lines for the initial assignment pass."""
    lines = [f"SOC {occ['soc_code']}: {occ['title']}"]
    if occ.get("education_level"):
        lines.append(f"  entry education: {occ['education_level']}")
    if occ.get("description"):
        lines.append(f"  {occ['description']}")
    return lines


def _format_retry_line(occ: dict, rejected: list[str]) -> list[str]:
    """Render an occupation as prompt lines for the retry pass."""
    lines = [f"SOC {occ['soc_code']}: {occ['title']}"]
    if occ.get("education_level"):
        lines.append(f"  entry education: {occ['education_level']}")
    if occ.get("description"):
        lines.append(f"  {occ['description']}")
    current = occ.get("skills", [])
    lines.append(f"  currently accepted: {current if current else '(none)'}")
    if rejected:
        lines.append(f"  rejected (not in vocabulary): {rejected}")
    return lines


async def _assign_batch(
    client: genai.Client,
    user_msg: str,
    sem: asyncio.Semaphore,
    system: str,
) -> dict[str, list[str]]:
    """Run one Gemini batch call and return the raw SOC → skill list mapping."""
    for attempt in range(MAX_RETRIES):
        async with sem:
            try:
                response = await client.aio.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=user_msg,
                    config=types.GenerateContentConfig(
                        system_instruction=system,
                        max_output_tokens=8192,
                        temperature=0.2,
                        response_mime_type="application/json",
                        thinking_config=types.ThinkingConfig(thinking_budget=0),
                    ),
                )
                text = response.text.strip()
                result = json.loads(text)
                if isinstance(result, dict):
                    return result
                logger.warning(f"Unexpected format: {text[:200]}")
                return {}
            except json.JSONDecodeError as e:
                logger.warning(f"JSON parse error: {e}")
                return {}
            except Exception as e:
                error_str = str(e).lower()
                if "resource_exhausted" in error_str or "429" in error_str:
                    wait = 2 ** attempt * 5
                    logger.info(f"Rate limited, waiting {wait}s (attempt {attempt + 1})")
                    await asyncio.sleep(wait)
                else:
                    logger.error(f"Gemini error: {e}")
                    return {}

    return {}


async def _run_initial_pass(
    client: genai.Client,
    occupations: list[dict],
    sem: asyncio.Semaphore,
    system: str,
) -> dict[str, list[str]]:
    """First pass: assign skills to every occupation."""
    batches = [occupations[i:i + BATCH_SIZE] for i in range(0, len(occupations), BATCH_SIZE)]
    logger.info(f"Initial pass: {len(batches)} batches of {BATCH_SIZE}")

    async def one(batch):
        lines: list[str] = []
        for occ in batch:
            lines.extend(_format_initial_line(occ))
        return await _assign_batch(client, "\n".join(lines), sem, system)

    results = await asyncio.gather(*[one(b) for b in batches])
    merged: dict[str, list[str]] = {}
    for result in results:
        if isinstance(result, dict):
            merged.update(result)
    return merged


async def _run_retry_pass(
    client: genai.Client,
    occupations: list[dict],
    rejected_by_soc: dict[str, list[str]],
    sem: asyncio.Semaphore,
    system: str,
) -> dict[str, list[str]]:
    """Retry pass: resubmit only the occupations below the floor."""
    if not occupations:
        return {}

    batches = [occupations[i:i + BATCH_SIZE] for i in range(0, len(occupations), BATCH_SIZE)]
    logger.info(f"Retry pass: {len(batches)} batches of {BATCH_SIZE} ({len(occupations)} occupations)")

    async def one(batch):
        lines: list[str] = []
        for occ in batch:
            lines.extend(_format_retry_line(occ, rejected_by_soc.get(occ["soc_code"], [])))
        return await _assign_batch(client, "\n".join(lines), sem, system)

    results = await asyncio.gather(*[one(b) for b in batches])
    merged: dict[str, list[str]] = {}
    for result in results:
        if isinstance(result, dict):
            merged.update(result)
    return merged


def _apply_mapping(
    occupations: list[dict],
    mapping: dict[str, list[str]],
    taxonomy: set[str],
) -> tuple[int, dict[str, list[str]], set[str]]:
    """Apply a SOC→skills mapping to occupations with taxonomy validation.

    Returns (updated_count, rejected_by_soc, off_taxonomy_terms). The rejected
    dict records the terms Gemini proposed that did not validate, keyed by
    SOC code, so the retry pass can include them in its prompt.
    """
    updated = 0
    rejected_by_soc: dict[str, list[str]] = {}
    off_taxonomy: set[str] = set()

    for occ in occupations:
        soc = occ["soc_code"]
        if soc not in mapping:
            continue
        valid, invalid = _filter_to_taxonomy(mapping[soc], taxonomy)
        occ["skills"] = valid
        updated += 1
        if invalid:
            rejected_by_soc[soc] = invalid
            off_taxonomy.update(invalid)

    return updated, rejected_by_soc, off_taxonomy


def _report(occupations: list[dict]) -> None:
    """Log a post-run summary of skill-count health and vocabulary coverage."""
    total = len(occupations)
    zero = sum(1 for o in occupations if not o.get("skills"))
    below = sum(1 for o in occupations if len(o.get("skills", [])) < MIN_SKILLS)
    all_skills: set[str] = set()
    for o in occupations:
        all_skills.update(o.get("skills", []))

    logger.info(
        f"Post-run: total={total} below_floor={below} zero_skills={zero} "
        f"unique_skills={len(all_skills)}"
    )


async def assign_all() -> None:
    """Assign skills to all occupations with validation and a bounded retry loop."""
    from ontology.skills import UNIFIED_TAXONOMY

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY required")

    with open(OCCUPATIONS_PATH) as f:
        occupations = json.load(f)
    logger.info(f"Loaded {len(occupations)} occupations")

    taxonomy_str = "\n".join(f"- {s}" for s in sorted(UNIFIED_TAXONOMY))
    initial_system = SYSTEM_INSTRUCTION.format(taxonomy=taxonomy_str)
    retry_system = RETRY_SYSTEM_INSTRUCTION.format(taxonomy=taxonomy_str)

    client = genai.Client(api_key=api_key)
    sem = asyncio.Semaphore(CONCURRENCY)

    # Initial pass
    mapping = await _run_initial_pass(client, occupations, sem, initial_system)
    updated, rejected_by_soc, off_taxonomy = _apply_mapping(
        occupations, mapping, UNIFIED_TAXONOMY
    )
    logger.info(f"Initial pass applied: updated={updated}")
    if off_taxonomy:
        logger.warning(f"Off-taxonomy terms dropped: {sorted(off_taxonomy)[:10]}")

    # Bounded retry passes for occupations still below the floor
    for pass_num in range(1, MAX_RETRY_PASSES + 1):
        below = _below_floor(occupations, MIN_SKILLS)
        if not below:
            break
        logger.info(f"Retry pass {pass_num}: {len(below)} occupations below floor")
        retry_occs = [o for o in occupations if o["soc_code"] in set(below)]
        retry_mapping = await _run_retry_pass(
            client, retry_occs, rejected_by_soc, sem, retry_system
        )
        _, retry_rejected, retry_off = _apply_mapping(
            retry_occs, retry_mapping, UNIFIED_TAXONOMY
        )
        rejected_by_soc.update(retry_rejected)
        if retry_off:
            logger.warning(f"Retry off-taxonomy terms dropped: {sorted(retry_off)[:10]}")

    # Write back
    with open(OCCUPATIONS_PATH, "w") as f:
        json.dump(occupations, f, indent=2)
    logger.info(f"Wrote {len(occupations)} occupations to {OCCUPATIONS_PATH}")

    _report(occupations)


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)-7s %(message)s",
        datefmt="%H:%M:%S",
    )
    asyncio.run(assign_all())


if __name__ == "__main__":
    main()
