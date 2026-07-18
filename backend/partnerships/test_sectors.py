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
  - the full SMCCD sector row in REGISTRY (all 11 sectors published; curated smccd retired)
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
        assert len(SECTORS["ecu"].socs) == 46  # full set; the rule trims it at build

    def test_uniform_priority_job_rule(self):
        # SOC curation is a declarative SectorRule applied UNIFORMLY to every
        # sector — the BACCC/COE "priority job" definition: > 239 regional annual
        # openings (i.e. >= 240), >= $54,081 near-living-wage (> $54,080), a
        # non-empty activity gate (reachable_only is OFF), and >= 2 member colleges
        # — durable across a sector_socs.csv regeneration, not hand-deleted rows.
        # Replaces the earlier ecu-only rule; now ecu and biotech share it.
        from partnerships.landscape import REGISTRY
        for sid in ("ecu", "biotech", "health", "adm"):
            rule = SECTORS[sid].rule
            assert rule.active
            assert rule.min_openings == 239       # keep regional openings > 239 (>= 240)
            assert rule.non_empty_only            # the activity gate (reachable_only is OFF)
            assert rule.min_wage == 54_081        # BACCC near-living-wage floor (> $54,080)
            assert rule.min_colleges == 2
        # Per-sector excluded_tops drop crosswalk-noise feeders. 070810 Computer
        # Networking (IT/CIS) is a noise feeder for ecu.
        assert "070810" in SECTORS["ecu"].excluded_tops
        assert REGISTRY["smccd-ecu"].in_scope("070810") is False
        assert REGISTRY["smccd-ecu"].soc_rule.active

    def test_target_socs_are_middle_skill_anchors(self):
        assert "19-4021" in SECTORS["biotech"].socs   # Biological Technicians
        assert "29-1141" in SECTORS["health"].socs    # Registered Nurses (middle-skill)
        assert "51-4041" in SECTORS["adm"].socs        # Machinists

    def test_total_soc_rows(self):
        # sector_socs.csv is the baccc_sectors categorization of every occupation in
        # the 314 middle-skill universe — so its row count equals the universe (all
        # 314 sectored, 1:1, no orphans). (Was 312: the two "Below Middle Skill"
        # driving occupations the universe keeps but the sector-file skill filter
        # dropped were added back under atl.)
        assert sum(len(v) for v in _load_sector_socs().values()) == 314

    def test_sector_socs_is_the_universe_baccc_join(self):
        # The defensible methodology, pinned: sector_socs.csv == the JOIN of the two
        # COE authorities — every occupation in the middle-skill universe
        # (occupations.json), categorized by its baccc_sectors sector (the committed
        # coe_occupation_sector.csv map). Catches drift; regenerate the file with
        # `python scripts/generate_sector_socs.py`. See scripts/generate_sector_socs.py
        # for the full methodology.
        import csv
        import json
        from pathlib import Path
        base = Path(__file__).resolve().parent
        universe = {o["soc_code"] for o in
                    json.loads((base.parent / "occupations" / "occupations.json").read_text())}
        with (base / "data" / "coe_occupation_sector.csv").open() as f:
            soc_to_sector = {r["soc"]: r["sector_id"] for r in csv.DictReader(f)}
        expected = {(soc_to_sector[s], s) for s in universe}   # each universe occ → its COE sector
        actual = {(sid, s) for sid, socs in _load_sector_socs().items() for s in socs}
        assert actual == expected, (
            "sector_socs.csv diverges from the universe × baccc_sectors join — "
            "run `python scripts/generate_sector_socs.py`")

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
        # SVAMP now runs the UNIVERSAL rule (is_vocational + the active gate) like every other member — no
        # fork. Its curation lives in the Composition (authored 12 occupations + charter), not vocational=False.
        assert REGISTRY["svamp"].vocational is True
        assert REGISTRY["svamp"].composition.is_authored is True

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
        # All 11 SMCCD sector instances are published (the full rail ships).
        assert REGISTRY["smccd-adm"].published is True
        assert REGISTRY["smccd-biotech"].published is True

    def test_in_scope_vocational_vs_division(self):
        from partnerships.landscape import REGISTRY
        bio = REGISTRY["smccd-biotech"]
        assert bio.in_scope("043000") is True   # Biotechnology — vocational
        assert bio.in_scope("040100") is False  # Biology — transfer, excluded
        svamp = REGISTRY["svamp"]
        assert svamp.in_scope("095500") is True   # div 09 CTE
        assert svamp.in_scope("043000") is False  # not div 09
