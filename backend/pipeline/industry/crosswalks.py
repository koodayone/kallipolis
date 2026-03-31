"""
Crosswalk utilities: TOP → CIP → SOC chain.

Provides authoritative government mappings from California community college
programs to federal occupational classifications. Used for demand profiling
and employer-occupation alignment.

Usage:
    from pipeline.industry.crosswalks import build_demand_profile
    profile = build_demand_profile("lacity", occupations, coe_demand)
"""

from __future__ import annotations

import csv
import json
import logging
from pathlib import Path

import openpyxl

logger = logging.getLogger(__name__)

# ── Data paths ────────────────────────────────────────────────────────────

DATASET_DIR = Path("/Users/dayonekoo/Desktop/cc_dataset")
TOP_CIP_PATH = DATASET_DIR / "top_cip_crosswalk.csv"
CIP_SOC_PATH = DATASET_DIR / "CIP2020_SOC2018_Crosswalk.xlsx"
COE_DEMAND_PATH = DATASET_DIR / "occupational_demand_coe.csv"

CALIBRATIONS_DIR = Path(__file__).parent.parent / "calibrations"


# ── Crosswalk loaders (cached) ────────────────────────────────────────────

_top_to_cip: dict[str, set[str]] | None = None
_cip_to_soc: dict[str, set[str]] | None = None
_coe_demand: dict[str, dict[str, dict]] | None = None


def _load_top_to_cip() -> dict[str, set[str]]:
    """Load TOP4 → CIP code mapping from Chancellor's Office crosswalk."""
    global _top_to_cip
    if _top_to_cip is not None:
        return _top_to_cip

    mapping: dict[str, set[str]] = {}
    with open(TOP_CIP_PATH, newline="") as f:
        reader = csv.reader(f)
        next(reader)  # skip header
        for row in reader:
            top_raw = row[0].split(" - ")[0].strip()
            cip_raw = row[2].split(" - ")[0].strip()
            top4 = top_raw.replace(".", "")[:4]
            if top4 and cip_raw:
                mapping.setdefault(top4, set()).add(cip_raw)

    _top_to_cip = mapping
    logger.info(f"Loaded TOP→CIP crosswalk: {len(mapping)} TOP4 codes")
    return mapping


def _load_cip_to_soc() -> dict[str, set[str]]:
    """Load CIP → SOC code mapping from NCES/BLS crosswalk."""
    global _cip_to_soc
    if _cip_to_soc is not None:
        return _cip_to_soc

    mapping: dict[str, set[str]] = {}
    wb = openpyxl.load_workbook(CIP_SOC_PATH, read_only=True)
    ws = wb["CIP-SOC"]
    for row in ws.iter_rows(min_row=2, values_only=True):
        cip, _, soc, _ = row
        if cip and soc:
            mapping.setdefault(str(cip), set()).add(str(soc))
    wb.close()

    _cip_to_soc = mapping
    logger.info(f"Loaded CIP→SOC crosswalk: {len(mapping)} CIP codes")
    return mapping


def _load_coe_demand() -> dict[str, dict[str, dict]]:
    """Load COE occupational demand projections.

    Returns: {region: {soc_code: {annual_openings, growth_rate, median_wage, jobs}}}
    """
    global _coe_demand
    if _coe_demand is not None:
        return _coe_demand

    data: dict[str, dict[str, dict]] = {}
    with open(COE_DEMAND_PATH, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            region = row["Region"]
            soc = row["SOC"]
            try:
                data.setdefault(region, {})[soc] = {
                    "annual_openings": int(row["Average Annual Job Openings"]),
                    "growth_rate": float(row["2024 - 2029 % Change"]),
                    "median_wage": int(row["Median Annual Earnings"]),
                    "jobs_2024": int(row["2024 Jobs"]),
                    "title": row["Description"],
                    "education": row["Typical Entry Level Education"],
                }
            except (ValueError, KeyError):
                continue

    _coe_demand = data
    logger.info(f"Loaded COE demand: {len(data)} regions, {sum(len(v) for v in data.values())} entries")
    return data


# ── Core functions ────────────────────────────────────────────────────────

def top4_to_soc(top4_codes: list[str]) -> dict[str, set[str]]:
    """Map TOP4 codes to SOC codes via TOP→CIP→SOC chain.

    Returns: {top4: {soc_code, ...}} for each TOP4 that has a mapping.
    """
    top_cip = _load_top_to_cip()
    cip_soc = _load_cip_to_soc()

    result: dict[str, set[str]] = {}
    for top4 in top4_codes:
        cips = top_cip.get(top4, set())
        socs: set[str] = set()
        for cip in cips:
            socs.update(cip_soc.get(cip, set()))
        if socs:
            result[top4] = socs

    return result


def build_demand_profile(
    college_key: str,
    occupations: list[dict],
    coe_region: str,
) -> list[dict]:
    """Build ranked demand profile for a college.

    Computes which occupations this college should be producing graduates for,
    ranked by composite score of enrollment weight × annual openings × growth × wage.

    Args:
        college_key: Pipeline key (e.g., "lacity")
        occupations: Full occupations list from occupations.json
        coe_region: COE region code (e.g., "LA", "Bay")

    Returns:
        Ranked list of dicts:
        [{soc_code, title, annual_openings, growth_rate, median_wage,
          enrollment_weight, composite_score, top4_sources}]
    """
    # Load calibration for enrollment weights
    cal_path = CALIBRATIONS_DIR / "top4" / f"{college_key}.json"
    if not cal_path.exists():
        logger.warning(f"No TOP4 calibration for {college_key}")
        return []

    with open(cal_path) as f:
        cal = json.load(f)

    top4_data = cal.get("top4_codes", {})
    total_enrollment = cal.get("total_enrollments", 1)

    # Map TOP4 → SOC
    top4_codes = list(top4_data.keys())
    top4_soc_map = top4_to_soc(top4_codes)

    # Build SOC → enrollment weight (sum across all TOP4s that feed this SOC)
    valid_socs = {o["soc_code"] for o in occupations}
    soc_weights: dict[str, float] = {}
    soc_top4_sources: dict[str, list[str]] = {}

    for top4, socs in top4_soc_map.items():
        enrollment = top4_data.get(top4, {}).get("enrollment", 0)
        weight = enrollment / total_enrollment if total_enrollment else 0
        for soc in socs:
            if soc in valid_socs:
                soc_weights[soc] = soc_weights.get(soc, 0) + weight
                soc_top4_sources.setdefault(soc, []).append(top4)

    if not soc_weights:
        logger.warning(f"No SOC codes reachable for {college_key}")
        return []

    # Load COE demand for this region
    coe = _load_coe_demand()
    region_demand = coe.get(coe_region, {})
    if not region_demand:
        # Fallback to statewide
        region_demand = coe.get("CA", {})
        logger.warning(f"No COE data for region {coe_region}, using statewide")

    # Score each SOC
    raw_scores: list[dict] = []
    for soc, enrollment_weight in soc_weights.items():
        demand = region_demand.get(soc)
        if not demand:
            continue
        raw_scores.append({
            "soc_code": soc,
            "title": demand["title"],
            "annual_openings": demand["annual_openings"],
            "growth_rate": demand["growth_rate"],
            "median_wage": demand["median_wage"],
            "jobs_2024": demand["jobs_2024"],
            "education": demand["education"],
            "enrollment_weight": enrollment_weight,
            "top4_sources": soc_top4_sources.get(soc, []),
        })

    if not raw_scores:
        return []

    # Normalize and compute composite score
    openings = [s["annual_openings"] for s in raw_scores]
    growths = [1 + s["growth_rate"] for s in raw_scores]  # shift so negative growth < 1
    wages = [s["median_wage"] for s in raw_scores]
    weights = [s["enrollment_weight"] for s in raw_scores]

    def _norm(values: list[float]) -> list[float]:
        lo, hi = min(values), max(values)
        if hi == lo:
            return [0.5] * len(values)
        return [(v - lo) / (hi - lo) for v in values]

    n_openings = _norm(openings)
    n_growths = _norm(growths)
    n_wages = _norm(wages)
    n_weights = _norm(weights)

    for i, s in enumerate(raw_scores):
        s["composite_score"] = n_weights[i] * n_openings[i] * n_growths[i] * n_wages[i]

    raw_scores.sort(key=lambda s: -s["composite_score"])
    return raw_scores
