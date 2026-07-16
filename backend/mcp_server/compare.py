"""The comparison engine — rank a set of analogous units by a chosen criterion.

Comparison is the layer's core analytical operation: it turns a *measure* into a *decision*
("this program addresses 1,610 openings" → "…the most of any you run"). Rather than a form per
comparison, ONE registry-driven engine: a curated ``{unit_type -> {criterion -> Criterion}}``
registry + a generic ``compare()`` that resolves a peer set, computes every admissible criterion
per unit, ranks by the chosen one, and binds each value through the provenance layer. Adding a
comparison is a registry ENTRY (data), not a form (code). v1 registers the ``program`` unit type.

Two load-bearing disciplines:
- **No composites.** A criterion must be a plain count that adds up (completions, openings) or a
  rate measured natively at the unit's grain (a program's own supply share) — never a rate you'd
  have to invent a weighted average to produce (a "program wage" blended from its occupations'
  wages). ``_register`` raises on ``composite=True``, so that hidden judgment — the opaque score we
  already superseded — cannot re-enter the registry through data entry. (A native ratio like
  supply_share or the trends is NOT a composite: no weights are chosen; it is computed AT this grain.)
- **Referential integrity by construction.** Every criterion's ``compute`` is a thin composition of
  the SAME ``canonical`` functions ``sector_overview``/``pathway`` use — never a reimplementation —
  so a program's numbers cannot drift between tools.

Self-contained (imports the canonical layer, catalog, provenance, viewlink, scope, resolvers — never
``forms``), so ``forms → compare`` stays one-directional.
"""
from __future__ import annotations

from dataclasses import dataclass, field as dc_field
from typing import Callable, Optional

from ontology.regions import COE_REGION_DISPLAY
from ontology.schema import get_driver
from partnerships.graph_reads import regional_demand
from partnerships.landscape_programs import build_programs_landscape, relevant_tops
from partnerships.members import region_member
from partnerships.resolve import resolve
from partnerships.sectors import SECTORS

from mcp_server import canonical as CAN
from mcp_server import catalog as C
from mcp_server import provenance as P
from mcp_server import viewlink as V
from mcp_server.envelope import (
    AnalysisEnvelope,
    DataBlock,
    Framing,
    Licensing,
    More,
    NextMove,
    QualifiedValue,
    Row,
    SortAxis,
)
from mcp_server.engine import select
from mcp_server.scope import coordinate_of, gate_envelope, scope_for

_TOP_N = 8
_ENROLL_WINDOW = 3   # prior same-season terms the enrollment trend averages over

# The wage criteria are read from statewide-pooled TOP6 cohorts (no college dimension),
# so their granularity is stated apart from the member-scoped "inst" grain — no member's
# own-graduate wage is ever implied.
_WAGE_GRAIN = ("statewide — pooled TOP6 award cohort (largest recipient type); "
               "not this member's own graduates")


# ── Criterion + registry ──────────────────────────────────────────────────

@dataclass(frozen=True)
class Criterion:
    key: str
    label: str
    unit: str
    field: str                 # provenance key → AUTHORITY_BY_FIELD (drives P.q source + vintage)
    higher_is_better: bool
    composite: bool            # a weighted blend (a rate rolled up via chosen weights) — MUST be False
    grain: str                 # granularity key: "inst" | "region" | "gap" | "share"
    compute: Callable          # (CompareContext, unit) -> value | None   (None ⇒ status "unavailable")
    vintage: Callable = dc_field(default=lambda ctx: None)   # (ctx) -> vintage str | None


def _register(criteria: dict[str, Criterion]) -> dict[str, Criterion]:
    """Enforce admissibility at construction: a criterion may not be a COMPOSITE — a rate rolled up
    from a finer grain by weights you chose (a 'program wage' blended from its occupations' wages).
    That is the opaque score we already superseded; a criterion must be a plain count or a
    natively-measured rate, never an invented weighted average."""
    for k, c in criteria.items():
        if c.key != k:
            raise ValueError(f"registry key {k!r} != criterion.key {c.key!r}")
        if c.composite:
            raise ValueError(
                f"criterion {k!r} is a composite — a rate that only exists by weight-averaging a finer "
                f"grain (e.g. a program wage blended from its occupations' wages). Use a plain count or "
                f"a natively-measured rate; the rate itself belongs to the grain where it is measured.")
    return criteria


# ── CompareContext — shared inputs resolved once per call ──────────────────

@dataclass
class CompareContext:
    spec: object
    entry: dict
    rspec: object
    member_colleges: list
    region_colleges: list
    sector_socs: list
    demand_by_soc: dict
    soc_facts: dict          # {soc -> full DEMANDS row: title, openings, wage, growth, employment}
    sector_tops: list        # the sector's candidate feeder programs (TOP6), for college enrollment
    recent_years: tuple
    latest_years: tuple
    enroll_latest: tuple
    enroll_recent: tuple
    region_disp: str
    region_g: str
    region_supply_g: str
    inst_g: str
    supply_v: str
    latest_v: str
    gap_v: str
    enroll_v: str
    award_trend_v: str
    enroll_trend_v: str
    wage_v: str


def build_context(member: str, sector: str) -> Optional[CompareContext]:
    sel = select(member, sector)
    if sel is None:
        return None
    entry, rspec = sel.entry, sel.spec
    region, region_disp = sel.region, sel.region_display
    member_colleges, region_colleges = sel.member_colleges, sel.region_colleges
    sector_socs = sel.sector_socs
    with get_driver().session() as s:
        demand = regional_demand(s, region, sector_socs)
    demand_by_soc = {soc: (d.get("annual_openings") or 0) for soc, d in demand.items()}
    sector_tops = sorted(relevant_tops(rspec).keys())   # the sector's candidate feeder programs

    recent_years, latest_years = CAN.recent_award_years(), CAN.recent_award_years(1)
    ss = CAN.same_season_terms()                     # same-season-as-latest terms, most recent first
    enroll_latest, enroll_recent = ss[:1], ss[1:1 + _ENROLL_WINDOW]
    supply_v, latest_v = CAN.vintage(recent_years), CAN.vintage(latest_years)
    wage_win = CAN.wage_window()
    return CompareContext(
        spec=sel.raw_spec, entry=entry, rspec=rspec, member_colleges=member_colleges,
        region_colleges=region_colleges, sector_socs=sector_socs, demand_by_soc=demand_by_soc,
        soc_facts=demand, sector_tops=sector_tops,
        recent_years=recent_years, latest_years=latest_years, enroll_latest=enroll_latest,
        enroll_recent=enroll_recent, region_disp=region_disp,
        region_g=f"regional ({region_disp})",
        region_supply_g=f"regional ({region_disp}) — all {len(region_colleges)} colleges",
        inst_g=f"institutional — {entry.get('member_kind', 'member')} (Σ {len(member_colleges)} colleges)",
        supply_v=supply_v, latest_v=latest_v, gap_v=f"{P.COE_DEMAND_VINTAGE} vs {supply_v}",
        enroll_v=(enroll_latest[0] if enroll_latest else "enrollment"),
        award_trend_v=f"{latest_v} ÷ {supply_v}",
        enroll_trend_v=(f"{enroll_latest[0]} ÷ prior {enroll_latest[0].split()[0]}s"
                        if enroll_latest else ""),
        wage_v=(f"pooled graduate wages, award years {wage_win}" if wage_win else "pooled graduate wages"))


# ── Program criteria — thin CAN.* compositions (referential integrity by construction) ──

def _c_addressable_demand(ctx, u):
    return CAN.addressable_demand(u.top6, ctx.sector_socs, ctx.demand_by_soc)[1]


def _c_addressable_gap(ctx, u):
    addr = CAN.addressable_demand(u.top6, ctx.sector_socs, ctx.demand_by_soc)[1]
    socs = CAN.program_socs(u.top6, within=ctx.sector_socs)
    return CAN.gap(addr, CAN.supply_over_socs(ctx.region_colleges, socs, spec=ctx.rspec))


def _c_completions(ctx, u):
    return CAN.supply_over_tops(ctx.member_colleges, [u.top6])


def _c_enrollment(ctx, u):
    return CAN.enrollment_over_tops(ctx.member_colleges, [u.top6])


def _c_supply_share(ctx, u):
    region = CAN.supply_over_tops(ctx.region_colleges, [u.top6])
    if not region:
        return None
    return round(CAN.supply_over_tops(ctx.member_colleges, [u.top6]) / region, 3)


def _c_award_trend(ctx, u):
    base = CAN.supply_over_tops(ctx.member_colleges, [u.top6], years=ctx.recent_years)
    if not base:
        return None
    return round(CAN.supply_over_tops(ctx.member_colleges, [u.top6], years=ctx.latest_years) / base, 2)


def _c_enrollment_trend(ctx, u):
    base = CAN.enrollment_over_tops(ctx.member_colleges, [u.top6], terms=ctx.enroll_recent)
    if not base:
        return None
    return round(CAN.enrollment_over_tops(ctx.member_colleges, [u.top6], terms=ctx.enroll_latest) / base, 2)


# Wage criteria — the measured graduate-wage outcome, read from the statewide-pooled
# ProgramWageOutcome cohort (NOT a weighted blend of the program's occupations' OES wages,
# which would be the composite _register forbids). All three read the SAME largest cohort
# (one resolver), so a program's lift and its levels are internally consistent.

def _c_wage_lift(ctx, u):
    w = CAN.program_wage_outcome(u.top6)
    if not w or w["wage_before"] is None or w["wage_after_2"] is None:
        return None
    return w["wage_after_2"] - w["wage_before"]


def _c_wage_after_2(ctx, u):
    w = CAN.program_wage_outcome(u.top6)
    return w["wage_after_2"] if w else None


def _c_wage_after_5(ctx, u):
    w = CAN.program_wage_outcome(u.top6)
    return w["wage_after_5"] if w else None


_PROGRAM = _register({
    "addressable_demand": Criterion("addressable_demand", "Addressable demand", "openings/yr",
                                    "annual_openings", True, False, "region", _c_addressable_demand),
    "addressable_gap": Criterion("addressable_gap", "Addressable gap", "openings/yr",
                                 "gap", True, False, "gap", _c_addressable_gap,
                                 vintage=lambda ctx: ctx.gap_v),
    "completions": Criterion("completions", "Completions (3-yr)", "completions/yr",
                             "projected_supply", True, False, "inst", _c_completions,
                             vintage=lambda ctx: ctx.supply_v),
    "enrollment": Criterion("enrollment", "Enrollment", "enrolled/term",
                            "enrollment", True, False, "inst", _c_enrollment,
                            vintage=lambda ctx: ctx.enroll_v),
    "supply_share": Criterion("supply_share", "Supply share (of region's output)", "fraction",
                              "supply_share", True, False, "share", _c_supply_share,
                              vintage=lambda ctx: ctx.supply_v),
    "award_trend": Criterion("award_trend", "Award trend (latest ÷ 3-yr)", "ratio",
                             "award_trend", True, False, "inst", _c_award_trend,
                             vintage=lambda ctx: ctx.award_trend_v),
    "enrollment_trend": Criterion("enrollment_trend", "Enrollment trend (same-season)", "ratio",
                                  "enrollment_trend", True, False, "inst", _c_enrollment_trend,
                                  vintage=lambda ctx: ctx.enroll_trend_v),
    "wage_lift": Criterion("wage_lift", "Wage lift (2-yr − pre-enrollment)", "$/yr",
                           "wage_lift", True, False, "statewide", _c_wage_lift,
                           vintage=lambda ctx: ctx.wage_v),
    "wage_after_2": Criterion("wage_after_2", "Median wage, 2 yrs after award", "$/yr",
                              "wage_after_2", True, False, "statewide", _c_wage_after_2,
                              vintage=lambda ctx: ctx.wage_v),
    "wage_after_5": Criterion("wage_after_5", "Median wage, 5 yrs after award", "$/yr",
                              "wage_after_5", True, False, "statewide", _c_wage_after_5,
                              vintage=lambda ctx: ctx.wage_v),
})


# ── Occupation criteria — rank the sector's demanded occupations by native measures ──
# Demand facts (openings, wage, growth, employment) are the DEMANDS-edge values carried on the
# context (soc_facts); supply/gap/share compose the SAME CAN.* resolvers the gap and occupation
# forms use, so a SOC's figures match across tools. Wage/growth take DISTINCT field keys
# (occ_median_wage / occ_growth_rate) — the occupation's regional OES signal, never a program's.

@dataclass(frozen=True)
class _OccUnit:
    soc: str
    title: str


def _oc_openings(ctx, u):
    return ctx.soc_facts.get(u.soc, {}).get("annual_openings")


def _oc_wage(ctx, u):
    return ctx.soc_facts.get(u.soc, {}).get("annual_wage")


def _oc_growth(ctx, u):
    return ctx.soc_facts.get(u.soc, {}).get("growth_rate")


def _oc_employment(ctx, u):
    return ctx.soc_facts.get(u.soc, {}).get("employment")


def _oc_regional_supply(ctx, u):
    return CAN.supply(ctx.region_colleges, u.soc, spec=ctx.rspec)


def _oc_supply_gap(ctx, u):
    openings = ctx.soc_facts.get(u.soc, {}).get("annual_openings")
    return CAN.gap(openings, CAN.supply(ctx.region_colleges, u.soc, spec=ctx.rspec))


def _oc_member_supply_share(ctx, u):
    region = CAN.supply(ctx.region_colleges, u.soc, spec=ctx.rspec)
    if not region:
        return None
    return round(CAN.supply(ctx.member_colleges, u.soc, spec=ctx.rspec) / region, 3)


_OCCUPATION = _register({
    "regional_openings": Criterion("regional_openings", "Regional openings", "openings/yr",
                                   "annual_openings", True, False, "region", _oc_openings),
    "median_wage": Criterion("median_wage", "Median wage (occupation)", "$/yr",
                             "occ_median_wage", True, False, "region", _oc_wage),
    "projected_growth": Criterion("projected_growth", "Projected growth (5-yr)", "%",
                                  "occ_growth_rate", True, False, "region", _oc_growth),
    "regional_employment": Criterion("regional_employment", "Regional employment", "jobs",
                                     "regional_employment", True, False, "region", _oc_employment),
    "regional_supply": Criterion("regional_supply", "Regional supply", "completions/yr",
                                 "projected_supply", True, False, "region_supply", _oc_regional_supply,
                                 vintage=lambda ctx: ctx.supply_v),
    "supply_gap": Criterion("supply_gap", "Supply gap (regional)", "openings/yr",
                            "gap", True, False, "gap", _oc_supply_gap,
                            vintage=lambda ctx: ctx.gap_v),
    "member_supply_share": Criterion("member_supply_share", "Member supply share", "fraction",
                                     "supply_share", True, False, "share", _oc_member_supply_share,
                                     vintage=lambda ctx: ctx.supply_v),
})


# ── College criteria — rank the region's colleges by their sector-scoped supply/coverage ──
# Positioning, never competition: each college's completions into the sector's occupations, its
# share of the region's output, and its enrollment in the sector's programs — all single-college
# scoped through the SAME CAN.* resolvers, so a college's figure matches the coverage form/builders.
# Share is the size-normalized headline (the default), so a small college is not buried by a big one.

def _cl_sector_supply(ctx, u):
    return CAN.supply_over_socs([u], ctx.sector_socs, spec=ctx.rspec)


def _cl_supply_share(ctx, u):
    region = CAN.supply_over_socs(ctx.region_colleges, ctx.sector_socs, spec=ctx.rspec)
    if not region:
        return None
    return round(CAN.supply_over_socs([u], ctx.sector_socs, spec=ctx.rspec) / region, 3)


def _cl_sector_enrollment(ctx, u):
    return CAN.enrollment_over_tops([u], ctx.sector_tops)


_COLLEGE = _register({
    "supply_share": Criterion("supply_share", "Supply share (of region's output)", "fraction",
                              "supply_share", True, False, "college_share", _cl_supply_share,
                              vintage=lambda ctx: ctx.supply_v),
    "sector_supply": Criterion("sector_supply", "Sector supply (completions)", "completions/yr",
                               "projected_supply", True, False, "college", _cl_sector_supply,
                               vintage=lambda ctx: ctx.supply_v),
    "sector_enrollment": Criterion("sector_enrollment", "Sector enrollment", "enrolled/term",
                                   "enrollment", True, False, "college", _cl_sector_enrollment,
                                   vintage=lambda ctx: ctx.enroll_v),
})


REGISTRY: dict[str, dict[str, Criterion]] = {
    "program": _PROGRAM, "occupation": _OCCUPATION, "college": _COLLEGE}
PEER_SET: dict[str, Callable] = {
    "program": lambda ctx: build_programs_landscape(ctx.rspec).tops,
    "occupation": lambda ctx: [_OccUnit(soc, f.get("title") or soc) for soc, f in ctx.soc_facts.items()],
    "college": lambda ctx: list(ctx.region_colleges)}
UNIT_LABEL: dict[str, Callable] = {
    "program": lambda u: f"{u.top6} {u.name}",
    "occupation": lambda u: f"{u.soc} {u.title}",
    "college": lambda u: str(u)}
_UNIT_ID: dict[str, Callable] = {
    "program": lambda u: u.top6,
    "occupation": lambda u: u.soc,
    "college": lambda u: str(u)}


@dataclass(frozen=True)
class _UnitMeta:
    """Per-unit-type surface metadata that generalizes the engine's once-program-only
    seams: whether a sector is required, and how a ranked unit is drilled into."""

    noun: str                    # singular unit noun, for messages
    needs_sector: bool
    drill_form: str              # internal form-id a ranked unit drills into
    coord_key: Optional[str]     # coordinate_of kwarg carrying the unit id ("top6" | "soc" | None)
    drill_hint: str              # what the drill reveals, for the next-move rationale


_UNIT_META: dict[str, _UnitMeta] = {
    "program": _UnitMeta("program", True, "pathway", "top6",
                         "the occupations it feeds and their demand"),
    "occupation": _UnitMeta("occupation", True, "occupation_profile", "soc",
                            "its full regional demand, supply, and employers"),
    "college": _UnitMeta("college", True, "coverage", None,
                         "how the sector's programs are covered across the region's colleges"),
}


# ── binding + framing helpers (inline; compare.py does not import forms) ───

def _grain(key: str, ctx: CompareContext) -> str:
    return {"region": ctx.region_g,
            "region_supply": ctx.region_supply_g,
            "gap": f"{ctx.region_g} − {ctx.region_supply_g}",
            "share": f"{ctx.inst_g} ÷ {ctx.region_supply_g}",
            "college": "institutional — a single college in the region",
            "college_share": f"a single college ÷ {ctx.region_supply_g}",
            "statewide": _WAGE_GRAIN,
            "inst": ctx.inst_g}.get(key, ctx.inst_g)


def _bind(c: Criterion, value, ctx: CompareContext) -> QualifiedValue:
    return P.q(c.field, value, granularity=_grain(c.grain, ctx), unit=c.unit,
              vintage=c.vintage(ctx), status="ok" if value is not None else "unavailable")


def _framing(salience) -> Framing:
    return Framing(meaning=C.FORMS["compare"].meaning, salience=salience)


def _licensing(*, licensed=None, not_licensed=None) -> Licensing:
    nl = list(not_licensed or [])
    nl.insert(0, C.FORMS["compare"].guardrail)
    return Licensing(licensed=list(licensed or []), not_licensed=nl)


# ── the engine ─────────────────────────────────────────────────────────────

# Loose-word aliases so a natural unit/criterion resolves to the registry token instead of gating —
# the model reaches for the intuitive word first (eval-observed: 'gap', 'wage', 'sector',
# 'institution'), and the resolution is transparent (the result's sorted_by names the resolved
# criterion). DISCIPLINE: a loose word is aliased for a unit_type ONLY when it maps to a SINGLE
# criterion there — an ambiguous word (program 'wage' → wage_lift/after_2/after_5; any 'supply' →
# two share/level figures) is deliberately left to GATE and enumerate, never a silent guess among
# several (the same rule test_compare_gates_unknown encodes).
_UNIT_ALIAS = {"programs": "program", "occupations": "occupation", "occ": "occupation",
               "colleges": "college", "school": "college", "schools": "college",
               "institution": "college", "institutions": "college"}
_CRIT_ALIAS = {
    "gap": {"program": "addressable_gap", "occupation": "supply_gap"},   # each unit's only gap
    "wage": {"occupation": "median_wage"},        # occupation's only wage; program's 3 wages stay gated
    "wages": {"occupation": "median_wage"},
    "openings": {"occupation": "regional_openings"},
    "growth": {"occupation": "projected_growth"},
    "employment": {"occupation": "regional_employment"},
    "demand": {"program": "addressable_demand"},  # program's only demand figure
}


def compare(member: str, unit_type: str = "program", criterion: str = "",
            sector: str = "") -> AnalysisEnvelope:
    """Rank the analogous units of ``unit_type`` by ``criterion``, showing every admissible criterion
    per unit (the full profile) sorted by the chosen one. v1: ``unit_type='program'`` ranks the
    member's programs in a sector. An invalid unit_type/criterion returns an explicit marker whose
    reason enumerates the registry — the registry is the single source of truth for the surface."""
    ut = (unit_type or "program").strip().lower()
    ut = _UNIT_ALIAS.get(ut, ut)
    crit = (criterion or "").strip().lower()
    if ut not in REGISTRY:
        hint = (" There is no whole-sector unit — use orient for the member's sector portfolio."
                if ut in ("sector", "sectors") else "")
        return gate_envelope("compare", member, sector, marker="unknown",
                             reason=f"Unknown unit type {unit_type!r}. Comparable units: {', '.join(REGISTRY)}.{hint}")
    crits = REGISTRY[ut]
    if not crit:
        crit = next(iter(crits))
    crit = _CRIT_ALIAS.get(crit, {}).get(ut, crit)
    if crit not in crits:
        return gate_envelope("compare", member, sector, marker="unknown",
                             reason=(f"Unknown criterion {criterion!r} for {ut}. Rank {ut}s by: "
                                     f"{', '.join(crits)}."))
    if _UNIT_META[ut].needs_sector and not sector:
        return gate_envelope("compare", member, sector, marker="unknown",
                             reason=f"Comparing {ut}s needs a sector (the {ut} set is scoped to a member×sector).")

    ctx = build_context(member, sector)
    if ctx is None:
        return gate_envelope("compare", member, sector,
                             reason=f"No live coordinate for ({member!r}, {sector!r}).")
    units = list(PEER_SET[ut](ctx))
    if not units:
        return gate_envelope("compare", member, sector, marker="unavailable",
                             reason=(f"{ctx.entry['member_label']} has no {_UNIT_META[ut].noun}s in this "
                                     f"sector to compare."))

    # Compute every criterion per unit (the full profile), then rank by the chosen one.
    computed = [(u, {ck: (c, c.compute(ctx, u)) for ck, c in crits.items()}) for u in units]
    sort_c = crits[crit]
    uid = _UNIT_ID[ut]

    def _key(item):
        v = item[1][crit][1]
        if v is None:                       # gated (e.g. a trend with no baseline) sorts last
            return (1, 0.0, uid(item[0]))
        return (0, -v if sort_c.higher_is_better else v, uid(item[0]))

    computed.sort(key=_key)

    salience = [C.SAL_PROJECTED_NOT_ACTUAL]
    if crit == "enrollment_trend" and len(ctx.enroll_recent) < 2:
        salience.append("small-n-season: fewer than two prior same-season terms — read the "
                        "enrollment trend cautiously.")
    if crit.startswith("wage"):
        salience.append(
            "statewide-pooled wage: these graduate-wage figures pool ALL California completers of the "
            "program's largest award cohort statewide — not just this member's own graduates — and are "
            "medians, never summed. They rank a program on the labor-market value of its credential, "
            "independent of how many the member awards.")

    meta = _UNIT_META[ut]
    label = UNIT_LABEL[ut]

    def _drill_coord(u):
        return coordinate_of(ctx.entry, **({meta.coord_key: uid(u)} if meta.coord_key else {}))

    rows = [Row(label=label(u), values={ck: _bind(c, v, ctx) for ck, (c, v) in vals.items()})
            for (u, vals) in computed[:_TOP_N]]
    more = None
    if len(computed) > _TOP_N:
        nxt = computed[_TOP_N][0]
        more = More(remaining=len(computed) - _TOP_N,
                    drill=C.as_move(meta.drill_form, _drill_coord(nxt),
                                    f"{len(computed) - _TOP_N} more {ut}s to compare."))

    top_u = computed[0][0] if computed else None
    next_moves = [
        C.as_move(meta.drill_form,
                  _drill_coord(top_u) if top_u else coordinate_of(ctx.entry),
                  (f"Drill into {label(top_u)} — {meta.drill_hint}." if (top_u and meta.coord_key)
                   else (f"See {meta.drill_hint}." if top_u else f"Drill into a {meta.noun}."))),
    ]

    coord = coordinate_of(ctx.entry)
    coord.region = ctx.region_disp
    summary = {
        "units_compared": QualifiedValue.ok(len(units), unit=f"{ut}s", source="derived",
                                            granularity=ctx.inst_g),
    }
    return AnalysisEnvelope(
        form="compare", coordinate=coord,
        data=DataBlock(summary=summary, rows=rows, more=more,
                       sorted_by=SortAxis(key=sort_c.key, label=sort_c.label, unit=sort_c.unit,
                                          direction="higher" if sort_c.higher_is_better else "lower")),
        framing=_framing(salience),
        licensing=_licensing(
            licensed=[f"The member's {ut}s in the sector, each with all comparison criteria, ranked by "
                      f"{sort_c.label.lower()}.",
                      "Every criterion is a plain sum-across pool or a native ratio — no weighting, no "
                      "composite; a ranking is defensible because each figure traces to its authority."]),
        next_moves=next_moves,
        view_link=V.view_link("compare", instance_id=ctx.spec.id, member_id=ctx.entry["member_id"],
                              sector_id=ctx.entry["sector_id"], unit_type=ut),
        provenance=P.build_provenance(
            [c.field for c in crits.values()],
            scope_granularity=f"demand {ctx.region_g}; supply {ctx.region_supply_g}; member {ctx.inst_g}; "
                              f"wage {_WAGE_GRAIN}",
            vintages={"demand": P.COE_DEMAND_VINTAGE, "projected_supply": ctx.supply_v,
                      "wage_outcomes": ctx.wage_v}),
    )
