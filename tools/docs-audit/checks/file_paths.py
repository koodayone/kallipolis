"""file_paths check: file path references in documentation resolve to existing files.

This check walks every markdown file under docs/, extracts candidate file
path references from inline code spans and markdown link URLs, applies a
heuristic to identify the candidates that look like file paths (rather
than code identifiers, model names, etc.), and verifies that each path
resolves to an existing file or directory in the repository.

The convention this check relies on is documented in docs/conventions.md
under "File path references": file paths should appear in inline code
spans (e.g., `backend/api/workflows.py`) or in markdown links
(e.g., [the loader](../../backend/pipeline/loader.py)).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, List, Tuple

from .base import Check, CheckResult, Status


# ── Patterns ──────────────────────────────────────────────────────────

# Inline code: matches `content` where content has no backticks or newlines
INLINE_CODE_RE = re.compile(r"`([^`\n]+)`")

# Markdown link: matches [text](url) where url has no parentheses
MARKDOWN_LINK_RE = re.compile(r"\[([^\]]*)\]\(([^)]+)\)")

# Top-level repo directories that signal a repo-relative path reference
REPO_RELATIVE_PREFIXES = (
    "backend/",
    "atlas/",
    "docs/",
    "tools/",
    "scripts/",
    ".github/",
    "app/",
    "components/",
    "lib/",
    "public/",
)

# Additional markdown files outside docs/ that the audit should verify.
# These are navigation/orientation READMEs that cite code paths — we want
# them covered by the same drift protection the docs tree gets.
EXTRA_AUDITED_MD_FILES = (
    "backend/README.md",
    "atlas/README.md",
)

# Recognized file extensions for path candidates
PATH_EXTENSIONS = frozenset(
    {
        ".py",
        ".ts",
        ".tsx",
        ".jsx",
        ".js",
        ".md",
        ".json",
        ".yaml",
        ".yml",
        ".toml",
        ".sh",
        ".html",
        ".css",
        ".sql",
        ".xml",
        ".txt",
        ".cfg",
        ".ini",
        ".lock",
    }
)


# ── Data types ────────────────────────────────────────────────────────


@dataclass
class PathReference:
    """A candidate file path reference extracted from a documentation file."""

    doc_file: Path  # The doc file containing the reference (absolute path)
    line: int       # 1-indexed line number where the reference appears
    text: str       # The raw text of the reference
    source: str     # "inline_code" or "markdown_link"


# ── Heuristics ────────────────────────────────────────────────────────


def looks_like_path(s: str) -> bool:
    """Return True if `s` looks like a file path (rather than a code identifier).

    A path candidate must:
    - Contain at least one forward slash
    - Not contain spaces (file paths in our docs do not have spaces)
    - Not start with http://, https://, #, or mailto:
    - Either end with a known file extension, or start with a known
      repo-relative directory prefix
    """
    if "/" not in s:
        return False
    if " " in s:
        return False
    if s.startswith(("http://", "https://", "#", "mailto:", "tel:")):
        return False

    # Strip trailing slash for the extension check (directories are valid paths too)
    s_stripped = s.rstrip("/")

    p = Path(s_stripped)
    if p.suffix in PATH_EXTENSIONS:
        return True

    # Repo-relative directory prefixes (allow paths like tools/docs-audit/)
    if any(s.startswith(prefix) for prefix in REPO_RELATIVE_PREFIXES):
        return True

    return False


# ── Extraction ────────────────────────────────────────────────────────


def extract_path_references(doc_file: Path) -> Iterator[PathReference]:
    """Yield all candidate path references from a markdown documentation file.

    Skips content inside fenced code blocks (```...```), since inline code
    patterns inside code blocks are part of code samples, not documentation
    references.
    """
    content = doc_file.read_text()
    lines = content.split("\n")
    in_code_block = False

    for lineno, line in enumerate(lines, 1):
        # Toggle code block state on lines that start with ```
        if line.strip().startswith("```"):
            in_code_block = not in_code_block
            continue

        if in_code_block:
            continue

        # Markdown links: [text](url)
        for match in MARKDOWN_LINK_RE.finditer(line):
            url = match.group(2).strip()

            # Strip optional title: "url" "title"
            if " " in url:
                url = url.split(" ", 1)[0]

            # Strip anchor
            url_no_anchor = url.split("#", 1)[0]
            if not url_no_anchor:
                continue

            if looks_like_path(url_no_anchor):
                yield PathReference(
                    doc_file=doc_file,
                    line=lineno,
                    text=url_no_anchor,
                    source="markdown_link",
                )

        # Inline code spans: `content`
        for match in INLINE_CODE_RE.finditer(line):
            content_text = match.group(1).strip()
            if looks_like_path(content_text):
                yield PathReference(
                    doc_file=doc_file,
                    line=lineno,
                    text=content_text,
                    source="inline_code",
                )


# ── Path resolution ───────────────────────────────────────────────────


def resolve_path(ref: PathReference, repo_root: Path) -> Path:
    """Resolve a path reference to an absolute filesystem path.

    Repo-relative paths (those starting with a known top-level directory)
    are resolved relative to the repo root. All other paths are resolved
    relative to the directory containing the documentation file.
    """
    if any(ref.text.startswith(prefix) for prefix in REPO_RELATIVE_PREFIXES):
        return (repo_root / ref.text).resolve()

    return (ref.doc_file.parent / ref.text).resolve()


# ── The check ─────────────────────────────────────────────────────────


class FilePathsCheck(Check):
    name = "file_paths"
    description = "File path references in documentation resolve to existing files"

    def run(self, repo_root: Path) -> CheckResult:
        docs_dir = repo_root / "docs"

        if not docs_dir.exists():
            return CheckResult(
                check=self.name,
                status=Status.SKIP,
                details=f"docs/ directory not found at {docs_dir}",
            )

        broken_refs: List[Tuple[PathReference, Path]] = []
        items_checked = 0

        doc_files = list(sorted(docs_dir.rglob("*.md")))
        for extra in EXTRA_AUDITED_MD_FILES:
            extra_path = repo_root / extra
            if extra_path.exists():
                doc_files.append(extra_path)

        for doc_file in doc_files:
            for ref in extract_path_references(doc_file):
                items_checked += 1
                resolved = resolve_path(ref, repo_root)
                if not resolved.exists():
                    broken_refs.append((ref, resolved))

        if not broken_refs:
            return CheckResult(
                check=self.name,
                status=Status.PASS,
                items_checked=items_checked,
            )

        # Format failure details
        details_lines = [
            f"Found {len(broken_refs)} broken file path reference(s) "
            f"out of {items_checked} checked:"
        ]
        for ref, resolved in broken_refs:
            try:
                rel_doc = ref.doc_file.relative_to(repo_root)
            except ValueError:
                rel_doc = ref.doc_file
            details_lines.append(
                f"  {rel_doc}:{ref.line}: `{ref.text}` "
                f"(from {ref.source}) → does not resolve to an existing file"
            )

        return CheckResult(
            check=self.name,
            status=Status.FAIL,
            details="\n".join(details_lines),
            items_checked=items_checked,
            resolution=(
                "For each broken reference, either update the documentation "
                "to point to an existing file, or restore the missing file. "
                "If the reference is intentional (e.g., to a file that does "
                "not yet exist), the documentation should not assert it as "
                "present."
            ),
        )
