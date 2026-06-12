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


class TestCatalogRollup:
    def test_college_and_district_rollup(self):
        # Pure rollup over synthetic supply: two AM feeders + one biotech feeder.
        from partnerships import members
        cofs, foothill, deanza = "College of San Mateo", "Foothill College", "De Anza College"
        college_tops = {foothill: {"095000"}, deanza: {"095000"}, cofs: {"099999"}}
        sector_candidates = {"adm": {"095000"}, "biotech": {"099999"}}
        entries = registry._rollup_catalog(college_tops, sector_candidates)
        ids = {e["id"] for e in entries}
        # College members feed only the sectors their TOPs intersect.
        assert {"foothill-adm", "deanza-adm"} <= ids
        csm_key = members.college_member(cofs).id
        assert f"{csm_key}-biotech" in ids
        assert f"{csm_key}-adm" not in ids
        # District rolls up: Foothill-De Anza CCD (foothill + deanza) is live for adm.
        assert "foothill-de-anza-ccd-adm" in ids
        # Entries carry the full identity the frontend needs to render a
        # generated instance with no landscapeInstances row.
        e = next(x for x in entries if x["id"] == "foothill-adm")
        assert e["member_kind"] == "college"
        assert e["sector_label"] == "Advanced Manufacturing"
        assert e["region"] == "Bay"
        assert e["colleges"] == ["foothill"]          # college-config id (catalog key)
        assert e["accent"].startswith("#")            # sector accent
        # District entry aggregates its colleges' config ids.
        d = next(x for x in entries if x["id"] == "foothill-de-anza-ccd-adm")
        assert set(d["colleges"]) == {"foothill", "deanza"}
