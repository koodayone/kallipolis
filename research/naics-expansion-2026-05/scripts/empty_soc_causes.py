"""Diagnose why supported SOCs end up empty under NAICS ≥1%:
- Structurally dispersed (no NAICS publishes at ≥1% nationally)
- Regional industry gap (≥1% NAICS exist but none in Bay pool)
- Just below threshold (pct_total in 0.5-1.0% range in regional pool)
"""

from __future__ import annotations

import os
from pathlib import Path

from neo4j import GraphDatabase

from ontology import oes as _oes
from ontology.oes import oes_socs_for_naics4

COLLEGE = "Foothill College"
THRESHOLD = 1.0


def main(out_path: str) -> None:
    _oes._ensure_loaded()
    soc_max_pct: dict[str, float] = {}
    soc_naics_at_threshold: dict[str, list[tuple[str, float]]] = {}
    for naics4, rows in _oes._socs_by_naics4.items():
        for r in rows:
            soc = r["soc"]
            pct = r.get("pct_total") or 0.0
            soc_max_pct[soc] = max(soc_max_pct.get(soc, 0.0), pct)
            if pct >= THRESHOLD:
                soc_naics_at_threshold.setdefault(soc, []).append((naics4, pct))
    for store, _key_len in [(_oes._socs_by_naics3, 3), (_oes._socs_by_naics2, 2)]:
        for naics_key, rows in store.items():
            for r in rows:
                soc = r["soc"]
                pct = r.get("pct_total") or 0.0
                soc_max_pct[soc] = max(soc_max_pct.get(soc, 0.0), pct)
                if pct >= THRESHOLD:
                    soc_naics_at_threshold.setdefault(soc, []).append((naics_key, pct))

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
            RETURN DISTINCT e.naics4 AS naics4
            """, r=region,
        ).data()
        regional_naics = {e["naics4"] for e in emps}
    driver.close()

    # Per supported SOC: classify why it's empty under ≥1%.
    empty: list[dict] = []
    served: list[str] = []
    for soc, title in supported_socs.items():
        # Is the SOC reached by any regional employer at ≥1%?
        served_by_regional = False
        max_regional_pct = 0.0
        regional_at_threshold: list[tuple[str, float]] = []
        for n4 in regional_naics:
            for r in oes_socs_for_naics4(n4):
                if r["soc"] != soc:
                    continue
                pct = r.get("pct_total") or 0.0
                max_regional_pct = max(max_regional_pct, pct)
                if pct >= THRESHOLD:
                    served_by_regional = True
                    regional_at_threshold.append((n4, pct))
        if served_by_regional:
            served.append(soc)
            continue
        empty.append({
            "soc": soc,
            "title": title,
            "max_regional_pct": max_regional_pct,
            "max_global_pct": soc_max_pct.get(soc, 0.0),
            "global_at_threshold": soc_naics_at_threshold.get(soc, []),
        })

    # Categorize.
    cat_a = []  # Structurally dispersed: max_global_pct < 1%
    cat_b = []  # Regional gap: max_global ≥ 1%, but regional NAICS don't include those
    cat_c = []  # Just below: max_regional_pct in [0.5, 1.0)
    for r in empty:
        if r["max_global_pct"] < THRESHOLD:
            cat_a.append(r)
        elif r["max_regional_pct"] >= 0.5:
            cat_c.append(r)
        else:
            cat_b.append(r)

    out: list[str] = []
    out.append(f"# Empty-SOC Diagnosis — {COLLEGE} ({region} region)\n\n")
    out.append(
        f"For each supported SOC at Foothill that ends up with zero "
        f"candidates under NAICS ≥{THRESHOLD}%, classifies the cause:\n\n"
        f"- **A: Structurally dispersed** — no NAICS publishes the SOC at "
        f"≥{THRESHOLD}% anywhere. The SOC is not partnership-amenable "
        f"under this methodology in any region.\n"
        f"- **B: Regional industry gap** — NAICS exist at ≥{THRESHOLD}% "
        f"globally, but those NAICS aren't in the Bay region's "
        f"employer pool. Other regions (or a future expansion of "
        f"this region's scrape) might surface candidates.\n"
        f"- **C: Just-below threshold** — the regional pool reaches "
        f"the SOC at 0.5–1.0%, falling just short of the bar. Could "
        f"be reconsidered with a slightly looser threshold.\n\n"
    )
    out.append(
        f"## Summary\n\n"
        f"| Cause | SOCs | Pct of empty |\n|---|---:|---:|\n"
        f"| A: Structurally dispersed | {len(cat_a)} | "
        f"{100*len(cat_a)/len(empty):.1f}% |\n"
        f"| B: Regional industry gap | {len(cat_b)} | "
        f"{100*len(cat_b)/len(empty):.1f}% |\n"
        f"| C: Just below threshold | {len(cat_c)} | "
        f"{100*len(cat_c)/len(empty):.1f}% |\n"
        f"| **Total empty SOCs** | **{len(empty)}** | |\n\n"
    )

    out.append(f"## A — Structurally dispersed ({len(cat_a)})\n\n")
    out.append(
        "These SOCs have no NAICS where pct_total reaches 1% nationally. "
        "Generalist or rare roles. Even with the full state's employer "
        "pool, this method would never surface candidates.\n\n"
    )
    out.append("| SOC | Title | Max NAICS pct_total (any) |\n"
               "|---|---|---:|\n")
    for r in sorted(cat_a, key=lambda r: -r["max_global_pct"]):
        out.append(f"| `{r['soc']}` | {r['title']} | "
                   f"{r['max_global_pct']:.2f}% |\n")

    out.append(f"\n## B — Regional industry gap ({len(cat_b)})\n\n")
    out.append(
        "These SOCs have NAICS at ≥1% somewhere, but the Bay region "
        "doesn't have employers in those NAICS. Other regions or "
        "broader employer scrapes could surface candidates.\n\n"
    )
    out.append("| SOC | Title | NAICS at ≥1% globally |\n|---|---|---|\n")
    for r in sorted(cat_b, key=lambda r: r["soc"]):
        naics_list = sorted(r["global_at_threshold"], key=lambda x: -x[1])[:5]
        s = "; ".join(f"`{n}` ({p:.1f}%)" for n, p in naics_list)
        if len(r["global_at_threshold"]) > 5:
            s += f" + {len(r['global_at_threshold']) - 5} more"
        out.append(f"| `{r['soc']}` | {r['title']} | {s} |\n")

    out.append(f"\n## C — Just below threshold ({len(cat_c)})\n\n")
    out.append(
        "These SOCs have regional NAICS reaching them at 0.5–1.0% — "
        "near miss. A looser threshold would surface candidates here, "
        "at the cost of admitting more noise.\n\n"
    )
    out.append("| SOC | Title | Max regional pct_total |\n|---|---|---:|\n")
    for r in sorted(cat_c, key=lambda r: -r["max_regional_pct"]):
        out.append(f"| `{r['soc']}` | {r['title']} | "
                   f"{r['max_regional_pct']:.2f}% |\n")

    Path(out_path).write_text("".join(out))
    print(f"Wrote {out_path}")
    print(f"  Empty SOCs: {len(empty)}")
    print(f"  A (structurally dispersed): {len(cat_a)}")
    print(f"  B (regional industry gap): {len(cat_b)}")
    print(f"  C (just below threshold): {len(cat_c)}")


if __name__ == "__main__":
    main("/app/empty_soc_causes.md")
