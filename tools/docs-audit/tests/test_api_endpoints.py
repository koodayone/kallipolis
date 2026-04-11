"""Unit tests for the api_endpoints check and its helpers."""

from pathlib import Path

from checks.api_endpoints import (
    APIEndpointsCheck,
    extract_actual_endpoints,
    extract_documented_endpoints,
    extract_router_prefixes,
)
from checks.base import Status


# ── extract_router_prefixes ───────────────────────────────────────────


class TestExtractRouterPrefixes:
    def test_single_router(self, tmp_path):
        main_py = tmp_path / "main.py"
        main_py.write_text(
            'app.include_router(ontology_router, prefix="/ontology", tags=["O"])\n'
        )
        prefixes = extract_router_prefixes(main_py)
        assert prefixes == {"ontology": "/ontology"}

    def test_multiple_routers(self, tmp_path):
        main_py = tmp_path / "main.py"
        main_py.write_text(
            'app.include_router(ontology_router, prefix="/ontology", tags=["O"])\n'
            'app.include_router(workflows_router, prefix="/workflows", tags=["W"])\n'
            'app.include_router(labor_market_router, prefix="/labor-market", tags=["L"])\n'
        )
        prefixes = extract_router_prefixes(main_py)
        assert prefixes == {
            "ontology": "/ontology",
            "workflows": "/workflows",
            "labor_market": "/labor-market",
        }


# ── extract_actual_endpoints ──────────────────────────────────────────


class TestExtractActualEndpoints:
    def test_extracts_endpoints_with_prefix(self, tmp_path):
        backend_dir = tmp_path / "backend"
        feature_dir = backend_dir / "students"
        feature_dir.mkdir(parents=True)
        (feature_dir / "api.py").write_text(
            "@router.get('/')\n"
            "def list_students(): pass\n"
            "\n"
            '@router.post("/query")\n'
            "def query_students(): pass\n"
        )
        prefixes = {"students": "/students"}
        endpoints = extract_actual_endpoints(backend_dir, prefixes)
        assert ("GET", "/students") in endpoints
        assert ("POST", "/students/query") in endpoints

    def test_feature_without_api_file_is_skipped(self, tmp_path):
        # A feature listed in prefixes but without an api.py file is silently
        # ignored (e.g., a feature that holds data and helpers but no routes).
        backend_dir = tmp_path / "backend"
        (backend_dir / "students").mkdir(parents=True)
        prefixes = {"students": "/students"}
        endpoints = extract_actual_endpoints(backend_dir, prefixes)
        assert endpoints == set()


# ── extract_documented_endpoints ──────────────────────────────────────


class TestExtractDocumentedEndpoints:
    def test_extracts_inline_endpoint(self, tmp_path):
        docs = tmp_path / "docs"
        docs.mkdir()
        (docs / "test.md").write_text(
            "The endpoint `POST /workflows/foo` does something."
        )
        endpoints = list(extract_documented_endpoints(docs))
        assert len(endpoints) == 1
        assert endpoints[0].method == "POST"
        assert endpoints[0].path == "/workflows/foo"

    def test_extracts_multiple_endpoints(self, tmp_path):
        docs = tmp_path / "docs"
        docs.mkdir()
        (docs / "test.md").write_text(
            "Use `GET /a` to read and `POST /b` to write."
        )
        endpoints = list(extract_documented_endpoints(docs))
        assert len(endpoints) == 2

    def test_skips_endpoints_in_code_blocks(self, tmp_path):
        docs = tmp_path / "docs"
        docs.mkdir()
        (docs / "test.md").write_text(
            "Real: `GET /real`\n"
            "\n"
            "```\n"
            "Example: `POST /not-real`\n"
            "```\n"
        )
        endpoints = list(extract_documented_endpoints(docs))
        assert len(endpoints) == 1
        assert endpoints[0].path == "/real"


# ── APIEndpointsCheck end-to-end ──────────────────────────────────────


def _make_minimal_repo(
    tmp_path: Path, doc_text: str, code_text: str, prefix: str = "/test"
) -> None:
    """Create a minimal repo with one doc and one feature router file."""
    docs = tmp_path / "docs"
    docs.mkdir(parents=True)
    (docs / "test.md").write_text(doc_text)

    feature_dir = tmp_path / "backend" / "test"
    feature_dir.mkdir(parents=True)
    (feature_dir / "api.py").write_text(code_text)

    main = tmp_path / "backend" / "main.py"
    main.write_text(
        f'app.include_router(test_router, prefix="{prefix}", tags=["T"])\n'
    )


class TestAPIEndpointsCheck:
    def test_passes_when_endpoint_exists(self, tmp_path):
        _make_minimal_repo(
            tmp_path,
            doc_text="See `POST /test/foo` for details.",
            code_text='@router.post("/foo")\ndef foo(): pass\n',
        )
        result = APIEndpointsCheck().run(tmp_path)
        assert result.status == Status.PASS
        assert result.items_checked == 1

    def test_fails_when_endpoint_does_not_exist(self, tmp_path):
        _make_minimal_repo(
            tmp_path,
            doc_text="See `POST /test/missing` for details.",
            code_text='@router.post("/foo")\ndef foo(): pass\n',
        )
        result = APIEndpointsCheck().run(tmp_path)
        assert result.status == Status.FAIL
        assert "/test/missing" in result.details

    def test_passes_when_no_endpoints_documented(self, tmp_path):
        _make_minimal_repo(
            tmp_path,
            doc_text="No endpoint mentions here.",
            code_text='@router.get("/foo")\ndef foo(): pass\n',
        )
        result = APIEndpointsCheck().run(tmp_path)
        assert result.status == Status.PASS
        assert result.items_checked == 0

    def test_skips_when_main_missing(self, tmp_path):
        docs = tmp_path / "docs"
        docs.mkdir()
        (docs / "test.md").write_text("`POST /foo`")
        result = APIEndpointsCheck().run(tmp_path)
        assert result.status == Status.SKIP
