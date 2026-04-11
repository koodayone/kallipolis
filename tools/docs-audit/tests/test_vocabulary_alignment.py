"""Unit tests for the vocabulary_alignment check."""

from pathlib import Path

from checks.base import Status
from checks.vocabulary_alignment import (
    VocabularyAlignmentCheck,
    _backend_to_canonical,
    _canonical_to_backend,
    _canonical_to_url_prefix,
)


# ── Transformation helpers ────────────────────────────────────────────


class TestCanonicalToBackend:
    def test_single_word(self):
        assert _canonical_to_backend("students") == "students"

    def test_hyphen_becomes_underscore(self):
        assert _canonical_to_backend("strong-workforce") == "strong_workforce"

    def test_multiple_hyphens(self):
        assert _canonical_to_backend("a-b-c") == "a_b_c"


class TestBackendToCanonical:
    def test_single_word(self):
        assert _backend_to_canonical("students") == "students"

    def test_underscore_becomes_hyphen(self):
        assert _backend_to_canonical("strong_workforce") == "strong-workforce"


class TestCanonicalToUrlPrefix:
    def test_prepends_slash(self):
        assert _canonical_to_url_prefix("students") == "/students"

    def test_preserves_hyphens(self):
        assert _canonical_to_url_prefix("strong-workforce") == "/strong-workforce"


# ── End-to-end check ──────────────────────────────────────────────────


def _make_aligned_repo(tmp_path: Path, units: list[str]) -> Path:
    """Create a minimal repo where every given unit has all four surface forms."""
    # Product docs — one per unit, plus one meta doc.
    product_dir = tmp_path / "docs" / "product"
    product_dir.mkdir(parents=True)
    (product_dir / "overview.md").write_text("# Overview")
    for unit in units:
        (product_dir / f"{unit}.md").write_text(f"# {unit}")

    # Backend feature dirs.
    backend_dir = tmp_path / "backend"
    backend_dir.mkdir()
    for unit in units:
        feature_dir = backend_dir / unit.replace("-", "_")
        feature_dir.mkdir()

    # main.py with the right router prefixes.
    main_lines = ["from fastapi import FastAPI", "app = FastAPI()"]
    for unit in units:
        main_lines.append(
            f'app.include_router({unit.replace("-", "_")}_router, '
            f'prefix="/{unit}", tags=["T"])'
        )
    (backend_dir / "main.py").write_text("\n".join(main_lines))

    # Atlas feature dirs.
    atlas_dir = tmp_path / "atlas" / "college-atlas"
    atlas_dir.mkdir(parents=True)
    for unit in units:
        (atlas_dir / unit).mkdir()

    return tmp_path


class TestVocabularyAlignmentCheck:
    def test_passes_on_aligned_single_unit(self, tmp_path):
        _make_aligned_repo(tmp_path, ["students"])
        result = VocabularyAlignmentCheck().run(tmp_path)
        assert result.status == Status.PASS, result.details

    def test_passes_on_hyphenated_unit(self, tmp_path):
        _make_aligned_repo(tmp_path, ["strong-workforce"])
        result = VocabularyAlignmentCheck().run(tmp_path)
        assert result.status == Status.PASS, result.details

    def test_passes_on_multiple_units(self, tmp_path):
        _make_aligned_repo(
            tmp_path, ["students", "courses", "employers", "strong-workforce"]
        )
        result = VocabularyAlignmentCheck().run(tmp_path)
        assert result.status == Status.PASS, result.details

    def test_skips_when_no_product_docs(self, tmp_path):
        result = VocabularyAlignmentCheck().run(tmp_path)
        assert result.status == Status.SKIP

    def test_skips_when_only_meta_docs(self, tmp_path):
        product_dir = tmp_path / "docs" / "product"
        product_dir.mkdir(parents=True)
        (product_dir / "overview.md").write_text("")
        (product_dir / "the-ontology.md").write_text("")
        result = VocabularyAlignmentCheck().run(tmp_path)
        assert result.status == Status.SKIP

    def test_flags_missing_backend_dir(self, tmp_path):
        _make_aligned_repo(tmp_path, ["students"])
        import shutil
        shutil.rmtree(tmp_path / "backend" / "students")
        result = VocabularyAlignmentCheck().run(tmp_path)
        assert result.status == Status.FAIL
        assert "backend/students" in result.details

    def test_flags_missing_atlas_dir(self, tmp_path):
        _make_aligned_repo(tmp_path, ["students"])
        import shutil
        shutil.rmtree(tmp_path / "atlas" / "college-atlas" / "students")
        result = VocabularyAlignmentCheck().run(tmp_path)
        assert result.status == Status.FAIL
        assert "atlas/college-atlas/students" in result.details

    def test_flags_missing_url_prefix(self, tmp_path):
        _make_aligned_repo(tmp_path, ["students"])
        # Rewrite main.py without the router mount.
        (tmp_path / "backend" / "main.py").write_text(
            "from fastapi import FastAPI\napp = FastAPI()\n"
        )
        result = VocabularyAlignmentCheck().run(tmp_path)
        assert result.status == Status.FAIL
        assert "/students" in result.details

    def test_flags_backend_dir_without_product_doc(self, tmp_path):
        _make_aligned_repo(tmp_path, ["students"])
        # Add an extra backend feature without a product doc.
        (tmp_path / "backend" / "mystery").mkdir()
        result = VocabularyAlignmentCheck().run(tmp_path)
        assert result.status == Status.FAIL
        assert "backend/mystery" in result.details
        assert "mystery.md" in result.details

    def test_flags_atlas_dir_without_product_doc(self, tmp_path):
        _make_aligned_repo(tmp_path, ["students"])
        # Add an extra atlas feature without a product doc.
        (tmp_path / "atlas" / "college-atlas" / "mystery").mkdir()
        result = VocabularyAlignmentCheck().run(tmp_path)
        assert result.status == Status.FAIL
        assert "atlas/college-atlas/mystery" in result.details

    def test_hyphen_underscore_transform_works(self, tmp_path):
        """A hyphenated unit doc maps to an underscored backend dir."""
        _make_aligned_repo(tmp_path, ["strong-workforce"])
        # Verify the backend dir was created with underscores.
        assert (tmp_path / "backend" / "strong_workforce").exists()
        # And the atlas dir with hyphens.
        assert (tmp_path / "atlas" / "college-atlas" / "strong-workforce").exists()
        # And the full check passes.
        result = VocabularyAlignmentCheck().run(tmp_path)
        assert result.status == Status.PASS, result.details

    def test_ignores_backend_non_feature_dirs(self, tmp_path):
        _make_aligned_repo(tmp_path, ["students"])
        # Shared infrastructure dirs should not be treated as missing features.
        (tmp_path / "backend" / "ontology").mkdir()
        (tmp_path / "backend" / "llm").mkdir()
        (tmp_path / "backend" / "pipeline").mkdir()
        result = VocabularyAlignmentCheck().run(tmp_path)
        assert result.status == Status.PASS, result.details

    def test_meta_docs_do_not_require_code(self, tmp_path):
        _make_aligned_repo(tmp_path, ["students"])
        # Adding more meta docs should not create new unit expectations.
        (tmp_path / "docs" / "product" / "the-atlas.md").write_text("")
        (tmp_path / "docs" / "product" / "the-skills-taxonomy.md").write_text("")
        result = VocabularyAlignmentCheck().run(tmp_path)
        assert result.status == Status.PASS, result.details
