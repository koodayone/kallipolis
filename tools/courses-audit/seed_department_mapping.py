"""Seed a per-college department overlay: pypdf gathers evidence, LLM canonicalizes.

For each course-code prefix present in the college's enriched JSON, we
scan the entire catalog PDF via pypdf's text layer and collect every
occurrence of `(PREFIX)` along with a few words of surrounding context.
Those raw observations are sent to Claude in a single call with a prompt
that asks for the canonical California community college department name.

Why this shape:
  - pypdf's role is "bulk evidence gathering," not "parse a specific TOC
    format." That's what it's actually good at.
  - The LLM's role is "distill the messy evidence into a clean canonical
    name," using the college's own wording as its source. It doesn't
    infer names from course titles or trust Gemini's fragmented
    `department` field — it reads what the catalog publishes.
  - Works across all catalog layouts. A TOC entry, a body section
    header, and a cross-reference in running text all contribute signal.
  - One LLM call per college, ~5-10k input tokens, pennies per call.

The operator still reviews the proposed overlay before committing. The
committed file remains the source of truth; the LLM only accelerates the
initial draft.

Usage:
    python tools/courses-audit/seed_department_mapping.py --college {key}
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections import defaultdict
from pathlib import Path

import anthropic
from pypdf import PdfReader

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "backend"))

from courses.department_mapping import (  # noqa: E402
    BASE_PATH,
    OVERLAY_DIR,
    extract_prefix,
    _load_mapping_file,
)

CACHE_DIR = REPO_ROOT / "backend" / "pipeline" / "cache"

# Any parenthesized sequence of 2-8 capital letters (possibly with internal
# spaces for multi-word prefixes like "C S", "V T"). No \b — it misbehaves
# after whitespace in pypdf output.
PREFIX_PARENS_RE = re.compile(r"\(([A-Z][A-Z ]{0,6}[A-Z])\)")

# Context window around each match: enough to pick up "Dance (DANC) (p. 405)"
# or "• Dance (DANC)" but small enough that snippets stay cheap to send.
CTX_CHARS_BEFORE = 60
CTX_CHARS_AFTER = 30

# Cap per prefix to keep LLM input bounded. The first N unique snippets
# per prefix are plenty of signal.
MAX_SNIPPETS_PER_PREFIX = 15
MAX_COURSE_TITLES_PER_PREFIX = 5


def gather_pdf_evidence(pdf_path: Path) -> dict[str, list[str]]:
    """Return {prefix: [context_snippet, ...]} for every parenthesized-prefix
    occurrence anywhere in the catalog PDF.

    Snippets are de-duplicated (case-insensitive, whitespace-normalized)
    and capped at MAX_SNIPPETS_PER_PREFIX per prefix.
    """
    reader = PdfReader(str(pdf_path))
    snippets_by_prefix: dict[str, list[str]] = defaultdict(list)
    seen_by_prefix: dict[str, set[str]] = defaultdict(set)

    for page in reader.pages:
        text = page.extract_text() or ""
        # Normalize internal runs of whitespace so snippets stay compact
        text_flat = re.sub(r"[ \t]+", " ", text)
        for m in PREFIX_PARENS_RE.finditer(text_flat):
            prefix = re.sub(r"\s+", " ", m.group(1))
            start = max(0, m.start() - CTX_CHARS_BEFORE)
            end = min(len(text_flat), m.end() + CTX_CHARS_AFTER)
            raw = text_flat[start:end].strip().replace("\n", " ")
            raw = re.sub(r"\s+", " ", raw)
            key = raw.lower()
            if key in seen_by_prefix[prefix]:
                continue
            seen_by_prefix[prefix].add(key)
            if len(snippets_by_prefix[prefix]) < MAX_SNIPPETS_PER_PREFIX:
                snippets_by_prefix[prefix].append(raw)
    return dict(snippets_by_prefix)


def gather_course_titles(
    enriched_path: Path,
) -> tuple[dict[str, int], dict[str, list[str]]]:
    """Return (prefix → course count, prefix → sample course titles)."""
    with enriched_path.open() as f:
        courses = json.load(f)
    counts: dict[str, int] = defaultdict(int)
    titles: dict[str, list[str]] = defaultdict(list)
    for c in courses:
        p = extract_prefix(c.get("code", ""))
        if not p:
            continue
        counts[p] += 1
        name = (c.get("name") or "").strip()
        if name and len(titles[p]) < MAX_COURSE_TITLES_PER_PREFIX:
            # Avoid near-duplicates that only differ by honors suffix etc.
            if not any(name.lower() == t.lower() for t in titles[p]):
                titles[p].append(name)
    return dict(counts), dict(titles)


def build_llm_prompt(
    college: str,
    evidence: dict[str, list[str]],
    titles: dict[str, list[str]],
    base: dict[str, str],
    prefix_order: list[str],
) -> str:
    """Render the per-college prompt for the canonicalization call."""
    base_examples = "\n".join(
        f"  {prefix:6s} -> {name}"
        for prefix, name in sorted(base.items())
    )

    blocks = []
    for prefix in prefix_order:
        ctxs = evidence.get(prefix, [])
        tts = titles.get(prefix, [])
        block = [f"PREFIX: {prefix}"]
        if ctxs:
            block.append("  Catalog text occurrences (the authoritative signal):")
            for c in ctxs:
                block.append(f"    - {c!r}")
        else:
            block.append(
                "  (no parenthesized-prefix occurrences found in PDF — rely on course titles)"
            )
        if tts:
            block.append("  Sample course titles under this prefix:")
            for t in tts:
                block.append(f"    - {t}")
        blocks.append("\n".join(block))
    prefix_evidence = "\n\n".join(blocks)

    return f"""You are canonicalizing California community college department names for {college}.

For each course-code prefix below, output the canonical human-readable department name the college uses in its catalog. Use the catalog text occurrences as your primary evidence — those are the college's own wording. Course titles are a secondary signal, useful when the catalog text is sparse.

## Style reference (how established prefixes are named)

These canonical names are already committed and illustrate the naming conventions to follow:

{base_examples}

## Rules

1. **Prefer the catalog's own wording.** If catalog text shows "Dance (DANC) (p. 405)" and "• Dance (DANC)", the canonical name is "Dance". Do not paraphrase.
2. **Match the college's level of specificity.** If the college distinguishes "Business/Accounting" from "Business/Finance" as separate departments, preserve that granularity — don't merge them into a generic "Business".
3. **Never emit a bare code.** "MATH" → "Mathematics", never "MATH". "STAT" → "Statistics", never "STAT".
4. **Never emit parenthesized code suffixes.** "Dance (DANC)" is the catalog's raw form; the canonical name is "Dance" without the suffix.
5. **Multi-word prefixes (C S, V T, R T, D A, D H, L A) are real** — preserve their internal spaces.
6. **Stay consistent with the style reference above.** Prefer "Communication Studies" over "Comm Studies". Prefer "Veterinary Technology" over "Vet Tech" unless the college's own wording says "Vet Tech".
7. **Specialty programs** (apprenticeships, adaptive learning, non-credit) follow patterns like "Apprenticeship: Sheet Metal" or "Non-Credit: English" — preserve the program-type qualifier.

## Evidence

{prefix_evidence}

## Output

Return ONLY a JSON object mapping each prefix to its canonical department name, no markdown fences, no commentary:

{{"PREFIX_1": "Canonical Name 1", "PREFIX_2": "Canonical Name 2", ...}}
"""


def extract_json(raw: str) -> dict:
    """Robust JSON extraction — handles plain JSON and fenced code blocks."""
    stripped = raw.strip()
    fence = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", stripped)
    if fence:
        stripped = fence.group(1).strip()
    # Find the first {...} span
    start = stripped.find("{")
    end = stripped.rfind("}")
    if start < 0 or end < 0 or end <= start:
        raise ValueError(f"No JSON object found in LLM response: {stripped[:200]!r}")
    return json.loads(stripped[start : end + 1])


def canonicalize_via_llm(
    college: str,
    evidence: dict[str, list[str]],
    titles: dict[str, list[str]],
    base: dict[str, str],
    prefixes_to_name: list[str],
) -> dict[str, str]:
    """Call Claude to produce {prefix: canonical_name} for the given prefixes."""
    if not prefixes_to_name:
        return {}

    prompt = build_llm_prompt(college, evidence, titles, base, prefixes_to_name)
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}],
    )
    raw = message.content[0].text
    parsed = extract_json(raw)
    # Defensive: coerce values to strings, strip whitespace
    return {str(k): str(v).strip() for k, v in parsed.items()}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    ap.add_argument("--college", required=True)
    ap.add_argument(
        "--verbose",
        action="store_true",
        help="Show evidence and LLM output for each prefix.",
    )
    args = ap.parse_args()

    college = args.college
    pdf_path = CACHE_DIR / f"{college}_catalog.pdf"
    enriched_path = CACHE_DIR / f"{college}_enriched.json"

    if not pdf_path.exists():
        print(f"ERROR: missing catalog PDF: {pdf_path}", file=sys.stderr)
        return 2
    if not enriched_path.exists():
        print(f"ERROR: missing enriched courses: {enriched_path}", file=sys.stderr)
        return 2
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print(
            "ERROR: ANTHROPIC_API_KEY not set in environment. This seeder "
            "calls Claude to canonicalize department names.",
            file=sys.stderr,
        )
        return 2

    print(f"Scanning {pdf_path.name} for parenthesized-prefix evidence...")
    evidence = gather_pdf_evidence(pdf_path)
    print(f"  Collected evidence for {len(evidence)} distinct prefix(es).")

    print(f"Reading course prefixes from {enriched_path.name}...")
    prefix_counts, titles = gather_course_titles(enriched_path)
    print(
        f"  {len(prefix_counts)} distinct prefix(es) across "
        f"{sum(prefix_counts.values())} courses."
    )

    base = _load_mapping_file(BASE_PATH)
    existing_overlay_path = OVERLAY_DIR / f"{college}.json"
    existing_overlay = _load_mapping_file(existing_overlay_path)

    # Prefixes that need a canonical name via LLM: those used in courses,
    # not already in base (base wins by design), and not already committed.
    to_canonicalize = sorted(
        p for p in prefix_counts
        if p not in base and p not in existing_overlay
    )
    # Edge case: prefixes with no PDF evidence AND no course titles — skip,
    # can't send a useful signal to the LLM.
    filtered = [p for p in to_canonicalize if evidence.get(p) or titles.get(p)]
    starved = [p for p in to_canonicalize if p not in filtered]

    print(
        f"Prefixes needing canonicalization: {len(filtered)}  "
        f"(skipping {len(starved)} with no evidence)"
    )
    if args.verbose:
        for p in filtered:
            ctxs = evidence.get(p, [])
            tts = titles.get(p, [])
            print(f"    {p!r}: {len(ctxs)} PDF snippet(s), {len(tts)} course title(s)")

    canonicalized: dict[str, str] = {}
    if filtered:
        print(f"Calling Claude (one request, {len(filtered)} prefixes)...")
        canonicalized = canonicalize_via_llm(
            college, evidence, titles, base, filtered
        )
        print(f"  LLM returned {len(canonicalized)} mapping(s).")

    # Build final proposed overlay
    proposed: dict[str, str] = {}
    missing: dict[str, int] = {}
    for prefix, count in sorted(prefix_counts.items()):
        if prefix in base:
            continue
        if prefix in existing_overlay:
            proposed[prefix] = existing_overlay[prefix]
        elif prefix in canonicalized:
            proposed[prefix] = canonicalized[prefix]
        else:
            missing[prefix] = count

    existing_collisions: list = []
    if existing_overlay_path.exists():
        try:
            existing_collisions = (
                json.loads(existing_overlay_path.read_text())
                .get("_meta", {})
                .get("allowed_collisions", [])
            )
        except json.JSONDecodeError:
            existing_collisions = []

    out_path = OVERLAY_DIR / f"{college}.proposed.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w") as f:
        json.dump(
            {
                "_meta": {
                    "college": college,
                    "last_reviewed": "",
                    "seeded_from": (
                        f"pypdf evidence from {pdf_path.relative_to(REPO_ROOT)} "
                        f"+ Claude canonicalization (claude-sonnet-4-6)"
                    ),
                    "allowed_collisions": existing_collisions,
                },
                "prefixes": dict(sorted(proposed.items())),
            },
            f,
            indent=2,
            ensure_ascii=False,
        )
        f.write("\n")

    print()
    print(f"Wrote proposed overlay: {out_path.relative_to(REPO_ROOT)}")
    print(f"  {len(proposed)} entries populated.")

    if existing_overlay:
        new_entries = set(proposed) - set(existing_overlay)
        removed = set(existing_overlay) - set(proposed)
        changed = {
            k for k in proposed.keys() & existing_overlay.keys()
            if proposed[k] != existing_overlay[k]
        }
        if not (new_entries or removed or changed):
            print("  (identical to committed overlay)")
        else:
            if new_entries:
                print(f"  New entries ({len(new_entries)}):")
                for k in sorted(new_entries):
                    print(f"    + {k!r}: {proposed[k]!r}")
            if removed:
                print(f"  Removed entries ({len(removed)}):")
                for k in sorted(removed):
                    print(f"    - {k!r}: {existing_overlay[k]!r}")
            if changed:
                print(f"  Changed entries ({len(changed)}):")
                for k in sorted(changed):
                    print(f"    ~ {k!r}: {existing_overlay[k]!r} -> {proposed[k]!r}")

    if missing:
        print()
        print(
            f"ACTION REQUIRED: {len(missing)} prefix(es) present in courses but "
            f"not resolved by the LLM (no PDF evidence and no titles, or "
            f"malformed response):"
        )
        for p, count in sorted(missing.items(), key=lambda kv: -kv[1]):
            print(f"    {p!r}: {count} course(s)")
        print("  Add manual entries to the proposed file before renaming to .json.")

    print()
    print(
        f"Next: review {out_path.relative_to(REPO_ROOT)}, spot-check against "
        f"the catalog if anything looks off, set `_meta.last_reviewed`, rename "
        f"to {existing_overlay_path.relative_to(REPO_ROOT)}, commit."
    )
    return 0 if not missing else 1


if __name__ == "__main__":
    sys.exit(main())
