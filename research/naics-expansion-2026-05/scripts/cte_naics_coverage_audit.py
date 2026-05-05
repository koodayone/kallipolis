"""For each CTE-classified SOC in the ontology, identify the NAICS-4
codes with highest pct_total — the industries that BLS publishes as
employing this occupation most heavily. Compare against the project's
curated NAICS search list (edd_scrape.CTE_NAICS_CODES). Surfaces both
coverage rate and concrete expansion candidates.

The fundamental question this answers:
  "For each CTE SOC, are the top-pct_total NAICS in our search space?"
"""

from __future__ import annotations

import csv
import os
from collections import Counter, defaultdict
from pathlib import Path

from neo4j import GraphDatabase

from ontology.crosswalks import COE_DEMAND_PATH
from ontology import oes as _oes
from employers.edd_scrape import CTE_NAICS_CODES

TOP_N = 5  # Per SOC, examine top-N NAICS by pct_total
HIGH_AFFINITY_THRESHOLD = 5.0  # NAICS at ≥5% pct_total are highest-affinity


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


def main(out_path: str) -> None:
    edu_by_soc = _load_education()
    _oes._ensure_loaded()

    # Build per-SOC NAICS profile: {soc: [(naics, pct_total), ...]}
    soc_to_naics: dict[str, list[tuple[str, float]]] = defaultdict(list)
    for naics4, rows in _oes._socs_by_naics4.items():
        for r in rows:
            pct = r.get("pct_total") or 0.0
            if pct > 0:
                soc_to_naics[r["soc"]].append((naics4, pct))
    for soc in soc_to_naics:
        soc_to_naics[soc].sort(key=lambda x: -x[1])

    # Get all CTE SOCs from the graph (institutional CTE filter applied).
    driver = GraphDatabase.driver(
        os.environ["NEO4J_URI"],
        auth=(os.environ["NEO4J_USERNAME"], os.environ["NEO4J_PASSWORD"]),
    )
    with driver.session() as session:
        cte_socs = session.run(
            "MATCH (o:Occupation) RETURN o.soc_code AS soc, o.title AS title"
        ).data()
    driver.close()

    # Per SOC, compute top-N NAICS coverage and high-affinity coverage.
    results: list[dict] = []
    for r in cte_socs:
        soc, title = r["soc"], r["title"]
        edu = edu_by_soc.get(soc, "")
        band = _band(edu)
        ranked = soc_to_naics.get(soc, [])
        top_n = ranked[:TOP_N]
        high_aff = [(n, p) for n, p in ranked if p >= HIGH_AFFINITY_THRESHOLD]
        # Coverage: how many of the top-N are in CTE_NAICS_CODES?
        top_n_in = [(n, p) for n, p in top_n if n in CTE_NAICS_CODES]
        top_n_out = [(n, p) for n, p in top_n if n not in CTE_NAICS_CODES]
        high_aff_in = [(n, p) for n, p in high_aff if n in CTE_NAICS_CODES]
        high_aff_out = [(n, p) for n, p in high_aff if n not in CTE_NAICS_CODES]
        results.append({
            "soc": soc, "title": title, "edu": edu, "band": band,
            "top_n": top_n, "top_n_in": top_n_in, "top_n_out": top_n_out,
            "high_aff": high_aff,
            "high_aff_in": high_aff_in, "high_aff_out": high_aff_out,
            "any_naics": bool(ranked),
        })

    # ── Aggregate ─────────────────────────────────────────────────────
    direct_cte = [r for r in results if r["band"] in ("Strong CTE", "Moderate CTE")]
    direct_with_naics = [r for r in direct_cte if r["any_naics"]]

    out: list[str] = []
    out.append("# CTE NAICS Search-Space Audit\n\n")
    out.append(
        "Diagnostic: for each CTE-classified SOC in the ontology, BLS "
        "OEWS publishes a ranked list of NAICS-4 industries that employ "
        "the occupation, weighted by pct_total. The project's employer "
        "scrape uses a curated NAICS list (`CTE_NAICS_CODES` in "
        "`backend/employers/edd_scrape.py`, documented at "
        "`docs/pipeline/swp-sector-naics.md`). This audit asks: are the "
        f"top-{TOP_N} NAICS for each CTE SOC in the search list, and "
        f"are the high-affinity NAICS (≥{HIGH_AFFINITY_THRESHOLD}% "
        "pct_total) covered?\n\n"
    )

    out.append("## Universe\n\n")
    out.append(f"- CTE-classified Occupation nodes in graph: "
               f"**{len(cte_socs)}**\n")
    out.append(f"- Direct-CTE band (Strong + Moderate entry-level): "
               f"**{len(direct_cte)}**\n")
    out.append(f"  - Strong CTE (postsecondary nondegree / associate's): "
               f"{sum(1 for r in direct_cte if r['band'] == 'Strong CTE')}\n")
    out.append(f"  - Moderate CTE (HS / some college / no credential): "
               f"{sum(1 for r in direct_cte if r['band'] == 'Moderate CTE')}\n")
    out.append(f"- Direct-CTE SOCs with ≥1 NAICS published by BLS: "
               f"**{len(direct_with_naics)}**\n")
    out.append(f"- NAICS-4 codes in `CTE_NAICS_CODES`: "
               f"**{len(CTE_NAICS_CODES)}**\n\n")

    out.append("## Coverage of top NAICS for direct-CTE SOCs\n\n")
    out.append(
        f"For each direct-CTE SOC with at least one BLS-published "
        f"NAICS, what fraction of its top-{TOP_N} NAICS appear in our "
        f"search list?\n\n"
    )
    bins = Counter()
    for r in direct_with_naics:
        n_top = len(r["top_n"])
        n_in = len(r["top_n_in"])
        ratio = n_in / n_top if n_top else 0
        if ratio == 1.0: bins["all"] += 1
        elif ratio >= 0.6: bins["most"] += 1
        elif ratio >= 0.2: bins["some"] += 1
        elif ratio > 0: bins["one"] += 1
        else: bins["none"] += 1
    out.append("| Coverage of top-N | SOCs |\n|---|---:|\n")
    out.append(f"| All top-{TOP_N} in search list | {bins['all']} |\n")
    out.append(f"| Most (≥60%) in search list | {bins['most']} |\n")
    out.append(f"| Some (20-60%) in search list | {bins['some']} |\n")
    out.append(f"| Only one in search list | {bins['one']} |\n")
    out.append(f"| None in search list | {bins['none']} |\n")

    # Average coverage across direct-CTE.
    total_top = sum(len(r["top_n"]) for r in direct_with_naics)
    total_in = sum(len(r["top_n_in"]) for r in direct_with_naics)
    out.append(f"\n**Aggregate top-{TOP_N} coverage rate: "
               f"{100*total_in/total_top:.1f}% "
               f"({total_in}/{total_top} top-NAICS pairs in search list)**\n")

    # High-affinity coverage.
    hac = [r for r in direct_with_naics if r["high_aff"]]
    total_hi = sum(len(r["high_aff"]) for r in hac)
    total_hi_in = sum(len(r["high_aff_in"]) for r in hac)
    out.append(f"\n**High-affinity (≥{HIGH_AFFINITY_THRESHOLD}%) coverage: "
               f"{100*total_hi_in/total_hi:.1f}% "
               f"({total_hi_in}/{total_hi} high-affinity NAICS in search list "
               f"across {len(hac)} CTE SOCs that have any high-affinity NAICS)**\n")

    # ── Per-SOC detail (direct CTE) ───────────────────────────────────
    out.append(f"\n---\n\n## Per-SOC: top-{TOP_N} NAICS for every direct-CTE SOC\n\n")
    out.append(
        f"For each direct-CTE SOC, lists the top-{TOP_N} NAICS by "
        f"pct_total. `✓` = NAICS is in the search list; blank = NAICS "
        f"is NOT in the search list (potential expansion target).\n\n"
    )
    direct_with_naics.sort(key=lambda r: (r["band"], r["soc"]))
    for r in direct_with_naics:
        out.append(f"\n### `{r['soc']}` {r['title']}\n")
        n_in = len(r["top_n_in"])
        n_top = len(r["top_n"])
        out.append(f"*{r['band']} · {r['edu']} · "
                   f"top-{TOP_N} coverage: {n_in}/{n_top}*\n\n")
        out.append("| pct_total | NAICS-4 | In search list | Label (if listed) |\n"
                   "|---:|---|:---:|---|\n")
        for n, p in r["top_n"]:
            in_list = n in CTE_NAICS_CODES
            label = CTE_NAICS_CODES[n][1] if in_list else ""
            mark = "✓" if in_list else " "
            out.append(f"| {p:.1f}% | {n} | {mark} | {label} |\n")

    # ── Gaps: NAICS not in search list, ranked by importance ──────────
    out.append("\n---\n\n## Expansion candidates: top NAICS not in search list\n\n")
    out.append(
        "NAICS-4 codes that appear in the top NAICS for direct-CTE SOCs "
        "but are NOT in the project's curated search list. Ranked by how "
        "many direct-CTE SOCs they're a top-NAICS for, then by "
        "aggregate pct_total they bring across those SOCs.\n\n"
    )
    naics_score: dict[str, dict] = {}
    for r in direct_with_naics:
        for n, p in r["top_n_out"]:
            entry = naics_score.setdefault(n, {"socs": [], "total_pct": 0.0})
            entry["socs"].append((r["soc"], r["title"], p, r["band"]))
            entry["total_pct"] += p
    ranked_gaps = sorted(naics_score.items(),
                         key=lambda kv: (-len(kv[1]["socs"]), -kv[1]["total_pct"]))
    out.append("| NAICS-4 | Direct-CTE SOCs it tops | Aggregate pct | "
               "Example SOCs |\n|---|---:|---:|---|\n")
    for naics, info in ranked_gaps[:30]:
        socs = info["socs"]
        examples = "; ".join(f"`{s}` ({b}, {p:.1f}%)"
                              for s, _, p, b in sorted(socs, key=lambda x: -x[2])[:3])
        out.append(f"| `{naics}` | {len(socs)} | {info['total_pct']:.1f}% | "
                   f"{examples} |\n")

    Path(out_path).write_text("".join(out))
    print(f"Wrote {out_path}")
    print(f"Direct-CTE SOCs: {len(direct_cte)}, "
          f"with NAICS data: {len(direct_with_naics)}")
    print(f"Aggregate top-{TOP_N} coverage: {100*total_in/total_top:.1f}%")
    print(f"High-affinity coverage: {100*total_hi_in/total_hi:.1f}%")


if __name__ == "__main__":
    main("/app/cte_naics_coverage_audit.md")
