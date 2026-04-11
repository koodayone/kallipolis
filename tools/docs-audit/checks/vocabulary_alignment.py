"""vocabulary_alignment check: one ontology unit, one name, every layer.

This is the check that makes the feature-primary convention load-bearing
across the full stack. Each ontology unit exists in multiple surface forms
— a product doc, a backend directory, a URL prefix, an atlas directory,
and (in the future) Pydantic model prefixes and Neo4j node labels. Without
enforcement, these surface forms drift independently: someone renames the
backend dir without touching the atlas, someone pluralizes a model name
differently, someone adds a kebab-case URL when the convention is
underscore. Each small drift erodes the property that "the name of a
thing is the same across every layer of conversation about that thing,"
which is what makes vocabulary alignment work for humans AND agents.

This check enforces bidirectional correspondence across four surface
forms: product doc, backend feature directory, URL prefix mounted in
main.py, and atlas feature directory. The product doc filename stem is
the canonical form; the other surfaces derive from it via well-defined
transformations. Mechanical transformations rather than a handwritten
mapping table, because the table would itself drift.

Neo4j node labels and Pydantic model prefixes are in scope for future
passes but not enforced here — they involve PascalCase and singular/plural
rules that need more design.

Methodology principles this check encodes (one per rule):

  1. Product doc filename stem is canonical. Other surfaces derive.
  2. Transformations are mechanical: hyphen→underscore for Python,
     identity for atlas, prepend-slash for URL.
  3. Bidirectional: check docs→code AND code→docs.
  4. Meta docs are excluded explicitly, not inferred.
  5. Exemptions (if any unit legitimately skips a surface) live in
     UNIT_EXEMPTIONS, visible in one place, required to be documented.
  6. Fail-loud: any divergence is a CI failure.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import List

from .base import Check, CheckResult, Status


# ── Canonical form derivation ─────────────────────────────────────────

# Meta docs that live under docs/product/ but do not name ontology units.
# Adding a new meta doc requires adding to this set — a deliberate step
# that forces the contributor to answer "is this a unit or meta?"
_META_DOC_STEMS = frozenset({
    "overview",
    "the-ontology",
    "the-atlas",
    "the-skills-taxonomy",
})

# Transformations from canonical (doc stem) to other surface forms.
#
#   canonical:        "strong-workforce"  (matches docs/product filename)
#   backend dir:      "strong_workforce"  (Python package convention)
#   atlas dir:        "strong-workforce"  (identity — atlas keeps kebab-case)
#   URL prefix:       "/strong-workforce" (identity — URLs use hyphens)


def _canonical_to_backend(canonical: str) -> str:
    """Canonical → backend directory name (hyphen to underscore)."""
    return canonical.replace("-", "_")


def _backend_to_canonical(backend_name: str) -> str:
    """Backend directory name → canonical (underscore to hyphen)."""
    return backend_name.replace("_", "-")


def _canonical_to_url_prefix(canonical: str) -> str:
    """Canonical → URL prefix (prepend slash)."""
    return f"/{canonical}"


# ── Unit surface-form locations ───────────────────────────────────────

_PRODUCT_DOCS_DIR = "docs/product"
_BACKEND_DIR = "backend"
_ATLAS_FEATURES_DIR = "atlas/college-atlas"
_MAIN_PY = "backend/main.py"


# Per-unit exemptions. Currently empty; add entries here when a unit
# legitimately skips one of the four surface forms. Each entry must
# document *why* the exemption exists so future readers can judge
# whether it still applies.
#
# Format: {canonical_name: frozenset({"backend", "atlas", "url"})}
# (Note: product doc is never exempt — that's the canonical source.)
UNIT_EXEMPTIONS: dict[str, frozenset[str]] = {}


# Regex for include_router decorator in main.py, same shape the
# api_endpoints check uses.
_INCLUDE_ROUTER_RE = re.compile(
    r'include_router\s*\(\s*(\w+)\s*,\s*prefix\s*=\s*["\']([^"\']+)["\']'
)


def _list_unit_canonicals(repo_root: Path) -> list[str]:
    """Walk docs/product/ and return the canonical form for each unit doc.

    Filters out meta docs via the explicit _META_DOC_STEMS exclusion list.
    """
    docs_dir = repo_root / _PRODUCT_DOCS_DIR
    if not docs_dir.exists():
        return []
    units: list[str] = []
    for doc in sorted(docs_dir.glob("*.md")):
        stem = doc.stem
        if stem in _META_DOC_STEMS:
            continue
        units.append(stem)
    return units


def _list_backend_feature_dirs(repo_root: Path) -> set[str]:
    """Return the set of feature directory names under backend/.

    A feature directory is any top-level backend subdirectory that is not
    part of the shared-infrastructure whitelist. This matches the
    definition in backend_layout.py.
    """
    backend_dir = repo_root / _BACKEND_DIR
    if not backend_dir.exists():
        return set()
    # Shared / infrastructure directories that are not features.
    non_feature = {
        "ontology", "llm", "pipeline", "tests", "scripts", "docs",
        "__pycache__",
    }
    result: set[str] = set()
    for entry in backend_dir.iterdir():
        if not entry.is_dir():
            continue
        if entry.name.startswith("."):
            continue
        if entry.name in non_feature:
            continue
        result.add(entry.name)
    return result


def _list_atlas_feature_dirs(repo_root: Path) -> set[str]:
    """Return the set of feature directory names under atlas/college-atlas/."""
    atlas_dir = repo_root / _ATLAS_FEATURES_DIR
    if not atlas_dir.exists():
        return set()
    result: set[str] = set()
    for entry in atlas_dir.iterdir():
        if not entry.is_dir():
            continue
        if entry.name.startswith("."):
            continue
        result.add(entry.name)
    return result


def _list_mounted_url_prefixes(repo_root: Path) -> set[str]:
    """Parse backend/main.py and return the set of mounted router URL prefixes."""
    main_py = repo_root / _MAIN_PY
    if not main_py.exists():
        return set()
    content = main_py.read_text()
    prefixes: set[str] = set()
    for match in _INCLUDE_ROUTER_RE.finditer(content):
        prefixes.add(match.group(2))
    return prefixes


# ── The check ─────────────────────────────────────────────────────────


class VocabularyAlignmentCheck(Check):
    name = "vocabulary_alignment"
    description = "Ontology units have matching surface forms across docs, backend, atlas, and URL prefixes"

    def run(self, repo_root: Path) -> CheckResult:
        canonicals = _list_unit_canonicals(repo_root)
        if not canonicals:
            return CheckResult(
                check=self.name,
                status=Status.SKIP,
                details=f"No unit docs found under {_PRODUCT_DOCS_DIR}/",
            )

        backend_features = _list_backend_feature_dirs(repo_root)
        atlas_features = _list_atlas_feature_dirs(repo_root)
        url_prefixes = _list_mounted_url_prefixes(repo_root)

        problems: List[str] = []
        items_checked = 0

        # Forward direction: every unit doc must have all four surfaces.
        for canonical in canonicals:
            items_checked += 1
            exemptions = UNIT_EXEMPTIONS.get(canonical, frozenset())

            expected_backend = _canonical_to_backend(canonical)
            if "backend" not in exemptions and expected_backend not in backend_features:
                problems.append(
                    f"  Unit '{canonical}' (from docs/product/{canonical}.md) "
                    f"has no matching backend directory. Expected: "
                    f"backend/{expected_backend}/"
                )

            if "atlas" not in exemptions and canonical not in atlas_features:
                problems.append(
                    f"  Unit '{canonical}' (from docs/product/{canonical}.md) "
                    f"has no matching atlas feature directory. Expected: "
                    f"atlas/college-atlas/{canonical}/"
                )

            expected_url = _canonical_to_url_prefix(canonical)
            if "url" not in exemptions and expected_url not in url_prefixes:
                problems.append(
                    f"  Unit '{canonical}' (from docs/product/{canonical}.md) "
                    f"has no matching URL prefix mounted in backend/main.py. "
                    f"Expected: include_router(..., prefix=\"{expected_url}\")"
                )

        # Reverse direction: every backend feature dir must have a product doc.
        canonical_set = set(canonicals)
        for backend_name in sorted(backend_features):
            items_checked += 1
            canonical_for_backend = _backend_to_canonical(backend_name)
            if canonical_for_backend not in canonical_set:
                problems.append(
                    f"  Backend feature 'backend/{backend_name}/' has no "
                    f"matching product doc. Expected: "
                    f"docs/product/{canonical_for_backend}.md"
                )

        # Reverse direction: every atlas feature dir must have a product doc.
        for atlas_name in sorted(atlas_features):
            items_checked += 1
            if atlas_name not in canonical_set:
                problems.append(
                    f"  Atlas feature 'atlas/college-atlas/{atlas_name}/' has "
                    f"no matching product doc. Expected: "
                    f"docs/product/{atlas_name}.md"
                )

        if not problems:
            return CheckResult(
                check=self.name,
                status=Status.PASS,
                items_checked=items_checked,
            )

        details_lines = [
            f"Found {len(problems)} vocabulary alignment violation(s) across "
            f"{items_checked} unit surface check(s):"
        ] + problems

        return CheckResult(
            check=self.name,
            status=Status.FAIL,
            details="\n".join(details_lines),
            items_checked=items_checked,
            resolution=(
                "For each violation, either add the missing surface form so "
                "the unit name appears consistently at every layer, or (if "
                "the unit legitimately skips a surface) add it to "
                "UNIT_EXEMPTIONS in tools/docs-audit/checks/"
                "vocabulary_alignment.py with a comment explaining why. "
                "If you are adding a new meta doc under docs/product/ that "
                "does not name an ontology unit, add its filename stem to "
                "_META_DOC_STEMS in the same file."
            ),
        )
