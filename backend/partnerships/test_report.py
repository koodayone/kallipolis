"""Unit tests for partnerships.report — the report's evaluation seams, rendered from a hand-built lens.

The renderer needs no graph: `LensModel` and its parts are plain dataclasses, the alignment
roster is a monkeypatched `view_roster`, and competencies come from the spec. No network,
no LLM.

Coverage:
  - the demand table adds median hourly (annual over 2,080) and a signed distance from the living wage for a single college, keeps the salary column otherwise, and shows dashes for a missing wage
  - the living wage is the college's own county; districts, consortia and an unmapped college get none
  - the demand caption names the basis, county and source only when a living wage is shown
  - the wage chart's living-wage rule sits inside a grown axis; its words and figure sit in the legend, and a short figure tag rides the rule only where the curves clear it
  - the wage section states what the dashed line is only when a living wage is drawn
  - the awards chart's openings label names the region
  - Sources merges the O*NET summaries into the Curriculum Alignment group when the grid is dropped, numbers outline lines after the links, and links the MIT county page only with a living wage
  - a certificate-column roster drops the competency grid from the report; a college-column roster keeps it
  - a program not yet offered: the TOP–CIP–SOC chain figure names the codes, titles and the umbrella SOC and carries no
    links or `xwrap` class; the crosswalk funnel is byte-identical to its pinned hash; Awards Offered renders the announced
    credential when the Curriculum Inventory has none; statewide supply draws no openings rule and drops "Regional";
    Sources add the chain group and cite the detailed code's O*NET summary; two colleges' certificate columns are prefixed
    with the college
  - a posting found on an employer's own careers site carries the site under its title and the section's intro names it;
    postings from the default feed alone render the intro and rows exactly as before
  - an authored employer note renders under the postings table only when set
"""

import re

import pytest

from ontology.living_wage import living_wage
from partnerships import alignment as A
from partnerships.alignment import Cell, Evidence, Plate, Row
from partnerships.lens import LensModel, LensOccupation, LensProgram, LensScope, LensSlice, LensWage, MemberRef, Play
from partnerships.report import (_ACCENTS, CompetencyColumn, LivePosting, ReportSpec, _awards_demand_svg, _awards_offered_section,
                                 _chain_data, _chain_svg, _crosswalk_svg, _demand_provenance, _demand_table, _employer_intro,
                                 _employer_table, _hourly, _living_wage_for, _onet_code, _sources_section, _vs,
                                 _wage_outcomes_svg, _wage_section, build_report_html)

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


def _tag(svg, tag="$79,040"):
    m = re.search(r'<text x="([\d.]+)" y="([\d.]+)"[^>]*text-anchor="(start|end)"[^>]*>' + re.escape(tag) + "</text>", svg)
    return (float(m.group(1)), float(m.group(2)), m.group(3)) if m else None


def _rule_y(svg):
    return float(re.search(r'<line x1="\d+" y1="([\d.]+)"[^>]*stroke-dasharray="7 4"', svg).group(1))


def test_wage_rule_tag_sits_only_where_the_curves_clear_it():
    lw = 38.0 * 2080
    rising = [LensWage("Degree", 30000, 60000, 90000, 100, "2015-16 to 2019-20")]
    svg = _wage_outcomes_svg(rising, "121000", lw, "LW")
    x, y, anchor = _tag(svg)
    assert anchor == "start" and y < _rule_y(svg)                    # curves start far below the rule → left, above
    assert "LW \u00b7 $79,040" in svg and 'stroke-dasharray="4 3"' in svg   # the words and the figure in the legend
    falling = [LensWage("Degree", 90000, 60000, 30000, 100, "w")]
    assert _tag(_wage_outcomes_svg(falling, "121000", lw, "LW"))[2] == "end"
    high = [LensWage("Degree", 100000, 120000, 140000, 100, "w")]
    svg = _wage_outcomes_svg(high, "121000", lw, "LW")
    assert _tag(svg)[1] > _rule_y(svg)                                # curves above the rule → tag beneath it
    flat = [LensWage("Degree", 79040, 79040, 79040, 100, "w"), LensWage("Certificate", 76000, 82000, 76000, 50, "w")]
    svg = _wage_outcomes_svg(flat, "121000", lw, "LW")
    assert _tag(svg) is None and "LW \u00b7 $79,040" in svg          # no clear spot: no tag on the rule, legend still says it
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


# ── a program not yet offered ─────────────────────────────────────────────────────
def test_chain_figure_names_codes_titles_and_umbrella_without_links():
    d = _chain_data("121200", ["29-2099.01"])
    assert d["top"] == ("121200", "Electro-Neurodiagnostic Technology") and [c for c, _ in d["cips"]] == ["51.0903"]
    assert d["socs"] == [("29-2099.01", "Neurodiagnostic Technologists")] and d["umbrellas"] == {0: ("29-2099", "Health Technologists and Technicians, All Other")}
    assert d["edges"] == [(0, 0)] and d["derived"]
    svg = _chain_svg(d["top"], d["cips"], d["socs"], d["edges"], d["umbrellas"])
    for s_ in ("TOP 1212.00", "CIP 51.0903", "SOC 29-2099.01", "Neurodiagnostic", ">SOC 29-2099<", 'class="chainfig"', "stroke-dasharray"):
        assert s_ in svg, s_
    assert "<a" not in svg and "xwrap" not in svg and "CCCCO" not in svg and "NCES" not in svg   # the caption names the authorities
    assert "Electroencephalographic" in svg and "Electroneurodiagnostic/" in svg      # the CIP title wraps at its slashes
    plain = _chain_svg(d["top"], d["cips"], [("29-2099", "Health Technologists and Technicians, All Other")], [(0, 0)], {})
    assert "stroke-dasharray" not in plain and plain.count(">SOC 29-2099<") == 1     # the node's own label; no frame tag
    assert svg.count("marker-end") == 2 and svg.count(" C ") == 2                     # one-to-one-to-one: two even curves
    assert _onet_code("29-2099.01") == "29-2099.01" and _onet_code("29-2099") == "29-2099.00"


def test_chain_shapes_across_the_evaluations():
    """The five shapes the 09-17 evaluations take, from the ontology."""
    conv = _chain_data("126100", ["21-1094"])                       # two CIPs converge on one occupation
    assert [c for c, _ in conv["cips"]] == ["51.1504", "51.2208"] and conv["edges"] == [(0, 0), (1, 0)]
    fan = _chain_data("010210", ["29-2056", "31-9096"])            # one CIP fans out to two
    assert [c for c, _ in fan["cips"]] == ["01.8301"] and fan["edges"] == [(0, 0), (0, 1)]
    many = _chain_data("010900", ["37-3012", "37-1012"])           # many to many
    assert len(many["cips"]) == 4 and (0, 0) in many["edges"] and (0, 1) in many["edges"] and many["derived"]
    authored = _chain_data("094500", ["51-9141", "17-3026", "17-3024"])
    assert authored["authored"] == [0] and not authored["derived"]  # 51-9141 is reached by no CIP: a stated-purpose bypass
    svg = _chain_svg(many["top"], many["cips"], many["socs"], many["edges"], {})
    assert svg.count("<rect") == 1 + 4 + 2 and svg.count("marker-end") == 4 + len(many["edges"])
    assert _ACCENTS[0] in svg and _ACCENTS[1] in svg                # each occupation its own accent
    bypass = _chain_svg(authored["top"], authored["cips"], authored["socs"], authored["edges"], {}, authored["authored"])
    assert bypass.count("stroke-dasharray") == 1 and "stated purpose" in bypass


def test_chain_section_draws_for_true_and_names_an_authored_destination(monkeypatch):
    monkeypatch.setattr("partnerships.report._living_wage_for", lambda lens: None)
    base = dict(org_name="F", org_short="R", lede="l", program_top="126100", crosswalk_chain=True)
    lens = _lens(occs=[_occ("21-1094", "Community Health Workers", 60000, 200)])
    html = build_report_html("foothill", Play(id="x", title="CHW", sector="health", socs=("21-1094",)), ReportSpec(**base), lens=lens)
    assert "<h1>TOP–CIP–SOC Crosswalk</h1>" in html and "CIP 51.1504" in html and "TOP–CIP–SOC Crosswalk Section" in html
    assert html.index("TOP–CIP–SOC Crosswalk</h1>") < html.index("Regional Occupational Demand</h1>")
    lens2 = _lens(occs=[_occ("51-9141", "Semiconductor Processing Technicians", 60000, 200), _occ("17-3026", "IET", 70000, 100)])
    html2 = build_report_html("foothill", Play(id="y", title="SP", sector="adm", socs=("51-9141", "17-3026")),
                              ReportSpec(**{**base, "program_top": "094500"}), lens=lens2)
    assert "<h1>TOP–CIP–SOC Crosswalk</h1>" in html2 and "SOC 51-9141 is the program’s stated purpose; the crosswalk does not reach it." in html2
    assert "to SOC 17-3026 in the" in html2 and "to SOC 51-9141" not in html2          # the NCES clause names only the crosswalk's destinations


def test_crosswalk_funnel_is_unchanged():
    import hashlib
    prog = LensProgram("Foothill College", "010210", "Veterinary Technology", True, ["29-2056"], {"2021": 10}, {"Fall 2021": 40}, {})
    svg = _crosswalk_svg([prog], [_occ()])
    assert hashlib.sha256(svg.encode()).hexdigest() == "8a7b15d9fc20a226b3ea3e17512bb6a65d5df9be1472aaf8469401ce6600bd20"


def test_awards_offered_renders_the_announced_credential_when_coci_has_none():
    planned = ({"title": "Neurodiagnostic Technology", "credential": "Associate in Science", "units": "Program map to be published"},)
    html = _awards_offered_section("Foothill College", "121200", planned)
    assert "<h1>Awards Offered</h1>" in html and 'class="lc1"' in html and "Associate in Science" in html
    assert "lists no approved award under TOP 121200 at Foothill College" in html
    assert _awards_offered_section("Foothill College", "121200") == ""                  # no announced award: nothing, as before


def _prog(college, awards):
    return LensProgram(college, "121200", "Electro-Neurodiagnostic Technology", False, ["29-2099"], awards, {},
                       {"associate degree": awards})


def test_statewide_supply_draws_no_rule_and_drops_regional(monkeypatch):
    monkeypatch.setattr("partnerships.report._living_wage_for", lambda lens: None)
    progs = [_prog("Orange Coast College", {"2021": 11, "2022": 16}), _prog("San Diego Mesa College", {"2021": 0, "2022": 28})]
    occ = _occ("29-2099", "Health Technologists and Technicians, All Other", 69710, 530)
    lens = _lens(occs=[occ], programs=progs)
    base = dict(org_name="Foothill College Program Evaluation", org_short="Regional", lede="l", program_top="121200",
                programs=(("Orange Coast College", "121200"), ("San Diego Mesa College", "121200")))
    play = Play(id="x", title="Neurodiagnostic Technology", sector="health", socs=("29-2099",))
    statewide = build_report_html("foothill", play, ReportSpec(**base, supply_scope="statewide"), lens=lens)
    regional = build_report_html("foothill", play, ReportSpec(**base), lens=lens)
    assert "openings a year" not in statewide and ">Annual Awards<" in statewide and "Regional Program Enrollment" not in statewide
    assert "530 openings a year" in regional and "Annual Awards vs. Annual Openings" in regional
    # comparators standing alone keep their own colours in the awards bands; the regional form keeps the neutral ramp
    assert 'fill="#c2410c"' in statewide and 'fill="#c2410c"' not in regional


def test_sources_add_the_chain_group_and_cite_the_detailed_code():
    html = _sources_section("Foothill College", "Health", "https://d", "Neurodiagnostic Technology", ["29-2099.01"], "121200",
                            chain=["29-2099.01"])
    assert "TOP–CIP–SOC Crosswalk Section" in html and "NCES CIP 2020 – SOC 2018 Crosswalk" in html and "TOP Code Manual" in html
    assert "link/summary/29-2099.01" in html and "29-2099.00" not in html
    assert "TOP–CIP–SOC Crosswalk Section" not in _sources_section("F", "H", "https://d", "T", ["29-2099"], "121200")


def test_two_colleges_certificate_columns_are_prefixed_with_the_college():
    from partnerships.alignment_plate import _col_label, column_legend
    def plate(college, key, cert):
        return Plate(college, key, cert, "credit", "121200", "Electro-Neurodiagnostic Technology", "29-2099.01",
                     "Neurodiagnostic Technologists", ["29-2099"], "", [], [], [], short_title="Neurodiagnostic Technology")
    a = plate("Orange Coast College", "orangecoast", "Associate in Science Degree, Neurodiagnostic Technology")
    b = plate("San Diego Mesa College", "sdmesa", "Associate of Science Degree, Neurodiagnostic Technology")
    assert _col_label(a, "certificate") == "Neurodiagnostic Technology"
    assert _col_label(a, "certificate", multi=True).startswith("Orange Coast ·")
    legend = column_legend([a, b], "certificate")
    assert "Orange Coast · Neurodiagnostic Technology" in legend and "San Diego Mesa · Neurodiagnostic Technology" in legend


def test_postings_from_an_employers_own_site_are_marked_and_named():
    default = {"29-2099": [LivePosting("Kaiser Permanente", "Neurodiagnostic Technician II", "https://c1/k")]}
    mixed = {"29-2099": [LivePosting("UCSF Health", "EEG Technologist, Night Shift", "https://careers.ucsf.edu/x/2958", "careers.ucsf.edu"),
                         LivePosting("Kaiser Permanente", "Neurodiagnostic Technician II", "https://c1/k")]}
    occ = [_occ("29-2099", "Health Technologists and Technicians, All Other", 69710, 530)]
    assert _employer_intro(default) == ("Live job postings from prominent regional employers, listed on CareerOneStop "
                                        "(U.S. Department of Labor).")
    assert "own careers site (careers.ucsf.edu)" in _employer_intro(mixed)
    plain, marked = _employer_table(occ, default), _employer_table(occ, mixed)
    assert "lsrc" not in plain
    assert marked.count('class="lsrc"') == 1 and ">careers.ucsf.edu</span>" in marked and 'rowspan="2"' in marked


def test_employer_note_renders_under_the_table_only_when_set(monkeypatch):
    monkeypatch.setattr("partnerships.report._living_wage_for", lambda lens: None)
    lens = _lens(occs=[_occ("29-2099", "Health Technologists and Technicians, All Other", 69710, 530)])
    play = Play(id="x", title="Neurodiagnostic Technology", sector="health", socs=("29-2099",))
    base = dict(org_name="F", org_short="R", lede="l")
    with_ = build_report_html("foothill", play, ReportSpec(**base, employer_note="UCSF Health is the founding partner. [According to UCSF](https://u/x), it funds it."), lens=lens)
    without = build_report_html("foothill", play, ReportSpec(**base), lens=lens)
    i, j = with_.index('<table class="live">'), with_.index("founding partner")
    assert i < j and 'href="https://u/x"' in with_ and "founding partner" not in without
