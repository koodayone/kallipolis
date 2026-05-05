"""Build per-college institutional metrics from DataMart CSVs.

Reads three Chancellor's Office DataMart reports from
`backend/ontology/datamart/` and produces one JSON file per college at
`backend/ontology/college_metrics/{backend_key}.json`. The backend keys
flow from `pipeline.datamart_keys.csv_name_to_backend_key`, which reads
catalog_sources.json so the output matches every other pipeline key.

Output schema (the four fields generate.py actually consumes):

    {
      "college": "Santa Barbara City College",
      "source": "DataMart Fall 2025: ...",
      "enrollment": 16893,
      "ft_ratio": 0.4,
      "retention_rate": 0.9287
    }

Data sources:
    StudentHeadcount.csv      → enrollment (Fall 2025 unduplicated)
    UnitLoadSumm.csv          → ft_ratio (≥12 units / all credit students)
    CourseRetSuccessSumm.csv  → retention_rate (Credit category college Total)

Usage:
    python -m pipeline.build_college_metrics
"""
from __future__ import annotations

import csv
import json
import logging
from pathlib import Path
from typing import Optional

from pipeline.datamart_keys import csv_name_to_backend_key

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("build_college_metrics")

DATAMART = Path(__file__).parent.parent / "ontology" / "datamart"
OUTPUT_DIR = Path(__file__).parent.parent / "ontology" / "college_metrics"

# Bucket labels in UnitLoadSumm. Full-time per Chancellor's Office is
# enrollment in 12+ units; the two FT buckets are "12.0 -14.9" and "15 +"
# (note the inconsistent spacing in the source CSV).
FT_BUCKETS = {"12.0 -14.9", "15 +"}
NON_CREDIT_BUCKETS = {"Non-Credit"}


def _parse_int(s: str) -> Optional[int]:
    s = (s or "").strip().replace(",", "").replace('"', "")
    if not s:
        return None
    try:
        return int(s)
    except ValueError:
        return None


def _parse_pct(s: str) -> Optional[float]:
    """Parse '86.54%' → 0.8654."""
    s = (s or "").strip().replace("%", "")
    if not s:
        return None
    try:
        return round(float(s) / 100.0, 4)
    except ValueError:
        return None


def parse_headcount(path: Path) -> dict[str, int]:
    """StudentHeadcount.csv → {backend_key: enrollment}."""
    out: dict[str, int] = {}
    with open(path) as f:
        for parts in csv.reader(f):
            if len(parts) < 2:
                continue
            name, count = parts[0].strip(), parts[1]
            # Skip header rows: blank name, "College Name" literal,
            # "Term"/"Fall 2025" header text.
            if not name or name == "College Name" or name == "Term":
                continue
            n = _parse_int(count)
            if n is None:
                continue
            key = csv_name_to_backend_key(name)
            if key:
                out[key] = n
    return out


def parse_unit_load(path: Path) -> dict[str, float]:
    """UnitLoadSumm.csv → {backend_key: ft_ratio}.

    For each college:
        ft_ratio = sum(FT_BUCKETS counts) / sum(all credit-bucket counts)

    "Non-Credit" rows are excluded from the denominator. The "Total" row
    for the college gives the all-students count, but FT ratio is
    conventionally computed against credit students only, so we sum the
    individual credit-bucket rows.
    """
    out: dict[str, float] = {}
    current_key: Optional[str] = None
    ft = 0
    credit_total = 0

    def _flush() -> None:
        nonlocal ft, credit_total
        if current_key and credit_total > 0:
            out[current_key] = round(ft / credit_total, 4)
        ft = 0
        credit_total = 0

    with open(path) as f:
        for parts in csv.reader(f):
            if len(parts) < 3:
                continue
            col0, col1, col2 = parts[0].strip(), parts[1].strip(), parts[2]

            # College Total row: "Foothill Total,,14135,..."
            if col0 and "Total" in col0 and not col1:
                _flush()
                name = col0.replace(" Total", "").strip()
                current_key = csv_name_to_backend_key(name)
                continue

            # Bucket row: ",12.0 -14.9,1817,12.85%"
            if col1 and current_key:
                if col1 in NON_CREDIT_BUCKETS:
                    continue
                count = _parse_int(col2)
                if count is None:
                    continue
                credit_total += count
                if col1 in FT_BUCKETS:
                    ft += count

    _flush()
    return out


# CourseRetSuccessSumm column layout for the Total row.
# After the 2 leading blank columns, categories appear in fixed order
# with 5 metrics each: Enrollment, Retention, Success, RetRate, SuccRate.
# We want the Credit category's RetRate column.
_CRSS_TOTAL_CREDIT_RETRATE_IDX = 2 + 5 + 3  # = 10


def parse_ret_success(path: Path) -> dict[str, float]:
    """CourseRetSuccessSumm.csv → {backend_key: retention_rate}.

    Each college's Total row carries Credit-category aggregates at fixed
    column indices. We pull the retention_rate from the Credit block.
    """
    out: dict[str, float] = {}
    with open(path) as f:
        for parts in csv.reader(f):
            if len(parts) <= _CRSS_TOTAL_CREDIT_RETRATE_IDX:
                continue
            col0 = parts[0].strip()
            # Total rows are the only ones with a non-empty col0.
            if not col0 or "Total" not in col0:
                continue
            name = col0.replace(" Total", "").strip()
            key = csv_name_to_backend_key(name)
            if not key:
                continue
            rate = _parse_pct(parts[_CRSS_TOTAL_CREDIT_RETRATE_IDX])
            if rate is not None:
                out[key] = rate
    return out


def main() -> int:
    headcount = parse_headcount(DATAMART / "StudentHeadcount.csv")
    ft_ratio = parse_unit_load(DATAMART / "UnitLoadSumm.csv")
    retention = parse_ret_success(DATAMART / "CourseRetSuccessSumm.csv")

    logger.info(
        f"Parsed: headcount={len(headcount)}, ft_ratio={len(ft_ratio)}, "
        f"retention={len(retention)}"
    )

    # Union of keys across the three sources — write a file for any
    # college that has at least one metric.
    keys = set(headcount) | set(ft_ratio) | set(retention)
    logger.info(f"Unique backend keys across sources: {len(keys)}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    written = 0
    for key in sorted(keys):
        record = {
            "college_key": key,
            "source": "DataMart Fall 2025: StudentHeadcount, UnitLoadSumm, CourseRetSuccessSumm",
        }
        if key in headcount:
            record["enrollment"] = headcount[key]
        if key in ft_ratio:
            record["ft_ratio"] = ft_ratio[key]
        if key in retention:
            record["retention_rate"] = retention[key]

        path = OUTPUT_DIR / f"{key}.json"
        with open(path, "w") as f:
            json.dump(record, f, indent=2, sort_keys=True)
            f.write("\n")
        written += 1

    logger.info(f"Wrote {written} metric files to {OUTPUT_DIR}")

    # Coverage report
    missing = []
    for key in sorted(keys):
        absent = []
        if key not in headcount:
            absent.append("enrollment")
        if key not in ft_ratio:
            absent.append("ft_ratio")
        if key not in retention:
            absent.append("retention_rate")
        if absent:
            missing.append((key, absent))
    if missing:
        logger.info(f"Partial-coverage colleges ({len(missing)}):")
        for key, absent in missing:
            logger.info(f"  {key}: missing {absent}")

    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
