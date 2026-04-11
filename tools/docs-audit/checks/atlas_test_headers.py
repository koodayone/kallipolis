"""atlas_test_headers check: every atlas test file has a JSDoc coverage header.

The atlas test suite documents each test file in plain language via a
top-of-file JSDoc block whose shape is defined in
`atlas/docs/testing.md`. The block names the unit under test, optionally
describes context, and lists the coverage areas as bullets under a
`Coverage:` label. This file-level summary is what keeps the suite
legible as it grows — a reader can open any test file and understand
what it guards without reading every `it` block.

This check enforces the convention mechanically so it cannot rot. For
each file matching `atlas/**/*.test.{ts,tsx}`, outside `node_modules/`
and `.next/`, the check verifies:

1. The file's first non-blank line is a JSDoc block opener (`/**`).
2. The JSDoc block contains a line that says `Coverage:` (with or
   without trailing text on the same line).

The check does not enforce the contents of the Coverage bullets — the
convention relies on author discipline at write time for that, and a
stricter parser would create friction without much safety gain. But a
file missing the header entirely, or whose header lacks a Coverage
section, is a clear drift signal and blocks the audit.

This check is atlas-only because the testing convention is atlas-only.
The backend uses pytest with its own conventions; adding a similar
enforcement there is a separate decision.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import List

from .base import Check, CheckResult, Status


# Directories walked for atlas test files. Relative to repo root.
_ATLAS_ROOT = "atlas"

# Directories inside atlas/ to ignore entirely.
_IGNORED_DIRS = frozenset({
    "node_modules",
    ".next",
    "public",
})

# Matches a JSDoc block opener as the first non-blank line.
_JSDOC_OPEN = re.compile(r"^\s*/\*\*")

# Matches a "Coverage:" line anywhere inside a JSDoc block.
_COVERAGE_LABEL = re.compile(r"\*\s*Coverage\s*:")


class AtlasTestHeadersCheck(Check):
    name = "atlas_test_headers"
    description = "every atlas test file starts with a JSDoc coverage header"

    def run(self, repo_root: Path) -> CheckResult:
        atlas_dir = repo_root / _ATLAS_ROOT
        if not atlas_dir.exists():
            return CheckResult(
                check=self.name,
                status=Status.SKIP,
                details=f"{_ATLAS_ROOT}/ not found at {atlas_dir}",
            )

        test_files = list(_find_test_files(atlas_dir))
        if not test_files:
            return CheckResult(
                check=self.name,
                status=Status.SKIP,
                details=f"no atlas test files found under {atlas_dir}",
            )

        problems: List[str] = []
        for path in test_files:
            issues = _check_file(path)
            if issues:
                rel = path.relative_to(repo_root)
                for issue in issues:
                    problems.append(f"  {rel}: {issue}")

        if problems:
            return CheckResult(
                check=self.name,
                status=Status.FAIL,
                details=(
                    f"Found {len(problems)} test file(s) missing the JSDoc "
                    f"coverage header:\n" + "\n".join(problems)
                ),
                resolution=(
                    "Every .test.ts/.test.tsx file in atlas/ must begin with "
                    "a /** JSDoc block containing a 'Coverage:' label and a "
                    "bullet list of what the file guards. See "
                    "atlas/docs/testing.md for the full convention."
                ),
                items_checked=len(test_files),
            )

        return CheckResult(
            check=self.name,
            status=Status.PASS,
            items_checked=len(test_files),
        )


def _find_test_files(atlas_dir: Path):
    """Yield every .test.ts/.test.tsx file under atlas/, skipping ignored dirs."""
    for path in atlas_dir.rglob("*"):
        # Skip anything inside an ignored directory.
        if any(part in _IGNORED_DIRS for part in path.parts):
            continue
        if path.is_file() and (path.name.endswith(".test.ts") or path.name.endswith(".test.tsx")):
            yield path


def _check_file(path: Path) -> List[str]:
    """Return a list of issues for a single test file. Empty = passing."""
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as e:
        return [f"could not read file: {e}"]

    issues: List[str] = []

    # Find the first non-blank line.
    lines = text.splitlines()
    first_code_idx = None
    for i, line in enumerate(lines):
        if line.strip():
            first_code_idx = i
            break

    if first_code_idx is None:
        issues.append("file is empty")
        return issues

    first_line = lines[first_code_idx]
    if not _JSDOC_OPEN.match(first_line):
        issues.append(
            "first non-blank line is not a JSDoc opener (expected '/**'); "
            "the header must come before any import or code"
        )
        return issues

    # Find the close of the JSDoc block. The block ends at a line
    # containing */. We only look inside the block for Coverage:.
    block_end_idx = None
    for i in range(first_code_idx, len(lines)):
        if "*/" in lines[i]:
            block_end_idx = i
            break

    if block_end_idx is None:
        issues.append("JSDoc opener has no matching '*/' close")
        return issues

    block_text = "\n".join(lines[first_code_idx : block_end_idx + 1])
    if not _COVERAGE_LABEL.search(block_text):
        issues.append(
            "JSDoc header is present but lacks a 'Coverage:' label; "
            "add a 'Coverage:' line followed by bullet points naming "
            "what the file guards"
        )

    return issues
