"""Stratified sample audit of employer→occupation assignments.

Produces a human-readable markdown checklist for sampled employers so
a reviewer can quickly judge whether each employer's assigned SOC
occupations are rational given its name, URL, sector, and description.

Optionally runs a stronger judge model (Gemini 2.5 Pro) over the same
sample for a quantitative agreement signal — useful for spotting
systematic drift in the Flash-driven occupation picker.

Stratification: samples are drawn per region, then balanced across
SWP sectors within the region so the dominant sector doesn't crowd
out the long tail.

Usage:
    python3 -m employers.audit_occupations
    python3 -m employers.audit_occupations --per-region 20
    python3 -m employers.audit_occupations --judge   # also run Pro comparison
    python3 -m employers.audit_occupations --region OC --per-region 30
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import random
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)

_THIS_DIR = Path(__file__).parent
EMPLOYERS_PATH = _THIS_DIR / "employers.json"
OCCUPATIONS_PATH = _THIS_DIR.parent / "occupations" / "occupations.json"
SAMPLE_MD = _THIS_DIR / ".audit_occupations_sample.md"
JUDGE_REPORT = _THIS_DIR / ".audit_occupations_judge.json"

REGIONS = ["FN", "CVML", "IE/D", "SCC", "Bay", "LA", "SD/I", "OC"]


def _is_loaded(emp: dict) -> bool:
    if not emp.get("enrichment_attempted"):
        return True
    if not emp.get("identity_verified"):
        return False
    return emp.get("enrichment_promoted") is True


def _load_soc_titles() -> dict[str, str]:
    with open(OCCUPATIONS_PATH) as f:
        occs = json.load(f)
    return {o["soc_code"]: o["title"] for o in occs}


def _stratified_sample(
    employers: list[dict],
    region: str,
    n: int,
    rng: random.Random,
) -> list[dict]:
    """Sample n employers from `region`, balancing across SWP sectors."""
    pool = [e for e in employers if region in e.get("regions", []) and _is_loaded(e)]
    if not pool:
        return []
    by_sector: dict[str, list[dict]] = defaultdict(list)
    for e in pool:
        sect = (e.get("swp_sectors") or ["(none)"])[0]
        by_sector[sect].append(e)
    # Round-robin pull from each sector bucket until n is reached
    for bucket in by_sector.values():
        rng.shuffle(bucket)
    sectors = list(by_sector.keys())
    rng.shuffle(sectors)
    chosen: list[dict] = []
    while len(chosen) < n and any(by_sector[s] for s in sectors):
        for s in sectors:
            if by_sector[s] and len(chosen) < n:
                chosen.append(by_sector[s].pop())
    return chosen


def _format_employer_block(emp: dict, soc_titles: dict[str, str]) -> str:
    name = emp["name"]
    url = emp.get("website") or "(no url)"
    desc = emp.get("description") or "(no description)"
    sector = (emp.get("swp_sectors") or ["(none)"])[0]
    occs = emp.get("occupations") or []
    region_str = ", ".join(emp.get("regions", []))

    occ_lines = []
    for soc in occs:
        title = soc_titles.get(soc, "(unknown SOC)")
        occ_lines.append(f"  - `{soc}` — {title}")
    occ_block = "\n".join(occ_lines) if occ_lines else "  - (none)"

    return (
        f"### {name}\n\n"
        f"- **Regions:** {region_str}\n"
        f"- **Sector:** {sector}\n"
        f"- **Website:** {url}\n"
        f"- **Description:** {desc}\n"
        f"- **Occupations:**\n{occ_block}\n\n"
        f"Reviewer flags (mark `[x]`):\n"
        f"- [ ] Occupations include obvious wrong picks (list them)\n"
        f"- [ ] Occupations missing obvious right picks (list them)\n"
        f"- [ ] Sector is wrong\n"
        f"- [ ] Description doesn't match the actual company\n"
        f"- [ ] URL is broken or wrong-entity\n\n"
        f"Notes: \n\n---\n\n"
    )


def emit_markdown(samples_by_region: dict[str, list[dict]], soc_titles: dict[str, str]) -> str:
    out = ["# Employer occupation sample audit\n"]
    out.append(f"_Generated {datetime.now(timezone.utc).isoformat(timespec='seconds')}_\n\n")
    total = sum(len(v) for v in samples_by_region.values())
    out.append(f"**Total samples: {total}** across {len(samples_by_region)} regions.\n\n")
    out.append(
        "Read each block. The most important question for each employer:\n"
        "**given the description, are the listed occupations a reasonable\n"
        "match for jobs that would actually be hired here?** Mark obvious\n"
        "wrong picks and obvious missing picks; we'll use the marked file\n"
        "to drive any occupation-pass fixes.\n\n"
    )
    for region in REGIONS:
        if region not in samples_by_region:
            continue
        out.append(f"## Region: {region}\n\n")
        for emp in samples_by_region[region]:
            out.append(_format_employer_block(emp, soc_titles))
    return "".join(out)


# ── Optional judge pass ────────────────────────────────────────────────


_JUDGE_PROMPT = (
    "You are auditing occupation assignments for a community-college "
    "workforce-development tool.\n\n"
    "An employer below has been assigned 1-5 SOC occupations from a "
    "constrained pool. Without looking at any URL, judge whether each "
    "assigned occupation is plausibly hired by this employer.\n\n"
    "EMPLOYER:\n"
    "  Name: {name}\n"
    "  Sector: {sector}\n"
    "  Description: {desc}\n\n"
    "ASSIGNED OCCUPATIONS:\n{occs}\n\n"
    "For each assigned occupation, answer 'plausible' or 'implausible'. "
    "Then give an overall verdict:\n"
    "  'all_plausible'  - every assigned occupation is plausible\n"
    "  'mostly_plausible' - most plausible, 1-2 weak picks\n"
    "  'mixed'  - some clearly wrong picks\n"
    "  'wrong'  - the assignment is broadly off\n\n"
    "Return JSON only:\n"
    '{{"per_occupation": {{"<soc>": "plausible"|"implausible", ...}}, '
    '"verdict": "all_plausible"|"mostly_plausible"|"mixed"|"wrong", '
    '"comment": "<one short sentence>"}}'
)


async def _judge_one(client, types, emp: dict, soc_titles: dict[str, str]) -> dict:
    occs = emp.get("occupations") or []
    occ_lines = "\n".join(
        f"  - {soc} — {soc_titles.get(soc, '(unknown)')}" for soc in occs
    )
    prompt = _JUDGE_PROMPT.format(
        name=emp["name"],
        sector=(emp.get("swp_sectors") or ["(none)"])[0],
        desc=(emp.get("description") or "")[:500],
        occs=occ_lines or "  (none)",
    )
    config = types.GenerateContentConfig(
        response_mime_type="application/json",
        temperature=0.0,
    )
    try:
        r = await client.aio.models.generate_content(
            model="gemini-2.5-pro",
            contents=prompt,
            config=config,
        )
        return json.loads(r.text)
    except Exception as e:
        return {"verdict": "error", "error": str(e)[:200], "per_occupation": {}}


async def _run_judge(samples_by_region: dict[str, list[dict]], soc_titles: dict[str, str]) -> list[dict]:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY not set")
    from google import genai
    from google.genai import types
    client = genai.Client(api_key=api_key)

    flat = []
    for region, samples in samples_by_region.items():
        for emp in samples:
            flat.append((region, emp))

    logger.info(f"Judging {len(flat)} samples with gemini-2.5-pro (batched 5)")
    results = []
    for i in range(0, len(flat), 5):
        batch = flat[i:i + 5]
        verdicts = await asyncio.gather(
            *(_judge_one(client, types, emp, soc_titles) for _region, emp in batch)
        )
        for (region, emp), v in zip(batch, verdicts):
            results.append({
                "region": region,
                "name": emp["name"],
                "sector": (emp.get("swp_sectors") or [None])[0],
                "assigned": emp.get("occupations") or [],
                "judge": v,
            })
        logger.info(f"  judged {min(i + 5, len(flat))}/{len(flat)}")
    return results


# ── Main ───────────────────────────────────────────────────────────────


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Stratified sample audit of employer→occupation assignments."
    )
    parser.add_argument("--per-region", type=int, default=15,
                        help="Samples to draw per region (default: 15)")
    parser.add_argument("--region", type=str, default=None,
                        help="Limit to a single region (e.g., OC)")
    parser.add_argument("--seed", type=int, default=42,
                        help="Random seed for reproducible sampling")
    parser.add_argument("--judge", action="store_true",
                        help="Also run gemini-2.5-pro to flag implausible picks")
    args = parser.parse_args()

    try:
        from dotenv import load_dotenv
        env_path = Path(__file__).resolve().parent.parent.parent / ".env"
        load_dotenv(env_path)
    except ImportError:
        pass

    logging.basicConfig(level=logging.INFO, format="%(message)s")
    rng = random.Random(args.seed)

    with open(EMPLOYERS_PATH) as f:
        employers = json.load(f)
    soc_titles = _load_soc_titles()

    target_regions = [args.region] if args.region else REGIONS
    samples_by_region: dict[str, list[dict]] = {}
    for region in target_regions:
        s = _stratified_sample(employers, region, args.per_region, rng)
        if s:
            samples_by_region[region] = s

    md = emit_markdown(samples_by_region, soc_titles)
    SAMPLE_MD.write_text(md)
    total = sum(len(v) for v in samples_by_region.values())
    print(f"Wrote {total} samples → {SAMPLE_MD}")

    if args.judge:
        results = asyncio.run(_run_judge(samples_by_region, soc_titles))
        JUDGE_REPORT.write_text(json.dumps(results, indent=2))

        # Aggregate
        from collections import Counter
        verdicts = Counter(r["judge"].get("verdict", "error") for r in results)
        print("\nJudge verdicts:")
        for v, c in verdicts.most_common():
            print(f"  {c:4d}  {v}")
        print(f"\nFull report → {JUDGE_REPORT}")

        # Surface the worst offenders for quick scanning
        problems = [r for r in results if r["judge"].get("verdict") in ("mixed", "wrong")]
        if problems:
            print(f"\n{len(problems)} flagged 'mixed' or 'wrong' — see {JUDGE_REPORT}")
            for r in problems[:10]:
                comment = r["judge"].get("comment", "")
                print(f"  [{r['region']}] {r['name']}: {r['judge'].get('verdict')} — {comment}")


if __name__ == "__main__":
    main()
