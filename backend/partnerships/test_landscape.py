"""Unit tests for the landscape engine's draft-instance routing gate.

A draft (unpublished) instance must route ONLY where it's explicitly enabled —
its DataMart graph data ships separately from its surface, so exposing it in an
environment that lacks the data renders an empty/half-populated consortium.

The gate is parsed, not bool()'d: the docker-compose passthrough materializes
the unset env var as the STRING "0" (`${VAR:-0}`), and bool("0") is True in
Python — a naive bool() leaves the gate OPEN at the default (shipped that way
once, caught in prod). These tests pin the parse against exactly that string.

The routing tests use a SYNTHETIC draft spec injected into the registry rather
than a real instance, so they pin the gate MECHANISM independently of which
instances happen to be published at any given time (both SVAMP and SMCCD are
published as of 2026-06-08).

Coverage:
  - draft disabled at the compose default "0" (the regression that shipped)
  - draft disabled when unset/empty/off; enabled only for 1/true/yes/on
  - routable_specs filters a draft spec when disabled, includes it when enabled
  - a published spec routes regardless of the draft flag
  - SVAMP's program-scope derives from the AM sector (crosswalk-noise leak regression guard)
"""

import partnerships.landscape as landscape
from partnerships.landscape import (
    LandscapeSpec,
    routable_specs,
    _draft_landscapes_enabled,
)


def _draft_spec(id="__draft_test__"):
    return LandscapeSpec(
        id=id, colleges=("De Anza College",), socs=("17-3023",),
        sector="Advanced Manufacturing", name="Test", accent="#000000",
        published=False,
    )


def test_draft_disabled_at_compose_default_zero_string(monkeypatch):
    # docker-compose `${VAR:-0}` sets the literal string "0" when unset.
    monkeypatch.setenv("KALLIPOLIS_DRAFT_LANDSCAPES", "0")
    assert _draft_landscapes_enabled() is False


def test_draft_disabled_when_unset_or_empty(monkeypatch):
    monkeypatch.delenv("KALLIPOLIS_DRAFT_LANDSCAPES", raising=False)
    assert _draft_landscapes_enabled() is False
    monkeypatch.setenv("KALLIPOLIS_DRAFT_LANDSCAPES", "")
    assert _draft_landscapes_enabled() is False
    monkeypatch.setenv("KALLIPOLIS_DRAFT_LANDSCAPES", "off")
    assert _draft_landscapes_enabled() is False


def test_draft_enabled_only_for_truthy_tokens(monkeypatch):
    for token in ("1", "true", "TRUE", "Yes", "on"):
        monkeypatch.setenv("KALLIPOLIS_DRAFT_LANDSCAPES", token)
        assert _draft_landscapes_enabled() is True, token


def test_routable_filters_draft_when_disabled_includes_when_enabled(monkeypatch):
    draft = _draft_spec()
    monkeypatch.setitem(landscape.REGISTRY, draft.id, draft)
    # Gate closed (the prod default): the draft spec is NOT routable.
    monkeypatch.setenv("KALLIPOLIS_DRAFT_LANDSCAPES", "0")
    assert draft.id not in {s.id for s in routable_specs()}
    # Gate open (local): the draft spec joins the routable set.
    monkeypatch.setenv("KALLIPOLIS_DRAFT_LANDSCAPES", "1")
    assert draft.id in {s.id for s in routable_specs()}


def test_published_spec_routes_regardless_of_flag(monkeypatch):
    pub = LandscapeSpec(
        id="__pub_test__", colleges=("De Anza College",), socs=("17-3023",),
        sector="Advanced Manufacturing", name="Test", accent="#000000",
        published=True,
    )
    monkeypatch.setitem(landscape.REGISTRY, pub.id, pub)
    monkeypatch.setenv("KALLIPOLIS_DRAFT_LANDSCAPES", "0")
    assert pub.id in {s.id for s in routable_specs()}


def test_svamp_program_scope_is_handpicked_portfolio():
    """SVAMP is AUTHORED: its program-scope universe IS the hand-picked Composition.programs (the
    portfolio) — a selection, not a derive-then-exclude. Regression guard for the crosswalk-noise leak:
    IT (070100…) and Commercial Music (100500) must not appear, and the charter (HVAC/Auto/Biotech)
    stays out — not because a sector excludes them, but because they simply aren't in the portfolio."""
    from partnerships.landscape import SVAMP_SPEC, _AM_PROGRAMS
    # Scope == the authored portfolio, exactly. in_scope_tops is that set (post the in_scope gate,
    # which for an authored spec is membership in composition.programs).
    assert SVAMP_SPEC.composition.programs == _AM_PROGRAMS
    scope = set(SVAMP_SPEC.in_scope_tops())
    assert scope == set(_AM_PROGRAMS)
    # Crosswalk-noise that once bled into AM is not in the hand-picked portfolio (the leak stays closed).
    assert not SVAMP_SPEC.in_scope("100500")   # Commercial Music
    assert not SVAMP_SPEC.in_scope("070100")   # IT / CIS
    # The charter stays out; core AM stays in.
    assert not SVAMP_SPEC.in_scope("094600")   # HVAC — not hand-picked
    assert not SVAMP_SPEC.in_scope("094800")   # Automotive — not hand-picked
    assert SVAMP_SPEC.in_scope("095630")       # Machining — core AM, in the portfolio
