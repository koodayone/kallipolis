"""Audit the NAICS-4 → SWP sector classification using pct_total.

For each NAICS-4 in the OEWS matrix, build the workforce profile —
which SOCs it employs and at what pct_total. Map each SOC to its
SWP sector (via TOP6→CIP→SOC). Aggregate pct_total per sector.
The dominant sector is the pct_total-weighted prediction.

Compare against the current assignment for NAICS in our pool.
For NAICS not in our pool, surface candidates that strongly predict
a SWP sector → potential expansion targets.
"""

from __future__ import annotations

import os
from collections import Counter, defaultdict
from pathlib import Path

from neo4j import GraphDatabase

from ontology.crosswalks import (
    _load_cip_to_soc, _load_pcah_cte_top6, _load_top_to_cip,
)
from ontology import oes as _oes
from ontology.oes import oes_socs_for_naics4


def _classify_soc_sector() -> dict[str, list[str]]:
    """SOC → list of plurality-winning SWP sectors via TOP6→CIP→SOC."""
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
        if not votes: continue
        top_v = max(votes.values())
        out[soc] = sorted([s for s, v in votes.items() if v == top_v])
    return out


def main(out_path: str) -> None:
    soc_to_sector = _classify_soc_sector()
    _oes._ensure_loaded()

    # Universe of NAICS-4 in the OEWS matrix.
    all_naics = set(_oes._socs_by_naics4.keys())

    driver = GraphDatabase.driver(
        os.environ["NEO4J_URI"],
        auth=(os.environ["NEO4J_USERNAME"], os.environ["NEO4J_PASSWORD"]),
    )
    with driver.session() as session:
        # Current NAICS in our pool with their declared SWP sectors.
        rows = session.run(
            """
            MATCH (e:Employer)
            WHERE e.naics4 IS NOT NULL
            RETURN e.naics4 AS naics4, e.swp_sectors AS sectors,
                   count(e) AS n_employers
            """
        ).data()
    driver.close()

    pool_naics: dict[str, dict] = {}
    for r in rows:
        n = r["naics4"]
        if n not in pool_naics:
            pool_naics[n] = {"sectors": set(), "n_employers": 0}
        pool_naics[n]["sectors"].update(r["sectors"] or [])
        pool_naics[n]["n_employers"] += r["n_employers"]

    # Per NAICS, compute pct_total-weighted SWP sector profile.
    def predict_sectors(naics4: str) -> tuple[list[tuple[str, float]], float]:
        rows = oes_socs_for_naics4(naics4)
        sector_weight: Counter = Counter()
        total_weighted = 0.0
        for r in rows:
            soc = r["soc"]
            pct = r.get("pct_total") or 0.0
            sectors = soc_to_sector.get(soc, [])
            if not sectors: continue
            # Distribute pct evenly across tied sectors.
            share = pct / len(sectors)
            for s in sectors:
                sector_weight[s] += share
            total_weighted += pct
        ranked = sector_weight.most_common()
        return ranked, total_weighted

    # ── Question 1: pool NAICS — does prediction match assignment? ───
    pool_results: list[dict] = []
    for naics, info in pool_naics.items():
        ranked, total = predict_sectors(naics)
        if not ranked:
            continue
        top_sector, top_w = ranked[0]
        share = top_w / total if total else 0
        assigned = info["sectors"]
        match = top_sector in assigned
        pool_results.append({
            "naics": naics,
            "n_employers": info["n_employers"],
            "assigned": assigned,
            "predicted": top_sector,
            "predicted_share": share,
            "ranked": ranked[:3],
            "match": match,
        })

    matched = sum(1 for r in pool_results if r["match"])
    total = len(pool_results)

    # ── Question 2: non-pool NAICS — predicted dominant sector ───────
    non_pool = []
    for naics in all_naics - set(pool_naics.keys()):
        ranked, total_w = predict_sectors(naics)
        if not ranked: continue
        top_sector, top_w = ranked[0]
        share = top_w / total_w if total_w else 0
        if share >= 0.5:  # >=50% of CTE-classified pct_total goes to one sector
            non_pool.append({
                "naics": naics,
                "predicted": top_sector,
                "predicted_share": share,
                "total_cte_weight": total_w,
                "ranked": ranked[:3],
            })

    out: list[str] = []
    out.append("# NAICS-4 → SWP Sector Rationality Audit\n\n")
    out.append(
        "Compares the SWP sector currently assigned to each NAICS-4 in the "
        "employer pool against the pct_total-weighted prediction from the "
        "BLS Industry-Occupation Matrix. Per NAICS-4, the predicted sector "
        "is the SWP sector that captures the most pct_total mass when "
        "each SOC's pct_total is allocated to its CCC-system-classified "
        "SWP sector (via the TOP6 → CIP → SOC chain).\n\n"
    )

    out.append("## Pool rationality\n\n")
    out.append(f"- NAICS-4 codes in pool: **{len(pool_naics)}** "
               f"({sum(p['n_employers'] for p in pool_naics.values())} total employers)\n")
    out.append(f"- Predictable (have ≥1 CTE-classified SOC): **{total}**\n")
    out.append(f"- Predicted-sector matches assigned-sector: **{matched}** "
               f"({100*matched/total:.1f}%)\n")
    out.append(f"- Mismatches: **{total - matched}** "
               f"({100*(total-matched)/total:.1f}%)\n\n")

    out.append("## NAICS where prediction matches assignment "
               f"({matched})\n\n")
    out.append("| NAICS-4 | Employers | Assigned | Predicted | "
               "Predicted share | Top 3 predicted sectors |\n"
               "|---|---:|---|---|---:|---|\n")
    matches = sorted(
        [r for r in pool_results if r["match"]],
        key=lambda r: -r["n_employers"]
    )
    for r in matches:
        ranked_s = "; ".join(f"{s} ({100*w/sum(x[1] for x in r['ranked']):.0f}%)"
                              for s, w in r["ranked"])
        out.append(f"| `{r['naics']}` | {r['n_employers']} | "
                   f"{', '.join(sorted(r['assigned'])) or '(none)'} | "
                   f"{r['predicted']} | {100*r['predicted_share']:.0f}% | "
                   f"{ranked_s} |\n")

    out.append(f"\n## NAICS where prediction disagrees with assignment "
               f"({total - matched})\n\n")
    out.append(
        "Cases where the pct_total-weighted dominant sector for the NAICS "
        "differs from its currently assigned SWP sector. Each is worth a "
        "human read — most are defensibly cross-cutting industries that "
        "could be classified either way; some may be true mis-classifications.\n\n"
    )
    out.append("| NAICS-4 | Employers | Assigned | Predicted | "
               "Predicted share | Top 3 predicted sectors |\n"
               "|---|---:|---|---|---:|---|\n")
    misses = sorted(
        [r for r in pool_results if not r["match"]],
        key=lambda r: -r["n_employers"]
    )
    for r in misses:
        ranked_s = "; ".join(f"{s} ({100*w/sum(x[1] for x in r['ranked']):.0f}%)"
                              for s, w in r["ranked"])
        out.append(f"| `{r['naics']}` | {r['n_employers']} | "
                   f"{', '.join(sorted(r['assigned'])) or '(none)'} | "
                   f"{r['predicted']} | {100*r['predicted_share']:.0f}% | "
                   f"{ranked_s} |\n")

    out.append(f"\n## NAICS not in pool with strong SWP-sector prediction "
               f"({len(non_pool)})\n\n")
    out.append(
        "NAICS-4 codes outside our employer scrape whose pct_total profile "
        "concentrates ≥50% in a single SWP sector. These are expansion "
        "candidates — adding employers in these NAICS would meaningfully "
        "extend the report's coverage for the predicted sector.\n\n"
    )
    out.append("| NAICS-4 | Predicted | Predicted share | Total CTE weight | "
               "Top 3 sectors |\n|---|---|---:|---:|---|\n")
    non_pool.sort(key=lambda r: -r["total_cte_weight"])
    for r in non_pool[:60]:
        ranked_s = "; ".join(f"{s} ({100*w/sum(x[1] for x in r['ranked']):.0f}%)"
                              for s, w in r["ranked"])
        out.append(f"| `{r['naics']}` | {r['predicted']} | "
                   f"{100*r['predicted_share']:.0f}% | "
                   f"{r['total_cte_weight']:.1f}% | {ranked_s} |\n")

    Path(out_path).write_text("".join(out))
    print(f"Wrote {out_path}")
    print(f"Pool NAICS: {len(pool_naics)}, predictable: {total}, "
          f"matches: {matched} ({100*matched/total:.1f}%), "
          f"mismatches: {total-matched}")
    print(f"Non-pool NAICS with strong sector prediction: {len(non_pool)}")


if __name__ == "__main__":
    main("/app/naics_classification_audit.md")
