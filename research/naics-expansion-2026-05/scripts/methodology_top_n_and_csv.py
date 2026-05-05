"""Render the methodology output in two digestible forms:
  1. Top-N-per-SOC markdown — for human scanning of the highest-signal
     candidates only (truncated per SOC to keep total file size reasonable)
  2. Full CSV — every (employer, SOC) pair, for spreadsheet review
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
TOP_N = 10


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
        if not votes: continue
        top_v = max(votes.values())
        out[soc] = sorted([s for s, v in votes.items() if v == top_v])
    return out


def main(md_path: str, csv_path: str) -> None:
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
            if r["soc"] not in supported_socs: continue
            pct = r.get("pct_total") or 0.0
            if pct <= 0: continue
            per_soc.setdefault(r["soc"], []).append({
                "name": emp["name"],
                "naics4": emp["naics4"],
                "pct_total": pct,
                "llm_corr": r["soc"] in llm_set,
            })
    for soc in per_soc:
        per_soc[soc].sort(key=lambda c: (-c["pct_total"], c["name"]))

    by_sector: dict[str, list[str]] = {}
    for soc in supported_socs:
        sectors = soc_to_sector.get(soc, [])
        if not sectors:
            by_sector.setdefault("(no PCAH sector)", []).append(soc)
            continue
        key = sectors[0] if len(sectors) == 1 else f"(tied: {' / '.join(sectors)})"
        by_sector.setdefault(key, []).append(soc)

    # ── Markdown: top-N per SOC ───────────────────────────────────────
    out: list[str] = []
    out.append(f"# Top {TOP_N} Partnership Candidates per SOC — {COLLEGE} ({region})\n\n")
    out.append(
        f"For each supported SOC, lists the top {TOP_N} regional "
        f"employers by pct_total (BLS Industry-Occupation Matrix "
        f"workforce share). Truncated for readability — the full list "
        f"per SOC is in the companion CSV. `LLM ✓` = employer's "
        f"identity-curated SOC list corroborates this assignment.\n\n"
    )
    out.append(f"- Supported SOCs: {len(supported_socs)}\n")
    out.append(f"- All have candidates: {len(per_soc)}\n")
    out.append(f"- Companion CSV: every (employer, SOC) pair "
               f"({sum(len(v) for v in per_soc.values()):,} rows)\n\n")

    sector_order = sorted(by_sector.keys(), key=lambda s: -len(by_sector[s]))
    for sector in sector_order:
        socs = by_sector[sector]
        out.append(f"\n## {sector}  ({len(socs)} SOCs)\n")
        def _max_pct(soc):
            return max((c["pct_total"] for c in per_soc.get(soc, [])),
                       default=0.0)
        socs.sort(key=lambda s: (-_max_pct(s), s))
        for soc in socs:
            cands = per_soc.get(soc, [])
            title = supported_socs[soc]
            edu = edu_by_soc.get(soc, "(unknown)")
            band = _band(edu)
            top_pct = _max_pct(soc)
            n = len(cands)
            out.append(f"\n### `{soc}` {title}\n")
            out.append(f"*{band} · {edu} · {n} total candidates · "
                       f"top: {top_pct:.2f}%*\n\n")
            shown = cands[:TOP_N]
            out.append("| pct_total | Employer | NAICS-4 | LLM |\n"
                       "|---:|---|---|:---:|\n")
            for c in shown:
                mark = "✓" if c["llm_corr"] else " "
                out.append(f"| {c['pct_total']:.1f}% | {c['name']} | "
                           f"{c['naics4']} | {mark} |\n")
            if n > TOP_N:
                out.append(f"\n*... and {n - TOP_N} more in the CSV*\n")

    Path(md_path).write_text("".join(out))
    print(f"Wrote {md_path}")

    # ── CSV: full pair-level data ─────────────────────────────────────
    with open(csv_path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow([
            "soc", "soc_title", "education_band", "education_level",
            "swp_sector", "rank_within_soc",
            "employer", "naics4", "pct_total", "llm_corroborated",
        ])
        for sector in sector_order:
            for soc in by_sector[sector]:
                cands = per_soc.get(soc, [])
                title = supported_socs[soc]
                edu = edu_by_soc.get(soc, "")
                band = _band(edu)
                for i, c in enumerate(cands, start=1):
                    w.writerow([
                        soc, title, band, edu, sector, i,
                        c["name"], c["naics4"], f"{c['pct_total']:.4f}",
                        "yes" if c["llm_corr"] else "no",
                    ])
    print(f"Wrote {csv_path}")


if __name__ == "__main__":
    main("/app/methodology_top10.md", "/app/methodology_full.csv")
