"""Combine and clean Course Details CSVs from the CCC Data Mart.

Source: California Community Colleges Chancellor's Office Data Mart
        Course Details report
        https://datamart.cccco.edu/Courses/Course_Details.aspx

Manual export workflow (until a Playwright scraper exists): on the
Course Details page, set "Select State-District-College" = Statewide
Search, "Select Term" = the term you want, multi-select all TOP codes,
click View Report, then Export → CSV. The export caps each file by row
count, so a full statewide pull arrives as 4–5 chunked CSVs. Drop them
all into the --raw-dir directory; this script handles the rest.

Outputs a single canonical course-inventory file with derived columns:
  - sam_code           — single-letter A/B/C/D/E from SAM Status
  - top_code           — 6-digit numeric, parsed from "<desc>-<NNNNNN>"
  - top_description    — descriptive portion of the TOP Code field
  - _source_file       — which raw CSV the row originally came from

Dedup: by (College, Control Number). Whitespace stripped from every
text field. SAM mapping covers all five DED-defined codes; an unmatched
SAM Status raises (data integrity check, not a silent drop).

Usage:
    python -m courses.combine_course_details
    python -m courses.combine_course_details \\
        --raw-dir backend/ontology/coursedetails/raw \\
        --output backend/ontology/coursedetails/CourseDetails_combined.csv
"""
from __future__ import annotations

import argparse
import csv
import logging
import re
import sys
from collections import Counter
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("combine_course_details")

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_RAW_DIR = REPO_ROOT / "backend" / "ontology" / "coursedetails" / "raw"
DEFAULT_OUTPUT = REPO_ROOT / "backend" / "ontology" / "coursedetails" / "CourseDetails_combined_fall2025.csv"

# SAM Status text → CB09 single-letter code. Definitions per the CCC
# MIS Data Element Dictionary entry for CB09 (COURSE-SAM-PRIORITY-CODE):
# https://webdata.cccco.edu/ded/cb/cb09.pdf
SAM_TO_CODE = {
    "apprenticeship": "A",
    "advanced occupational": "B",
    "clearly occupational": "C",
    "possibly occupational": "D",
    "non-occupational": "E",
}

# Data Mart's TOP Code field combines description and 6-digit code:
# "Machining and Machine Tools-095630"
TOP_RE = re.compile(r"^(.*?)-(\d{6})$")


def sam_code(text: str) -> str:
    t = text.strip().lower()
    for prefix, code in SAM_TO_CODE.items():
        if t.startswith(prefix):
            return code
    raise ValueError(f"Unrecognized SAM Status: {text!r}")


def parse_top(text: str) -> tuple[str, str]:
    t = text.strip()
    m = TOP_RE.match(t)
    if m:
        return m.group(1).strip(), m.group(2)
    return t, ""


def combine(raw_dir: Path, output: Path) -> int:
    raw_files = sorted(p for p in raw_dir.glob("CourseDetails*.csv") if p.name != output.name)
    if not raw_files:
        logger.error(f"No raw CourseDetails*.csv files found in {raw_dir}")
        return 1

    rows: list[dict] = []
    seen: set[tuple[str, str]] = set()
    per_file_stats: list[tuple[str, int, int]] = []

    for f in raw_files:
        n_in = n_dup = 0
        with f.open(encoding="utf-8", errors="replace") as fh:
            for row in csv.DictReader(fh):
                n_in += 1
                cleaned = {
                    k.strip(): (v.strip() if isinstance(v, str) else v)
                    for k, v in row.items()
                }
                key = (cleaned["College"], cleaned["Control Number"])
                if key in seen:
                    n_dup += 1
                    continue
                seen.add(key)
                top_desc, top_num = parse_top(cleaned["TOP Code"])
                cleaned["sam_code"] = sam_code(cleaned["SAM Status"])
                cleaned["top_code"] = top_num
                cleaned["top_description"] = top_desc
                cleaned["_source_file"] = f.name
                rows.append(cleaned)
        per_file_stats.append((f.name, n_in, n_dup))

    if not rows:
        logger.error("No rows extracted from any raw file")
        return 1

    output.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0].keys())
    with output.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)

    logger.info(f"Wrote {len(rows):,} unique rows to {output}")
    logger.info(f"\nPer-source row counts (in / dup-skipped):")
    for name, n_in, n_dup in per_file_stats:
        logger.info(f"  {name:<35s}  {n_in:>6,}  {n_dup:>5} dropped")

    sam_counts = Counter(r["sam_code"] for r in rows)
    logger.info(f"\nSAM code distribution:")
    for code in "ABCDE":
        n = sam_counts.get(code, 0)
        pct = 100 * n / len(rows)
        logger.info(f"  {code}: {n:>6,} ({pct:>5.1f}%)")

    college_count = len({r["College"] for r in rows})
    logger.info(f"\nColleges represented: {college_count}")
    terms = sorted({r["Term"] for r in rows})
    logger.info(f"Terms: {terms}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-dir", type=Path, default=DEFAULT_RAW_DIR,
                        help=f"Directory containing raw Data Mart CSVs (default: {DEFAULT_RAW_DIR})")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT,
                        help=f"Output path for the combined CSV (default: {DEFAULT_OUTPUT})")
    args = parser.parse_args()
    return combine(args.raw_dir, args.output)


if __name__ == "__main__":
    sys.exit(main())
