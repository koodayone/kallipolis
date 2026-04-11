"""Unit tests for the atlas_test_headers check."""

from pathlib import Path

from checks.atlas_test_headers import AtlasTestHeadersCheck
from checks.base import Status


VALID_HEADER = """/**
 * Tests for doThing — the thing that does the thing.
 *
 * Coverage:
 *   - Does the thing
 *   - Does not not do the thing
 */

import { describe, it, expect } from "vitest";

describe("doThing", () => {
  it("does the thing", () => {
    expect(true).toBe(true);
  });
});
"""


HEADER_MISSING_COVERAGE = """/**
 * Tests for doThing. No Coverage label here.
 */

import { describe, it, expect } from "vitest";

describe("doThing", () => {
  it("does the thing", () => {
    expect(true).toBe(true);
  });
});
"""


NO_HEADER_AT_ALL = """import { describe, it, expect } from "vitest";

describe("doThing", () => {
  it("does the thing", () => {
    expect(true).toBe(true);
  });
});
"""


HEADER_WITH_UNCLOSED_BLOCK = """/**
 * Tests for doThing.

import { describe, it, expect } from "vitest";
"""


def _make_atlas_with_test(tmp_path: Path, relative_test_path: str, contents: str) -> Path:
    """Build a tmp atlas/ tree with one test file at the given relative path."""
    atlas = tmp_path / "atlas"
    atlas.mkdir(parents=True, exist_ok=True)
    test_file = atlas / relative_test_path
    test_file.parent.mkdir(parents=True, exist_ok=True)
    test_file.write_text(contents)
    return test_file


class TestAtlasTestHeadersCheck:
    def test_skips_when_atlas_missing(self, tmp_path):
        result = AtlasTestHeadersCheck().run(tmp_path)
        assert result.status == Status.SKIP

    def test_skips_when_no_test_files_present(self, tmp_path):
        (tmp_path / "atlas").mkdir()
        result = AtlasTestHeadersCheck().run(tmp_path)
        assert result.status == Status.SKIP

    def test_passes_on_valid_header(self, tmp_path):
        _make_atlas_with_test(
            tmp_path,
            "college-atlas/thing/thing.test.ts",
            VALID_HEADER,
        )
        result = AtlasTestHeadersCheck().run(tmp_path)
        assert result.status == Status.PASS, result.details
        assert result.items_checked == 1

    def test_passes_on_valid_tsx_file(self, tmp_path):
        _make_atlas_with_test(
            tmp_path,
            "college-atlas/thing/Thing.test.tsx",
            VALID_HEADER,
        )
        result = AtlasTestHeadersCheck().run(tmp_path)
        assert result.status == Status.PASS, result.details

    def test_fails_when_header_missing(self, tmp_path):
        _make_atlas_with_test(
            tmp_path,
            "college-atlas/thing/thing.test.ts",
            NO_HEADER_AT_ALL,
        )
        result = AtlasTestHeadersCheck().run(tmp_path)
        assert result.status == Status.FAIL
        assert "JSDoc opener" in result.details
        assert "thing.test.ts" in result.details

    def test_fails_when_coverage_label_missing(self, tmp_path):
        _make_atlas_with_test(
            tmp_path,
            "college-atlas/thing/thing.test.ts",
            HEADER_MISSING_COVERAGE,
        )
        result = AtlasTestHeadersCheck().run(tmp_path)
        assert result.status == Status.FAIL
        assert "Coverage:" in result.details

    def test_fails_when_block_never_closes(self, tmp_path):
        _make_atlas_with_test(
            tmp_path,
            "college-atlas/thing/thing.test.ts",
            HEADER_WITH_UNCLOSED_BLOCK,
        )
        result = AtlasTestHeadersCheck().run(tmp_path)
        assert result.status == Status.FAIL
        assert "matching '*/'" in result.details

    def test_ignores_files_inside_node_modules(self, tmp_path):
        """Test files inside node_modules/ must not be checked."""
        nm = tmp_path / "atlas" / "node_modules" / "some-dep" / "foo.test.ts"
        nm.parent.mkdir(parents=True)
        nm.write_text(NO_HEADER_AT_ALL)
        result = AtlasTestHeadersCheck().run(tmp_path)
        # No real test files present, so the check should skip.
        assert result.status == Status.SKIP

    def test_ignores_files_inside_next_build_output(self, tmp_path):
        """Test files inside .next/ must not be checked."""
        nx = tmp_path / "atlas" / ".next" / "types" / "foo.test.ts"
        nx.parent.mkdir(parents=True)
        nx.write_text(NO_HEADER_AT_ALL)
        result = AtlasTestHeadersCheck().run(tmp_path)
        assert result.status == Status.SKIP

    def test_reports_multiple_bad_files_together(self, tmp_path):
        _make_atlas_with_test(tmp_path, "a/a.test.ts", NO_HEADER_AT_ALL)
        _make_atlas_with_test(tmp_path, "b/b.test.ts", HEADER_MISSING_COVERAGE)
        _make_atlas_with_test(tmp_path, "c/c.test.ts", VALID_HEADER)

        result = AtlasTestHeadersCheck().run(tmp_path)
        assert result.status == Status.FAIL
        assert result.items_checked == 3
        assert "a/a.test.ts" in result.details
        assert "b/b.test.ts" in result.details
        # The passing file should not appear in the details.
        assert "c/c.test.ts" not in result.details
