"""Unit tests for the markdown_links check and its helpers."""

from pathlib import Path

from checks.base import Status
from checks.markdown_links import (
    MarkdownLinksCheck,
    extract_anchor_links,
    get_file_anchors,
)
from extractors.markdown import heading_to_anchor


# ── heading_to_anchor ─────────────────────────────────────────────────


class TestHeadingToAnchor:
    def test_simple_heading(self):
        assert heading_to_anchor("The essence") == "the-essence"

    def test_multiple_words(self):
        assert heading_to_anchor("How students are generated today") == "how-students-are-generated-today"

    def test_strips_inline_formatting(self):
        assert heading_to_anchor("*The* essence") == "the-essence"
        assert heading_to_anchor("`code` heading") == "code-heading"

    def test_strips_punctuation(self):
        assert heading_to_anchor("What is it, really?") == "what-is-it-really"
        assert heading_to_anchor("Two arenas: analysis and action") == "two-arenas-analysis-and-action"

    def test_preserves_underscores(self):
        # Code-style identifiers in headings keep underscores
        assert heading_to_anchor("Schema_constraints check") == "schema_constraints-check"

    def test_collapses_whitespace(self):
        assert heading_to_anchor("Hello   world") == "hello-world"


# ── get_file_anchors ──────────────────────────────────────────────────


class TestGetFileAnchors:
    def test_extracts_all_heading_levels(self, tmp_path):
        doc = tmp_path / "test.md"
        doc.write_text(
            "# Top level\n"
            "\n"
            "## The essence\n"
            "\n"
            "### A sub-section\n"
        )
        anchors = get_file_anchors(doc)
        assert anchors == {"top-level", "the-essence", "a-sub-section"}

    def test_skips_headings_inside_code_blocks(self, tmp_path):
        doc = tmp_path / "test.md"
        doc.write_text(
            "## Real heading\n"
            "\n"
            "```\n"
            "## Not a heading\n"
            "```\n"
        )
        anchors = get_file_anchors(doc)
        assert anchors == {"real-heading"}


# ── extract_anchor_links ──────────────────────────────────────────────


class TestExtractAnchorLinks:
    def test_extracts_cross_file_anchor(self, tmp_path):
        doc = tmp_path / "test.md"
        doc.write_text("See [other](./other.md#section) for details.")
        links = list(extract_anchor_links(doc))
        assert len(links) == 1
        assert links[0].anchor == "section"
        assert links[0].target_file.name == "other.md"

    def test_extracts_same_file_anchor(self, tmp_path):
        doc = tmp_path / "test.md"
        doc.write_text("See [the section below](#section).")
        links = list(extract_anchor_links(doc))
        assert len(links) == 1
        assert links[0].anchor == "section"
        assert links[0].target_file == doc

    def test_skips_links_without_anchors(self, tmp_path):
        doc = tmp_path / "test.md"
        doc.write_text("See [other](./other.md) for details.")
        links = list(extract_anchor_links(doc))
        assert links == []

    def test_skips_external_anchors(self, tmp_path):
        doc = tmp_path / "test.md"
        doc.write_text("See [external](https://example.com/page#frag) for details.")
        links = list(extract_anchor_links(doc))
        assert links == []


# ── MarkdownLinksCheck end-to-end ─────────────────────────────────────


class TestMarkdownLinksCheck:
    def test_passes_when_anchor_resolves(self, tmp_path):
        docs = tmp_path / "docs"
        docs.mkdir()
        (docs / "target.md").write_text(
            "# Top\n\n## The essence\n\nContent here.\n"
        )
        (docs / "source.md").write_text(
            "See [the essence](./target.md#the-essence) for details."
        )

        result = MarkdownLinksCheck().run(tmp_path)
        assert result.status == Status.PASS
        assert result.items_checked == 1

    def test_fails_when_anchor_does_not_resolve(self, tmp_path):
        docs = tmp_path / "docs"
        docs.mkdir()
        (docs / "target.md").write_text("# Top\n\n## The essence\n")
        (docs / "source.md").write_text(
            "See [other](./target.md#nonexistent) for details."
        )

        result = MarkdownLinksCheck().run(tmp_path)
        assert result.status == Status.FAIL
        assert "nonexistent" in result.details

    def test_skips_anchors_to_missing_files(self, tmp_path):
        # If the target file doesn't exist, that's the file_paths check's
        # job to report, not ours
        docs = tmp_path / "docs"
        docs.mkdir()
        (docs / "source.md").write_text(
            "See [other](./missing.md#anything) for details."
        )

        result = MarkdownLinksCheck().run(tmp_path)
        # The anchor link is counted but not reported as broken
        assert result.status == Status.PASS

    def test_passes_when_no_anchor_links(self, tmp_path):
        docs = tmp_path / "docs"
        docs.mkdir()
        (docs / "source.md").write_text("Just plain prose with no links.")

        result = MarkdownLinksCheck().run(tmp_path)
        assert result.status == Status.PASS
        assert result.items_checked == 0
