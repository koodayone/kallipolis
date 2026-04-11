"""Unit tests for the backend_test_docstrings check."""

from pathlib import Path

from checks.backend_test_docstrings import BackendTestDocstringsCheck
from checks.base import Status


def _make_test_file(path: Path, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body)


def _valid_docstring(unit: str = "the unit") -> str:
    return (
        f'"""Unit tests for {unit}.\n'
        "\n"
        "Coverage:\n"
        "  - first thing\n"
        "  - second thing\n"
        '"""\n'
    )


class TestBackendTestDocstringsCheck:
    def test_skips_when_backend_missing(self, tmp_path):
        result = BackendTestDocstringsCheck().run(tmp_path)
        assert result.status == Status.SKIP

    def test_skips_when_no_test_files(self, tmp_path):
        (tmp_path / "backend" / "students").mkdir(parents=True)
        result = BackendTestDocstringsCheck().run(tmp_path)
        assert result.status == Status.SKIP

    def test_passes_on_well_formed_test_file(self, tmp_path):
        _make_test_file(
            tmp_path / "backend" / "students" / "test_helpers.py",
            _valid_docstring("students.helpers") + "\ndef test_foo():\n    assert 1 == 1\n",
        )
        result = BackendTestDocstringsCheck().run(tmp_path)
        assert result.status == Status.PASS, result.details
        assert result.items_checked == 1

    def test_fails_when_docstring_is_missing(self, tmp_path):
        _make_test_file(
            tmp_path / "backend" / "students" / "test_helpers.py",
            "def test_foo():\n    assert 1 == 1\n",
        )
        result = BackendTestDocstringsCheck().run(tmp_path)
        assert result.status == Status.FAIL
        assert "docstring is missing" in result.details

    def test_fails_when_coverage_label_is_missing(self, tmp_path):
        _make_test_file(
            tmp_path / "backend" / "students" / "test_helpers.py",
            '"""Just a description with no coverage label."""\n\ndef test_foo():\n    pass\n',
        )
        result = BackendTestDocstringsCheck().run(tmp_path)
        assert result.status == Status.FAIL
        assert "Coverage:" in result.details

    def test_ignores_non_test_files_in_feature_dirs(self, tmp_path):
        # helpers.py has no docstring but is not a test file, so it's out of scope.
        _make_test_file(
            tmp_path / "backend" / "students" / "helpers.py",
            "def compute_gpa(grades):\n    return 0\n",
        )
        result = BackendTestDocstringsCheck().run(tmp_path)
        assert result.status == Status.SKIP

    def test_ignores_integration_tests(self, tmp_path):
        # tests/integration/ is not in _SCANNED_DIRS, so it's out of scope.
        _make_test_file(
            tmp_path / "backend" / "tests" / "integration" / "test_thing.py",
            "def test_thing():\n    pass\n",
        )
        result = BackendTestDocstringsCheck().run(tmp_path)
        assert result.status == Status.SKIP

    def test_scans_multiple_feature_dirs(self, tmp_path):
        _make_test_file(
            tmp_path / "backend" / "students" / "test_helpers.py",
            _valid_docstring("students.helpers") + "\ndef test_foo(): pass\n",
        )
        _make_test_file(
            tmp_path / "backend" / "employers" / "test_generate.py",
            _valid_docstring("employers.generate") + "\ndef test_bar(): pass\n",
        )
        _make_test_file(
            tmp_path / "backend" / "ontology" / "test_mcf_lookup.py",
            _valid_docstring("ontology.mcf_lookup") + "\ndef test_baz(): pass\n",
        )
        result = BackendTestDocstringsCheck().run(tmp_path)
        assert result.status == Status.PASS, result.details
        assert result.items_checked == 3

    def test_reports_all_failing_files(self, tmp_path):
        _make_test_file(
            tmp_path / "backend" / "students" / "test_helpers.py",
            _valid_docstring() + "\ndef test_foo(): pass\n",
        )
        _make_test_file(
            tmp_path / "backend" / "employers" / "test_generate.py",
            "def test_bar(): pass\n",  # no docstring
        )
        _make_test_file(
            tmp_path / "backend" / "llm" / "test_query_engine.py",
            '"""No coverage label."""\n\ndef test_baz(): pass\n',
        )
        result = BackendTestDocstringsCheck().run(tmp_path)
        assert result.status == Status.FAIL
        assert "test_generate.py" in result.details
        assert "test_query_engine.py" in result.details
        assert "test_helpers.py" not in result.details

    def test_ignores_pycache(self, tmp_path):
        _make_test_file(
            tmp_path / "backend" / "students" / "test_helpers.py",
            _valid_docstring() + "\ndef test_foo(): pass\n",
        )
        # A bytecode-like stray file in __pycache__ should be skipped.
        _make_test_file(
            tmp_path / "backend" / "students" / "__pycache__" / "test_helpers.py",
            "def test_stray(): pass\n",
        )
        result = BackendTestDocstringsCheck().run(tmp_path)
        assert result.status == Status.PASS, result.details
        assert result.items_checked == 1

    def test_handles_syntax_error_as_a_reported_issue(self, tmp_path):
        _make_test_file(
            tmp_path / "backend" / "students" / "test_helpers.py",
            "def broken(:\n",
        )
        result = BackendTestDocstringsCheck().run(tmp_path)
        assert result.status == Status.FAIL
        assert "syntax error" in result.details
