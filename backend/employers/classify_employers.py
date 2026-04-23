"""Classify employers into a single primary SWP sector via Gemini.

Replaces the prior NAICS-derived classification stack (retag_sectors,
drop_out_of_scope, classify_orphans) with a single description-driven
LLM call. The description field — generated from each employer's
website by populate_description.py — is a far richer signal than NAICS
codes for distinguishing what the employer actually does. Defense
contractors and medical-device makers can share NAICS 3345; their
descriptions cannot be confused.

Design goals (mirrors populate_description.py):
  * One input (description), one output (single sector enum). No
    fallback chains, no NAICS lookups, no name-pattern rules.
  * Observable: per-batch progress log + structured state file +
    incremental employers.json writes.
  * Fail-fast: no retries on deterministic 4xx errors; one retry on
    transient 5xx/429; any other failure sets the affected employers'
    swp_sectors = [] so the next run re-attempts them.
  * Parallel: batches are independent; asyncio + bounded semaphore.
  * No fallbacks for MVP: employers lacking website or description
    are DROPPED from the dataset (per operator direction — null
    description means no qualifying online presence).

Usage:
    python3 -m employers.classify_employers --dry-run
    python3 -m employers.classify_employers
    python3 -m employers.classify_employers --concurrency 3
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import re
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)

_THIS_DIR = Path(__file__).parent
EMPLOYERS_PATH = _THIS_DIR / "employers.json"
PROGRESS_LOG = _THIS_DIR / ".classify_progress.log"
STATE_FILE = _THIS_DIR / ".classify_state.json"

_BATCH_SIZE = 50
_DEFAULT_CONCURRENCY = 5
_INCREMENTAL_WRITE_EVERY = 5
_TRANSIENT_RETRY_SLEEP = 30.0


_SECTOR_DEFINITIONS: dict[str, str] = {
    "Advanced Manufacturing": (
        "Manufacturing of complex products: defense, aerospace, "
        "electronics, machinery, medical devices, industrial equipment."
    ),
    "Advanced Transportation and Logistics": (
        "Transit systems, trucking, shipping, warehousing, "
        "distribution, last-mile delivery, supply-chain operations."
    ),
    "Agriculture, Water and Environmental Technologies": (
        "Farming, food processing, beverages, dairy, water management, "
        "environmental services, waste management, conservation."
    ),
    "Business and Entrepreneurship": (
        "Management consulting, business services, marketing/PR, "
        "professional services that support general business operations."
    ),
    "Education and Human Development": (
        "Schools, school districts, universities, training programs, "
        "social services, family services, child welfare, vocational rehab."
    ),
    "Energy, Construction and Utilities": (
        "Construction trades, builders, contractors, utilities, "
        "energy production/distribution, infrastructure, public works."
    ),
    "Global Trade": (
        "Wholesale distribution, import/export, large-scale "
        "wholesale of consumer or industrial goods."
    ),
    "Health": (
        "Hospitals, clinics, medical practices, healthcare delivery, "
        "dental, behavioral health, healthcare facilities."
    ),
    "Information and Communication Technologies - Digital Media": (
        "Software, IT services, telecommunications, networking, "
        "digital media production, broadcasting, web/cloud services."
    ),
    "Life Sciences - Biotechnology": (
        "Biotech R&D, pharmaceutical research, life-sciences research, "
        "genetic/diagnostic research, scientific R&D."
    ),
    "Public Safety": (
        "Police, sheriff, fire, corrections, jail/detention, courts, "
        "district attorney/public defender, lifeguards, emergency response."
    ),
    "Retail, Hospitality and Tourism": (
        "Restaurants, hotels/resorts, retail stores, tourism, "
        "recreation venues, food service, casinos, theme parks."
    ),
}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _progress(msg: str) -> None:
    line = f"[{_now_iso()}] {msg}"
    print(line, flush=True)
    with open(PROGRESS_LOG, "a") as f:
        f.write(line + "\n")


def _write_state(state: dict) -> None:
    STATE_FILE.write_text(json.dumps(state, indent=2))


def _get_gemini_client():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY not set")
    from google import genai
    return genai.Client(api_key=api_key)


def _build_prompt(batch: list[dict], sectors: list[str]) -> str:
    sector_lines = "\n".join(
        f"- {s}: {_SECTOR_DEFINITIONS[s]}" for s in sectors
    )
    employer_lines = "\n".join(
        f"- {e['name']}: {e['description']}" for e in batch
    )
    return (
        "Classify each employer below into exactly ONE Strong Workforce "
        "Program sector based on their description.\n\n"
        "SECTORS:\n" + sector_lines + "\n\n"
        "Rules:\n"
        "1. Pick the SINGLE most representative sector for the employer's "
        "primary line of business.\n"
        "2. Use the description as the source of truth. Read it carefully; "
        "the employer name alone is not enough.\n"
        "3. For multi-line conglomerates, pick what they are most known "
        "for / do most.\n"
        "4. Use the exact input employer name verbatim in the 'name' field.\n\n"
        'Return ONLY a JSON array: [{"name": "...", "sector": "..."}]. '
        "One object per input, same order as input. No prose outside JSON.\n\n"
        "EMPLOYERS:\n" + employer_lines
    )


async def _classify_batch_async(
    client, types, batch: list[dict], sectors: list[str], label: str
) -> dict[str, str] | None:
    prompt = _build_prompt(batch, sectors)
    schema = {
        "type": "ARRAY",
        "items": {
            "type": "OBJECT",
            "properties": {
                "name": {"type": "STRING"},
                "sector": {"type": "STRING", "enum": sectors},
            },
            "required": ["name", "sector"],
        },
    }
    config = types.GenerateContentConfig(
        response_mime_type="application/json",
        response_schema=schema,
        temperature=0.0,
    )

    response = None
    for attempt in (1, 2):
        try:
            response = await client.aio.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=config,
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
    if response is None or not response.text:
        _progress(f"    {label}: FAIL — empty response")
        return None

    try:
        # With response_schema enforced, the output should already be
        # valid JSON without preamble, but use regex extract for
        # resilience.
        match = re.search(r"\[[\s\S]*\]", response.text)
        source = match.group(0) if match else response.text
        parsed = json.loads(source)
    except json.JSONDecodeError as e:
        _progress(f"    {label}: FAIL — JSON parse: {e}")
        return None

    if not isinstance(parsed, list) or len(parsed) != len(batch):
        _progress(f"    {label}: FAIL — shape mismatch")
        return None

    valid_sectors = set(sectors)
    out: dict[str, str] = {}
    for i in range(len(batch)):
        name = batch[i]["name"]
        sector = parsed[i].get("sector")
        if sector in valid_sectors:
            out[name] = sector
    return out


async def _run_all_batches(
    client,
    types,
    batches: list[list[dict]],
    employers: list[dict],
    sectors: list[str],
    concurrency: int,
    dry_run: bool,
    state: dict,
) -> tuple[Counter, int]:
    sem = asyncio.Semaphore(concurrency)
    write_lock = asyncio.Lock()
    n_batches = len(batches)
    by_sector: Counter = Counter()
    totals = {"done": 0, "classified": 0, "failed": 0}

    # Employer name → list of refs so we can stamp the result back.
    # (Names are unique in employers.json.)
    name_to_emp = {e["name"]: e for e in employers}

    async def process(batch_idx: int, batch: list[dict]) -> None:
        async with sem:
            label = f"batch {batch_idx + 1}/{n_batches}"
            t0 = time.monotonic()
            result = await _classify_batch_async(client, types, batch, sectors, label)
            elapsed = time.monotonic() - t0

            async with write_lock:
                if result:
                    got = 0
                    for emp in batch:
                        sector = result.get(emp["name"])
                        if sector:
                            name_to_emp[emp["name"]]["swp_sectors"] = [sector]
                            by_sector[sector] += 1
                            totals["classified"] += 1
                            got += 1
                        else:
                            totals["failed"] += 1
                    _progress(
                        f"  {label}: {got}/{len(batch)} classified, "
                        f"{elapsed:.1f}s ({totals['done'] + 1}/{n_batches} done)"
                    )
                else:
                    totals["failed"] += len(batch)
                    _progress(
                        f"  {label}: 0/{len(batch)} (failed), "
                        f"{elapsed:.1f}s ({totals['done'] + 1}/{n_batches} done)"
                    )

                totals["done"] += 1
                state.update({
                    "batches_done": totals["done"],
                    "classified": totals["classified"],
                    "failed": totals["failed"],
                    "updated_at": _now_iso(),
                })
                _write_state(state)

                if not dry_run and totals["done"] % _INCREMENTAL_WRITE_EVERY == 0:
                    with open(EMPLOYERS_PATH, "w") as f:
                        json.dump(employers, f, indent=2)
                    _progress(f"  checkpoint: wrote employers.json after {totals['done']} batches")

    tasks = [process(i, batches[i]) for i in range(n_batches)]
    await asyncio.gather(*tasks)
    return by_sector, totals["failed"]


def classify(dry_run: bool = False, concurrency: int = _DEFAULT_CONCURRENCY) -> dict:
    sectors = list(_SECTOR_DEFINITIONS.keys())

    with open(EMPLOYERS_PATH) as f:
        employers = json.load(f)

    before_total = len(employers)

    # Drop employers lacking website or description. No fallbacks.
    keep: list[dict] = []
    dropped_no_website = 0
    dropped_no_description = 0
    for emp in employers:
        if not emp.get("website"):
            dropped_no_website += 1
            continue
        if not emp.get("description"):
            dropped_no_description += 1
            continue
        keep.append(emp)

    # Classification targets are the kept employers. Also overwrite the
    # employers list to drop the filtered-out entries from the dataset.
    targets = keep
    batches = [targets[i:i + _BATCH_SIZE] for i in range(0, len(targets), _BATCH_SIZE)]
    n_batches = len(batches)

    PROGRESS_LOG.write_text("")
    state = {
        "started_at": _now_iso(),
        "before_total": before_total,
        "dropped_no_website": dropped_no_website,
        "dropped_no_description": dropped_no_description,
        "targets": len(targets),
        "batches_total": n_batches,
        "batches_done": 0,
        "classified": 0,
        "failed": 0,
        "concurrency": concurrency,
    }
    _write_state(state)
    _progress(
        f"Started classify: {len(targets)} targets in {n_batches} batches "
        f"of {_BATCH_SIZE}, concurrency={concurrency}. "
        f"Dropped {dropped_no_website} no-website, "
        f"{dropped_no_description} no-description from {before_total}."
    )

    if not targets:
        _progress("Nothing to do.")
        state["finished_at"] = _now_iso()
        _write_state(state)
        return state

    client = _get_gemini_client()
    from google.genai import types

    by_sector, failed = asyncio.run(
        _run_all_batches(client, types, batches, targets, sectors, concurrency, dry_run, state)
    )

    if not dry_run:
        with open(EMPLOYERS_PATH, "w") as f:
            json.dump(targets, f, indent=2)
        _progress(f"Final write: employers.json with {len(targets)} employers")

    state["by_sector"] = dict(by_sector.most_common())
    state["finished_at"] = _now_iso()
    _write_state(state)
    _progress(
        f"Done: {sum(by_sector.values())} classified, {failed} failed, "
        f"kept {len(targets)} of {before_total} employers"
    )
    return state


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--concurrency", type=int, default=_DEFAULT_CONCURRENCY)
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(message)s")
    state = classify(dry_run=args.dry_run, concurrency=args.concurrency)

    print("=" * 60)
    print("FINAL STATE")
    print("=" * 60)
    for k, v in state.items():
        if isinstance(v, dict):
            print(f"  {k}:")
            for s, n in v.items():
                print(f"    {n:4d}  {s}")
        else:
            print(f"  {k:28s}  {v}")
    if args.dry_run:
        print("(dry run — employers.json not modified)")


if __name__ == "__main__":
    main()
