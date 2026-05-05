"""Empirical validation: methodology expansion impact for canonical
CTE sectors at San Diego City College.

Strategy:
  1. Identify canonical-sector NAICS (existing in CTE_NAICS_CODES +
     missing NAICS whose pct_total-weighted dominant sector is
     canonical).
  2. Scrape San Diego county at E+ size (the proposed size threshold)
     for that union.
  3. For each returned employer, categorize:
       - "in_graph": already in graph as SD/I-region employer (existing
         F+ pool, no marginal gain)
       - "size_gain": existing NAICS, employer not in graph (gained
         by lowering F→E)
       - "naics_gain": missing NAICS, employer not in graph (gained
         by adding NAICS)
  4. Aggregate per canonical sector.

URL/website filter is NOT applied here — the user wants the pre-filter
view to understand methodology impact. The website filter would prune
~30-50% of these employers downstream.
"""

from __future__ import annotations

import json
import logging
import os
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)

import openpyxl
from neo4j import GraphDatabase

from ontology.crosswalks import (
    _load_cip_to_soc, _load_pcah_cte_top6, _load_top_to_cip,
)
from ontology import oes as _oes
from ontology.oes import oes_socs_for_naics4
from employers.edd_scrape import search_naics_codes, CTE_NAICS_CODES

CANONICAL_SECTORS = {
    "Advanced Manufacturing",
    "Energy, Construction and Utilities",
    "Health",
    "Advanced Transportation and Logistics",
    "Public Safety",
    "Information and Communication Technologies - Digital Media",
    "Agriculture, Water and Environmental Technologies",
}


def _classify_soc_sector() -> dict[str, str]:
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


def _load_naics_titles() -> dict[str, str]:
    wb = openpyxl.load_workbook(_oes.OES_NAICS4_PATH, read_only=True)
    ws = wb.active
    rows = ws.iter_rows(values_only=True)
    header = next(rows)
    cols = {c: i for i, c in enumerate(header)}
    titles: dict[str, str] = {}
    for row in rows:
        if not row: continue
        n = row[cols["NAICS"]]; t = row[cols["NAICS_TITLE"]]
        if n is None or t is None: continue
        s = str(n).strip()
        if len(s) == 6 and s.isdigit():
            titles.setdefault(s[:4], str(t))
    wb.close()
    return titles


def predict_dominant_sector(naics4: str, soc_to_sector: dict[str, str]) -> tuple[str | None, float]:
    """Return (dominant_sector, share_of_pct_total)."""
    rows = oes_socs_for_naics4(naics4)
    sector_w: Counter = Counter()
    total = 0.0
    for r in rows:
        sector = soc_to_sector.get(r["soc"])
        if not sector: continue
        pct = r.get("pct_total") or 0.0
        sector_w[sector] += pct
        total += pct
    if not sector_w: return None, 0.0
    top, w = sector_w.most_common(1)[0]
    return top, w / total if total else 0.0


def main() -> None:
    soc_to_sector = _classify_soc_sector()
    _oes._ensure_loaded()
    naics_titles = _load_naics_titles()

    # All NAICS-4 BLS publishes.
    all_naics = set(_oes._socs_by_naics4.keys())

    # Predict dominant sector for every NAICS, restrict to canonical.
    canonical_naics: dict[str, dict] = {}
    for naics in all_naics:
        sector, share = predict_dominant_sector(naics, soc_to_sector)
        if sector in CANONICAL_SECTORS and share >= 0.4:
            canonical_naics[naics] = {
                "sector": sector,
                "share": share,
                "in_search_list": naics in CTE_NAICS_CODES,
                "title": naics_titles.get(naics, "(no title)"),
            }

    # Pull existing SD/I-region employers from graph.
    driver = GraphDatabase.driver(
        os.environ["NEO4J_URI"],
        auth=(os.environ["NEO4J_USERNAME"], os.environ["NEO4J_PASSWORD"]),
    )
    with driver.session() as session:
        existing = session.run(
            """
            MATCH (e:Employer)-[:IN_MARKET]->(:Region {name: $r})
            RETURN e.name AS name
            """, r="SD/I",
        ).data()
    driver.close()
    existing_names = {e["name"].strip().lower() for e in existing}

    in_list = sum(1 for v in canonical_naics.values() if v["in_search_list"])
    missing = sum(1 for v in canonical_naics.values() if not v["in_search_list"])
    logger.info(f"Canonical NAICS (≥40% pct_total share to a canonical sector): "
                f"{len(canonical_naics)}")
    logger.info(f"  In existing search list: {in_list}")
    logger.info(f"  Missing (would be added by expansion): {missing}")
    logger.info(f"Existing SD/I employers in graph: {len(existing_names)}")

    # Scrape San Diego county at E+ for the union.
    naics_list = sorted(canonical_naics.keys())
    results: dict[str, list[dict]] = {}
    for i, naics in enumerate(naics_list, 1):
        t0 = time.time()
        try:
            employers = search_naics_codes(
                county_name="San Diego",
                naics_codes=[naics],
                min_size="E",
                max_pages_per_code=3,
            )
        except Exception as e:
            results[naics] = []
            logger.warning(f"[{i}/{len(naics_list)}] {naics}: ERROR {e}")
            continue
        results[naics] = employers
        logger.info(f"[{i}/{len(naics_list)}] {naics}: {len(employers)} employers "
                    f"({time.time()-t0:.1f}s)")
        if i % 10 == 0:
            Path("/app/sd_canonical_partial.json").write_text(
                json.dumps({"results": {k: [e.get("name", "?") for e in v]
                                        for k, v in results.items()}}, indent=2)
            )

    # Categorize each (naics, employer) pair.
    by_sector: dict[str, dict] = {
        s: {"in_graph": [], "size_gain": [], "naics_gain": []}
        for s in CANONICAL_SECTORS
    }
    for naics, emps in results.items():
        info = canonical_naics[naics]
        sector = info["sector"]
        is_existing_naics = info["in_search_list"]
        for emp in emps:
            name = (emp.get("name") or "").strip()
            in_graph = name.lower() in existing_names
            entry = {"name": name, "naics": naics,
                     "naics_title": info["title"]}
            if in_graph:
                by_sector[sector]["in_graph"].append(entry)
            elif is_existing_naics:
                by_sector[sector]["size_gain"].append(entry)
            else:
                by_sector[sector]["naics_gain"].append(entry)

    # Output JSON for further analysis.
    out = {
        "canonical_naics_count": len(canonical_naics),
        "existing_naics_in_list": in_list,
        "missing_naics": missing,
        "by_sector": {
            sector: {
                "in_graph_count": len(d["in_graph"]),
                "size_gain_count": len(d["size_gain"]),
                "naics_gain_count": len(d["naics_gain"]),
                "size_gain_sample": d["size_gain"][:15],
                "naics_gain_sample": d["naics_gain"][:15],
            }
            for sector, d in by_sector.items()
        },
    }
    Path("/app/sd_canonical_expansion.json").write_text(json.dumps(out, indent=2))
    logger.info("Wrote /app/sd_canonical_expansion.json")

    print("\n=== Per-canonical-sector breakdown ===")
    print(f"{'Sector':<55} {'In graph':>10} {'Size gain':>10} {'NAICS gain':>11}")
    print("-" * 90)
    for sector in sorted(by_sector.keys()):
        d = by_sector[sector]
        print(f"{sector[:55]:<55} {len(d['in_graph']):>10} "
              f"{len(d['size_gain']):>10} {len(d['naics_gain']):>11}")


if __name__ == "__main__":
    main()
