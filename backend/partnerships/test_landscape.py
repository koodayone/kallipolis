"""Unit tests for the landscape engine's draft-instance routing gate.

A draft (unpublished) instance must route ONLY where it's explicitly enabled —
its DataMart graph data ships separately from its surface, so exposing it in an
environment that lacks the data renders an empty/half-populated consortium.

The gate is parsed, not bool()'d: the docker-compose passthrough materializes
the unset env var as the STRING "0" (`${VAR:-0}`), and bool("0") is True in
Python — a naive bool() leaves the gate OPEN at the default (shipped that way
once, caught in prod). These tests pin the parse against exactly that string.

Coverage:
  - draft disabled at the compose default "0" (the regression that shipped)
  - draft disabled when unset or empty
  - draft enabled only for explicit truthy tokens (1/true/yes/on, case-insensitive)
  - routable_specs reflects the gate: svamp always; smccd only when enabled
  - SMCCD is draft (published False), SVAMP published
"""

from partnerships.landscape import (
    routable_specs,
    _draft_landscapes_enabled,
    SVAMP_SPEC,
    SMCCD_SPEC,
)


def test_draft_disabled_at_compose_default_zero_string(monkeypatch):
    # docker-compose `${VAR:-0}` sets the literal string "0" when unset.
    monkeypatch.setenv("KALLIPOLIS_DRAFT_LANDSCAPES", "0")
    assert _draft_landscapes_enabled() is False
    assert [s.id for s in routable_specs()] == ["svamp"]


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
    # With the gate open, the draft instance joins the routable set.
    assert sorted(s.id for s in routable_specs()) == ["smccd", "svamp"]


def test_smccd_is_draft_svamp_is_published():
    assert SVAMP_SPEC.published is True
    assert SMCCD_SPEC.published is False
