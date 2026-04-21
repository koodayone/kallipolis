"""Department name resolution for the course-extraction pipeline.

The `department` field on a course is a derived, human-readable display value
computed from the course code's prefix via a committed `{prefix → name}`
mapping. The mapping has two layers:

  base.json          — prefixes with stable names across California CCCs
                       (MATH → Mathematics, ENGL → English, ...)
  overlays/{key}.json — per-college prefixes for local programs
                       (APSM → Apprenticeship: Sheet Metal, ...)

Resolution is `{**base, **overlay[college]}` — the college overlay wins on
any conflict, which lets a college supply a locally-preferred name without
disturbing the base.

Why this module exists: Gemini Flash emits the `department` field
inconsistently during extraction (e.g., "Dance" vs "Dance (DANC)" vs "DANC"
vs unrelated category labels like "Transfer Studies: CSU GE"). Fragmenting
a course corpus into departments keyed by raw Gemini output produces
duplicate UI buckets. The prefix of the course code is a reliable identity,
so we key canonical names off the prefix and ignore Gemini's department
output.
"""
from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Optional

MAPPING_DIR = Path(__file__).resolve().parent
BASE_PATH = MAPPING_DIR / "base.json"
OVERLAY_DIR = MAPPING_DIR / "overlays"

# A course code's prefix is everything before the final whitespace-separated
# token, provided that token looks like a course number: an optional leading
# letter followed by 1-4 digits and up to 2 trailing letters. Handles:
#   "MATH 1A"    → "MATH"
#   "C S 81"     → "C S"      (multi-word prefix)
#   "V T 51A"    → "V T"      (multi-word prefix, trailing letter)
#   "POLS C1000" → "POLS"     (CCCN-style code, leading letter on number)
#   "MED A 10"   → "MED A"    (3-token code, rare)
#   "MATH 1AHP"  → "MATH"     (honors suffix, 3 trailing letters)
_COURSE_NUMBER_RE = re.compile(r"^[A-Z]?\d{1,4}[A-Z]{0,4}$")

# For invariant validation: reject values like "Dance (DANC)" that contain a
# parenthesized all-caps suffix — that's the fragmentation pattern this
# module exists to eliminate.
_PAREN_CODE_SUFFIX_RE = re.compile(r"\s*\([A-Z][A-Z ]{1,7}\)\s*$")


class UnknownPrefixError(KeyError):
    """Raised when a prefix has no mapping entry and strict mode is on."""

    def __init__(self, prefix: str, college: str):
        super().__init__(prefix)
        self.prefix = prefix
        self.college = college

    def __str__(self):
        return (
            f"No department mapping for prefix {self.prefix!r} at college "
            f"{self.college!r}. Add an entry to "
            f"backend/courses/department_mapping/overlays/{self.college}.json "
            f"under \"prefixes\"."
        )


class InvalidMappingError(ValueError):
    """Raised when a mapping file fails invariant checks at load time."""


# Catalog-specific annotation suffixes that some colleges append to course
# codes to flag transfer status, prerequisites, etc. (Shasta uses `*` and
# `#`, for example). They are not part of the course code proper — strip
# them before parsing so the prefix resolver doesn't reject these courses.
_CODE_ANNOTATION_SUFFIX_RE = re.compile(r"[*#†‡§¶@!?]+\s*$")


def extract_prefix(code: str) -> Optional[str]:
    """Return the subject prefix of a course code, or None if malformed."""
    code = (code or "").strip()
    code = _CODE_ANNOTATION_SUFFIX_RE.sub("", code).strip()
    if not code:
        return None
    idx = code.rfind(" ")
    if idx < 0:
        return None
    prefix = code[:idx].strip()
    suffix = code[idx + 1 :].strip()
    if not prefix or not _COURSE_NUMBER_RE.match(suffix):
        return None
    return prefix


def _validate_entry(prefix: str, name: str, file_label: str) -> None:
    """Enforce invariants on a single {prefix: name} pair."""
    if not isinstance(name, str) or not name:
        raise InvalidMappingError(
            f"{file_label}: prefix {prefix!r} has empty or non-string name"
        )
    if name == prefix:
        raise InvalidMappingError(
            f"{file_label}: prefix {prefix!r} maps to its bare code "
            f"(human-readable names required; bare codes are a UI failure)"
        )
    if len(name) < 3:
        raise InvalidMappingError(
            f"{file_label}: prefix {prefix!r} maps to {name!r} (too short, "
            f"need ≥3 chars)"
        )
    if _PAREN_CODE_SUFFIX_RE.search(name):
        raise InvalidMappingError(
            f"{file_label}: prefix {prefix!r} maps to {name!r} which contains "
            f"a parenthesized code suffix — strip it"
        )


def _load_mapping_file(path: Path) -> dict[str, str]:
    """Parse a mapping file, validate invariants, return {prefix: name}."""
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError as e:
        raise InvalidMappingError(f"{path}: invalid JSON: {e}") from e
    prefixes = data.get("prefixes")
    if not isinstance(prefixes, dict):
        raise InvalidMappingError(
            f"{path}: missing or non-dict 'prefixes' key"
        )
    # Error label: repo-relative path when the file lives under the repo,
    # otherwise the absolute path (typical for unit tests using tmp_path).
    try:
        label = str(path.relative_to(MAPPING_DIR.parent.parent))
    except ValueError:
        label = str(path)
    for prefix, name in prefixes.items():
        _validate_entry(prefix, name, label)
    return dict(prefixes)


@lru_cache(maxsize=None)
def resolve(college: str) -> dict[str, str]:
    """Return the merged {prefix: canonical_name} mapping for a college.

    Base is loaded once; per-college overlay is layered on top (overlay
    wins). Raises InvalidMappingError if any file fails invariant checks.
    """
    base = _load_mapping_file(BASE_PATH)
    overlay = _load_mapping_file(OVERLAY_DIR / f"{college}.json")
    merged = {**base, **overlay}
    # Collision check: different prefixes mapping to the same name are
    # allowed only when explicitly whitelisted. `_meta.allowed_collisions`
    # can be declared in base.json (for cross-college cases like POLI/POLS
    # both meaning "Political Science") or in the per-college overlay.
    allowed = _load_allowed_collisions(BASE_PATH) | _load_allowed_collisions(
        OVERLAY_DIR / f"{college}.json"
    )
    _check_collisions(merged, allowed, college)
    return merged


def _load_allowed_collisions(path: Path) -> set[frozenset[str]]:
    """Read `_meta.allowed_collisions` from a mapping file, as set of frozensets."""
    if not path.exists():
        return set()
    data = json.loads(path.read_text())
    raw = data.get("_meta", {}).get("allowed_collisions", [])
    return {frozenset(group) for group in raw}


def _check_collisions(
    mapping: dict[str, str],
    allowed: set[frozenset[str]],
    college: str,
) -> None:
    """Reject unintended many-to-one prefix→name collapses."""
    from collections import defaultdict

    by_name: dict[str, list[str]] = defaultdict(list)
    for prefix, name in mapping.items():
        by_name[name].append(prefix)
    for name, prefixes in by_name.items():
        if len(prefixes) < 2:
            continue
        if frozenset(prefixes) in allowed:
            continue
        raise InvalidMappingError(
            f"{college}: prefixes {sorted(prefixes)} all map to {name!r}. "
            f"If intentional, add [{sorted(prefixes)}] to _meta.allowed_collisions "
            f"in overlays/{college}.json."
        )


def canonical_name(code: str, college: str, *, strict: bool = True) -> str:
    """Return the canonical human-readable department name for a course code.

    In strict mode (default), an unmapped prefix raises UnknownPrefixError
    — the pipeline is expected to fail loudly rather than propagate bare
    codes downstream.

    In non-strict mode (escape hatch for operational rollouts), an unmapped
    prefix yields 'Unmapped: {PREFIX}' so it's visible as clearly-wrong in
    the UI, nudging the operator to fill in the overlay.
    """
    prefix = extract_prefix(code)
    if prefix is None:
        raise ValueError(f"Could not extract prefix from course code {code!r}")
    mapping = resolve(college)
    name = mapping.get(prefix)
    if name is None:
        if strict:
            raise UnknownPrefixError(prefix, college)
        return f"Unmapped: {prefix}"
    return name


def resolve_unknown_prefixes(
    courses: list[dict],
    college: str,
) -> dict[str, int]:
    """Return {prefix → count} for prefixes present in courses but missing
    from the mapping. Useful for error reporting in Stage 2.5."""
    mapping = resolve(college)
    missing: dict[str, int] = {}
    for c in courses:
        prefix = extract_prefix(c.get("code", ""))
        if prefix is None:
            continue
        if prefix not in mapping:
            missing[prefix] = missing.get(prefix, 0) + 1
    return dict(sorted(missing.items(), key=lambda kv: -kv[1]))


def _clean_passthrough_department(dept: str) -> str:
    """Apply minimal surface cleanup to a department string when the course's
    code is too malformed to look up in the mapping.

    The only transformation is stripping the trailing parenthesized-code
    suffix (" (IS)", " (DANC)", etc.) that Gemini sometimes appends. That
    matches the fragmentation pattern the resolver exists to eliminate, so
    cleaning it here keeps pass-through courses from forming their own
    singleton UI buckets. Everything else is left alone — we don't try to
    guess canonical names from arbitrary Gemini strings.
    """
    dept = (dept or "").strip()
    return _PAREN_CODE_SUFFIX_RE.sub("", dept).strip()


def canonicalize_courses(
    courses: list[dict],
    college: str,
    *,
    strict: bool = True,
) -> tuple[list[dict], int]:
    """Rewrite each course's `department` field to its canonical name.

    Returns (new_course_list, rewrite_count). Does not mutate input.
    In strict mode, raises UnknownPrefixError at the first unmapped prefix
    (callers typically want to short-circuit and surface a summary error).

    When a course's code is unparseable by `extract_prefix`, the course
    passes through with a lightly-cleaned version of its original
    Gemini-emitted `department` field (see `_clean_passthrough_department`).
    """
    mapping = resolve(college)
    rewrote = 0
    out = []
    for c in courses:
        c = dict(c)
        prefix = extract_prefix(c.get("code", ""))
        if prefix is None:
            original = c.get("department", "")
            cleaned = _clean_passthrough_department(original)
            if cleaned and cleaned != original:
                c["department"] = cleaned
                rewrote += 1
            out.append(c)
            continue
        if prefix in mapping:
            new_dept = mapping[prefix]
        elif strict:
            raise UnknownPrefixError(prefix, college)
        else:
            new_dept = f"Unmapped: {prefix}"
        if c.get("department") != new_dept:
            rewrote += 1
        c["department"] = new_dept
        out.append(c)
    return out, rewrote
