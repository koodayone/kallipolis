"""Populate the ``operations_summary`` field for every employer from their
existing ``description``.

The ``operations_summary`` is a verb phrase that follows the employer's
name in the executive summary's opening sentence:

    f"{employer.name} {employer.operations_summary}."
    -> "Bellarmine College Preparatory operates an all-boys Jesuit private
       high school in San Jose, serving approximately 1,600 students."

The phrase is computed once per employer and stored on the Employer node;
proposal generation at runtime uses it directly with no LLM call. This
is the single LLM-driven characterization needed to make the rest of the
partnership-proposal narrative deterministic.

Mirrors ``populate_description.py``'s observability pattern: progress
log, state file, incremental writes, fail-fast on deterministic errors,
one retry on transient ones.

Usage:
    python3 -m employers.characterize --dry-run
    python3 -m employers.characterize --limit 20            # test on 20
    python3 -m employers.characterize                       # incremental: only fills empties
    python3 -m employers.characterize --regenerate          # rewrite all
    python3 -m employers.characterize --region FN           # scope to one COE region
    python3 -m employers.characterize --region BA --regenerate
    python3 -m employers.characterize --concurrency 10
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
_BATCH_SIZE = 10

# 5 concurrent batches in flight = 50 employers being characterized at once.
_DEFAULT_CONCURRENCY = 5

# Incremental write cadence: every 5 batches = 50 employers.
_INCREMENTAL_WRITE_EVERY = 5

# Single retry with 30 s back-off on 5xx/429.
_TRANSIENT_RETRY_SLEEP = 30.0


PROMPT_HEADER = """You write a single one-line characterization of each employer for an institutional workforce-development artifact. The output for each employer is a verb phrase that follows the employer's name in a present-tense sentence:

    {employer_name} {operations_summary}.
    -> "Bellarmine College Preparatory operates an all-boys Jesuit private high school in San Jose, serving approximately 1,600 students."

The audience is a community-college coordinator drafting a partnership proposal. They need a clean, factual line about what the employer actually does. They do not need marketing prose, scope inflation, or any content beyond the operational facts.

================================================================================
SHAPE
================================================================================

- 10-22 words.
- Starts with a present-tense, third-person-singular verb (operates, provides, manufactures, serves, produces, distributes, sells, runs, designs, develops, builds, grows, etc.).
- States what the employer does and any concrete scale figure from the description (employee count, store / hospital / location count, member count, bed count, square footage, fleet size, etc.).
- Includes a specific CITY only when the employer is meaningfully tied to one (single-campus school, single-site manufacturer, headquartered firm). Otherwise omit geography entirely.
- Does NOT repeat the employer's name (the template prepends it).
- Does NOT end with a period (the template adds the final period).

================================================================================
FORBIDDEN: GEOGRAPHIC SCOPE LARGER THAN A CITY
================================================================================

Strip all of these even when the description contains them. Regional scope is supplied downstream by Centers-of-Excellence figures; including it here either duplicates or contradicts that.

- Counties: "[county name] County", "across the county", "the county", "to county residents", "the county fleet" — even when the entity is a county-government agency whose name already contains the county. The entity name preserves the jurisdiction; the verb phrase describes what the agency actually does.
- Multi-county regions: "Central Valley", "Bay Area", "Inland Empire", "South Central Coast", "Far North", "the Bay", "the West Coast", "the East Coast", "the South", "the Midwest", "the Pacific Northwest".
- US state names ("California", "Oregon", "Massachusetts", etc.) and postal abbreviations ("CA", "OR", "MA").
- National scope: "U.S.", "United States", "America", "American", "the country", "across the country", "nationwide", "national".
- Multi-state: "across all states", "across multiple states", "across [N] states".
- Continental: "North America", "North American", "across the continent".
- Global: "globally", "global", "worldwide", "international", "internationally", "across the world", "around the world".

The entity's own name may contain a state or country (e.g., "Saputo Cheese USA", "Woolf Farming Company of California"). The verb phrase itself must not — the name is preserved by the template; the verb phrase strips its own geography.

================================================================================
FORBIDDEN: SUBJECTIVE, EVALUATIVE, OR PROMOTIONAL LANGUAGE
================================================================================

Strip these and their close synonyms even when the description uses them. Description text is often marketing copy; the operations_summary is not.

- Quality boasting: premium, high-quality, top-quality, world-class, world-renowned, best, finest, finest-in-class, top-tier, leading, premier, market-leading.
- Novelty boasting: innovative, cutting-edge, state-of-the-art, advanced (as an offering adjective), revolutionary, transformative, next-generation, pioneering, breakthrough, life-changing.
- Scope inflation: comprehensive, full-service, full-suite, end-to-end, one-stop, integrated (as inflation), turnkey, holistic, all-in-one.
- Filler quantifiers: diverse, wide variety, broad portfolio, extensive, vast, robust, exhaustive.
- Values positioning: sustainable, sustainably, responsibly, ethically, authentic, genuine, real, mission-driven, purpose-driven, faith-based, community-focused (when used as identity language).
- Reputation positioning: trusted, beloved, renowned, prestigious, esteemed, recognized, established (as evaluation), respected.
- Branding registers: enterprise-grade, industry-leading, industry-standard, business-grade, professional-grade.
- Mission-statement verbs: inspires, empowers, transforms, revolutionizes, facilitates [abstract noun], champions, fosters, cultivates.
- Inflation marks: "200+", "5,000+" — use plain "more than 200" or just "200".
- Superlative framings: "only", "sole", "exclusive" qualifiers ("California's only state-operated facility" -> "a state-operated facility").
- Forward-looking copy: "investing in X through 2026", "will expand", "plans to", "set to launch" — strip all forward-looking content; the summary describes present operations only.

================================================================================
FORBIDDEN: OFF-TOPIC CONTENT
================================================================================

- The employer's name (the template prepends it; do not repeat).
- Partnerships, partnership concepts, "partner with".
- Students as a talent pipeline, hiring, workforce development.
- Colleges, universities, education-as-pipeline.
- Founding year unless it conveys substantive operational character (a 1972 family farm vs. a 2023 startup is informative; a 1985 software company is not).
- Past-tense verbs unless the entity has demonstrably ceased operations. Default to present tense even when the description uses past tense. ("Suddenlink provided cable television" -> "operates as a cable and internet service provider".)

================================================================================
WORKED EXAMPLES (study these — they are the target style)
================================================================================

INPUT name: Bellarmine College Preparatory
INPUT description: Bellarmine College Preparatory is an all-boys Jesuit private high school in San Jose, California, serving approximately 1,600 students from across the Bay Area.
GOOD operations_summary: operates an all-boys Jesuit private high school in San Jose, serving approximately 1,600 students
NOTES: city kept; "California" stripped; "across the Bay Area" stripped.

INPUT name: Saputo Cheese USA
INPUT description: Saputo Cheese USA transforms milk into high-quality, safe, and nutritious cheese and dairy products serving consumers across the U.S.
GOOD operations_summary: produces cheese and dairy products from milk for retail and food-service consumers
NOTES: "high-quality, safe, and nutritious" stripped (subjective); "across the U.S." stripped.

INPUT name: Adventist Health Tulare
INPUT description: Adventist Health Tulare is a faith-based health system providing comprehensive primary, urgent, and specialty care across the West Coast and Hawaii.
GOOD operations_summary: operates a hospital in Tulare providing primary, urgent, and specialty care
NOTES: "faith-based" stripped (values positioning); "comprehensive" stripped (scope inflation); "across the West Coast and Hawaii" stripped (region/state forbidden).

INPUT name: Porterville Developmental Center
INPUT description: Porterville Developmental Center is California's only state-operated facility serving individuals with intellectual disabilities who have legal system contact.
GOOD operations_summary: operates a state-run residential facility in Porterville serving individuals with intellectual disabilities and legal-system involvement
NOTES: "California's only" stripped (state name AND superlative framing); city kept.

INPUT name: Woolf Farming Company of California
INPUT description: Woolf Farming Company of California grows, processes, and delivers natural products to the food chain as a certified B Corp in California.
GOOD operations_summary: grows, processes, and delivers agricultural products to the food chain
NOTES: "California" stripped; "certified B Corp" stripped (values positioning).

INPUT name: Roseburg Forest Products
INPUT description: Roseburg Forest Products manufactures diverse wood products like lumber, plywood, and engineered wood for North American construction and furniture markets.
GOOD operations_summary: manufactures wood products including lumber, plywood, and engineered wood for construction and furniture markets
NOTES: "diverse" stripped (filler quantifier); "North American" stripped (continent forbidden).

INPUT name: Hussmann Corporation
INPUT description: Hussmann is a manufacturer of refrigerated display merchandisers and refrigeration systems, providing installation and service to food retailers worldwide.
GOOD operations_summary: manufactures refrigerated display merchandisers and refrigeration systems for food retailers, with installation and service
NOTES: "worldwide" stripped (global scope forbidden).

INPUT name: KARL STORZ Endoscopy-America
INPUT description: KARL STORZ Endoscopy-America sells endoscopes, instruments, imaging systems, electromechanical devices, and OR1 integration solutions in El Segundo to customers across all states.
GOOD operations_summary: sells endoscopes, imaging systems, and OR1 integration solutions to medical customers from El Segundo
NOTES: city El Segundo kept; "across all states" stripped (multi-state scope forbidden).

INPUT name: Universal Music Group
INPUT description: Universal Music Group specializes in music-based entertainment serving artists and fans globally, leveraging insights for brand opportunities.
GOOD operations_summary: produces and distributes recorded music and music-publishing services for artists and consumers
NOTES: "globally" stripped; "leveraging insights for brand opportunities" stripped (corporate puffery).

INPUT name: Suddenlink Communications
INPUT description: Suddenlink provided cable television, high-speed internet, and phone services to residential and business customers.
GOOD operations_summary: operates as a cable, internet, and phone service provider for residential and business customers
NOTES: past-tense "provided" rewritten to present-tense.

INPUT name: Marquez Brothers International
INPUT description: Marquez Brothers International delivers authentic food products including cheeses, creams, yogurts, meats, and desserts maintaining high standards of quality.
GOOD operations_summary: produces and distributes cheeses, yogurts, creams, meats, and desserts for retail and food-service customers
NOTES: "authentic" stripped (values positioning); "maintaining high standards of quality" stripped (quality boasting).

INPUT name: P2S
INPUT description: P2S designs sustainable mechanical, electrical, plumbing, and technology solutions for educational, healthcare, and government sectors.
GOOD operations_summary: designs mechanical, electrical, plumbing, and technology systems for educational, healthcare, and government facilities
NOTES: "sustainable" stripped (values positioning).

INPUT name: Alcon Research
INPUT description: Alcon Research develops and manufactures innovative life-changing vision products including Clareon TruPlus IOLs.
GOOD operations_summary: develops and manufactures vision products including intraocular lenses
NOTES: "innovative" and "life-changing" stripped (novelty boasting).

INPUT name: Sun Pacific
INPUT description: Sun Pacific grows, packs, and ships fresh produce including mandarins, kiwi, oranges, grapes, and lemons.
GOOD operations_summary: grows, packs, and ships fresh produce including mandarins, oranges, grapes, and lemons

INPUT name: WNA Inc.
INPUT description: WNA Inc. is a manufacturer of disposable plastic tableware and food service products based in Chicopee, Massachusetts.
GOOD operations_summary: manufactures disposable plastic tableware and food-service products in Chicopee
NOTES: city Chicopee kept; "Massachusetts" stripped.

INPUT name: Holiday Market
INPUT description: Holiday Market is a grocery store chain providing fresh produce, meats, and deli items across Northern California and Southern Oregon.
GOOD operations_summary: operates a grocery store chain providing fresh produce, meats, and deli items
NOTES: "across Northern California and Southern Oregon" stripped — multi-state scope is forbidden even when it is the description's central scope claim. The chain still has a clear identity ("a grocery store chain") without geographic scope.

INPUT name: Shasta County Road Department
INPUT description: The Shasta County Road Department manages county infrastructure including roads, bridges, traffic signals, and signs, and oversees garbage services for Shasta County residents.
GOOD operations_summary: manages public infrastructure including roads, bridges, traffic signals, and signs, and oversees garbage services
NOTES: "for Shasta County residents" stripped; "county" within "county fleet" / "to county residents" is forbidden even though the entity is a county agency. The entity name "Shasta County Road Department" already conveys the jurisdiction; the verb phrase describes the work.

INPUT name: Providence St Joseph Hospital
INPUT description: Providence St Joseph Hospital provides comprehensive medical services through hospitals, urgent care, and virtual appointments.
GOOD operations_summary: provides medical services through hospitals, urgent care, and virtual appointments
NOTES: "comprehensive" stripped (scope inflation). Especially common in hospital descriptions; never carry it through.

INPUT name: Klamath National Forest
INPUT description: Klamath National Forest manages national forest and grassland lands, offering diverse recreation and focusing on forest health.
GOOD operations_summary: manages national forest and grassland lands, offering recreation and managing forest health
NOTES: "diverse" stripped (filler quantifier). The phrase "offering diverse X" is almost always inflation; just say "offering X".

INPUT name: Sierra Pacific Industries
INPUT description: Sierra Pacific Industries produces wood products including lumber, millwork, windows, doors, and fencing from sustainably managed forests.
GOOD operations_summary: produces wood products including lumber, millwork, windows, doors, and fencing
NOTES: "from sustainably managed forests" stripped (values positioning). Strip the entire trailing values clause; the verb phrase describes the products, not the supply chain virtue.

================================================================================
OUTPUT FORMAT
================================================================================

Return ONLY a JSON array of objects, one per input, in the same order:
[{"name": "...", "operations_summary": "..."}]

No prose before or after. No markdown fences. No explanation.

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
    when assembling ``f"{name} {summary}."``."""
    s = (summary or "").strip()
    while s.endswith("."):
        s = s[:-1].rstrip()
    return s


async def _generate_batch_async(
    client, batch: list[dict], label: str
) -> dict[str, str] | None:
    """Async Gemini call. Returns {name: operations_summary} or None on failure."""
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
    region: str | None = None,
) -> dict:
    """Populate ``operations_summary`` on every employer with a description.

    Append-only by default (only fills employers without one). Pass
    ``regenerate=True`` to overwrite existing summaries. Pass
    ``region`` to scope to employers whose ``regions`` list contains
    the given COE region code (e.g., "FN", "Bay", "OC").
    """
    with open(EMPLOYERS_PATH) as f:
        employers = json.load(f)

    pool = employers
    if region:
        pool = [e for e in pool if region in (e.get("regions") or [])]
    has_description = [e for e in pool if e.get("description")]
    if regenerate:
        targets = has_description
    else:
        targets = [e for e in has_description if not e.get("operations_summary")]
    if limit:
        targets = targets[:limit]

    batches = [targets[i:i + _BATCH_SIZE] for i in range(0, len(targets), _BATCH_SIZE)]
    n_batches = len(batches)

    PROGRESS_LOG.write_text("")
    state = {
        "started_at": _now_iso(),
        "region_filter": region,
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
        f"(regenerate={regenerate}, region={region}, limit={limit})"
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
        "--region", type=str, default=None,
        help="Scope to employers whose regions list contains this COE region code "
             "(FN, CVML, Bay, SCC, LA, IE/D, OC, SD/I).",
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
        region=args.region,
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
