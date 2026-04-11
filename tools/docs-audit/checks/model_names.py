"""model_names check: documented LLM model names match the names used in code.

This check verifies that any LLM model name appearing in the documentation
(in inline code spans, e.g., `` `claude-sonnet-4-6` `` or `` `gemini-2.5-flash` ``)
matches an actual model name passed to an LLM client in the backend code
(via `model="..."` in API call constructions).

The convention this check relies on is documented in docs/conventions.md
under "Model names": the verbatim model identifier in inline code.

The check is conservative: it only verifies inline code spans whose
content matches a known model-name pattern (claude-*, gemini-*, gpt-*).
This avoids false positives from inline code that contains other LLM
identifier-shaped strings.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, List, Set

from extractors.markdown import iter_inline_code

from .base import Check, CheckResult, Status


# ── Patterns ──────────────────────────────────────────────────────────

# Inline code that looks like a model name (claude-*, gemini-*, gpt-*).
# Conservative: requires the entire string to match this shape.
KNOWN_MODEL_PATTERNS = [
    re.compile(r"claude[-\w.]+"),
    re.compile(r"gemini[-\w.]+"),
    re.compile(r"gpt[-\w.]+"),
]

# Match `model="..."` or `model='...'` in Python code
MODEL_PARAM_RE = re.compile(r"model\s*=\s*[\"']([^\"']+)[\"']")


# ── Data types ────────────────────────────────────────────────────────


@dataclass
class DocumentedModel:
    """A model name mentioned in the documentation."""

    doc_file: Path
    line: int
    name: str


# ── Extraction ────────────────────────────────────────────────────────


def looks_like_model_name(content: str) -> bool:
    """Return True if `content` matches one of the known model name patterns."""
    return any(pattern.fullmatch(content) for pattern in KNOWN_MODEL_PATTERNS)


def extract_used_models(code_dir: Path) -> Set[str]:
    """Extract all model names referenced in `model="..."` patterns in code."""
    models: Set[str] = set()
    for py_file in code_dir.rglob("*.py"):
        if "__pycache__" in py_file.parts:
            continue
        try:
            content = py_file.read_text()
        except (UnicodeDecodeError, PermissionError):
            continue
        for match in MODEL_PARAM_RE.finditer(content):
            models.add(match.group(1))
    return models


def extract_documented_models(docs_dir: Path) -> Iterator[DocumentedModel]:
    """Yield each model name mentioned in inline code spans across docs."""
    for doc_file in sorted(docs_dir.rglob("*.md")):
        for lineno, content in iter_inline_code(doc_file):
            if looks_like_model_name(content):
                yield DocumentedModel(
                    doc_file=doc_file,
                    line=lineno,
                    name=content,
                )


# ── The check ─────────────────────────────────────────────────────────


class ModelNamesCheck(Check):
    name = "model_names"
    description = "Documented LLM model names match the names used in backend code"

    def run(self, repo_root: Path) -> CheckResult:
        docs_dir = repo_root / "docs"
        backend_dir = repo_root / "backend"

        if not docs_dir.exists():
            return CheckResult(
                check=self.name,
                status=Status.SKIP,
                details=f"docs/ not found at {docs_dir}",
            )
        if not backend_dir.exists():
            return CheckResult(
                check=self.name,
                status=Status.SKIP,
                details=f"backend/ not found at {backend_dir}",
            )

        used_models = extract_used_models(backend_dir)

        broken: List[DocumentedModel] = []
        items_checked = 0

        for model in extract_documented_models(docs_dir):
            items_checked += 1
            if model.name not in used_models:
                broken.append(model)

        if not broken:
            return CheckResult(
                check=self.name,
                status=Status.PASS,
                items_checked=items_checked,
            )

        details_lines = [
            f"Found {len(broken)} documented model name(s) "
            f"not used in backend code (out of {items_checked} checked):"
        ]
        models_in_code = (
            ", ".join(sorted(used_models)) if used_models else "<none found>"
        )
        details_lines.append(f"  Models used in code: {models_in_code}")
        for model in broken:
            try:
                rel_doc = model.doc_file.relative_to(repo_root)
            except ValueError:
                rel_doc = model.doc_file
            details_lines.append(
                f"  {rel_doc}:{model.line}: "
                f"`{model.name}` is not used by any backend code"
            )

        return CheckResult(
            check=self.name,
            status=Status.FAIL,
            details="\n".join(details_lines),
            items_checked=items_checked,
            resolution=(
                "For each documented model that is not used in code, "
                "either update the documentation to use a model that is "
                "actually called, or update the code to use the documented "
                "model. Model names must match verbatim."
            ),
        )
