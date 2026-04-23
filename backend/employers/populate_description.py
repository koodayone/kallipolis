"""Populate the ``description`` field for every employer from their website.

Design goals:
  * Minimal input/output: the LLM reads the employer's website via URL
    context and returns a single 30-50 word sentence. No prose essays;
    no template fields; no confidence scores; no fallback tiers. Just
    the text needed to (a) show in the atlas UI as a scannable one-
    liner and (b) feed the downstream SWP sector classifier.
  * Observable from the first batch: writes a line per batch to a
    progress file, a structured state file after every batch, and
    incremental ``employers.json`` writes every _INCREMENTAL_WRITE_EVERY
    batches. PYTHONUNBUFFERED=1 in the backend container's env makes
    stdout line-flushed as well.
  * Fail-fast on anomalies: no retries on deterministic errors (4xx,
    schema mismatches, malformed JSON). One retry on transient 5xx/
    429 with a 30-second back-off. Anything else that fails gets its
    batch's employers flagged with ``description: null`` (same three-
    state pattern as ``website``) so the next run re-attempts them.
  * Parallelism: batches are independent (each is a self-contained
    Gemini call with no cross-batch state). Run _CONCURRENCY batches
    concurrently via asyncio + a bounded semaphore. Scales linearly
    with concurrency until the API rate limit is hit; 429s fall to
    the transient-retry path.

Only employers with a verified website are processed.

Usage:
    python3 -m employers.populate_description --dry-run
    python3 -m employers.populate_description --limit 20 --force     # test
    python3 -m employers.populate_description --force                 # full one-shot
    python3 -m employers.populate_description                         # incremental
    python3 -m employers.populate_description --concurrency 5 --force # dial down
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
PROGRESS_LOG = _THIS_DIR / ".populate_progress.log"
STATE_FILE = _THIS_DIR / ".populate_state.json"

# 5 URLs per batch balances URL-fetch latency (Gemini fetches
# sequentially within a single call) against per-batch overhead.
_URL_BATCH_SIZE = 5

# Default concurrency. 10 concurrent batches = 50 URLs in flight at
# once. Well under the paid-tier Gemini Flash RPM ceiling; transient
# 429s fall to the one-retry path. Override via --concurrency on the
# CLI to dial up (faster) or down (if rate-limited).
_DEFAULT_CONCURRENCY = 10

# Incremental write cadence for employers.json. Every 10 completed
# batches = 50 employers, so a crash loses at most ~50 descriptions.
_INCREMENTAL_WRITE_EVERY = 10

# Single retry with 30 s back-off on 5xx/429; then give up.
_TRANSIENT_RETRY_SLEEP = 30.0


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
    lines = "\n".join(f"- {e['name']} | {e['website']}" for e in batch)
    return (
        "Read each employer's website and write ONE sentence (30-50 "
        "words) describing what they do and their primary industry. "
        "Be factual; do not hallucinate. Use the exact input employer "
        "name verbatim.\n\n"
        'Return ONLY a JSON array: [{"name": "...", "description": "..."}]\n'
        "One object per input, same order as input. No prose, no "
        "markdown, no explanation outside the JSON.\n\n"
        "EMPLOYERS:\n" + lines
    )


# LLM-failure patterns — descriptions matching these are the model
# telling us it couldn't fetch the URL, dressed up as a description.
# They slip past length and template-prefix gates because they're
# grammatically normal sentences. Matched at start, case-insensitive.
_LLM_FAILURE_PATTERNS = (
    "i am unable to",
    "i cannot",
    "i could not",
    "unable to access",
    "unable to provide a description",
    "cannot provide a description",
    "website content could not be",
    "website could not be browsed",
    "url could not be fetched",
    "url could not be accessed",
    "no description can be",
    "no description could be",
)


def _is_llm_failure_leak(description: str) -> bool:
    lower = description.strip().lower()
    return any(p in lower for p in _LLM_FAILURE_PATTERNS)


async def _generate_batch_async(
    client, types, batch: list[dict], label: str
) -> dict[str, str] | None:
    """Async Gemini call. Returns {name: description} or None on any failure.

    Fail-fast policy:
      * 4xx / invalid_argument / permission → immediate None (no retry)
      * 5xx / 429 / rate → one retry after _TRANSIENT_RETRY_SLEEP
      * Empty response / no JSON array / parse error → immediate None
      * Any other exception → immediate None
    Per-description gate: descriptions matching LLM failure patterns
    are dropped (returned as empty string) so the upstream flag-null
    path handles them. These patterns are the model saying "I couldn't
    read the URL" in prose form; they slip past length/template gates
    because they're grammatically normal sentences.
    """
    prompt = _build_prompt(batch)
    config = types.GenerateContentConfig(
        tools=[types.Tool(url_context=types.UrlContext())],
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
        desc = str(parsed[i].get("description", "") or "").strip()
        if desc and _is_llm_failure_leak(desc):
            # Model produced a prose "I can't read this URL" as the
            # description. Treat as failure, not success.
            out[batch[i]["name"]] = ""
        else:
            out[batch[i]["name"]] = desc
    return out


async def _run_all_batches(
    client,
    types,
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

    # Mutable counters guarded by write_lock.
    totals = {"done": 0, "populated": 0, "flagged": 0}

    async def process(batch_idx: int, batch: list[dict]) -> None:
        async with sem:
            label = f"batch {batch_idx + 1}/{n_batches}"
            t0 = time.monotonic()
            result = await _generate_batch_async(client, types, batch, label)
            elapsed = time.monotonic() - t0

            async with write_lock:
                if result:
                    got = 0
                    for emp in batch:
                        desc = result.get(emp["name"], "")
                        if desc:
                            emp["description"] = desc
                            totals["populated"] += 1
                            got += 1
                        else:
                            emp["description"] = None
                            totals["flagged"] += 1
                    _progress(
                        f"  {label}: {got}/{len(batch)} populated, "
                        f"{elapsed:.1f}s ({totals['done'] + 1}/{n_batches} done)"
                    )
                else:
                    for emp in batch:
                        emp["description"] = None
                        totals["flagged"] += 1
                    _progress(
                        f"  {label}: 0/{len(batch)} (failed), "
                        f"{elapsed:.1f}s ({totals['done'] + 1}/{n_batches} done)"
                    )

                totals["done"] += 1
                state.update({
                    "batches_done": totals["done"],
                    "descriptions_populated": totals["populated"],
                    "descriptions_flagged_null": totals["flagged"],
                    "last_batch_label": label,
                    "last_batch_elapsed_s": round(elapsed, 1),
                    "updated_at": _now_iso(),
                })
                _write_state(state)

                # Incremental write pegged to completion count, not
                # batch_idx (which arrives out of order under parallelism).
                if not dry_run and totals["done"] % _INCREMENTAL_WRITE_EVERY == 0:
                    with open(EMPLOYERS_PATH, "w") as f:
                        json.dump(employers, f, indent=2)
                    _progress(f"  checkpoint: wrote employers.json after {totals['done']} batches")

    tasks = [process(i, batches[i]) for i in range(n_batches)]
    await asyncio.gather(*tasks)
    return totals["populated"], totals["flagged"]


def populate(
    dry_run: bool = False,
    limit: int | None = None,
    force: bool = False,
    concurrency: int = _DEFAULT_CONCURRENCY,
) -> dict:
    with open(EMPLOYERS_PATH) as f:
        employers = json.load(f)

    before_total = len(employers)
    has_website = [e for e in employers if e.get("website")]

    if force:
        targets = has_website
    else:
        targets = [e for e in has_website if not e.get("description")]
    if limit:
        targets = targets[:limit]

    batches = [targets[i:i + _URL_BATCH_SIZE] for i in range(0, len(targets), _URL_BATCH_SIZE)]
    n_batches = len(batches)

    PROGRESS_LOG.write_text("")  # truncate
    state = {
        "started_at": _now_iso(),
        "targets": len(targets),
        "batches_total": n_batches,
        "batches_done": 0,
        "descriptions_populated": 0,
        "descriptions_flagged_null": 0,
        "concurrency": concurrency,
    }
    _write_state(state)
    _progress(
        f"Started populate: {len(targets)} targets in {n_batches} batches "
        f"of {_URL_BATCH_SIZE}, concurrency={concurrency} "
        f"(force={force}, limit={limit})"
    )

    if not targets:
        _progress("Nothing to do.")
        return state

    client = _get_gemini_client()
    from google.genai import types

    populated, flagged = asyncio.run(
        _run_all_batches(client, types, batches, employers, concurrency, dry_run, state)
    )

    if not dry_run:
        with open(EMPLOYERS_PATH, "w") as f:
            json.dump(employers, f, indent=2)
        _progress(f"Final write: employers.json")

    state["finished_at"] = _now_iso()
    state["descriptions_populated"] = populated
    state["descriptions_flagged_null"] = flagged
    _write_state(state)
    _progress(
        f"Done: {populated} populated, {flagged} flagged null out of {len(targets)} targets"
    )
    return state


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--concurrency", type=int, default=_DEFAULT_CONCURRENCY,
                        help=f"Concurrent batches in flight (default {_DEFAULT_CONCURRENCY})")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(message)s")
    state = populate(
        dry_run=args.dry_run,
        limit=args.limit,
        force=args.force,
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
