"""
Generate occupations.json from COE (Centers of Excellence) data.

COE is the sole data source for the occupations domain.

The workforce-development band filter is applied here (not at load time), so
every row written to occupations.json is a row the graph will load. The band
matches docs/product/occupations.md: postsecondary certificate through
bachelor's degree.

Usage:
    python -m occupations.generate
"""

from __future__ import annotations

import csv
import json
import logging
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

COE_CSV_DEFAULT = Path(__file__).parents[3] / "cc_dataset" / "occupational_demand_coe.csv"
OUTPUT_PATH = Path(__file__).parent / "occupations.json"
EXISTING_PATH = Path(__file__).parent / "occupations.json"

# Education levels excluded from the workforce-development band. Occupations
# whose typical entry-level education falls outside postsecondary certificate
# through bachelor's are not what community colleges serve.
EXCLUDED_EDUCATION = frozenset({
    "No formal educational credential",
    "High school diploma or equivalent",
    "Some college, no degree",
    "Master's degree",
    "Doctoral or professional degree",
    "N/A",
})


def _parse_int(value) -> int | None:
    """Coerce a CSV cell to int, returning None on empty or bad input."""
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (ValueError, TypeError):
        return None


def _parse_float(value) -> float | None:
    """Coerce a CSV cell to float, returning None on empty or bad input."""
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def _parse_row(row: dict) -> tuple[str, str, dict, str, dict]:
    """Extract (soc, region, occupation_shell, education, region_metrics) from a CSV row."""
    soc = row["SOC"].strip()
    region = row["Region"].strip()
    title = row["Description"].strip()
    education = row["Typical Entry Level Education"].strip()

    occupation_shell = {
        "soc_code": soc,
        "title": title,
        "description": "",
        "skills": [],
        "education_level": education,
        "regions": {},
    }

    region_metrics = {
        "employment": _parse_int(row.get("2024 Jobs")),
        "annual_wage": _parse_int(row.get("Median Annual Earnings")),
        "growth_rate": _parse_float(row.get("2024 - 2029 % Change")),
        "annual_openings": _parse_int(row.get("Average Annual Job Openings")),
    }

    return soc, region, occupation_shell, education, region_metrics


def _is_in_workforce_band(education_level: str) -> bool:
    """True when an education level falls inside the community-college workforce band."""
    return education_level not in EXCLUDED_EDUCATION


def generate_from_coe(csv_path: Path) -> list[dict]:
    """Parse COE CSV and produce occupations list for the pipeline."""
    occupations: dict[str, dict] = {}

    with open(csv_path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            soc, region, shell, education, metrics = _parse_row(row)

            if not _is_in_workforce_band(education):
                continue

            if soc not in occupations:
                occupations[soc] = shell

            occupations[soc]["regions"][region] = metrics

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
    logger.info(f"Generated {len(result)} occupations in the workforce-development band")

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
