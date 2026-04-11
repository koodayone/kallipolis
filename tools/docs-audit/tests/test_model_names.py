"""Unit tests for the model_names check and its helpers."""

from pathlib import Path

from checks.base import Status
from checks.model_names import (
    ModelNamesCheck,
    extract_documented_models,
    extract_used_models,
    looks_like_model_name,
)


# ── looks_like_model_name ─────────────────────────────────────────────


class TestLooksLikeModelName:
    def test_claude_model(self):
        assert looks_like_model_name("claude-sonnet-4-6")
        assert looks_like_model_name("claude-opus-4-6")
        assert looks_like_model_name("claude-haiku-4-5-20251001")

    def test_gemini_model(self):
        assert looks_like_model_name("gemini-2.5-flash")
        assert looks_like_model_name("gemini-1.5-pro")

    def test_gpt_model(self):
        assert looks_like_model_name("gpt-4o")

    def test_not_a_model(self):
        assert not looks_like_model_name("backend/api/workflows.py")
        assert not looks_like_model_name("PRIMARY_STICKINESS = 0.60")
        assert not looks_like_model_name("MERGE")
        assert not looks_like_model_name("Claude")  # capitalized, not a model identifier

    def test_partial_name_does_not_match(self):
        # Bare "claude" without a suffix is not a full model name
        assert not looks_like_model_name("claude")
        assert not looks_like_model_name("gemini")


# ── extract_used_models ───────────────────────────────────────────────


class TestExtractUsedModels:
    def test_extracts_double_quoted(self, tmp_path):
        code = tmp_path / "test.py"
        code.write_text(
            'client.messages.create(model="claude-sonnet-4-6")\n'
        )
        models = extract_used_models(tmp_path)
        assert models == {"claude-sonnet-4-6"}

    def test_extracts_single_quoted(self, tmp_path):
        code = tmp_path / "test.py"
        code.write_text(
            "client.models.generate_content(model='gemini-2.5-flash')\n"
        )
        models = extract_used_models(tmp_path)
        assert models == {"gemini-2.5-flash"}

    def test_extracts_from_multiple_files(self, tmp_path):
        (tmp_path / "a.py").write_text('foo(model="claude-sonnet-4-6")')
        (tmp_path / "b.py").write_text('bar(model="gemini-2.5-flash")')
        models = extract_used_models(tmp_path)
        assert models == {"claude-sonnet-4-6", "gemini-2.5-flash"}


# ── extract_documented_models ─────────────────────────────────────────


class TestExtractDocumentedModels:
    def test_extracts_inline_model_name(self, tmp_path):
        docs = tmp_path / "docs"
        docs.mkdir()
        (docs / "test.md").write_text(
            "The product uses `claude-sonnet-4-6` for narrative generation."
        )
        models = list(extract_documented_models(docs))
        assert len(models) == 1
        assert models[0].name == "claude-sonnet-4-6"

    def test_skips_non_model_inline_code(self, tmp_path):
        docs = tmp_path / "docs"
        docs.mkdir()
        (docs / "test.md").write_text(
            "The file is `backend/api/workflows.py` and the constant is "
            "`PRIMARY_STICKINESS`."
        )
        models = list(extract_documented_models(docs))
        assert models == []

    def test_skips_models_inside_code_blocks(self, tmp_path):
        docs = tmp_path / "docs"
        docs.mkdir()
        (docs / "test.md").write_text(
            "Real: `claude-sonnet-4-6`\n"
            "\n"
            "```python\n"
            "model = 'claude-old-model'\n"
            "```\n"
        )
        models = list(extract_documented_models(docs))
        assert len(models) == 1
        assert models[0].name == "claude-sonnet-4-6"


# ── ModelNamesCheck end-to-end ────────────────────────────────────────


def _make_repo(tmp_path: Path, doc_text: str, code_text: str) -> None:
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "test.md").write_text(doc_text)

    backend = tmp_path / "backend"
    backend.mkdir()
    (backend / "code.py").write_text(code_text)


class TestModelNamesCheck:
    def test_passes_when_model_used_in_code(self, tmp_path):
        _make_repo(
            tmp_path,
            doc_text="Uses `claude-sonnet-4-6` for narrative work.",
            code_text='client.messages.create(model="claude-sonnet-4-6")',
        )
        result = ModelNamesCheck().run(tmp_path)
        assert result.status == Status.PASS
        assert result.items_checked == 1

    def test_fails_when_model_not_in_code(self, tmp_path):
        _make_repo(
            tmp_path,
            doc_text="Uses `claude-old-version` for narrative work.",
            code_text='client.messages.create(model="claude-sonnet-4-6")',
        )
        result = ModelNamesCheck().run(tmp_path)
        assert result.status == Status.FAIL
        assert "claude-old-version" in result.details

    def test_passes_when_no_models_documented(self, tmp_path):
        _make_repo(
            tmp_path,
            doc_text="No model names here.",
            code_text='client.messages.create(model="claude-sonnet-4-6")',
        )
        result = ModelNamesCheck().run(tmp_path)
        assert result.status == Status.PASS
        assert result.items_checked == 0

    def test_skips_when_backend_missing(self, tmp_path):
        docs = tmp_path / "docs"
        docs.mkdir()
        (docs / "test.md").write_text("`claude-sonnet-4-6`")
        result = ModelNamesCheck().run(tmp_path)
        assert result.status == Status.SKIP
