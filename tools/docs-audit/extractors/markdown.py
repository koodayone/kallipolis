"""Shared markdown parsing helpers for audit checks.

These helpers are used by multiple checks to walk markdown documentation
files and extract structured content (inline code spans, markdown links,
headings) while skipping content inside fenced code blocks.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Iterator, Tuple


# ── Patterns ──────────────────────────────────────────────────────────

INLINE_CODE_RE = re.compile(r"`([^`\n]+)`")
MARKDOWN_LINK_RE = re.compile(r"\[([^\]]*)\]\(([^)]+)\)")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")


# ── Iteration helpers ────────────────────────────────────────────────


def iter_markdown_lines(doc_file: Path) -> Iterator[Tuple[int, str]]:
    """Yield (lineno, line) pairs for a markdown file, skipping fenced code blocks.

    Lines inside ``` ... ``` blocks are not yielded. The fence lines themselves
    are also not yielded.
    """
    in_code_block = False
    for lineno, line in enumerate(doc_file.read_text().split("\n"), 1):
        if line.strip().startswith("```"):
            in_code_block = not in_code_block
            continue
        if in_code_block:
            continue
        yield lineno, line


def iter_inline_code(doc_file: Path) -> Iterator[Tuple[int, str]]:
    """Yield (lineno, content) for each inline code span outside code blocks."""
    for lineno, line in iter_markdown_lines(doc_file):
        for match in INLINE_CODE_RE.finditer(line):
            yield lineno, match.group(1).strip()


def iter_markdown_links(doc_file: Path) -> Iterator[Tuple[int, str, str]]:
    """Yield (lineno, text, url) for each markdown link outside code blocks.

    The url has any optional title (`url "title"`) stripped.
    """
    for lineno, line in iter_markdown_lines(doc_file):
        for match in MARKDOWN_LINK_RE.finditer(line):
            text = match.group(1)
            url = match.group(2).strip()
            if " " in url:
                url = url.split(" ", 1)[0]
            yield lineno, text, url


def iter_headings(doc_file: Path) -> Iterator[Tuple[int, int, str]]:
    """Yield (lineno, level, text) for each markdown heading outside code blocks.

    Level is 1-6 corresponding to # through ######.
    """
    for lineno, line in iter_markdown_lines(doc_file):
        match = HEADING_RE.match(line)
        if match:
            level = len(match.group(1))
            text = match.group(2)
            yield lineno, level, text


# ── Anchor generation ────────────────────────────────────────────────


def heading_to_anchor(heading_text: str) -> str:
    """Convert a markdown heading to its GitHub-flavored anchor slug.

    Approximation of GitHub's slugification rules:
    - Lowercase
    - Strip leading/trailing whitespace
    - Strip inline markdown formatting characters that are not valid in slugs
      (asterisks and backticks). Underscores are preserved because they are
      valid slug characters; this is approximate behavior — in true GitHub
      slugification, paired `_text_` emphasis markers are stripped because
      they are interpreted as emphasis before slugification, but isolated
      underscores in identifiers are preserved. The audit prefers to preserve
      both rather than try to parse emphasis.
    - Replace whitespace with single hyphens
    - Strip characters that are not alphanumeric, hyphen, or underscore
    """
    text = heading_text.strip().lower()
    # Strip inline formatting markers (but not underscores)
    text = re.sub(r"[*`]", "", text)
    # Replace whitespace with hyphens
    text = re.sub(r"\s+", "-", text)
    # Strip everything that is not alphanumeric, hyphen, or underscore
    text = re.sub(r"[^a-z0-9_-]", "", text)
    return text
