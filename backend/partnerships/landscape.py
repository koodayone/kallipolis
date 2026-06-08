"""LandscapeSpec — the per-instance parameter set behind an aggregated
partnership landscape.

SVAMP began as a bespoke one-off (see svamp.py): a fixed set of member
colleges and target occupations, hardcoded as module constants, aggregated
into one regional landscape. Standing up a SECOND such landscape (the San
Mateo CCD advanced-manufacturing view) revealed that the bespoke part is a
*config object*, not the machinery — `build_svamp_landscape()` takes no
arguments and reads five module globals; the builders, the regional-vs-
institutional invariant, and the dashboard components are all already
parameter-blind. This module lifts those globals into one declarative spec so
the same engine renders any instance.

This is deliberately NOT an ontology unit and NOT a general framework in the
governed sense — it is a registry of bespoke prototype surfaces nested inside
the `partnerships` unit (so it stays clear of the vocabulary_alignment /
backend_layout audits, exactly as svamp.py already does). Each instance is a
SURFACE, not a graph concept.

The aggregation invariant (unchanged, see svamp.py module docstring) is what
constrains the spec: DEMAND and EMPLOYERS are REGIONAL, read once per SOC /
as a distinct union over the region; SUPPLY and STUDENTS are INSTITUTIONAL,
summed across member colleges. That is why `colleges` is the only school-side
field and the region is DERIVED from it (`resolve_region`) rather than
specified — the members must collapse to a single COE region for the regional
reads to be a single shared number. Both current instances (SVAMP, SMCCD) sit
entirely within the "Bay" region, so each is single-region.

Engine convention — `college` is the single-college scope argument.
Because INSTITUTIONAL reads sum across `spec.colleges`, "iterate the members"
is the engine's most common loop. A builder may ALSO take a `college` argument
to scope one surface to a single member (the crosswalk's per-college taught
marking is the first such case). To keep the two from colliding — a member
loop named `for college in colleges` silently rebinds the scope argument to
the last member — institutional sums are owned by named pure helpers
(svamp_programs._consortium_supply is the model), and any inline member loop
iterates `member`, never `college`. The name `college` is reserved for the
scope argument alone.
"""

from __future__ import annotations

from dataclasses import dataclass

from ontology.crosswalks import is_cte_top4_family
from ontology.regions import COLLEGE_COE_REGION


@dataclass(frozen=True)
class LandscapeSpec:
    """One aggregated-landscape instance.

    Mirrors exactly the constants `build_svamp_landscape()` reads today; the
    SVAMP instance below reproduces them verbatim so the refactor that threads
    `spec` through the builders is behavior-preserving. The invariant is pinned
    by the graph-free assembly tests (partnerships/test_svamp*.py), which
    exercise the pure builders for both consortium and single-college scope.
    """

    # Stable instance key. Drives the API route prefix (/partnerships/<id>),
    # the frontend route (/<id>), and the session-cache namespace.
    id: str

    # ── Scope (the parameters the user picks per instance) ────────────────
    # Member colleges (institutional axis). Region is DERIVED from these, not
    # specified — they must share one COE region (see resolve_region).
    colleges: tuple[str, ...]
    # Target occupations (demand axis). One SvampCell per SOC, in this order.
    socs: tuple[str, ...]
    # Program/supply scope: TOP division + the mandate exclusions, applied on
    # top of the faithful (never-edited) TOP-CIP-SOC crosswalk. See in_scope.
    top_division: str
    excluded_tops: frozenset[str]

    # ── Identity (presentation; surfaced to the frontend via the payload) ──
    # Canonical PCAH Strong Workforce sector label (drives the priority-sector
    # tag and the leaf report's sector framing).
    sector: str
    # Consortium display name — woven into the masthead, report headers, and
    # the server-composed executive summary.
    name: str
    # Brand accent hex — the scope color the whole instrument wears.
    accent: str

    def in_scope(self, top6: str | None) -> bool:
        """Whether a TOP6 is in this instance's scoped program universe: in the
        configured TOP division, a CTE (career-technical) workforce program —
        not transfer/academic — and not excluded by the director's mandate.

        Identical predicate to svamp.is_svamp_top (which becomes a thin alias
        to SVAMP_SPEC.in_scope). Family-level CTE test, so newer TOP6 codes the
        PCAH file misses (e.g. 095690 Digital Fabrication Technician) stay in
        while all-transfer families (0901) fall out.
        """
        return (
            bool(top6)
            and top6.startswith(self.top_division)
            and top6 not in self.excluded_tops
            and is_cte_top4_family(top6)
        )

    def resolve_region(self) -> str:
        """The single shared COE region for the member colleges — the
        precondition that makes regional demand one number per SOC. Asserts the
        members collapse to exactly one region (the same guard as
        svamp._resolve_region)."""
        regions = {COLLEGE_COE_REGION.get(c, "") for c in self.colleges}
        regions.discard("")
        if len(regions) != 1:
            raise ValueError(
                f"Landscape '{self.id}' member colleges must share one COE "
                f"region; got {regions or 'none'}"
            )
        return next(iter(regions))


# ── Shared advanced-manufacturing scope ───────────────────────────────────
# SVAMP and SMCCD target the identical occupation + program scope; only the
# member colleges (and identity) differ. Defined once so the two instances
# cannot drift.
_AM_SOCS: tuple[str, ...] = (
    "17-3023", "17-3024", "17-3026", "17-3027", "17-3028", "17-3029",
    "49-9041", "49-9043", "51-4041", "51-9141", "51-9161", "51-9162",
)
_AM_TOP_DIVISION = "09"  # Engineering & Industrial Technologies
_AM_EXCLUDED_TOPS = frozenset({
    "094600",  # Environmental Control Technology (HVAC)
    "094800",  # Automotive Technology
})


# ── Instances ─────────────────────────────────────────────────────────────

# Instance #1: the original Silicon Valley consortium. Reproduces svamp.py's
# constants verbatim — the golden-snapshot invariant depends on it.
SVAMP_SPEC = LandscapeSpec(
    id="svamp",
    colleges=(
        "De Anza College",
        "Evergreen Valley College",
        "Foothill College",
        "Mission College",
        "Ohlone College",
    ),
    socs=_AM_SOCS,
    top_division=_AM_TOP_DIVISION,
    excluded_tops=_AM_EXCLUDED_TOPS,
    sector="Advanced Manufacturing",
    name="Silicon Valley Advanced Manufacturing Partnership",
    accent="#ff5a5a",
)

# Instance #2: San Mateo County CCD — same advanced-manufacturing scope, the
# three district colleges (all "Bay" region, so region resolves for free).
# NOTE: name + accent are PLACEHOLDERS pending confirmation.
SMCCD_SPEC = LandscapeSpec(
    id="smccd",
    colleges=(
        "College of San Mateo",
        "Skyline College",
        "Cañada College",
    ),
    socs=_AM_SOCS,
    top_division=_AM_TOP_DIVISION,
    excluded_tops=_AM_EXCLUDED_TOPS,
    sector="Advanced Manufacturing",
    name="SMCCD - Advanced Manufacturing",
    accent="#8b6fd0",  # placeholder — pending confirmation
)


# Registry: every mounted instance. Adding a third landscape = one entry here
# (plus its frontend route); the engine and components are untouched.
REGISTRY: dict[str, LandscapeSpec] = {
    SVAMP_SPEC.id: SVAMP_SPEC,
    SMCCD_SPEC.id: SMCCD_SPEC,
}
