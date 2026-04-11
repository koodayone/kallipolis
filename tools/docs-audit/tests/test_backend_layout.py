"""Unit tests for the backend_layout check."""

from pathlib import Path

from checks.backend_layout import BackendLayoutCheck
from checks.base import Status


def _make_valid_backend(tmp_path: Path) -> Path:
    """Create a minimal valid backend tree that passes every rule."""
    backend = tmp_path / "backend"
    backend.mkdir()
    (backend / "main.py").write_text("")
    (backend / "__init__.py").write_text("")

    # The six feature directories, each with the core file shape.
    for feature in (
        "students",
        "courses",
        "occupations",
        "employers",
        "partnerships",
        "strong_workforce",
    ):
        fdir = backend / feature
        fdir.mkdir()
        (fdir / "__init__.py").write_text("")
        (fdir / "api.py").write_text("")
        (fdir / "models.py").write_text("")

    # Shared infrastructure and orchestration directories (allowed but
    # don't need a specific file shape).
    for d in ("ontology", "llm", "pipeline", "tests", "scripts", "docs"):
        (backend / d).mkdir()

    return backend


class TestBackendLayoutCheck:
    def test_passes_on_valid_tree(self, tmp_path):
        _make_valid_backend(tmp_path)
        result = BackendLayoutCheck().run(tmp_path)
        assert result.status == Status.PASS, result.details

    def test_skips_when_backend_missing(self, tmp_path):
        result = BackendLayoutCheck().run(tmp_path)
        assert result.status == Status.SKIP

    def test_flags_unknown_top_level_dir(self, tmp_path):
        _make_valid_backend(tmp_path)
        (tmp_path / "backend" / "utils").mkdir()
        result = BackendLayoutCheck().run(tmp_path)
        assert result.status == Status.FAIL
        assert "backend/utils/" in result.details

    def test_flags_stray_python_file_at_top_level(self, tmp_path):
        _make_valid_backend(tmp_path)
        (tmp_path / "backend" / "helpers.py").write_text("")
        result = BackendLayoutCheck().run(tmp_path)
        assert result.status == Status.FAIL
        assert "backend/helpers.py" in result.details

    def test_flags_feature_missing_core_file(self, tmp_path):
        _make_valid_backend(tmp_path)
        # Remove students/api.py so the feature is missing a core file.
        (tmp_path / "backend" / "students" / "api.py").unlink()
        result = BackendLayoutCheck().run(tmp_path)
        assert result.status == Status.FAIL
        assert "students" in result.details
        assert "api.py" in result.details

    def test_flags_missing_feature_directory(self, tmp_path):
        _make_valid_backend(tmp_path)
        # Remove the whole partnerships feature dir.
        import shutil
        shutil.rmtree(tmp_path / "backend" / "partnerships")
        result = BackendLayoutCheck().run(tmp_path)
        assert result.status == Status.FAIL
        assert "partnerships" in result.details

    def test_dotfiles_are_ignored(self, tmp_path):
        _make_valid_backend(tmp_path)
        (tmp_path / "backend" / ".DS_Store").write_text("")
        (tmp_path / "backend" / ".gitignore").write_text("")
        (tmp_path / "backend" / ".github").mkdir()
        result = BackendLayoutCheck().run(tmp_path)
        assert result.status == Status.PASS, result.details

    def test_pycache_is_ignored(self, tmp_path):
        _make_valid_backend(tmp_path)
        (tmp_path / "backend" / "__pycache__").mkdir()
        result = BackendLayoutCheck().run(tmp_path)
        assert result.status == Status.PASS, result.details

    def test_allowed_top_level_files_pass(self, tmp_path):
        _make_valid_backend(tmp_path)
        (tmp_path / "backend" / "README.md").write_text("")
        (tmp_path / "backend" / "Dockerfile").write_text("")
        (tmp_path / "backend" / "requirements.txt").write_text("")
        (tmp_path / "backend" / "run_all.sh").write_text("")
        result = BackendLayoutCheck().run(tmp_path)
        assert result.status == Status.PASS, result.details

    def test_multiple_violations_all_reported(self, tmp_path):
        _make_valid_backend(tmp_path)
        (tmp_path / "backend" / "utils").mkdir()
        (tmp_path / "backend" / "helpers.py").write_text("")
        result = BackendLayoutCheck().run(tmp_path)
        assert result.status == Status.FAIL
        assert "backend/utils/" in result.details
        assert "backend/helpers.py" in result.details
