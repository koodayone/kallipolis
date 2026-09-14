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
  - a full three-point cohort draws a polyline and a dot per checkpoint
  - no lift multiple is printed (it contradicted the levels it sat beside)
  - a single-checkpoint cohort renders (hollow marker) and is never dropped
  - the y-axis is zero-based and the x-axis honours the real year offsets
  - no cohort is lost between the CSV and the plate, for all four shipped evaluations
  - the section is evaluations-only and carries the statewide caveat
"""
import re

import pytest

from ontology.programs import get_wage_outcomes
from partnerships.lens import LensWage
from partnerships.report import (_WAGE_CHART, _WAGE_POINTS, _wage_label, _wage_outcomes_svg,
                                 _wage_qualifier, _wage_rank, _wage_table)

#: The four TOPs the shipped program evaluations cover.
EVAL_TOPS = ("121000", "010900", "126100", "010210")


def _rows(top6):
    return [LensWage(w["recipient_type"], w["wage_before"], w["wage_after_2"],
                     w["wage_after_5"], w["n"], w["window"])
            for w in get_wage_outcomes(top6)]


def _svg(top6):
    return _wage_outcomes_svg(_rows(top6), top6)


def _tbl(top6):
    return _wage_table(_rows(top6))


# ── vocabulary ───────────────────────────────────────────────────────────────

def test_recipient_labels_name_the_approval_route():
    """This section is the only place in the report the CO-approved / locally-approved
    split appears. Bare "Certificate" beside "Local certificate" read as "certificates
    in general" versus "a local one"."""
    assert _wage_label("Associate or Baccalaureate Degree Recipient") == "Degree"
    assert _wage_label("Chancellor's Office Approved Certificates Recipient") == "Certificate, CO-approved"
    assert _wage_label("Locally Approved Certificates Recipient") == "Certificate, locally approved"


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
    labels = re.findall(r'fill="#5a6577">(Degree|Certificate,[^<]*)</text>', svg)
    assert labels == ["Degree", "Certificate, CO-approved", "Certificate, locally approved"]


# ── geometry ─────────────────────────────────────────────────────────────────

def test_a_full_cohort_draws_a_trajectory():
    svg = _svg("121000")
    assert svg.count("<polyline") == 2                 # both RT cohorts are complete
    assert svg.count('<circle') == 6                   # three checkpoints x two cohorts


def test_no_lift_multiple_is_printed():
    """Removed as noise, and as a genuine misread: the certificate cohort often
    carries the LARGER multiple while ending at the LOWER level — Veterinary
    Technology is 1.7x vs 2.5x but finishes $14k behind, because it started higher.
    Two true numbers pointing opposite ways. The lines carry the lift."""
    for top in EVAL_TOPS:
        assert "×" not in _svg(top), f"{top}: a lift multiple is still rendered"


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
    assert "Certificate, locally approved" in svg, "the orphan cohort was dropped"
    assert svg.count('r="5.5" fill="none"') == 1, "no hollow marker for the lone point"
    assert svg.count("<polyline") == 1, "a one-point cohort must not draw a line"


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


# ── the value table ──────────────────────────────────────────────────────────
# Direct point labels were measured and rejected: across the four evaluations five of
# eleven adjacent pairs sit closer than a label is tall, and Environmental
# Horticulture's degree and local certificate are $629 apart at two years — 1.2px.

def test_the_table_carries_the_figures_and_the_sample_sizes():
    t = _tbl("121000")
    for v in ("$28,040", "$87,457", "$96,733", "$23,813", "$75,095", "$86,357"):
        assert v in t, f"missing {v}"
    assert "n=648" in t and "n=185" in t


def test_a_missing_checkpoint_prints_n_slash_a_not_a_blank():
    """The reason the table exists as much as the figures do. Community Health
    Worker's local certificate has no before or five-year figure; a blank cell would
    read as an oversight, and an omitted row as a complete picture."""
    t = _tbl("126100")
    assert t.count('class="num na">n/a</td>') == 2
    assert "$61,661" in t
    assert "n=12" in t


def test_the_label_and_count_do_not_run_together():
    """`.trend td.prog span` is inline, so without a separator the cell rendered
    "Certificaten=28"."""
    assert "</b> <span>" in _tbl("126100")


def test_the_table_emits_the_class_build_docx_renders_natively():
    """table.trend becomes a real Word table, so a reader can select $96,733. Baked
    into the chart raster it would be pixels."""
    t = _tbl("121000")
    assert t.startswith('<table class="trend">')
    assert t.count("<th>") == len(_WAGE_POINTS)


def test_no_table_without_rows():
    assert _wage_table([]) == ""


def test_the_degree_row_says_it_pools_associate_and_baccalaureate():
    """DataMart's degree cohort is one bucket for both. Respiratory Therapy lists an
    A.S. AND a B.S. under Awards Offered, so an unqualified "Degree" line there reads
    as the associate alone."""
    assert _wage_qualifier("Associate or Baccalaureate Degree Recipient") == \
        "associate or baccalaureate"
    assert "associate or baccalaureate" in _tbl("121000")


def test_certificate_rows_need_no_qualifier_beyond_their_label():
    """Their labels already carry the approval route, so a sub-line would repeat it."""
    for rt in ("Chancellor's Office Approved Certificates Recipient",
               "Locally Approved Certificates Recipient"):
        assert _wage_qualifier(rt) == ""
