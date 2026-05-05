"""For sample SOCs and all Advanced Manufacturing SOCs:
  1. Compute the rank position of each LLM-picked employer in the
     NAICS-sorted full list under the new methodology.
  2. Per Advanced Manufacturing SOC: side-by-side LLM picks vs new
     method top-10, with rank annotations.

Tells us how far down the NAICS-sorted list the LLM identity-relevant
picks appear — i.e., how buried they actually are.
"""

from __future__ import annotations

import csv
import json
import os
from collections import Counter, defaultdict
from pathlib import Path

from neo4j import GraphDatabase

from ontology.crosswalks import (
    COE_DEMAND_PATH, _load_cip_to_soc, _load_pcah_cte_top6, _load_top_to_cip,
)
from ontology import oes as _oes
from ontology.oes import oes_socs_for_naics4

REGIONS = [("SD", "/app/sd_full.json"), ("LA", "/app/la_full.json")]
GRAPH_REGIONS = ["SD/I", "LA"]

# Sample SOCs from prior analysis
PRIOR_SAMPLE = [
    ("49-9021", "HVAC Mechanics"),
    ("47-2111", "Electricians"),
    ("23-2011", "Paralegals"),
    ("49-3023", "Auto Service Techs"),
    ("29-2061", "LVNs"),
    ("13-2011", "Accountants"),
]


def _classify_soc_sector() -> dict[str, list[str]]:
    top6_to_sector = _load_pcah_cte_top6()
    top_cip = _load_top_to_cip()
    cip_soc = _load_cip_to_soc()
    soc_to_tops: dict[str, set[str]] = {}
    for top6, cips in top_cip.items():
        for cip in cips:
            for soc in cip_soc.get(cip, set()):
                soc_to_tops.setdefault(soc, set()).add(top6)
    out: dict[str, list[str]] = {}
    for soc, tops in soc_to_tops.items():
        votes: Counter = Counter()
        for t in tops:
            sector = top6_to_sector.get(t)
            if sector:
                votes[sector] += 1
        if votes:
            top_v = max(votes.values())
            out[soc] = sorted([s for s, v in votes.items() if v == top_v])
    return out


def main(out_path: str) -> None:
    _oes._ensure_loaded()
    soc_to_sectors = _classify_soc_sector()

    region_data: dict[str, dict[str, list[str]]] = {}
    for region, path in REGIONS:
        if Path(path).exists():
            region_data[region] = json.loads(Path(path).read_text())

    driver = GraphDatabase.driver(
        os.environ["NEO4J_URI"],
        auth=(os.environ["NEO4J_USERNAME"], os.environ["NEO4J_PASSWORD"]),
    )
    with driver.session() as session:
        llm_rows = session.run(
            """
            MATCH (e:Employer)-[:IN_MARKET]->(r:Region)
            WHERE r.name IN $regions
            MATCH (e)-[:HIRES_FOR]->(o:Occupation)
            RETURN o.soc_code AS soc, o.title AS title,
                   r.name AS region, e.name AS name, e.naics4 AS naics4
            """, regions=GRAPH_REGIONS,
        ).data()
        all_socs = session.run(
            "MATCH (o:Occupation) RETURN o.soc_code AS soc, o.title AS title"
        ).data()
    driver.close()

    soc_titles = {r["soc"]: r["title"] for r in all_socs}

    llm_per_soc: dict[str, list[dict]] = defaultdict(list)
    for r in llm_rows:
        llm_per_soc[r["soc"]].append({
            "name": r["name"], "region": r["region"], "naics": r["naics4"],
        })

    # New method per-SOC ranked list.
    new_per_soc: dict[str, list[dict]] = defaultdict(list)
    for region, naics_to_emps in region_data.items():
        for naics, employers in naics_to_emps.items():
            if not employers: continue
            for r in oes_socs_for_naics4(naics):
                soc = r["soc"]
                pct = r.get("pct_total") or 0.0
                if pct <= 0: continue
                seen = set()
                for emp in employers:
                    key = emp.lower().strip()
                    if key in seen: continue
                    seen.add(key)
                    new_per_soc[soc].append({
                        "name": emp, "region": region, "naics": naics,
                        "pct_total": pct,
                    })
    for soc in new_per_soc:
        new_per_soc[soc].sort(key=lambda x: -x["pct_total"])

    # For each LLM pick, compute its rank in the new method's list.
    def llm_ranks(soc: str) -> list[dict]:
        ranked = new_per_soc.get(soc, [])
        ranked_keys = [(x["name"].lower().strip(), x) for x in ranked]
        result = []
        for pick in llm_per_soc.get(soc, []):
            key = pick["name"].lower().strip()
            for i, (k, x) in enumerate(ranked_keys, 1):
                if k == key:
                    result.append({
                        "name": pick["name"],
                        "region": pick["region"],
                        "llm_naics": pick["naics"],
                        "rank": i,
                        "pct_at_rank": x["pct_total"],
                    })
                    break
            else:
                # LLM pick not in new pool at all (employer not E+ size or
                # NAICS not scraped).
                result.append({
                    "name": pick["name"],
                    "region": pick["region"],
                    "llm_naics": pick["naics"],
                    "rank": None,
                    "pct_at_rank": 0,
                })
        return result

    out: list[str] = []
    out.append("# LLM Pick Rank Positions in New-Method NAICS-Sorted Lists\n\n")
    out.append(
        "For each LLM-picked employer, its rank position in the new "
        "method's NAICS-sorted full list (by pct_total descending). "
        "Rank=1 means top of list; high ranks mean the LLM pick is "
        "buried deep below the top-pct NAICS. `not in pool` means the "
        "employer didn't surface in the SD+LA E+ scrape (size below E "
        "or in unscraped NAICS).\n\n"
    )

    out.append("## Prior sample SOCs — LLM rank distribution\n\n")
    for soc, label in PRIOR_SAMPLE:
        ranks = llm_ranks(soc)
        if not ranks: continue
        n = len(ranks)
        in_pool = [r for r in ranks if r["rank"] is not None]
        not_in_pool = [r for r in ranks if r["rank"] is None]
        if in_pool:
            ranks_only = sorted([r["rank"] for r in in_pool])
            median = ranks_only[len(ranks_only)//2]
            in_top10 = sum(1 for r in ranks_only if r <= 10)
            in_top30 = sum(1 for r in ranks_only if r <= 30)
            in_top100 = sum(1 for r in ranks_only if r <= 100)
        else:
            median = "—"
            in_top10 = in_top30 = in_top100 = 0
        out.append(f"### `{soc}` {label}\n")
        out.append(f"- LLM picks: {n}\n")
        out.append(f"- In new pool: {len(in_pool)}\n")
        out.append(f"- Not in new pool: {len(not_in_pool)}\n")
        if in_pool:
            out.append(f"- Median rank of LLM picks in new sorted list: **{median}**\n")
            out.append(f"- LLM picks in new top 10: {in_top10}/{len(in_pool)}\n")
            out.append(f"- LLM picks in new top 30: {in_top30}/{len(in_pool)}\n")
            out.append(f"- LLM picks in new top 100: {in_top100}/{len(in_pool)}\n")
        out.append("\nLLM picks with their rank in the new sorted list:\n\n")
        out.append("| Rank | Region | Employer | LLM-NAICS | pct_total |\n"
                   "|---:|:---:|---|---|---:|\n")
        ranks.sort(key=lambda r: (r["rank"] is None, r["rank"] or 0))
        for r in ranks[:25]:
            rank = r["rank"] if r["rank"] else "**not in pool**"
            out.append(f"| {rank} | {r['region']} | {r['name']} | "
                       f"{r['llm_naics']} | {r['pct_at_rank']:.1f}% |\n")
        if len(ranks) > 25:
            out.append(f"\n*... and {len(ranks)-25} more LLM picks*\n")
        out.append("\n")

    # Advanced Manufacturing SOCs
    advmfg_socs = [
        soc for soc, sectors in soc_to_sectors.items()
        if sectors == ["Advanced Manufacturing"]
        and soc in soc_titles
    ]
    advmfg_socs = [s for s in advmfg_socs if new_per_soc.get(s) or llm_per_soc.get(s)]

    out.append(f"\n---\n\n# Advanced Manufacturing SOCs — Side by Side\n\n")
    out.append(
        f"For every Advanced Manufacturing SOC ({len(advmfg_socs)}): "
        f"LLM picks (with ranks in the new sorted list) and the new "
        f"method's top 5.\n\n"
    )

    # Sort by LLM presence then SOC code.
    advmfg_socs.sort(key=lambda s: (-len(llm_per_soc.get(s, [])), s))

    for soc in advmfg_socs:
        title = soc_titles.get(soc, "")
        ranks = llm_ranks(soc)
        new_top = new_per_soc.get(soc, [])[:5]

        out.append(f"\n## `{soc}` {title}\n\n")
        out.append(f"- LLM picks: **{len(ranks)}**\n")
        out.append(f"- New method pool size: **{len(new_per_soc.get(soc, []))}**\n")
        if new_top:
            out.append(f"- Top NAICS: `{new_top[0]['naics']}` "
                       f"at {new_top[0]['pct_total']:.1f}%\n")
        out.append("\n")

        # New method top 5
        out.append("**New method top 5:**\n\n")
        if not new_top:
            out.append("*No employers in new pool.*\n\n")
        else:
            out.append("| Rank | pct_total | NAICS | Region | Employer |\n"
                       "|---:|---:|---|:---:|---|\n")
            for i, e in enumerate(new_top, 1):
                out.append(f"| {i} | {e['pct_total']:.1f}% | {e['naics']} | "
                           f"{e['region']} | {e['name']} |\n")

        # LLM picks with ranks
        if ranks:
            ranks.sort(key=lambda r: (r["rank"] is None, r["rank"] or 0))
            out.append("\n**LLM picks with their ranks in new sorted list:**\n\n")
            out.append("| Rank in new list | Region | Employer | LLM NAICS | pct |\n"
                       "|---:|:---:|---|---|---:|\n")
            for r in ranks[:15]:
                rank = r["rank"] if r["rank"] else "—"
                out.append(f"| {rank} | {r['region']} | {r['name']} | "
                           f"{r['llm_naics']} | {r['pct_at_rank']:.1f}% |\n")
            if len(ranks) > 15:
                out.append(f"\n*... and {len(ranks)-15} more LLM picks*\n")

    Path(out_path).write_text("".join(out))
    print(f"Wrote {out_path}")
    print(f"Advanced Manufacturing SOCs: {len(advmfg_socs)}")


if __name__ == "__main__":
    main("/app/llm_rank_position_and_advmfg.md")
