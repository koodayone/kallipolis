"""Unit tests for the report's Wage Outcomes section — partnerships/report.py.

Guards the trajectory plate and the label vocabulary behind it. Wage data is the one
figure in a program evaluation that describes PEOPLE rather than counts of things, and
it is also the most easily misread: it is pooled STATEWIDE at TOP6 grain, its cohorts
predate every other vintage in the report, and DataMart reports N/A for some
checkpoints.

Three invariants here are corrections of real failures elsewhere in this codebase:

  - A cohort missing an endpoint must still RENDER. The dashboard's version filters on
    `wage_before != null && wage_after_5 != null`, which silently deletes Community
    Health Worker's 12-recipient local certificate and draws as a complete picture —
    the same class of omission as the enrolment total that dropped a college.
  - The y-axis starts at zero. A track from $28k to $97k on an axis beginning at $20k
    overstates the multiple.
  - The three checkpoints are -2, +2 and +5 years relative to award, so they are NOT
    evenly spaced; drawn uniformly, the second segment reads steeper than it is.

Coverage:
  - recipient-type labels and their credential-weight ordering
  - a full three-point cohort draws a polyline, a dot per checkpoint, and its multiple
  - a single-checkpoint cohort renders (hollow marker, no multiple) and is never dropped
  - the y-axis is zero-based and the x-axis honours the real year offsets
  - no cohort is lost between the CSV and the plate, for all four shipped evaluations
  - the section is evaluations-only and carries the statewide caveat
"""
import re

import pytest

from ontology.programs import get_wage_outcomes
from partnerships.lens import LensWage
from partnerships.report import (_WAGE_CHART, _WAGE_POINTS, _wage_label, _wage_outcomes_svg,
                                 _wage_rank)

#: The four TOPs the shipped program evaluations cover.
EVAL_TOPS = ("121000", "010900", "126100", "010210")


def _rows(top6):
    return [LensWage(w["recipient_type"], w["wage_before"], w["wage_after_2"],
                     w["wage_after_5"], w["n"], w["window"])
            for w in get_wage_outcomes(top6)]


def _svg(top6):
    return _wage_outcomes_svg(_rows(top6), top6)


# ── vocabulary ───────────────────────────────────────────────────────────────

def test_recipient_labels_match_the_reports_own_words():
    """Awards Offered directly above calls a Certificate of Achievement a
    "certificate"; the wage section must not invent a second vocabulary for it."""
    assert _wage_label("Associate or Baccalaureate Degree Recipient") == "Degree"
    assert _wage_label("Chancellor's Office Approved Certificates Recipient") == "Certificate"
    assert _wage_label("Locally Approved Certificates Recipient") == "Local certificate"


def test_unknown_recipient_type_degrades_to_its_own_name():
    assert _wage_label("Something New Recipient") == "Something New"


def test_cohorts_order_by_credential_weight_not_outcome():
    """Environmental Horticulture's certificate out-earns its degree. Row order stays
    credential-weighted so the section matches Awards Offered; the LINES show the
    inversion on their own."""
    assert _wage_rank("Associate or Baccalaureate Degree Recipient") == 0
    assert _wage_rank("Chancellor's Office Approved Certificates Recipient") == 1
    assert _wage_rank("Locally Approved Certificates Recipient") == 2
    svg = _svg("010900")
    labels = re.findall(r'fill="#[0-9a-f]{6}">(Degree|Certificate|Local certificate)<', svg)
    assert labels == ["Degree", "Certificate", "Local certificate"]


# ── geometry ─────────────────────────────────────────────────────────────────

def test_a_full_cohort_draws_a_trajectory_with_its_multiple():
    svg = _svg("121000")
    assert svg.count("<polyline") == 2                 # both RT cohorts are complete
    assert "3.4×" in svg                               # 28,040 -> 96,733
    assert "n=648" in svg


def test_the_y_axis_starts_at_zero():
    """Anchoring anywhere else inflates the lift the section exists to show."""
    for top in EVAL_TOPS:
        ticks = [int(t.replace(",", ""))
                 for t in re.findall(r'text-anchor="end">\$([\d,]+)</text>', _svg(top))]
        assert ticks, f"{top}: no y ticks"
        # order-independent: the axis is zero-based whichever way the ticks emit
        assert min(ticks) == 0, f"{top}: lowest tick is {min(ticks):,}, not 0"


def test_checkpoints_are_spaced_by_their_real_year_offsets():
    """-2, +2, +5 — gaps of 4 years then 3. Equal spacing would make the second
    segment read steeper than it is."""
    assert [y for y, _l in _WAGE_POINTS] == [-2, 2, 5]
    svg = _svg("121000")
    xs = sorted({float(x) for x in re.findall(r'<circle cx="([\d.]+)"', svg)})
    assert len(xs) == 3
    first, second = xs[1] - xs[0], xs[2] - xs[1]
    assert first / second == pytest.approx(4 / 3, rel=0.02)


def test_labels_fit_inside_the_plate():
    """The right gutter was 150 and clipped "n=76" to "n=7" — a truncated sample size
    reads as a real, wrong number."""
    width = _WAGE_CHART[0]
    for top in EVAL_TOPS:
        for m in re.finditer(r'<text x="([\d.]+)"[^>]*>([^<]*)<tspan[^>]*>([^<]*)</tspan>',
                             _svg(top)):
            end = float(m.group(1)) + 5.6 * len(m.group(2)) + 4.8 * len(m.group(3))
            assert end <= width, f"{top}: label {m.group(2)!r} overruns the plate"


# ── the omission guard ───────────────────────────────────────────────────────

def test_a_single_checkpoint_cohort_renders_and_is_not_dropped():
    """THE REGRESSION this file exists for. Community Health Worker's locally approved
    certificate reports only the 2-year figure (N/A before, N/A at five). It must
    appear — as a hollow marker with no multiple, because there is no trajectory to
    claim — not vanish."""
    rows = _rows("126100")
    orphan = [r for r in rows
              if r.wage_before is None and r.wage_after_2 and r.wage_after_5 is None]
    assert len(orphan) == 1 and orphan[0].n == 12, "fixture changed; revisit this test"
    svg = _svg("126100")
    assert "Local certificate" in svg, "the orphan cohort was dropped"
    assert svg.count('r="5.5" fill="none"') == 1, "no hollow marker for the lone point"
    assert svg.count("<polyline") == 1, "a one-point cohort must not draw a line"
    assert "n=12" in svg


def test_a_lone_point_claims_no_multiple():
    """A lift needs two endpoints. Stating one from a single observation would be
    inventing the number the section exists to report."""
    svg = _svg("126100")
    tail = svg[svg.index("Local certificate"):]
    assert "×" not in tail[:tail.index("</text>")]


@pytest.mark.parametrize("top6", EVAL_TOPS)
def test_every_cohort_in_the_csv_reaches_the_plate(top6):
    """No cohort may be lost between the export and the chart, whatever its nulls."""
    svg = _svg(top6)
    for r in _rows(top6):
        if any((r.wage_before, r.wage_after_2, r.wage_after_5)):
            assert _wage_label(r.recipient_type) in svg, \
                f"{top6}: {r.recipient_type!r} is in the data but not the chart"


def test_a_cohort_with_no_figures_at_all_yields_no_chart():
    empty = [LensWage("Associate or Baccalaureate Degree Recipient", None, None, None, 5, "w")]
    assert _wage_outcomes_svg(empty, "999999") == ""
    assert _wage_outcomes_svg([], "999999") == ""
