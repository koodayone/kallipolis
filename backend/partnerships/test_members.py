"""Member catalog + the generalized region resolution — graph-free.

The member is the "who" axis of a `member × sector` landscape. These tests pin
the catalog enumeration and member→colleges resolution against the on-disk
authorities (the college catalog + COLLEGE_COE_REGION), with no graph I/O, and
the `resolve_region → resolve_regions` generalization that lets the engine reach
beyond single-region members.

Coverage:
  - catalog enumeration: all colleges / districts / regions counts
  - multi-college districts resolve their full college set (LACCD 9, SMCCD 3)
  - college member id = the catalog backend key; district id = a slug
  - region member gathers its region's colleges and is single-region
  - the SMCCD reconciliation: catalog "San Mateo CCD" == the pinned member's colleges
  - resolve_regions returns the sorted region set; single for current instances
  - resolve_region stays the |regions|==1 special case (raises on multi-region)
"""

import pytest

from partnerships import members
from partnerships.members import MemberKind
from partnerships.landscape import LandscapeSpec, SVAMP_SPEC, MEMBERS


class TestMemberCatalog:
    def test_catalog_counts(self):
        assert len(members.all_colleges()) == 115          # the committed catalog
        assert len(members.all_districts()) == 72          # CCCCO districts present
        # 9 regions carry colleges (the statewide "CA" rollup is not a member region).
        assert "Bay" in members.all_regions()
        assert "CA" not in members.all_regions()

    def test_college_member_keys_off_catalog_key(self):
        m = members.college_member("Foothill College")
        assert m.kind is MemberKind.COLLEGE
        assert m.id == "foothill"                          # the backend key
        assert m.colleges == ("Foothill College",)
        assert m.regions() == ("Bay",)

    def test_multi_college_district_resolves_full_set(self):
        laccd = members.district_member("Los Angeles CCD")
        assert laccd.kind is MemberKind.DISTRICT
        assert len(laccd.colleges) == 9                    # the nine LACCD colleges
        assert laccd.regions() == ("LA",)

    def test_smccd_reconciliation(self):
        # The catalog spells it "San Mateo CCD"; the pinned MemberSet labels it
        # "San Mateo County CCD". Same three colleges either way — the pinned
        # member keeps its id/label/URLs; the catalog is the generative source.
        d = members.district_member("San Mateo CCD")
        assert d.id == "san-mateo"                          # slug (CCD dropped)
        assert len(d.colleges) == 3
        assert {"College of San Mateo", "Skyline College"} <= set(d.colleges)

    def test_region_member_gathers_region(self):
        bay = members.region_member("Bay")
        assert bay.kind is MemberKind.REGION
        assert bay.regions() == ("Bay",)                    # single by construction
        assert "College of San Mateo" in bay.colleges       # SMCCD
        assert "Foothill College" in bay.colleges           # SVAMP
        assert len(bay.colleges) >= 20

    def test_slug(self):
        assert members._slug("Foothill-De Anza CCD") == "foothill-de-anza"
        assert members._slug("San Jose-Evergreen CCD") == "san-jose-evergreen"


class TestRegionResolution:
    def test_resolve_regions_single_for_current_instances(self):
        assert SVAMP_SPEC.resolve_regions() == ("Bay",)
        assert SVAMP_SPEC.resolve_region() == "Bay"

    def test_resolve_region_raises_on_multi_region_member(self):
        # A spec whose colleges span two COE regions: resolve_regions reports
        # both; resolve_region (the single-region contract) refuses. Colleges are
        # drawn from the region map itself so the names are guaranteed to resolve.
        bay_college = members.region_member("Bay").colleges[0]
        la_college = members.region_member("LA").colleges[0]
        spec = LandscapeSpec(
            id="__multi__",
            colleges=(bay_college, la_college),
            socs=(), top_divisions=(), excluded_tops=frozenset(),
            sector="x", name="x", accent="#000",
        )
        assert spec.resolve_regions() == ("Bay", "LA")
        with pytest.raises(ValueError):
            spec.resolve_region()
