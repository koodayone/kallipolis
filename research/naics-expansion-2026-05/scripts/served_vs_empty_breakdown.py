"""Comprehensive served-vs-empty SOC breakdown for Foothill, NAICS ≥1%.
Renders the full served list (sorted by candidate count) and the full
empty list (grouped by cause A/B/C) so the empty-bucket damage can be
judged directly.
"""

from __future__ import annotations

import csv
import os
from pathlib import Path

from neo4j import GraphDatabase

from ontology import oes as _oes
from ontology.crosswalks import COE_DEMAND_PATH
from ontology.oes import oes_socs_for_naics4

COLLEGE = "Foothill College"
THRESHOLD = 1.0


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
    soc_max_global: dict[str, float] = {}
    for store in [_oes._socs_by_naics4, _oes._socs_by_naics3, _oes._socs_by_naics2]:
        for rows in store.values():
            for r in rows:
                soc = r["soc"]
                pct = r.get("pct_total") or 0.0
                soc_max_global[soc] = max(soc_max_global.get(soc, 0.0), pct)

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
            RETURN DISTINCT e.naics4 AS n
            """, r=region,
        ).data()
        regional_naics = {e["n"] for e in emps}
    driver.close()

    counts: dict[str, int] = {}
    max_regional_pct: dict[str, float] = {}
    for n4 in regional_naics:
        for r in oes_socs_for_naics4(n4):
            soc = r["soc"]
            if soc not in supported_socs:
                continue
            pct = r.get("pct_total") or 0.0
            max_regional_pct[soc] = max(max_regional_pct.get(soc, 0.0), pct)
            if pct >= THRESHOLD:
                counts[soc] = counts.get(soc, 0) + 1

    served = [s for s in supported_socs if counts.get(s, 0) > 0]
    empty = [s for s in supported_socs if counts.get(s, 0) == 0]

    cat_a, cat_b, cat_c = [], [], []
    for s in empty:
        if soc_max_global.get(s, 0.0) < THRESHOLD:
            cat_a.append(s)
        elif max_regional_pct.get(s, 0.0) >= 0.5:
            cat_c.append(s)
        else:
            cat_b.append(s)

    out: list[str] = []
    out.append(f"# Served vs Empty — {COLLEGE}, NAICS ≥{THRESHOLD}%\n\n")
    out.append(
        f"- Curriculum-supported SOCs: **{len(supported_socs)}**\n"
        f"- Served (≥1 candidate): **{len(served)}** "
        f"({100*len(served)/len(supported_socs):.1f}%)\n"
        f"- Empty: **{len(empty)}**\n"
        f"  - A — Structurally dispersed: {len(cat_a)}\n"
        f"  - B — Regional industry gap: {len(cat_b)}\n"
        f"  - C — Just below threshold: {len(cat_c)}\n\n"
    )

    out.append(f"## Served SOCs ({len(served)}) — sorted by candidate count\n\n")
    out.append("| SOC | Title | Band | Candidates |\n|---|---|---|---:|\n")
    for soc in sorted(served, key=lambda s: (-counts[s], s)):
        out.append(
            f"| `{soc}` | {supported_socs[soc]} | "
            f"{_band(edu_by_soc.get(soc, ''))} | {counts[soc]} |\n"
        )

    out.append(f"\n## Empty SOCs — Bucket A: structurally dispersed ({len(cat_a)})\n\n")
    out.append(
        "These would not surface candidates in any region. Sorted by max "
        "global pct_total descending — those nearest 1% are the closest "
        "near-misses.\n\n"
    )
    out.append("| SOC | Title | Band | Max global pct |\n|---|---|---|---:|\n")
    for soc in sorted(cat_a, key=lambda s: -soc_max_global.get(s, 0.0)):
        out.append(
            f"| `{soc}` | {supported_socs[soc]} | "
            f"{_band(edu_by_soc.get(soc, ''))} | "
            f"{soc_max_global.get(soc, 0.0):.2f}% |\n"
        )

    out.append(f"\n## Empty SOCs — Bucket B: regional industry gap ({len(cat_b)})\n\n")
    out.append("Concentrated in industries not represented in Bay region's pool.\n\n")
    out.append("| SOC | Title | Band |\n|---|---|---|\n")
    for soc in sorted(cat_b):
        out.append(
            f"| `{soc}` | {supported_socs[soc]} | "
            f"{_band(edu_by_soc.get(soc, ''))} |\n"
        )

    out.append(f"\n## Empty SOCs — Bucket C: just below threshold ({len(cat_c)})\n\n")
    out.append("| SOC | Title | Band | Max regional pct |\n|---|---|---|---:|\n")
    for soc in sorted(cat_c, key=lambda s: -max_regional_pct.get(s, 0.0)):
        out.append(
            f"| `{soc}` | {supported_socs[soc]} | "
            f"{_band(edu_by_soc.get(soc, ''))} | "
            f"{max_regional_pct.get(soc, 0.0):.2f}% |\n"
        )

    Path(out_path).write_text("".join(out))
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main("/app/served_vs_empty_breakdown.md")
