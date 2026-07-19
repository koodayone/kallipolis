"""Unit tests for the demand-quality predicate (partnerships.resolve.soc_in_demand).

soc_in_demand is the single birthplace of the in_demand gate — sector_lenses composes it over a SOC set
to derive the in_demand lens, and landscape_build stamps every cell with it for the priority split. These
pin the gate on a synthetic SOC so the assertions never couple to the live demand data.

Coverage:
  - both gates clear → in demand
  - openings must STRICTLY exceed the floor (== floor fails)
  - wage must MEET the floor (== floor passes)
  - a declining occupation still qualifies (the growth gate was dropped 2026-07-18)
  - missing figures read as zero (never crash on None), so below-floor → not in demand
  - INCLUDE_SOCS bypasses the openings floor ONLY — the wage gate still applies
"""

from partnerships.resolve import soc_in_demand
from partnerships.sectors import INCLUDE_SOCS, SectorRule

_RULE = SectorRule(min_openings=250, min_wage=50_000)
_SYNTH = "00-0000"  # a synthetic SOC, member of no exemption set


def _gate(**kw):
    base = dict(openings=500, wage=60_000, rule=_RULE)
    base.update(kw)
    return soc_in_demand(_SYNTH, **base)


def test_passes_when_both_gates_clear():
    assert _gate() is True


def test_openings_must_strictly_exceed_floor():
    assert _gate(openings=250) is False        # == floor fails (the gate is `<=`)
    assert _gate(openings=251) is True          # one above the floor passes


def test_wage_must_meet_floor():
    assert _gate(wage=49_999) is False
    assert _gate(wage=50_000) is True           # exactly the floor passes (the gate is `<`)


def test_no_growth_gate():
    # Growth is no longer a parameter or a gate — a role that would once be excluded as declining is in
    # demand purely on openings + wage.
    assert _gate() is True


def test_missing_figures_read_as_zero():
    # None openings/wage must not crash and read as below-floor → not in demand.
    assert soc_in_demand(_SYNTH, openings=None, wage=None, rule=_RULE) is False


def test_include_socs_bypass_the_openings_floor_only():
    if not INCLUDE_SOCS:
        return  # nothing curated below the floor in this build — mechanism is a no-op
    exempt = next(iter(INCLUDE_SOCS))
    # Below the openings floor, but INCLUDE_SOCS admits it — the wage gate still clears.
    assert soc_in_demand(exempt, openings=10, wage=60_000, rule=_RULE) is True
    # The bypass is openings-only: a below-floor wage still fails for an exempt SOC.
    assert soc_in_demand(exempt, openings=10, wage=40_000, rule=_RULE) is False
    # A non-exempt SOC with the same low openings fails outright.
    assert soc_in_demand(_SYNTH, openings=10, wage=60_000, rule=_RULE) is False
