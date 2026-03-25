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

BAY_AREA_METROS = {
    "San Jose-Sunnyvale-Santa Clara": "CA-OEWS-San Jose-Sunnyvale-Santa Clara MSA-2025.xlsx",
    "Oakland-Fremont-Berkeley": "CA-OEWS-Oakland-Fremont-Berkeley MD-2025.xlsx",
    "San Francisco-San Mateo-Redwood City": "CA-OEWS-San Francisco-San Mateo-Redwood City MD-2025.xlsx",
    "Santa Rosa-Petaluma": "CA-OEWS-Santa Rosa-Petaluma MSA-2025.xlsx",
    "Napa": "CA-OEWS-Napa MSA-2025.xlsx",
    "Vallejo": "CA-OEWS-Vallejo MSA-2025.xlsx",
    "Santa Cruz-Watsonville": "CA-OEWS-Santa Cruz-Watsonville MSA-2025.xlsx",
    "San Rafael": "CA-OEWS-San Rafael MD-2025.xlsx",
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
    for region_name, filename in BAY_AREA_METROS.items():
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
        "regions": list(BAY_AREA_METROS.keys()),
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
