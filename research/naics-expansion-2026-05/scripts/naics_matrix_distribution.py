"""NAICS-matrix-based occupation-employer linkage for one college.

Computes, per Occupation, how many regional employers WOULD hire for it
under an OEWS NAICS-4 → SOC association (rather than the LLM-curated
~5-SOC-per-employer rule that drives PREPARES_FOR today).

Scope rules:
  1. Restrict to the SOC set the college can prepare students for —
     the distinct SOCs reached by any PREPARES_FOR edge from a Course
     at this college (i.e., curriculum-supported SOCs).
  2. Restrict to employers in the college's regional pool
     (Employer-[:IN_MARKET]->Region<-[:IN_MARKET]-College).
  3. For each employer, pull the OEWS SOC set via its NAICS-4.
  4. Per supported SOC, count distinct employers whose OEWS set
     contains it.

Side-by-side with the current LLM-curated count for comparison.
"""

from __future__ import annotations

import os
import sys
from collections import Counter

from neo4j import GraphDatabase

from ontology.oes import oes_socs_for_naics4

COLLEGE = sys.argv[1] if len(sys.argv) > 1 else "Foothill College"


def main() -> None:
    driver = GraphDatabase.driver(
        os.environ["NEO4J_URI"],
        auth=(os.environ["NEO4J_USERNAME"], os.environ["NEO4J_PASSWORD"]),
    )
    with driver.session() as session:
        region = session.run(
            "MATCH (c:College {name: $n})-[:IN_MARKET]->(r:Region) "
            "RETURN r.name AS name",
            n=COLLEGE,
        ).single()["name"]

        # Curriculum-supported SOCs: distinct SOC reached by any
        # PREPARES_FOR edge from a Course at this college.
        supported = session.run(
            """
            MATCH (c:Course {college: $col})-[:PREPARES_FOR]->(occ:Occupation)
            RETURN DISTINCT occ.soc_code AS soc, occ.title AS title
            """,
            col=COLLEGE,
        ).data()
        supported_socs = {r["soc"] for r in supported}
        soc_titles = {r["soc"]: r["title"] for r in supported}

        # Regional employers + NAICS-4.
        employers = session.run(
            """
            MATCH (e:Employer)-[:IN_MARKET]->(r:Region {name: $r})
            WHERE e.naics4 IS NOT NULL
            RETURN e.name AS name, e.naics4 AS naics4
            """,
            r=region,
        ).data()

        # LLM-curated comparator: current HIRES_FOR for the same
        # college's regional employer pool.
        curated_rows = session.run(
            """
            MATCH (e:Employer)-[:IN_MARKET]->(:Region {name: $r})
            MATCH (e)-[:HIRES_FOR]->(occ:Occupation)
            WHERE occ.soc_code IN $supported
            RETURN occ.soc_code AS soc, count(DISTINCT e) AS n
            """,
            r=region,
            supported=list(supported_socs),
        ).data()
    driver.close()

    print(f"College: {COLLEGE}")
    print(f"Region:  {region}")
    print(f"Curriculum-supported SOCs: {len(supported_socs)}")
    print(f"Regional employers (with NAICS-4): {len(employers)}")
    print()

    # NAICS-matrix tally.
    naics_counts: Counter = Counter()
    employer_soc_breadth: list[int] = []
    n_no_oes_match = 0
    for emp in employers:
        socs = oes_socs_for_naics4(emp["naics4"])
        if not socs:
            n_no_oes_match += 1
            continue
        hire_set = {r["soc"] for r in socs} & supported_socs
        employer_soc_breadth.append(len(hire_set))
        for soc in hire_set:
            naics_counts[soc] += 1

    print(f"Employers with no OEWS reach into supported SOCs: {n_no_oes_match}")
    print(f"Median supported-SOCs reached per employer (NAICS-matrix): "
          f"{sorted(employer_soc_breadth)[len(employer_soc_breadth)//2]}")
    print(f"Mean supported-SOCs reached per employer: "
          f"{sum(employer_soc_breadth)/max(1, len(employer_soc_breadth)):.1f}")
    print()

    curated_counts = {r["soc"]: r["n"] for r in curated_rows}

    # Distribution buckets (NAICS-matrix view).
    buckets = Counter()
    for soc in supported_socs:
        n = naics_counts.get(soc, 0)
        if n == 0:
            buckets["0"] += 1
        elif n <= 5:
            buckets["1-5"] += 1
        elif n <= 20:
            buckets["6-20"] += 1
        elif n <= 50:
            buckets["21-50"] += 1
        elif n <= 100:
            buckets["51-100"] += 1
        else:
            buckets["100+"] += 1

    print("Per-occupation employer count (NAICS-matrix view):")
    print(f"{'Bucket':>10} {'SOCs':>6} {'Pct':>7}")
    total = len(supported_socs)
    for k in ["0", "1-5", "6-20", "21-50", "51-100", "100+"]:
        n = buckets[k]
        print(f"{k:>10} {n:>6} {100*n/total:>6.1f}%")

    served_naics = sum(1 for s in supported_socs if naics_counts.get(s, 0) > 0)
    served_curated = sum(1 for s in supported_socs if curated_counts.get(s, 0) > 0)
    print()
    print(f"Served (≥1 employer):")
    print(f"  NAICS-matrix:  {served_naics}/{total} ({100*served_naics/total:.1f}%)")
    print(f"  LLM-curated:   {served_curated}/{total} ({100*served_curated/total:.1f}%)")

    # Side-by-side top-15.
    print()
    print(f"{'SOC':<10} {'Title':<55} {'NAICS':>6} {'LLM':>5} {'×':>5}")
    ranked = sorted(supported_socs, key=lambda s: -naics_counts.get(s, 0))
    for soc in ranked[:20]:
        n_naics = naics_counts.get(soc, 0)
        n_llm = curated_counts.get(soc, 0)
        ratio = n_naics / n_llm if n_llm else float('inf') if n_naics else 0
        ratio_s = f"{ratio:.1f}" if ratio != float('inf') else "—"
        title = (soc_titles.get(soc) or "")[:55]
        print(f"{soc:<10} {title:<55} {n_naics:>6} {n_llm:>5} {ratio_s:>5}")

    # Bottom: SOCs with no NAICS coverage at all.
    zero_naics = [s for s in supported_socs if naics_counts.get(s, 0) == 0]
    print()
    print(f"\nSOCs with 0 NAICS-matrix employers ({len(zero_naics)}):")
    for soc in sorted(zero_naics)[:25]:
        print(f"  {soc}  {soc_titles.get(soc, '')[:60]}")


if __name__ == "__main__":
    main()
