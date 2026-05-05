"""NAICS-only F+ expansion sanity check using existing scrape data.

Uses oc_F_results.json (Orange County, F+ size, 127 missing NAICS) as
the empirical reference. Groups new employers by SWP sector via the
extended CTE_NAICS_CODES lookup. Augments with SD canonical scrape
(sd_canonical_expansion.json) for the canonical NAICS subset.

Output: per-sector breakdown with sample employer names + CTE industry
and SOC cluster mapping.
"""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

from employers.edd_scrape import CTE_NAICS_CODES
from ontology.oes import oes_socs_for_naics4

# Canonical CTE sectors per the project's framing
CANONICAL = {
    "Advanced Manufacturing",
    "Advanced Transportation and Logistics",
    "Energy, Construction and Utilities",
    "Health",
    "Public Safety",
    "Information and Communication Technologies - Digital Media",
    "Agriculture, Water and Environmental Technologies",
}


def main() -> None:
    print(f"=== NAICS-only F+ expansion — sanity check ===")
    print(f"Source data: Orange County scrape at F+ for 127 missing NAICS\n")

    with open("/app/oc_F_results.json") as f:
        oc_data = json.load(f)

    # oc_data is {naics: [{name, sector, count, sample}]}
    # Re-shape: per-sector employer counts + samples
    by_sector: dict[str, list[dict]] = defaultdict(list)
    by_naics: dict[str, dict] = {}
    sector_employer_set: dict[str, set[str]] = defaultdict(set)

    total_employers = 0
    nonzero_naics = 0
    naics_in_lookup_now = 0

    for naics, info in oc_data.items():
        if not isinstance(info, dict): continue
        count = info.get("count", 0)
        sample = info.get("sample", [])
        by_naics[naics] = {"count": count, "sample": sample}
        if count > 0:
            nonzero_naics += 1
            total_employers += count
        # Map to sectors via lookup (now contains the expansion entries)
        entry = CTE_NAICS_CODES.get(naics)
        if not entry:
            continue
        naics_in_lookup_now += 1
        sectors = entry[2]
        title = entry[1]
        for sector in sectors:
            for name in sample:
                if name and name not in sector_employer_set[sector]:
                    sector_employer_set[sector].add(name)
                    by_sector[sector].append({
                        "name": name, "naics": naics, "naics_title": title,
                    })

    print(f"OC F+ scrape: {nonzero_naics}/{len(oc_data)} NAICS yielded ≥1 F+ employer")
    print(f"Total (NAICS, employer) pairs: {total_employers}")
    print(f"NAICS now in CTE_NAICS_CODES: {naics_in_lookup_now}/{len(oc_data)}\n")

    # Per-sector breakdown
    print(f"=== Per-sector new employers (canonical sectors marked ★) ===\n")
    sector_order = sorted(by_sector.keys(),
                          key=lambda s: -len(by_sector[s]))
    for sector in sector_order:
        emps = by_sector[sector]
        marker = "★" if sector in CANONICAL else " "
        print(f"### {marker} {sector} — {len(emps)} new employers (sample-based)")
        for e in emps[:15]:
            print(f"  - {e['name']}  [NAICS {e['naics']} — {e['naics_title'][:50]}]")
        if len(emps) > 15:
            print(f"  ... (sample shown; full lists in scrape data)")
        print()

    # Now show what canonical CTE SOCs benefit from the NEW NAICS
    print(f"=== Canonical CTE SOCs newly served by these NAICS ===\n")
    print("For the new NAICS, which canonical-CTE-relevant SOCs do they")
    print("publish at meaningful pct_total in OEWS?\n")
    naics_to_top_socs: dict[str, list[tuple[str, float]]] = {}
    for naics in oc_data:
        if naics not in CTE_NAICS_CODES: continue
        rows = oes_socs_for_naics4(naics)
        top = sorted(
            [(r["soc"], r.get("pct_total") or 0.0) for r in rows
             if (r.get("pct_total") or 0.0) > 0],
            key=lambda x: -x[1],
        )[:3]
        if top:
            naics_to_top_socs[naics] = top

    # Sample 12 high-impact NAICS by employer count
    high_impact = sorted(
        [(n, by_naics.get(n, {}).get("count", 0)) for n in naics_to_top_socs],
        key=lambda x: -x[1],
    )[:18]
    for naics, count in high_impact:
        if count == 0: continue
        title = CTE_NAICS_CODES.get(naics, ("", "(?)",))[1]
        sectors = ", ".join(CTE_NAICS_CODES.get(naics, ("", "", []))[2])
        print(f"NAICS {naics} {title[:55]}  ({count} F+ employers)")
        print(f"  Sector tags: {sectors}")
        for soc, pct in naics_to_top_socs[naics]:
            print(f"    SOC {soc}: {pct:.1f}% pct_total")
        print()


if __name__ == "__main__":
    main()
