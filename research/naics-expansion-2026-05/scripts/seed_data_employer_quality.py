"""For each SOC featured in the seed-data partnership reports, query
the new NAICS-OEWS-derived HIRES_FOR pool to assess whether the top
employers per SOC constitute defensible partnership lists.

Output: per (college, SOC) pair:
  - Seed partnership employer (for reference)
  - Top 10 employers from new methodology in the college's region
  - Whether seed employer appears in new pool
  - Sample names for human judgment
"""

from __future__ import annotations

import json
import os
from collections import defaultdict
from pathlib import Path

from neo4j import GraphDatabase

REGION_FOR = {
    "Foothill College": "Bay",
    "Compton College": "LA",
    "San Diego City College": "SD/I",
    "College of the Sequoias": "CVML",
    "College of the Desert": "IE/D",
    "Oxnard College": "SCC",
    "Shasta College": "FN",
    "Irvine Valley College": "OC",
}


def main() -> None:
    seed_path = Path("/app/seededPartnerships.json")
    seed = json.loads(seed_path.read_text())

    driver = GraphDatabase.driver(
        os.environ["NEO4J_URI"],
        auth=(os.environ["NEO4J_USERNAME"], os.environ["NEO4J_PASSWORD"]),
    )

    with driver.session() as session:
        for college, partnerships in seed.items():
            region = REGION_FOR.get(college)
            if not region: continue
            print(f"\n{'='*78}")
            print(f"## {college}  (region: {region})")
            print(f"{'='*78}")

            for p in partnerships:
                proposal = p["proposal"]
                soc = proposal["selected_soc_code"]
                seed_emp = proposal["employer"]
                seed_occupation = proposal["selected_occupation"]

                print(f"\n### `{soc}` {seed_occupation}")
                print(f"   Seed partnership employer: **{seed_emp}**")

                # Top employers from new HIRES_FOR pool, sorted by pct_total
                rows = session.run(
                    """
                    MATCH (e:Employer)-[h:HIRES_FOR]->(o:Occupation {soc_code: $soc})
                    MATCH (e)-[:IN_MARKET]->(:Region {name: $region})
                    OPTIONAL MATCH (e)-[ih:IDENTITY_HIRES_FOR]->(o)
                    RETURN e.name AS name, e.naics4 AS naics4,
                           h.pct_total AS pct_total,
                           ih IS NOT NULL AS llm_corroborated
                    ORDER BY h.pct_total DESC, e.name
                    LIMIT 10
                    """, soc=soc, region=region,
                ).data()

                if not rows:
                    print(f"   ⚠ No HIRES_FOR edges for SOC {soc} in {region}")
                    continue

                # Check if seed employer appears anywhere in pool
                full_pool = session.run(
                    """
                    MATCH (e:Employer)-[:HIRES_FOR]->(o:Occupation {soc_code: $soc})
                    MATCH (e)-[:IN_MARKET]->(:Region {name: $region})
                    RETURN e.name AS name
                    """, soc=soc, region=region,
                ).data()
                pool_names = {r["name"].lower().strip() for r in full_pool}
                seed_in_pool = seed_emp.lower().strip() in pool_names
                print(f"   Pool size in {region}: {len(pool_names)}")
                if seed_in_pool:
                    print(f"   Seed employer in new pool: ✓")
                else:
                    print(f"   Seed employer in new pool: ✗  (not in scrape-loaded set)")

                print(f"   Top 10 by pct_total under new methodology:")
                for r in rows:
                    mark = "✓" if r["llm_corroborated"] else " "
                    is_seed = " ← seed" if r["name"].lower().strip() == seed_emp.lower().strip() else ""
                    print(f"     [{mark}] {r['pct_total']:>5.1f}%  {r['name']:<40}  "
                          f"NAICS-{r['naics4']}{is_seed}")

    driver.close()


if __name__ == "__main__":
    main()
