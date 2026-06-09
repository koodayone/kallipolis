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
        top_division="09", excluded_tops=frozenset(),
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
        top_division="09", excluded_tops=frozenset(),
        sector="Advanced Manufacturing", name="Test", accent="#000000",
        published=True,
    )
    monkeypatch.setitem(landscape.REGISTRY, pub.id, pub)
    monkeypatch.setenv("KALLIPOLIS_DRAFT_LANDSCAPES", "0")
    assert pub.id in {s.id for s in routable_specs()}
