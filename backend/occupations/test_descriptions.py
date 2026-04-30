"""Unit tests for occupations/descriptions.py — SOC 2018 definition lookup.

descriptions.py serves the authoritative BLS SOC 2018 definitions out
of the bundled O*NET Occupation Data file. These tests pin the contract:
known SOCs resolve to the BLS definition, unknown SOCs return None, and
the loader correctly prefers the .00 row over O*NET specialty rows.

Coverage:
  - Known SOCs (Compliance Officers, Locomotive Engineers, RNs) resolve
    to BLS-faithful definitions, with regression assertions against the
    pre-refactor drift modes (HR-flavored compliance text; engineering-
    discipline locomotive text)
  - Unknown SOCs and empty input return None
  - Loader indexes the full BLS detailed code set (~867 codes) and
    returns non-empty descriptions for every entry
"""

from occupations.descriptions import (
    _load_soc_descriptions,
    get_description,
)


class TestKnownSocResolves:
    def test_compliance_officers_match_bls_definition(self):
        desc = get_description("13-1041")
        assert desc is not None
        assert "compliance" in desc.lower()
        # The hand-curated dictionary's pre-refactor bug shipped HR-flavored
        # text on this SOC; the BLS definition is regulatory enforcement.
        assert "benefit" not in desc.lower()
        assert "compensation" not in desc.lower()

    def test_locomotive_engineers_describe_train_driving_not_engineering(self):
        # The regex fallback's pre-refactor bug treated this title as a
        # discipline of engineering. BLS describes it as operating trains.
        desc = get_description("53-4011")
        assert desc is not None
        assert "locomotive" in desc.lower()
        assert "engineering principles" not in desc.lower()

    def test_registered_nurses_resolves(self):
        desc = get_description("29-1141")
        assert desc is not None
        assert "patient" in desc.lower() or "nurs" in desc.lower()


class TestUnknownSocReturnsNone:
    def test_made_up_soc_returns_none(self):
        assert get_description("99-9999") is None

    def test_empty_string_returns_none(self):
        assert get_description("") is None


class TestLoaderShape:
    def test_loader_indexes_full_set_of_socs(self):
        descriptions = _load_soc_descriptions()
        # Sanity floor: BLS SOC 2018 has ~867 detailed codes; O*NET ships
        # the same set on its .00 rows. If this drops, the file may have
        # been truncated.
        assert len(descriptions) >= 800

    def test_every_loaded_description_is_non_empty(self):
        for soc, desc in _load_soc_descriptions().items():
            assert desc, f"SOC {soc} has empty description"
            assert len(desc) > 20, f"SOC {soc} has implausibly short description: {desc!r}"
