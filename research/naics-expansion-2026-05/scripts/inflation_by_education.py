"""Inflation profile of NAICS-matrix vs LLM-curated employer counts,
sliced by COE 'typical entry-level education' for each SOC.

If the user's claim holds — "generic cross-industry SOCs are weak CTE
candidates" — high-inflation SOCs should cluster at Bachelor's+ entry,
with the strongest CTE-pathway education levels (postsecondary
nondegree award, associate's, HS + on-the-job) showing low or
moderate inflation.
"""

from __future__ import annotations

import csv
import os
import sys
from collections import Counter, defaultdict
from pathlib import Path

from neo4j import GraphDatabase

from ontology.crosswalks import COE_DEMAND_PATH
from ontology.oes import oes_socs_for_naics4

COLLEGE = sys.argv[1] if len(sys.argv) > 1 else "Foothill College"

# COE region for each loaded college (matches COE_REGION_DISPLAY codes
# in regions.py). Picked from College.region property and the
# region-code mapping in the graph.
COE_REGION_FOR = {
    "Foothill College": "Bay",
    "Compton College": "LA",
    "San Diego City College": "SD/I",
    "College of the Sequoias": "CVML",
    "College of the Desert": "IE/D",
    "Oxnard College": "SCC",
    "Shasta College": "FN",
    "Irvine Valley College": "OC",
}


def _load_education_for_socs() -> dict[str, str]:
    """Pull typical entry-level education per SOC from the COE demand file.
    The CSV has one row per (region, SOC); education is constant per SOC."""
    edu: dict[str, str] = {}
    with open(COE_DEMAND_PATH, newline="") as f:
        for row in csv.DictReader(f):
            soc = row["SOC"]
            level = row.get("Typical Entry Level Education", "").strip()
            if soc and level:
                edu.setdefault(soc, level)
    return edu


def _bucket_education(level: str) -> str:
    """Coarse-grain to four CTE-relevance bands."""
    cte_strong = {
        "Postsecondary nondegree award",
        "Associate's degree",
    }
    cte_moderate = {
        "High school diploma or equivalent",
        "Some college, no degree",
        "No formal educational credential",
    }
    cte_weak = {
        "Bachelor's degree",
    }
    cte_minimal = {
        "Master's degree",
        "Doctoral or professional degree",
    }
    if level in cte_strong:
        return "Strong CTE (postsecondary award / associate's)"
    if level in cte_moderate:
        return "Moderate CTE (HS / some college / none)"
    if level in cte_weak:
        return "Weak CTE (bachelor's-entry)"
    if level in cte_minimal:
        return "Minimal CTE (master's+)"
    return "Unknown / not in COE"


def main() -> None:
    edu_by_soc = _load_education_for_socs()

    driver = GraphDatabase.driver(
        os.environ["NEO4J_URI"],
        auth=(os.environ["NEO4J_USERNAME"], os.environ["NEO4J_PASSWORD"]),
    )
    with driver.session() as session:
        region = session.run(
            "MATCH (c:College {name: $n})-[:IN_MARKET]->(r:Region) "
            "RETURN r.name AS name", n=COLLEGE,
        ).single()["name"]

        supported = session.run(
            """
            MATCH (c:Course {college: $col})-[:PREPARES_FOR]->(occ:Occupation)
            RETURN DISTINCT occ.soc_code AS soc, occ.title AS title
            """, col=COLLEGE,
        ).data()
        supported_socs = {r["soc"]: r["title"] for r in supported}

        employers = session.run(
            """
            MATCH (e:Employer)-[:IN_MARKET]->(:Region {name: $r})
            WHERE e.naics4 IS NOT NULL
            RETURN e.name AS name, e.naics4 AS naics4
            """, r=region,
        ).data()

        curated = session.run(
            """
            MATCH (e:Employer)-[:IN_MARKET]->(:Region {name: $r})
            MATCH (e)-[:HIRES_FOR]->(occ:Occupation)
            WHERE occ.soc_code IN $supported
            RETURN occ.soc_code AS soc, count(DISTINCT e) AS n
            """, r=region, supported=list(supported_socs),
        ).data()
    driver.close()

    naics_counts: Counter = Counter()
    for emp in employers:
        socs = oes_socs_for_naics4(emp["naics4"])
        if not socs:
            continue
        for r in socs:
            if r["soc"] in supported_socs:
                naics_counts[r["soc"]] += 1

    curated_counts = {r["soc"]: r["n"] for r in curated}

    print(f"College: {COLLEGE}")
    print(f"Region:  {region}")
    print(f"Supported SOCs: {len(supported_socs)}")
    print(f"Regional employers: {len(employers)}")
    print()

    # Bucket every supported SOC by education band, and within each band
    # report the inflation profile.
    by_band: dict[str, list[dict]] = defaultdict(list)
    for soc, title in supported_socs.items():
        edu = edu_by_soc.get(soc, "")
        band = _bucket_education(edu)
        n_naics = naics_counts.get(soc, 0)
        n_llm = curated_counts.get(soc, 0)
        by_band[band].append({
            "soc": soc, "title": title, "edu": edu,
            "naics": n_naics, "llm": n_llm,
        })

    band_order = [
        "Strong CTE (postsecondary award / associate's)",
        "Moderate CTE (HS / some college / none)",
        "Weak CTE (bachelor's-entry)",
        "Minimal CTE (master's+)",
        "Unknown / not in COE",
    ]
    print(f"{'Education band':<55} {'SOCs':>5} {'Med NAICS':>10} {'Med LLM':>8} {'Med ratio':>10}")
    print("-" * 92)
    for band in band_order:
        recs = by_band.get(band, [])
        if not recs:
            continue
        naics_vals = sorted([r["naics"] for r in recs])
        llm_vals = sorted([r["llm"] for r in recs])
        med_n = naics_vals[len(naics_vals)//2]
        med_l = llm_vals[len(llm_vals)//2]
        ratios = []
        for r in recs:
            if r["llm"] > 0:
                ratios.append(r["naics"] / r["llm"])
        ratios.sort()
        med_r = f"{ratios[len(ratios)//2]:.1f}" if ratios else "—"
        print(f"{band:<55} {len(recs):>5} {med_n:>10} {med_l:>8} {med_r:>10}")

    # Top-inflated SOCs in each band — does the user's claim hold?
    print()
    for band in band_order:
        recs = by_band.get(band, [])
        if not recs:
            continue
        recs.sort(key=lambda r: -r["naics"])
        print(f"\n── {band}  ({len(recs)} SOCs)")
        print(f"  Top 10 by NAICS-matrix count:")
        for r in recs[:10]:
            ratio = (r["naics"] / r["llm"]) if r["llm"] > 0 else float("inf")
            ratio_s = f"{ratio:>5.1f}×" if ratio != float("inf") else "    —"
            print(f"    NAICS={r['naics']:>3} LLM={r['llm']:>3} {ratio_s}  "
                  f"{r['soc']}  {r['title'][:55]}")


if __name__ == "__main__":
    main()
