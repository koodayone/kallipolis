"""Analyze the composition of TOP-reachable SOCs in the ontology.

For each Occupation node in the graph, compile:
  - Education band (Strong CTE / Moderate CTE / Bachelor's / Master's+)
  - Statewide annual openings (COE California aggregate)
  - Median wage (COE CA)
  - 5-year growth rate (COE CA)
  - College coverage (how many of 8 loaded colleges support the SOC
    via PREPARES_FOR)

Then bucket into prioritization tiers grounded in CTE-program-
development logic: direct-CTE + high regional demand + decent wage =
top priority for program emphasis.
"""

from __future__ import annotations

import csv
import os
from collections import Counter, defaultdict
from pathlib import Path

from neo4j import GraphDatabase

from ontology.crosswalks import COE_DEMAND_PATH


def _load_coe_california() -> dict[str, dict]:
    """Load COE statewide ('CA' region) demand data per SOC."""
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
                    "jobs_2024": int(row["2024 Jobs"]),
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


def _demand_tier(openings: int) -> str:
    if openings >= 5000: return "Very high (≥5k/yr)"
    if openings >= 1000: return "High (1k-5k/yr)"
    if openings >= 200: return "Medium (200-1k/yr)"
    if openings >= 50: return "Low (50-200/yr)"
    if openings > 0: return "Very low (<50/yr)"
    return "No data"


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
        # Per-college support count for each SOC.
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
        title = s["title"]
        c = coe.get(soc, {})
        edu = c.get("education", "")
        band = _band(edu)
        enriched.append({
            "soc": soc, "title": title, "edu": edu, "band": band,
            "openings": c.get("annual_openings", 0),
            "median_wage": c.get("median_wage", 0),
            "growth_rate": c.get("growth_rate", 0.0),
            "demand_tier": _demand_tier(c.get("annual_openings", 0)),
            "n_colleges": college_count.get(soc, 0),
        })

    out: list[str] = []
    out.append("# TOP-Reachable SOC Composition Analysis\n\n")
    out.append(
        "Composition of the 506 SOCs in the graph (the institutional "
        "CTE-reachable universe) by education band, statewide demand, "
        "wage, growth, and per-college coverage. Tests whether all "
        "TOP-reachable SOCs are equally CTE-relevant or whether the "
        "set has natural prioritization structure.\n\n"
    )

    out.append("## Composition by education band\n\n")
    by_band = defaultdict(list)
    for r in enriched:
        by_band[r["band"]].append(r)
    out.append("| Band | SOCs | Pct |\n|---|---:|---:|\n")
    band_order = ["Strong CTE", "Moderate CTE", "Bachelor's", "Master's+", "Unknown"]
    for b in band_order:
        n = len(by_band[b])
        if n: out.append(f"| {b} | {n} | {100*n/len(enriched):.1f}% |\n")
    direct = len(by_band["Strong CTE"]) + len(by_band["Moderate CTE"])
    out.append(f"| **Direct-CTE total** | **{direct}** | "
               f"**{100*direct/len(enriched):.1f}%** |\n")

    out.append("\n## Composition by statewide demand tier\n\n")
    by_demand = defaultdict(list)
    for r in enriched:
        by_demand[r["demand_tier"]].append(r)
    out.append("| Demand tier | SOCs | Pct |\n|---|---:|---:|\n")
    for t in ["Very high (≥5k/yr)", "High (1k-5k/yr)", "Medium (200-1k/yr)",
              "Low (50-200/yr)", "Very low (<50/yr)", "No data"]:
        n = len(by_demand[t])
        if n: out.append(f"| {t} | {n} | {100*n/len(enriched):.1f}% |\n")

    out.append("\n## Cross-tab: education band × demand tier\n\n")
    out.append(
        "Counts of SOCs at each (band, demand) combination. The "
        "high-priority CTE-program-development quadrant is "
        "**Strong/Moderate CTE × Medium-or-higher demand**.\n\n"
    )
    cross = defaultdict(int)
    for r in enriched:
        cross[(r["band"], r["demand_tier"])] += 1
    out.append("| Band \\ Demand | ≥5k | 1k-5k | 200-1k | 50-200 | <50 | No data |\n"
               "|---|---:|---:|---:|---:|---:|---:|\n")
    for b in band_order:
        if b not in by_band: continue
        row = [b]
        for t in ["Very high (≥5k/yr)", "High (1k-5k/yr)", "Medium (200-1k/yr)",
                  "Low (50-200/yr)", "Very low (<50/yr)", "No data"]:
            row.append(str(cross.get((b, t), 0)))
        out.append(f"| {' | '.join(row)} |\n")

    # Priority bucketing.
    def priority(r: dict) -> str:
        if r["band"] not in ("Strong CTE", "Moderate CTE"):
            return "Out of direct-CTE scope"
        if r["openings"] >= 1000:
            return "Tier 1: high-demand direct CTE"
        if r["openings"] >= 200:
            return "Tier 2: medium-demand direct CTE"
        if r["openings"] >= 50:
            return "Tier 3: low-demand direct CTE"
        if r["openings"] > 0:
            return "Tier 4: niche direct CTE"
        return "No demand data"

    by_priority = defaultdict(list)
    for r in enriched:
        by_priority[priority(r)].append(r)

    out.append("\n## Prioritization tiers\n\n")
    out.append(
        "Direct-CTE SOCs grouped by statewide demand. The tier model "
        "frames CTE-program-development priority: high regional "
        "demand × direct-CTE entry-level = top priority for emphasis.\n\n"
    )
    out.append("| Tier | SOCs | Median wage | Median growth |\n"
               "|---|---:|---:|---:|\n")
    for t in ["Tier 1: high-demand direct CTE", "Tier 2: medium-demand direct CTE",
              "Tier 3: low-demand direct CTE", "Tier 4: niche direct CTE",
              "No demand data", "Out of direct-CTE scope"]:
        recs = by_priority[t]
        if not recs: continue
        wages = sorted([r["median_wage"] for r in recs if r["median_wage"]])
        growths = sorted([r["growth_rate"] for r in recs])
        med_w = wages[len(wages)//2] if wages else 0
        med_g = growths[len(growths)//2] if growths else 0
        out.append(f"| {t} | {len(recs)} | ${med_w:,} | {med_g:+.1f}% |\n")

    # Top SOCs in Tier 1.
    out.append("\n## Tier 1 (high-demand direct CTE) — full list\n\n")
    out.append(
        "These are the highest-priority CTE program-development "
        "candidates: ≥1000 statewide annual openings, direct-CTE "
        "entry-level. Sorted by openings desc.\n\n"
    )
    tier1 = sorted(by_priority["Tier 1: high-demand direct CTE"],
                   key=lambda r: -r["openings"])
    out.append("| SOC | Title | Band | CA Openings/yr | Median Wage | Growth | Colleges |\n"
               "|---|---|---|---:|---:|---:|---:|\n")
    for r in tier1:
        out.append(f"| `{r['soc']}` | {r['title']} | {r['band']} | "
                   f"{r['openings']:,} | ${r['median_wage']:,} | "
                   f"{r['growth_rate']:+.1f}% | {r['n_colleges']}/8 |\n")

    # Tier 4 / niche — useful to inspect for noise.
    out.append("\n## Tier 4 (niche direct CTE, <50 openings/yr) — sample\n\n")
    out.append(
        "Direct-CTE SOCs with very low statewide demand. Useful to "
        "inspect for whether they're niche-but-real CCC programs or "
        "noise the institutional CTE filter didn't catch.\n\n"
    )
    tier4 = sorted(by_priority["Tier 4: niche direct CTE"],
                   key=lambda r: r["openings"])
    out.append("| SOC | Title | Band | CA Openings/yr | Wage | Growth |\n"
               "|---|---|---|---:|---:|---:|\n")
    for r in tier4[:30]:
        out.append(f"| `{r['soc']}` | {r['title']} | {r['band']} | "
                   f"{r['openings']:,} | ${r['median_wage']:,} | "
                   f"{r['growth_rate']:+.1f}% |\n")

    # Out of scope inspection.
    out.append("\n## Out-of-direct-CTE-scope SOCs in graph (sample of "
               "high-demand)\n\n")
    out.append(
        "SOCs in the graph that require Bachelor's+ entry. They're "
        "TOP-reachable (transfer-track) but not direct CCC outcomes. "
        "Showing high-demand examples to assess whether they belong "
        "in the report at all.\n\n"
    )
    oos = sorted(by_priority["Out of direct-CTE scope"],
                 key=lambda r: -r["openings"])
    out.append("| SOC | Title | Band | CA Openings/yr | Wage |\n"
               "|---|---|---|---:|---:|\n")
    for r in oos[:25]:
        out.append(f"| `{r['soc']}` | {r['title']} | {r['band']} | "
                   f"{r['openings']:,} | ${r['median_wage']:,} |\n")

    Path(out_path).write_text("".join(out))
    print(f"Wrote {out_path}")
    print(f"Total SOCs: {len(enriched)}")
    for b in band_order:
        n = len(by_band[b])
        if n: print(f"  {b}: {n}")
    for t in ["Tier 1: high-demand direct CTE", "Tier 2: medium-demand direct CTE",
              "Tier 3: low-demand direct CTE", "Tier 4: niche direct CTE"]:
        n = len(by_priority[t])
        print(f"  {t}: {n}")


if __name__ == "__main__":
    main("/app/soc_composition_analysis.md")
