"""Unit + integration tests for courses.department_mapping.

This module owns the `{prefix → canonical_name}` resolution that converts
a course code's subject prefix into a human-readable department display
name. It backs Stage 2.5 of the extraction pipeline, which rewrites the
`department` field on every enriched course before Neo4j load.

Coverage:
  - Prefix extraction handles single-word ("MATH 1A"), multi-word
    ("C S 81", "V T 51A"), CCCN-style ("POLS C1000"), 3-token
    ("MED A 10"), honors-suffixed ("MATH 1AHP"), and annotation-marker
    ("ENGL 1B*") course codes; rejects malformed input.
  - Invariant enforcement on mapping files: bare codes rejected,
    parenthesized code suffixes rejected, short names rejected, empty
    values rejected, multi-word prefixes accepted.
  - Resolver assembles base + overlay correctly, handles whitelisted
    collisions (POLI+POLS → "Political Science"), raises on unmapped
    prefixes in strict mode, emits "Unmapped: PREFIX" placeholders in
    non-strict mode.
  - canonicalize_courses rewrites department fields per prefix mapping
    and applies surface cleanup to pass-through courses with unparseable
    codes.
  - Cross-college human-readable invariant: every prefix used in every
    featured college's enriched.json resolves to a human-readable name,
    no bare codes, no parenthesized code suffixes. This is the CI gate
    that catches regressions when a new catalog introduces a prefix
    without a mapping entry.
  - Live mapping file sanity: base.json and every overlay load without
    invariant violations.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from courses.department_mapping import (
    BASE_PATH,
    MAPPING_DIR,
    OVERLAY_DIR,
    InvalidMappingError,
    UnknownPrefixError,
    _load_mapping_file,
    canonical_name,
    canonicalize_courses,
    extract_prefix,
    resolve,
    resolve_unknown_prefixes,
)

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
CACHE_DIR = REPO_ROOT / "backend" / "pipeline" / "cache"

# Colleges that have been onboarded with both an enriched JSON and a
# committed overlay. The CI invariant check is scoped to these; colleges
# without an overlay file aren't expected to pass yet.
ONBOARDED_COLLEGES = [
    "foothill", "shasta", "sequoias", "oxnard", "compton",
    "irvinevalley", "desert", "sandiegocity",
]


# ── 1. Prefix extraction ─────────────────────────────────────────────────


class TestExtractPrefix:
    """The parser must be robust to every code shape the catalogs produce."""

    @pytest.mark.parametrize(
        "code,expected",
        [
            # Single-word prefixes
            ("MATH 1A", "MATH"),
            ("ENGL 1C", "ENGL"),
            ("BIOL 40A", "BIOL"),
            ("PSYC C1000H", "PSYC"),
            # Multi-word prefixes — critical: each preserves its internal space
            ("C S 81", "C S"),
            ("D A 50", "D A"),
            ("D H 356", "D H"),
            ("V T 51A", "V T"),
            ("R T 53AL", "R T"),
            ("L A 50", "L A"),
            # 3-token prefix (rare but exists, e.g., "MED A 10")
            ("MED A 10", "MED A"),
            # CCCN-style codes: number starts with a letter
            ("POLS C1000", "POLS"),
            ("COMM C1000", "COMM"),
            ("STAT C1000", "STAT"),
            # Honors/program suffixes (3+ trailing letters)
            ("MATH 1AHP", "MATH"),
            ("MATH 1BHP", "MATH"),
            # Catalog annotation markers (Shasta uses * and # for transfer
            # and prerequisite flags). These are not part of the code proper.
            ("ENGL 1B*", "ENGL"),
            ("ENGL C1001#", "ENGL"),
            ("PSYC 1*", "PSYC"),
            ("COMM C1000*", "COMM"),
        ],
    )
    def test_well_formed(self, code: str, expected: str) -> None:
        assert extract_prefix(code) == expected

    @pytest.mark.parametrize(
        "code",
        [
            "",
            "   ",
            "invalid",  # no whitespace
            "MATH",  # no course number
            "MATH abc",  # course "number" isn't digit-shaped
            "foo bar",  # lowercase prefix rejected; bar isn't a number
        ],
    )
    def test_malformed(self, code: str) -> None:
        assert extract_prefix(code) is None


# ── 2. Invariant enforcement ─────────────────────────────────────────────


class TestInvariants:
    """Mapping files that violate the human-readable invariants must fail
    loudly at load time. The resolver is the single enforcement point; if
    it passes bad data, the UI inherits bad data."""

    def _write_overlay(self, tmp_path: Path, prefixes: dict[str, str], meta: dict | None = None) -> Path:
        path = tmp_path / "overlays"
        path.mkdir()
        fake_overlay = path / "fake.json"
        fake_overlay.write_text(
            json.dumps(
                {
                    "_meta": meta or {},
                    "prefixes": prefixes,
                },
            )
        )
        return fake_overlay

    def test_bare_code_rejected(self, tmp_path: Path) -> None:
        """`STAT → "STAT"` must be rejected — bare codes are a UI failure."""
        fake = self._write_overlay(tmp_path, {"STAT": "STAT"})
        with pytest.raises(InvalidMappingError, match="bare code"):
            _load_mapping_file(fake)

    def test_parenthesized_code_suffix_rejected(self, tmp_path: Path) -> None:
        """`DANC → "Dance (DANC)"` must be rejected — this is the exact
        fragmentation pattern the module exists to eliminate."""
        fake = self._write_overlay(tmp_path, {"DANC": "Dance (DANC)"})
        with pytest.raises(InvalidMappingError, match="parenthesized code"):
            _load_mapping_file(fake)

    def test_short_name_rejected(self, tmp_path: Path) -> None:
        fake = self._write_overlay(tmp_path, {"FOO": "Hi"})
        with pytest.raises(InvalidMappingError, match="too short"):
            _load_mapping_file(fake)

    def test_empty_name_rejected(self, tmp_path: Path) -> None:
        fake = self._write_overlay(tmp_path, {"FOO": ""})
        with pytest.raises(InvalidMappingError):
            _load_mapping_file(fake)

    def test_multiword_prefix_accepted(self, tmp_path: Path) -> None:
        """Multi-word prefixes are valid and common — `"C S"` must load."""
        fake = self._write_overlay(tmp_path, {"C S": "Computer Science"})
        got = _load_mapping_file(fake)
        assert got == {"C S": "Computer Science"}


# ── 3. Resolution + canonicalization ─────────────────────────────────────


class TestResolve:
    """The live base + Foothill mapping is the smallest non-trivial test."""

    def test_foothill_resolves(self) -> None:
        m = resolve("foothill")
        assert m["MATH"] == "Mathematics"
        assert m["DANC"] == "Dance"
        assert m["STAT"] == "Statistics"
        assert m["COMM"] == "Communication Studies"
        assert m["V T"] == "Veterinary Technology"
        assert m["C S"] == "Computer Science"

    def test_poli_pols_intentional_collision(self) -> None:
        """POLI and POLS are the old and new CCCN numbering for the same
        subject. Both must resolve to "Political Science" and the collision
        must be whitelisted (not raise)."""
        m = resolve("foothill")
        assert m["POLI"] == "Political Science"
        assert m["POLS"] == "Political Science"

    def test_canonical_name_strict_raises_on_unknown(self) -> None:
        with pytest.raises(UnknownPrefixError) as excinfo:
            canonical_name("ZZZZ 99", "foothill", strict=True)
        assert excinfo.value.prefix == "ZZZZ"
        assert "overlays/foothill.json" in str(excinfo.value)

    def test_canonical_name_non_strict_returns_placeholder(self) -> None:
        got = canonical_name("ZZZZ 99", "foothill", strict=False)
        assert got == "Unmapped: ZZZZ"

    def test_canonicalize_courses_rewrites_department(self) -> None:
        courses = [
            {"code": "DANC 18A", "department": "Dance (DANC)"},
            {"code": "DANC 10", "department": "Dance"},  # already canonical
            {"code": "STAT C1000", "department": "Mathematics (MATH)"},
            {"code": "MATH 1A", "department": "Mathematics"},  # already canonical
        ]
        new, rewrote = canonicalize_courses(courses, "foothill")
        assert new[0]["department"] == "Dance"
        assert new[1]["department"] == "Dance"
        assert new[2]["department"] == "Statistics"
        assert new[3]["department"] == "Mathematics"
        assert rewrote == 2  # two courses had their department changed

    def test_canonicalize_courses_cleans_passthrough_parens(self) -> None:
        """Courses with unparseable codes pass through, but their Gemini
        department string is still lightly cleaned of parenthesized-code
        suffixes so they don't form singleton UI buckets."""
        courses = [
            # Unparseable code (slash-alternate numbering); Gemini gave a
            # parens-suffix label — that suffix should be stripped.
            {"code": "IS 99/199", "department": "Independent Study (IS)"},
            # Unparseable code + already-clean label → no change.
            {"code": "PSYC 1C1000*", "department": "Psychology"},
        ]
        new, rewrote = canonicalize_courses(courses, "shasta")
        assert new[0]["department"] == "Independent Study"
        assert new[1]["department"] == "Psychology"
        assert rewrote == 1


# ── 4. Cross-college human-readable invariant (the CI gate) ──────────────


class TestHumanReadableInvariant:
    """For every onboarded college, every prefix in its enriched courses
    must resolve through the mapping to a human-readable name. This is the
    regression gate: any new college or catalog update that introduces a
    prefix without adding a mapping entry fails here."""

    @pytest.mark.parametrize("college", ONBOARDED_COLLEGES)
    def test_every_prefix_resolves(self, college: str) -> None:
        enriched_path = CACHE_DIR / f"{college}_enriched.json"
        if not enriched_path.exists():
            pytest.skip(f"no enriched file for {college}")
        courses = json.loads(enriched_path.read_text())
        missing = resolve_unknown_prefixes(courses, college)
        assert missing == {}, (
            f"{college}: {len(missing)} prefix(es) have no mapping entry:\n"
            + "\n".join(f"  {p!r} ({n} courses)" for p, n in missing.items())
        )

    @pytest.mark.parametrize("college", ONBOARDED_COLLEGES)
    def test_every_resolved_name_is_human_readable(self, college: str) -> None:
        """Every value in the resolved mapping must satisfy the display
        invariants: not bare code, no parenthesized code suffix, ≥3 chars.
        The resolver enforces this at load time, so this test is a
        redundant shield — useful to have when the resolver itself is the
        thing being refactored."""
        import re as _re

        m = resolve(college)
        paren_re = _re.compile(r"\s*\([A-Z][A-Z ]{1,7}\)\s*$")
        for prefix, name in m.items():
            assert name, f"{college}/{prefix}: empty name"
            assert name != prefix, (
                f"{college}/{prefix}: name equals bare code {name!r}"
            )
            assert len(name) >= 3, (
                f"{college}/{prefix}: name too short {name!r}"
            )
            assert not paren_re.search(name), (
                f"{college}/{prefix}: name has parenthesized code suffix {name!r}"
            )


# ── 5. Base + overlay file sanity ────────────────────────────────────────


class TestLiveMappingFiles:
    """Guardrails on the committed files themselves, independent of any
    particular college's courses."""

    def test_base_loads(self) -> None:
        base = _load_mapping_file(BASE_PATH)
        assert base, "base.json is empty"
        # Spot-check a few values we expect to be present and correct
        assert base["MATH"] == "Mathematics"
        assert base["ENGL"] == "English"
        assert base["STAT"] == "Statistics"

    def test_all_overlay_files_load(self) -> None:
        for overlay in OVERLAY_DIR.glob("*.json"):
            # Will raise InvalidMappingError if any invariant fails
            got = _load_mapping_file(overlay)
            assert got, f"{overlay.name} has no prefix entries"
