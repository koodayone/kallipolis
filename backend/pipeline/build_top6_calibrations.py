"""Build per-college TOP6 calibration files from DataMart grade distribution data.

Parses top6_grades.csv (hierarchical format — same as the TOP4 file, but with
6-digit TOP codes in the `{name}-{NNNNNN} Total` rows) and writes
backend/ontology/calibrations/top6/{college_key}.json for each college.

Alongside the per-TOP6 entries, each JSON also carries a top4_rollup section
that aggregates the per-TOP6 grade distributions up to 4-digit parent codes.
This gives the student generator a tier-ladder fallback at sample time
without needing to load a separate TOP4 calibration:
    exact TOP6 grades -> parent top4_rollup -> DEFAULT_GRADES.

Usage:
    python -m pipeline.build_top6_calibrations /path/to/top6_grades.csv

Output:
    Overwrites backend/ontology/calibrations/top6/{college_key}.json
"""

import csv
import json
import re
import sys
from pathlib import Path


# Grade label normalization. Mirrors build_calibrations.py exactly so the
# TOP6 grade buckets sum the same way the TOP4 build does.
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


# Override mapping for CSV college names whose snake_case form does not
# match the backend college key convention. The existing TOP4 calibrations
# and the rest of the backend key colleges like "Irvine" as "irvinevalley",
# so TOP6 files need to land under the same names.
CSV_NAME_OVERRIDES: dict[str, str] = {
    "Irvine": "irvinevalley",
    "San Diego City": "sandiegocity",
    "San Diego Mesa": "sandiegomesa",
    "San Diego Miramar": "sandiegomira",
    "San Joaquin Delta": "sanjoquin",
    "San Jose City": "sanjosecity",
    "San Mateo": "csm",
    "San Francisco": "ccsf",
    "Berkeley City": "berkeleycc",
    "Chabot Hayward": "chabot",
    "Deanza": "deanza",
    "Napa": "napavalley",
    "Los Medanos": "losmedanos",
    "Las Positas": "laspositas",
    "Contra Costa": "contracosta",
    "Evergreen Valley": "evergreen",
    "Diablo Valley": "diablo",
    "Santa Rosa": "santarosa",
    "West Valley": "westvalley",
}


def college_key(name: str) -> str:
    """Convert a CSV display name into a backend college key.

    Prefers an explicit override when the snake_case conversion would
    diverge from the backend convention. Otherwise: lowercase, spaces to
    underscores, strip non-alphanumeric.
    """
    name = name.strip()
    if name in CSV_NAME_OVERRIDES:
        return CSV_NAME_OVERRIDES[name]
    key = re.sub(r"\s+", "_", name.lower())
    key = re.sub(r"[^a-z0-9_]", "", key)
    return key


def parse_grades_file(filepath: str) -> dict:
    """Parse top6_grades.csv into per-college, per-TOP6 data.

    Returns: {college_name: {"total_enrollments": int, "top6_codes": {...}}}
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

    # Normalize
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
    if len(sys.argv) < 2:
        print("Usage: python -m pipeline.build_top6_calibrations /path/to/top6_grades.csv")
        sys.exit(1)

    filepath = sys.argv[1]
    print(f"Parsing {filepath}...")
    colleges = parse_grades_file(filepath)
    print(f"Found {len(colleges)} colleges")

    output_dir = Path(__file__).parent.parent / "ontology" / "calibrations" / "top6"
    output_dir.mkdir(parents=True, exist_ok=True)

    written = 0
    for name, data in sorted(colleges.items()):
        key = college_key(name)
        top6_count = len(data["top6_codes"])
        if top6_count == 0:
            continue

        output = {
            "college_name": name,
            "college_key": key,
            "total_enrollments": data["total_enrollments"],
            "top6_codes": data["top6_codes"],
            "top4_rollup": _compute_top4_rollup(data["top6_codes"]),
        }

        path = output_dir / f"{key}.json"
        with open(path, "w") as f:
            json.dump(output, f, indent=2)
        written += 1

    print(f"Written {written} calibration files to {output_dir}")

    total_top6s = sum(len(d["top6_codes"]) for d in colleges.values())
    print(f"Total TOP6 codes across all colleges: {total_top6s}")


if __name__ == "__main__":
    main()
