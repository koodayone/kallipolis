"""Side-by-side per-SOC comparison: LLM-curated employers vs
NAICS-matrix ≥1% pct_total employers, for a single college, across a
range of SOCs spanning the CTE-relevance spectrum.

For each SOC: shows the LLM list, the ≥1% list, the overlap, and a
qualitative read on whether the methods are agreeing, complementary, or
diverging.
"""

from __future__ import annotations

import csv
import os
from pathlib import Path

from neo4j import GraphDatabase

from ontology.crosswalks import COE_DEMAND_PATH
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


def main(out_path: str) -> None:
    edu_by_soc = _load_education_for_socs()
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

    # Build per-SOC sets.
    llm_by_soc: dict[str, set[str]] = {}
    naics_by_soc: dict[str, list[tuple[str, float]]] = {}
    for emp in employers:
        for soc in emp["llm_socs"]:
            if soc in supported_socs:
                llm_by_soc.setdefault(soc, set()).add(emp["name"])
        oes = oes_socs_for_naics4(emp["naics4"])
        for r in oes:
            if r["soc"] in supported_socs:
                pct = r.get("pct_total") or 0.0
                if pct >= THRESHOLD:
                    naics_by_soc.setdefault(r["soc"], []).append(
                        (emp["name"], pct)
                    )

    # Pick SOCs spanning the spectrum:
    #  - both methods agree heavily
    #  - LLM only (filter loses)
    #  - NAICS only (LLM loses)
    #  - high overlap, large list
    #  - one Strong CTE, one Moderate CTE, one Bachelor's
    samples = [
        # (soc, label)
        ("49-9021", "Strong CTE: HVAC Mechanics"),
        ("17-3023", "Strong CTE: Electrical/Electronic Engineering Techs"),
        ("29-1141", "Strong CTE: Registered Nurses"),
        ("47-2031", "Strong CTE: Carpenters"),
        ("29-2042", "Strong CTE: EMTs (LLM missed)"),
        ("43-3031", "Moderate CTE: Bookkeeping clerks (LLM missed)"),
        ("15-1232", "Moderate CTE: Computer User Support (LLM missed)"),
        ("43-6013", "Moderate CTE: Medical Secretaries (LLM missed)"),
        ("13-2011", "Bachelor's: Accountants (cross-cutting)"),
        ("15-1252", "Bachelor's: Software Developers (LLM-strong)"),
        ("11-9021", "Bachelor's: Construction Managers"),
        ("11-1011", "Bachelor's: Chief Executives (both fail)"),
    ]

    out: list[str] = []
    out.append(f"# Method Side-by-Side: {COLLEGE} ({region} region)\n\n")
    out.append(
        f"For each SOC: comparing LLM-curated employer list vs "
        f"NAICS-matrix at pct_total ≥ {THRESHOLD}%. The third column "
        f"shows the overlap so you can read the actual methodological "
        f"agreement on real candidate lists.\n\n"
    )

    for soc, label in samples:
        title = supported_socs.get(soc, "(not in supported set)")
        edu = edu_by_soc.get(soc, "")
        llm = sorted(llm_by_soc.get(soc, set()))
        naics_pairs = sorted(naics_by_soc.get(soc, []),
                             key=lambda x: -x[1])
        naics = [n for n, _ in naics_pairs]
        naics_set = set(naics)
        llm_set = set(llm)
        both = llm_set & naics_set
        llm_only = llm_set - naics_set
        naics_only = naics_set - llm_set

        out.append(f"\n## `{soc}` — {title}\n")
        out.append(f"*{label} · entry: {edu}*\n\n")
        out.append(
            f"- LLM-curated: **{len(llm)}** employers\n"
            f"- NAICS ≥{THRESHOLD}%: **{len(naics)}** employers\n"
            f"- In both: **{len(both)}**\n"
            f"- LLM-only: **{len(llm_only)}**\n"
            f"- NAICS-only: **{len(naics_only)}**\n\n"
        )

        out.append("| LLM-curated | NAICS ≥1% (top 20 by pct_total) |\n"
                   "|---|---|\n")
        # Render side-by-side. Mark overlap with ✓.
        max_rows = max(len(llm), min(20, len(naics)))
        naics_display = naics_pairs[:20]
        for i in range(max_rows):
            l = ""
            if i < len(llm):
                e = llm[i]
                mark = "✓" if e in naics_set else " "
                l = f"[{mark}] {e}"
            n = ""
            if i < len(naics_display):
                e, pct = naics_display[i]
                mark = "✓" if e in llm_set else " "
                n = f"[{mark}] {pct:>4.1f}%  {e}"
            out.append(f"| {l} | {n} |\n")
        if len(naics) > 20:
            out.append(f"| | ... and {len(naics) - 20} more |\n")

    Path(out_path).write_text("".join(out))
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main("/app/method_side_by_side.md")
