# NAICS-4 Search-Space Expansion Research (May 2026)

This directory captures the research that derived a 268-code expansion of `CTE_NAICS_CODES` (`backend/employers/edd_scrape.py`) from the prior 140-code editorial set.

## Status

**Not merged to main.** The expanded `edd_scrape.py` on this branch reflects the proposed 268-code set; main remains at 140 codes pending a coordinated re-scrape across all 9 COE regions.

## Methodology

For each curriculum-supported SOC, list every NAICS-4 industry that the BLS OEWS National Industry-Occupation Matrix publishes as employing that SOC at any positive workforce share (`pct_total > 0`). Sort employers by `pct_total` descending. Aggregate the union of NAICS-4 codes across all supported SOCs to derive the search space.

The expansion adds 128 NAICS-4 codes:
- 122 codes auto-classified via `pct_total`-weighted SOC→sector aggregation (per-NAICS sector profile from BLS OEWS, SOC sectors via TOP→PCAH crosswalk)
- 6 Public Administration codes hand-mapped (9211, 9231, 9251, 9261, 9281) plus 9991/9992/9993 OEWS government aggregates added by the auto-classifier

The generator: `backend/employers/auto_classify_naics.py`.

## Validation

Validated on Foothill College (Bay region) only. After expansion:
- Curriculum-supported SOCs: 249
- SOCs with ≥1 candidate employer at `pct_total > 0`: 249 (100.0%)
- Total `(SOC, employer)` pairs: 26,613
- Distinct regional employers represented: 311 of 311

See `docs/final_methodology_validation.md` for the full validation report.

## Why deferred

The expansion has not been validated against rural-county cases (FN, CVML rural sub-regions, GS's Colusa/Sutter/Yuba counties) and has not been rolled out across regions. Running it for one region in isolation would produce an asymmetric NAICS universe across the 9 regions, breaking cross-region rollups. The next coordinated rescrape across all regions should land this expansion.

## Contents

- `docs/` — analysis and methodology reports (markdown)
- `data/` — derived data artifacts (CSV, JSON, intermediate text)
- `scripts/` — analysis scripts that produced the reports

The committed `backend/employers/edd_scrape.py` on this branch is the 268-code version; diff against `main` shows the additions.
