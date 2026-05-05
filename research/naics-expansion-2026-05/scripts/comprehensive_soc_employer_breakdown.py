"""Comprehensive per-SOC breakdown of partnership candidates under
NAICS ≥1% pct_total methodology, for one college. Organized by SWP
sector and CTE education band.

For each supported SOC: lists every regional employer in a NAICS-4
where the SOC has pct_total ≥ 1%, with NAICS-4, pct_total, and an
LLM-corroboration marker. SOCs with no candidates are listed at the
end.
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
THRESHOLD = 1.0


def _load_education_for_socs() -> dict[str, str]:
    edu: dict[str, str] = {}
    with open(COE_DEMAND_PATH, newline="") as f:
        for row in csv.DictReader(f):
            if row["SOC"] and row.get("Typical Entry Level Education"):
                edu.setdefault(row["SOC"], row["Typical Entry Level Education"].strip())
    return edu


def _band(level: str) -> str:
    if level in {"Postsecondary nondegree award", "Associate's degree"}:
        return "Strong CTE"
    if level in {"High school diploma or equivalent", "Some college, no degree",
                 "No formal educational credential"}:
        return "Moderate CTE"
    if level == "Bachelor's degree":
        return "Bachelor's"
    if level in {"Master's degree", "Doctoral or professional degree"}:
        return "Master's+"
    return "Unknown"


def _classify_soc_sector() -> dict[str, list[str]]:
    """Plurality-classify each SOC to a SWP sector via the crosswalk:
    SOC → set of TOP6 → sector via PCAH. Returns {soc: [winners]}.
    """
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
    edu_by_soc = _load_education_for_socs()
    soc_to_sector = _classify_soc_sector()

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
            OPTIONAL MATCH (e)-[:HIRES_FOR]->(o:Occupation)
            RETURN e.name AS name, e.naics4 AS naics4,
                   collect(DISTINCT o.soc_code) AS llm_socs
            """, r=region,
        ).data()
    driver.close()

    # Per-SOC candidate list under threshold.
    per_soc: dict[str, list[dict]] = {}
    for emp in employers:
        oes = oes_socs_for_naics4(emp["naics4"])
        for r in oes:
            if r["soc"] not in supported_socs:
                continue
            pct = r.get("pct_total") or 0.0
            if pct < THRESHOLD:
                continue
            per_soc.setdefault(r["soc"], []).append({
                "name": emp["name"],
                "naics4": emp["naics4"],
                "pct_total": pct,
                "llm_corr": r["soc"] in emp["llm_socs"],
            })

    # Group by sector.
    by_sector: dict[str, list[str]] = {}
    unsectored: list[str] = []
    for soc in supported_socs:
        sectors = soc_to_sector.get(soc, [])
        if not sectors:
            unsectored.append(soc)
            continue
        # If tied, route to a synthetic "(tied)" bucket to flag.
        key = sectors[0] if len(sectors) == 1 else f"(tied: {' / '.join(sectors)})"
        by_sector.setdefault(key, []).append(soc)

    # ── Render ────────────────────────────────────────────────────────
    out: list[str] = []
    out.append(f"# Partnership-Candidate Breakdown — {COLLEGE} ({region} region)\n\n")
    out.append(
        f"Methodology: NAICS ≥{THRESHOLD}% pct_total per BLS OEWS "
        f"Industry-Occupation Matrix. For each SOC the college "
        f"can prepare students for, lists every regional employer "
        f"whose NAICS-4 publishes that SOC at ≥{THRESHOLD}% of typical "
        f"workforce. The `LLM` column marks whether the employer's "
        f"identity-curated SOC list (Gemini Flash + Gemini Pro audit) "
        f"corroborates this assignment.\n\n"
    )

    served = [s for s in supported_socs if per_soc.get(s)]
    empty = [s for s in supported_socs if not per_soc.get(s)]
    out.append("## Coverage summary\n\n")
    out.append(f"- Curriculum-supported SOCs: **{len(supported_socs)}**\n")
    out.append(f"- SOCs with ≥1 candidate at ≥{THRESHOLD}%: "
               f"**{len(served)}** ({100*len(served)/len(supported_socs):.1f}%)\n")
    out.append(f"- SOCs with no candidate: **{len(empty)}**\n")
    out.append(f"- Total (SOC, employer) pairs: "
               f"**{sum(len(v) for v in per_soc.values())}**\n")
    out.append(f"- Distinct regional employers represented: "
               f"**{len({e['name'] for v in per_soc.values() for e in v})}** "
               f"of {len(employers)}\n\n")

    out.append("## Candidate-count distribution\n\n")
    buckets = Counter()
    for soc in supported_socs:
        n = len(per_soc.get(soc, []))
        if n == 0: buckets["0"] += 1
        elif n <= 5: buckets["1-5"] += 1
        elif n <= 15: buckets["6-15"] += 1
        elif n <= 50: buckets["16-50"] += 1
        elif n <= 100: buckets["51-100"] += 1
        else: buckets["100+"] += 1
    out.append("| Candidates | SOCs |\n|---|---:|\n")
    for k in ["0", "1-5", "6-15", "16-50", "51-100", "100+"]:
        out.append(f"| {k} | {buckets[k]} |\n")

    # Sector ordering by SOC count desc.
    sector_order = sorted(by_sector.keys(),
                          key=lambda s: -len(by_sector[s]))

    out.append("\n## SOC totals by SWP sector\n\n")
    out.append("| Sector | Supported SOCs | With candidates |\n"
               "|---|---:|---:|\n")
    for sector in sector_order:
        socs = by_sector[sector]
        with_cands = sum(1 for s in socs if per_soc.get(s))
        out.append(f"| {sector} | {len(socs)} | {with_cands} |\n")

    # ── Per-sector detail ─────────────────────────────────────────────
    out.append("\n---\n\n# Per-SOC detail\n\n")
    out.append(
        "Within each sector, SOCs are listed in descending order of "
        "candidate count so the strongest alignment surfaces first. "
        "Each candidate row shows the employer, its NAICS-4, the "
        "pct_total (BLS-published share of that NAICS-4 workforce in "
        "this SOC), and an `✓` if the LLM-curated identity layer "
        "corroborates.\n\n"
    )

    for sector in sector_order:
        socs = by_sector[sector]
        with_cands_n = sum(1 for s in socs if per_soc.get(s))
        out.append(f"\n## {sector}  "
                   f"({with_cands_n}/{len(socs)} SOCs with candidates)\n\n")
        socs.sort(key=lambda s: (-len(per_soc.get(s, [])), s))
        for soc in socs:
            cands = per_soc.get(soc, [])
            title = supported_socs[soc]
            band = _band(edu_by_soc.get(soc, ""))
            edu = edu_by_soc.get(soc, "(unknown)")
            out.append(f"\n### `{soc}` {title}\n")
            out.append(f"*{band} · entry-level: {edu} · "
                       f"{len(cands)} candidate{'s' if len(cands) != 1 else ''}*\n\n")
            if not cands:
                out.append("*No regional employer in a NAICS-4 publishing this "
                           "SOC at ≥1% of workforce.*\n")
                continue
            cands.sort(key=lambda c: (-c["pct_total"], c["name"]))
            out.append("| Employer | NAICS-4 | pct_total | LLM |\n"
                       "|---|---|---:|:---:|\n")
            for c in cands:
                mark = "✓" if c["llm_corr"] else " "
                out.append(f"| {c['name']} | {c['naics4']} | "
                           f"{c['pct_total']:.1f}% | {mark} |\n")

    # Unsectored.
    if unsectored:
        out.append(f"\n## SOCs with no PCAH sector classification "
                   f"({len(unsectored)})\n\n")
        for soc in unsectored:
            cands = per_soc.get(soc, [])
            out.append(f"- `{soc}` {supported_socs[soc]} — "
                       f"{len(cands)} candidate{'s' if len(cands) != 1 else ''}\n")

    Path(out_path).write_text("".join(out))
    print(f"Wrote {out_path} "
          f"({len(supported_socs)} SOCs, "
          f"{sum(len(v) for v in per_soc.values())} (SOC, employer) pairs)")


if __name__ == "__main__":
    main("/app/comprehensive_soc_employer_breakdown.md")
