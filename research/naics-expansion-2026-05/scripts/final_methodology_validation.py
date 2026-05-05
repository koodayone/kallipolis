"""Comprehensive methodology validation: every supported SOC at Foothill,
every regional employer where BLS publishes the (NAICS-4, SOC) pair at
any positive pct_total, sorted by pct_total descending. LLM-corroboration
shown as an additional column. No threshold cut.

Methodology:
  - Inclusion: BLS publishes the (NAICS-4 of employer, SOC) pair with pct_total > 0
  - Sort: pct_total descending per SOC, then employer name alphabetic
  - Display: pct_total per row, LLM-corroboration marker
"""

from __future__ import annotations

import csv
import os
from collections import Counter
from pathlib import Path

from neo4j import GraphDatabase

from ontology.crosswalks import (
    COE_DEMAND_PATH,
    _load_cip_to_soc,
    _load_pcah_cte_top6,
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
        if not votes:
            continue
        top_v = max(votes.values())
        out[soc] = sorted([s for s, v in votes.items() if v == top_v])
    return out


def main(out_path: str) -> None:
    edu_by_soc = _load_education()
    soc_to_sector = _classify_soc_sector()

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
        supported_socs = {r["soc"]: r["title"] for r in supported}
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

    per_soc: dict[str, list[dict]] = {}
    for emp in emps:
        llm_set = set(emp["llm"])
        for r in oes_socs_for_naics4(emp["naics4"]):
            if r["soc"] not in supported_socs:
                continue
            pct = r.get("pct_total") or 0.0
            if pct <= 0:
                continue
            per_soc.setdefault(r["soc"], []).append({
                "name": emp["name"],
                "naics4": emp["naics4"],
                "pct_total": pct,
                "llm_corr": r["soc"] in llm_set,
            })

    by_sector: dict[str, list[str]] = {}
    unsectored: list[str] = []
    for soc in supported_socs:
        sectors = soc_to_sector.get(soc, [])
        if not sectors:
            unsectored.append(soc)
            continue
        key = sectors[0] if len(sectors) == 1 else f"(tied: {' / '.join(sectors)})"
        by_sector.setdefault(key, []).append(soc)

    out: list[str] = []
    out.append(f"# Final Methodology Validation — {COLLEGE} ({region} region)\n\n")
    out.append(
        "**Methodology:** For each supported SOC, list every regional "
        "employer whose NAICS-4 industry is published by the BLS OEWS "
        "Industry-Occupation Matrix as employing this SOC at any "
        "positive workforce share (pct_total > 0). Sort employers by "
        "pct_total descending, then by name. The `pct_total` column "
        "shows the published industry-occupation workforce share — a "
        "higher value indicates the occupation is a more central role "
        "in the employer's industry. The `LLM` column marks whether "
        "the employer's identity-curated SOC list (Gemini Flash + "
        "Gemini Pro audit) corroborates this assignment as one of the "
        "employer's top hiring roles.\n\n"
    )

    served = [s for s in supported_socs if per_soc.get(s)]
    empty = [s for s in supported_socs if not per_soc.get(s)]
    total_pairs = sum(len(v) for v in per_soc.values())

    out.append("## Coverage summary\n\n")
    out.append(f"- Curriculum-supported SOCs: **{len(supported_socs)}**\n")
    out.append(f"- SOCs with ≥1 candidate at any pct_total > 0: "
               f"**{len(served)}** "
               f"({100*len(served)/len(supported_socs):.1f}%)\n")
    out.append(f"- SOCs with no candidate (BLS publishes no row): "
               f"**{len(empty)}**\n")
    out.append(f"- Total (SOC, employer) pairs: **{total_pairs:,}**\n")
    out.append(f"- Distinct regional employers represented: "
               f"**{len({e['name'] for v in per_soc.values() for e in v})}** "
               f"of {len(emps)}\n\n")

    # Distribution buckets.
    out.append("## Per-SOC list size distribution\n\n")
    buckets = Counter()
    for soc in supported_socs:
        n = len(per_soc.get(soc, []))
        if n == 0: buckets["0"] += 1
        elif n <= 20: buckets["1-20"] += 1
        elif n <= 50: buckets["21-50"] += 1
        elif n <= 100: buckets["51-100"] += 1
        elif n <= 200: buckets["101-200"] += 1
        else: buckets["200+"] += 1
    out.append("| List size | SOCs |\n|---|---:|\n")
    for k in ["0", "1-20", "21-50", "51-100", "101-200", "200+"]:
        out.append(f"| {k} | {buckets[k]} |\n")

    # Per-SOC pct_total ceiling distribution.
    out.append("\n## Top-pct_total ceiling per SOC\n\n")
    out.append(
        "Maximum pct_total seen across each SOC's regional candidate "
        "list. Reflects how concentrated the SOC is in any one "
        "industry the Bay region has employers in.\n\n"
    )
    ceilings = Counter()
    for soc in served:
        max_pct = max(c["pct_total"] for c in per_soc[soc])
        if max_pct >= 10: ceilings["≥10%"] += 1
        elif max_pct >= 5: ceilings["5-10%"] += 1
        elif max_pct >= 2: ceilings["2-5%"] += 1
        elif max_pct >= 1: ceilings["1-2%"] += 1
        elif max_pct >= 0.5: ceilings["0.5-1%"] += 1
        else: ceilings["<0.5%"] += 1
    out.append("| Top pct_total | SOCs |\n|---|---:|\n")
    for k in ["≥10%", "5-10%", "2-5%", "1-2%", "0.5-1%", "<0.5%"]:
        out.append(f"| {k} | {ceilings[k]} |\n")

    sector_order = sorted(by_sector.keys(), key=lambda s: -len(by_sector[s]))
    out.append("\n## SOC totals by SWP sector\n\n")
    out.append("| Sector | Supported SOCs | With candidates |\n|---|---:|---:|\n")
    for sector in sector_order:
        socs = by_sector[sector]
        with_cands = sum(1 for s in socs if per_soc.get(s))
        out.append(f"| {sector} | {len(socs)} | {with_cands} |\n")

    out.append("\n---\n\n# Per-SOC employer lists\n\n")
    out.append(
        "Within each SWP sector, SOCs are ordered by descending top-"
        "pct_total ceiling (the most industry-central occupations "
        "first). Within each SOC, employers are sorted by pct_total "
        "descending.\n\n"
    )

    for sector in sector_order:
        socs = by_sector[sector]
        out.append(f"\n## {sector}  ({len(socs)} SOCs)\n\n")
        # Sort SOCs within sector by max pct_total descending so the
        # most concentrated occupations surface first.
        def _max_pct(soc):
            cands = per_soc.get(soc, [])
            return max((c["pct_total"] for c in cands), default=0.0)
        socs.sort(key=lambda s: (-_max_pct(s), s))
        for soc in socs:
            cands = per_soc.get(soc, [])
            title = supported_socs[soc]
            edu = edu_by_soc.get(soc, "(unknown)")
            band = _band(edu)
            top_pct = max((c["pct_total"] for c in cands), default=0.0)
            out.append(f"\n### `{soc}` {title}\n")
            n = len(cands)
            out.append(f"*{band} · entry-level: {edu} · "
                       f"{n} candidate{'s' if n != 1 else ''} · "
                       f"top pct_total: {top_pct:.2f}%*\n\n")
            if not cands:
                out.append("*BLS publishes no row for this SOC against any "
                           "regional employer's NAICS-4.*\n")
                continue
            cands.sort(key=lambda c: (-c["pct_total"], c["name"]))
            out.append("| pct_total | Employer | NAICS-4 | LLM |\n"
                       "|---:|---|---|:---:|\n")
            for c in cands:
                mark = "✓" if c["llm_corr"] else " "
                out.append(f"| {c['pct_total']:.1f}% | {c['name']} | "
                           f"{c['naics4']} | {mark} |\n")

    if unsectored:
        out.append(f"\n## SOCs with no PCAH sector classification "
                   f"({len(unsectored)})\n\n")
        for soc in unsectored:
            cands = per_soc.get(soc, [])
            n = len(cands)
            out.append(f"- `{soc}` {supported_socs[soc]} — "
                       f"{n} candidate{'s' if n != 1 else ''}\n")

    Path(out_path).write_text("".join(out))
    print(f"Wrote {out_path}")
    print(f"  {len(supported_socs)} SOCs, {total_pairs:,} (SOC, employer) pairs")


if __name__ == "__main__":
    main("/app/final_methodology_validation.md")
