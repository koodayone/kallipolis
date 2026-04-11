"""markdown_links check: anchor links in markdown resolve to actual headings.

This check verifies that markdown links containing anchors (e.g.,
`[text](./other.md#section-name)`) resolve to actual `## Section Name`
headings in the target file. Same-file anchors (`[text](#section)`) are
also validated.

The convention this check relies on is documented in docs/conventions.md
under "Cross-references": anchor links should match section headers
exactly.

This check focuses specifically on anchor validation. The file portion
of links (whether the target file exists) is covered by the file_paths
check, so this check skips link targets that do not exist rather than
double-reporting them.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterator, List, Set, Tuple

from extractors.markdown import (
    heading_to_anchor,
    iter_headings,
    iter_markdown_links,
)

from .base import Check, CheckResult, Status


# ── Data types ────────────────────────────────────────────────────────


@dataclass
class AnchorLink:
    """A markdown link with an anchor that needs to be verified."""

    doc_file: Path        # The doc file containing the link (absolute)
    line: int             # 1-indexed line number
    target_file: Path     # The file the link points to (absolute, may not exist)
    anchor: str           # The anchor portion (without leading #)


# ── Extraction ────────────────────────────────────────────────────────


def extract_anchor_links(doc_file: Path) -> Iterator[AnchorLink]:
    """Yield each markdown link in `doc_file` that has an anchor."""
    for lineno, _text, url in iter_markdown_links(doc_file):
        if "#" not in url:
            continue

        # Skip external URLs
        if url.startswith(("http://", "https://", "mailto:", "tel:")):
            continue

        file_part, anchor = url.split("#", 1)
        if not anchor:
            continue

        if not file_part:
            # Same-file anchor: #section
            target = doc_file
        else:
            target = (doc_file.parent / file_part).resolve()

        yield AnchorLink(
            doc_file=doc_file,
            line=lineno,
            target_file=target,
            anchor=anchor,
        )


def get_file_anchors(doc_file: Path) -> Set[str]:
    """Extract the set of valid anchors (heading slugs) from a markdown file."""
    anchors: Set[str] = set()
    for _lineno, _level, text in iter_headings(doc_file):
        anchor = heading_to_anchor(text)
        if anchor:
            anchors.add(anchor)
    return anchors


# ── The check ─────────────────────────────────────────────────────────


class MarkdownLinksCheck(Check):
    name = "markdown_links"
    description = "Markdown link anchors resolve to actual headings in target files"

    def run(self, repo_root: Path) -> CheckResult:
        docs_dir = repo_root / "docs"
        if not docs_dir.exists():
            return CheckResult(
                check=self.name,
                status=Status.SKIP,
                details=f"docs/ directory not found at {docs_dir}",
            )

        # Cache headings per target file (avoid re-parsing on every link)
        heading_cache: Dict[Path, Set[str]] = {}

        def get_headings_cached(file: Path) -> Set[str]:
            if file not in heading_cache:
                if file.exists() and file.is_file():
                    heading_cache[file] = get_file_anchors(file)
                else:
                    heading_cache[file] = set()
            return heading_cache[file]

        broken: List[AnchorLink] = []
        items_checked = 0
        skipped_missing_target = 0

        for doc_file in sorted(docs_dir.rglob("*.md")):
            for link in extract_anchor_links(doc_file):
                items_checked += 1

                # Skip links whose target file doesn't exist; that's
                # the file_paths check's responsibility.
                if not link.target_file.exists():
                    skipped_missing_target += 1
                    continue

                target_anchors = get_headings_cached(link.target_file)
                if link.anchor not in target_anchors:
                    broken.append(link)

        if not broken:
            return CheckResult(
                check=self.name,
                status=Status.PASS,
                items_checked=items_checked,
            )

        details_lines = [
            f"Found {len(broken)} broken anchor link(s) "
            f"out of {items_checked} checked:"
        ]
        for link in broken:
            try:
                rel_doc = link.doc_file.relative_to(repo_root)
                rel_target = link.target_file.relative_to(repo_root)
            except ValueError:
                rel_doc = link.doc_file
                rel_target = link.target_file
            details_lines.append(
                f"  {rel_doc}:{link.line}: anchor #{link.anchor} "
                f"not found in {rel_target}"
            )

        return CheckResult(
            check=self.name,
            status=Status.FAIL,
            details="\n".join(details_lines),
            items_checked=items_checked,
            resolution=(
                "For each broken anchor, either update the link to match "
                "an existing heading in the target file, or update the "
                "target file to add the missing heading. Anchor slugs are "
                "lowercased, with whitespace replaced by hyphens, and "
                "non-alphanumeric characters stripped."
            ),
        )
