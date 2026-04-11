"""
Parse COE (Centers of Excellence) occupational demand CSV into structured JSON.

Source: California Centers of Excellence occupational demand projections (2024-2029).
Covers ~800 SOC codes across 9 COE regions plus statewide.

Usage:
    python -m pipeline.industry.coe_parser /path/to/occupational_demand_coe.csv
"""

import csv
import json
import logging
import sys
from pathlib import Path

logger = logging.getLogger(__name__)


def parse_coe(filepath: str) -> dict:
    """Parse COE occupational demand CSV into a dict keyed by SOC code."""
    occupations: dict[str, dict] = {}

    with open(filepath, newline="") as f:
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

            if soc not in occupations:
                occupations[soc] = {
                    "title": title,
                    "education_level": education,
                    "regions": {},
                }

            occupations[soc]["regions"][region] = {
                "growth_rate": growth_rate,
                "annual_openings": annual_openings,
                "median_annual_earnings": median_annual,
            }

    result = {
        "source": "Centers of Excellence Occupational Demand 2024-2029",
        "occupations": occupations,
    }

    logger.info(f"Parsed {len(occupations)} unique SOC codes from COE data")
    region_codes = set()
    for occ in occupations.values():
        region_codes.update(occ["regions"].keys())
    logger.info(f"Regions: {sorted(region_codes)}")

    return result


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    if len(sys.argv) < 2:
        print("Usage: python -m pipeline.industry.coe_parser /path/to/occupational_demand_coe.csv")
        sys.exit(1)

    filepath = sys.argv[1]
    result = parse_coe(filepath)

    out_path = Path(__file__).parent / "coe_parsed.json"
    with open(out_path, "w") as f:
        json.dump(result, f, indent=2)
    print(f"Wrote {len(result['occupations'])} occupations to {out_path}")
