"""Apply OEWS pct_total threshold filtering to the NAICS-matrix
employer pool, to surface employers in industries where a SOC is a
non-trivial share of the workforce — a BLS-grounded proxy for
partnership candidacy.
"""

from __future__ import annotations

import os

from neo4j import GraphDatabase

from ontology.oes import oes_socs_for_naics4

COLLEGE = "Foothill College"

SAMPLE_SOCS = [
    ("49-9021", "Heating, Air Conditioning, and Refrigeration Mechanics"),
    ("15-1231", "Computer Network Support Specialists"),
    ("17-3023", "Electrical and Electronic Engineering Technologists"),
    ("13-2011", "Accountants and Auditors"),
    ("11-1011", "Chief Executives"),
]
THRESHOLDS = [0.5, 1.0, 2.0, 5.0]


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
                   collect(DISTINCT o.soc_code) AS llm_socs
            """, r=region,
        ).data()
    driver.close()

    print(f"# pct_total threshold filtering — {COLLEGE} ({region})\n")

    # Pre-compute (employer, soc) → pct_total via OEWS NAICS-4 reach.
    emp_soc_pct: dict[tuple[str, str], float] = {}
    emp_naics: dict[str, str] = {}
    for emp in employers:
        emp_naics[emp["name"]] = emp["naics4"]
        socs = oes_socs_for_naics4(emp["naics4"])
        for r in socs:
            emp_soc_pct[(emp["name"], r["soc"])] = r.get("pct_total", 0.0)

    for soc, title in SAMPLE_SOCS:
        # All NAICS-matrix employers (no threshold).
        all_emps = [e for e in employers if (e["name"], soc) in emp_soc_pct]
        print(f"## {soc} — {title}")
        print(f"NAICS-matrix total: {len(all_emps)}")
        print(f"\n  Threshold (pct_total ≥ X) → employer count")
        for thresh in THRESHOLDS:
            kept = [e for e in all_emps
                    if emp_soc_pct[(e["name"], soc)] >= thresh]
            print(f"    ≥ {thresh:.1f}%   : {len(kept):>4}")

        # Show the first 25 employers passing the 1% threshold for inspection.
        kept_1pct = sorted(
            [e for e in all_emps if emp_soc_pct[(e["name"], soc)] >= 1.0],
            key=lambda e: -emp_soc_pct[(e["name"], soc)]
        )
        print(f"\n  Top 25 employers at ≥1.0% (sorted by pct_total desc):")
        for e in kept_1pct[:25]:
            pct = emp_soc_pct[(e["name"], soc)]
            corroborated = "✓" if soc in e["llm_socs"] else " "
            print(f"    [{corroborated}] {pct:>5.1f}%  {e['name']}  "
                  f"(NAICS-4 {e['naics4']})")
        print()


if __name__ == "__main__":
    main()
