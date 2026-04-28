"""Unit tests for ontology.mcf_lookup string normalizers.

These two functions are the lookup-key bridge between Neo4j course codes
("CT 100") and the Chancellor's Office Master Course File format
("CT100AB", "ATHL004"). Drift here silently breaks TOP6 resolution for
SWP projects. Both normalizers must agree on the same canonical form
for the (normalized_course_id, college_lower) index lookup to work at
runtime.

Particularly load-bearing: the zero-padding canonicalization. Foothill's
MCF zero-pads numeric portions to three digits ("ATHL004", "ART003L",
"PHED010A"); the catalog scrape produces un-padded form ("ATHL 4",
"ART 3L", "PHED 10A"). Without canonicalization, two-thirds of
Foothill's catalog courses fail to find their MCF entries — the gap
that surfaced as 32% TOP6 coverage versus peers' 95-99%. Both sides
canonicalize to the un-padded form so the lookup succeeds regardless
of which padding convention a college submits its MCF under.

Coverage:
  - _normalize_course_code: space stripping between prefix and number
  - _normalize_course_code: multiletter prefixes and split prefixes
  - _normalize_course_code: alphanumeric suffix preservation
  - _normalize_course_code: case folding and whitespace cleanup
  - _normalize_mcf_course_id: trailing-dot stripping (MCF export quirk)
  - _normalize_mcf_course_id: whitespace and case handling
  - _strip_numeric_padding: leading-zero canonicalization across the
    full range of Foothill MCF shapes (ATHL004, CS001A, PHED010A,
    ART003L) and pass-through on un-padded / non-alpha-prefixed forms
  - Round-trip equivalence between the two normalizers on the same input
  - Round-trip equivalence across the padding-convention divide (catalog
    "ATHL 4" must produce the same key as MCF "ATHL004")
"""

from ontology.mcf_lookup import (
    _normalize_course_code,
    _normalize_mcf_course_id,
    _strip_numeric_padding,
)


class TestNormalizeCourseCode:
    def test_strips_space_between_prefix_and_number(self):
        assert _normalize_course_code("CT 221") == "CT221"

    def test_handles_multiletter_prefix(self):
        assert _normalize_course_code("ARCH 100") == "ARCH100"

    def test_preserves_alphanumeric_suffix(self):
        assert _normalize_course_code("ACCT 101A") == "ACCT101A"

    def test_handles_split_prefix_and_strips_zero_padding(self):
        # "D H 063A" — split prefix plus zero-padded number. Both
        # transformations apply; the canonical form is un-padded "DH63A".
        assert _normalize_course_code("D H 063A") == "DH63A"

    def test_uppercases_input(self):
        assert _normalize_course_code("ct 221") == "CT221"

    def test_collapses_leading_and_trailing_whitespace(self):
        assert _normalize_course_code("  CT 221  ") == "CT221"

    def test_strips_zero_padding_when_present(self):
        # Foothill catalog rarely produces zero-padded codes, but some
        # peer catalogs occasionally do. The normalizer must collapse
        # to the same canonical un-padded form regardless.
        assert _normalize_course_code("ATHL 004") == "ATHL4"


class TestNormalizeMcfCourseId:
    def test_strips_trailing_dot(self):
        # MCF exports sometimes emit "CT221." with a trailing dot.
        assert _normalize_mcf_course_id("CT221.") == "CT221"

    def test_strips_internal_whitespace(self):
        assert _normalize_mcf_course_id("CT 221") == "CT221"

    def test_uppercases_input(self):
        assert _normalize_mcf_course_id("ct221") == "CT221"

    def test_strips_foothill_three_digit_zero_padding(self):
        # The Foothill MCF convention. Catalog-side "ATHL 4" must land
        # on the same key as MCF-side "ATHL004".
        assert _normalize_mcf_course_id("ATHL004") == "ATHL4"

    def test_strips_zero_padding_with_alpha_suffix(self):
        # "ART003L" — three-digit pad with trailing letter.
        assert _normalize_mcf_course_id("ART003L") == "ART3L"

    def test_strips_zero_padding_with_split_prefix(self):
        # "C S 001A" — Foothill MCF's split-prefix + zero-pad form.
        assert _normalize_mcf_course_id("C S 001A") == "CS1A"

    def test_round_trips_with_course_code_normalizer(self):
        # Both functions should produce the same key for the same logical
        # course, which is what makes the (normalized, college) index
        # lookup work.
        assert _normalize_course_code("CT 221") == _normalize_mcf_course_id("CT 221.")

    def test_round_trips_across_padding_divide(self):
        # The single most important contract: a catalog code in
        # un-padded form must produce the same key as the MCF entry
        # in zero-padded form. Without this, Foothill-style MCFs
        # produce systematic misses and partnerships render with empty
        # curriculum evidence under the new TOP-SOC gating.
        assert _normalize_course_code("ATHL 4") == _normalize_mcf_course_id("ATHL004")
        assert _normalize_course_code("PHED 10A") == _normalize_mcf_course_id("PHED010A")
        assert _normalize_course_code("C S 1A") == _normalize_mcf_course_id("C S 001A.")


class TestStripNumericPadding:
    """Direct coverage of the helper. Behavioral spec: when the code
    starts with letters followed by zero-padded digits, strip the
    leading zeros from the digit block; otherwise return unchanged."""

    def test_strips_three_digit_zero_pad(self):
        assert _strip_numeric_padding("ATHL004") == "ATHL4"

    def test_strips_pad_with_alpha_suffix(self):
        assert _strip_numeric_padding("CS001A") == "CS1A"

    def test_passes_unpadded_codes_through(self):
        assert _strip_numeric_padding("CS1A") == "CS1A"
        assert _strip_numeric_padding("MATH101") == "MATH101"

    def test_strips_single_zero_pad(self):
        assert _strip_numeric_padding("PHED010A") == "PHED10A"

    def test_passes_pure_numeric_through(self):
        # San Diego City has all-numeric MCF entries ("055"). No alpha
        # prefix means no zero-pad to strip.
        assert _strip_numeric_padding("055") == "055"

    def test_passes_hyphenated_through(self):
        # Compton MCF uses hyphens ("ACR-20"). Pattern doesn't match,
        # so we leave it alone; Compton's lookup path is unaffected.
        assert _strip_numeric_padding("ACR-20") == "ACR-20"
