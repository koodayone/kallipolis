"""Per-college CTE program priority analysis.

For each loaded college:
  - Filter to direct-CTE supported SOCs (Strong + Moderate education bands)
  - Compute priority composite from regional COE demand × wage × growth
  - Group by SWP sector (via TOP6→PCAH classification)
  - Surface top SOCs and sector concentration

Also: per-canonical-sector, count supported SOCs and the
methodology-expansion potential (current top-5 NAICS in
CTE_NAICS_CODES vs. total OEWS-published top-5 NAICS).
"""

from __future__ import annotations

import csv
import os
from collections import Counter, defaultdict
from pathlib import Path

from neo4j import GraphDatabase

from ontology.crosswalks import (
    COE_DEMAND_PATH,
    _load_cip_to_soc,
    _load_pcah_cte_top6,
    _load_top_to_cip,
)
from ontology import oes as _oes
from employers.edd_scrape import CTE_NAICS_CODES

CANONICAL_SECTORS = [
    "Advanced Manufacturing",
    "Energy, Construction and Utilities",
    "Health",
    "Advanced Transportation and Logistics",
    "Public Safety",
    "Information and Communication Technologies - Digital Media",
    "Agriculture, Water and Environmental Technologies",
]

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


def _load_coe(region: str) -> dict[str, dict]:
    data: dict[str, dict] = {}
    with open(COE_DEMAND_PATH, newline="") as f:
        for row in csv.DictReader(f):
            if row["Region"] != region: continue
            soc = row["SOC"]
            try:
                data[soc] = {
                    "openings": int(row["Average Annual Job Openings"]),
                    "growth": float(row["2024 - 2029 % Change"]),
                    "wage": int(row["Median Annual Earnings"]),
                    "education": row["Typical Entry Level Education"].strip(),
                }
            except (ValueError, KeyError):
                continue
    return data


def _band(level: str) -> str:
    if level in {"Postsecondary nondegree award", "Associate's degree"}: return "Strong CTE"
    if level in {"High school diploma or equivalent", "Some college, no degree",
                 "No formal educational credential"}: return "Moderate CTE"
    return "Other"


def _classify_soc_sector() -> dict[str, str]:
    top6_to_sector = _load_pcah_cte_top6()
    top_cip = _load_top_to_cip()
    cip_soc = _load_cip_to_soc()
    soc_to_tops: dict[str, set[str]] = {}
    for top6, cips in top_cip.items():
        for cip in cips:
            for soc in cip_soc.get(cip, set()):
                soc_to_tops.setdefault(soc, set()).add(top6)
    out: dict[str, str] = {}
    for soc, tops in soc_to_tops.items():
        votes: Counter = Counter()
        for t in tops:
            sector = top6_to_sector.get(t)
            if sector:
                votes[sector] += 1
        if votes:
            out[soc] = votes.most_common(1)[0][0]
    return out


def _composite(rec: dict) -> float:
    """Priority = openings * wage * (1 + growth/100). Normalized later."""
    return rec["openings"] * rec["wage"] * (1 + rec["growth"]/100)


def main(out_path: str) -> None:
    soc_to_sector = _classify_soc_sector()
    _oes._ensure_loaded()

    # Per-SOC top-5 NAICS by pct_total.
    soc_to_naics: dict[str, list[tuple[str, float]]] = defaultdict(list)
    for naics4, rows in _oes._socs_by_naics4.items():
        for r in rows:
            pct = r.get("pct_total") or 0.0
            if pct > 0:
                soc_to_naics[r["soc"]].append((naics4, pct))
    for soc in soc_to_naics:
        soc_to_naics[soc].sort(key=lambda x: -x[1])

    driver = GraphDatabase.driver(
        os.environ["NEO4J_URI"],
        auth=(os.environ["NEO4J_USERNAME"], os.environ["NEO4J_PASSWORD"]),
    )
    with driver.session() as session:
        colleges = [r["n"] for r in session.run(
            "MATCH (c:College) RETURN c.name AS n ORDER BY n").data()]
        per_college: dict[str, dict] = {}
        for college in colleges:
            supported = session.run(
                """
                MATCH (c:Course {college: $col})-[:PREPARES_FOR]->(occ:Occupation)
                RETURN DISTINCT occ.soc_code AS soc, occ.title AS title
                """, col=college).data()
            per_college[college] = {
                "supported": {r["soc"]: r["title"] for r in supported},
            }
    driver.close()

    out: list[str] = []
    out.append("# Per-College CTE Priority Analysis\n\n")
    out.append(
        "For each loaded college: direct-CTE supported SOCs ranked by "
        "regional demand × wage × growth composite, with sector "
        "concentration and methodology-expansion potential.\n\n"
    )

    # ── Per-college: top priorities + sector breakdown ─────────────
    for college in colleges:
        region = COE_REGION_FOR.get(college, "CA")
        coe = _load_coe(region)
        supported = per_college[college]["supported"]

        recs: list[dict] = []
        for soc, title in supported.items():
            c = coe.get(soc)
            if not c: continue
            band = _band(c["education"])
            if band not in ("Strong CTE", "Moderate CTE"): continue
            sector = soc_to_sector.get(soc, "Unclassified")
            comp = _composite(c)
            recs.append({
                "soc": soc, "title": title, "band": band, "sector": sector,
                "openings": c["openings"], "wage": c["wage"], "growth": c["growth"],
                "composite": comp,
            })
        recs.sort(key=lambda r: -r["composite"])

        out.append(f"\n## {college}  (region: {region})\n")
        out.append(f"Direct-CTE supported SOCs with regional demand data: "
                   f"**{len(recs)}**\n\n")

        # Sector concentration.
        by_sector: dict[str, list[dict]] = defaultdict(list)
        for r in recs:
            by_sector[r["sector"]].append(r)
        out.append("### Sector concentration of supported SOCs\n\n")
        out.append("| Sector | SOCs | Top SOC by composite |\n|---|---:|---|\n")
        for sector in sorted(by_sector.keys(), key=lambda s: -len(by_sector[s])):
            top = by_sector[sector][0]
            canonical_marker = "★" if sector in CANONICAL_SECTORS else " "
            out.append(f"| {canonical_marker} {sector} | {len(by_sector[sector])} | "
                       f"`{top['soc']}` {top['title'][:45]} |\n")

        # Top 20 by composite.
        out.append("\n### Top 20 priority SOCs (by demand × wage × growth)\n\n")
        out.append("| SOC | Title | Sector | Band | Openings/yr | Wage | Growth |\n"
                   "|---|---|---|---|---:|---:|---:|\n")
        for r in recs[:20]:
            sector_short = r["sector"][:30]
            out.append(f"| `{r['soc']}` | {r['title'][:40]} | {sector_short} | "
                       f"{r['band']} | {r['openings']:,} | "
                       f"${r['wage']:,} | {r['growth']:+.1f}% |\n")

        # Methodology-expansion potential per canonical sector.
        out.append("\n### Methodology-expansion potential (canonical sectors)\n\n")
        out.append(
            "For each canonical sector, of the supported SOCs: how "
            "many of their top-5 OEWS NAICS are currently in the search "
            "list vs missing? Higher 'missing' numbers = more headroom "
            "for methodology gain.\n\n"
        )
        out.append("| Sector | SOCs | In search-list NAICS | Missing NAICS | Capture rate |\n"
                   "|---|---:|---:|---:|---:|\n")
        for sector in CANONICAL_SECTORS:
            recs_s = by_sector.get(sector, [])
            if not recs_s: continue
            in_list = 0
            missing = 0
            for r in recs_s:
                top5 = soc_to_naics.get(r["soc"], [])[:5]
                for n, _ in top5:
                    if n in CTE_NAICS_CODES:
                        in_list += 1
                    else:
                        missing += 1
            total = in_list + missing
            rate = 100 * in_list / total if total else 0
            out.append(f"| {sector} | {len(recs_s)} | {in_list} | {missing} | "
                       f"{rate:.0f}% |\n")

    Path(out_path).write_text("".join(out))
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main("/app/per_college_priorities.md")
