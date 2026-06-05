"""Unit test for the SVAMP Programs-lens aggregation invariant.

The Programs lens anchors on supply (program-owned, additive across colleges)
and shows demand only as a per-SOC relationship (occupation-owned, regional,
never summed across the SOCs a program feeds). These tests pin that on the pure
assembly functions, with no graph or filesystem I/O.

Coverage:
  - Landscape: awards_total summed across colleges; latest-year only (not older)
  - Landscape: coverage matrix keys on activity — per-(college, TOP) enrolled +
    latest-year awards (covered = both, partial = one, gap = neither), with a
    cell present for every member college and an awards-only program (no tagged
    course / no enrollment) still reading partial rather than vanishing
  - Report: each crosswalk SOC's demand taken once (not summed across SOCs, not
    multiplied by college count)
  - Report: awards series are per-college and additive to the consortium total
  - Report: targeted (college, TOP) slice yields one series + sets `college`,
    and stays gap-less (program axis owns no gap)
  - Report: no gap / per-program demand field exists
  - Report: all five colleges present in curriculum (dimmed-empty handled client-side)
  - Enrollment terms exclude summer
  - Occupation (aggregated dual): gap = openings − consortium supply (occupation
    axis owns the gap); occupation-grain wage; feeding TOPs summed per college;
    a multi-SOC feeding TOP counts in full (never split across SOCs)
"""

from partnerships.svamp import SVAMP_COLLEGES
from partnerships.svamp_programs import (
    _assemble_landscape,
    _assemble_program_report,
    _assemble_occupation,
)


def test_landscape_awards_total_summed_across_colleges_latest_year_only():
    land = _assemble_landscape(
        region="Bay", region_display="Bay Area",
        universe={"095600": {"49-9041"}},
        titles={"095600": "Manufacturing and Industrial Technology"},
        awards_rows=[
            {"college": "De Anza College", "top6": "095600", "year": "2024-2025", "awards": 10},
            {"college": "Ohlone College", "top6": "095600", "year": "2024-2025", "awards": 5},
            {"college": "De Anza College", "top6": "095600", "year": "2023-2024", "awards": 99},
        ],
        enroll_rows=[],
        coverage_rows=[
            {"college": "De Anza College", "top6": "095600", "n": 3},
            {"college": "Ohlone College", "top6": "095600", "n": 2},
        ],
    )
    t = land.tops[0]
    assert t.awards_total == 15          # 10 + 5 latest year (not the older 99)
    assert t.soc_count == 1              # crosswalk cardinality, not demand
    assert t.n_colleges_offering == 2    # derived from coverage_rows


def test_landscape_coverage_matrix_keys_on_activity_per_cell():
    # Activity, not catalog: De Anza enrolled + conferring → covered; Ohlone
    # enrolled, no awards → partial; Foothill confers but no enrollment (the
    # 095630-style awards-only case) → partial, NOT gap; the rest → gap. Every
    # member college gets a cell.
    land = _assemble_landscape(
        region="Bay", region_display="Bay Area",
        universe={"095600": {"49-9041"}},
        titles={"095600": "Manufacturing and Industrial Technology"},
        awards_rows=[
            {"college": "De Anza College", "top6": "095600", "year": "2024-2025", "awards": 10},
            {"college": "Foothill College", "top6": "095600", "year": "2024-2025", "awards": 7},
        ],
        enroll_rows=[
            {"college": "De Anza College", "top6": "095600", "term": "Fall 2024", "count": 50},
            {"college": "Ohlone College", "top6": "095600", "term": "Fall 2024", "count": 30},
        ],
        coverage_rows=[
            {"college": "De Anza College", "top6": "095600", "n": 3},
            {"college": "Ohlone College", "top6": "095600", "n": 2},
        ],
    )
    cells = {(c.college, c.top6): c for c in land.matrix.cells}
    assert len(land.matrix.cells) == len(SVAMP_COLLEGES)   # one cell per college
    deanza = cells[("De Anza College", "095600")]
    assert (deanza.enrolled, deanza.awards > 0) == (True, True)    # covered
    ohlone = cells[("Ohlone College", "095600")]
    assert (ohlone.enrolled, ohlone.awards > 0) == (True, False)   # partial (enroll only)
    foothill = cells[("Foothill College", "095600")]
    assert (foothill.enrolled, foothill.awards > 0) == (False, True)  # partial (awards only)
    mission = cells[("Mission College", "095600")]
    assert (mission.enrolled, mission.awards > 0) == (False, False)   # gap


def _report():
    return _assemble_program_report(
        top6="095600", name="Manufacturing", region="Bay", region_display="Bay Area",
        demand_rows=[
            {"soc_code": "49-9041", "title": "Industrial Machinery Mechanics",
             "annual_openings": 550, "annual_wage": 60000},
            {"soc_code": "51-4041", "title": "Machinists",
             "annual_openings": 510, "annual_wage": 58000},
        ],
        awards_rows=[
            {"college": "De Anza College", "year": "2024-2025", "awards": 10},
            {"college": "Ohlone College", "year": "2024-2025", "awards": 5},
        ],
        enroll_rows=[
            {"college": "De Anza College", "term": "Fall 2024", "count": 100},
            {"college": "De Anza College", "term": "Summer 2024", "count": 5},
        ],
        course_rows=[],
        wage_fn=lambda t: [],
    )


def test_report_demand_per_soc_not_summed_or_multiplied():
    rep = _report()
    # One row per crosswalk SOC, each carrying the single regional openings —
    # never summed across SOCs, never multiplied by college count.
    assert {o.soc_code: o.annual_openings for o in rep.occupations} == {
        "49-9041": 550, "51-4041": 510}


def test_report_awards_series_are_per_college_and_additive():
    rep = _report()
    totals = {s.college: sum(v or 0 for v in s.vals) for s in rep.awards_by_college}
    assert totals == {"De Anza College": 10, "Ohlone College": 5}  # sums to consortium total 15


def test_report_has_no_gap_or_demand_aggregate_field():
    rep = _report()
    assert not hasattr(rep, "gap")
    assert not hasattr(rep, "demand_total")


def test_report_lists_all_colleges_in_curriculum():
    rep = _report()
    assert [c.college for c in rep.curriculum_by_college] == SVAMP_COLLEGES


def test_report_enrollment_terms_exclude_summer():
    rep = _report()
    assert "Fall 2024" in rep.enrollment_terms
    assert "Summer 2024" not in rep.enrollment_terms


def test_targeted_report_single_college_slice():
    # college set ⇒ the (college, TOP) slice: one series, `college` populated,
    # demand unchanged (regional, per-SOC), and still gap-less.
    rep = _assemble_program_report(
        top6="095600", name="Manufacturing", region="Bay", region_display="Bay Area",
        demand_rows=[
            {"soc_code": "49-9041", "title": "Industrial Machinery Mechanics",
             "annual_openings": 550, "annual_wage": 60000},
        ],
        awards_rows=[{"college": "De Anza College", "year": "2024-2025", "awards": 10}],
        enroll_rows=[{"college": "De Anza College", "term": "Fall 2024", "count": 100}],
        course_rows=[],
        wage_fn=lambda t: [],
        college="De Anza College",
    )
    assert rep.college == "De Anza College"
    assert [s.college for s in rep.awards_by_college] == ["De Anza College"]
    assert {o.soc_code: o.annual_openings for o in rep.occupations} == {"49-9041": 550}
    assert not hasattr(rep, "gap")   # program axis stays gap-less even when targeted


def test_occupation_gap_wage_and_feeding_supply():
    # The aggregated-occupation dual: gap = openings − consortium supply, an
    # occupation-grain wage, feeding TOPs summed per college, and a feeding TOP
    # that serves multiple SOCs counted in full (never split across SOCs).
    rep = _assemble_occupation(
        soc="17-3027", title="Mechanical Engineering Technologists",
        description="Apply theory and principles of mechanical engineering.",
        region="Bay", region_display="Bay Area",
        annual_openings=300, annual_wage=72000, growth_rate=0.05, employment=15000,
        consortium_supply=120.0,
        feeding=["094800", "095600"],
        universe={"094800": {"17-3027", "17-3029"}, "095600": {"17-3027", "49-9041"}},
        titles={"094800": "Automotive Technology", "095600": "Manufacturing"},
        awards_rows=[
            {"college": "De Anza College", "top6": "094800", "year": "2024-2025", "awards": 200},
            {"college": "De Anza College", "top6": "095600", "year": "2024-2025", "awards": 20},
            {"college": "Ohlone College", "top6": "095600", "year": "2024-2025", "awards": 30},
        ],
        enroll_rows=[],
        course_rows=[
            {"college": "De Anza College", "top6": "094800", "code": "AUTO1",
             "name": "Intro", "description": "", "learning_outcomes": [], "top_code": "094800"},
        ],
        crosswalk={"tops": [], "cips": [], "n_taught": 0, "n_total": 0, "coverage_pct": 0.0},
    )
    assert rep.gap == 180                  # 300 openings − 120 supply (occupation owns the gap)
    assert rep.annual_wage == 72000        # occupation-grain wage, not a program aggregate
    assert rep.employment == 15000         # regional current employment carried through
    fmap = {t.top6: t for t in rep.feeding_tops}
    assert set(fmap) == {"094800", "095600"}      # both 09 feeding TOPs
    assert fmap["094800"].awards_total == 200
    assert fmap["095600"].awards_total == 50      # 20 + 30 across colleges
    assert fmap["094800"].soc_count == 2          # serves >1 SOC; counted in full, not split
    aby = {s.college: sum(v or 0 for v in s.vals) for s in rep.awards_by_college}
    assert aby == {"De Anza College": 220, "Ohlone College": 30}   # Σ over feeding TOPs per college
