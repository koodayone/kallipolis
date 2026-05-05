"""Plurality-classify Occupations to SWP sectors via PREPARES_FOR.via_top.

Two votes computed per Occupation:
  - unweighted: one vote per distinct via_top (crosswalk topology)
  - weighted:   one vote per PREPARES_FOR edge (curricular emphasis)

Reports the shape of both distributions: clean single-sector vs ties vs
SOCs with no PREPARES_FOR coverage at all.
"""

from __future__ import annotations

import os
from collections import Counter, defaultdict

from neo4j import GraphDatabase

from ontology.crosswalks import _load_pcah_cte_top6


def main() -> None:
    top6_to_sector = _load_pcah_cte_top6()

    driver = GraphDatabase.driver(
        os.environ["NEO4J_URI"],
        auth=(os.environ["NEO4J_USERNAME"], os.environ["NEO4J_PASSWORD"]),
    )

    with driver.session() as session:
        # Per Occupation, get (via_top, edge_count) breakdown.
        rows = session.run(
            """
            MATCH (occ:Occupation)
            OPTIONAL MATCH (occ)<-[r:PREPARES_FOR]-(:Course)
            WITH occ.soc_code AS soc, occ.title AS title,
                 r.via_top AS via_top, count(r) AS edges
            RETURN soc, title, collect({via_top: via_top, edges: edges}) AS breakdown
            """
        ).data()

    no_coverage: list[tuple[str, str]] = []
    untraceable: list[tuple[str, str, list[str]]] = []  # has via_top, none in PCAH
    unweighted_results: list[dict] = []
    weighted_results: list[dict] = []

    for r in rows:
        soc = r["soc"]
        title = r["title"]
        # Filter out the OPTIONAL MATCH null sentinel.
        breakdown = [b for b in r["breakdown"] if b["via_top"] is not None]

        if not breakdown:
            no_coverage.append((soc, title))
            continue

        # Map each via_top to a sector (skip TOP6 not in PCAH — non-CTE).
        unweighted = Counter()
        weighted = Counter()
        traced_tops: list[str] = []
        for b in breakdown:
            sector = top6_to_sector.get(b["via_top"])
            if sector is None:
                continue
            traced_tops.append(b["via_top"])
            unweighted[sector] += 1
            weighted[sector] += b["edges"]

        if not unweighted:
            tops = [b["via_top"] for b in breakdown]
            untraceable.append((soc, title, tops))
            continue

        unweighted_results.append({
            "soc": soc, "title": title,
            "distribution": dict(unweighted),
            "n_tops": len(traced_tops),
        })
        weighted_results.append({
            "soc": soc, "title": title,
            "distribution": dict(weighted),
            "n_edges": sum(weighted.values()),
        })

    # ── Shape report ──────────────────────────────────────────────────
    def shape(results: list[dict], label: str) -> None:
        single = 0
        tie2 = 0
        tie3plus = 0
        sector_winners: Counter = Counter()
        for r in results:
            d = r["distribution"]
            top_count = max(d.values())
            winners = [s for s, c in d.items() if c == top_count]
            if len(winners) == 1:
                single += 1
                sector_winners[winners[0]] += 1
            elif len(winners) == 2:
                tie2 += 1
            else:
                tie3plus += 1
        total = len(results)
        print(f"\n── {label} ────────────────────────────────────")
        print(f"Total occupations classified: {total}")
        print(f"  Single-sector (clean plurality): {single} ({100*single/total:.1f}%)")
        print(f"  Two-way tie:                     {tie2} ({100*tie2/total:.1f}%)")
        print(f"  Three+ way tie:                  {tie3plus} ({100*tie3plus/total:.1f}%)")
        print(f"\n  Sector distribution among single-winner SOCs:")
        for sector, n in sector_winners.most_common():
            print(f"    {n:>4}  {sector}")

    print(f"Total Occupation nodes:       {len(rows)}")
    print(f"  No PREPARES_FOR coverage:   {len(no_coverage)}")
    print(f"  All via_top non-CTE (PCAH): {len(untraceable)}")

    shape(unweighted_results, "UNWEIGHTED (one vote per distinct via_top)")
    shape(weighted_results,   "WEIGHTED (one vote per PREPARES_FOR edge)")

    # ── Disagreement: unweighted vs weighted ──────────────────────────
    weighted_by_soc = {r["soc"]: r["distribution"] for r in weighted_results}
    unweighted_by_soc = {r["soc"]: r["distribution"] for r in unweighted_results}

    def winner(d: dict) -> str | None:
        if not d:
            return None
        top = max(d.values())
        winners = sorted([s for s, c in d.items() if c == top])
        return "TIE:" + "|".join(winners) if len(winners) > 1 else winners[0]

    disagreements = []
    for soc, uw in unweighted_by_soc.items():
        w = weighted_by_soc.get(soc)
        if w is None:
            continue
        uw_w = winner(uw)
        w_w = winner(w)
        if uw_w != w_w:
            disagreements.append((soc, uw_w, w_w))
    print(f"\n── DISAGREEMENT (unweighted winner ≠ weighted winner) ──")
    print(f"  {len(disagreements)} of {len(unweighted_by_soc)} SOCs disagree")

    # ── Sample inspection ─────────────────────────────────────────────
    print(f"\n── Sample: 10 SOCs with widest sector spread (weighted) ──")
    weighted_results.sort(key=lambda r: -len(r["distribution"]))
    for r in weighted_results[:10]:
        dist = sorted(r["distribution"].items(), key=lambda x: -x[1])
        print(f"  {r['soc']}  {r['title'][:55]}")
        for sector, c in dist:
            print(f"      {c:>5}  {sector}")

    driver.close()


if __name__ == "__main__":
    main()
