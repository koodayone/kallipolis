"""Unit tests for the file_paths check."""

from pathlib import Path

from checks.base import Status
from checks.file_paths import (
    FilePathsCheck,
    extract_path_references,
    looks_like_path,
    resolve_path,
)


# ── looks_like_path heuristic ─────────────────────────────────────────


class TestLooksLikePath:
    def test_repo_relative_python_file(self):
        assert looks_like_path("backend/api/workflows.py")

    def test_repo_relative_typescript_file(self):
        assert looks_like_path("atlas/middleware.ts")

    def test_relative_markdown_link(self):
        assert looks_like_path("./the-atlas.md")

    def test_parent_relative_markdown_link(self):
        assert looks_like_path("../product/students.md")

    def test_repo_relative_directory(self):
        assert looks_like_path("tools/docs-audit/")

    def test_no_slash_is_not_path(self):
        assert not looks_like_path("variable_name")
        assert not looks_like_path("PRIMARY_STICKINESS")

    def test_contains_space_is_not_path(self):
        assert not looks_like_path("hello world")
        assert not looks_like_path("PRIMARY_STICKINESS = 0.60")

    def test_external_url_is_not_path(self):
        assert not looks_like_path("https://example.com/foo.html")
        assert not looks_like_path("http://example.com")
        assert not looks_like_path("mailto:user@example.com")

    def test_anchor_only_is_not_path(self):
        assert not looks_like_path("#section-header")

    def test_unknown_extension_with_no_repo_prefix_is_not_path(self):
        # Has slash but unknown extension and no recognized prefix
        assert not looks_like_path("foo/bar.xyz")


# ── Extraction ────────────────────────────────────────────────────────


class TestExtractPathReferences:
    def test_extracts_inline_code_path(self, tmp_path):
        doc = tmp_path / "test.md"
        doc.write_text(
            "Some text. The file is `backend/api/workflows.py` somewhere."
        )
        refs = list(extract_path_references(doc))
        assert len(refs) == 1
        assert refs[0].text == "backend/api/workflows.py"
        assert refs[0].source == "inline_code"
        assert refs[0].line == 1

    def test_extracts_markdown_link_path(self, tmp_path):
        doc = tmp_path / "test.md"
        doc.write_text("See [the atlas](./the-atlas.md) for details.")
        refs = list(extract_path_references(doc))
        assert len(refs) == 1
        assert refs[0].text == "./the-atlas.md"
        assert refs[0].source == "markdown_link"

    def test_skips_non_path_inline_code(self, tmp_path):
        doc = tmp_path / "test.md"
        doc.write_text(
            "The model name is `claude-sonnet-4-6` and the constant is "
            "`PRIMARY_STICKINESS = 0.60`."
        )
        refs = list(extract_path_references(doc))
        assert refs == []

    def test_skips_external_urls_in_links(self, tmp_path):
        doc = tmp_path / "test.md"
        doc.write_text("See [the spec](https://example.com/spec) for details.")
        refs = list(extract_path_references(doc))
        assert refs == []

    def test_strips_anchor_from_link(self, tmp_path):
        doc = tmp_path / "test.md"
        doc.write_text("See [section](./other.md#section) for details.")
        refs = list(extract_path_references(doc))
        assert len(refs) == 1
        assert refs[0].text == "./other.md"

    def test_skips_content_inside_code_blocks(self, tmp_path):
        doc = tmp_path / "test.md"
        doc.write_text(
            "Real reference: `backend/api/workflows.py`\n"
            "\n"
            "```python\n"
            "# This is inside a code block\n"
            "from `fake/path/file.py` import something\n"
            "```\n"
            "\n"
            "Another real reference: `atlas/middleware.ts`"
        )
        refs = list(extract_path_references(doc))
        # Only the two outside the code block should be extracted
        texts = [r.text for r in refs]
        assert "backend/api/workflows.py" in texts
        assert "atlas/middleware.ts" in texts
        assert "fake/path/file.py" not in texts

    def test_multiple_references_on_one_line(self, tmp_path):
        doc = tmp_path / "test.md"
        doc.write_text(
            "Both `backend/api/workflows.py` and `atlas/middleware.ts` are here."
        )
        refs = list(extract_path_references(doc))
        assert len(refs) == 2


# ── Path resolution ───────────────────────────────────────────────────


class TestResolvePath:
    def test_repo_relative_path(self, tmp_path):
        from checks.file_paths import PathReference

        ref = PathReference(
            doc_file=tmp_path / "docs" / "test.md",
            line=1,
            text="backend/api/workflows.py",
            source="inline_code",
        )
        resolved = resolve_path(ref, tmp_path)
        assert resolved == (tmp_path / "backend" / "api" / "workflows.py").resolve()

    def test_doc_relative_path(self, tmp_path):
        from checks.file_paths import PathReference

        ref = PathReference(
            doc_file=tmp_path / "docs" / "product" / "test.md",
            line=1,
            text="../the-atlas.md",
            source="markdown_link",
        )
        resolved = resolve_path(ref, tmp_path)
        assert resolved == (tmp_path / "docs" / "the-atlas.md").resolve()


# ── End-to-end check ──────────────────────────────────────────────────


class TestFilePathsCheck:
    def test_passes_when_all_paths_exist(self, tmp_path):
        # Build a fake repo with a doc that references an existing file
        docs = tmp_path / "docs"
        docs.mkdir()
        backend_api = tmp_path / "backend" / "api"
        backend_api.mkdir(parents=True)
        (backend_api / "workflows.py").write_text("")

        (docs / "test.md").write_text(
            "See `backend/api/workflows.py` for details."
        )

        result = FilePathsCheck().run(tmp_path)
        assert result.status == Status.PASS
        assert result.items_checked == 1

    def test_fails_when_path_does_not_exist(self, tmp_path):
        docs = tmp_path / "docs"
        docs.mkdir()

        (docs / "test.md").write_text(
            "See `backend/api/missing.py` for details."
        )

        result = FilePathsCheck().run(tmp_path)
        assert result.status == Status.FAIL
        assert result.items_checked == 1
        assert "missing.py" in result.details
        assert "test.md:1" in result.details

    def test_skips_when_docs_directory_missing(self, tmp_path):
        # No docs/ directory in the fake repo
        result = FilePathsCheck().run(tmp_path)
        assert result.status == Status.SKIP

    def test_passes_with_no_references(self, tmp_path):
        docs = tmp_path / "docs"
        docs.mkdir()
        (docs / "test.md").write_text("Plain prose with no references.")

        result = FilePathsCheck().run(tmp_path)
        assert result.status == Status.PASS
        assert result.items_checked == 0

    def test_relative_link_within_docs(self, tmp_path):
        docs = tmp_path / "docs"
        product = docs / "product"
        product.mkdir(parents=True)

        (product / "the-atlas.md").write_text("# The Atlas")
        (product / "students.md").write_text(
            "See [the atlas](./the-atlas.md) for details."
        )

        result = FilePathsCheck().run(tmp_path)
        assert result.status == Status.PASS
        assert result.items_checked == 1
