"""Build per-college TOP6 calibration files from DataMart grade distribution data.

Parses `backend/ontology/datamart/top6_grades.csv` (hierarchical format —
college Total rows, then per-TOP6 Total rows like
"Accounting-050200 Total", then per-grade rows) and writes
`backend/ontology/college_metrics/top6/{backend_key}.json` for each college.

Each output file carries:
- per-TOP6 grade distributions and enrollment counts
- a `top4_rollup` section that aggregates the per-TOP6 grade
  distributions up to 4-digit parent codes — gives the student
  generator a tier-ladder fallback at sample time without needing a
  separate TOP4 calibration:
      exact TOP6 grades → parent top4_rollup → DEFAULT_GRADES.

Backend keys flow through `pipeline.datamart_keys.csv_name_to_backend_key`,
which sources catalog_sources.json. CSV display names that don't map to
a catalog backend key (CalBright, Madera, continuing-ed entities) are
skipped.

Usage:
    python -m pipeline.build_top6_calibrations
    python -m pipeline.build_top6_calibrations /custom/path/top6_grades.csv
"""

import csv
import json
import re
import sys
from pathlib import Path

from pipeline.datamart_keys import csv_name_to_backend_key


# Grade label normalization. Maps CSV grade labels to the short codes
# the student generator's grade sampler uses.
GRADE_MAP = {
    "Grade A": "A",
    "Grade B": "B",
    "Grade C": "C",
    "Grade D": "D",
    "Grade F": "F",
    "Withdrew": "W",
    "Excused Withdrawal": "W",
    "Pass": "P",
    "No Pass": "NP",
    "Incomplete": "W",
}


DEFAULT_GRADES_CSV = (
    Path(__file__).parent.parent / "ontology" / "datamart" / "top6_grades.csv"
)
OUTPUT_DIR = (
    Path(__file__).parent.parent / "ontology" / "college_metrics" / "top6"
)


def parse_grades_file(filepath: str) -> dict:
    """Parse top6_grades.csv into per-college, per-TOP6 data.

    Returns: {college_display_name: {"total_enrollments": int, "top6_codes": {...}}}
    """
    colleges: dict = {}
    current_college = None
    current_top6 = None
    current_top6_name = None
    current_enrollment = 0
    current_grades: dict = {}

    with open(filepath, encoding="utf-8", errors="replace") as f:
        reader = csv.reader(f)
        for parts in reader:
            if len(parts) < 4:
                continue

            col0 = parts[0].strip()
            col1 = parts[1].strip()
            col2 = parts[2].strip()
            col3 = parts[3].strip().replace(",", "")
            col4 = parts[4].strip().replace("%", "") if len(parts) > 4 else ""

            # College total line: "Foothill Total,,,"27,853",0.76%"
            if col0 and "Total" in col0 and not col1:
                if current_college and current_top6 and current_grades:
                    _save_top6(
                        colleges, current_college, current_top6,
                        current_top6_name, current_enrollment, current_grades,
                    )

                current_college = col0.replace(" Total", "").strip()
                current_top6 = None
                current_grades = {}
                colleges.setdefault(current_college, {
                    "total_enrollments": 0,
                    "top6_codes": {},
                })
                try:
                    colleges[current_college]["total_enrollments"] = int(col3)
                except (ValueError, TypeError):
                    pass
                continue

            # TOP6 code line: ",Accounting-050200 Total,,306,3.12%"
            if col1 and "Total" in col1 and not col2:
                if current_college and current_top6 and current_grades:
                    _save_top6(
                        colleges, current_college, current_top6,
                        current_top6_name, current_enrollment, current_grades,
                    )

                m = re.match(r"(.+)-(\d{6})\s*Total", col1)
                if m:
                    current_top6_name = m.group(1).strip()
                    current_top6 = m.group(2)
                    try:
                        current_enrollment = int(col3)
                    except (ValueError, TypeError):
                        current_enrollment = 0
                    current_grades = {}
                else:
                    current_top6 = None
                continue

            # Grade line: ",,Grade A,188,61.44%"
            if col2 and current_top6 and current_college:
                normalized = GRADE_MAP.get(col2)
                if normalized and col4:
                    try:
                        pct = float(col4) / 100.0
                        current_grades[normalized] = (
                            current_grades.get(normalized, 0) + pct
                        )
                    except (ValueError, TypeError):
                        pass

    # Flush last TOP6
    if current_college and current_top6 and current_grades:
        _save_top6(
            colleges, current_college, current_top6,
            current_top6_name, current_enrollment, current_grades,
        )

    return colleges


def _save_top6(colleges, college_name, top6, name, enrollment, grades):
    if not grades:
        return
    total = sum(grades.values())
    if total > 0:
        grades = {k: round(v / total, 4) for k, v in grades.items()}
    colleges[college_name]["top6_codes"][top6] = {
        "name": name,
        "enrollment": enrollment,
        "grades": grades,
    }


def _compute_top4_rollup(top6_codes: dict) -> dict:
    """Aggregate per-TOP6 grade distributions into parent-TOP4 rollups.

    Returns {top4: {"enrollment": int, "grades": {A, B, ...}}} where grades
    are enrollment-weighted averages of the contributing TOP6 distributions
    and normalized to sum to ~1.0.
    """
    rollup: dict = {}
    for top6, entry in top6_codes.items():
        top4 = top6[:4]
        bucket = rollup.setdefault(top4, {"enrollment": 0, "_weighted": {}})
        bucket["enrollment"] += entry["enrollment"]
        for grade, share in entry["grades"].items():
            bucket["_weighted"][grade] = (
                bucket["_weighted"].get(grade, 0) + share * entry["enrollment"]
            )

    out = {}
    for top4, bucket in rollup.items():
        if bucket["enrollment"] <= 0:
            continue
        grades = {
            g: round(w / bucket["enrollment"], 4)
            for g, w in bucket["_weighted"].items()
        }
        # Re-normalize (rounding drift) so shares sum to ~1.0
        s = sum(grades.values())
        if s > 0:
            grades = {g: round(v / s, 4) for g, v in grades.items()}
        out[top4] = {"enrollment": bucket["enrollment"], "grades": grades}
    return out


def main():
    filepath = sys.argv[1] if len(sys.argv) > 1 else str(DEFAULT_GRADES_CSV)
    print(f"Parsing {filepath}...")
    colleges = parse_grades_file(filepath)
    print(f"Found {len(colleges)} colleges in CSV")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    written = 0
    skipped_no_key = []
    skipped_no_top6 = []
    for name, data in sorted(colleges.items()):
        backend_key = csv_name_to_backend_key(name)
        if not backend_key:
            skipped_no_key.append(name)
            continue
        if not data["top6_codes"]:
            skipped_no_top6.append(name)
            continue

        output = {
            "college_name": name,
            "college_key": backend_key,
            "total_enrollments": data["total_enrollments"],
            "top6_codes": data["top6_codes"],
            "top4_rollup": _compute_top4_rollup(data["top6_codes"]),
        }

        path = OUTPUT_DIR / f"{backend_key}.json"
        with open(path, "w") as f:
            json.dump(output, f, indent=2)
        written += 1

    print(f"Wrote {written} calibration files to {OUTPUT_DIR}")
    if skipped_no_key:
        print(f"Skipped {len(skipped_no_key)} colleges absent from "
              f"catalog_sources: {sorted(skipped_no_key)}")
    if skipped_no_top6:
        print(f"Skipped {len(skipped_no_top6)} colleges with no TOP6 codes")

    total_top6s = sum(len(d["top6_codes"]) for d in colleges.values())
    print(f"Total TOP6 codes across all parsed colleges: {total_top6s}")


if __name__ == "__main__":
    main()
