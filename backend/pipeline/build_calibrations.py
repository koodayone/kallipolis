"""Build per-college TOP4 calibration files from DataMart grade distribution data.

Parses GradesSummAll.csv (hierarchical format) and generates calibrations/top4/{college}.json
for each college with TOP4 enrollment counts and grade distributions.

Usage:
    python -m pipeline.build_calibrations /path/to/GradesSummAll.csv

Output:
    Overwrites calibrations/top4/{college_key}.json for each college found
"""

import csv
import io
import json
import re
import sys
from pathlib import Path


# Grade label normalization
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


def college_key(name: str) -> str:
    """Convert college display name to filesystem key.

    Examples:
        'Sequoias' → 'sequoias'
        'Berkeley City' → 'berkeley_city'
        'Allan Hancock' → 'allan_hancock'
        'San Jose City' → 'san_jose_city'
    """
    name = name.strip()
    # Lowercase, replace spaces with underscores
    key = re.sub(r"\s+", "_", name.lower())
    # Remove any non-alphanumeric characters except underscores
    key = re.sub(r"[^a-z0-9_]", "", key)
    return key


def parse_grades_file(filepath: str) -> dict:
    """Parse GradesSummAll.csv into per-college, per-TOP4 data.

    Returns: {college_name: {top4_code: {name, enrollment, grades}}}
    """
    colleges = {}
    current_college = None
    current_top4 = None
    current_top4_name = None
    current_enrollment = 0
    current_grades = {}

    with open(filepath, encoding="utf-8", errors="replace") as f:
        reader = csv.reader(f)
        for line_no, parts in enumerate(reader):
            if len(parts) < 4:
                continue

            col0 = parts[0].strip()
            col1 = parts[1].strip()
            col2 = parts[2].strip()
            col3 = parts[3].strip().replace(",", "")
            col4 = parts[4].strip().replace("%", "") if len(parts) > 4 else ""

            # College total line: "Sequoias Total,,,"42,817",1.17%"
            if col0 and "Total" in col0 and not col1:
                # Save previous TOP4 if exists
                if current_college and current_top4 and current_grades:
                    _save_top4(colleges, current_college, current_top4,
                              current_top4_name, current_enrollment, current_grades)

                current_college = col0.replace(" Total", "").strip()
                current_top4 = None
                current_grades = {}
                colleges.setdefault(current_college, {
                    "total_enrollments": 0,
                    "top4_codes": {},
                })
                # Parse total enrollment
                try:
                    total = int(col3)
                    colleges[current_college]["total_enrollments"] = total
                except (ValueError, TypeError):
                    pass
                continue

            # TOP4 code line: ",Accounting-0502 Total,,339,3.46%"
            if col1 and "Total" in col1 and not col2:
                # Save previous TOP4
                if current_college and current_top4 and current_grades:
                    _save_top4(colleges, current_college, current_top4,
                              current_top4_name, current_enrollment, current_grades)

                # Parse TOP code and name
                m = re.match(r"(.+)-(\d{4})\s*Total", col1)
                if m:
                    current_top4_name = m.group(1).strip()
                    current_top4 = m.group(2)
                    try:
                        current_enrollment = int(col3)
                    except (ValueError, TypeError):
                        current_enrollment = 0
                    current_grades = {}
                else:
                    current_top4 = None
                continue

            # Grade line: ",,Grade A,214,63.13%"
            if col2 and current_top4 and current_college:
                grade_label = col2.strip()
                normalized = GRADE_MAP.get(grade_label)
                if normalized and col4:
                    try:
                        pct = float(col4) / 100.0
                        # Accumulate (W can come from multiple sources)
                        current_grades[normalized] = current_grades.get(normalized, 0) + pct
                    except (ValueError, TypeError):
                        pass

    # Save last TOP4
    if current_college and current_top4 and current_grades:
        _save_top4(colleges, current_college, current_top4,
                  current_top4_name, current_enrollment, current_grades)

    return colleges


def _save_top4(colleges, college_name, top4, name, enrollment, grades):
    """Save a TOP4 entry to the colleges dict."""
    if not grades:
        return

    # Normalize grades to sum to ~1.0
    total = sum(grades.values())
    if total > 0:
        grades = {k: round(v / total, 4) for k, v in grades.items()}

    colleges[college_name]["top4_codes"][top4] = {
        "name": name,
        "enrollment": enrollment,
        "grades": grades,
    }


def main():
    if len(sys.argv) < 2:
        print("Usage: python -m pipeline.build_calibrations /path/to/GradesSummAll.csv")
        sys.exit(1)

    filepath = sys.argv[1]
    print(f"Parsing {filepath}...")
    colleges = parse_grades_file(filepath)
    print(f"Found {len(colleges)} colleges")

    output_dir = Path(__file__).parent / "calibrations" / "top4"
    output_dir.mkdir(parents=True, exist_ok=True)

    written = 0
    for name, data in sorted(colleges.items()):
        key = college_key(name)
        top4_count = len(data["top4_codes"])
        if top4_count == 0:
            continue

        output = {
            "college_name": name,
            "total_enrollments": data["total_enrollments"],
            "top4_codes": data["top4_codes"],
        }

        path = output_dir / f"{key}.json"
        with open(path, "w") as f:
            json.dump(output, f, indent=2)
        written += 1

    print(f"Written {written} calibration files to {output_dir}")

    # Summary stats
    total_top4s = sum(len(d["top4_codes"]) for d in colleges.values())
    print(f"Total TOP4 codes across all colleges: {total_top4s}")


if __name__ == "__main__":
    main()
