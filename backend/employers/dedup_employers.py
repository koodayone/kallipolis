"""Deduplicate employer records by website-cluster + LLM judgment.

Many EDD-derived records that share a website are actually the same
entity recorded twice with name variations (Saint Agnes / St. Agnes;
Tulare Joint Union High School / Tulare Joint Union High School District;
Lion Raisins / Lion Dehydrators). Others sharing a website are
genuinely separate facilities of the same parent (Adventist Health
Tulare / Adventist Health Hanford / Adventist Health Reedley — four
distinct hospitals). The dedup job is to tell the two cases apart.

Approach:

  1. Cluster employers by canonicalized website (strip trailing slash,
     lowercase). The canonicalization is intentionally minimal — the
     LLM handles all semantic judgment downstream.

  2. For each cluster with >1 employer, send a Flash call with the
     names, descriptions, and regions. The response_schema enforces a
     groupings output: each input employer is assigned to a group,
     where employers in the same group are deemed the same entity.

  3. For each group with >1 member, merge into one record:
     - Name: prefer the longer, more-canonical name (Saint Agnes over St. Agnes)
     - Description: prefer the longer of the two
     - Regions: union
     - Occupations: union, capped at _OCC_MAX (5)
     - swp_sectors: keep dominant
     - Website: shared (already by definition)
     - Boolean flags: AND-merge

  4. Log every merge to merges.jsonl for transparency. Restoreable from
     git if a merge proves wrong.

Usage:
    python3 -m employers.dedup_employers --dry-run
    python3 -m employers.dedup_employers
    python3 -m employers.dedup_employers --region FN  # scope to one region
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)

_THIS_DIR = Path(__file__).parent
EMPLOYERS_PATH = _THIS_DIR / "employers.json"
MERGES_LOG = _THIS_DIR / "merges.jsonl"

_OCC_MAX = 5  # match enrich.py's ceiling


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _canonical_url(url: str) -> str:
    """Minimal canonicalization for clustering: lowercase, strip
    trailing slash, strip leading 'www.'. The semantic question 'do
    these employers share an actual web identity' is what we're
    testing; small normalization differences shouldn't fragment the
    cluster."""
    if not url:
        return ""
    u = url.strip().lower().rstrip("/")
    # Strip http(s):// for comparison
    u = re.sub(r"^https?://", "", u)
    # Strip leading www. so www.foo.com == foo.com
    u = re.sub(r"^www\.", "", u)
    return u


def _build_clusters(employers: list[dict], region: str | None) -> dict[str, list[dict]]:
    """Group employers by canonical website. Filters to a region if given."""
    clusters: dict[str, list[dict]] = defaultdict(list)
    for e in employers:
        if region and region not in e.get("regions", []):
            continue
        url = _canonical_url(e.get("website", "") or "")
        if not url:
            continue
        clusters[url].append(e)
    return {k: v for k, v in clusters.items() if len(v) > 1}


# ── LLM judgment ────────────────────────────────────────────────────────


def _build_dedup_prompt(employers: list[dict]) -> str:
    """One LLM call per same-website cluster. Asks the model to group
    employers into same-entity groups."""
    lines = []
    for i, e in enumerate(employers):
        regions = ",".join(e.get("regions", []))
        desc = (e.get("description") or "")[:300]
        lines.append(
            f"[{i}] {e['name']}\n"
            f"    regions: {regions}\n"
            f"    description: {desc}"
        )
    return (
        "These employers share the same website. Determine which are "
        "the same entity (name variations of one organization) and "
        "which are separate facilities or divisions of a shared parent "
        "organization.\n\n"
        "Rule of thumb:\n"
        "- Same entity (MERGE): name spellings differ trivially "
        "('Saint' vs 'St.', '\\u0027s Office' suffix, 'Inc/Company/District' "
        "suffix added, descriptive expansion like 'X' vs 'X Retirement "
        "Community').\n"
        "- Separate entities (KEEP SEPARATE): name distinguishes by "
        "city, division, or facility type ('Adventist Health Tulare' vs "
        "'Adventist Health Hanford' — different cities = different "
        "facilities; 'Enloe Medical Center' vs 'Enloe Homecare' — "
        "different services = different operational units).\n\n"
        "Group each employer into a numbered group; employers in the "
        "same group are the same entity. Singletons are fine.\n\n"
        "EMPLOYERS:\n"
        + "\n\n".join(lines)
        + "\n\nReturn JSON only:\n"
        '{"groups": [[<index>, <index>, ...], [<index>, ...], ...]}'
        "\nEvery employer index must appear in exactly one group."
    )


def _dedup_schema(n: int) -> dict:
    return {
        "type": "OBJECT",
        "properties": {
            "groups": {
                "type": "ARRAY",
                "items": {
                    "type": "ARRAY",
                    "items": {"type": "INTEGER"},
                },
            },
        },
        "required": ["groups"],
    }


async def _call_dedup(client, types, employers: list[dict]) -> list[list[int]] | None:
    """Send one cluster to the LLM. Returns groups (each a list of
    employer indices), or None on failure."""
    n = len(employers)
    prompt = _build_dedup_prompt(employers)
    schema = _dedup_schema(n)
    config = types.GenerateContentConfig(
        response_mime_type="application/json",
        response_schema=schema,
        temperature=0.0,
    )
    for attempt in (1, 2):
        try:
            r = await client.aio.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=config,
            )
            break
        except Exception as e:
            err = str(e).lower()
            if any(t in err for t in ("503", "429", "rate", "unavailable")) and attempt == 1:
                logger.info(f"  transient, retry: {e}")
                await asyncio.sleep(20)
                continue
            logger.error(f"  dedup call failed: {e}")
            return None
    try:
        parsed = json.loads(r.text)
    except json.JSONDecodeError:
        return None
    groups = parsed.get("groups") or []
    if not isinstance(groups, list):
        return None
    # Validate groups: every index 0..n-1 appears exactly once
    seen = set()
    for g in groups:
        if not isinstance(g, list):
            return None
        for i in g:
            if not isinstance(i, int) or i < 0 or i >= n or i in seen:
                return None
            seen.add(i)
    if len(seen) != n:
        return None
    return groups


# ── Merge logic ─────────────────────────────────────────────────────────


def _merge_records(records: list[dict]) -> dict:
    """Merge a group of duplicate records into one. Prefers richer
    fields where possible."""
    # Name: longer is usually more canonical
    chosen = max(records, key=lambda r: len(r["name"]))
    out = dict(chosen)

    # Description: prefer longer/richer; default to chosen's
    descriptions = [r.get("description", "") for r in records if r.get("description")]
    if descriptions:
        out["description"] = max(descriptions, key=len)

    # Regions: union (preserve order)
    seen_regions: set[str] = set()
    out_regions: list[str] = []
    for r in records:
        for region in r.get("regions", []) or []:
            if region not in seen_regions:
                seen_regions.add(region)
                out_regions.append(region)
    out["regions"] = out_regions

    # Occupations: union, cap at _OCC_MAX
    seen_occs: set[str] = set()
    out_occs: list[str] = []
    for r in records:
        for soc in r.get("occupations", []) or []:
            if soc not in seen_occs:
                seen_occs.add(soc)
                out_occs.append(soc)
    out["occupations"] = out_occs[:_OCC_MAX]

    # swp_sectors: dominant value
    sector_counts: Counter = Counter()
    for r in records:
        for s in r.get("swp_sectors", []) or []:
            sector_counts[s] += 1
    if sector_counts:
        out["swp_sectors"] = [sector_counts.most_common(1)[0][0]]

    # Boolean flags: AND-merge (require all sources to be True)
    for flag in ("identity_verified", "enrichment_promoted"):
        if all(r.get(flag) is True for r in records):
            out[flag] = True
        else:
            out.pop(flag, None)

    # OR-merge enrichment_attempted (any source attempted means the merged record was attempted)
    out["enrichment_attempted"] = any(r.get("enrichment_attempted") for r in records)

    return out


def _log_merge(group: list[dict], merged: dict, dry_run: bool) -> None:
    if dry_run:
        return
    entry = {
        "merged_into": merged["name"],
        "absorbed": [r["name"] for r in group if r["name"] != merged["name"]],
        "website": merged.get("website"),
        "merged_regions": merged["regions"],
        "merged_occupations": merged["occupations"],
        "merged_at": _now_iso(),
    }
    with open(MERGES_LOG, "a") as f:
        f.write(json.dumps(entry) + "\n")


# ── Orchestration ───────────────────────────────────────────────────────


async def dedup(region: str | None, dry_run: bool) -> dict:
    with open(EMPLOYERS_PATH) as f:
        employers = json.load(f)

    clusters = _build_clusters(employers, region=region)
    logger.info(f"Found {len(clusters)} same-website clusters with 2+ members"
                + (f" (region={region})" if region else ""))

    if not clusters:
        return {"clusters": 0, "merges": 0, "absorbed": 0}

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY not set")
    from google import genai
    from google.genai import types
    client = genai.Client(api_key=api_key)

    merges_count = 0
    absorbed_count = 0
    name_to_replacement: dict[str, dict] = {}
    drop_names: set[str] = set()

    for url, cluster in clusters.items():
        groups = await _call_dedup(client, types, cluster)
        if groups is None:
            logger.warning(f"  {url}: dedup call failed; leaving cluster as-is")
            continue
        for group_indices in groups:
            if len(group_indices) <= 1:
                continue
            group_records = [cluster[i] for i in group_indices]
            merged = _merge_records(group_records)
            kept_name = merged["name"]
            for r in group_records:
                if r["name"] == kept_name:
                    name_to_replacement[r["name"]] = merged
                else:
                    drop_names.add(r["name"])
            merges_count += 1
            absorbed_count += len(group_records) - 1
            _log_merge(group_records, merged, dry_run)
            logger.info(
                f"  {url}: merged {len(group_records)} → 1 "
                f"({kept_name!r} ← {[r['name'] for r in group_records if r['name'] != kept_name]})"
            )

    # Apply changes: drop absorbed records, replace kept records with merged versions
    if not dry_run:
        new_employers: list[dict] = []
        for e in employers:
            if e["name"] in drop_names:
                continue
            if e["name"] in name_to_replacement:
                new_employers.append(name_to_replacement[e["name"]])
            else:
                new_employers.append(e)
        with open(EMPLOYERS_PATH, "w") as f:
            json.dump(new_employers, f, indent=2)
        logger.info(f"Wrote {len(new_employers)} employers (was {len(employers)})")

    return {
        "clusters": len(clusters),
        "merges": merges_count,
        "absorbed": absorbed_count,
        "kept": sum(1 for c in clusters.values() for _ in c) - absorbed_count - merges_count if merges_count else 0,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Deduplicate employer records by same-website clustering + LLM judgment."
    )
    parser.add_argument("--region", type=str, default=None,
                        help="Limit dedup to clusters where at least one record is in this region")
    parser.add_argument("--dry-run", action="store_true",
                        help="Report findings without writing employers.json or merges.jsonl")
    args = parser.parse_args()

    try:
        from dotenv import load_dotenv
        env_path = Path(__file__).resolve().parent.parent.parent / ".env"
        load_dotenv(env_path)
    except ImportError:
        pass

    logging.basicConfig(level=logging.INFO, format="%(message)s")
    stats = asyncio.run(dedup(region=args.region, dry_run=args.dry_run))

    print("=" * 60)
    print("DEDUP COMPLETE" + (" (dry run)" if args.dry_run else ""))
    print("=" * 60)
    for k, v in stats.items():
        print(f"  {k:12s}  {v}")


if __name__ == "__main__":
    main()
