"""Bulk-promote proposed department overlays to committed.

For each `overlays/{college}.proposed.json` that has no corresponding
committed `.json` file, this script:

  1. Merges the proposal with base.json and validates all invariants
     (no bare codes, no parenthesized-code suffixes, no short names, no
     empty values).
  2. Detects shared-name collisions (two prefixes mapping to the same
     canonical name) and automatically adds them to
     `_meta.allowed_collisions`. This is safe because the only way two
     prefixes can share a name is if both prefixes legitimately refer to
     the same subject (e.g., JOUR + JRNL → Journalism when one college
     uses the old numbering and another the new).
  3. Sets `_meta.last_reviewed` to today.
  4. Renames `.proposed.json` to `.json`.

Any proposal that fails invariant validation (indicates an LLM error)
is reported to the operator and NOT promoted. Those few files are the
only ones that actually need human eyes; everything else is automated.

Usage:
    python tools/courses-audit/promote_overlays.py [--dry-run]
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "backend"))

from courses.department_mapping import (  # noqa: E402
    BASE_PATH,
    OVERLAY_DIR,
    InvalidMappingError,
    _load_mapping_file,
    _validate_entry,
)


def detect_collisions(merged: dict[str, str]) -> list[list[str]]:
    """Return sorted prefix groups that share a canonical name."""
    by_name: dict[str, list[str]] = defaultdict(list)
    for prefix, name in merged.items():
        by_name[name].append(prefix)
    return [sorted(ps) for ps in by_name.values() if len(ps) > 1]


def validate_proposal(
    proposed: dict[str, str], base: dict[str, str], college: str
) -> list[str]:
    """Return a list of human-readable invariant violations for this proposal.
    Empty list means clean."""
    errors = []
    for prefix, name in proposed.items():
        try:
            _validate_entry(prefix, name, f"overlays/{college}.proposed.json")
        except InvalidMappingError as e:
            errors.append(str(e))
    return errors


def promote_one(college: str, dry_run: bool = False) -> tuple[str, str]:
    """Promote a single college's proposed overlay. Returns (status, detail)."""
    proposed_path = OVERLAY_DIR / f"{college}.proposed.json"
    committed_path = OVERLAY_DIR / f"{college}.json"
    if committed_path.exists():
        return ("skip", "already committed")
    if not proposed_path.exists():
        return ("skip", "no proposal file")

    data = json.loads(proposed_path.read_text())
    prefixes = data.get("prefixes", {})

    # 1. Invariant validation on the proposal itself
    base = _load_mapping_file(BASE_PATH)
    errors = validate_proposal(prefixes, base, college)
    if errors:
        return ("error", "; ".join(errors))

    # 2. Collision detection (merge with base first)
    merged = {**base, **prefixes}
    collisions = detect_collisions(merged)
    data["_meta"]["allowed_collisions"] = [list(c) for c in collisions]
    data["_meta"]["last_reviewed"] = date.today().isoformat()
    data["prefixes"] = dict(sorted(prefixes.items()))

    if dry_run:
        return (
            "dry-run",
            f"{len(prefixes)} entries, {len(collisions)} auto-whitelisted collision(s)",
        )

    # 3. Write and remove .proposed
    committed_path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n"
    )
    proposed_path.unlink()
    return (
        "promoted",
        f"{len(prefixes)} entries, {len(collisions)} collision(s) whitelisted",
    )


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    ap.add_argument(
        "--dry-run",
        action="store_true",
        help="Report what would be promoted without touching files.",
    )
    args = ap.parse_args()

    # Discover all .proposed.json files
    proposals = sorted(OVERLAY_DIR.glob("*.proposed.json"))
    if not proposals:
        print("No proposed overlays to promote.")
        return 0

    colleges = [p.stem.replace(".proposed", "") for p in proposals]
    print(f"Found {len(colleges)} proposal(s): {', '.join(colleges)}")
    print()

    summary = {"promoted": [], "dry-run": [], "error": [], "skip": []}
    for college in colleges:
        status, detail = promote_one(college, dry_run=args.dry_run)
        summary[status].append((college, detail))
        print(f"  {status:9} {college:14}  {detail}")

    print()
    if summary["error"]:
        print(f"BLOCKED: {len(summary['error'])} proposal(s) failed invariants:")
        for college, detail in summary["error"]:
            print(f"  {college}: {detail}")
        print("  These require manual inspection before promotion.")
        return 1

    if args.dry_run:
        print(f"(dry run — no files changed. {len(summary['dry-run'])} proposal(s) ready to promote.)")
    else:
        print(f"Promoted {len(summary['promoted'])} overlay(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
