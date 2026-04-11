"""api_endpoints check: documented API endpoints match @router decorators.

This check verifies that every API endpoint mentioned in the documentation
(in the form `` `METHOD /path` `` inline) actually exists in the FastAPI
backend code as a `@router.{method}("path")` decorator.

The convention this check relies on is documented in docs/conventions.md
under "API endpoints": endpoints in markdown tables or inline as
`` `POST /workflows/partnerships/targeted/stream` ``. This check covers
the inline form. Table-form endpoints are not currently extracted.

The check reads `backend/main.py` to determine each router's prefix
(e.g., `app.include_router(ontology_router, prefix="/ontology")`) and
joins the prefix with the path on each `@router` decorator to compute
the full endpoint path.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterator, List, Set, Tuple

from extractors.markdown import iter_markdown_lines

from .base import Check, CheckResult, Status


# ── Patterns ──────────────────────────────────────────────────────────

# Inline endpoint mention: `METHOD /path`
ENDPOINT_RE = re.compile(r"`(GET|POST|PUT|DELETE|PATCH)\s+(/[^\s`]+)`")

# FastAPI router decorator: @router.method("path", ...)
ROUTER_DECORATOR_RE = re.compile(
    r"@router\.(get|post|put|delete|patch)\s*\(\s*[\"']([^\"']+)[\"']"
)

# include_router with prefix: app.include_router(name, prefix="/x", ...)
INCLUDE_ROUTER_RE = re.compile(
    r"app\.include_router\(\s*(\w+)\s*,\s*prefix\s*=\s*[\"']([^\"']+)[\"']"
)


# ── Data types ────────────────────────────────────────────────────────


@dataclass
class DocumentedEndpoint:
    """An endpoint mentioned in the documentation."""

    doc_file: Path
    line: int
    method: str  # "GET", "POST", etc.
    path: str    # "/workflows/foo" — already includes the prefix


# ── Extraction ────────────────────────────────────────────────────────


def extract_router_prefixes(main_py: Path) -> Dict[str, str]:
    """Read backend/main.py and return a mapping of feature name to URL prefix.

    A line like:
        app.include_router(students_router, prefix="/students", tags=["Students"])
    produces:
        {"students": "/students"}

    The mapping uses the feature name (the part before "_router") so that the
    same name can be used to look up the file at backend/<feature>/api.py.
    """
    content = main_py.read_text()
    prefixes: Dict[str, str] = {}
    for match in INCLUDE_ROUTER_RE.finditer(content):
        router_name = match.group(1)
        prefix = match.group(2)
        if router_name.endswith("_router"):
            feature = router_name[: -len("_router")]
            prefixes[feature] = prefix
    return prefixes


def extract_actual_endpoints(backend_dir: Path, prefixes: Dict[str, str]) -> Set[Tuple[str, str]]:
    """Extract all actual endpoints from per-feature FastAPI router files.

    Returns a set of (METHOD, FULL_PATH) tuples where FULL_PATH includes
    the router prefix. Each feature's routes live at backend/<feature>/api.py.
    """
    endpoints: Set[Tuple[str, str]] = set()
    for feature, prefix in prefixes.items():
        api_file = backend_dir / feature / "api.py"
        if not api_file.exists():
            continue
        try:
            content = api_file.read_text()
        except (UnicodeDecodeError, PermissionError):
            continue
        for match in ROUTER_DECORATOR_RE.finditer(content):
            method = match.group(1).upper()
            path = match.group(2)
            # Strip a trailing slash unless the full path would be empty
            full_path = prefix + path
            if len(full_path) > 1 and full_path.endswith("/"):
                full_path = full_path.rstrip("/")
            endpoints.add((method, full_path))
    return endpoints


def extract_documented_endpoints(docs_dir: Path) -> Iterator[DocumentedEndpoint]:
    """Yield each documented endpoint mention from markdown files."""
    for doc_file in sorted(docs_dir.rglob("*.md")):
        for lineno, line in iter_markdown_lines(doc_file):
            for match in ENDPOINT_RE.finditer(line):
                yield DocumentedEndpoint(
                    doc_file=doc_file,
                    line=lineno,
                    method=match.group(1),
                    path=match.group(2),
                )


# ── The check ─────────────────────────────────────────────────────────


class APIEndpointsCheck(Check):
    name = "api_endpoints"
    description = "Documented API endpoints match actual FastAPI router decorators"

    def run(self, repo_root: Path) -> CheckResult:
        docs_dir = repo_root / "docs"
        backend_dir = repo_root / "backend"
        main_py = backend_dir / "main.py"

        if not docs_dir.exists():
            return CheckResult(
                check=self.name,
                status=Status.SKIP,
                details=f"docs/ not found at {docs_dir}",
            )
        if not main_py.exists():
            return CheckResult(
                check=self.name,
                status=Status.SKIP,
                details=f"backend/main.py not found at {main_py}",
            )

        prefixes = extract_router_prefixes(main_py)
        actual = extract_actual_endpoints(backend_dir, prefixes)

        broken: List[DocumentedEndpoint] = []
        items_checked = 0

        for endpoint in extract_documented_endpoints(docs_dir):
            items_checked += 1
            if (endpoint.method, endpoint.path) not in actual:
                broken.append(endpoint)

        if not broken:
            return CheckResult(
                check=self.name,
                status=Status.PASS,
                items_checked=items_checked,
            )

        details_lines = [
            f"Found {len(broken)} documented endpoint(s) "
            f"that do not exist in code (out of {items_checked} checked):"
        ]
        for endpoint in broken:
            try:
                rel_doc = endpoint.doc_file.relative_to(repo_root)
            except ValueError:
                rel_doc = endpoint.doc_file
            details_lines.append(
                f"  {rel_doc}:{endpoint.line}: "
                f"`{endpoint.method} {endpoint.path}` not found in any feature's api.py"
            )

        return CheckResult(
            check=self.name,
            status=Status.FAIL,
            details="\n".join(details_lines),
            items_checked=items_checked,
            resolution=(
                "For each documented endpoint that is missing from the code, "
                "either update the documentation to remove or correct the "
                "reference, or add the missing endpoint to the corresponding "
                "feature's api.py (e.g., backend/students/api.py)."
            ),
        )
