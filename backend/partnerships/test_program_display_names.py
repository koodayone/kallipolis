"""Unit tests for partnerships/program_display_names.json — the curated program cache.

Guards the hand-curated layer the report renders on top of the graph: the college's own
program name, its catalog URL, and the unit counts shown in "Awards Offered". These are
transcribed from college catalogs by a human (or a model reading one), so unlike the
graph they have no upstream validation — these tests are it.

The rule that motivated the file: a unit figure means one of two different things and
they cannot be rendered alike. A Certificate of Achievement IS its core-and-support
sequence, so its number is the whole award ("basis": "award"). A degree's catalog figure
is MAJOR coursework only, with general education on top ("basis": "major"). Foothill's
Environmental Horticulture major is 64 quarter units under a degree that requires 90, and
the report printed "64 quarter units" against "associate degree" — false. It survived
review because the other two degrees have majors of 93 and 100, which clear the 90-unit
minimum on their own and so looked indistinguishable from a correct total.

Coverage:
  - every entry carries the name, url and confidence the renderer expects
  - award_units entries are {units, basis} with a basis the renderer understands
  - a degree total below its credential's minimum MUST be marked as a part, not a whole
  - every figure records the credential tier, so the guard cannot be fooled by a
    programme name that does not contain the word "degree"
  - certificate figures are positive and calendars are ones we can label
"""
import json
from pathlib import Path

import pytest

CACHE = Path(__file__).resolve().parent / "program_display_names.json"

#: Minimum units for a whole degree, by credential and calendar. Associate: Title 5
#: §55063, 60 semester units. Baccalaureate: 120 semester units, of which a CCC upper
#: division programme is only the top slice. A figure below its minimum CANNOT be the
#: award's total — it is a part of the award, and must say which part.
DEGREE_MINIMUM = {
    "associate degree": {"semester": 60, "quarter": 90},
    "baccalaureate": {"semester": 120, "quarter": 180},
}
#: What a cached figure MEASURES.
#:   award    the whole award — a Certificate of Achievement IS its course sequence
#:   major    degree coursework, with general education on top
#:   program  a completion programme's own units, over a prerequisite degree AND a GE
#:            pattern (Foothill's Respiratory Care B.S.: 68 on top of an associate)
BASES = {"major", "award", "program"}
#: Calendars we can label a unit figure with. Anything else and the renderer
#: cannot say "quarter units", leaving a bare number beside DataMart's
#: semester-normalised labels meaning something different.
CALENDARS = {"semester", "quarter"}


def _names():
    return json.loads(CACHE.read_text())["names"]


def test_cache_loads_and_is_keyed_by_college_and_top():
    n = _names()
    assert n, "cache is empty"
    for k in n:
        college, _, top6 = k.partition("|")
        assert college and top6.isdigit() and len(top6) == 6, f"malformed key {k!r}"


def test_every_entry_has_what_the_renderer_reads():
    for k, v in _names().items():
        assert v.get("name"), f"{k}: no display name"
        assert v.get("url", "").startswith("http"), f"{k}: no catalog url"
        assert v.get("confidence") in {"high", "medium", "low"}, f"{k}: bad confidence"


def test_award_units_carry_a_basis_the_renderer_understands():
    """{units, basis}. A bare number is the pre-basis shape the renderer still tolerates,
    but nothing new should be added that way — the basis is the whole point."""
    for k, v in _names().items():
        for title, u in (v.get("award_units") or {}).items():
            assert isinstance(u, dict), f"{k}/{title}: award_units must be {{units, basis}}"
            assert isinstance(u.get("units"), (int, float)) and u["units"] > 0, \
                f"{k}/{title}: units must be a positive number"
            assert u.get("basis") in BASES, f"{k}/{title}: basis must be one of {BASES}"
            assert u.get("tier"), f"{k}/{title}: no credential tier recorded"


def test_entries_with_units_declare_a_calendar():
    """Without it the renderer cannot say "quarter units", and an unqualified number
    sits beside DataMart's semester-normalised award labels meaning something else."""
    for k, v in _names().items():
        if v.get("award_units"):
            assert v.get("calendar") in CALENDARS, \
                f"{k}: award_units present but calendar is {v.get('calendar')!r}"


@pytest.mark.parametrize("key,title,u", [
    (k, t, u)
    for k, v in _names().items()
    for t, u in (v.get("award_units") or {}).items()
    if isinstance(u, dict)
])
def test_a_degree_total_clears_the_degree_minimum(key, title, u):
    """A figure marked as the award's own total must actually be one.

    TWO REGRESSIONS, same class. Environmental Horticulture's associate degree carried
    64 as an "award" total under a 90-unit minimum. The Respiratory Care baccalaureate
    carried 68 as an "award" total when the catalog also requires a GE pattern and a
    prerequisite associate degree — a bachelor's is 180 quarter units, not 68. Any degree
    total below its minimum is a PART of the award wearing the label of the whole.

    Keys on the recorded TIER, not the programme name. A first version asked whether the
    title contained "degree" — and "Environmental Horticulture & Design" does not, so the
    guard sailed straight past the one row it existed to catch.
    """
    if u["basis"] != "award" or u["tier"] not in DEGREE_MINIMUM:
        return
    v = _names()[key]
    minimum = DEGREE_MINIMUM[u["tier"]][v["calendar"]]
    assert u["units"] >= minimum, (
        f"{key}/{title}: {u['units']} is below the {v['calendar']} {u['tier']} minimum "
        f"({minimum}) — mark it basis='major'/'program' or correct the figure")


def test_the_baccalaureate_is_a_completion_programme_not_a_whole_degree():
    """68 units is the programme, over a prerequisite associate degree and a GE pattern."""
    u = _names()["Foothill College|121000"]["award_units"]["Respiratory Care"]
    assert u["tier"] == "baccalaureate" and u["units"] == 68
    assert u["basis"] == "program", "68 is not a whole bachelor's degree"


def test_the_environmental_horticulture_case_stays_fixed():
    """The specific row that was wrong, pinned so it cannot regress silently."""
    au = _names()["Foothill College|010900"]["award_units"]
    deg = au["Environmental Horticulture & Design"]
    cert = au["Environmental Horticulture and Design"]
    assert deg["units"] == 64 and deg["basis"] == "major", \
        "the degree figure is major coursework; the degree itself needs 90 quarter units"
    assert cert["units"] == 64 and cert["basis"] == "award", \
        "a Certificate of Achievement IS the core-and-support sequence — 64 is its total"
