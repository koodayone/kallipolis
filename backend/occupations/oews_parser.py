"""
Parse EDD OEWS XLSX files into a structured JSON of occupations per region.

Usage:
    python -m pipeline.industry.oews_parser /path/to/oews-xlsx-dir
"""

import json
import sys
import logging
from pathlib import Path

import openpyxl

logger = logging.getLogger(__name__)

METROS = {
    # Bay Area
    "San Jose-Sunnyvale-Santa Clara": "CA-OEWS-San Jose-Sunnyvale-Santa Clara MSA-2025.xlsx",
    "Oakland-Fremont-Berkeley": "CA-OEWS-Oakland-Fremont-Berkeley MD-2025.xlsx",
    "San Francisco-San Mateo-Redwood City": "CA-OEWS-San Francisco-San Mateo-Redwood City MD-2025.xlsx",
    "Santa Rosa-Petaluma": "CA-OEWS-Santa Rosa-Petaluma MSA-2025.xlsx",
    "Napa": "CA-OEWS-Napa MSA-2025.xlsx",
    "Vallejo": "CA-OEWS-Vallejo MSA-2025.xlsx",
    "Santa Cruz-Watsonville": "CA-OEWS-Santa Cruz-Watsonville MSA-2025.xlsx",
    "San Rafael": "CA-OEWS-San Rafael MD-2025.xlsx",
    # Los Angeles / Southern California
    "Los Angeles-Long Beach-Glendale": "CA-OEWS-Los Angeles-Long Beach-Glendale MD-2025.xlsx",
    "Anaheim-Santa Ana-Irvine": "CA-OEWS-Anaheim-Santa Ana-Irvine MD-2025.xlsx",
    "Riverside-San Bernardino-Ontario": "CA-OEWS-Riverside-San Bernardino-Ontario MSA-2025.xlsx",
    "Oxnard-Thousand Oaks-Ventura": "CA-OEWS-Oxnard-Thousand Oaks-Ventura MSA-2025.xlsx",
    "San Diego-Chula Vista-Carlsbad": "CA-OEWS-San Diego-Chula Vista-Carlsbad MSA-2025.xlsx",
    # Central Valley
    "Fresno": "CA-OEWS-Fresno MSA-2025.xlsx",
    "Bakersfield-Delano": "CA-OEWS-Bakersfield-Delano MSA-2025.xlsx",
    "Stockton-Lodi": "CA-OEWS-Stockton-Lodi MSA-2025.xlsx",
    "Modesto": "CA-OEWS-Modesto MSA-2025.xlsx",
    "Visalia": "CA-OEWS-Visalia MSA-2025.xlsx",
    "Merced": "CA-OEWS-Merced MSA-2025.xlsx",
    "Hanford-Corcoran": "CA-OEWS-Hanford-Corcoran MSA-2025.xlsx",
    # Sacramento / Northern California
    "Sacramento-Roseville-Folsom": "CA-OEWS-Sacramento-Roseville-Folsom MSA-2025.xlsx",
    "Chico": "CA-OEWS-Chico MSA-2025.xlsx",
    "Redding": "CA-OEWS-Redding MSA-2025.xlsx",
    "Yuba City": "CA-OEWS-Yuba City MSA-2025.xlsx",
    # Central / South Coast
    "Salinas": "CA-OEWS-Salinas MSA-2025.xlsx",
    "San Luis Obispo-Paso Robles": "CA-OEWS-San Luis Obispo-Paso Robles MSA-2025.xlsx",
    "Santa Maria-Santa Barbara": "CA-OEWS-Santa Maria-Santa Barbara MSA-2025.xlsx",
    # Other / Imperial
    "El Centro": "CA-OEWS-El Centro MSA-2025.xlsx",
    # Rural regions
    "Eastern Sierra-Mother Lode": "CA-OEWS-Eastern Sierra-Mother Lode Region-2025.xlsx",
    "North Coast": "CA-OEWS-North Coast Region-2025.xlsx",
    "North Valley-Northern Mountains": "CA-OEWS-North Valley-Northern Mountains Region-2025.xlsx",
}


def parse_oews_file(filepath: Path, region_name: str) -> list[dict]:
    """Parse a single OEWS XLSX file, returning detailed occupation rows."""
    wb = openpyxl.load_workbook(filepath, read_only=True)
    ws = wb["OEWS Data"]

    occupations = []
    for i, row in enumerate(ws.iter_rows(values_only=True)):
        if i < 8:
            continue
        soc_code = row[2]
        if not soc_code or not isinstance(soc_code, str):
            continue
        # Skip broad categories
        if soc_code.endswith("-0000"):
            continue

        title = row[3]
        employment = row[4] if isinstance(row[4], (int, float)) else None
        annual_wage = row[7] if isinstance(row[7], (int, float)) else None

        occupations.append({
            "soc_code": soc_code,
            "title": title,
            "employment": int(employment) if employment else None,
            "annual_wage": round(annual_wage) if annual_wage else None,
        })

    wb.close()
    return occupations


def parse_all(oews_dir: str) -> dict:
    """Parse all Bay Area OEWS files and deduplicate occupations."""
    oews_path = Path(oews_dir)

    # Collect per-region data
    region_data: dict[str, list[dict]] = {}
    for region_name, filename in METROS.items():
        filepath = oews_path / filename
        if not filepath.exists():
            logger.warning(f"Missing: {filepath}")
            continue
        rows = parse_oews_file(filepath, region_name)
        region_data[region_name] = rows
        logger.info(f"  {region_name}: {len(rows)} occupations")

    # Deduplicate by SOC code, aggregate across regions
    occ_map: dict[str, dict] = {}
    for region_name, rows in region_data.items():
        for row in rows:
            soc = row["soc_code"]
            if soc not in occ_map:
                occ_map[soc] = {
                    "soc_code": soc,
                    "title": row["title"],
                    "wages": [],
                    "regions": {},
                }
            if row["employment"]:
                occ_map[soc]["regions"][region_name] = row["employment"]
            if row["annual_wage"]:
                occ_map[soc]["wages"].append(row["annual_wage"])

    # Compute average wage across regions
    occupations = []
    for soc, data in sorted(occ_map.items()):
        avg_wage = round(sum(data["wages"]) / len(data["wages"])) if data["wages"] else None
        occupations.append({
            "soc_code": data["soc_code"],
            "title": data["title"],
            "annual_wage": avg_wage,
            "regions": data["regions"],
        })

    result = {
        "source": "EDD OEWS 2025 (May 2024 employment, Q1 2025 wages)",
        "regions": list(METROS.keys()),
        "occupations": occupations,
    }

    logger.info(f"Total unique occupations: {len(occupations)}")
    logger.info(f"Regions: {len(region_data)}")
    return result


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    if len(sys.argv) < 2:
        print("Usage: python -m pipeline.industry.oews_parser /path/to/oews-xlsx-dir")
        sys.exit(1)

    oews_dir = sys.argv[1]
    result = parse_all(oews_dir)

    out_path = Path(__file__).parent / "oews_parsed.json"
    with open(out_path, "w") as f:
        json.dump(result, f, indent=2)
    print(f"Wrote {len(result['occupations'])} occupations to {out_path}")
