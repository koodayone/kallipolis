"""
Generate occupations.json from COE (Centers of Excellence) middle-skill data.

COE is the sole data source for occupation demand metrics, and its middle-skill
designation is the authoritative occupation universe. Community colleges target
middle-skill occupations, so the occupation set is exactly the SOCs the COE
middle-skill publication (ontology/occupational_demand_middle_skill.csv) tracks
regional demand for — every SOC in that file becomes a node, with no derived
filter applied here.

This replaces an earlier COE-∩-CTE-reachable filter, which had a two-sided
error: it admitted non-middle-skill occupations reachable only by crosswalk
over-reach (management and professional roles that are not CC targets), and it
dropped middle-skill occupations the crosswalk could not reach (real regional
demand with no CC pipeline). Grounding the occupation set on the COE middle-skill
designation resolves both. See docs/product/occupations.md and
docs/pipeline/occupation-generation.md for the product and pipeline framing.

Usage:
    python -m occupations.generate
"""

from __future__ import annotations

import csv
import json
import logging
import sys
from pathlib import Path

from ontology.crosswalks import COE_DEMAND_PATH

logger = logging.getLogger(__name__)

# COE demand CSV ships in-repo via ontology/crosswalks.py (the same file
# ontology/supply.py reads at runtime). Previously this module pointed at
# an out-of-repo dev path; centralizing through crosswalks.py makes the
# data layout single-source-of-truth.
COE_CSV_DEFAULT = COE_DEMAND_PATH
OUTPUT_PATH = Path(__file__).parent / "occupations.json"
EXISTING_PATH = Path(__file__).parent / "occupations.json"


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


def _parse_row(row: dict) -> tuple[str, str, dict, dict]:
    """Extract (soc, region, occupation_shell, region_metrics) from a CSV row."""
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

    return soc, region, occupation_shell, region_metrics


def generate_from_coe(csv_path: Path) -> list[dict]:
    """Parse COE CSV and produce occupations list for the pipeline."""
    occupations: dict[str, dict] = {}

    with open(csv_path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            soc, region, shell, metrics = _parse_row(row)

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
    logger.info(f"Generated {len(result)} middle-skill occupations (COE designation)")

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
