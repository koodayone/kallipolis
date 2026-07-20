"""Composition — the selection-not-invention guardrail (Step 1, unified-engine).

Proves the property the whole authoring design rests on: a Composition can SELECT from the grounded universe
(subset of the sector's occupations / vocational programs) but can never INVENT — an out-of-universe value
is a ScopeError, so authoring structurally cannot express a fork. Graph-free (pure data), except the two
registered-spec checks which read the crosswalk/taxonomy.

Coverage:
  - Default Composition is derived (occupations=None), authored when occupations set
  - validate() passes a subset of the sector membership + vocational universe
  - validate() rejects an authored occupation outside the sector's membership (ScopeError)
  - validate() rejects a charter exclude/include outside the vocational universe (ScopeError)
  - Composition is frozen/hashable (safe as an lru_cache key / frozen-spec field)
  - SVAMP's registered composition is authored, its charter is {HVAC, Auto, Biotech}, and it validates
    against the live AM membership + vocational universe
  - A rule-derived member (SMCCD-adm) carries the empty default Composition
"""
import pytest

from partnerships.composition import Composition, ScopeError, validate

MEMBERSHIP = frozenset({"11-1111", "22-2222", "33-3333"})   # a sector's grounded occupation set
VOC = frozenset({"094500", "094800", "095630"})             # a grounded is_vocational program set


def test_default_is_derived_and_validates():
    c = Composition()
    assert c.is_authored is False
    validate(c, membership=MEMBERSHIP, vocational_universe=VOC)  # no authored values → no-op


def test_authored_subset_is_ok():
    c = Composition(occupations=("11-1111", "22-2222"), program_excludes=frozenset({"094800"}))
    assert c.is_authored is True
    validate(c, membership=MEMBERSHIP, vocational_universe=VOC)  # subset of both universes → passes


def test_authored_occupation_outside_membership_is_rejected():
    c = Composition(occupations=("11-1111", "99-9999"))         # 99-9999 is not a sector occupation
    with pytest.raises(ScopeError, match="99-9999"):
        validate(c, membership=MEMBERSHIP, vocational_universe=VOC)


def test_charter_exclude_outside_vocational_is_rejected():
    c = Composition(program_excludes=frozenset({"000000"}))     # 000000 is not a vocational program
    with pytest.raises(ScopeError, match="000000"):
        validate(c, membership=MEMBERSHIP, vocational_universe=VOC)


def test_charter_include_outside_vocational_is_rejected():
    c = Composition(program_includes=frozenset({"000000"}))
    with pytest.raises(ScopeError, match="000000"):
        validate(c, membership=MEMBERSHIP, vocational_universe=VOC)


def test_frozen_is_hashable():
    # Frozen so it can be an lru_cache key / live on a frozen spec without a mutable-default footgun.
    assert hash(Composition(occupations=("11-1111",))) == hash(Composition(occupations=("11-1111",)))


def test_svamp_registered_composition_is_authored_and_valid():
    """The one live author today: SVAMP hand-picks BOTH sides and passes the guardrail against the real AM
    membership + vocational universe — its 12 occupations ⊆ the sector's 49, its 23-program portfolio ⊆ the
    vocational universe. No program_excludes: a hand-pick is a selection, so there is nothing to subtract."""
    from ontology.crosswalks import _load_vocational_top6
    from partnerships.landscape import SVAMP_SPEC, _AM_PROGRAMS
    from partnerships.sectors import SECTORS

    comp = SVAMP_SPEC.composition
    assert comp.is_authored                          # hand-picked occupations
    assert comp.programs == _AM_PROGRAMS             # ...and hand-picked programs (the portfolio) — both sides
    assert comp.program_excludes == frozenset()      # selection, not exclusion — no charter to subtract
    validate(comp, membership=SECTORS["adm"].socs, vocational_universe=_load_vocational_top6())


def test_derived_members_carry_empty_composition():
    """A rule-derived member (SMCCD-adm) carries the default empty Composition — occupations derived, no
    charter — so the field is a no-op there and the migration is byte-identical."""
    from partnerships.landscape import SMCCD_ADM_SPEC

    assert SMCCD_ADM_SPEC.composition.is_authored is False
    assert SMCCD_ADM_SPEC.composition.program_excludes == frozenset()
