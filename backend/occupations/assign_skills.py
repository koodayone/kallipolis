"""
Assign skills to occupations from the unified taxonomy via Gemini Flash.

Reads occupations.json, batches occupations, sends to Gemini Flash with
the closed vocabulary, writes updated skills back.

Usage:
    python -m pipeline.industry.assign_occupation_skills
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

SYSTEM_INSTRUCTION = """You are a workforce analyst assigning standardized skills to occupations.

For each occupation, select at least 6 skills from the vocabulary below that the occupation requires or regularly uses. Include every additional skill that applies. Be thorough — include both primary technical skills and secondary professional skills.
Use EXACT names from the vocabulary. Do NOT invent new skill names.

Return a JSON object mapping each SOC code to its skill array.
Example: {{"11-2011": ["Administration & Management", "Strategic Planning", "Budgeting"]}}

VOCABULARY:
{taxonomy}"""


async def _assign_batch(
    client: genai.Client,
    batch: list[dict],
    sem: asyncio.Semaphore,
    system: str,
) -> dict[str, list[str]]:
    """Assign skills to a batch of occupations."""
    lines = []
    for occ in batch:
        lines.append(f"SOC {occ['soc_code']}: {occ['title']}")
        if occ.get("description"):
            lines.append(f"  {occ['description'][:200]}")
    user_msg = "\n".join(lines)

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
                else:
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


async def assign_all() -> None:
    """Assign skills to all occupations."""
    from ontology.skills import UNIFIED_TAXONOMY

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY required")

    # Load occupations
    with open(OCCUPATIONS_PATH) as f:
        occupations = json.load(f)
    logger.info(f"Loaded {len(occupations)} occupations")

    # Build system prompt with taxonomy
    taxonomy_str = "\n".join(f"- {s}" for s in sorted(UNIFIED_TAXONOMY))
    system = SYSTEM_INSTRUCTION.format(taxonomy=taxonomy_str)

    # Batch and assign
    client = genai.Client(api_key=api_key)
    sem = asyncio.Semaphore(CONCURRENCY)

    batches = [occupations[i:i + BATCH_SIZE] for i in range(0, len(occupations), BATCH_SIZE)]
    logger.info(f"Processing {len(batches)} batches of {BATCH_SIZE}")

    tasks = [_assign_batch(client, batch, sem, system) for batch in batches]
    results = await asyncio.gather(*tasks)

    # Merge results
    all_mappings: dict[str, list[str]] = {}
    for result in results:
        if isinstance(result, dict):
            all_mappings.update(result)

    # Update occupations with new skills
    updated = 0
    unmapped = 0
    off_taxonomy = set()
    for occ in occupations:
        soc = occ["soc_code"]
        if soc in all_mappings:
            # Validate against taxonomy
            valid = [s for s in all_mappings[soc] if s in UNIFIED_TAXONOMY]
            invalid = [s for s in all_mappings[soc] if s not in UNIFIED_TAXONOMY]
            for s in invalid:
                off_taxonomy.add(s)
            occ["skills"] = valid
            updated += 1
        else:
            unmapped += 1

    logger.info(f"Updated: {updated}, Unmapped: {unmapped}")
    if off_taxonomy:
        logger.warning(f"Off-taxonomy terms dropped: {sorted(off_taxonomy)[:10]}")

    # Write back
    with open(OCCUPATIONS_PATH, "w") as f:
        json.dump(occupations, f, indent=2)
    logger.info(f"Wrote {len(occupations)} occupations to {OCCUPATIONS_PATH}")

    # Stats
    all_skills = set()
    for occ in occupations:
        all_skills.update(occ.get("skills", []))
    logger.info(f"Unique skills across occupations: {len(all_skills)}")


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)-7s %(message)s", datefmt="%H:%M:%S")
    asyncio.run(assign_all())


if __name__ == "__main__":
    main()
