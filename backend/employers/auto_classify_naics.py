"""Auto-classify expansion NAICS-4 codes to SWP sectors via pct_total.

For each NAICS-4 not already in CTE_NAICS_CODES that appears as a
top-N (by pct_total) NAICS for any direct-CTE supported SOC: compute
the SWP sector profile (pct_total weighted by SOC→TOP→PCAH sector),
assign primary sector and secondary sectors above a relative
threshold, emit a Python dict-literal extension ready to drop into
edd_scrape.CTE_NAICS_CODES.

Plus the 6 Public Administration NAICS (9211, 9221, 9231, 9251, 9261,
9281) — these surface real government employers in EDD but were
excluded from the prior PCAH-curated list because OEWS publishes
Public Administration workforce composition under synthetic 999X
aggregates rather than standard 92XX codes.

Usage:
    python -m employers.auto_classify_naics > /tmp/extension.txt
"""

from __future__ import annotations

import csv
from collections import Counter, defaultdict

from neo4j import GraphDatabase
import os

from ontology.crosswalks import (
    COE_DEMAND_PATH, _load_cip_to_soc, _load_pcah_cte_top6, _load_top_to_cip,
)
from ontology import oes as _oes
from ontology.oes import oes_socs_for_naics4
from employers.edd_scrape import CTE_NAICS_CODES

TOP_N_PER_SOC = 5
SECONDARY_SECTOR_RELATIVE_THRESHOLD = 0.30  # ≥30% of primary's weight

# Public Administration NAICS that surface real government employers
# in EDD but aren't in the PCAH-derived sector lookup (PCAH classifies
# TOPs, not NAICS, and OEWS publishes Public Admin under 999X aggregates).
PUBLIC_ADMIN_NAICS = {
    "9211": ("92", "Public Administration - Executive/Legislative/General Government", ["Public Safety", "Education and Human Development"]),
    "9221": ("92", "Public Administration - Justice/Public Order/Safety", ["Public Safety"]),
    "9231": ("92", "Public Administration - Human Resource Programs", ["Education and Human Development"]),
    "9251": ("92", "Public Administration - Housing/Urban Programs", ["Energy, Construction and Utilities"]),
    "9261": ("92", "Public Administration - Economic Programs", ["Business and Entrepreneurship"]),
    "9281": ("92", "Public Administration - National Security", ["Public Safety"]),
}


def _load_naics_titles() -> dict[str, str]:
    import openpyxl
    titles: dict[str, str] = {}
    for path in (_oes.OES_NAICS4_PATH, _oes.OES_NAICS3_PATH, _oes.OES_NAICS2_PATH):
        wb = openpyxl.load_workbook(path, read_only=True)
        ws = wb.active
        rows = ws.iter_rows(values_only=True)
        header = next(rows)
        cols = {c: i for i, c in enumerate(header)}
        for row in rows:
            if not row: continue
            n = row[cols["NAICS"]]; t = row[cols["NAICS_TITLE"]]
            if n is None or t is None: continue
            s = str(n).strip()
            if len(s) == 6 and s.isdigit():
                titles.setdefault(s[:4], str(t))
            else:
                titles.setdefault(s, str(t))
        wb.close()
    return titles


def _classify_soc_sector() -> dict[str, str]:
    """SOC → plurality-winning SWP sector via TOP6→PCAH."""
    top6_to_sector = _load_pcah_cte_top6()
    top_cip = _load_top_to_cip()
    cip_soc = _load_cip_to_soc()
    soc_to_tops: dict[str, set[str]] = {}
    for top6, cips in top_cip.items():
        for cip in cips:
            for soc in cip_soc.get(cip, set()):
                soc_to_tops.setdefault(soc, set()).add(top6)
    out: dict[str, str] = {}
    for soc, tops in soc_to_tops.items():
        votes: Counter = Counter()
        for t in tops:
            sector = top6_to_sector.get(t)
            if sector:
                votes[sector] += 1
        if votes:
            out[soc] = votes.most_common(1)[0][0]
    return out


def _direct_cte_supported_socs() -> set[str]:
    edu: dict[str, str] = {}
    with open(COE_DEMAND_PATH, newline="") as f:
        for row in csv.DictReader(f):
            if row["SOC"] and row.get("Typical Entry Level Education"):
                edu.setdefault(row["SOC"], row["Typical Entry Level Education"].strip())
    direct = {
        soc for soc, level in edu.items()
        if level in {"Postsecondary nondegree award", "Associate's degree",
                     "High school diploma or equivalent",
                     "Some college, no degree",
                     "No formal educational credential"}
    }
    driver = GraphDatabase.driver(
        os.environ["NEO4J_URI"],
        auth=(os.environ["NEO4J_USERNAME"], os.environ["NEO4J_PASSWORD"]),
    )
    with driver.session() as session:
        rows = session.run(
            "MATCH (:Course)-[:PREPARES_FOR]->(o:Occupation) "
            "RETURN DISTINCT o.soc_code AS soc"
        ).data()
    driver.close()
    return direct & {r["soc"] for r in rows}


def _predict_sectors(naics4: str, soc_to_sector: dict[str, str]) -> list[str]:
    """Predict SWP sector list for a NAICS-4 via pct_total-weighted
    SOC→sector aggregation. Primary = highest weight; secondary =
    sectors above the relative threshold."""
    rows = oes_socs_for_naics4(naics4)
    sector_w: Counter = Counter()
    for r in rows:
        sector = soc_to_sector.get(r["soc"])
        # 'Unassigned' is a PCAH placeholder for non-CTE TOPs and is
        # not a real SWP sector — exclude it from auto-classification
        # so it doesn't pollute employer sector tags.
        if not sector or sector == "Unassigned": continue
        sector_w[sector] += (r.get("pct_total") or 0.0)
    if not sector_w: return []
    ranked = sector_w.most_common()
    primary_w = ranked[0][1]
    if primary_w <= 0: return []
    out = [ranked[0][0]]
    for sector, w in ranked[1:]:
        if w / primary_w >= SECONDARY_SECTOR_RELATIVE_THRESHOLD:
            out.append(sector)
    return out


def main() -> None:
    _oes._ensure_loaded()
    soc_to_sector = _classify_soc_sector()
    naics_titles = _load_naics_titles()
    direct_socs = _direct_cte_supported_socs()

    soc_to_naics: dict[str, list[tuple[str, float]]] = defaultdict(list)
    for naics4, rows in _oes._socs_by_naics4.items():
        for r in rows:
            pct = r.get("pct_total") or 0.0
            if pct > 0:
                soc_to_naics[r["soc"]].append((naics4, pct))
    for soc in soc_to_naics:
        soc_to_naics[soc].sort(key=lambda x: -x[1])

    expansion_naics: set[str] = set()
    for soc in direct_socs:
        for naics, _ in soc_to_naics.get(soc, [])[:TOP_N_PER_SOC]:
            if naics not in CTE_NAICS_CODES:
                expansion_naics.add(naics)

    extension: dict[str, tuple[str, str, list[str]]] = {}

    # First: auto-classified expansion NAICS via pct_total prediction
    for naics in sorted(expansion_naics):
        sectors = _predict_sectors(naics, soc_to_sector)
        if not sectors: continue  # NAICS with no CTE-classified SOCs
        title = naics_titles.get(naics, "(no BLS title)")
        extension[naics] = (naics[:2], title, sectors)

    # Second: hand-mapped Public Admin NAICS (defensible from each
    # NAICS's institutional definition, not derivable from OEWS since
    # OEWS aggregates Public Admin under 999X)
    for naics, entry in PUBLIC_ADMIN_NAICS.items():
        if naics not in CTE_NAICS_CODES:
            extension[naics] = entry

    # Emit as Python dict-literal block ready to paste into
    # CTE_NAICS_CODES (alphabetical/numerical by NAICS).
    print(f"# CTE_NAICS_CODES extension: {len(extension)} new entries")
    print(f"# - {len(expansion_naics)} top-N missing NAICS auto-classified via pct_total")
    print(f"# - {len(PUBLIC_ADMIN_NAICS)} Public Administration NAICS (manual mapping)")
    print()
    for naics, (sect, label, sectors) in sorted(extension.items()):
        sector_repr = ", ".join(repr(s) for s in sectors)
        print(f'    "{naics}": ("{sect}", {label!r}, [{sector_repr}]),')


if __name__ == "__main__":
    main()
