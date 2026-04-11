"""Unit tests for the numerical_constants check and its helpers."""

from pathlib import Path

from checks.base import Status
from checks.numerical_constants import (
    DOC_CONSTANT_RE,
    NumericalConstantsCheck,
    extract_actual_constants,
    extract_documented_constants,
)


# ── DOC_CONSTANT_RE ───────────────────────────────────────────────────


class TestDocConstantRegex:
    def test_int_constant(self):
        m = DOC_CONSTANT_RE.match("DEPT_CAP = 6")
        assert m.group(1) == "DEPT_CAP"
        assert m.group(2) == "6"

    def test_float_constant(self):
        m = DOC_CONSTANT_RE.match("PRIMARY_STICKINESS = 0.60")
        assert m.group(1) == "PRIMARY_STICKINESS"
        assert m.group(2) == "0.60"

    def test_negative(self):
        m = DOC_CONSTANT_RE.match("OFFSET = -3")
        assert m.group(2) == "-3"

    def test_lowercase_does_not_match(self):
        assert DOC_CONSTANT_RE.match("dept_cap = 6") is None

    def test_mixed_case_does_not_match(self):
        assert DOC_CONSTANT_RE.match("DeptCap = 6") is None

    def test_non_numeric_value_does_not_match(self):
        assert DOC_CONSTANT_RE.match('NAME = "foo"') is None

    def test_strips_whitespace(self):
        m = DOC_CONSTANT_RE.match("  DEPT_CAP = 6  ")
        assert m is not None


# ── extract_actual_constants ──────────────────────────────────────────


class TestExtractActualConstants:
    def test_extracts_int_and_float(self, tmp_path):
        (tmp_path / "config.py").write_text(
            "DEPT_CAP = 6\n"
            "PRIMARY_STICKINESS = 0.60\n"
        )
        result = extract_actual_constants(tmp_path)
        assert result["DEPT_CAP"] == {6.0}
        assert result["PRIMARY_STICKINESS"] == {0.6}

    def test_aggregates_across_files(self, tmp_path):
        (tmp_path / "a.py").write_text("BATCH_SIZE = 500\n")
        (tmp_path / "b.py").write_text("BATCH_SIZE = 500\n")
        (tmp_path / "c.py").write_text("BATCH_SIZE = 100\n")
        result = extract_actual_constants(tmp_path)
        assert result["BATCH_SIZE"] == {500.0, 100.0}

    def test_skips_non_constant_assignments(self, tmp_path):
        (tmp_path / "x.py").write_text(
            "DEPT_CAP = 6\n"
            "lower = 5\n"
            "MyClass = 7\n"  # not all-uppercase
            "ITEMS = [1, 2, 3]\n"  # not a numeric literal
            "NAME = 'foo'\n"  # not numeric
            "TRUTH = True\n"  # bool excluded
        )
        result = extract_actual_constants(tmp_path)
        assert "DEPT_CAP" in result
        assert "lower" not in result
        assert "MyClass" not in result
        assert "ITEMS" not in result
        assert "NAME" not in result
        assert "TRUTH" not in result

    def test_skips_function_locals(self, tmp_path):
        (tmp_path / "x.py").write_text(
            "DEPT_CAP = 6\n"
            "def f():\n"
            "    LOCAL = 99\n"
            "    return LOCAL\n"
        )
        result = extract_actual_constants(tmp_path)
        assert "DEPT_CAP" in result
        assert "LOCAL" not in result

    def test_skips_cache_and_test_dirs(self, tmp_path):
        (tmp_path / "real.py").write_text("REAL_CONST = 1\n")

        cache_dir = tmp_path / "cache"
        cache_dir.mkdir()
        (cache_dir / "junk.py").write_text("CACHE_CONST = 1\n")

        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        (tests_dir / "t.py").write_text("TEST_CONST = 1\n")

        result = extract_actual_constants(tmp_path)
        assert "REAL_CONST" in result
        assert "CACHE_CONST" not in result
        assert "TEST_CONST" not in result

    def test_returns_empty_when_dir_missing(self, tmp_path):
        assert extract_actual_constants(tmp_path / "nope") == {}


# ── extract_documented_constants ──────────────────────────────────────


class TestExtractDocumentedConstants:
    def test_extracts_inline_code_constants(self, tmp_path):
        docs = tmp_path / "docs"
        docs.mkdir()
        (docs / "x.md").write_text(
            "The cap is `DEPT_CAP = 6` per department.\n"
            "Stickiness: `PRIMARY_STICKINESS = 0.60`.\n"
        )
        result = extract_documented_constants(docs)
        names = {c.name for c in result}
        assert names == {"DEPT_CAP", "PRIMARY_STICKINESS"}

    def test_skips_non_constant_inline_code(self, tmp_path):
        docs = tmp_path / "docs"
        docs.mkdir()
        (docs / "x.md").write_text(
            "Path: `backend/foo.py` and constant `DEPT_CAP = 6`.\n"
        )
        result = extract_documented_constants(docs)
        assert len(result) == 1
        assert result[0].name == "DEPT_CAP"

    def test_skips_constants_inside_code_blocks(self, tmp_path):
        docs = tmp_path / "docs"
        docs.mkdir()
        (docs / "x.md").write_text(
            "Real: `DEPT_CAP = 6`\n"
            "\n"
            "```python\n"
            "FAKE = 99\n"
            "```\n"
        )
        result = extract_documented_constants(docs)
        assert len(result) == 1
        assert result[0].name == "DEPT_CAP"


# ── NumericalConstantsCheck end-to-end ────────────────────────────────


def _make_repo(tmp_path: Path, doc_text: str, py_text: str) -> None:
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "test.md").write_text(doc_text)

    backend = tmp_path / "backend"
    backend.mkdir()
    (backend / "config.py").write_text(py_text)


class TestNumericalConstantsCheck:
    def test_passes_when_doc_matches_code(self, tmp_path):
        _make_repo(
            tmp_path,
            doc_text="The cap is `DEPT_CAP = 6`.",
            py_text="DEPT_CAP = 6\n",
        )
        result = NumericalConstantsCheck().run(tmp_path)
        assert result.status == Status.PASS, result.details
        assert result.items_checked == 1

    def test_passes_when_float_values_are_equivalent(self, tmp_path):
        _make_repo(
            tmp_path,
            doc_text="`PRIMARY_STICKINESS = 0.60`",
            py_text="PRIMARY_STICKINESS = 0.6\n",
        )
        result = NumericalConstantsCheck().run(tmp_path)
        assert result.status == Status.PASS

    def test_fails_when_value_drifted(self, tmp_path):
        _make_repo(
            tmp_path,
            doc_text="The cap is `DEPT_CAP = 6`.",
            py_text="DEPT_CAP = 8\n",
        )
        result = NumericalConstantsCheck().run(tmp_path)
        assert result.status == Status.FAIL
        assert "DEPT_CAP" in result.details
        assert "8" in result.details

    def test_fails_when_constant_not_defined(self, tmp_path):
        _make_repo(
            tmp_path,
            doc_text="`MISSING_CONST = 42`",
            py_text="OTHER = 1\n",
        )
        result = NumericalConstantsCheck().run(tmp_path)
        assert result.status == Status.FAIL
        assert "MISSING_CONST" in result.details
        assert "no such constant" in result.details

    def test_passes_when_one_of_many_definitions_matches(self, tmp_path):
        # BATCH_SIZE is defined in two files; doc claims one of them.
        docs = tmp_path / "docs"
        docs.mkdir()
        (docs / "x.md").write_text("`BATCH_SIZE = 500`")

        backend = tmp_path / "backend"
        backend.mkdir()
        (backend / "a.py").write_text("BATCH_SIZE = 500\n")
        (backend / "b.py").write_text("BATCH_SIZE = 100\n")

        result = NumericalConstantsCheck().run(tmp_path)
        assert result.status == Status.PASS

    def test_passes_with_no_documented_claims(self, tmp_path):
        _make_repo(
            tmp_path,
            doc_text="No constants here.",
            py_text="DEPT_CAP = 6\n",
        )
        result = NumericalConstantsCheck().run(tmp_path)
        assert result.status == Status.PASS
        assert result.items_checked == 0

    def test_skips_when_docs_missing(self, tmp_path):
        backend = tmp_path / "backend"
        backend.mkdir()
        (backend / "config.py").write_text("DEPT_CAP = 6\n")
        result = NumericalConstantsCheck().run(tmp_path)
        assert result.status == Status.SKIP

    def test_skips_when_backend_missing(self, tmp_path):
        docs = tmp_path / "docs"
        docs.mkdir()
        (docs / "x.md").write_text("`DEPT_CAP = 6`")
        result = NumericalConstantsCheck().run(tmp_path)
        assert result.status == Status.SKIP
