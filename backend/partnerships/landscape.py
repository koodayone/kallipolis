"""LandscapeSpec — the per-instance parameter set behind an aggregated
partnership landscape.

SVAMP began as a bespoke one-off (see landscape_build.py): a fixed set of member
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
backend_layout audits, exactly as landscape_build.py already does). Each instance is a
SURFACE, not a graph concept.

The aggregation invariant (unchanged, see landscape_build.py module docstring) is what
constrains the spec: DEMAND and EMPLOYERS are REGIONAL, read once per SOC /
as a distinct union over the region; SUPPLY is INSTITUTIONAL, summed across
member colleges. That is why `colleges` is the only school-side
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
(landscape_programs._consortium_supply is the model), and any inline member loop
iterates `member`, never `college`. The name `college` is reserved for the
scope argument alone.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

from ontology.crosswalks import _load_top_to_cip, is_cte_top4_family, is_vocational
from ontology.regions import COLLEGE_COE_REGION
from partnerships.composition import Composition
from partnerships.sectors import SECTORS, Sector, SectorRule


# ── Enrollment-term axis ──────────────────────────────────────────────────
# Term helpers live here (beneath the builders) so the computation resolvers
# — landscape_build, landscape_programs, and mcp_server.canonical — all read
# ONE term-exclusion rule without importing each other. Terms are NOT a fixed
# list: the course-section exports span ~5 years and colleges run different
# calendars (quarter vs. semester), so the term axis is the chronologically
# sorted union of whatever Term nodes exist. This orders "Season YYYY" labels:
# Winter < Spring < Summer < Fall within a year.
_SEASON_ORDER = {"Winter": 0, "Spring": 1, "Summer": 2, "Fall": 3}

# Seasons excluded from the enrollment trend. Summer enrollment is
# structurally low (fewer offerings, shorter term), so it reads as noise on the
# trend rather than signal; the data stays in the graph and can be re-included
# by clearing this set.
_ENROLLMENT_EXCLUDE_SEASONS = {"Summer"}

# Specific terms excluded from the enrollment trend. The two DataMart
# course-section exports cover different windows — credit runs Winter 2021 →
# Fall 2025, noncredit runs Fall 2020 → Winter 2026 — so these boundary terms
# carry only ONE family and the blended total is structurally incomplete
# there. The data stays in the graph; drop a term from this set when the
# narrower export is re-pulled to cover it.
_ENROLLMENT_EXCLUDE_TERMS = {"Fall 2020", "Winter 2026"}


def _term_excluded(term: str) -> bool:
    """True for terms the enrollment trend omits — excluded seasons (Summer)
    and the export-boundary terms only one credit family covers."""
    return term in _ENROLLMENT_EXCLUDE_TERMS or term.split()[0] in _ENROLLMENT_EXCLUDE_SEASONS


def _term_sort_key(term: str) -> tuple[int, int]:
    parts = term.split()
    season = parts[0] if parts else ""
    try:
        year = int(parts[-1])
    except (ValueError, IndexError):
        year = 0
    return (year, _SEASON_ORDER.get(season, 9))


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
    # Target occupations (demand axis). One LandscapeCell per SOC, in this order.
    socs: tuple[str, ...]
    # Program/supply scope: TOP divisions + the mandate exclusions, applied on
    # top of the faithful (never-edited) TOP-CIP-SOC crosswalk. See in_scope.
    # A tuple so an instance may span more than one division — the AM instances
    # pass a 1-tuple ("09",); a Life Sciences & Health frame spans 04/12/19/03.
    top_divisions: tuple[str, ...]
    excluded_tops: frozenset[str]

    # ── Identity (presentation; surfaced to the frontend via the payload) ──
    # Canonical PCAH Strong Workforce sector label (drives the priority-sector
    # tag and the leaf report's sector framing). This is the DISPLAY form.
    sector: str
    # Consortium display name — woven into the masthead, report headers, and
    # the server-composed executive summary.
    name: str
    # Brand accent hex — the scope color the whole instrument wears.
    accent: str

    # ── Lifecycle ─────────────────────────────────────────────────────────
    # Published instances route everywhere; a DRAFT instance (published=False)
    # routes only where KALLIPOLIS_DRAFT_LANDSCAPES is set — local iteration,
    # never the public surface. The gate exists because an instance's surface
    # ships as code but its DataMart graph data ships separately: a landscape
    # whose data isn't yet in an environment must not render an empty
    # consortium there. Flip to True once the data lands. See routable_specs.
    published: bool = True

    # Whether a division-mode universe is restricted to CTE families (the
    # looser family-level is_cte_top4_family test). True for the curated AM
    # instances. Ignored when vocational=True.
    cte_only: bool = True

    # Scope mode. True for the sector-derived instances: the program universe is
    # the authoritative per-TOP CTE gate — is_vocational (TOP6-exact, CCCCO
    # Taxonomy of Programs 7th Ed) — and top_divisions/cte_only are unused. False
    # for the curated AM instances (the legacy division + family-CTE predicate).
    vocational: bool = False

    # SOC-selection curation for sector instances (demand floor / reachable /
    # non-empty), applied at request time by partnerships.resolve.resolve().
    # None for the curated AM instances (no SOC filtering). See landscape_for.
    soc_rule: SectorRule | None = None

    # The per-member Composition — the authored narrowing (occupation subset + charter). Default = empty
    # (derived; what most members use). SVAMP fills it in. The engine reads member scope through this; today
    # its ``program_excludes`` MIRRORS the legacy charter in ``excluded_tops`` so the migration is byte-
    # identical (in_scope consults both, idempotently). Step 2 makes it authoritative and retires the legacy
    # fields. See partnerships/composition.py and research/architecture/UNIFIED-ENGINE-PLAN.md.
    composition: Composition = Composition()

    # The exact COE/EDD `swp_sectors` tag the Employer nodes carry (Sector.swp_tag).
    # Diverges from the display `sector` ("&"/short form vs "and"/full COE name),
    # so the regional employer query matches on this, falling back to `sector`
    # when unset (SVAMP, whose display label already equals the COE tag).
    swp_tag: str | None = None

    # Home TOP2 division(s) gating the feeder universe (Sector.home_divisions) —
    # empty = no division gate (the default; AM/ATL/ECU/ICT rely on excluded_tops).
    home_divisions: tuple[str, ...] = ()

    # The county/ies of the member colleges — scopes the regional employer map to
    # the district's geographic shed (the COE region is too coarse; see
    # MemberSet.counties). Empty = no county scoping (whole region).
    counties: tuple[str, ...] = ()

    # Employer-map shortlist cap: keep only the top_n firms by size (the sizable,
    # most partnership-viable employers) per industry. None = uncapped (SVAMP,
    # which is a curated SOC-breadth set, not a size-ranked one).
    top_n: int | None = None

    # ── Employer-pool expansion (greedy county → region) ──────────────────
    # When a (member × sector) map has fewer than `employer_threshold` viable
    # firms in the home county/ies, widen the shed to the NEAREST counties
    # within the COE region (counties_by_proximity) until the threshold is met —
    # so a district whose home county lacks an industry still gets a shortlist of
    # the nearest real partners rather than an empty map. 0 disables expansion
    # (home shed only — SVAMP, dense in Santa Clara). The reach (the counties the
    # map actually drew from) is reported in the employer payload as a local-vs-
    # regional signal. `max_radius` caps how far it may reach (counties in the
    # widened shed); 0 = within the whole region. Analysis (2026-06-11): T=15,
    # nearest-first, region-capped fills 92% of (district × sector) cells with
    # 100+ firms at a median reach of 2 counties — the lever for the small-county
    # structural gap (the size floor is the separate lever for small-firm sectors).
    employer_threshold: int = 0
    max_radius: int = 0

    @property
    def effective_program_excludes(self) -> frozenset[str]:
        """Every program out of this instance's feeder universe, in ONE place: the sector-level crosswalk-
        noise (``excluded_tops`` — e.g. IT / Commercial Music bleeding into Advanced Manufacturing) unioned
        with the member's charter (``composition.program_excludes`` — e.g. SVAMP's HVAC / Automotive /
        Biotech). Both scope consumers — ``in_scope`` and the programs landscape's per-occupation gather —
        read this, so they cannot disagree about what is out of scope."""
        return frozenset(self.excluded_tops) | self.composition.program_excludes

    def in_scope(self, top6: str | None) -> bool:
        """Whether a TOP6 is in this instance's scoped program universe.

        Two modes:
        - vocational=True (sector-derived instances): the authoritative
          TOP6-exact CTE gate is_vocational (CCCCO Taxonomy of Programs 7th Ed
          vocational asterisk), minus any mandate exclusions. No division
          restriction — the sector's SOC set is the anchor and relevant_tops
          intersects it with the crosswalk-reachable feeders.
        - vocational=False (curated AM instances, e.g. SVAMP): the legacy
          predicate — in a configured TOP division, CTE per the looser
          family-level test when cte_only, minus mandate exclusions. Thin alias
          for svamp.is_svamp_top.
        """
        if not top6:
            return False
        if self.vocational:
            return (
                is_vocational(top6)
                and top6 not in self.effective_program_excludes
                and (not self.home_divisions or top6[:2] in self.home_divisions)
            )
        return (
            any(top6.startswith(d) for d in self.top_divisions)
            and top6 not in self.effective_program_excludes
            and (not self.cte_only or is_cte_top4_family(top6))
        )

    def in_scope_tops(self) -> list[str]:
        """Every TOP6 in this instance's scoped program universe — `in_scope`
        applied across the full TOP catalog, in catalog order. The single source
        for the in-scope TOP set that resolve, clusters, and svamp each derive
        (graph-free; the crosswalk load is cached)."""
        return [t for t in _load_top_to_cip() if self.in_scope(t)]

    def resolve_regions(self) -> tuple[str, ...]:
        """The COE region(s) the member colleges span, sorted and de-duplicated.

        Single-element for a college or a district member (and for every
        instance that exists today); multi-element for a region/state member or
        a cross-region consortium. The aggregation invariant generalizes over
        this set: demand and employers are read PER REGION across it, supply
        sums over the member colleges. `resolve_region()` is the |regions| == 1
        special case the current builders rely on."""
        regions = {COLLEGE_COE_REGION.get(c, "") for c in self.colleges}
        regions.discard("")
        return tuple(sorted(regions))

    def resolve_region(self) -> str:
        """The single shared COE region for the member colleges — the
        precondition that makes regional demand one number per SOC. Asserts the
        members collapse to exactly one region (the same guard as
        svamp._resolve_region). Multi-region members use resolve_regions()."""
        regions = self.resolve_regions()
        if len(regions) != 1:
            raise ValueError(
                f"Landscape '{self.id}' member colleges must share one COE "
                f"region; got {regions or 'none'}"
            )
        return regions[0]


# ── Member sets (the institutional axis) ──────────────────────────────────
# A MemberSet is the school-side half of a `member × sector` landscape: the
# colleges aggregated into one instance. Composed with a Sector (sectors.py)
# by the spec factory. Members must share one COE region (resolve_region) so
# regional demand stays one number per SOC. The curated AM instances (SVAMP,
# SMCCD-AM) list their colleges inline and do NOT use this; it is for the
# sector-derived instances (smccd-biotech, smccd-health, …).
@dataclass(frozen=True)
class MemberSet:
    id: str                      # URL/id segment: "{id}-{sector}"
    label: str                   # display label (masthead)
    colleges: tuple[str, ...]
    # The county/ies the member colleges sit in — the geographic shed used to
    # scope the regional employer map to firms the district can actually partner
    # with. The COE region (e.g. "Bay") is too coarse: it spans Santa Clara
    # (SVAMP) and San Mateo (SMCCD) alike, so without this an SMCCD map would
    # show South-Bay employers and SVAMP would show peninsula ones. Empty = no
    # county scoping (the whole region).
    counties: tuple[str, ...] = ()


MEMBERS: dict[str, MemberSet] = {
    "smccd": MemberSet(
        id="smccd",
        label="San Mateo County CCD",
        colleges=(
            "College of San Mateo",
            "Skyline College",
            "Cañada College",
        ),
        counties=("San Mateo",),
    ),
    # BACCC — the Bay Area Community College Consortium: every college the COE
    # Bay region assigns (all 26 in the catalog). The consortium-level join — the
    # whole region's supply, summed across 26 members per sector. counties=()
    # (whole region): the employer map draws the region's geocoded Bay firms
    # (today San Mateo + Santa Clara), which is honest for a region-wide
    # consortium even before the other counties are geocoded.
    "baccc": MemberSet(
        id="baccc",
        label="Bay Area Community College Consortium",
        colleges=(
            "Berkeley City College",
            "Cabrillo College",
            "Cañada College",
            "Chabot College",
            "City College of San Francisco",
            "College of Alameda",
            "College of Marin",
            "College of San Mateo",
            "Contra Costa College",
            "De Anza College",
            "Diablo Valley College",
            "Evergreen Valley College",
            "Foothill College",
            "Gavilan College",
            "Laney College",
            "Las Positas College",
            "Los Medanos College",
            "Merritt College",
            "Mission College",
            "Napa Valley College",
            "Ohlone College",
            "San Jose City College",
            "Santa Rosa Junior College",
            "Skyline College",
            "Solano Community College",
            "West Valley College",
        ),
        counties=(),
    ),
}


def landscape_for(
    member: MemberSet, sector: Sector, *, published: bool = False
) -> LandscapeSpec:
    """Compose a `member × sector` landscape instance — the generic generator
    behind smccd-biotech, smccd-health, and any future combination.

    The sector supplies the demand anchor (its middle-skill SOCs) and identity
    (label, accent); the member supplies the colleges. The feeding TOP universe
    is DERIVED — vocational=True makes in_scope the authoritative is_vocational
    gate, and relevant_tops intersects it with the crosswalk-reachable feeders —
    so no division/CTE config is needed. Draft by default (data-readiness gated
    by routable_specs); pass published=True once verified in an environment.
    """
    return LandscapeSpec(
        id=f"{member.id}-{sector.id}",
        colleges=member.colleges,
        socs=sector.socs,
        top_divisions=(),  # unused in vocational mode
        excluded_tops=sector.excluded_tops,  # sector-level crosswalk-noise drops
        home_divisions=sector.home_divisions,  # TOP2 home-division gate (e.g. Health=12)
        soc_rule=sector.rule,                # sector-level SOC curation (resolve())
        vocational=True,
        published=published,
        sector=sector.label,
        swp_tag=sector.swp_tag,              # COE employer-vocabulary tag (match key)
        counties=member.counties,            # geographic shed for the employer map
        top_n=25,                            # top-25-by-size shortlist per industry
        employer_threshold=15,               # widen the shed (nearest county) until 15 viable firms
        name=f"{member.label} — {sector.label}",
        accent=sector.accent,
    )


# ── Shared advanced-manufacturing scope ───────────────────────────────────
# SVAMP and SMCCD target the identical occupation + program scope; only the
# member colleges (and identity) differ. Defined once so the two instances
# cannot drift.
_AM_SOCS: tuple[str, ...] = (
    "17-3023", "17-3024", "17-3026", "17-3027", "17-3028", "17-3029",
    "49-9041", "49-9043", "51-4041", "51-9141", "51-9161", "51-9162",
)
_AM_TOP_DIVISIONS: tuple[str, ...] = ("09",)  # Engineering & Industrial Technologies
_AM_EXCLUDED_TOPS = frozenset({
    "094600",  # Environmental Control Technology (HVAC)
    "094800",  # Automotive Technology
})


# ── Instances ─────────────────────────────────────────────────────────────

# Instance #1: the original Silicon Valley consortium. Reproduces landscape_build.py's
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
    top_divisions=_AM_TOP_DIVISIONS,  # "09" — the per-occupation crosswalk gather's top_prefix (landscape_programs)
    excluded_tops=SECTORS["adm"].excluded_tops,  # sector crosswalk-noise drops (parity with /smccd-adm); charter is in composition
    sector="Advanced Manufacturing",
    counties=("Santa Clara",),  # SVAMP's shed — keeps the peninsula (SMCCD) out
    name="Silicon Valley Advanced Manufacturing Partnership",
    accent="#ff5a5a",
    # SVAMP under the UNIVERSAL rule (Step 2b). It runs is_vocational + the active program gate, like every
    # sector-derived member, and its program-scope universe DERIVES from the AM sector — excluded_tops (the
    # sector's audited crosswalk-noise drops, e.g. IT / Commercial Music bleeding into AM), home_divisions and
    # soc_rule all come from SECTORS["adm"], never a hand-copy, so SVAMP cannot drift from /smccd-adm. Its only
    # per-member authoring is the Composition: the 12 hand-picked occupations (a subset of the AM sector's set;
    # resolve keeps them final because is_authored) and the charter (Automotive / HVAC / Biotech), both applied
    # via effective_program_excludes.
    vocational=True,
    soc_rule=SECTORS["adm"].rule,
    home_divisions=SECTORS["adm"].home_divisions,  # AM has none today (uses excluded_tops); derived so it can't drift
    composition=Composition(occupations=_AM_SOCS, program_excludes=_AM_EXCLUDED_TOPS | {"043000"}),
)

# Instance #2+: the SMCCD member set's sector views — a `member × sector` row,
# one instance per Strong Workforce priority sector the district has CTE programs
# in. SOCs come from the sector's middle-skill set (sectors.py); the feeding TOP
# universe is derived (is_vocational ∩ crosswalk-reachable), so these need NO
# scope config. SVAMP above stays hand-authored (a curated SOC subset +
# director's-mandate exclusions, not a whole sector).
#
# All SMCCD sector instances are PUBLISHED — the full member×sector rail ships
# in preview. `adm` (Advanced Manufacturing) is the canonical AM surface,
# replacing the earlier curated 12-SOC `smccd` instance (now retired; /smccd
# redirects to /smccd-adm). Occupation coverage is thin on a few sectors (the
# crosswalk under-maps some allied-health TOPs; a handful of programs aren't yet
# in the graph), so their supply renders sparse — honest, not broken.
# `unassigned` is omitted (a residual catch-all). Publishing rides on the prod
# graph carrying the employer enrichment (websites + geocodes); see the
# deployment doc's "Push local → prod" flow.
SMCCD_ADM_SPEC = landscape_for(MEMBERS["smccd"], SECTORS["adm"], published=True)
_SMCCD_SECTOR_IDS: tuple[str, ...] = (
    "biotech", "health", "business", "atl", "public_safety",
    "retail", "ict", "agwet", "edhd", "ecu",
)
_SMCCD_SECTOR_SPECS = [SMCCD_ADM_SPEC] + [
    landscape_for(MEMBERS["smccd"], SECTORS[sid], published=True)
    for sid in _SMCCD_SECTOR_IDS
]

# Instance set #3: BACCC — the same 11-sector rail over the full Bay consortium
# (26 colleges). The consortium-level join: 26-member supply per sector, rendered
# by the same engine. The coverage matrix flips to vertical headers at this
# column count (front-end), the only rendering accommodation the 26-wide join
# needs. PUBLISHED — ships in preview alongside SVAMP/SMCCD.
_BACCC_SECTOR_IDS: tuple[str, ...] = (
    "adm", "biotech", "health", "business", "atl", "public_safety",
    "retail", "ict", "agwet", "edhd", "ecu",
)
_BACCC_SECTOR_SPECS = [
    landscape_for(MEMBERS["baccc"], SECTORS[sid], published=True)
    for sid in _BACCC_SECTOR_IDS
]


# Registry: every defined instance. Adding a landscape = one entry here (plus its
# frontend route); the engine and components are untouched. The bare `smccd` id
# is intentionally absent — /smccd redirects to /smccd-adm (the AM sector view).
REGISTRY: dict[str, LandscapeSpec] = {
    SVAMP_SPEC.id: SVAMP_SPEC,
    **{s.id: s for s in _SMCCD_SECTOR_SPECS},
    **{s.id: s for s in _BACCC_SECTOR_SPECS},
}


_TRUTHY = frozenset({"1", "true", "yes", "on"})


def _draft_landscapes_enabled() -> bool:
    """Whether draft instances route in this environment. Parsed as an explicit
    truthy value, NOT bool(str): the docker-compose passthrough materializes the
    unset var as the STRING "0" (`${VAR:-0}`), and bool("0") is True in Python —
    so a naive bool() would leave the gate OPEN at the default. Only 1/true/yes/
    on (case-insensitive) enable it; "0"/""/anything else gate."""
    return os.environ.get("KALLIPOLIS_DRAFT_LANDSCAPES", "").strip().lower() in _TRUTHY


def routable_specs() -> list[LandscapeSpec]:
    """The instances whose API routes the app exposes in THIS environment:
    published instances always, draft instances only when
    KALLIPOLIS_DRAFT_LANDSCAPES is truthy (local iteration). Prod leaves it at
    the compose default "0", so a draft landscape's routes never exist there —
    its frontend surface is gated by the mirror flag (DRAFT_LANDSCAPES_ENABLED)
    and its graph data isn't loaded anyway. The registry is the full
    catalogue; this is the per-environment view of it."""
    draft = _draft_landscapes_enabled()
    return [spec for spec in REGISTRY.values() if spec.published or draft]
