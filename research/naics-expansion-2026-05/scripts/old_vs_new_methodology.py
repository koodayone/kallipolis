"""For every direct-CTE SOC supported by at least one college, compare:
  - Old method: existing HIRES_FOR edges in graph (F+ employers in
    SD/I or LA region, LLM-curated identity match)
  - New method: expanded scrape (E+ at 0% pct_total threshold,
    sorted by pct_total descending)

Per-SOC metrics:
  - n_old, n_new (count comparison)
  - top-10 overlap rate (do methods agree on best candidates)
  - new-only and old-only employers (where each method finds what
    the other misses)
  - qualitative read on top-of-list defensibility
"""

from __future__ import annotations

import csv
import json
import os
from collections import Counter, defaultdict
from pathlib import Path

from neo4j import GraphDatabase

from ontology.crosswalks import COE_DEMAND_PATH
from ontology import oes as _oes
from ontology.oes import oes_socs_for_naics4

REGIONS = [
    ("SD", "/app/sd_full.json"),
    ("LA", "/app/la_full.json"),
]
GRAPH_REGIONS = ["SD/I", "LA"]


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


def _norm(name: str) -> str:
    return (name or "").strip().lower()


def main(out_path: str) -> None:
    edu_by_soc = _load_education()
    _oes._ensure_loaded()

    # Load expanded-scrape data per region.
    region_data: dict[str, dict[str, list[str]]] = {}
    for region, path in REGIONS:
        if Path(path).exists():
            region_data[region] = json.loads(Path(path).read_text())

    # Get old-method (graph) employer-SOC pairs in SD/I + LA regions.
    driver = GraphDatabase.driver(
        os.environ["NEO4J_URI"],
        auth=(os.environ["NEO4J_USERNAME"], os.environ["NEO4J_PASSWORD"]),
    )
    with driver.session() as session:
        old_data = session.run(
            """
            MATCH (e:Employer)-[:IN_MARKET]->(r:Region)
            WHERE r.name IN $regions
            MATCH (e)-[:HIRES_FOR]->(o:Occupation)
            RETURN o.soc_code AS soc, o.title AS title,
                   r.name AS region, e.name AS name
            """, regions=GRAPH_REGIONS,
        ).data()
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
    n_colleges_per_soc = {r["soc"]: r["n_colleges"] for r in soc_supporters}

    # Old method: per-SOC employer set (SD/I + LA combined).
    old_per_soc: dict[str, set[str]] = defaultdict(set)
    for r in old_data:
        old_per_soc[r["soc"]].add(_norm(r["name"]))

    # New method: per-SOC ranked employer list with pct_total.
    new_per_soc: dict[str, list[dict]] = defaultdict(list)
    for region, naics_to_emps in region_data.items():
        for naics, employers in naics_to_emps.items():
            if not employers: continue
            rows = oes_socs_for_naics4(naics)
            for row in rows:
                soc = row["soc"]
                pct = row.get("pct_total") or 0.0
                if pct <= 0: continue
                seen = set()
                for emp in employers:
                    key = _norm(emp)
                    if key in seen: continue
                    seen.add(key)
                    new_per_soc[soc].append({
                        "region": region, "employer": emp, "naics": naics,
                        "pct_total": pct, "key": key,
                    })
    for soc in new_per_soc:
        new_per_soc[soc].sort(key=lambda x: -x["pct_total"])

    # Direct-CTE supported SOCs.
    direct_socs = [
        soc for soc in soc_titles
        if _band(edu_by_soc.get(soc, "")) in ("Strong CTE", "Moderate CTE")
        and n_colleges_per_soc.get(soc, 0) > 0
    ]

    # Per-SOC comparison.
    rows = []
    for soc in direct_socs:
        old_set = old_per_soc.get(soc, set())
        new_list = new_per_soc.get(soc, [])
        new_top10 = new_list[:10]
        new_top10_keys = {x["key"] for x in new_top10}
        new_all_keys = {x["key"] for x in new_list}

        rows.append({
            "soc": soc,
            "title": soc_titles[soc],
            "band": _band(edu_by_soc.get(soc, "")),
            "n_colleges": n_colleges_per_soc.get(soc, 0),
            "n_old": len(old_set),
            "n_new": len(new_list),
            "n_new_top10": len(new_top10),
            "top10_overlap_with_old": len(new_top10_keys & old_set),
            "old_in_new": len(old_set & new_all_keys),
            "old_only": len(old_set - new_all_keys),
            "new_only_top10": len(new_top10_keys - old_set),
            "top_pct": new_list[0]["pct_total"] if new_list else 0.0,
            "top_employers": [(x["employer"], x["pct_total"], x["region"], x["naics"])
                              for x in new_top10],
            "old_sample": sorted(old_set)[:5],
        })

    # Aggregate findings.
    out: list[str] = []
    out.append("# Old vs New Methodology — Per-SOC Quality Comparison\n\n")
    out.append(
        "For every direct-CTE supported SOC, compares the existing "
        "Neo4j-graph employer pool (LLM-curated, F+ size, current "
        "`CTE_NAICS_CODES`) against the expanded methodology pool "
        "(0% pct_total filter, E+ size, expanded NAICS). Both restricted "
        "to SD/I + LA regions for apples-to-apples comparison.\n\n"
    )

    n_total = len(rows)
    new_covers_old = sum(1 for r in rows if r["n_new"] >= r["n_old"])
    new_more_than_2x = sum(1 for r in rows if r["n_old"] > 0 and r["n_new"] >= r["n_old"] * 2)
    new_top10_includes_old = sum(1 for r in rows if r["top10_overlap_with_old"] > 0)
    old_completely_lost = sum(1 for r in rows if r["n_old"] > 0 and r["old_in_new"] == 0)
    new_seeded = sum(1 for r in rows if r["n_old"] == 0 and r["n_new"] > 0)
    median_old = sorted([r["n_old"] for r in rows])[len(rows)//2]
    median_new = sorted([r["n_new"] for r in rows])[len(rows)//2]

    out.append("## Aggregate findings\n\n")
    out.append(f"- Direct-CTE supported SOCs (SD/I + LA): **{n_total}**\n")
    out.append(f"- Median candidate count (old): **{median_old}**\n")
    out.append(f"- Median candidate count (new): **{median_new}**\n")
    out.append(f"- SOCs where new method has ≥ old count: "
               f"**{new_covers_old} ({100*new_covers_old/n_total:.1f}%)**\n")
    out.append(f"- SOCs where new method has ≥2× old count: "
               f"**{new_more_than_2x} ({100*new_more_than_2x/n_total:.1f}%)**\n")
    out.append(f"- SOCs where new top-10 includes ≥1 old-method employer: "
               f"**{new_top10_includes_old} ({100*new_top10_includes_old/n_total:.1f}%)**\n")
    out.append(f"- SOCs where old method had employers but new method has none "
               f"(coverage regression): **{old_completely_lost}**\n")
    out.append(f"- SOCs newly seeded by new method (old=0, new>0): "
               f"**{new_seeded}**\n\n")

    # Distribution of new vs old by band.
    out.append("## Coverage distribution by band\n\n")
    bands = ["Strong CTE", "Moderate CTE"]
    for b in bands:
        sub = [r for r in rows if r["band"] == b]
        if not sub: continue
        n = len(sub)
        with_new = sum(1 for r in sub if r["n_new"] > 0)
        with_old = sum(1 for r in sub if r["n_old"] > 0)
        median_n = sorted([r["n_new"] for r in sub])[n//2]
        median_o = sorted([r["n_old"] for r in sub])[n//2]
        out.append(f"**{b}** ({n} SOCs)\n")
        out.append(f"- With ≥1 candidate: old {with_old}/{n}, new {with_new}/{n}\n")
        out.append(f"- Median candidates: old {median_o}, new {median_n}\n\n")

    # Per-SOC table — top of distribution and bottom.
    rows.sort(key=lambda r: -r["n_new"])
    out.append("## Per-SOC counts: every direct-CTE SOC\n\n")
    out.append(
        "Table includes: SOC, title, band, # supporting colleges, old "
        "count, new count, ratio (new/old or 'NEW' if old was 0), "
        "top-10 overlap with old, and top pct_total in new method.\n\n"
    )
    out.append("| SOC | Title | Band | Coll | Old | New | Δ | Top10∩Old | Top % |\n"
               "|---|---|---|---:|---:|---:|---|---:|---:|\n")
    for r in rows:
        ratio = (f"{r['n_new']/r['n_old']:.1f}x" if r["n_old"] > 0
                 else f"NEW({r['n_new']})")
        out.append(f"| `{r['soc']}` | {r['title'][:38]} | {r['band'][:5]} | "
                   f"{r['n_colleges']}/8 | {r['n_old']} | {r['n_new']} | "
                   f"{ratio} | {r['top10_overlap_with_old']}/10 | "
                   f"{r['top_pct']:.1f}% |\n")

    # Coverage regressions (where old had what new lost).
    regressions = [r for r in rows if r["n_old"] > 0 and r["old_in_new"] < r["n_old"] * 0.3]
    if regressions:
        out.append(f"\n## Coverage regressions ({len(regressions)} SOCs)\n\n")
        out.append(
            "SOCs where less than 30% of the old-method employers "
            "survive in the new method's full pool. May indicate the "
            "old LLM-curated picks were identity-aligned but in NAICS "
            "the new method doesn't reach. Sample of old employers "
            "absent from new pool shown.\n\n"
        )
        out.append("| SOC | Title | n_old | n_new | old_in_new | old_only | "
                   "Old sample (lost) |\n|---|---|---:|---:|---:|---:|---|\n")
        for r in sorted(regressions, key=lambda r: -r["n_old"])[:30]:
            sample = "; ".join(r["old_sample"][:3])
            out.append(f"| `{r['soc']}` | {r['title'][:35]} | {r['n_old']} | "
                       f"{r['n_new']} | {r['old_in_new']} | {r['old_only']} | "
                       f"{sample[:80]} |\n")

    Path(out_path).write_text("".join(out))
    print(f"Wrote {out_path}")
    print(f"Aggregate: {n_total} SOCs, "
          f"new ≥ old in {new_covers_old}, new ≥2× old in {new_more_than_2x}, "
          f"newly seeded {new_seeded}, regressions {old_completely_lost}")


if __name__ == "__main__":
    main("/app/old_vs_new_methodology.md")
