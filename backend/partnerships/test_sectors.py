"""Sector + MemberSet registries — the two axes of a member×sector landscape.

Pins the middle-skill SOC counts (derived from the BACCC sector crosstabs) and
the registry/data consistency so a drifting sector_socs.csv or _SECTOR_META is
caught.

Coverage:
  - SECTORS registry shape (12 industries) and Sector objects (label, accent)
  - per-sector middle-skill SOC counts + known target SOCs (biotech/health/adm)
  - sector_socs.csv <-> _SECTOR_META consistency (no orphan ids on either side)
  - SMCCD MemberSet membership (the three district colleges)
  - landscape_for() composition (id, vocational mode, sector SOCs, draft default)
  - the full SMCCD sector row in REGISTRY (adm published, rest draft; curated smccd retired)
  - in_scope vocational vs division behavior across the registry
"""

from partnerships.sectors import SECTORS, Sector, _load_sector_socs
from partnerships.landscape import MEMBERS, MemberSet


class TestSectorRegistry:
    def test_registry_nonempty(self):
        assert len(SECTORS) == 12  # 13 BACCC sectors minus non_cte_stem (0 mid-skill)

    def test_sectors_are_sector_objects(self):
        for s in SECTORS.values():
            assert isinstance(s, Sector)
            assert s.label and s.accent.startswith("#")

    def test_known_socs_per_sector(self):
        # sector.socs is the FULL generated middle-skill set (the committed CSV);
        # ecu's display set (12) is derived at build time by its SectorRule —
        # see resolve.effective_socs, not enforced here (needs the graph).
        assert len(SECTORS["biotech"].socs) == 7
        assert len(SECTORS["health"].socs) == 40
        assert len(SECTORS["adm"].socs) == 49
        assert len(SECTORS["ecu"].socs) == 46  # full set; rule trims to 12 at build

    def test_ecu_curation_rule(self):
        # The ECU curation lives as a declarative SectorRule (durable across a
        # sector_socs.csv regeneration), not hand-deleted SOC rows.
        from partnerships.landscape import REGISTRY
        rule = SECTORS["ecu"].rule
        assert rule.active
        assert rule.min_openings == 100
        assert rule.reachable_only and rule.non_empty_only
        # 070810 Computer Networking (IT/CIS) — crosswalk artifact, excluded feeder.
        assert "070810" in SECTORS["ecu"].excluded_tops
        assert REGISTRY["smccd-ecu"].in_scope("070810") is False
        # the rule rides onto the instance spec; non-ecu sectors stay no-op.
        assert REGISTRY["smccd-ecu"].soc_rule.active
        assert not SECTORS["biotech"].rule.active

    def test_target_socs_are_middle_skill_anchors(self):
        assert "19-4021" in SECTORS["biotech"].socs   # Biological Technicians
        assert "29-1141" in SECTORS["health"].socs    # Registered Nurses (middle-skill)
        assert "51-4041" in SECTORS["adm"].socs        # Machinists

    def test_total_soc_rows(self):
        # The full generated middle-skill set (no hand-deletions — ecu curation is
        # now a declarative SectorRule applied at build time, not CSV row removal).
        assert sum(len(v) for v in _load_sector_socs().values()) == 312

    def test_registry_and_data_agree(self):
        # Every registered sector has SOCs, and every data sector is registered.
        data_ids = set(_load_sector_socs())
        meta_ids = set(SECTORS)
        assert data_ids == meta_ids
        for sid in meta_ids:
            assert SECTORS[sid].socs, f"{sid} has no SOCs"


class TestMemberSets:
    def test_smccd_members(self):
        m = MEMBERS["smccd"]
        assert isinstance(m, MemberSet)
        assert len(m.colleges) == 3
        assert "Cañada College" in m.colleges
        assert "College of San Mateo" in m.colleges


class TestLandscapeComposition:
    def test_factory_builds_member_x_sector(self):
        from partnerships.landscape import landscape_for
        spec = landscape_for(MEMBERS["smccd"], SECTORS["biotech"])
        assert spec.id == "smccd-biotech"
        assert spec.vocational is True
        assert spec.socs == SECTORS["biotech"].socs
        assert spec.colleges == MEMBERS["smccd"].colleges
        assert spec.accent == SECTORS["biotech"].accent
        assert spec.published is False  # draft by default

    def test_registry_has_sector_instances(self):
        from partnerships.landscape import REGISTRY
        assert REGISTRY["smccd-biotech"].vocational is True
        assert REGISTRY["smccd-health"].vocational is True
        assert REGISTRY["svamp"].vocational is False  # SVAMP stays curated

    def test_full_smccd_sector_row(self):
        from partnerships.landscape import REGISTRY
        expected = {
            f"smccd-{s}" for s in (
                "adm", "biotech", "health", "business", "atl", "public_safety",
                "retail", "ict", "agwet", "edhd", "ecu",
            )
        }
        assert expected <= set(REGISTRY)  # all 11 wired (adm + 10)
        assert "smccd" not in REGISTRY             # curated AM retired; /smccd → /smccd-adm
        assert "smccd-unassigned" not in REGISTRY  # residual catch-all, omitted
        for sid in expected:
            assert REGISTRY[sid].vocational is True
            assert REGISTRY[sid].socs  # non-empty SOC set
        # adm is the published canonical AM surface; the rest are draft.
        assert REGISTRY["smccd-adm"].published is True
        assert REGISTRY["smccd-biotech"].published is False

    def test_in_scope_vocational_vs_division(self):
        from partnerships.landscape import REGISTRY
        bio = REGISTRY["smccd-biotech"]
        assert bio.in_scope("043000") is True   # Biotechnology — vocational
        assert bio.in_scope("040100") is False  # Biology — transfer, excluded
        svamp = REGISTRY["svamp"]
        assert svamp.in_scope("095500") is True   # div 09 CTE
        assert svamp.in_scope("043000") is False  # not div 09
