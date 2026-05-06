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
    _load_mcf_index,
    _normalize_course_code,
    _normalize_mcf_course_id,
    _strip_numeric_padding,
    _strip_punctuation,
    lookup_top6_per_course,
)
from ontology.supply import _normalize_college


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
        # Compton MCF uses hyphens ("ACR-20") which the punctuation
        # stripper handles upstream; this helper itself leaves the
        # hyphen alone (it would no-op since the pattern requires
        # alpha-prefix-then-digits).
        assert _strip_numeric_padding("ACR-20") == "ACR-20"


class TestStripPunctuation:
    """The hyphen / asterisk / footnote-marker cleanup. Catches MCF
    convention drift (Compton 'ACR-20', Shasta 'ENGL-129') and
    catalog-scrape artifacts ('ENGL C1000*', 'MATH 1A†')."""

    def test_strips_hyphens_in_mcf_separator_drift(self):
        assert _strip_punctuation("ENGL-129") == "ENGL129"
        assert _strip_punctuation("ACR-20") == "ACR20"
        assert _strip_punctuation("ANTH-5") == "ANTH5"

    def test_strips_asterisk_catalog_scrape_artifact(self):
        assert _strip_punctuation("ENGLC1000*") == "ENGLC1000"

    def test_strips_obscure_footnote_markers(self):
        # Daggers and section markers occasionally appear in PDFs.
        assert _strip_punctuation("MATH1A†") == "MATH1A"
        assert _strip_punctuation("HIST20§") == "HIST20"

    def test_passes_clean_codes_through(self):
        assert _strip_punctuation("CS1A") == "CS1A"
        assert _strip_punctuation("ATHL004") == "ATHL004"

    def test_round_trips_via_full_normalizer_strips_then_pads(self):
        # The catalog-scrape miss "ENGL-129" (Shasta MCF) and the
        # catalog form "ENGL 129" must converge.
        assert _normalize_course_code("ENGL 129") == _normalize_mcf_course_id("ENGL-129")


class TestCollegeNameNormalization:
    """Symmetry between the MCF index builder and the lookup path.

    The lookup applies `_normalize_college` (which strips " College",
    " Community College", and "College of [the] " from a Neo4j-style
    display name) and lowercases the result. Before the fix that
    landed alongside this test, the index builder kept the raw MCF
    "College" column lowercased without applying the same suffix
    stripping. Five of 125 MCF files carry the " College" suffix in
    that column (Reedley, Allan Hancock, etc.), so for those colleges
    every lookup queried "<key>" while the index held "<key> college"
    — every match failed and Stage 2 aborted at the 80% TOP6 coverage
    floor with 0/N courses tagged.
    """

    def test_normalize_college_strips_college_suffix(self):
        # The contract that the MCF index builder relies on.
        assert _normalize_college("Reedley College") == "Reedley"
        assert _normalize_college("Foothill College") == "Foothill"

    def test_normalize_college_idempotent_on_unsuffixed(self):
        # Most MCF files use the bare form already; the normalizer must
        # leave them unchanged so index keys agree across both shapes.
        assert _normalize_college("Foothill") == "Foothill"
        assert _normalize_college("Reedley") == "Reedley"

    def test_normalize_college_strips_periods(self):
        # Catalog-side names sometimes carry a period after abbreviated
        # words ("Mt. San Antonio College") while the MCF College column
        # writes them without ("Mt San Antonio"). Without period
        # stripping, _normalize_college's index-vs-lookup symmetry
        # breaks for those colleges and Stage 2 aborts at 0% TOP6
        # coverage on the load gate.
        assert _normalize_college("Mt. San Antonio College") == "Mt San Antonio"
        assert _normalize_college("Mt. San Antonio") == "Mt San Antonio"
        # Idempotent on already-stripped form.
        assert _normalize_college("Mt San Antonio") == "Mt San Antonio"

    def test_normalize_college_collapses_double_spaces(self):
        # Period stripping can leave behind double spaces if the period
        # was preceded and followed by spaces. The normalizer should
        # collapse them to single spaces so the resulting key shape is
        # consistent.
        assert _normalize_college("Foo .  Bar College") == "Foo Bar"

    def test_index_lookup_succeeds_for_period_college(self):
        # Regression: lookup_top6_per_course("Mt. San Antonio College")
        # returned None for every mtsac course because the index had
        # keys like ("ACCS33", "mt san antonio") while the lookup
        # queried ("ACCS33", "mt. san antonio"). ACCS33 is a real entry
        # in MasterCourseFile_mt_san_antonio.csv with TOP6 493032; the
        # assertion is that the lookup now finds it.
        result = lookup_top6_per_course(["ACCS 33"], "Mt. San Antonio College")
        assert result.get("ACCS 33") == "493032"

    def test_index_lookup_succeeds_for_suffixed_college(self):
        # Regression: the bug was that `lookup_top6_per_course("Reedley
        # College")` returned None for every Reedley course because the
        # index had keys like ("ACCTG19", "reedley college") while the
        # lookup queried ("ACCTG19", "reedley"). ACCTG19 is a real entry
        # in MasterCourseFile_reedley_college.csv with TOP6 050200
        # (Accounting); the assertion is that the lookup now finds it.
        result = lookup_top6_per_course(["ACCTG 19"], "Reedley College")
        assert result.get("ACCTG 19") == "050200"

    def test_index_uses_normalized_college_keys(self):
        # Direct check on the index keys themselves: reedley entries
        # must be under "reedley", not "reedley college". A non-zero
        # count under the normalized key is the simplest invariant
        # that prevents this bug from recurring.
        idx = _load_mcf_index()
        reedley_entries = sum(1 for (_, col) in idx if col == "reedley")
        suffixed_entries = sum(1 for (_, col) in idx if col == "reedley college")
        assert reedley_entries > 100, (
            f"expected >100 reedley index entries under canonical key, "
            f"got {reedley_entries}"
        )
        assert suffixed_entries == 0, (
            f"index still has {suffixed_entries} entries under unstripped "
            f"'reedley college' key — _load_mcf_index regressed"
        )
