"""Delete catalog-extraction artifact Course nodes from Neo4j.

Apply the same `is_artifact` rules used at extraction time
(`backend/courses/extraction_filter.py`) to every Course node already
in the graph. Rows whose code/name matches an artifact pattern are
DETACH-DELETEd along with their CONTAINS / PREPARES_FOR edges.

This is a one-time cleanup for graphs that were loaded BEFORE the
extraction filter was wired into `scrape_pdf.py`. Future loads
won't produce artifacts because the filter runs at extraction time.

Always dry-run first. The default mode prints the artifacts grouped
by reason, with counts per college, and writes nothing.

Usage:
    python tools/courses-audit/delete_artifact_courses.py            # dry-run
    python tools/courses-audit/delete_artifact_courses.py --college sbcc
    python tools/courses-audit/delete_artifact_courses.py --apply    # delete
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO / "backend"))

from courses.extraction_filter import is_artifact  # noqa: E402

COLLEGES = [
    ("shasta", "Shasta College"),
    ("siskiyous", "College of the Siskiyous"),
    ("lassen", "Lassen College"),
    ("mendocino", "Mendocino College"),
    ("butte", "Butte College"),
    ("sacramentocity", "Sacramento City College"),
    ("laketahoe", "Lake Tahoe Community College"),
    ("foothill", "Foothill College"),
    ("berkeleycc", "Berkeley City College"),
    ("napavalley", "Napa Valley College"),
    ("hartnell", "Hartnell College"),
    ("sequoias", "College of the Sequoias"),
    ("merced", "Merced College"),
    ("cerrocoso", "Cerro Coso Community College"),
    ("sbcc", "Santa Barbara City College"),
    ("oxnard", "Oxnard College"),
    ("compton", "Compton College"),
    ("lavalley", "Los Angeles Valley College"),
    ("irvinevalley", "Irvine Valley College"),
    ("desert", "College of the Desert"),
    ("sandiegocity", "San Diego City College"),
    ("imperialvalley", "Imperial Valley College"),
]


def _cypher(query: str) -> str:
    cmd = [
        "docker", "exec", "-i", "kallipolis-neo4j-1", "cypher-shell",
        "-u", "neo4j", "-p", "kallipolis_dev", "--format", "plain", query,
    ]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if r.returncode != 0:
        raise RuntimeError(f"cypher-shell failed: {r.stderr.strip()[:500]}")
    return r.stdout


def _cypher_str(s: str) -> str:
    return "'" + s.replace("\\", "\\\\").replace("'", "\\'") + "'"


def fetch_courses_for(name: str) -> list[tuple[str, str]]:
    """[(code, name)] for a college via delim-joined output."""
    out = _cypher(
        f"MATCH (c:Course {{college: '{name}'}}) "
        "RETURN c.code + '|||' + coalesce(c.name, '') AS line"
    )
    rows = []
    for line in out.splitlines()[1:]:
        s = line.strip()
        if not s or s == "NULL":
            continue
        if len(s) >= 2 and s[0] == '"' and s[-1] == '"':
            s = s[1:-1]
        parts = s.split("|||")
        if len(parts) == 2:
            rows.append((parts[0], parts[1]))
    return rows


def identify_artifacts(college_name: str) -> list[tuple[str, str, str]]:
    """Return [(code, name, reason), ...] for each artifact at this college."""
    out = []
    for code, name in fetch_courses_for(college_name):
        is_art, reason = is_artifact(code, name)
        if is_art:
            out.append((code, name, reason))
    return out


def delete_artifacts(college_name: str, codes: list[str]) -> int:
    """DETACH DELETE Course nodes for the given codes at this college.
    Returns the number of nodes actually removed."""
    if not codes:
        return 0
    CHUNK = 200
    total = 0
    for i in range(0, len(codes), CHUNK):
        chunk = codes[i:i + CHUNK]
        codes_lit = ", ".join(_cypher_str(c) for c in chunk)
        out = _cypher(
            f"MATCH (c:Course) "
            f"WHERE c.college = {_cypher_str(college_name)} "
            f"AND c.code IN [{codes_lit}] "
            f"DETACH DELETE c "
            f"RETURN count(c) AS n"
        )
        # Last non-header line is the count
        lines = [l.strip() for l in out.splitlines()[1:] if l.strip()]
        if lines:
            try:
                total += int(lines[-1])
            except ValueError:
                pass
    return total


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    ap.add_argument("--college", help="single college key")
    ap.add_argument("--apply", action="store_true",
                    help="actually DELETE (default is dry-run)")
    args = ap.parse_args()

    targets = (
        [(k, n) for k, n in COLLEGES if k == args.college]
        if args.college
        else COLLEGES
    )
    if not targets:
        print(f"unknown college key: {args.college}", file=sys.stderr)
        return 2

    mode = "APPLY" if args.apply else "dry-run"
    print(f"{'key':18s} {'total':>6s} {'artif':>6s}  reasons  ({mode})")
    print("-" * 90)

    grand_total = 0
    grand_artif = 0
    reason_totals: Counter = Counter()
    per_college_artifacts: dict[str, list[tuple[str, str, str]]] = {}

    for key, name in targets:
        artifacts = identify_artifacts(name)
        per_college_artifacts[key] = artifacts
        total = len(fetch_courses_for(name))
        grand_total += total
        grand_artif += len(artifacts)

        # Bucket reasons
        rc: Counter = Counter()
        for _, _, r in artifacts:
            rc[r] += 1
            reason_totals[r] += 1

        # Format top reasons inline
        top = ", ".join(f"{r.split(':')[0]}:{n}" for r, n in rc.most_common(3))
        print(f"{key:18s} {total:>6d} {len(artifacts):>6d}  {top}")

    print("-" * 90)
    print(f"{'GRAND TOTAL':18s} {grand_total:>6d} {grand_artif:>6d}")
    print(f"\nReasons across all colleges:")
    for r, n in reason_totals.most_common():
        print(f"  {n:>5d}  {r}")

    if not args.apply:
        print(f"\n(dry-run — pass --apply to actually delete)")
        return 0

    # APPLY pass
    print(f"\nApplying deletes…")
    grand_deleted = 0
    for key, name in targets:
        artifacts = per_college_artifacts[key]
        codes = [c for c, _, _ in artifacts]
        deleted = delete_artifacts(name, codes)
        grand_deleted += deleted
        if deleted:
            print(f"  {key:18s} deleted {deleted}")

    print(f"\nDELETED {grand_deleted} artifact Course nodes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
