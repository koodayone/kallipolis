"""For representative SOCs, side-by-side: LLM-curated employers vs
new-method top employers, with each employer's NAICS and the
pct_total that NAICS publishes for the SOC. Tests whether LLM picks
add signal beyond what top-pct NAICS-based selection captures.
"""

from __future__ import annotations

import json
import os
from collections import defaultdict
from pathlib import Path

from neo4j import GraphDatabase

from ontology import oes as _oes
from ontology.oes import oes_socs_for_naics4

REGIONS = [
    ("SD", "/app/sd_full.json"),
    ("LA", "/app/la_full.json"),
]
GRAPH_REGIONS = ["SD/I", "LA"]

# Representative SOCs spanning the spectrum.
SAMPLE_SOCS = [
    ("49-9021", "HVAC Mechanics — Strong CTE specialty"),
    ("47-2111", "Electricians — Strong-CTE-aligned trade"),
    ("23-2011", "Paralegals — Strong CTE legal specialty"),
    ("49-3023", "Automotive Service Techs — very distinctive"),
    ("31-9091", "Dental Assistants — distinctive medical"),
    ("29-2061", "LVNs — distinctive nursing"),
    ("29-2042", "EMTs — distinctive emergency"),
    ("33-3051", "Police — distinctive public safety"),
    ("15-1232", "Computer User Support — moderate"),
    ("13-2011", "Accountants — cross-cutting bachelor's"),
]


def main(out_path: str) -> None:
    _oes._ensure_loaded()
    region_data: dict[str, dict[str, list[str]]] = {}
    for region, path in REGIONS:
        if Path(path).exists():
            region_data[region] = json.loads(Path(path).read_text())

    driver = GraphDatabase.driver(
        os.environ["NEO4J_URI"],
        auth=(os.environ["NEO4J_USERNAME"], os.environ["NEO4J_PASSWORD"]),
    )
    with driver.session() as session:
        # LLM picks per SOC in SD/I + LA, with each employer's NAICS-4.
        rows = session.run(
            """
            MATCH (e:Employer)-[:IN_MARKET]->(r:Region)
            WHERE r.name IN $regions
            MATCH (e)-[:HIRES_FOR]->(o:Occupation)
            RETURN o.soc_code AS soc, r.name AS region,
                   e.name AS name, e.naics4 AS naics4
            """, regions=GRAPH_REGIONS,
        ).data()
    driver.close()

    llm_per_soc: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        llm_per_soc[r["soc"]].append({
            "name": r["name"], "region": r["region"], "naics": r["naics4"],
        })

    # Build new-method per-SOC pool with pct_total.
    new_per_soc: dict[str, list[dict]] = defaultdict(list)
    for region, naics_to_emps in region_data.items():
        for naics, employers in naics_to_emps.items():
            if not employers: continue
            socs = oes_socs_for_naics4(naics)
            for r in socs:
                soc = r["soc"]
                pct = r.get("pct_total") or 0.0
                if pct <= 0: continue
                seen = set()
                for emp in employers:
                    key = emp.lower().strip()
                    if key in seen: continue
                    seen.add(key)
                    new_per_soc[soc].append({
                        "name": emp, "region": region, "naics": naics,
                        "pct_total": pct,
                    })
    for soc in new_per_soc:
        new_per_soc[soc].sort(key=lambda x: -x["pct_total"])

    out: list[str] = []
    out.append("# LLM Picks vs Top-NAICS Picks: Side-by-Side\n\n")
    out.append(
        "For each sample SOC, compares the LLM-curated employer set "
        "(from graph HIRES_FOR edges in SD/I + LA) against the top "
        "employers under the new methodology (sorted by pct_total of "
        "the NAICS each employer sits in). The pct_total column shows "
        "what BLS publishes for the (NAICS, SOC) pair — same for every "
        "employer in the same NAICS.\n\n"
        "**Key question:** When the LLM picks an employer, does that "
        "employer sit in the top-pct NAICS for the SOC (LLM is "
        "redundant with NAICS) or in a lower-pct NAICS (LLM adds "
        "signal NAICS-sort misses)?\n\n"
    )

    # Pre-compute SOC's NAICS pct profile for marking.
    for soc, label in SAMPLE_SOCS:
        # Build NAICS → pct_total for this SOC across all OEWS.
        pct_by_naics: dict[str, float] = {}
        for naics, rows_n in _oes._socs_by_naics4.items():
            for r in rows_n:
                if r["soc"] == soc:
                    pct_by_naics[naics] = r.get("pct_total") or 0.0
        # Order NAICS by pct_total to find tiers.
        ranked = sorted(pct_by_naics.items(), key=lambda x: -x[1])
        top_pct = ranked[0][1] if ranked else 0
        top_naics = ranked[0][0] if ranked else None

        llm = llm_per_soc.get(soc, [])
        new = new_per_soc.get(soc, [])[:10]

        out.append(f"\n## `{soc}` {label}\n\n")
        out.append(f"**Top NAICS for this SOC**: `{top_naics}` "
                   f"at {top_pct:.1f}% pct_total\n\n")
        out.append(f"**LLM-curated picks (SD/I + LA)**: {len(llm)} employers\n\n")

        # Group LLM picks by NAICS, annotated with pct_total for this SOC.
        llm_by_naics: dict[str, list[dict]] = defaultdict(list)
        for e in llm:
            llm_by_naics[e["naics"]].append(e)

        out.append("LLM picks grouped by NAICS (with that NAICS's pct_total for this SOC):\n\n")
        out.append("| NAICS | NAICS pct_total for SOC | n employers | Sample names |\n"
                   "|---|---:|---:|---|\n")
        for naics, emps in sorted(llm_by_naics.items(),
                                  key=lambda kv: -pct_by_naics.get(kv[0], 0)):
            pct = pct_by_naics.get(naics, 0)
            in_top = "**TOP**" if naics == top_naics else (
                f"({100*pct/top_pct:.0f}% of top)" if top_pct > 0 else "")
            sample = "; ".join(e["name"] for e in emps[:5])
            out.append(f"| `{naics}` {in_top} | {pct:.1f}% | {len(emps)} | "
                       f"{sample[:100]} |\n")

        # Now the new method's top 10
        out.append("\nTop 10 employers under new method (sort by pct_total desc):\n\n")
        out.append("| pct_total | NAICS | Region | Employer | Also picked by LLM? |\n"
                   "|---:|---|:---:|---|:---:|\n")
        llm_keys = {e["name"].lower().strip() for e in llm}
        for e in new:
            corr = "✓" if e["name"].lower().strip() in llm_keys else " "
            out.append(f"| {e['pct_total']:.1f}% | {e['naics']} | "
                       f"{e['region']} | {e['name']} | {corr} |\n")

        # Diagnosis
        n_llm_in_top_naics = len(llm_by_naics.get(top_naics, []))
        n_llm_total = len(llm)
        out.append("\n**Diagnosis**: ")
        if n_llm_total == 0:
            out.append("LLM made no picks for this SOC — "
                       "new method provides full coverage where LLM had none.\n")
        elif n_llm_in_top_naics / n_llm_total >= 0.7:
            out.append(f"{n_llm_in_top_naics}/{n_llm_total} LLM picks "
                       f"({100*n_llm_in_top_naics/n_llm_total:.0f}%) sit in "
                       f"the top-pct NAICS — LLM is **largely redundant** "
                       f"with NAICS-based selection.\n")
        elif n_llm_in_top_naics / n_llm_total >= 0.3:
            out.append(f"{n_llm_in_top_naics}/{n_llm_total} LLM picks "
                       f"({100*n_llm_in_top_naics/n_llm_total:.0f}%) sit in "
                       f"the top-pct NAICS — LLM and NAICS partially overlap; "
                       f"LLM also picks in lower-pct NAICS.\n")
        else:
            out.append(f"Only {n_llm_in_top_naics}/{n_llm_total} LLM picks "
                       f"({100*n_llm_in_top_naics/n_llm_total:.0f}%) sit in "
                       f"the top-pct NAICS — LLM picks are spread across "
                       f"different NAICS than the top one. **LLM may be "
                       f"adding signal** the NAICS-sort misses.\n")

    Path(out_path).write_text("".join(out))
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main("/app/llm_vs_new_side_by_side.md")
