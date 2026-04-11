"""Build system-wide prefix → TOP4 mapping from all CCC master course files.

Reads all MasterCourseFile_*.csv files and extracts course prefix → 4-digit TOP code
mappings. For conflicts (same prefix, different TOP codes across colleges), uses
majority vote.

Usage:
    python -m pipeline.build_prefix_mapping /path/to/mastercoursefiles/

Output:
    Overwrites calibrations/prefix_to_top4.json
"""

import csv
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path


def extract_prefix(course_id: str) -> str:
    """Extract alphabetic prefix from a course ID.

    Examples:
        'AGTC113' → 'AGTC'
        'ENGL 017' → 'ENGL'
        'IT144AC' → 'IT'
        'A J 001' → 'A J'
    """
    course_id = course_id.strip()
    # Match leading alphabetic characters and spaces
    m = re.match(r"^([A-Za-z][A-Za-z ]*)", course_id)
    if not m:
        return ""
    return m.group(1).strip().upper()


def normalize_top4(top_code: str) -> str:
    """Normalize a 6-digit TOP code to 4 digits.

    Examples:
        '011600' → '0116'
        '150100' → '1501'
        '0502' → '0502'
    """
    top_code = top_code.strip()
    # Remove trailing zeros beyond 4 digits
    if len(top_code) == 6:
        return top_code[:4]
    if len(top_code) == 4:
        return top_code
    # Handle other formats
    return top_code[:4].ljust(4, "0")


def build_prefix_mapping(mcf_dir: str) -> dict[str, str]:
    """Build prefix → TOP4 mapping from all master course files."""
    mcf_path = Path(mcf_dir)
    files = sorted(mcf_path.glob("MasterCourseFile_*.csv"))

    if not files:
        print(f"No MasterCourseFile_*.csv found in {mcf_dir}")
        sys.exit(1)

    print(f"Found {len(files)} master course files")

    # Collect all prefix → TOP4 votes
    prefix_votes: dict[str, Counter] = defaultdict(Counter)
    total_rows = 0
    skipped = 0

    for f in files:
        try:
            with open(f, encoding="utf-8", errors="replace") as fh:
                reader = csv.DictReader(fh)
                for row in reader:
                    total_rows += 1
                    course_id = row.get("Course ID", "").strip()
                    top_code = row.get("TOP Code", "").strip()

                    if not course_id or not top_code:
                        skipped += 1
                        continue

                    prefix = extract_prefix(course_id)
                    if not prefix:
                        skipped += 1
                        continue

                    top4 = normalize_top4(top_code)
                    if not top4 or top4 == "0000":
                        skipped += 1
                        continue

                    prefix_votes[prefix][top4] += 1
        except Exception as e:
            print(f"  Warning: error reading {f.name}: {e}")

    print(f"Processed {total_rows} rows ({skipped} skipped)")
    print(f"Found {len(prefix_votes)} unique prefixes")

    # Resolve conflicts via majority vote
    mapping = {}
    conflicts = 0
    for prefix, votes in sorted(prefix_votes.items()):
        top4, count = votes.most_common(1)[0]
        if len(votes) > 1:
            conflicts += 1
        mapping[prefix] = top4

    print(f"Resolved {conflicts} prefix conflicts via majority vote")

    return mapping


def main():
    if len(sys.argv) < 2:
        print("Usage: python -m pipeline.build_prefix_mapping /path/to/mastercoursefiles/")
        sys.exit(1)

    mcf_dir = sys.argv[1]
    mapping = build_prefix_mapping(mcf_dir)

    # Load existing mapping to preserve any manual entries
    output_path = Path(__file__).parent.parent / "ontology" / "calibrations" / "prefix_to_top4.json"
    existing = {}
    if output_path.exists():
        with open(output_path) as f:
            existing = json.load(f)
        print(f"Existing mapping: {len(existing)} entries")

    # Merge: new entries override existing, but keep any existing entries not in new
    merged = {**existing, **mapping}
    new_entries = len(merged) - len(existing)
    print(f"Merged mapping: {len(merged)} entries ({new_entries} new)")

    # Write
    with open(output_path, "w") as f:
        json.dump(merged, f, indent=2, sort_keys=True)
    print(f"Written to {output_path}")


if __name__ == "__main__":
    main()
