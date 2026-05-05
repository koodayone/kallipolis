"""Test whether sorting by pct_total identifies viable partnership candidates.

For each (employer, SOC) pair in Foothill's candidate pool at 0%
threshold, bucket by pct_total tier and compute the LLM-corroboration
rate per tier. If sorting by pct_total is meaningful, corroboration
rate should rise monotonically with pct_total.
"""

from __future__ import annotations

import os
from collections import defaultdict

from neo4j import GraphDatabase

from ontology.oes import oes_socs_for_naics4

COLLEGE = "Foothill College"


def main() -> None:
    driver = GraphDatabase.driver(
        os.environ["NEO4J_URI"],
        auth=(os.environ["NEO4J_USERNAME"], os.environ["NEO4J_PASSWORD"]),
    )
    with driver.session() as session:
        region = session.run(
            "MATCH (c:College {name: $n})-[:IN_MARKET]->(r:Region) RETURN r.name AS n",
            n=COLLEGE,
        ).single()["n"]
        supported = session.run(
            """
            MATCH (c:Course {college: $col})-[:PREPARES_FOR]->(occ:Occupation)
            RETURN DISTINCT occ.soc_code AS soc, occ.title AS title
            """, col=COLLEGE,
        ).data()
        supported_socs = {r["soc"] for r in supported}
        emps = session.run(
            """
            MATCH (e:Employer)-[:IN_MARKET]->(:Region {name: $r})
            WHERE e.naics4 IS NOT NULL
            OPTIONAL MATCH (e)-[:HIRES_FOR]->(o:Occupation)
            RETURN e.name AS name, e.naics4 AS naics4,
                   collect(DISTINCT o.soc_code) AS llm
            """, r=region,
        ).data()
    driver.close()

    # Build all (employer, SOC) candidate pairs at any pct_total > 0,
    # restricted to supported SOCs. For each pair, capture pct_total
    # and LLM-corroboration boolean.
    pairs: list[dict] = []
    for emp in emps:
        llm_set = set(emp["llm"])
        for r in oes_socs_for_naics4(emp["naics4"]):
            if r["soc"] not in supported_socs:
                continue
            pct = r.get("pct_total") or 0.0
            if pct <= 0:
                continue
            pairs.append({
                "employer": emp["name"],
                "soc": r["soc"],
                "naics4": emp["naics4"],
                "pct_total": pct,
                "llm_corr": r["soc"] in llm_set,
            })

    print(f"Total (employer, SOC) candidate pairs at pct_total > 0: {len(pairs)}\n")

    # Tier bands.
    tiers = [
        ("≥10%", 10.0, 1000.0),
        ("5-10%", 5.0, 10.0),
        ("2-5%", 2.0, 5.0),
        ("1-2%", 1.0, 2.0),
        ("0.5-1%", 0.5, 1.0),
        ("0.1-0.5%", 0.1, 0.5),
        ("<0.1%", 0.0, 0.1),
    ]
    print(f"## LLM-corroboration rate by pct_total tier\n")
    print(f"{'Tier':<10} {'Pairs':>7} {'LLM-corr':>9} {'Rate':>7}")
    print("-" * 40)
    for label, lo, hi in tiers:
        sub = [p for p in pairs if lo <= p["pct_total"] < hi]
        n_corr = sum(1 for p in sub if p["llm_corr"])
        rate = n_corr / len(sub) if sub else 0
        print(f"{label:<10} {len(sub):>7} {n_corr:>9} {100*rate:>6.1f}%")
    print()

    # Also: cumulative — does sorting top-N by pct_total recover most LLM picks?
    pairs_sorted = sorted(pairs, key=lambda p: -p["pct_total"])
    total_corr = sum(1 for p in pairs if p["llm_corr"])
    print(f"## Cumulative recovery of LLM-corroborated pairs by sort position\n")
    print(f"Total LLM-corroborated pairs in pool: {total_corr}\n")
    print(f"{'Top-N':>6} {'% of pool':>10} {'Corr in top-N':>15} "
          f"{'% of LLM corr':>14}")
    print("-" * 55)
    for frac in [0.05, 0.10, 0.20, 0.30, 0.50]:
        cutoff = int(len(pairs_sorted) * frac)
        top_n = pairs_sorted[:cutoff]
        n_corr = sum(1 for p in top_n if p["llm_corr"])
        recovery = n_corr / total_corr if total_corr else 0
        print(f"{cutoff:>6} {100*frac:>9.0f}% {n_corr:>15} {100*recovery:>13.1f}%")

    # Per-SOC: does the LLM-corroborated employer rank near the top
    # under pct_total sort? Compute median rank.
    per_soc: dict[str, list[dict]] = defaultdict(list)
    for p in pairs:
        per_soc[p["soc"]].append(p)
    ranks_of_llm: list[float] = []
    for soc, recs in per_soc.items():
        recs.sort(key=lambda p: -p["pct_total"])
        for i, r in enumerate(recs):
            if r["llm_corr"]:
                # Normalized rank: 0 = top, 1 = bottom.
                ranks_of_llm.append(i / max(1, len(recs) - 1))
    if ranks_of_llm:
        ranks_of_llm.sort()
        med = ranks_of_llm[len(ranks_of_llm) // 2]
        q25 = ranks_of_llm[len(ranks_of_llm) // 4]
        q75 = ranks_of_llm[3 * len(ranks_of_llm) // 4]
        print(f"\n## Per-SOC normalized rank of LLM-corroborated pairs\n")
        print(f"(0.0 = top of pct_total sort, 1.0 = bottom)\n")
        print(f"  Median rank:          {med:.3f}")
        print(f"  25th percentile:      {q25:.3f}")
        print(f"  75th percentile:      {q75:.3f}")
        print(f"  Pairs at top decile:  "
              f"{100*sum(1 for r in ranks_of_llm if r <= 0.1)/len(ranks_of_llm):.1f}%")
        print(f"  Pairs at bottom half: "
              f"{100*sum(1 for r in ranks_of_llm if r > 0.5)/len(ranks_of_llm):.1f}%")


if __name__ == "__main__":
    main()
