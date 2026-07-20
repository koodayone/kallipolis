"""The per-member Composition — how a member narrows a sector to its chosen scope.

The ONLY per-member scope input to the engine. Each knob is a SELECTION from a grounded universe, never a
new fact or rule:

  - ``occupations``  None → the sector's occupation membership (COVERS) supplies the set (the default,
                     what most members use); a tuple → the member's HAND-PICKED subset of it.
  - ``programs``     None → the sector's home_sector portfolio (SCOPES) supplies the set; a tuple → the
                     member's HAND-PICKED program set (a subset of the vocational universe). The
                     supply-side twin of ``occupations`` — an authored member hand-picks BOTH.

``validate`` enforces **selection, not invention**: every authored value must be a subset of the grounded
universe it selects from, so a Composition can never express a fork (a new rule, threshold, occupation, or
edge). This is what lets every member author its own view while the system stays one engine. See
research/architecture/sector-membership-authority.md.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Optional


@dataclass(frozen=True)
class Composition:
    """A member's authored narrowing of a sector. Frozen — it is data the engine reads, not state."""

    # None → the sector's occupation membership (COVERS); a tuple → an explicit subset of it.
    occupations: Optional[tuple[str, ...]] = None
    # None → the sector's home_sector portfolio (SCOPES); a tuple → the member's HAND-PICKED program set
    # (an explicit subset of the vocational universe). The supply-side twin of ``occupations``: when set,
    # it IS the feeder universe. See research/architecture/sector-membership-authority.md.
    programs: Optional[tuple[str, ...]] = None

    @property
    def is_authored(self) -> bool:
        """True when the member hand-picked its occupation set (vs. deriving it from the sector). The
        provenance is implicit in whether ``occupations`` is set — no separate flag to drift out of sync."""
        return self.occupations is not None


class ScopeError(ValueError):
    """A Composition tried to select something outside the grounded universe — an attempted fork."""


def validate(comp: Composition, *, membership: Iterable[str], vocational_universe: Iterable[str]) -> None:
    """Enforce selection-not-invention. ``membership`` is the sector's grounded occupation set;
    ``vocational_universe`` is the grounded ``is_vocational`` program set. Raises :class:`ScopeError` on any
    authored value that is not a subset of the universe it selects from — so authoring can select, but can
    never invent a new occupation or program (and, by construction, never a rule)."""
    if comp.occupations is not None:
        stray = sorted(set(comp.occupations) - set(membership))
        if stray:
            raise ScopeError(
                f"authored occupations must be a subset of the sector's membership; not members: {stray}")
    if comp.programs is not None:
        stray = sorted(set(comp.programs) - set(vocational_universe))
        if stray:
            raise ScopeError(
                f"authored programs must be grounded vocational programs; not in the vocational universe: {stray}")
