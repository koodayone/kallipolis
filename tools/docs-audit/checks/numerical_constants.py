"""numerical_constants check: documented constants match backend Python.

Verifies that every inline code span in the documentation of the form
`` `IDENTIFIER = value` `` corresponds to an actual module-level
constant assignment with the same numeric value somewhere in the
backend Python code. This is the convention codified in
`docs/conventions.md` under "Numerical constants":

> The verbatim Python identifier in inline code:
> `` `PRIMARY_STICKINESS = 0.60` ``, `` `DEPT_CAP = 6` ``,
> `` `BATCH_SIZE = 30` ``. The audit cross-references these against
> the actual constants in the corresponding Python files.

The check is one-directional (docs → code) because not every constant
in code needs to be documented — only those that documentation makes
claims about. Drift this catches: prose updates that hard-code an old
value after the constant has been changed in code.

Comparison rule:
- For each documented `IDENT = value`, find every `IDENT = numeric` at
  the module level of any backend `.py` file.
- If at least one matches by float-equality, the claim passes.
- Otherwise the check reports a discrepancy with the actual values
  found in code (or "no such constant" if the name is not defined
  anywhere in the backend).
"""

from __future__ import annotations

import ast
import re
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Set

from extractors.markdown import iter_inline_code

from .base import Check, CheckResult, Status


# ── Patterns ──────────────────────────────────────────────────────────

# Inline code form: IDENT = numeric_value
# IDENT is UPPER_SNAKE_CASE (must start with a letter so we don't match
# stray = signs). Value is an int or float, optionally negative.
DOC_CONSTANT_RE = re.compile(
    r"^\s*([A-Z][A-Z0-9_]*)\s*=\s*(-?\d+(?:\.\d+)?)\s*$"
)


# ── Data types ────────────────────────────────────────────────────────


@dataclass(frozen=True)
class DocumentedConstant:
    """A numerical constant claim found in the documentation."""

    name: str
    value: float
    source_file: Path
    lineno: int


# ── Loader for actual constants ───────────────────────────────────────


def extract_actual_constants(backend_dir: Path) -> Dict[str, Set[float]]:
    """Walk every Python file under `backend/` and collect module-level
    numeric constant assignments.

    Returns a dict mapping each UPPER_SNAKE_CASE name to the set of
    numeric values it has been assigned (as floats — int and float are
    not distinguished, since the docs convention writes them
    interchangeably).

    A name may map to multiple values if it appears in multiple files
    (e.g., `BATCH_SIZE` is defined in three loader modules); a doc claim
    matches if it agrees with any one of them.
    """
    constants: Dict[str, Set[float]] = defaultdict(set)

    if not backend_dir.exists():
        return {}

    for py_file in backend_dir.rglob("*.py"):
        # Skip caches and test directories — they may contain throwaway
        # constants that should not back documentation claims.
        parts = set(py_file.parts)
        if "cache" in parts or "tests" in parts or "__pycache__" in parts:
            continue
        try:
            tree = ast.parse(py_file.read_text())
        except (SyntaxError, UnicodeDecodeError):
            continue

        for node in ast.iter_child_nodes(tree):
            if not isinstance(node, ast.Assign):
                continue
            if len(node.targets) != 1:
                continue
            target = node.targets[0]
            if not isinstance(target, ast.Name):
                continue
            name = target.id
            # Must look like a constant identifier.
            if not name or not name[0].isalpha() or not name.isupper():
                continue
            value = node.value
            # Accept int and float literals only — not lists, tuples,
            # or expressions. ast.Constant covers both since 3.8.
            if not isinstance(value, ast.Constant):
                continue
            v = value.value
            if isinstance(v, bool) or not isinstance(v, (int, float)):
                continue
            constants[name].add(float(v))

    return dict(constants)


# ── Documented constant extractor ─────────────────────────────────────


def extract_documented_constants(docs_dir: Path) -> List[DocumentedConstant]:
    """Walk every markdown file under `docs/` and extract inline code
    spans that match the `IDENT = value` constant convention."""
    found: List[DocumentedConstant] = []

    if not docs_dir.exists():
        return found

    for md_file in docs_dir.rglob("*.md"):
        for lineno, content in iter_inline_code(md_file):
            match = DOC_CONSTANT_RE.match(content)
            if not match:
                continue
            name = match.group(1)
            try:
                value = float(match.group(2))
            except ValueError:
                continue
            found.append(
                DocumentedConstant(
                    name=name,
                    value=value,
                    source_file=md_file,
                    lineno=lineno,
                )
            )

    return found


# ── The check ─────────────────────────────────────────────────────────


class NumericalConstantsCheck(Check):
    name = "numerical_constants"
    description = (
        "Inline `IDENT = value` constants in docs match backend Python"
    )

    def run(self, repo_root: Path) -> CheckResult:
        docs_dir = repo_root / "docs"
        backend_dir = repo_root / "backend"

        if not docs_dir.exists():
            return CheckResult(
                check=self.name,
                status=Status.SKIP,
                details=f"Documentation directory not found at {docs_dir}",
            )
        if not backend_dir.exists():
            return CheckResult(
                check=self.name,
                status=Status.SKIP,
                details=f"Backend directory not found at {backend_dir}",
            )

        documented = extract_documented_constants(docs_dir)
        actual = extract_actual_constants(backend_dir)

        problems: List[str] = []

        for claim in documented:
            rel_source = claim.source_file.relative_to(repo_root)
            if claim.name not in actual:
                problems.append(
                    f"  {rel_source}:{claim.lineno}: "
                    f"`{claim.name} = {_format(claim.value)}` "
                    f"— no such constant defined in backend/"
                )
                continue
            code_values = actual[claim.name]
            if claim.value not in code_values:
                code_values_fmt = sorted(_format(v) for v in code_values)
                problems.append(
                    f"  {rel_source}:{claim.lineno}: "
                    f"`{claim.name} = {_format(claim.value)}` "
                    f"— backend defines {claim.name} as "
                    f"{code_values_fmt}"
                )

        if not problems:
            return CheckResult(
                check=self.name,
                status=Status.PASS,
                items_checked=len(documented),
            )

        details_lines = [
            f"Found {len(problems)} numerical constant discrepancies "
            f"across {len(documented)} documented claims:"
        ]
        details_lines.extend(problems)

        return CheckResult(
            check=self.name,
            status=Status.FAIL,
            details="\n".join(details_lines),
            items_checked=len(documented),
            resolution=(
                "For each discrepancy, either update the prose in the doc "
                "to match the actual constant value in the backend, or "
                "update the constant in the backend to match the documented "
                "value. The two must agree."
            ),
        )


def _format(value: float) -> str:
    """Render a float without a trailing .0 when it's an integer value."""
    if value == int(value):
        return str(int(value))
    return str(value)
