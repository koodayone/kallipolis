"""Denominator analysis: how many SOCs at each layer of the ontology,
broken down by education band, with served counts under each method.
"""

from __future__ import annotations

import csv
import os
from collections import defaultdict

from neo4j import GraphDatabase

from ontology.crosswalks import (
    COE_DEMAND_PATH,
    _load_cip_to_soc,
    _load_top_to_cip,
)
from ontology.oes import oes_socs_for_naics4

COLLEGE = "Foothill College"


def _load_education() -> dict[str, str]:
    edu: dict[str, str] = {}
    with open(COE_DEMAND_PATH, newline="") as f:
        for row in csv.DictReader(f):
            if row["SOC"] and row.get("Typical Entry Level Education"):
                edu.setdefault(row["SOC"], row["Typical Entry Level Education"].strip())
    return edu


def _band(level: str) -> str:
    if level in {"Postsecondary nondegree award", "Associate's degree"}: return "Strong CTE"
    if level in {"High school diploma or equivalent", "Some college, no degree",
                 "No formal educational credential"}: return "Moderate CTE"
    if level == "Bachelor's degree": return "Bachelor's"
    if level in {"Master's degree", "Doctoral or professional degree"}: return "Master's+"
    return "Unknown"


def main() -> None:
    edu_by_soc = _load_education()

    # Universe 1: every SOC reachable via TOP6→CIP→SOC chain (system-wide).
    top_cip = _load_top_to_cip()
    cip_soc = _load_cip_to_soc()
    universe_soc: set[str] = set()
    for top6, cips in top_cip.items():
        for cip in cips:
            universe_soc.update(cip_soc.get(cip, set()))

    driver = GraphDatabase.driver(
        os.environ["NEO4J_URI"],
        auth=(os.environ["NEO4J_USERNAME"], os.environ["NEO4J_PASSWORD"]),
    )
    with driver.session() as session:
        # Universe 2: Occupation nodes in graph (graph after CTE filter).
        graph_socs = {r["soc"] for r in session.run(
            "MATCH (o:Occupation) RETURN o.soc_code AS soc"
        ).data()}
        # Universe 3: Foothill's supported SOCs.
        supported = session.run(
            """
            MATCH (c:Course {college: $col})-[:PREPARES_FOR]->(occ:Occupation)
            RETURN DISTINCT occ.soc_code AS soc, occ.title AS title
            """, col=COLLEGE,
        ).data()
        supported_socs = {r["soc"] for r in supported}

        region = session.run(
            "MATCH (c:College {name: $n})-[:IN_MARKET]->(r:Region) RETURN r.name AS n",
            n=COLLEGE,
        ).single()["n"]

        # Employers, with their LLM-curated SOCs.
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

    # Per-method served set across thresholds.
    counts_at: dict[float, dict[str, int]] = {t: defaultdict(int) for t in [0.0, 0.5, 1.0, 2.0, 5.0]}
    counts_llm: dict[str, int] = defaultdict(int)
    for emp in emps:
        oes = oes_socs_for_naics4(emp["naics4"])
        for r in oes:
            soc = r["soc"]
            if soc not in supported_socs:
                continue
            pct = r.get("pct_total") or 0.0
            for t in counts_at:
                if pct >= t:
                    counts_at[t][soc] += 1
        for soc in emp["llm"]:
            if soc in supported_socs:
                counts_llm[soc] += 1

    # Per-band rollup.
    bands = ["Strong CTE", "Moderate CTE", "Bachelor's", "Master's+", "Unknown"]
    band_supported: dict[str, list[str]] = defaultdict(list)
    for soc in supported_socs:
        band_supported[_band(edu_by_soc.get(soc, ""))].append(soc)

    print(f"## Denominators\n")
    print(f"| Layer | Count |")
    print(f"|---|---:|")
    print(f"| All SOCs reachable via TOP→CIP→SOC (CCC system universe) | {len(universe_soc)} |")
    print(f"| Occupation nodes in graph (after CTE filter) | {len(graph_socs)} |")
    print(f"| Foothill supported SOCs (curriculum reaches them) | {len(supported_socs)} |")
    print()

    print(f"## Foothill supported SOCs by education band\n")
    print(f"| Band | SOCs | Pct of supported |")
    print(f"|---|---:|---:|")
    for b in bands:
        n = len(band_supported.get(b, []))
        if n:
            print(f"| {b} | {n} | {100*n/len(supported_socs):.1f}% |")
    direct_cte = len(band_supported["Strong CTE"]) + len(band_supported["Moderate CTE"])
    print(f"| **Direct-CTE total (Strong + Moderate)** | **{direct_cte}** | "
          f"**{100*direct_cte/len(supported_socs):.1f}%** |")
    print()

    print(f"## Served counts per band, per method\n")
    print(f"{'Band':<15} {'Total':>5} {'LLM':>4} {'≥0%':>4} {'≥0.5%':>5} {'≥1%':>4} "
          f"{'≥2%':>4} {'≥5%':>4}")
    print(f"{'─'*50}")
    for b in bands:
        socs = band_supported.get(b, [])
        if not socs: continue
        total = len(socs)
        llm = sum(1 for s in socs if counts_llm[s] > 0)
        n0 = sum(1 for s in socs if counts_at[0.0][s] > 0)
        n05 = sum(1 for s in socs if counts_at[0.5][s] > 0)
        n1 = sum(1 for s in socs if counts_at[1.0][s] > 0)
        n2 = sum(1 for s in socs if counts_at[2.0][s] > 0)
        n5 = sum(1 for s in socs if counts_at[5.0][s] > 0)
        print(f"{b:<15} {total:>5} {llm:>4} {n0:>4} {n05:>5} {n1:>4} {n2:>4} {n5:>4}")
    print(f"{'─'*50}")
    socs = list(supported_socs)
    total = len(socs)
    llm = sum(1 for s in socs if counts_llm[s] > 0)
    n0 = sum(1 for s in socs if counts_at[0.0][s] > 0)
    n05 = sum(1 for s in socs if counts_at[0.5][s] > 0)
    n1 = sum(1 for s in socs if counts_at[1.0][s] > 0)
    n2 = sum(1 for s in socs if counts_at[2.0][s] > 0)
    n5 = sum(1 for s in socs if counts_at[5.0][s] > 0)
    print(f"{'TOTAL':<15} {total:>5} {llm:>4} {n0:>4} {n05:>5} {n1:>4} {n2:>4} {n5:>4}")
    print()

    # Distribution shape per band at 0%, 1%, LLM
    print(f"## Per-SOC list size — Strong CTE band only\n")
    print(f"For each Strong CTE SOC, how big is the candidate list under each method?\n")
    print(f"{'Method':<10} {'0 emp':>5} {'1-5':>5} {'6-15':>5} {'16-50':>5} "
          f"{'51-100':>6} {'100+':>5}")
    print(f"{'─'*55}")
    for label, getter in [
        ("LLM", lambda s: counts_llm[s]),
        ("≥0%", lambda s: counts_at[0.0][s]),
        ("≥1%", lambda s: counts_at[1.0][s]),
    ]:
        b = {"0": 0, "1-5": 0, "6-15": 0, "16-50": 0, "51-100": 0, "100+": 0}
        for s in band_supported["Strong CTE"]:
            n = getter(s)
            if n == 0: b["0"] += 1
            elif n <= 5: b["1-5"] += 1
            elif n <= 15: b["6-15"] += 1
            elif n <= 50: b["16-50"] += 1
            elif n <= 100: b["51-100"] += 1
            else: b["100+"] += 1
        print(f"{label:<10} {b['0']:>5} {b['1-5']:>5} {b['6-15']:>5} {b['16-50']:>5} "
              f"{b['51-100']:>6} {b['100+']:>5}")


if __name__ == "__main__":
    main()
