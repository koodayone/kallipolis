"""The per-member Composition — how a member narrows a sector to its charter.

The ONLY per-member scope input to the engine. Each knob is a SELECTION from a grounded universe, never a
new fact or rule:

  - ``occupations``      None → the universal lenses DERIVE the set (the default, what most members use);
                         a tuple → the member's AUTHORED subset of the sector's occupation membership.
  - ``program_excludes`` programs the member's charter drops from its otherwise-eligible feeders
                         (e.g. SVAMP excludes Automotive / HVAC / Biotech).
  - ``program_includes`` (reserved, empty today) explicit additions within the vocational universe, for a
                         member whose derived scope misses a program it runs — unused until one needs it.

``validate`` enforces **selection, not invention**: every authored value must be a subset of the grounded
universe it selects from, so a Composition can never express a fork (a new rule, threshold, occupation, or
edge). This is what lets every member author its own view while the system stays one engine. See
research/architecture/UNIFIED-ENGINE-PLAN.md (Phase B — the Composition).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Optional


@dataclass(frozen=True)
class Composition:
    """A member's authored narrowing of a sector. Frozen — it is data the engine reads, not state."""

    # None → derived by the lenses; a tuple → an explicit subset of the sector's occupation membership.
    occupations: Optional[tuple[str, ...]] = None
    # Charter subtraction: grounded programs the member sets outside its scope.
    program_excludes: frozenset[str] = frozenset()
    # Reserved (empty today): grounded programs the member adds back within the vocational universe.
    program_includes: frozenset[str] = frozenset()

    @property
    def is_authored(self) -> bool:
        """True when the member hand-picked its occupation set (vs. deriving it from the lenses). The
        provenance is implicit in whether ``occupations`` is set — no separate flag to drift out of sync."""
        return self.occupations is not None


class ScopeError(ValueError):
    """A Composition tried to select something outside the grounded universe — an attempted fork."""


def validate(comp: Composition, *, membership: Iterable[str], vocational_universe: Iterable[str]) -> None:
    """Enforce selection-not-invention. ``membership`` is the sector's grounded occupation set;
    ``vocational_universe`` is the grounded ``is_vocational`` program set. Raises :class:`ScopeError` on any
    value that is not a subset of the universe it selects from — so authoring can subtract/select, but can
    never invent a new occupation or program (and, by construction, never a rule)."""
    members = set(membership)
    voc = set(vocational_universe)
    if comp.occupations is not None:
        stray = sorted(set(comp.occupations) - members)
        if stray:
            raise ScopeError(
                f"authored occupations must be a subset of the sector's membership; not members: {stray}")
    for label, sel in (("excludes", comp.program_excludes), ("includes", comp.program_includes)):
        stray = sorted(set(sel) - voc)
        if stray:
            raise ScopeError(
                f"charter {label} must be grounded vocational programs; not in the vocational universe: {stray}")
