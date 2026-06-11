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
