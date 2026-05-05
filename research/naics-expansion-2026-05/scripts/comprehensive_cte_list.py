"""Comprehensive list of CTE occupations in the ontology, categorized
by CTE-relevance tier.

Tiers:
  1. Direct CTE (Strong + Moderate education bands) — CCC trains the
     credential the employer hires on.
  2. Transfer-track CTE candidate — Bachelor's-entry SOCs with
     substantial regional demand. CCC produces the foundation; the BS
     program completes the credential. CCC is part of the pipeline.
  3. Bachelor's non-CTE — Bachelor's-entry SOCs with low demand or
     unclear CCC pipeline alignment.
  4. Out of CCC scope — Master's+ entry.
"""

from __future__ import annotations

import csv
import os
from collections import defaultdict
from pathlib import Path

from neo4j import GraphDatabase

from ontology.crosswalks import COE_DEMAND_PATH

TRANSFER_TRACK_DEMAND_THRESHOLD = 500  # CA annual openings


def _load_coe_california() -> dict[str, dict]:
    data: dict[str, dict] = {}
    with open(COE_DEMAND_PATH, newline="") as f:
        for row in csv.DictReader(f):
            if row["Region"] != "CA": continue
            soc = row["SOC"]
            try:
                data[soc] = {
                    "annual_openings": int(row["Average Annual Job Openings"]),
                    "growth_rate": float(row["2024 - 2029 % Change"]),
                    "median_wage": int(row["Median Annual Earnings"]),
                    "education": row["Typical Entry Level Education"].strip(),
                }
            except (ValueError, KeyError):
                continue
    return data


def _band(level: str) -> str:
    if level in {"Postsecondary nondegree award", "Associate's degree"}: return "Strong CTE"
    if level in {"High school diploma or equivalent", "Some college, no degree",
                 "No formal educational credential"}: return "Moderate CTE"
    if level == "Bachelor's degree": return "Bachelor's"
    if level in {"Master's degree", "Doctoral or professional degree"}: return "Master's+"
    return "Unknown"


def _tier(band: str, openings: int) -> str:
    if band in ("Strong CTE", "Moderate CTE"): return "1. Direct CTE"
    if band == "Bachelor's":
        if openings >= TRANSFER_TRACK_DEMAND_THRESHOLD:
            return "2. Transfer-track CTE candidate"
        return "3. Bachelor's, low transfer-track signal"
    if band == "Master's+": return "4. Out of CCC scope"
    return "5. Unknown"


def main(out_path: str) -> None:
    coe = _load_coe_california()

    driver = GraphDatabase.driver(
        os.environ["NEO4J_URI"],
        auth=(os.environ["NEO4J_USERNAME"], os.environ["NEO4J_PASSWORD"]),
    )
    with driver.session() as session:
        socs = session.run(
            "MATCH (o:Occupation) RETURN o.soc_code AS soc, o.title AS title"
        ).data()
        support = session.run(
            """
            MATCH (col:College)
            OPTIONAL MATCH (col)-[:OFFERS]->(:Department)-[:CONTAINS]->(:Course)
                          -[:PREPARES_FOR]->(occ:Occupation)
            RETURN occ.soc_code AS soc, count(DISTINCT col) AS n_colleges
            """
        ).data()
    driver.close()

    college_count = {r["soc"]: r["n_colleges"] for r in support if r["soc"]}

    enriched: list[dict] = []
    for s in socs:
        soc = s["soc"]
        c = coe.get(soc, {})
        edu = c.get("education", "")
        band = _band(edu)
        openings = c.get("annual_openings", 0)
        tier = _tier(band, openings)
        enriched.append({
            "soc": soc, "title": s["title"], "edu": edu, "band": band,
            "openings": openings,
            "median_wage": c.get("median_wage", 0),
            "growth_rate": c.get("growth_rate", 0.0),
            "tier": tier,
            "n_colleges": college_count.get(soc, 0),
        })

    by_tier: dict[str, list[dict]] = defaultdict(list)
    for r in enriched:
        by_tier[r["tier"]].append(r)
    for t in by_tier:
        by_tier[t].sort(key=lambda r: -r["openings"])

    out: list[str] = []
    out.append("# Comprehensive CTE Occupations List\n\n")
    out.append(
        "All 506 SOCs in the ontology, categorized by CTE-relevance tier. "
        "Transfer-track threshold: ≥500 statewide annual openings "
        "(rationale: a meaningful CCC transfer pipeline requires "
        "real downstream hiring volume).\n\n"
    )

    out.append("## Tier counts\n\n")
    out.append("| Tier | SOCs | Pct |\n|---|---:|---:|\n")
    for t in ["1. Direct CTE", "2. Transfer-track CTE candidate",
              "3. Bachelor's, low transfer-track signal",
              "4. Out of CCC scope", "5. Unknown"]:
        n = len(by_tier.get(t, []))
        if n: out.append(f"| {t} | {n} | {100*n/len(enriched):.1f}% |\n")

    direct = len(by_tier.get("1. Direct CTE", []))
    transfer = len(by_tier.get("2. Transfer-track CTE candidate", []))
    out.append(f"\n**Total CTE-relevant (direct + transfer-track): "
               f"{direct + transfer} ({100*(direct+transfer)/len(enriched):.1f}%)**\n\n")

    # Tier 1: Direct CTE
    t1 = by_tier["1. Direct CTE"]
    out.append(f"\n---\n\n## Tier 1: Direct CTE  ({len(t1)} SOCs)\n\n")
    out.append(
        "CCC trains the credential the employer hires on. Strong CTE "
        "(postsecondary nondegree / associate's) and Moderate CTE "
        "(HS / some college / no credential) education bands. Sorted "
        "by California annual openings descending.\n\n"
    )
    out.append("| SOC | Title | Band | CA Openings/yr | Wage | Growth | Colleges |\n"
               "|---|---|---|---:|---:|---:|---:|\n")
    for r in t1:
        out.append(f"| `{r['soc']}` | {r['title']} | {r['band']} | "
                   f"{r['openings']:,} | ${r['median_wage']:,} | "
                   f"{r['growth_rate']:+.1f}% | {r['n_colleges']}/8 |\n")

    # Tier 2: Transfer-track CTE
    t2 = by_tier["2. Transfer-track CTE candidate"]
    out.append(f"\n---\n\n## Tier 2: Transfer-track CTE candidate  "
               f"({len(t2)} SOCs)\n\n")
    out.append(
        "Bachelor's-entry SOCs with ≥500 California annual openings. "
        "CCC produces the foundation; the BS program completes the "
        "credential; the employer hires the BS grad. The CCC's role is "
        "the 2+2 transfer pipeline. These are real CCC outcomes "
        "downstream — partnership engagement model differs from direct "
        "CTE (foundational training + transfer support vs. terminal "
        "credential).\n\n"
    )
    out.append("| SOC | Title | CA Openings/yr | Wage | Growth | Colleges |\n"
               "|---|---|---:|---:|---:|---:|\n")
    for r in t2:
        out.append(f"| `{r['soc']}` | {r['title']} | "
                   f"{r['openings']:,} | ${r['median_wage']:,} | "
                   f"{r['growth_rate']:+.1f}% | {r['n_colleges']}/8 |\n")

    # Tier 3: Low-signal bachelor's
    t3 = by_tier.get("3. Bachelor's, low transfer-track signal", [])
    out.append(f"\n---\n\n## Tier 3: Bachelor's, low transfer-track signal  "
               f"({len(t3)} SOCs)\n\n")
    out.append(
        "Bachelor's-entry SOCs with <500 California annual openings. "
        "TOP-reachable but the demand is too thin to justify a CCC "
        "transfer pipeline focus. Could be considered noise from a "
        "CTE-program-development perspective.\n\n"
    )
    out.append("| SOC | Title | CA Openings/yr | Wage |\n"
               "|---|---|---:|---:|\n")
    for r in t3:
        out.append(f"| `{r['soc']}` | {r['title']} | "
                   f"{r['openings']:,} | ${r['median_wage']:,} |\n")

    # Tier 4: Out of scope
    t4 = by_tier.get("4. Out of CCC scope", [])
    out.append(f"\n---\n\n## Tier 4: Out of CCC scope  ({len(t4)} SOCs)\n\n")
    out.append(
        "Master's+ entry. Not directly CCC outcomes. Reachable via "
        "TOP-CIP-SOC because some TOPs feed graduate-prep programs, "
        "but neither direct-CTE nor transfer-track CTE.\n\n"
    )
    out.append("| SOC | Title | CA Openings/yr | Wage |\n"
               "|---|---|---:|---:|\n")
    for r in t4:
        out.append(f"| `{r['soc']}` | {r['title']} | "
                   f"{r['openings']:,} | ${r['median_wage']:,} |\n")

    Path(out_path).write_text("".join(out))
    print(f"Wrote {out_path}")
    for t in sorted(by_tier.keys()):
        print(f"  {t}: {len(by_tier[t])}")


if __name__ == "__main__":
    main("/app/comprehensive_cte_list.md")
