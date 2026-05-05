"""For a sample of SOCs at one college, list every regional employer
that would link to it under the NAICS-matrix association, so a human
can scan and judge whether each (employer, SOC) pair is defensible.

For each SOC: prints up to 25 regional employers with their NAICS-4,
description, and current LLM-curated SOC set. The LLM-curated column
is included as context — if an employer with HVAC Mechanics in its
NAICS reach also has it in its LLM picks, that's strong corroboration.
If only NAICS reaches it, the description is the read.
"""

from __future__ import annotations

import os
from collections import defaultdict

from neo4j import GraphDatabase

from ontology.oes import oes_socs_for_naics4

COLLEGE = "Foothill College"

# A spread across the CTE relevance spectrum, picked from earlier
# analysis. Strong CTE: classic CCC training pathways. Cross-cutting:
# the cleanest test of "every employer hires accountants" defensibility.
# Weak CTE: the case where a long employer list is most likely to read
# as noise.
SAMPLE_SOCS = [
    ("49-9021", "Heating, Air Conditioning, and Refrigeration Mechanics",
     "Strong CTE"),
    ("15-1231", "Computer Network Support Specialists", "Strong CTE"),
    ("17-3023", "Electrical and Electronic Engineering Technologists",
     "Strong CTE"),
    ("13-2011", "Accountants and Auditors", "Cross-cutting bachelor's"),
    ("11-1011", "Chief Executives", "Weak CTE / cross-cutting"),
]

PER_SOC_LIMIT = 25


def main() -> None:
    driver = GraphDatabase.driver(
        os.environ["NEO4J_URI"],
        auth=(os.environ["NEO4J_USERNAME"], os.environ["NEO4J_PASSWORD"]),
    )
    with driver.session() as session:
        region = session.run(
            "MATCH (c:College {name: $n})-[:IN_MARKET]->(r:Region) "
            "RETURN r.name AS name", n=COLLEGE,
        ).single()["name"]

        employers = session.run(
            """
            MATCH (e:Employer)-[:IN_MARKET]->(:Region {name: $r})
            WHERE e.naics4 IS NOT NULL
            OPTIONAL MATCH (e)-[:HIRES_FOR]->(o:Occupation)
            RETURN e.name AS name, e.naics4 AS naics4,
                   e.description AS description,
                   collect(DISTINCT o.soc_code) AS llm_socs
            """, r=region,
        ).data()
    driver.close()

    # Build NAICS-matrix membership for each SOC of interest.
    soc_to_employers: dict[str, list[dict]] = defaultdict(list)
    for emp in employers:
        oes = oes_socs_for_naics4(emp["naics4"])
        if not oes:
            continue
        oes_socs = {r["soc"] for r in oes}
        for soc, _, _ in SAMPLE_SOCS:
            if soc in oes_socs:
                soc_to_employers[soc].append(emp)

    print(f"# Employer Defensibility Scan — {COLLEGE} ({region} region)\n")
    print(f"NAICS-matrix association: an employer 'hires for' a SOC if "
          f"that SOC appears in the BLS OEWS Industry-Occupation Matrix "
          f"row for the employer's NAICS-4.\n")

    for soc, title, band in SAMPLE_SOCS:
        emps = soc_to_employers[soc]
        print(f"\n## {soc} — {title}  [{band}]\n")
        print(f"Regional employers under NAICS-matrix: {len(emps)}\n")
        if not emps:
            continue
        # Sort: those with the SOC also in their LLM-curated set first
        # (high-confidence corroborated), then alphabetic.
        emps.sort(key=lambda e: (soc not in e["llm_socs"], e["name"]))
        shown = emps[:PER_SOC_LIMIT]
        for e in shown:
            corroborated = "✓" if soc in e["llm_socs"] else " "
            desc = (e["description"] or "")[:140]
            print(f"  [{corroborated}] {e['name']}  (NAICS-4 {e['naics4']})")
            if desc:
                print(f"      {desc}")
        if len(emps) > PER_SOC_LIMIT:
            print(f"\n  ... and {len(emps) - PER_SOC_LIMIT} more")


if __name__ == "__main__":
    main()
