"""Populate the ``operations_summary`` field for every employer from their
existing ``description``.

The ``operations_summary`` is a verb phrase that follows the employer's
name in the executive summary's opening sentence:

    f"{employer.name} {employer.operations_summary}."
    → "Bellarmine College Preparatory serves approximately 1,600 students
       at its all-boys Jesuit private high school in San Jose."

The phrase is computed once per employer and stored on the Employer node;
proposal generation at runtime uses it directly with no LLM call. This
is the single LLM-driven characterization needed to make the rest of the
partnership-proposal narrative deterministic.

Design constraints (so the resulting prose composes well downstream):
  * No geographic territory larger than a city — regional scope is added
    by other parts of the proposal (Occupational Demand cites the COE
    region with its labor-market figures). Including the COE region in
    this sentence would either duplicate or contradict that.
  * No mention of the partnership, students-as-pipeline, the college, or
    workforce development — those are the *next* sentences' job.
  * No superlatives or subjective adjectives ("largest", "leading",
    "innovative") — the institutional voice persuades through specificity,
    not boosterism.
  * Verb phrase only: starts with a third-person-singular verb, does not
    repeat the employer's name (the template prepends it).

Mirrors ``populate_description.py``'s observability pattern: progress
log, state file, incremental writes, fail-fast on deterministic errors,
one retry on transient ones.

Usage:
    python3 -m employers.characterize --dry-run
    python3 -m employers.characterize --limit 20            # test on 20
    python3 -m employers.characterize                       # incremental: only fills empties
    python3 -m employers.characterize --regenerate          # rewrite all
    python3 -m employers.characterize --concurrency 10      # dial up
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import re
import time
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)

_THIS_DIR = Path(__file__).parent
EMPLOYERS_PATH = _THIS_DIR / "employers.json"
PROGRESS_LOG = _THIS_DIR / ".characterize_progress.log"
STATE_FILE = _THIS_DIR / ".characterize_state.json"

# 10 employers per call: calibrated at ~4s/batch, 576 input tokens, 425 output.
# Larger batches risk the model losing the per-input rule discipline; smaller
# batches waste shared-prompt overhead. 10 is the empirically validated point.
_BATCH_SIZE = 10

# 5 concurrent batches in flight = 50 employers being characterized at once.
# Conservative starting point; bump to 10 if API headroom permits.
_DEFAULT_CONCURRENCY = 5

# Incremental write cadence: every 5 batches = 50 employers, so a crash loses
# at most ~50 characterizations.
_INCREMENTAL_WRITE_EVERY = 5

# Single retry with 30 s back-off on 5xx/429.
_TRANSIENT_RETRY_SLEEP = 30.0


PROMPT_HEADER = """You characterize employers for an institutional workforce-development artifact. For each employer, write ONE verb phrase (10-22 words) that follows their name in a sentence. The output must obey these rules without exception.

REQUIRED:
- Start with a third-person-singular verb (operates, provides, manufactures, serves, produces, runs, etc.)
- Name what the employer does and any concrete scale figures from the description (employee count, store/hospital/location count, member count, bed count, etc.)
- Mention a specific city ONLY if the employer is meaningfully tied to one (single-campus school, headquartered manufacturer); otherwise omit geography entirely
- End without a period (the template adds the final period)

DO NOT include any of the following — strip them even if the description contains them:

GEOGRAPHIC TERRITORIES LARGER THAN A CITY (any of these are forbidden):
- counties or "[county name] County"
- regions like "Central Valley", "Bay Area", "Inland Empire", "Southern California", "Northern California"
- US state names ("California", "Massachusetts", etc.) and abbreviations ("CA", "MA")
- "U.S.", "United States", "America", "American", "North America", "nationwide", "across the country"

SUBJECTIVE OR EVALUATIVE ADJECTIVES (any of these are forbidden, plus their synonyms):
- premium, high-quality, top-quality, world-class, world-renowned, leading, premier
- innovative, cutting-edge, state-of-the-art, advanced (when used as an adjective for the employer's offering)
- comprehensive, full-service, full-suite, end-to-end (when used to inflate the offering)
- diverse, wide-range, wide variety, broad portfolio, extensive (when used as filler before a noun)
- responsibly, sustainably, ethically (when used as adverbs to modify produce/raise/grow)
- trusted, beloved, renowned, prestigious, esteemed, certified-B-Corp positioning, faith-based positioning
- "[N]+" used to inflate ("over 200+ locations" → say "more than 200 locations" or just "200 locations")
- "only" / "sole" / "exclusive" superlative framings ("California's only state-operated facility" → "a state-operated facility")

OTHER FORBIDDEN CONTENT:
- The employer's name (the template prepends it; do not repeat)
- The partnership concept, students-as-talent-pipeline, colleges, workforce development, or "the partnership"
- Founding year ("founded in 1972") unless it conveys substantive operational character

EXAMPLES of correctly characterized employers (these are the target style):

INPUT name: Bellarmine College Preparatory
INPUT description: Bellarmine College Preparatory is an all-boys Jesuit private high school in San Jose, California, serving approximately 1,600 students from across the Bay Area.
GOOD operations_summary: operates an all-boys Jesuit college-preparatory high school in San Jose, serving approximately 1,600 students
(Notes: city kept; "California" stripped; "across the Bay Area" stripped.)

INPUT name: Saputo Cheese USA
INPUT description: Saputo Cheese USA transforms milk into high-quality, safe, and nutritious cheese and dairy products serving consumers across the U.S.
GOOD operations_summary: produces cheese and dairy products from milk for retail and food-service consumers
(Notes: "high-quality, safe, and nutritious" stripped as subjective; "across the U.S." stripped.)

INPUT name: Adventist Health Tulare
INPUT description: Adventist Health Tulare is a faith-based health system providing primary, urgent, and specialty care across the West Coast and Hawaii.
GOOD operations_summary: operates a hospital in Tulare providing primary, urgent, and specialty care
(Notes: "faith-based" stripped as positioning; "across the West Coast and Hawaii" stripped — region/state forbidden; the city Tulare is in the entity name and stays.)

INPUT name: Porterville Developmental Center
INPUT description: Porterville Developmental Center is California's only state-operated facility serving individuals with intellectual disabilities who have legal system contact.
GOOD operations_summary: operates a state-run residential facility in Porterville serving individuals with intellectual disabilities and legal-system involvement
(Notes: "California's only" stripped — state name AND superlative framing; city Porterville kept from the entity name.)

INPUT name: Woolf Farming Company of California
INPUT description: Woolf Farming Company of California grows, processes, and delivers natural products to the food chain as a certified B Corp in California.
GOOD operations_summary: grows, processes, and delivers agricultural products to the food chain
(Notes: "California" stripped from BOTH the trailing "in California" AND any tail-references; "certified B Corp" stripped as positioning. The state name in the company's own name is fine because the template doesn't repeat the company name in the verb phrase.)

INPUT name: Sun Pacific
INPUT description: Sun Pacific grows, packs, and ships fresh produce including mandarins, kiwi, oranges, grapes, and lemons.
GOOD operations_summary: grows, packs, and ships fresh produce including mandarins, oranges, grapes, and lemons

INPUT name: WNA
INPUT description: WNA Inc. is a manufacturer of disposable plastic tableware and food service products based in Chicopee, Massachusetts.
GOOD operations_summary: manufactures disposable plastic tableware and food-service products in Chicopee
(Notes: city kept; "Massachusetts" stripped.)

INPUT name: Roseburg Forest Products
INPUT description: Roseburg Forest Products manufactures diverse wood products like lumber, plywood, and engineered wood for North American construction and furniture markets.
GOOD operations_summary: manufactures wood products including lumber, plywood, and engineered wood for construction and furniture markets
(Notes: "diverse" stripped as subjective filler; "North American" stripped — continent forbidden.)

Return ONLY a JSON array of objects, one per input, in the same order: [{"name": "...", "operations_summary": "..."}]

EMPLOYERS:"""


def _get_gemini_client():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY not set")
    from google import genai
    return genai.Client(api_key=api_key)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _progress(msg: str) -> None:
    """Append a line to the progress log AND echo to stdout."""
    line = f"[{_now_iso()}] {msg}"
    print(line, flush=True)
    with open(PROGRESS_LOG, "a") as f:
        f.write(line + "\n")


def _write_state(state: dict) -> None:
    STATE_FILE.write_text(json.dumps(state, indent=2))


def _build_prompt(batch: list[dict]) -> str:
    lines = "\n".join(f"- {e['name']} | {e['description']}" for e in batch)
    return PROMPT_HEADER + "\n" + lines


def _normalize(summary: str) -> str:
    """Trim and strip a trailing period — the template adds the final period
    when assembling ``f"{name} {summary}."``. The LLM occasionally emits
    one anyway despite the prompt rule; rather than re-prompt, we just
    drop it."""
    s = (summary or "").strip()
    while s.endswith("."):
        s = s[:-1].rstrip()
    return s


async def _generate_batch_async(
    client, batch: list[dict], label: str
) -> dict[str, str] | None:
    """Async Gemini call. Returns {name: operations_summary} or None on failure.

    Same fail-fast shape as populate_description._generate_batch_async:
      * Transient (5xx/429/rate) → one retry after _TRANSIENT_RETRY_SLEEP
      * Anything else → immediate None; caller flags the batch's employers
    """
    prompt = _build_prompt(batch)

    response = None
    for attempt in (1, 2):
        try:
            response = await client.aio.models.generate_content(
                model="gemini-2.5-flash-lite",
                contents=prompt,
            )
            break
        except Exception as e:
            err = str(e).lower()
            is_transient = any(tok in err for tok in ("503", "429", "rate", "unavailable"))
            if is_transient and attempt == 1:
                _progress(f"    {label}: transient, retry in {int(_TRANSIENT_RETRY_SLEEP)}s — {e}")
                await asyncio.sleep(_TRANSIENT_RETRY_SLEEP)
                continue
            _progress(f"    {label}: FAIL — {type(e).__name__}: {e}")
            return None
    if response is None:
        return None

    if not response.text:
        _progress(f"    {label}: FAIL — empty response")
        return None

    match = re.search(r"\[[\s\S]*\]", response.text)
    if not match:
        _progress(f"    {label}: FAIL — no JSON array in response")
        return None

    try:
        parsed = json.loads(match.group(0))
    except json.JSONDecodeError as e:
        _progress(f"    {label}: FAIL — JSON parse: {e}")
        return None

    if not isinstance(parsed, list) or len(parsed) != len(batch):
        _progress(
            f"    {label}: FAIL — shape mismatch (expected list of "
            f"{len(batch)}, got {type(parsed).__name__} of "
            f"{len(parsed) if isinstance(parsed, list) else '?'})"
        )
        return None

    out: dict[str, str] = {}
    for i in range(len(batch)):
        summary = _normalize(str(parsed[i].get("operations_summary", "") or ""))
        out[batch[i]["name"]] = summary
    return out


async def _run_all_batches(
    client,
    batches: list[list[dict]],
    employers: list[dict],
    concurrency: int,
    dry_run: bool,
    state: dict,
) -> tuple[int, int]:
    """Run all batches with bounded concurrency. Returns (populated, flagged)."""
    sem = asyncio.Semaphore(concurrency)
    write_lock = asyncio.Lock()
    n_batches = len(batches)

    totals = {"done": 0, "populated": 0, "flagged": 0}

    async def process(batch_idx: int, batch: list[dict]) -> None:
        async with sem:
            label = f"batch {batch_idx + 1}/{n_batches}"
            t0 = time.monotonic()
            result = await _generate_batch_async(client, batch, label)
            elapsed = time.monotonic() - t0

            async with write_lock:
                if result:
                    got = 0
                    for emp in batch:
                        summary = result.get(emp["name"], "")
                        if summary:
                            emp["operations_summary"] = summary
                            totals["populated"] += 1
                            got += 1
                        else:
                            emp["operations_summary"] = None
                            totals["flagged"] += 1
                    _progress(
                        f"  {label}: {got}/{len(batch)} populated, "
                        f"{elapsed:.1f}s ({totals['done'] + 1}/{n_batches} done)"
                    )
                else:
                    for emp in batch:
                        emp["operations_summary"] = None
                        totals["flagged"] += 1
                    _progress(
                        f"  {label}: 0/{len(batch)} (failed), "
                        f"{elapsed:.1f}s ({totals['done'] + 1}/{n_batches} done)"
                    )

                totals["done"] += 1
                state.update({
                    "batches_done": totals["done"],
                    "summaries_populated": totals["populated"],
                    "summaries_flagged_null": totals["flagged"],
                    "last_batch_label": label,
                    "last_batch_elapsed_s": round(elapsed, 1),
                    "updated_at": _now_iso(),
                })
                _write_state(state)

                if not dry_run and totals["done"] % _INCREMENTAL_WRITE_EVERY == 0:
                    with open(EMPLOYERS_PATH, "w") as f:
                        json.dump(employers, f, indent=2)
                    _progress(f"  checkpoint: wrote employers.json after {totals['done']} batches")

    tasks = [process(i, batches[i]) for i in range(n_batches)]
    await asyncio.gather(*tasks)
    return totals["populated"], totals["flagged"]


def characterize(
    dry_run: bool = False,
    limit: int | None = None,
    regenerate: bool = False,
    concurrency: int = _DEFAULT_CONCURRENCY,
) -> dict:
    """Populate ``operations_summary`` on every employer with a description.

    Append-only by default (only fills employers without one). Pass
    ``regenerate=True`` to overwrite existing summaries.
    """
    with open(EMPLOYERS_PATH) as f:
        employers = json.load(f)

    has_description = [e for e in employers if e.get("description")]
    if regenerate:
        targets = has_description
    else:
        targets = [e for e in has_description if not e.get("operations_summary")]
    if limit:
        targets = targets[:limit]

    batches = [targets[i:i + _BATCH_SIZE] for i in range(0, len(targets), _BATCH_SIZE)]
    n_batches = len(batches)

    PROGRESS_LOG.write_text("")  # truncate
    state = {
        "started_at": _now_iso(),
        "targets": len(targets),
        "batches_total": n_batches,
        "batches_done": 0,
        "summaries_populated": 0,
        "summaries_flagged_null": 0,
        "concurrency": concurrency,
        "regenerate": regenerate,
    }
    _write_state(state)
    _progress(
        f"Started characterize: {len(targets)} targets in {n_batches} batches "
        f"of {_BATCH_SIZE}, concurrency={concurrency} "
        f"(regenerate={regenerate}, limit={limit})"
    )

    if not targets:
        _progress("Nothing to do.")
        return state

    client = _get_gemini_client()

    populated, flagged = asyncio.run(
        _run_all_batches(client, batches, employers, concurrency, dry_run, state)
    )

    if not dry_run:
        with open(EMPLOYERS_PATH, "w") as f:
            json.dump(employers, f, indent=2)
        _progress("Final write: employers.json")

    state["finished_at"] = _now_iso()
    state["summaries_populated"] = populated
    state["summaries_flagged_null"] = flagged
    _write_state(state)
    _progress(
        f"Done: {populated} populated, {flagged} flagged null out of {len(targets)} targets"
    )
    return state


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument(
        "--regenerate", action="store_true",
        help="Overwrite existing operations_summary values; default is append-only.",
    )
    parser.add_argument(
        "--concurrency", type=int, default=_DEFAULT_CONCURRENCY,
        help=f"Concurrent batches in flight (default {_DEFAULT_CONCURRENCY})",
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(message)s")
    state = characterize(
        dry_run=args.dry_run,
        limit=args.limit,
        regenerate=args.regenerate,
        concurrency=args.concurrency,
    )

    print("=" * 60)
    print("FINAL STATE")
    print("=" * 60)
    for k, v in state.items():
        print(f"  {k:28s}  {v}")
    if args.dry_run:
        print("(dry run — employers.json not modified)")


if __name__ == "__main__":
    main()
