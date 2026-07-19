"""Instance resolution: pinned vs generated member×sector specs — graph-free.

`spec_for` is the seam the dynamic API route uses to resolve any instance id.
These tests pin the id parsing (hyphenated member ids vs the closed, hyphen-free
sector-id set) and that pinned ids return the exact hand-authored spec while
generated ids compose a correct spec. `has_supply` (the graph-dependent publish
gate) is exercised separately against a live graph, not here.

Coverage:
  - _parse splits "{member}-{sector}" using the sector-id set (hyphenated
    member ids and underscore sector ids both parse)
  - spec_for returns the IDENTICAL pinned spec for a REGISTRY id
  - spec_for composes a generated college×sector spec (id, colleges, sector)
  - spec_for returns None for an unknown member or a missing sector suffix
"""

from partnerships import registry
from partnerships.landscape import REGISTRY


class TestParse:
    def test_simple(self):
        assert registry._parse("foothill-adm") == ("foothill", "adm")

    def test_hyphenated_member(self):
        assert registry._parse("foothill-de-anza-biotech") == ("foothill-de-anza", "biotech")

    def test_underscore_sector(self):
        assert registry._parse("smccd-public_safety") == ("smccd", "public_safety")

    def test_no_sector_suffix(self):
        assert registry._parse("foothill") is None
        assert registry._parse("foothill-notasector") is None


class TestSpecFor:
    def test_pinned_is_identity(self):
        assert registry.spec_for("svamp") is REGISTRY["svamp"]
        assert registry.spec_for("smccd-adm") is REGISTRY["smccd-adm"]

    def test_generated_college_sector(self):
        spec = registry.spec_for("foothill-adm")
        assert spec is not None
        assert spec.id == "foothill-adm"
        assert spec.colleges == ("Foothill College",)
        assert spec.sector == "Advanced Manufacturing"   # SECTORS['adm'].label
        assert spec.vocational is True

    def test_unknown_resolves_none(self):
        assert registry.spec_for("garbage-adm") is None      # unknown member
        assert registry.spec_for("foothill") is None         # no sector suffix


class TestEntry:
    """`_entry` builds the identity the frontend needs to render a generated
    instance with no landscapeInstances row (graph-free). Which (member, sector)
    pairs are LIVE is the route's own `relevant_tops` gate — graph-dependent, so
    exercised against a live graph, not here (see `_live_sectors`)."""

    def test_college_entry_identity(self):
        from partnerships import members
        e = registry._entry(members.college_member("Foothill College"), "adm")
        assert e["id"] == "foothill-adm"
        assert e["member_kind"] == "college"
        assert e["sector_label"] == "Advanced Manufacturing"
        assert e["region"] == "Bay"
        assert e["colleges"] == ["foothill"]          # college-config id (catalog key)
        assert e["accent"].startswith("#")            # sector accent

    def test_district_entry_aggregates_member_colleges(self):
        from partnerships import members
        catalog = members._catalog()
        dname, dcolleges = next(
            (n, c) for n, c in members._district_colleges().items() if len(c) > 1
        )
        e = registry._entry(members.district_member(dname), "adm")
        assert e["member_kind"] == "district"
        # config ids for exactly the member colleges present in the catalog
        assert set(e["colleges"]) == {catalog[c]["key"] for c in dcolleges if c in catalog}
