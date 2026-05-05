"""SOC → top NAICS assignment table, organized by SWP sector.

For each direct-CTE supported SOC: top-1 NAICS by pct_total under the
expanded methodology. SWP sector via TOP6→PCAH plurality classification.
"""

from __future__ import annotations

import csv
import os
from collections import Counter, defaultdict
from pathlib import Path

import openpyxl
from neo4j import GraphDatabase

from ontology.crosswalks import (
    COE_DEMAND_PATH, _load_cip_to_soc, _load_pcah_cte_top6, _load_top_to_cip,
)
from ontology import oes as _oes


def _classify_soc_sector() -> dict[str, list[str]]:
    """SOC → list of plurality-winning SWP sectors via TOP6→PCAH."""
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
        if votes:
            top_v = max(votes.values())
            out[soc] = sorted([s for s, v in votes.items() if v == top_v])
    return out


def _load_naics_titles() -> dict[str, str]:
    titles: dict[str, str] = {}
    for path, keylen in [(_oes.OES_NAICS4_PATH, 4),
                         (_oes.OES_NAICS3_PATH, 3),
                         (_oes.OES_NAICS2_PATH, 2)]:
        wb = openpyxl.load_workbook(path, read_only=True)
        ws = wb.active
        rows = ws.iter_rows(values_only=True)
        header = next(rows)
        cols = {c: i for i, c in enumerate(header)}
        for row in rows:
            if not row: continue
            n = row[cols["NAICS"]]; t = row[cols["NAICS_TITLE"]]
            if n is None or t is None: continue
            s = str(n).strip()
            if len(s) == 6 and s.isdigit():
                titles.setdefault(s[:4], str(t))
            else:
                titles.setdefault(s, str(t))
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


def main(out_path: str) -> None:
    edu_by_soc = _load_education()
    soc_to_sectors = _classify_soc_sector()
    naics_titles = _load_naics_titles()
    _oes._ensure_loaded()

    # Per-SOC top NAICS by pct_total (across all NAICS levels).
    soc_to_top: dict[str, tuple[str, float, str]] = {}
    soc_to_top3: dict[str, list[tuple[str, float, str]]] = defaultdict(list)
    for naics, rows in _oes._socs_by_naics4.items():
        for r in rows:
            soc = r["soc"]
            pct = r.get("pct_total") or 0.0
            if pct <= 0: continue
            soc_to_top3[soc].append((naics, pct, "NAICS-4"))
    for naics, rows in _oes._socs_by_naics3.items():
        for r in rows:
            soc = r["soc"]
            pct = r.get("pct_total") or 0.0
            if pct <= 0: continue
            soc_to_top3[soc].append((naics, pct, "NAICS-3"))
    for naics, rows in _oes._socs_by_naics2.items():
        for r in rows:
            soc = r["soc"]
            pct = r.get("pct_total") or 0.0
            if pct <= 0: continue
            soc_to_top3[soc].append((naics, pct, "NAICS-2"))
    for soc in soc_to_top3:
        soc_to_top3[soc].sort(key=lambda x: -x[1])

    driver = GraphDatabase.driver(
        os.environ["NEO4J_URI"],
        auth=(os.environ["NEO4J_USERNAME"], os.environ["NEO4J_PASSWORD"]),
    )
    with driver.session() as session:
        all_socs = session.run(
            "MATCH (o:Occupation) RETURN o.soc_code AS soc, o.title AS title"
        ).data()
        soc_supporters = session.run(
            """
            MATCH (col:College)-[:OFFERS]->(:Department)-[:CONTAINS]->(:Course)
                  -[:PREPARES_FOR]->(o:Occupation)
            RETURN o.soc_code AS soc, count(DISTINCT col) AS n_colleges
            """
        ).data()
    driver.close()
    soc_titles = {r["soc"]: r["title"] for r in all_socs}
    n_colleges = {r["soc"]: r["n_colleges"] for r in soc_supporters}

    direct_socs = [
        s for s in soc_titles
        if _band(edu_by_soc.get(s, "")) in ("Strong CTE", "Moderate CTE")
        and n_colleges.get(s, 0) > 0
    ]

    by_sector: dict[str, list[dict]] = defaultdict(list)
    for soc in direct_socs:
        sectors = soc_to_sectors.get(soc, ["Unclassified"])
        sector_key = sectors[0] if len(sectors) == 1 else f"(tied: {' / '.join(sectors)})"
        top3 = soc_to_top3.get(soc, [])
        top1 = top3[0] if top3 else (None, 0, "")
        by_sector[sector_key].append({
            "soc": soc,
            "title": soc_titles[soc],
            "band": _band(edu_by_soc.get(soc, "")),
            "n_colleges": n_colleges.get(soc, 0),
            "top_naics": top1[0],
            "top_pct": top1[1],
            "top_level": top1[2],
            "top_naics_title": naics_titles.get(top1[0], "(no title)") if top1[0] else "",
            "top3": top3[:3],
        })
    for sector in by_sector:
        by_sector[sector].sort(key=lambda r: -r["top_pct"])

    out: list[str] = []
    out.append("# SOC → Top NAICS Assignment by SWP Sector\n\n")
    out.append(
        "For every direct-CTE SOC supported by ≥1 of the 8 loaded "
        "colleges: the highest pct_total NAICS published by BLS OEWS "
        "(industry where the occupation is most concentrated as a "
        "share of workforce). Organized by SWP sector classification "
        "via TOP6→PCAH plurality.\n\n"
        "Top NAICS uses the descent rule — prefers NAICS-4 detail; "
        "falls back to NAICS-3 or NAICS-2 if BLS doesn't publish "
        "NAICS-4 detail for the industry-occupation pair.\n\n"
    )

    out.append(f"## Sector totals\n\n")
    out.append("| Sector | SOCs |\n|---|---:|\n")
    for sector in sorted(by_sector.keys(), key=lambda s: -len(by_sector[s])):
        out.append(f"| {sector} | {len(by_sector[sector])} |\n")
    out.append(f"| **TOTAL** | **{sum(len(v) for v in by_sector.values())}** |\n")

    out.append("\n---\n\n")
    sector_order = sorted(by_sector.keys(), key=lambda s: -len(by_sector[s]))
    for sector in sector_order:
        socs = by_sector[sector]
        out.append(f"\n## {sector}  ({len(socs)} SOCs)\n\n")
        out.append("| SOC | Title | Band | Coll | Top NAICS | NAICS Title | pct_total |\n"
                   "|---|---|---|---:|---|---|---:|\n")
        for r in socs:
            level_marker = "" if r["top_level"] == "NAICS-4" else f" *({r['top_level']})*"
            out.append(f"| `{r['soc']}` | {r['title']} | {r['band']} | "
                       f"{r['n_colleges']}/8 | `{r['top_naics']}`{level_marker} | "
                       f"{r['top_naics_title']} | {r['top_pct']:.1f}% |\n")

    Path(out_path).write_text("".join(out))
    print(f"Wrote {out_path}")
    total = sum(len(v) for v in by_sector.values())
    print(f"  {total} direct-CTE SOCs organized into {len(by_sector)} sector buckets")


if __name__ == "__main__":
    main("/app/soc_to_top_naics_table.md")
