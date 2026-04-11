"""backend_layout check: the backend/ directory follows the feature-primary
convention.

This check enforces three structural invariants that the refactor established
and that the rest of the audit (api_endpoints, graph_properties, etc.) relies
on to stay granular:

1. Only known directories and files live at the top of `backend/`. Each
   feature gets its own directory; shared infrastructure lives in
   `ontology/` and `llm/`; orchestration lives in `pipeline/`. Any other
   top-level entry is a drift signal — a contributor creating a "shared"
   or "utils" or "miscellaneous" catchment that erodes the convention.

2. Each feature directory contains the core file shape: `__init__.py`,
   `api.py`, and `models.py` at minimum. A feature missing one of these
   is either half-built or structurally broken.

3. No stray Python files live directly under `backend/` except `main.py`.
   Every Python file is either an entry point, a feature file, or shared
   infrastructure — never a top-level "helper" that bypasses the convention.

The check is deliberately minimal at MVP. It does not yet enforce the
cross-feature import DAG (strong_workforce → partnerships etc.) because
that rule needs more design. It does not check file-name patterns inside
features (e.g., "every feature must have api.py but may or may not have
generate.py") because the set of valid feature files is naturally growing
and a strict whitelist would create friction without much safety gain.
The three rules above catch the structural violations that would actually
degrade the feature-primary convention.
"""

from __future__ import annotations

from pathlib import Path
from typing import List

from .base import Check, CheckResult, Status


# Allowed top-level entries under `backend/`. Anything else is flagged.
_ALLOWED_TOP_LEVEL_DIRS = frozenset({
    # Feature directories (ontology units)
    "students",
    "courses",
    "occupations",
    "employers",
    "partnerships",
    "strong_workforce",
    # Shared infrastructure
    "ontology",
    "llm",
    # Orchestration and utilities
    "pipeline",
    "tests",
    "scripts",
    "docs",
})

_ALLOWED_TOP_LEVEL_FILES = frozenset({
    "__init__.py",
    "main.py",
    "README.md",
    "Dockerfile",
    "requirements.txt",
    "run_all.sh",
    "pyproject.toml",
})

# Directories ignored entirely (generated, unchecked).
_IGNORED_DIRS = frozenset({
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
})

# The six feature directories — each must have the core file shape.
_FEATURE_DIRS = frozenset({
    "students",
    "courses",
    "occupations",
    "employers",
    "partnerships",
    "strong_workforce",
})

# Minimum files every feature directory must contain.
_FEATURE_CORE_FILES = frozenset({
    "__init__.py",
    "api.py",
    "models.py",
})


class BackendLayoutCheck(Check):
    name = "backend_layout"
    description = "backend/ follows the feature-primary layout convention"

    def run(self, repo_root: Path) -> CheckResult:
        backend_dir = repo_root / "backend"

        if not backend_dir.exists():
            return CheckResult(
                check=self.name,
                status=Status.SKIP,
                details=f"backend/ not found at {backend_dir}",
            )

        problems: List[str] = []
        items_checked = 0

        # Rule 1: whitelist top-level entries
        for entry in sorted(backend_dir.iterdir()):
            if entry.name in _IGNORED_DIRS:
                continue
            # Dotfiles and dot-directories are tooling/metadata — out of scope
            # for a feature-layout check (.gitignore, .github, .DS_Store, etc.).
            if entry.name.startswith("."):
                continue
            items_checked += 1
            if entry.is_dir():
                if entry.name not in _ALLOWED_TOP_LEVEL_DIRS:
                    problems.append(
                        f"  backend/{entry.name}/ is not an allowed top-level "
                        f"directory. Expected one of: {sorted(_ALLOWED_TOP_LEVEL_DIRS)}. "
                        f"New features go in their own directory; shared code "
                        f"belongs in ontology/ or llm/."
                    )
            elif entry.is_file():
                if entry.name not in _ALLOWED_TOP_LEVEL_FILES:
                    problems.append(
                        f"  backend/{entry.name} is not an allowed top-level "
                        f"file. Python files other than main.py belong inside "
                        f"a feature directory or shared infrastructure dir."
                    )

        # Rule 2: each feature directory has the core file shape
        for feature in sorted(_FEATURE_DIRS):
            feature_dir = backend_dir / feature
            if not feature_dir.exists():
                problems.append(
                    f"  backend/{feature}/ does not exist. Every ontology unit "
                    f"must have its own feature directory."
                )
                continue
            items_checked += 1
            present = {f.name for f in feature_dir.iterdir() if f.is_file()}
            missing = _FEATURE_CORE_FILES - present
            if missing:
                problems.append(
                    f"  backend/{feature}/ is missing core files: "
                    f"{sorted(missing)}. Every feature directory must contain "
                    f"__init__.py, api.py, and models.py at minimum."
                )

        if not problems:
            return CheckResult(
                check=self.name,
                status=Status.PASS,
                items_checked=items_checked,
            )

        details_lines = [
            f"Found {len(problems)} backend layout violation(s):"
        ] + problems

        return CheckResult(
            check=self.name,
            status=Status.FAIL,
            details="\n".join(details_lines),
            items_checked=items_checked,
            resolution=(
                "For each violation, either move the offending file or directory "
                "into the right place under backend/ (feature dirs own their "
                "code; cross-cutting code goes in ontology/ or llm/), or update "
                "_ALLOWED_TOP_LEVEL_DIRS / _ALLOWED_TOP_LEVEL_FILES in "
                "tools/docs-audit/checks/backend_layout.py if the new entry is "
                "a deliberate addition to the convention."
            ),
        )
