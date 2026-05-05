"""Re-run the TOP6 lookup against every existing Course node and update
`top_code` where the new lookup logic resolves a code that was previously
unmapped. Idempotent — running it twice produces the same result.

Why this exists: when `backend/ontology/mcf_lookup.py` gains a new
fallback (slash-strip, fullname-prefix, alt-prefix, decimal-suffix
parent), the existing graph stays at the old top_code values until the
loader runs again. Running the loader requires re-extracting from PDF
or replaying the cached `enriched.json` for every college — neither
is necessary just to re-resolve TOP codes. This script just calls
`lookup_top6_per_course` over the codes already in Neo4j and writes
the results back.

Read/write to Neo4j is via `docker exec kallipolis-neo4j-1 cypher-shell`
because the bolt port isn't published to the host.

Usage:
    python tools/courses-audit/relookup_top_codes.py
    python tools/courses-audit/relookup_top_codes.py --college sbcc
    python tools/courses-audit/relookup_top_codes.py --dry-run
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO / "backend"))

from ontology.mcf_lookup import lookup_top6_per_course  # noqa: E402

# Featured colleges — same list as the audit.
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


def _cypher_shell(query: str) -> str:
    """Run a Cypher query through `docker exec cypher-shell` and return
    stdout. Pass values inline as Cypher literals — cypher-shell's
    --param requires JSON that conflicts with the shell's quote
    handling for non-trivial values, so we avoid it."""
    cmd = [
        "docker", "exec", "-i", "kallipolis-neo4j-1", "cypher-shell",
        "-u", "neo4j", "-p", "kallipolis_dev", "--format", "plain",
        query,
    ]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if r.returncode != 0:
        raise RuntimeError(f"cypher-shell failed: {r.stderr.strip()[:500]}")
    return r.stdout


def _cypher_str(s: str) -> str:
    """Quote a Python string as a Cypher single-quoted string literal."""
    return "'" + s.replace("\\", "\\\\").replace("'", "\\'") + "'"


def fetch_courses_for(name: str) -> list[tuple[str, str]]:
    """Return [(code, current_top_code)] for one college's Course nodes,
    using a delimiter-joined query to avoid cypher-shell CSV quirks."""
    out = _cypher_shell(
        f"MATCH (c:Course {{college: '{name}'}}) "
        "RETURN c.code + '|||' + coalesce(c.top_code, '') AS line"
    )
    rows: list[tuple[str, str]] = []
    for line in out.splitlines()[1:]:  # skip header
        s = line.strip()
        if not s or s == "NULL":
            continue
        if len(s) >= 2 and s[0] == '"' and s[-1] == '"':
            s = s[1:-1]
        parts = s.split("|||")
        if len(parts) == 2:
            rows.append((parts[0], parts[1]))
    return rows


def apply_updates(name: str, updates: list[dict]) -> None:
    """Write the new top_code values via an UNWIND with the batch
    embedded as a Cypher literal list. Sized in chunks to keep the
    statement length well under the cypher-shell command line limit."""
    if not updates:
        return
    CHUNK = 200
    for i in range(0, len(updates), CHUNK):
        chunk = updates[i:i + CHUNK]
        rows_cypher = ", ".join(
            f"{{code: {_cypher_str(u['code'])}, "
            f"top_code: {_cypher_str(u['top_code'])}}}"
            for u in chunk
        )
        query = (
            f"UNWIND [{rows_cypher}] AS row "
            f"MATCH (c:Course {{code: row.code, college: {_cypher_str(name)}}}) "
            f"SET c.top_code = row.top_code "
            f"RETURN count(c) AS n"
        )
        _cypher_shell(query)


def relookup_college(key: str, name: str, dry_run: bool) -> dict:
    """Run lookup_top6_per_course for one college's Course nodes and
    write back any newly-resolved top_code values."""
    rows = fetch_courses_for(name)
    if not rows:
        return {"college": key, "skipped": "no Course nodes"}

    codes = [r[0] for r in rows]
    old_by_code = {c: t for c, t in rows}
    new_by_code = lookup_top6_per_course(codes, name)

    newly_resolved: list[tuple[str, str]] = []
    changed: list[tuple[str, str, str]] = []
    lost: list[tuple[str, str]] = []
    unchanged_with = unchanged_without = 0
    for code, new_top in new_by_code.items():
        old_top = old_by_code.get(code, "")
        if not old_top and new_top:
            newly_resolved.append((code, new_top))
        elif old_top and not new_top:
            lost.append((code, old_top))
            unchanged_with += 1
        elif old_top and new_top and old_top != new_top:
            changed.append((code, old_top, new_top))
        elif old_top:
            unchanged_with += 1
        else:
            unchanged_without += 1

    stats = {
        "college": key,
        "total": len(codes),
        "newly_resolved": len(newly_resolved),
        "changed": len(changed),
        "lost_in_new_lookup_kept_old": len(lost),
        "already_had_top": unchanged_with,
        "still_unmapped": unchanged_without,
    }

    if dry_run:
        return stats

    updates = [
        {"code": c, "top_code": t} for c, t in newly_resolved
    ] + [
        {"code": c, "top_code": new} for c, _, new in changed
    ]
    apply_updates(name, updates)
    return stats


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    ap.add_argument("--college", help="single college key")
    ap.add_argument("--dry-run", action="store_true",
                    help="report what would change but don't write")
    args = ap.parse_args()

    targets = (
        [(k, n) for k, n in COLLEGES if k == args.college]
        if args.college
        else COLLEGES
    )
    if not targets:
        print(f"unknown college key: {args.college}", file=sys.stderr)
        return 2

    print(
        f"{'key':18s} {'total':>6s} {'newly':>6s} {'chg':>4s} "
        f"{'lost':>5s} {'have':>6s} {'none':>6s}  ({'dry-run' if args.dry_run else 'WRITE'})"
    )
    print("-" * 80)
    grand_newly = 0
    for key, name in targets:
        s = relookup_college(key, name, args.dry_run)
        if "skipped" in s:
            print(f"{key:18s} (skipped: {s['skipped']})")
            continue
        print(
            f"{key:18s} {s['total']:>6d} {s['newly_resolved']:>6d} "
            f"{s['changed']:>4d} {s['lost_in_new_lookup_kept_old']:>5d} "
            f"{s['already_had_top']:>6d} {s['still_unmapped']:>6d}"
        )
        grand_newly += s["newly_resolved"]
    print("-" * 80)
    print(
        f"{'NEW TOP CODES':18s}: +{grand_newly}"
        f"{' (dry run — not written)' if args.dry_run else ''}"
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())
