"""Unit test for the SVAMP Programs-lens aggregation invariant.

The Programs lens anchors on supply (program-owned, additive across colleges)
and shows demand only as a per-SOC relationship (occupation-owned, regional,
never summed across the SOCs a program feeds). These tests pin that on the pure
assembly functions, with no graph or filesystem I/O.

Coverage:
  - Landscape: projected_supply is THE supply measure — awards over the passed
    award-year window ÷ window length, summed across colleges (the same supply
    definition as the occupation landscape and the MCP); years outside the window
    are excluded, and a zero year still counts toward the divisor
  - Landscape: total_supply is that projection over the whole feeder universe,
    rounded once (never a re-sum of the per-TOP tiles)
  - Landscape: coverage matrix keys on activity — per-(college, TOP) enrolled +
    projected>0 (covered = both, partial = one, gap = neither), with a cell present
    for every member college and a supplying-only program (no tagged course / no
    enrollment) still reading partial rather than vanishing
  - Report: each crosswalk SOC's demand taken once (not summed across SOCs, not
    multiplied by college count)
  - Report: awards series are per-college and additive to the consortium total
  - Report: awards_by_type decomposes each college's flat series by credential
    type (types sum back to the college total per year), ordered by credential
    weight (degrees → certificates large-to-small → noncredit); rows without an
    award_type yield no decomposition (pre-split callers)
  - Report: enrollment_by_credit decomposes each college's flat enrollment by
    credit family (families sum back to the college total per term — the flat
    line is ALL instructional activity, credit + noncredit), in fixed family
    order (degree-applicable → not-degree-applicable → Non-Credit), with None
    where a family doesn't report a term; rows without a credit_type yield no
    decomposition
  - Report: targeted (college, TOP) slice yields one series + sets `college`,
    and stays gap-less (program axis owns no gap)
  - Report: no gap / per-program demand field exists
  - Report: all five colleges present in curriculum (dimmed-empty handled client-side)
  - Enrollment terms exclude summer
  - Enrollment terms exclude the export-boundary terms (Fall 2020 / Winter
    2026) that only one of the two course-section exports covers
  - Occupation (aggregated dual): gap = openings − consortium supply (occupation
    axis owns the gap); occupation-grain wage; feeding TOPs summed per college;
    a multi-SOC feeding TOP counts in full (never split across SOCs)
"""

from partnerships.landscape_build import SVAMP_COLLEGES
from partnerships.landscape_programs import (
    _assemble_landscape,
    _assemble_program_report,
    _assemble_occupation,
    _consortium_supply,
    _crosswalk_taught_scope,
)


# ── Institutional-sum + per-college scope helpers ───────────────────────────
# These pin the two halves of the occupation report's college-scoping that an
# earlier draft got wrong: the member-summed supply (whose hand-rolled loop
# shadowed the `college` scope argument) and the consortium-vs-single-college
# crosswalk decision. Pure, so they need no graph — the coverage the
# generalized engine relies on in place of an end-to-end snapshot.

def test_consortium_supply_sums_over_every_member():
    # Injected supply_fn returns a per-college amount; the helper sums them.
    supply = {"A": 4.0, "B": 1.5, "C": 2.5}
    total = _consortium_supply(
        ["095600"], ["A", "B", "C"],
        supply_fn=lambda feeding, college: ([], supply[college]),
    )
    assert total == 8.0


def test_consortium_supply_is_zero_when_no_feeding_tops():
    # No feeding TOPs ⇒ no supply, and supply_fn is never called.
    called = []
    total = _consortium_supply(
        [], ["A", "B"],
        supply_fn=lambda feeding, college: called.append(college) or ([], 1.0),
    )
    assert total == 0.0 and called == []


def test_crosswalk_taught_scope_consortium_union_vs_single_college():
    colleges = ["De Anza College", "Ohlone College", "Mission College"]
    # No college ⇒ consortium union over every member (taught-college empty).
    assert _crosswalk_taught_scope(None, colleges) == ("", colleges)
    # A college ⇒ that college's single-college branch (no union list).
    assert _crosswalk_taught_scope("Ohlone College", colleges) == ("Ohlone College", None)


def test_landscape_projected_supply_over_window():
    # projected_supply = in-window awards ((10 + 5) + 99 = 114) ÷ 3 window years =
    # 38.0; the older 2019-2020 (1000) is outside the window and excluded; a zero
    # year (2022-2023) still counts toward the divisor of 3.
    land = _assemble_landscape(
        region="Bay", region_display="Bay Area",
        universe={"095600": {"49-9041"}},
        titles={"095600": "Manufacturing and Industrial Technology"},
        awards_rows=[
            {"college": "De Anza College", "top6": "095600", "year": "2024-2025", "awards": 10},
            {"college": "Ohlone College", "top6": "095600", "year": "2024-2025", "awards": 5},
            {"college": "De Anza College", "top6": "095600", "year": "2023-2024", "awards": 99},
            {"college": "De Anza College", "top6": "095600", "year": "2019-2020", "awards": 1000},
        ],
        enroll_rows=[],
        award_years=("2024-2025", "2023-2024", "2022-2023"),
    )
    t = land.tops[0]
    assert t.projected_supply == 38.0    # (15 + 99) / 3 window years; older 1000 excluded
    assert land.total_supply == 38.0     # headline = one round over the feeder universe
    assert t.soc_count == 1              # crosswalk cardinality, not demand


def test_landscape_coverage_matrix_keys_on_activity_per_cell():
    # Activity, not catalog: De Anza enrolled + supplying → covered; Ohlone
    # enrolled, no supply → partial; Foothill supplies but no enrollment (the
    # 095630-style supply-only case) → partial, NOT gap; the rest → gap. Every
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
        award_years=("2024-2025", "2023-2024", "2022-2023"),
    )
    cells = {(c.college, c.top6): c for c in land.matrix.cells}
    assert len(land.matrix.cells) == len(SVAMP_COLLEGES)   # one cell per college
    deanza = cells[("De Anza College", "095600")]
    assert (deanza.enrolled, deanza.projected > 0) == (True, True)    # covered
    ohlone = cells[("Ohlone College", "095600")]
    assert (ohlone.enrolled, ohlone.projected > 0) == (True, False)   # partial (enroll only)
    foothill = cells[("Foothill College", "095600")]
    assert (foothill.enrolled, foothill.projected > 0) == (False, True)  # partial (supply only)
    mission = cells[("Mission College", "095600")]
    assert (mission.enrolled, mission.projected > 0) == (False, False)   # gap


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


def test_report_awards_by_type_decomposes_college_series():
    # Per-(college, year, award_type) rows: the flat per-college series sums the
    # types back out, and awards_by_type carries the decomposition aligned to
    # the same award_years axis, in credential-weight order (degree first, then
    # certificates largest band first).
    rep = _assemble_program_report(
        top6="095630", name="Machining", region="Bay", region_display="Bay Area",
        demand_rows=[],
        awards_rows=[
            {"college": "De Anza College", "year": "2023-2024",
             "award_type": "Certificate requiring 8 to fewer than 16 semester units", "awards": 24},
            {"college": "De Anza College", "year": "2024-2025",
             "award_type": "Certificate requiring 8 to fewer than 16 semester units", "awards": 35},
            {"college": "De Anza College", "year": "2024-2025",
             "award_type": "Certificate requiring 30 to < 60 semester units", "awards": 6},
            {"college": "De Anza College", "year": "2024-2025",
             "award_type": "Associate of Science (A.S.) degree", "awards": 8},
        ],
        enroll_rows=[],
        course_rows=[],
        wage_fn=lambda t: [],
    )
    assert rep.award_years == ["2023-2024", "2024-2025"]
    # Flat series sums the types: 2023-24 = 24, 2024-25 = 35 + 6 + 8 = 49.
    assert [s.vals for s in rep.awards_by_college] == [[24, 49]]
    # Decomposition in credential-weight order, aligned to award_years (a type
    # absent in a year ⇒ 0).
    assert [(s.award_type, s.vals) for s in rep.awards_by_type] == [
        ("Associate of Science (A.S.) degree", [0, 8]),
        ("Certificate requiring 30 to < 60 semester units", [0, 6]),
        ("Certificate requiring 8 to fewer than 16 semester units", [24, 35]),
    ]
    # Every type series carries its college (single-college fixture).
    assert {s.college for s in rep.awards_by_type} == {"De Anza College"}


def test_report_awards_rows_without_type_yield_no_decomposition():
    # Pre-split rows (no award_type / credit_type keys) still produce the flat
    # per-college series; the decompositions are simply empty.
    rep = _report()
    assert rep.awards_by_type == []
    assert rep.enrollment_by_credit == []
    assert {s.college: sum(v or 0 for v in s.vals) for s in rep.awards_by_college} == {
        "De Anza College": 10, "Ohlone College": 5}


def test_report_enrollment_by_credit_decomposes_college_series():
    # The Ohlone 095600 crossover shape: per-(college, term, credit_type) rows.
    # The flat series sums the families (credit + noncredit = all instructional
    # activity); the decomposition aligns to enrollment_terms in fixed family
    # order, None where a family doesn't report a term; summer stays excluded.
    rep = _assemble_program_report(
        top6="095600", name="Manufacturing", region="Bay", region_display="Bay Area",
        demand_rows=[],
        awards_rows=[],
        enroll_rows=[
            {"college": "Ohlone College", "term": "Spring 2025",
             "credit_type": "Credit - Degree Applicable", "count": 223},
            {"college": "Ohlone College", "term": "Fall 2025",
             "credit_type": "Credit - Degree Applicable", "count": 195},
            {"college": "Ohlone College", "term": "Fall 2025",
             "credit_type": "Non-Credit", "count": 200},
            {"college": "Ohlone College", "term": "Summer 2025",
             "credit_type": "Non-Credit", "count": 60},
        ],
        course_rows=[],
        wage_fn=lambda t: [],
    )
    assert rep.enrollment_terms == ["Spring 2025", "Fall 2025"]   # summer excluded
    # Flat = families summed: Spring 223, Fall 195 + 200 = 395.
    assert [s.vals for s in rep.enrollment_by_college] == [[223, 395]]
    # Decomposition in fixed family order, None where a family has no term.
    assert [(s.credit_type, s.vals) for s in rep.enrollment_by_credit] == [
        ("Credit - Degree Applicable", [223, 195]),
        ("Non-Credit", [None, 200]),
    ]
    assert {s.college for s in rep.enrollment_by_credit} == {"Ohlone College"}


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


def test_report_enrollment_terms_exclude_export_boundary_terms():
    # Fall 2020 / Winter 2026 are covered by only ONE of the two DataMart
    # course-section exports (the noncredit pull runs wider than the credit
    # one), so the blended total is structurally incomplete there — those
    # terms stay off the axis until the narrower export is re-pulled.
    rep = _assemble_program_report(
        top6="095600", name="Manufacturing", region="Bay", region_display="Bay Area",
        demand_rows=[], awards_rows=[],
        enroll_rows=[
            {"college": "De Anza College", "term": "Fall 2020",
             "credit_type": "Non-Credit", "count": 107},
            {"college": "De Anza College", "term": "Fall 2021",
             "credit_type": "Non-Credit", "count": 323},
            {"college": "De Anza College", "term": "Winter 2026",
             "credit_type": "Non-Credit", "count": 50},
        ],
        course_rows=[], wage_fn=lambda t: [],
    )
    assert rep.enrollment_terms == ["Fall 2021"]
    assert [s.vals for s in rep.enrollment_by_college] == [[323]]
    assert [s.vals for s in rep.enrollment_by_credit] == [[323]]


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
        award_years=("2024-2025", "2023-2024", "2022-2023"),
    )
    assert rep.gap == 180                  # 300 openings − 120 supply (occupation owns the gap)
    assert rep.annual_wage == 72000        # occupation-grain wage, not a program aggregate
    assert rep.employment == 15000         # regional current employment carried through
    fmap = {t.top6: t for t in rep.feeding_tops}
    assert set(fmap) == {"094800", "095600"}      # both 09 feeding TOPs
    assert fmap["094800"].projected_supply == 66.7  # 200 / 3 window years (projected)
    assert fmap["095600"].projected_supply == 16.7  # (20 + 30) / 3 across colleges (projected)
    assert fmap["094800"].soc_count == 2          # serves >1 SOC; counted in full, not split
    aby = {s.college: sum(v or 0 for v in s.vals) for s in rep.awards_by_college}
    assert aby == {"De Anza College": 220, "Ohlone College": 30}   # Σ over feeding TOPs per college
