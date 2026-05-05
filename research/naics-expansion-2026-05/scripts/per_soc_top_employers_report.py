"""Per-SOC top employer report under expanded methodology.

For each direct-CTE supported SOC, list top employers by pct_total
across the two scraped regions (SD and LA). Uses OEWS NAICS-occupation
matrix to determine pct_total for each (employer, NAICS, SOC) triple.
"""

from __future__ import annotations

import csv
import json
import os
from collections import Counter, defaultdict
from pathlib import Path

import openpyxl
from neo4j import GraphDatabase

from ontology.crosswalks import (
    COE_DEMAND_PATH, _load_cip_to_soc, _load_pcah_cte_top6, _load_top_to_cip,
)
from ontology import oes as _oes
from ontology.oes import oes_socs_for_naics4
from employers.edd_scrape import CTE_NAICS_CODES

REGIONS = [
    ("SD", "/app/sd_full.json"),
    ("LA", "/app/la_full.json"),
]

TOP_N = 10


def _load_naics_titles() -> dict[str, str]:
    wb = openpyxl.load_workbook(_oes.OES_NAICS4_PATH, read_only=True)
    ws = wb.active
    rows = ws.iter_rows(values_only=True)
    header = next(rows)
    cols = {c: i for i, c in enumerate(header)}
    titles: dict[str, str] = {}
    for row in rows:
        if not row: continue
        n = row[cols["NAICS"]]; t = row[cols["NAICS_TITLE"]]
        if n is None or t is None: continue
        s = str(n).strip()
        if len(s) == 6 and s.isdigit():
            titles.setdefault(s[:4], str(t))
    wb.close()
    return titles


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


def main(out_path: str) -> None:
    edu_by_soc = _load_education()
    soc_to_sector = _classify_soc_sector()
    naics_titles = _load_naics_titles()
    _oes._ensure_loaded()

    # Load scrape results per region: {region: {naics: [employers]}}
    region_data: dict[str, dict[str, list[str]]] = {}
    for region, path in REGIONS:
        if Path(path).exists():
            region_data[region] = json.loads(Path(path).read_text())
        else:
            region_data[region] = {}

    # Get direct-CTE supported SOCs from graph.
    driver = GraphDatabase.driver(
        os.environ["NEO4J_URI"],
        auth=(os.environ["NEO4J_USERNAME"], os.environ["NEO4J_PASSWORD"]),
    )
    with driver.session() as session:
        all_socs = session.run(
            "MATCH (o:Occupation) RETURN o.soc_code AS soc, o.title AS title"
        ).data()
        # Per-SOC: which colleges support it
        soc_colleges = session.run(
            """
            MATCH (col:College)-[:OFFERS]->(:Department)-[:CONTAINS]->(:Course)
                  -[:PREPARES_FOR]->(o:Occupation)
            RETURN o.soc_code AS soc, collect(DISTINCT col.name) AS colleges
            """
        ).data()
    driver.close()
    soc_titles = {r["soc"]: r["title"] for r in all_socs}
    soc_supporters = {r["soc"]: r["colleges"] for r in soc_colleges}

    direct_socs = [
        s for s in all_socs
        if _band(edu_by_soc.get(s["soc"], "")) in ("Strong CTE", "Moderate CTE")
        and s["soc"] in soc_supporters
    ]

    # Per SOC: collect (region, employer, naics, pct_total) tuples.
    per_soc: dict[str, list[dict]] = defaultdict(list)
    for s in direct_socs:
        soc = s["soc"]
        # Get all NAICS where this SOC is published with pct_total > 0
        for region, naics_to_emps in region_data.items():
            for naics, employers in naics_to_emps.items():
                if not employers: continue
                # Look up pct_total for this (NAICS, SOC) pair
                rows = oes_socs_for_naics4(naics)
                pct = next((r.get("pct_total", 0) for r in rows if r["soc"] == soc), 0)
                if pct <= 0: continue
                # Dedupe employers within the same (region, naics)
                seen = set()
                for emp in employers:
                    key = emp.lower().strip()
                    if key in seen: continue
                    seen.add(key)
                    per_soc[soc].append({
                        "region": region,
                        "employer": emp,
                        "naics": naics,
                        "naics_title": naics_titles.get(naics, "(no title)"),
                        "pct_total": pct,
                    })
        per_soc[soc].sort(key=lambda x: -x["pct_total"])

    # Group SOCs by sector.
    by_sector: dict[str, list] = defaultdict(list)
    for s in direct_socs:
        sector = soc_to_sector.get(s["soc"], "Unclassified")
        by_sector[sector].append(s)

    out: list[str] = []
    out.append("# Per-SOC Top Employers — Expanded Methodology Demonstration\n\n")
    out.append(
        "For every direct-CTE SOC supported by at least one of the 8 "
        "loaded colleges, lists the top employers under the fully "
        "expanded methodology:\n\n"
        "- **NAICS**: every NAICS in the union of `CTE_NAICS_CODES` "
        "and missing-but-relevant NAICS (top-5 per direct-CTE SOC by "
        "OEWS pct_total)\n"
        "- **Size**: E+ (50+ employees)\n"
        "- **Filter**: 0% (every BLS-published pair), sorted by "
        "pct_total descending\n"
        "- **Regions**: San Diego (SD/I) and Los Angeles (LA)\n\n"
        "Each employer's pct_total is the BLS-published share of that "
        "industry's workforce in this occupation. URL-filter is NOT "
        "applied — this is the pre-filter view.\n\n"
    )
    out.append("## Coverage summary\n\n")
    served = sum(1 for s in direct_socs if per_soc.get(s["soc"]))
    out.append(f"- Direct-CTE supported SOCs: **{len(direct_socs)}**\n")
    out.append(f"- SOCs with ≥1 candidate from SD or LA: **{served}** "
               f"({100*served/len(direct_socs):.1f}%)\n")
    out.append(f"- Total (SOC, region, employer) tuples: "
               f"**{sum(len(v) for v in per_soc.values()):,}**\n\n")

    # Per-sector sections.
    sector_order = sorted(by_sector.keys(),
                          key=lambda s: -len(by_sector[s]))
    out.append("## SOCs by sector\n\n")
    out.append("| Sector | SOCs | With candidates |\n|---|---:|---:|\n")
    for sector in sector_order:
        socs = by_sector[sector]
        with_cands = sum(1 for s in socs if per_soc.get(s["soc"]))
        out.append(f"| {sector} | {len(socs)} | {with_cands} |\n")

    out.append("\n---\n\n# Per-SOC top employers\n\n")
    for sector in sector_order:
        socs = by_sector[sector]
        out.append(f"\n## {sector}  ({len(socs)} SOCs)\n")
        # Order SOCs by max top pct_total
        def _max_pct(s):
            cands = per_soc.get(s["soc"], [])
            return cands[0]["pct_total"] if cands else 0
        socs.sort(key=lambda s: (-_max_pct(s), s["soc"]))
        for s in socs:
            soc = s["soc"]
            title = soc_titles[soc]
            cands = per_soc.get(soc, [])
            edu = edu_by_soc.get(soc, "")
            band = _band(edu)
            n_colleges = len(soc_supporters.get(soc, []))
            out.append(f"\n### `{soc}` {title}\n")
            out.append(f"*{band} · {edu} · {n_colleges}/8 colleges support · "
                       f"{len(cands)} candidates*\n\n")
            if not cands:
                out.append("*No regional employer in scraped NAICS where BLS "
                           "publishes this SOC.*\n")
                continue
            top = cands[:TOP_N]
            out.append("| pct_total | Region | Employer | NAICS-4 |\n"
                       "|---:|:---:|---|---|\n")
            for c in top:
                out.append(f"| {c['pct_total']:.1f}% | {c['region']} | "
                           f"{c['employer']} | {c['naics']} |\n")
            if len(cands) > TOP_N:
                out.append(f"\n*... and {len(cands)-TOP_N} more candidates*\n")

    Path(out_path).write_text("".join(out))
    print(f"Wrote {out_path}")
    print(f"  {len(direct_socs)} direct-CTE SOCs, "
          f"{served} with candidates, "
          f"{sum(len(v) for v in per_soc.values()):,} pairs")


if __name__ == "__main__":
    main("/app/per_soc_top_employers.md")
