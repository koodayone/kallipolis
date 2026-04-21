"""Audit-only: majority-vote cleanup of the `department` field in an enriched file.

NOTE — retired from production use. Stage 2.5 of the main pipeline
(`backend/courses/department_mapping/` + `backend/pipeline/run.py`) now
canonicalizes `department` via a committed prefix→name mapping that is
reviewed by the operator during college onboarding. That path guarantees
human-readable names ("Statistics", not bare "STAT"), which majority-vote
cannot when Gemini never emitted a clean variant for a prefix.

Kept here as a debugging tool: useful for surveying the shape of Gemini's
raw department output on a fresh extraction before the overlay is seeded,
or for comparing a new Gemini output against the baseline fragmentation
pattern. Does NOT produce data suitable for production — always prefer
the pipeline's Stage 2.5 output.

What it does:
  1. Extracts the code prefix from each course's `code` field
  2. Per prefix, collects all `department` strings Gemini emitted
  3. Picks a canonical name per prefix using deterministic rules:
       a. Prefer the longest variant that is neither the bare code nor ends with
          " (CODE)"
       b. Fallback: strip trailing " (CODE)" from any parens form
       c. Last resort: use the bare code
  4. Rewrites each course's `department` to the canonical value

Usage (debugging only):
    python3 normalize_departments.py --dry-run backend/pipeline/cache/foothill_enriched.json
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from collections import defaultdict
from pathlib import Path


CODE_PREFIX_RE = re.compile(r"^([A-Z][A-Z ]*?)\s+[A-Z]?\d")


def code_prefix(code: str) -> str | None:
    """Extract the subject prefix from a course code.

    Examples:
      'MATH 1A'   -> 'MATH'
      'C S 81'    -> 'C S'
      'POLS C1000' -> 'POLS'
    """
    m = CODE_PREFIX_RE.match(code.strip())
    return m.group(1) if m else None


def build_canonical_map(
    courses: list[dict],
) -> tuple[dict[str, str], list[tuple[str, str]]]:
    """Map each code prefix to a single canonical department string.

    Per prefix, variants are partitioned into four buckets:
      - own_parens:     ends with " (PREFIX)" — Gemini confirming the prefix
      - bare:           equals PREFIX exactly
      - foreign_parens: ends with " (OTHER)" — Gemini mislabeling with a
                        different subject's code
      - other:          anything else (including plain names like "Dance")

    Decision, in order:
      1. If any own_parens variant exists, strip its suffix and use it. Most
         reliable signal because Gemini is self-identifying the subject.
      2. Else use the highest-count `other` variant, provided it's not
         outnumbered by the bare variant.
      3. Else use the bare prefix. (Neutral — bare code is better than an
         unrelated category label.)
      4. Else (only foreign_parens or nothing remains) fall back to the bare
         prefix as the canonical — refuse to propagate a clearly-wrong label.

    Returns (canonical_map, suspicious_prefixes). Suspicious = prefixes where
    every variant was a foreign-parens mislabel, meaning we fell back to the
    bare code. These warrant manual review or prompt tuning upstream.
    """
    from collections import Counter

    counts_by_prefix: dict[str, Counter] = defaultdict(Counter)
    for c in courses:
        prefix = code_prefix(c.get("code", ""))
        dept = (c.get("department") or "").strip()
        if prefix and dept:
            counts_by_prefix[prefix][dept] += 1

    parens_any_re = re.compile(r"\s*\(([A-Z][A-Z ]*)\)\s*$")

    canonical: dict[str, str] = {}
    suspicious: list[tuple[str, str]] = []
    for prefix, counts in counts_by_prefix.items():
        own_parens_suffix = f" ({prefix})"
        own_parens_variants: list[tuple[str, int]] = []
        bare_count = 0
        foreign_parens_variants: list[tuple[str, int]] = []
        other_variants: list[tuple[str, int]] = []

        for dept, count in counts.items():
            if dept == prefix:
                bare_count = count
                continue
            if dept.endswith(own_parens_suffix):
                own_parens_variants.append((dept, count))
                continue
            m = parens_any_re.search(dept)
            if m and m.group(1) != prefix:
                foreign_parens_variants.append((dept, count))
            else:
                other_variants.append((dept, count))

        # 1. Own-prefix parens wins (strip suffix)
        if own_parens_variants:
            best = max(own_parens_variants, key=lambda x: (x[1], len(x[0])))
            canonical[prefix] = best[0][: -len(own_parens_suffix)]
            continue

        # 2. Best "other" variant, if not beaten by bare
        if other_variants:
            best = max(other_variants, key=lambda x: (x[1], len(x[0])))
            if best[1] >= bare_count:
                canonical[prefix] = best[0]
                continue

        # 3. Bare prefix
        if bare_count > 0:
            canonical[prefix] = prefix
            continue

        # 4. Only foreign-parens or similar junk — fall back to bare code
        suspicious.append((prefix, str(sorted(counts.keys()))))
        canonical[prefix] = prefix

    return canonical, suspicious


def normalize_courses(courses: list[dict], canonical: dict[str, str]) -> tuple[list[dict], int]:
    """Return a new list with `department` rewritten. Also return #changed."""
    changed = 0
    out = []
    for c in courses:
        c = dict(c)  # shallow copy
        prefix = code_prefix(c.get("code", ""))
        if prefix and prefix in canonical:
            new_dept = canonical[prefix]
            if c.get("department") != new_dept:
                changed += 1
            c["department"] = new_dept
        out.append(c)
    return out, changed


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("path", type=Path, help="Path to {college}_enriched.json")
    ap.add_argument("--dry-run", action="store_true", help="Print mapping, do not write")
    ap.add_argument("--no-backup", action="store_true", help="Skip writing .bak file")
    args = ap.parse_args()

    if not args.path.exists():
        print(f"ERROR: {args.path} not found", file=sys.stderr)
        return 2

    with args.path.open() as f:
        courses = json.load(f)

    before_depts = {(c.get("department") or "") for c in courses}
    canonical, suspicious = build_canonical_map(courses)
    normalized, changed = normalize_courses(courses, canonical)
    after_depts = {c["department"] for c in normalized}

    print(f"Canonical mapping ({len(canonical)} prefixes):")
    for prefix in sorted(canonical):
        print(f"  {prefix:<8} -> {canonical[prefix]!r}")
    print()
    print(f"Before: {len(before_depts)} unique department strings")
    print(f"After:  {len(after_depts)} unique department strings")
    print(f"Courses with department rewritten: {changed}")
    if suspicious:
        print(f"\nFell back to bare code ({len(suspicious)}) — all Gemini variants were foreign-prefix mislabels:")
        for prefix, variants in suspicious:
            print(f"  {prefix:<8}  Gemini emitted: {variants}")
        print(f"  (fix upstream: Gemini should emit 'Subject Name ({prefix})' or 'Subject Name')")

    if args.dry_run:
        print("\n(dry run — no files written)")
        return 0

    if not args.no_backup:
        bak = args.path.with_suffix(args.path.suffix + ".pre_dept_norm.bak")
        shutil.copy(args.path, bak)
        print(f"\nBackup: {bak}")

    with args.path.open("w") as f:
        json.dump(normalized, f, indent=2, ensure_ascii=False)
    print(f"Wrote:  {args.path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
