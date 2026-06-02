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
"""

from partnerships.svamp import (
    SVAMP_COLLEGES,
    SVAMP_SOCS,
    _assemble_landscape,
)


def _demand_by_soc():
    # Distinct regional demand per SOC (shared by all colleges).
    return {soc: {"title": f"Occ {soc}", "annual_openings": 100 + i * 10}
            for i, soc in enumerate(SVAMP_SOCS)}


def _align_all_colleges_teach_first_soc():
    # Every college teaches only the first SOC, each routing through one TOP6.
    first = SVAMP_SOCS[0]
    return {c: {first: {"course_count": 3, "student_count": 40, "top_codes": ["010100"]}}
            for c in SVAMP_COLLEGES}


def _fake_supply(top_codes, college):
    # Each taught (college, SOC) contributes exactly 10.0 of supply.
    return [], 10.0


def _build():
    return _assemble_landscape(
        region="Bay",
        region_display="Bay Area",
        demand_by_soc=_demand_by_soc(),
        align_by_college=_align_all_colleges_teach_first_soc(),
        candidate_employers=224,  # already-deduped regional union
        supply_fn=_fake_supply,
    )


def test_regional_demand_counted_once_not_per_college():
    land = _build()
    demand_once = sum(100 + i * 10 for i in range(len(SVAMP_SOCS)))
    assert land.aggregate.regional_demand_total == demand_once
    # The bug this guards against: multiplying by the 5 colleges.
    assert land.aggregate.regional_demand_total != demand_once * len(SVAMP_COLLEGES)


def test_supply_summed_across_colleges():
    land = _build()
    # 5 colleges each teach 1 SOC at 10.0 supply -> 50.0 combined.
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
    # Only the first SOC is taught (by all colleges) -> 1 distinct taught occ.
    assert land.aggregate.occupations_taught == 1
