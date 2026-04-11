"""
Parse the 26-college 4-digit TOP code grade distribution CSV into per-college JSON files.

Usage:
    python -m pipeline.calibrations.parse_top4 /path/to/26_4top_grades.csv
"""

import json
import re
import sys
from pathlib import Path

COLLEGE_NAME_TO_KEY = {
    "Alameda": "alameda",
    "Berkeley City": "berkeleycc",
    "Cabrillo": "cabrillo",
    "Canada": "canada",
    "Chabot Hayward": "chabot",
    "Contra Costa": "contracosta",
    "Deanza": "deanza",
    "Diablo Valley": "diablo",
    "Evergreen Valley": "evergreen",
    "Foothill": "foothill",
    "Gavilan": "gavilan",
    "Laney": "laney",
    "Las Positas": "laspositas",
    "Los Medanos": "losmedanos",
    "Marin": "marin",
    "Merritt": "merritt",
    "Mission": "mission",
    "Napa": "napavalley",
    "Ohlone": "ohlone",
    "San Francisco": "ccsf",
    "San Jose City": "sanjosecity",
    "San Mateo": "csm",
    "Santa Rosa": "santarosa",
    "Skyline": "skyline",
    "Solano": "solano",
    "West Valley": "westvalley",
}

GRADE_MAP = {
    "Grade A": "A",
    "Grade B": "B",
    "Grade C": "C",
    "Grade D": "D",
    "Grade F": "F",
    "Withdrew": "W",
    "Pass": "P",
}


def parse_csv(csv_path: str) -> dict[str, dict]:
    """Parse the multi-college 4-digit grade distribution CSV."""
    lines = open(csv_path).readlines()

    colleges = {}
    current_college = None
    current_top4 = None

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Parse CSV fields
        parts = []
        in_quote = False
        cf = ""
        for ch in line:
            if ch == '"':
                in_quote = not in_quote
            elif ch == "," and not in_quote:
                parts.append(cf.strip())
                cf = ""
            else:
                cf += ch
        parts.append(cf.strip())

        # College total line
        if parts[0] and "Total" in parts[0] and not parts[1]:
            match = re.match(r"(.+?)\s+Total", parts[0])
            if match:
                name = match.group(1).strip()
                key = COLLEGE_NAME_TO_KEY.get(name)
                if key:
                    total = int(parts[3].replace(",", ""))
                    current_college = key
                    colleges[key] = {
                        "college_name": name,
                        "total_enrollments": total,
                        "top4_codes": {},
                    }
                    current_top4 = None
                else:
                    current_college = None
            continue

        # TOP4 code line
        if current_college and parts[1] and "Total" in parts[1]:
            match = re.match(r"(.+?)-(\d{4})\s+Total", parts[1])
            if match:
                top_name = match.group(1).strip()
                top_code = match.group(2)
                enrollment = int(parts[3].replace(",", ""))
                current_top4 = top_code
                colleges[current_college]["top4_codes"][top_code] = {
                    "name": top_name,
                    "enrollment": enrollment,
                    "grades": {},
                }
            continue

        # Grade line
        if current_college and current_top4 and parts[2]:
            grade_label = parts[2].strip()
            grade = GRADE_MAP.get(grade_label)
            if grade:
                try:
                    pct = float(parts[4].replace("%", "")) / 100
                    colleges[current_college]["top4_codes"][current_top4]["grades"][grade] = round(pct, 4)
                except (ValueError, IndexError):
                    pass

    return colleges


def main():
    if len(sys.argv) < 2:
        csv_path = "/Users/dayonekoo/Desktop/26_4top_grades.csv"
    else:
        csv_path = sys.argv[1]

    colleges = parse_csv(csv_path)

    out_dir = Path(__file__).parent / "top4"
    out_dir.mkdir(exist_ok=True)

    for key, data in colleges.items():
        out_path = out_dir / f"{key}.json"
        with open(out_path, "w") as f:
            json.dump(data, f, indent=2)

    print(f"Parsed {len(colleges)} colleges")
    for key in sorted(colleges):
        c = colleges[key]
        print(f"  {key:<15} {c['total_enrollments']:>7,} enrollments, {len(c['top4_codes']):>3} TOP4 codes")


if __name__ == "__main__":
    main()
