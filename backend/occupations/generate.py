"""
Generate occupations.json from COE (Centers of Excellence) data.

COE is the sole data source for the occupations domain. This replaces
the previous OEWS-based generation pipeline.

Usage:
    python -m pipeline.industry.generate_occupations_from_coe
"""

import csv
import json
import logging
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

COE_CSV_DEFAULT = Path(__file__).parents[3] / "cc_dataset" / "occupational_demand_coe.csv"
OUTPUT_PATH = Path(__file__).parent / "occupations.json"
EXISTING_PATH = Path(__file__).parent / "occupations.json"


def generate_from_coe(csv_path: Path) -> list[dict]:
    """Parse COE CSV and produce occupations list for the pipeline."""
    occupations: dict[str, dict] = {}

    with open(csv_path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            soc = row["SOC"].strip()
            region = row["Region"].strip()
            title = row["Description"].strip()
            education = row["Typical Entry Level Education"].strip()

            # Parse numeric fields
            try:
                growth_rate = float(row["2024 - 2029 % Change"]) if row["2024 - 2029 % Change"] else None
            except (ValueError, TypeError):
                growth_rate = None

            try:
                annual_openings = int(row["Average Annual Job Openings"]) if row["Average Annual Job Openings"] else None
            except (ValueError, TypeError):
                annual_openings = None

            try:
                median_annual = int(row["Median Annual Earnings"]) if row["Median Annual Earnings"] else None
            except (ValueError, TypeError):
                median_annual = None

            try:
                jobs = int(row["2024 Jobs"]) if row["2024 Jobs"] else None
            except (ValueError, TypeError):
                jobs = None

            if soc not in occupations:
                occupations[soc] = {
                    "soc_code": soc,
                    "title": title,
                    "description": "",
                    "skills": [],
                    "education_level": education,
                    "regions": {},
                }

            occupations[soc]["regions"][region] = {
                "employment": jobs,
                "annual_wage": median_annual,
                "growth_rate": growth_rate,
                "annual_openings": annual_openings,
            }

    # Preserve existing skills and descriptions if occupations.json exists
    if EXISTING_PATH.exists():
        with open(EXISTING_PATH) as f:
            existing = json.load(f)
        existing_by_soc = {o["soc_code"]: o for o in existing}
        for soc, occ in occupations.items():
            prev = existing_by_soc.get(soc)
            if prev:
                if prev.get("skills"):
                    occ["skills"] = prev["skills"]
                if prev.get("description"):
                    occ["description"] = prev["description"]

    result = sorted(occupations.values(), key=lambda o: o["soc_code"])
    logger.info(f"Generated {len(result)} occupations from COE data")

    # Log region coverage
    regions = set()
    for occ in result:
        regions.update(occ["regions"].keys())
    logger.info(f"COE regions: {sorted(regions)}")

    return result


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    csv_path = Path(sys.argv[1]) if len(sys.argv) > 1 else COE_CSV_DEFAULT
    if not csv_path.exists():
        print(f"COE CSV not found: {csv_path}")
        sys.exit(1)

    result = generate_from_coe(csv_path)

    with open(OUTPUT_PATH, "w") as f:
        json.dump(result, f, indent=2)
    print(f"Wrote {len(result)} occupations to {OUTPUT_PATH}")
