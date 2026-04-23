"""Stratified audit of SWP sector classifications.

For each of the 12 SWP sectors, samples a fixed number of employers
and asks a stronger judge model (Gemini 2.5 Pro by default) to
classify each one blind — without seeing the existing label. Agreement
with the primary classification (from classify_employers.py, run with
Flash) is a proxy for per-sector correctness.

Disagreements fall into three categories operators should review:
  * Genuine misclassifications by the Flash classifier.
  * Genuine misclassifications by the Pro judge (less likely but
    possible when the description is ambiguous).
  * Legitimately borderline employers where either sector is
    defensible.

The script emits:
  1. A per-sector agreement table.
  2. A JSON report (.audit_report.json) with every sample and
     every disagreement, so they can be reviewed outside this run.

Usage:
    python3 -m employers.audit_classifications
    python3 -m employers.audit_classifications --sample-per-sector 30
    python3 -m employers.audit_classifications --judge-model gemini-2.5-flash
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import random
import re
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

from employers.classify_employers import _SECTOR_DEFINITIONS

logger = logging.getLogger(__name__)

_THIS_DIR = Path(__file__).parent
EMPLOYERS_PATH = _THIS_DIR / "employers.json"
AUDIT_REPORT = _THIS_DIR / ".audit_report.json"

_DEFAULT_SAMPLE_PER_SECTOR = 20
_DEFAULT_JUDGE_MODEL = "gemini-2.5-pro"
_SEED = 42
_BATCH_SIZE = 25
_CONCURRENCY = 3


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


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
        "You are auditing Strong Workforce Program sector "
        "classifications. For each employer below, read the "
        "description carefully and pick the SINGLE most representative "
        "SWP sector from the list. This is a blind re-classification — "
        "you do not see any prior label.\n\n"
        "SECTORS:\n" + sector_lines + "\n\n"
        "Rules:\n"
        "1. Pick ONE sector per employer based on the description.\n"
        "2. For multi-line conglomerates, pick what they are most "
        "known for / do most.\n"
        "3. Use exact input employer name verbatim in 'name'.\n\n"
        'Return ONLY a JSON array: [{"name": "...", "sector": "..."}]. '
        "One object per input, same order as input.\n\n"
        "EMPLOYERS:\n" + employer_lines
    )


async def _judge_batch(
    client, types, batch: list[dict], sectors: list[str],
    label: str, model: str,
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
                model=model,
                contents=prompt,
                config=config,
            )
            break
        except Exception as e:
            err = str(e).lower()
            is_transient = any(tok in err for tok in ("503", "429", "rate", "unavailable"))
            if is_transient and attempt == 1:
                print(f"    {label}: transient, retry in 30s", flush=True)
                await asyncio.sleep(30)
                continue
            print(f"    {label}: FAIL — {type(e).__name__}: {e}", flush=True)
            return None
    if response is None or not response.text:
        return None

    try:
        match = re.search(r"\[[\s\S]*\]", response.text)
        source = match.group(0) if match else response.text
        parsed = json.loads(source)
    except json.JSONDecodeError:
        return None

    if not isinstance(parsed, list) or len(parsed) != len(batch):
        return None

    valid = set(sectors)
    return {
        batch[i]["name"]: parsed[i].get("sector")
        for i in range(len(batch))
        if parsed[i].get("sector") in valid
    }


async def _run_audit(
    client, types, sample: list[dict], sectors: list[str], model: str,
) -> dict[str, str]:
    sem = asyncio.Semaphore(_CONCURRENCY)
    batches = [sample[i:i + _BATCH_SIZE] for i in range(0, len(sample), _BATCH_SIZE)]
    n = len(batches)
    results: dict[str, str] = {}
    lock = asyncio.Lock()
    done = [0]

    async def process(idx: int, batch: list[dict]) -> None:
        async with sem:
            t0 = time.monotonic()
            label = f"batch {idx + 1}/{n}"
            r = await _judge_batch(client, types, batch, sectors, label, model)
            elapsed = time.monotonic() - t0
            async with lock:
                if r:
                    results.update(r)
                    done[0] += 1
                    print(f"  {label}: {len(r)}/{len(batch)} judged, {elapsed:.1f}s ({done[0]}/{n})", flush=True)
                else:
                    done[0] += 1
                    print(f"  {label}: FAILED, {elapsed:.1f}s ({done[0]}/{n})", flush=True)

    await asyncio.gather(*[process(i, b) for i, b in enumerate(batches)])
    return results


def run_audit(sample_per_sector: int, judge_model: str) -> dict:
    sectors = list(_SECTOR_DEFINITIONS.keys())

    with open(EMPLOYERS_PATH) as f:
        employers = json.load(f)

    classified = [e for e in employers if e.get("swp_sectors")]
    by_sector: dict[str, list[dict]] = defaultdict(list)
    for e in classified:
        by_sector[e["swp_sectors"][0]].append(e)

    print(f"Dataset: {len(classified)} classified employers across {len(by_sector)} sectors", flush=True)
    for s in sectors:
        print(f"  {len(by_sector[s]):4d}  {s}", flush=True)
    print("", flush=True)

    rng = random.Random(_SEED)
    sample: list[dict] = []
    per_sector_sample: dict[str, list[dict]] = {}
    for s in sectors:
        pool = by_sector[s]
        chunk = rng.sample(pool, min(sample_per_sector, len(pool)))
        per_sector_sample[s] = chunk
        sample.extend(chunk)

    print(f"Sample: {len(sample)} employers (stratified, {sample_per_sector}/sector max)", flush=True)
    print(f"Judge model: {judge_model}", flush=True)
    print("", flush=True)

    client = _get_gemini_client()
    from google.genai import types

    t_start = time.monotonic()
    judgments = asyncio.run(_run_audit(client, types, sample, sectors, judge_model))
    t_elapsed = time.monotonic() - t_start

    # Compute agreement per sector
    per_sector_agreement: dict[str, dict] = {}
    disagreements: list[dict] = []

    for s in sectors:
        chunk = per_sector_sample[s]
        agree = 0
        judged = 0
        for emp in chunk:
            judgment = judgments.get(emp["name"])
            if judgment is None:
                continue
            judged += 1
            if judgment == s:
                agree += 1
            else:
                disagreements.append({
                    "name": emp["name"],
                    "description": emp.get("description"),
                    "flash_sector": s,
                    "pro_sector": judgment,
                })
        per_sector_agreement[s] = {
            "sampled": len(chunk),
            "judged": judged,
            "agreed": agree,
            "disagreed": judged - agree,
            "agreement_pct": round(100 * agree / judged, 1) if judged else 0,
        }

    total_sampled = sum(a["sampled"] for a in per_sector_agreement.values())
    total_judged = sum(a["judged"] for a in per_sector_agreement.values())
    total_agreed = sum(a["agreed"] for a in per_sector_agreement.values())

    report = {
        "ran_at": _now_iso(),
        "judge_model": judge_model,
        "elapsed_s": round(t_elapsed, 1),
        "total_sampled": total_sampled,
        "total_judged": total_judged,
        "total_agreed": total_agreed,
        "overall_agreement_pct": round(100 * total_agreed / total_judged, 1) if total_judged else 0,
        "per_sector_agreement": per_sector_agreement,
        "disagreements": disagreements,
    }

    AUDIT_REPORT.write_text(json.dumps(report, indent=2))

    print("=" * 70, flush=True)
    print("AUDIT RESULTS", flush=True)
    print("=" * 70, flush=True)
    print(f"Elapsed:              {report['elapsed_s']}s", flush=True)
    print(f"Sampled / Judged:     {total_sampled} / {total_judged}", flush=True)
    print(f"Overall agreement:    {report['overall_agreement_pct']}%", flush=True)
    print("", flush=True)
    print(f"{'Sector':55} {'N':>4} {'Agree':>6} {'%':>5}", flush=True)
    print("-" * 70, flush=True)
    for s in sectors:
        a = per_sector_agreement[s]
        print(f"{s:55} {a['sampled']:>4} {a['agreed']:>6} {a['agreement_pct']:>5.1f}", flush=True)
    print("", flush=True)
    print(f"Disagreements written to {AUDIT_REPORT.name}: {len(disagreements)}", flush=True)

    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sample-per-sector", type=int, default=_DEFAULT_SAMPLE_PER_SECTOR)
    parser.add_argument("--judge-model", type=str, default=_DEFAULT_JUDGE_MODEL)
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(message)s")
    run_audit(args.sample_per_sector, args.judge_model)


if __name__ == "__main__":
    main()
