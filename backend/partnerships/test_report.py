"""Unit tests for partnerships.report — the report's evaluation seams, rendered from a hand-built lens.

The renderer needs no graph: `LensModel` and its parts are plain dataclasses, the alignment
roster is a monkeypatched `view_roster`, and competencies come from the spec. No network,
no LLM.

Coverage:
  - the demand table adds median hourly (annual over 2,080) and a signed distance from the living wage for a single college, keeps the salary column otherwise, and shows dashes for a missing wage
  - the living wage is the college's own county; districts, consortia and an unmapped college get none
  - the demand caption names the basis, county and source only when a living wage is shown
  - the wage chart's living-wage rule sits inside a grown axis and its label goes to the end where the curves clear it, above or below as space allows
  - the wage section states what the dashed line is only when a living wage is drawn
  - the awards chart's openings label names the region
  - Sources merges the O*NET summaries into the Curriculum Alignment group when the grid is dropped, numbers outline lines after the links, and links the MIT county page only with a living wage
  - a certificate-column roster drops the competency grid from the report; a college-column roster keeps it
"""

import re

import pytest

from ontology.living_wage import living_wage
from partnerships import alignment as A
from partnerships.alignment import Cell, Evidence, Plate, Row
from partnerships.lens import LensModel, LensOccupation, LensProgram, LensScope, LensSlice, LensWage, MemberRef, Play
from partnerships.report import (CompetencyColumn, ReportSpec, _awards_demand_svg, _demand_provenance, _demand_table,
                                 _hourly, _living_wage_for, _sources_section, _vs, _wage_outcomes_svg, _wage_section,
                                 build_report_html)

SC = living_wage("Santa Clara")


def _occ(soc="29-2056", title="Veterinary Technologists and Technicians", wage=61280, openings=310):
    return LensOccupation(soc, title, "Performs procedures.", "Bay", openings, wage, 0.127, [], True, [])


def _lens(kind="college", name="Foothill College", occs=None, wages=None, programs=None):
    return LensModel(LensScope(MemberRef("foothill", name, kind), ("Bay",), LensSlice("play", "p", "P"), ()),
                     occs or [_occ()], programs=programs or [], award_years=["2021", "2022"], wages=wages or {})


def test_demand_table_hourly_and_distance_columns():
    t = _demand_table([_occ(), _occ("17-3026", "IET", 79950, 150), _occ("99-0000", "No wage", 0, 5)], SC)
    assert t.count("<th") == 6 and "Median hourly" in t and "vs. living wage" in t
    assert "$29.46" in t and "−$8.54" in t and "$38.44" in t and "+$0.44" in t
    assert t.count('<td class="n">—</td>') >= 5                       # the no-wage row and the total row show dashes
    plain = _demand_table([_occ(), _occ("99-0000", "No wage", 0, 5)])
    assert plain.count("<th") == 5 and "$61,280" in plain and "Median salary" in plain and "living" not in plain
    assert _hourly(61280) == pytest.approx(29.4615, abs=1e-3) and _vs(38.0, 38.0) == "+$0.00" and _vs(29.46, 38.0)[0] == "−"


def test_living_wage_is_the_colleges_county_only():
    assert _living_wage_for(_lens()).county == "Santa Clara County"
    assert _living_wage_for(_lens(kind="district", name="Foothill-De Anza CCD")) is None
    assert _living_wage_for(_lens(kind="consortium", name="SVAMP")) is None
    assert _living_wage_for(_lens(name="Nowhere College")) is None


def test_demand_caption_names_basis_county_and_source_only_with_a_living_wage():
    with_ = _demand_provenance(_lens(), SC)
    assert "Bay Area region" in with_ and "divided by 2,080 hours" in with_
    assert "one adult with no children in Santa Clara County" in with_ and SC.url in with_ and SC.vintage in with_
    assert "MIT" not in _demand_provenance(_lens())


def _svg_label(svg, label):
    m = re.search(r'<text x="([\d.]+)" y="([\d.]+)"[^>]*text-anchor="(start|end)"[^>]*>' + re.escape(label) + "</text>", svg)
    assert m, svg[-600:]
    return float(m.group(1)), float(m.group(2)), m.group(3)


def _rule_y(svg):
    return float(re.search(r'<line x1="\d+" y1="([\d.]+)"[^>]*stroke-dasharray="7 4"', svg).group(1))


def test_wage_rule_label_sits_where_the_curves_clear_it():
    lw = 38.0 * 2080
    rising = [LensWage("Degree", 30000, 60000, 90000, 100, "2015-16 to 2019-20")]
    svg = _wage_outcomes_svg(rising, "121000", lw, "LW")
    x, y, anchor = _svg_label(svg, "LW")
    assert anchor == "start" and y < _rule_y(svg)                    # curves start far below the rule → left, above
    falling = [LensWage("Degree", 90000, 60000, 30000, 100, "w")]
    x, y, anchor = _svg_label(_wage_outcomes_svg(falling, "121000", lw, "LW"), "LW")
    assert anchor == "end"                                             # the right end has the room
    high = [LensWage("Degree", 100000, 120000, 140000, 100, "w")]
    svg = _wage_outcomes_svg(high, "121000", lw, "LW")
    x, y, anchor = _svg_label(svg, "LW")
    assert y > _rule_y(svg)                                            # curves above the rule → label beneath it
    low = [LensWage("Degree", 20000, 25000, 30000, 100, "w")]
    svg = _wage_outcomes_svg(low, "121000", lw, "LW")
    assert "$100,000" in svg and _rule_y(svg) > 18                     # the axis grows to hold the rule inside the plot


def test_wage_section_states_the_dashed_line_only_with_a_living_wage():
    wages = {"121000": [LensWage("Certificate", 30000, 60000, 90000, 12, "2015-16 to 2019-20")]}
    spec = ReportSpec("O", "o", "l", program_top="121000")
    with_ = _wage_section(_lens(wages=wages), spec, SC)
    assert "The dashed line represents the annualized living wage" in with_ and "Santa Clara County" in with_ and "2015-16 to 2019-20" in with_
    assert "dashed" not in _wage_section(_lens(wages=wages), spec)
    assert _wage_section(_lens(), spec) == ""


def test_awards_rule_names_the_region():
    prog = LensProgram("Foothill College", "121000", "RT", True, ["29-1126"], {"2021": 10, "2022": 12}, {}, {"t": {"2021": 10, "2022": 12}})
    svg = _awards_demand_svg([prog], ["2021", "2022"], 410, region="Bay Area")
    assert "410 openings a year, Bay Area" in svg
    assert "410 openings a year<" in _awards_demand_svg([prog], ["2021", "2022"], 410)


def test_sources_merge_summaries_when_consolidated_and_number_outlines_after_links():
    out = _sources_section("Org", "Sec", "http://d", "T", ["51-9141"], "094500", curriculum=True,
                           outlines=["<b>Foothill</b> · Cert: x"], consolidated=True, living=SC)
    assert "Occupational Competencies Section" not in out
    assert out.index("Curriculum Alignment Section") < out.index("O*NET Summary of 51-9141") < out.index("College Program Alignment")
    assert "(4) Course outlines of record" in out and "MIT Living Wage Calculator — Santa Clara County" in out
    plain = _sources_section("Org", "Sec", "http://d", "T", ["51-9141"], "094500", curriculum=True, outlines=["x"])
    assert "Occupational Competencies Section" in plain and "(3) Course outlines of record" in plain and "MIT" not in plain


def _plate():
    rows = [Row("d1", "Diagnose equipment malfunctions.", "t", {"C 1": Cell(2, [Evidence("C 1", "outcomes", 2, "q", "b")])})]
    return Plate("Foothill College", "foothill", "Cert", "credit", "094500", "Mfg", "51-9141", "Semiconductor Processing Technicians",
                 [], "", [{"code": "C 1", "title": "Course", "source_url": "https://x/c1"}], [], rows, role="paired", short_title="Cert")


def test_a_certificate_roster_drops_the_grid_and_a_college_roster_keeps_it(monkeypatch):
    spec = ReportSpec("Org", "o", "lede", program_top="094500", curriculum_alignment="r",
                      competencies=[CompetencyColumn("51-9141", "Assesses.", ["K"], ["S"], ["A"], ["T"])])
    play = Play("p", "T", "adm", ("51-9141",))
    occ = _occ("51-9141", "Semiconductor Processing Technicians", 49340, 180)
    def roster(columns):
        return lambda rid: ({"id": rid, "columns": columns, "occupations": ["51-9141"], "top_n": 10,
                             "programs": [{"program": "foothill-x", "paired_soc": "51-9141"}]}, [_plate()])
    monkeypatch.setattr(A, "view_roster", roster("certificate"))
    html = build_report_html("foothill", play, spec, lens=_lens(occs=[occ]))
    assert "<h1>Occupational Competencies</h1>" not in html and '<table class="cmpgrid"' not in html
    assert '<p class="alg-desc">' in html and "Assesses." in html and "Occupational Competencies Section" not in html
    monkeypatch.setattr(A, "view_roster", roster("college"))
    html = build_report_html("foothill", play, spec, lens=_lens(occs=[occ]))
    assert "<h1>Occupational Competencies</h1>" in html and '<table class="cmpgrid"' in html and '<p class="alg-desc">' not in html
