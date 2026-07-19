"""Unit test for the SVAMP aggregation invariant.

The point of aggregating is that two pillars are regional (demand, employers)
and two are institutional (supply, students). Getting that wrong — e.g.
summing regional demand across colleges, or summing per-cell employer counts —
silently inflates the headline numbers. These tests pin the invariant on the
pure assembly function, with no graph or filesystem I/O.

Coverage:
  - Regional demand counted once, never multiplied by the college count
  - Supply summed across the member colleges (institutional)
  - Employer union passed through verbatim, never summed across cells
  - Consortium gap = regional demand total − combined supply total
  - Every college lists all SVAMP SOCs, including gap (untaught) rows
  - Per-SOC regional demand identical across all colleges
  - occupations_taught counts distinct SOCs with ≥1 aligned college
  - Cell coverage keys on feeding-program activity (enrolled + feeding_awards),
    not the course pipeline — an awards-only feeding program (the 095630 →
    Machinists seam) reads partial, not gap
  - Director's-mandate TOP exclusions (automotive, HVAC) fail is_svamp_top —
    out of the program universe everywhere it gates — while core AM programs
    and Industrial Systems (094500, not to be confused with HVAC 094600) stay in
"""

from partnerships.landscape_build import (
    SVAMP_COLLEGES,
    SVAMP_SOCS,
    SVAMP_MANDATE_EXCLUDED_TOPS,
    _assemble_landscape,
    is_svamp_top,
)
from partnerships.landscape import LandscapeSpec
from partnerships.sectors import SectorRule


def _demand_by_soc():
    # Distinct regional demand per SOC (shared by all colleges).
    return {soc: {"title": f"Occ {soc}", "annual_openings": 100 + i * 10}
            for i, soc in enumerate(SVAMP_SOCS)}


def _align_all_colleges_teach_first_soc():
    # Every college teaches only the first SOC, each routing through one TOP6.
    first = SVAMP_SOCS[0]
    return {c: {first: {"course_count": 3, "top_codes": ["010100"]}}
            for c in SVAMP_COLLEGES}


def _fake_supply(tops, college):
    # A college contributes 10.0 supply over any non-empty feeder set, 0 when it
    # runs no feeder for the SOC — mirrors supply_fn_graph's empty-tops → 0.0.
    return [], (10.0 if tops else 0.0)


def _build():
    return _assemble_landscape(
        region="Bay",
        region_display="Bay Area",
        demand_by_soc=_demand_by_soc(),
        align_by_college=_align_all_colleges_teach_first_soc(),
        candidate_employers=224,  # already-deduped regional union
        supply_fn=_fake_supply,
        soc_feeding={SVAMP_SOCS[0]: {"010100"}},  # every college feeds the first SOC
    )


def test_regional_demand_counted_once_not_per_college():
    land = _build()
    demand_once = sum(100 + i * 10 for i in range(len(SVAMP_SOCS)))
    assert land.aggregate.regional_demand_total == demand_once
    # The bug this guards against: multiplying by the 5 colleges.
    assert land.aggregate.regional_demand_total != demand_once * len(SVAMP_COLLEGES)


def test_supply_summed_across_colleges():
    land = _build()
    # Supply over the DEDUPED feeder union ({010100}) summed across 5 colleges at
    # 10.0 each -> 50.0 — never a per-cell sum (which would double-count a shared feeder).
    assert land.aggregate.combined_supply_total == 50.0


def test_employers_passed_through_not_summed():
    land = _build()
    # The regional union count is used verbatim, not multiplied/summed.
    assert land.aggregate.candidate_employers == 224


def test_consortium_gap_is_demand_minus_combined_supply():
    land = _build()
    agg = land.aggregate
    assert agg.gap == round(agg.regional_demand_total - agg.combined_supply_total)


def test_every_college_has_all_socs_including_gap_rows():
    land = _build()
    assert len(land.colleges) == len(SVAMP_COLLEGES)
    for col in land.colleges:
        assert [c.soc_code for c in col.cells] == SVAMP_SOCS
        # Untaught SOCs surface as gap rows: zero supply, gap == regional demand.
        for cell in col.cells:
            if cell.course_count == 0:
                assert cell.supply == 0.0
                assert cell.gap == (cell.annual_openings or 0)


def test_demand_identical_across_colleges_per_soc():
    land = _build()
    for i, soc in enumerate(SVAMP_SOCS):
        openings = {next(c.annual_openings for c in col.cells if c.soc_code == soc)
                    for col in land.colleges}
        assert openings == {100 + i * 10}


def test_occupations_taught_counts_distinct_aligned_socs():
    land = _build()
    # Only the first SOC has a producing feeder (supply > 0) -> 1 distinct taught occ.
    assert land.aggregate.occupations_taught == 1


def test_cell_coverage_keys_on_feeding_activity_not_courses():
    # A SOC fed by a 09 program that CONFERS but has no enrollment (the 095630 →
    # Machinists seam) reads partial, not gap — coverage rides feeding-program
    # activity, not the course pipeline. With NO course-routed alignment at all,
    # De Anza still surfaces (awards only → partial); a college with both
    # enrollment and awards on a feeding program reads covered.
    soc = SVAMP_SOCS[0]
    program_data = {
        ("De Anza College", "095630"): {
            "name": "Machining", "awards_by_year": {"2024-2025": 49}, "enroll": {},
        },
        ("Ohlone College", "095630"): {
            "name": "Machining", "awards_by_year": {"2024-2025": 12},
            "enroll": {"Fall 2024": 30},
        },
    }
    land = _assemble_landscape(
        region="Bay", region_display="Bay Area",
        demand_by_soc=_demand_by_soc(),
        align_by_college={c: {} for c in SVAMP_COLLEGES},   # no course-routed alignment
        candidate_employers=0,
        supply_fn=_fake_supply,
        program_data=program_data,
        wage_fn=lambda top6: [],   # routing now builds programs → stub out wage I/O
        soc_feeding={soc: {"095630"}},
    )

    def cell(college):
        col = next(c for c in land.colleges if c.name == college)
        return next(x for x in col.cells if x.soc_code == soc)

    de = cell("De Anza College")
    assert (de.enrolled, de.feeding_awards > 0) == (False, True)   # partial — awards only
    # The cell carries the conferring program even with no tagged course, so the
    # targeted view's program-outcomes panel can surface its awards (the seam fix).
    assert len(de.programs) == 1 and de.awards_recent == 49
    oh = cell("Ohlone College")
    assert (oh.enrolled, oh.feeding_awards > 0) == (True, True)    # covered — both
    fo = cell("Foothill College")
    assert (fo.enrolled, fo.feeding_awards > 0) == (False, False)  # gap — neither
    assert fo.programs == []                                        # nothing to show


def test_mandate_excluded_tops_fail_is_svamp_top():
    # Director's-mandate exclusions: division-09, crosswalk-linked, but their
    # employment flows run to other industry verticals (automotive →
    # dealerships/fleets; HVAC → building trades). is_svamp_top is the single
    # predicate every program-universe surface gates on, so failing here keeps
    # them out of the treemap, coverage, feeding sets, and demand views alike.
    assert SVAMP_MANDATE_EXCLUDED_TOPS == {"094600", "094800"}
    for t in SVAMP_MANDATE_EXCLUDED_TOPS:
        assert not is_svamp_top(t)
    assert is_svamp_top("095630")   # core AM (Machining) stays in
    assert is_svamp_top("094500")   # Industrial Systems — NOT HVAC (094600) — stays in


# ── Priority split: per-cell in_demand stamp + surfaced criteria ──────────────
# A DERIVED spec (rule-bearing, non-authored) engages the demand gate, so each
# cell carries the member-independent in_demand verdict and the landscape surfaces
# the thresholds the split reads on. Synthetic SOCs keep the gate arithmetic pure.

_DERIVED_SOCS = ("11-1111", "22-2222", "33-3333", "44-4444")


def _derived_demand():
    # A clears both gates; B is below the openings floor; C below the wage floor;
    # D is declining but the growth gate was dropped, so D is in demand on openings+wage.
    return {
        "11-1111": {"title": "A", "annual_openings": 800, "annual_wage": 70_000, "growth_rate": 0.04},
        "22-2222": {"title": "B", "annual_openings": 100, "annual_wage": 70_000, "growth_rate": 0.04},
        "33-3333": {"title": "C", "annual_openings": 800, "annual_wage": 40_000, "growth_rate": 0.04},
        "44-4444": {"title": "D", "annual_openings": 800, "annual_wage": 70_000, "growth_rate": -0.02},
    }


def _derived_spec():
    # soc_rule active + default Composition (occupations=None → is_authored False) = a derived spec.
    return LandscapeSpec(
        id="__derived_test__", colleges=("De Anza College", "Foothill College"),
        socs=_DERIVED_SOCS, top_divisions=("09",), excluded_tops=frozenset(),
        sector="Advanced Manufacturing", name="Test", accent="#000000",
        soc_rule=SectorRule(min_openings=239, min_wage=54_081),
    )


def _derived_build():
    spec = _derived_spec()
    return _assemble_landscape(
        region="Bay", region_display="Bay Area",
        demand_by_soc=_derived_demand(),
        align_by_college={c: {} for c in spec.colleges},
        candidate_employers=0,
        supply_fn=_fake_supply,
        soc_feeding={s: set() for s in _DERIVED_SOCS},
        spec=spec,
    )


def test_derived_spec_stamps_in_demand_per_soc():
    land = _derived_build()
    verdict = {c.soc_code: c.in_demand for c in land.colleges[0].cells}
    assert verdict == {"11-1111": True, "22-2222": False, "33-3333": False, "44-4444": True}
    # in_demand is member-independent — identical across every college's cells.
    for col in land.colleges:
        assert {c.soc_code: c.in_demand for c in col.cells} == verdict


def test_derived_spec_surfaces_demand_criteria():
    land = _derived_build()
    assert land.demand_criteria is not None
    assert land.demand_criteria.min_openings == 239
    assert land.demand_criteria.min_wage == 54_081


def test_authored_spec_shows_no_split():
    # The default build is authored (SVAMP's occupations are hand-picked) → every occupation reads as
    # in-demand and no criteria surface, so the dashboard renders no priority split.
    land = _build()
    assert all(c.in_demand for col in land.colleges for c in col.cells)
    assert land.demand_criteria is None
