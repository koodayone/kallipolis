"""The four Tier 1 form adapters — the heart of the framing layer.

Each adapter: resolve the (member, sector) coordinate to a ``LandscapeSpec``
(gate if unresolvable), call the SAME deterministic builder ``api.py`` calls, and
re-shape the typed output into an ``AnalysisEnvelope`` — provenance attached from
the engine's own substrate (never invented), Distinguish enforced by separate
named keys, progressive disclosure (summary + top-N + a scoped re-call), framing
(static meaning + computed salience), licensing, catalog-edge next-moves, and the
corroborating dashboard view-link. No engine logic is reimplemented.
"""
from __future__ import annotations

import dataclasses
from typing import Optional

from partnerships.landscape_build import build_landscape
from partnerships.landscape_employers import build_landscape_employers
from partnerships.landscape_programs import (
    build_landscape_occupation,
    build_program_report,
    build_programs_landscape,
)
from partnerships.members import region_member
from partnerships.predicates import (
    CC_SERVABLE_EDUCATION as _CC_SERVABLE_EDUCATION,
    OPENINGS_FLOOR as _OPENINGS_FLOOR,
    WAGE_FLOOR as _WAGE_FLOOR,
)
from partnerships.resolve import resolve, sector_lenses

from mcp_server import canonical as CAN
from mcp_server import catalog as C
from mcp_server import provenance as P
from mcp_server import viewlink as V
from mcp_server.envelope import (
    AnalysisEnvelope,
    Coordinate,
    DataBlock,
    Framing,
    Gate,
    Licensing,
    More,
    NextMove,
    QualifiedValue,
    Row,
    SortAxis,
)
from mcp_server.compare import compare
from mcp_server.engine import select, select_member, supply
from mcp_server.scope import coordinate_of, find_scope, gate_envelope, scope_for, sectors_for_member

_TOP_N = 8  # progressive-disclosure row cap (summary-first; drill on request)


# ── shared helpers ────────────────────────────────────────────────────────

def _regional(region_display: str) -> str:
    return f"regional ({region_display})"


def _institutional(entry: dict, n_colleges: int) -> str:
    return f"institutional — {entry.get('member_kind', 'member')} (Σ {n_colleges} colleges)"


def _awards_window(award_years: list[str]) -> str:
    if not award_years:
        return "DataMart awards — vintage unavailable"
    if len(award_years) == 1:
        return f"DataMart awards — {award_years[0]}"
    return f"DataMart awards — {award_years[0]}…{award_years[-1]}"


def _derived(value, *, unit: str, granularity: str) -> QualifiedValue:
    """A structural count over the graph (member/program cardinality) — not an
    institutional-authority fact, but still Bound so no bare number escapes."""
    return QualifiedValue.ok(value, unit=unit, source="derived", granularity=granularity)


def _framing(form_id: str, salience: list[str]) -> Framing:
    return Framing(meaning=C.FORMS[form_id].meaning, salience=salience)


def _licensing(form_id: str, *, licensed=None, not_licensed=None, gates=None) -> Licensing:
    nl = list(not_licensed or [])
    nl.insert(0, C.FORMS[form_id].guardrail)   # the §1.2 guardrail leads the anti-claims
    return Licensing(licensed=list(licensed or []), not_licensed=nl, gates=list(gates or []))


def _drill(form: str, entry: dict, *, remaining: int,
           soc: Optional[str] = None, top6: Optional[str] = None) -> More:
    tool = C.tool_name(form)   # the drill pointer is a call target — the verb, carrying the entity/lens
    return More(
        remaining=remaining,
        drill=C.as_move(form, coordinate_of(entry, soc=soc, top6=top6),
                        f"{remaining} more rows; re-call {tool} scoped to one row to drill in."),
    )


def _empty_member_sector(form: str, entry: dict, region_display: str) -> AnalysisEnvelope:
    """A VALID coordinate whose member-anchored SOC universe is empty: the member runs no
    active program feeding this sector's qualifying middle-skill occupations, so a generated
    landscape has nothing to show. Surface an explicit marker — NEVER 0-readable 'no demand'
    (the region may well have unmet demand here; this view is scoped to what the member already
    serves, not greenfield occupations). Routes back to orient to pick a served sector."""
    coord = coordinate_of(entry)
    coord.region = region_display
    reason = (f"{entry['member_label']} runs no active program feeding this sector's qualifying "
              f"middle-skill occupations, so a member-anchored {form} view is empty. The region "
              f"may still have unmet demand in this sector — this view is scoped to occupations "
              f"the member already serves, not greenfield ones.")
    return AnalysisEnvelope(
        form=form, coordinate=coord,
        framing=_framing(form, [C.SAL_MEMBER_ANCHORED]),
        licensing=_licensing(form,
                             gates=[Gate(field="member_supply", marker="unavailable",
                                         reason=reason)]),
        next_moves=[C.as_move("orient", coord,
                              "See which sectors this member actually runs programs in.")],
        view_link=V.view_link(form, instance_id=entry["id"], member_id=entry["member_id"],
                              sector_id=entry["sector_id"]),
    )


_ROSTER_N = 12   # named colleges inline per program; the count field discloses any remainder


def _program_roster(colleges, top6: str, granularity: str) -> list[Row]:
    """Top-N named colleges offering a program (Defect 2) — label + Covered/Partial/Gap class
    + projected annual supply, from the ONE canonical roster. A college with no recent supply
    stays in the roster (its class shows the absence) rather than silently dropping the way
    OES-suppressed employers do; the row's count field discloses any remainder beyond top-N."""
    return [Row(label=cell.college, values={
        "coverage": QualifiedValue.ok(cell.coverage, source="datamart", granularity=granularity),
        "projected_supply": P.q("projected_supply", cell.projected, granularity=granularity, unit="completions/yr"),
    }) for cell in CAN.college_roster(colleges, top6)[:_ROSTER_N]]


# ── gap ───────────────────────────────────────────────────────────────────

def _unserved_occupation(entry: dict, soc: str, region_display: str) -> AnalysisEnvelope:
    """A VALID member×sector coordinate whose requested occupation the member feeds no program
    into: the member-anchored gap has no row for it. GATE rather than fall through to the
    served-sector summary (which would misread a sector aggregate as this occupation's gap), and
    route to occupation_profile — the region-derived view that gives the occupation's regional
    demand and gap whether or not the member serves it (its member_supply is then a clean share,
    possibly 0)."""
    coord = coordinate_of(entry, soc=soc)
    coord.region = region_display
    reason = (f"{entry['member_label']} runs no active program feeding this occupation, so a "
              f"member-anchored gap view has no row for it — the sector summary is NOT this "
              f"occupation's figure. See occupation_profile for its regional demand and gap "
              f"(region-derived; this member's own supply shows as its share, which may be 0).")
    return AnalysisEnvelope(
        form="gap", coordinate=coord,
        framing=_framing("gap", [C.SAL_MEMBER_ANCHORED]),
        licensing=_licensing("gap", gates=[Gate(field="gap", marker="unavailable", reason=reason)]),
        next_moves=[C.as_move("occupation_profile", coordinate_of(entry, soc=soc),
                              "The occupation's regional demand, supply, and gap — "
                              "region-derived, not gated to what the member serves.")],
        view_link=V.view_link("gap", instance_id=entry["id"], member_id=entry["member_id"],
                              sector_id=entry["sector_id"], soc=soc),
    )


def analyze_gap(member: str, sector: str, *, soc: Optional[str] = None) -> AnalysisEnvelope:
    sel = select(member, sector)
    if sel is None:
        return gate_envelope("gap", member, sector,
                             reason=f"No live coordinate for ({member!r}, {sector!r}). Confirm the member id and its live sectors via list_institutions.")
    entry, resolved_spec = sel.entry, sel.spec
    land = build_landscape(resolved_spec)   # SOC universe + regional demand (scope-invariant)
    agg = land.aggregate

    # Supply resolves through the ONE canonical resolver (canonical.supply): DataMart
    # 3-yr-avg completions over is_vocational crosswalk feeders — the single supply measure.
    # Regional supply (every college in the member's COE region) is the gap denominator; the
    # member's own supply is its share. All come from the same function, so no sibling tool can
    # disagree. Demand + the SOC set come from the landscape.
    region = sel.region
    member_colleges, region_colleges = sel.member_colleges, sel.region_colleges
    recent = CAN.recent_award_years()

    region_g = _regional(land.region_display)
    inst_g = _institutional(entry, agg.n_colleges)
    region_supply_g = f"regional ({land.region_display}) — all {len(region_colleges)} colleges"
    supply_v = CAN.vintage(recent)
    gap_v = f"{P.COE_DEMAND_VINTAGE} vs {supply_v}"    # supply side now DataMart, not the COE window

    per_soc: dict[str, dict] = {}
    for col in land.colleges:
        for cell in col.cells:
            r = per_soc.get(cell.soc_code)
            if r is None:
                r = per_soc[cell.soc_code] = {
                    "title": cell.title, "openings": cell.annual_openings,
                    "member_supply": supply(sel, over="member", soc=cell.soc_code),
                    "regional_supply": supply(sel, over="region", soc=cell.soc_code)}
            if r["openings"] is None:
                r["openings"] = cell.annual_openings
    for r in per_soc.values():
        r["gap"] = CAN.gap(r["openings"], r["regional_supply"])

    if not per_soc:   # member serves no qualifying occupation here — gate, never 0-readable
        return _empty_member_sector("gap", entry, land.region_display)

    socs = list(per_soc)
    agg_region_supply = CAN.supply_over_socs(region_colleges, socs, spec=resolved_spec)
    summary = {
        "regional_demand": P.q("annual_openings", agg.regional_demand_total,
                               granularity=region_g, unit="openings/yr"),
        "regional_supply": P.q("projected_supply", agg_region_supply,
                               granularity=region_supply_g, unit="completions/yr", vintage=supply_v),
        "member_supply": P.q("projected_supply", CAN.supply_over_socs(member_colleges, socs, spec=resolved_spec),
                             granularity=inst_g, unit="completions/yr", vintage=supply_v),
        "gap": P.q("gap", int(round(agg.regional_demand_total - agg_region_supply)),
                   granularity=f"{region_g} − {region_supply_g}", unit="openings/yr", vintage=gap_v),
    }

    items = sorted(per_soc.items(), key=lambda kv: kv[1]["gap"], reverse=True)
    if soc is not None:
        items = [(s, r) for s, r in items if s == soc]
        if not items:   # member serves this sector but no program feeding THIS occupation:
            return _unserved_occupation(entry, soc, land.region_display)   # gate, don't fall to summary
    window = items if soc is not None else items[:_TOP_N]
    rows = [Row(label=f"{s} {r['title']}", values={
        "regional_demand": P.q("annual_openings", r["openings"], granularity=region_g, unit="openings/yr"),
        "regional_supply": P.q("projected_supply", r["regional_supply"], granularity=region_supply_g, unit="completions/yr", vintage=supply_v),
        "member_supply": P.q("projected_supply", r["member_supply"], granularity=inst_g, unit="completions/yr", vintage=supply_v),
        "gap": P.q("gap", r["gap"], granularity="regional openings − regional supply", unit="openings/yr", vintage=gap_v),
    }) for s, r in window]
    more = None
    if soc is None and len(items) > _TOP_N:
        more = _drill("gap", entry, remaining=len(items) - _TOP_N, soc=items[_TOP_N][0])

    salience = [C.SAL_PROJECTED_NOT_ACTUAL]
    if getattr(resolved_spec, "soc_rule", None) and resolved_spec.soc_rule.active:
        salience.append(C.SAL_MEMBER_ANCHORED)   # generated view: only occupations the member serves
    if 0 < agg.combined_awards < 5 * max(1, agg.n_colleges):
        salience.append(C.SAL_SMALL_N)

    coord = coordinate_of(entry, soc=soc)
    coord.region = land.region_display
    return AnalysisEnvelope(
        form="gap", coordinate=coord,
        data=DataBlock(summary=summary, rows=rows, more=more),
        framing=_framing("gap", salience),
        licensing=_licensing("gap",
                             licensed=["Regional annual openings vs total regional completions feeding the occupation, per occupation.",
                                       "member_supply is this member's own share of that regional supply."],
                             not_licensed=["Supply is a 3-yr average of DataMart completions (All Awards) over the occupation's CTE feeder programs — a multi-year projection, not a single year."]),
        next_moves=C.build_next_moves("gap", entry, soc=soc),
        view_link=V.view_link("gap", instance_id=sel.instance_id, member_id=entry["member_id"],
                              sector_id=entry["sector_id"], soc=soc),
        provenance=P.build_provenance(
            ["annual_openings", "projected_supply", "gap"],
            scope_granularity=f"demand {region_g}; supply {region_supply_g}; member share {inst_g}",
            vintages={"demand": P.COE_DEMAND_VINTAGE, "projected_supply": supply_v}),
    )


# ── coverage ──────────────────────────────────────────────────────────────

def analyze_coverage(member: str, sector: str) -> AnalysisEnvelope:
    sel = select(member, sector)
    if sel is None:
        return gate_envelope("coverage", member, sector,
                             reason=f"No live coordinate for ({member!r}, {sector!r}). Confirm the member id and its live sectors via list_institutions.")
    entry, rspec = sel.entry, sel.spec
    member_colleges = sel.member_colleges
    pl = build_programs_landscape(rspec)
    if not pl.tops:   # member offers no program in this sector — gate, never 0-readable
        return _empty_member_sector("coverage", entry, pl.region_display)
    inst_g = _institutional(entry, pl.n_colleges)
    supply_v = CAN.vintage(CAN.recent_award_years())

    covered = partial = uncovered = 0
    if pl.matrix:
        # One coverage predicate (quantities.coverage). NOTE: this preserves the current
        # ruleless (enrolled-OR-awarded) classification. On rule-bearing instances (BACCC,
        # sector-derived SMCCD) the dashboard matrix uses awards_only — an enrolled-but-not-
        # awarding cell is a gap, not partial — and this MCP count still diverges from it.
        # Passing awards_only=pl.matrix.coverage_awards_only closes that gap; deferred to the
        # S7 sign-off because it moves the reported counts on those instances.
        for c in pl.matrix.cells:
            cls = CAN.coverage(c.enrolled, c.projected)
            if cls == "covered":
                covered += 1
            elif cls == "partial":
                partial += 1
            else:
                uncovered += 1

    summary = {
        "member_colleges": _derived(pl.n_colleges, unit="colleges", granularity=inst_g),
        "programs": _derived(len(pl.tops), unit="TOP6 programs", granularity=inst_g),
        "covered_cells": P.q("coverage", covered, granularity=inst_g, unit="college×program cells", vintage=supply_v),
        "partial_cells": P.q("coverage", partial, granularity=inst_g, unit="college×program cells", vintage=supply_v),
        "gap_cells": P.q("coverage", uncovered, granularity=inst_g, unit="college×program cells", vintage=supply_v),
    }

    tops = sorted(pl.tops, key=lambda t: t.projected_supply, reverse=True)
    rows = [Row(label=f"{t.top6} {t.name}", values={
        "projected_supply": P.q("projected_supply", t.projected_supply, granularity=inst_g, unit="completions/yr", vintage=supply_v),
        "enrollment": P.q("enrollment", t.enrollment_total, granularity=inst_g, unit="enrolled"),
        "colleges_with_program": _derived(CAN.colleges_with_program(member_colleges, t.top6),
                                          unit="colleges", granularity=inst_g),
        "colleges_actively_awarding": _derived(CAN.colleges_actively_awarding(member_colleges, t.top6),
                                               unit="colleges (recent)", granularity=inst_g),
        "occupations_fed": _derived(t.soc_count, unit="SOCs", granularity="TOP→CIP→SOC crosswalk"),
    }, roster=_program_roster(member_colleges, t.top6, inst_g)) for t in tops[:_TOP_N]]
    more = _drill("coverage", entry, remaining=len(tops) - _TOP_N) if len(tops) > _TOP_N else None

    coord = coordinate_of(entry)
    coord.region = pl.region_display
    return AnalysisEnvelope(
        form="coverage", coordinate=coord,
        data=DataBlock(summary=summary, rows=rows, more=more),
        framing=_framing("coverage", []),
        licensing=_licensing("coverage",
                             licensed=["Covered / Partial / Gap classification of each (college, program) cell."],
                             not_licensed=["A 'gap' cell is no realized supply — not a claim about need or intent."]),
        next_moves=C.build_next_moves("coverage", entry),
        view_link=V.view_link("coverage", instance_id=sel.instance_id, member_id=entry["member_id"],
                              sector_id=entry["sector_id"]),
        provenance=P.build_provenance(
            ["coverage", "projected_supply", "enrollment"],
            scope_granularity=inst_g,
            vintages={"projected_supply": supply_v}),
    )


# ── pathway (program ↔ occupation, exactly-one-of) ────────────────────────

def analyze_pathway(member: str, sector: str, *, program: Optional[str] = None,
                    occupation: Optional[str] = None) -> AnalysisEnvelope:
    sel = select(member, sector)
    if sel is None:
        return gate_envelope("pathway", member, sector,
                             reason=f"No live coordinate for ({member!r}, {sector!r}). Confirm the member id and its live sectors via list_institutions.")
    entry = sel.entry

    if bool(program) == bool(occupation):   # both or neither
        coord = coordinate_of(entry)
        return AnalysisEnvelope(
            form="pathway", coordinate=coord,
            framing=_framing("pathway", []),
            licensing=Licensing(gates=[Gate(
                field="program|occupation", marker="unknown",
                reason="Provide exactly one of program (a TOP6 code) or occupation (a SOC code).")]),
            next_moves=C.build_next_moves("pathway", entry))

    if program:
        # Program-anchor drill. Occupations resolve through the CANONICAL crosswalk
        # (CAN.program_socs = is_vocational top6_to_soc, sector-bounded) so the program's addressable
        # demand here EQUALS the figure sector_overview shows for the same program — referential
        # integrity. The occupations it feeds are ranked by DESIRABILITY (opportunity = openings ×
        # median wage) with the regional gap for each. The natural descent is to a single occupation.
        from ontology.regions import COE_REGION_DISPLAY
        from ontology.schema import get_driver
        from partnerships.graph_reads import regional_demand
        from partnerships.sectors import SECTORS

        rspec = sel.spec
        pr = build_program_report(program, None, spec=rspec)   # program display name + bridging CIPs
        member_colleges = list(rspec.colleges)
        region = rspec.resolve_region()
        region_colleges = list(region_member(region).colleges)
        region_disp = COE_REGION_DISPLAY.get(region, region)
        sector_socs = list(SECTORS[entry["sector_id"]].addressable_socs)
        prog_socs = sorted(CAN.program_socs(program, within=sector_socs))
        with get_driver().session() as session:
            demand = regional_demand(session, region, prog_socs)
        demand_by_soc = {s: (d.get("annual_openings") or 0) for s, d in demand.items()}
        _, addressable = CAN.addressable_demand(program, sector_socs, demand_by_soc)
        recent = CAN.recent_award_years()
        supply_v = CAN.vintage(recent)
        region_g = _regional(region_disp)
        region_supply_g = f"regional ({region_disp}) — all {len(region_colleges)} colleges"
        inst_g = _institutional(entry, len(member_colleges))
        gap_v = f"{P.COE_DEMAND_VINTAGE} vs {supply_v}"
        n_cips = len(pr.crosswalk.cips) if pr.crosswalk else 0
        summary = {
            "program": QualifiedValue.ok(pr.name, source="datamart", granularity="TOP6 program"),
            "member_supply": P.q("projected_supply", CAN.supply_over_tops(member_colleges, [program]),
                                 granularity=inst_g, unit="completions/yr", vintage=supply_v),
            "addressable_demand": P.q("annual_openings", addressable,
                                      granularity=f"{region_g} — the occupations this program feeds", unit="openings/yr"),
            "occupations_fed": _derived(len(prog_socs), unit="SOCs", granularity="TOP→CIP→SOC crosswalk (in sector)"),
            "bridging_cips": _derived(n_cips, unit="CIPs", granularity="TOP→CIP→SOC crosswalk"),
        }
        occ_rows = []
        for soc in prog_socs:
            d = demand.get(soc, {})
            openings = d.get("annual_openings")
            if not openings:
                continue
            occ_rows.append((soc, d.get("title") or soc, openings, d.get("annual_wage"),
                             CAN.gap(openings, CAN.supply(region_colleges, soc, spec=rspec))))
        occ_rows.sort(key=lambda r: (r[2] or 0, r[3] or 0), reverse=True)   # by openings; wage breaks ties
        rows = [Row(label=f"{soc} {title}", values={
            "annual_openings": P.q("annual_openings", openings, granularity=region_g, unit="openings/yr"),
            "annual_wage": P.q("annual_wage", wage, granularity=region_g, unit="USD/yr (occ. median)"),
            "gap": P.q("gap", g, granularity=f"{region_g} − {region_supply_g}", unit="openings/yr", vintage=gap_v),
        }) for (soc, title, openings, wage, g) in occ_rows[:_TOP_N]]
        more = _drill("pathway", entry, remaining=len(occ_rows) - _TOP_N, top6=program) if len(occ_rows) > _TOP_N else None
        salience = [C.SAL_LOSSY_CROSSWALK] if len(prog_socs) >= 4 else []
        top_occ = occ_rows[0] if occ_rows else None
        next_moves = [
            C.as_move("occupation_profile",
                      coordinate_of(entry, soc=top_occ[0]) if top_occ else coordinate_of(entry, top6=program),
                      (f"Drill into a desirable occupation — e.g. {top_occ[0]} {top_occ[1]} — its "
                       f"full demand, who trains for it, and who hires." if top_occ else
                       "Drill into one of these occupations for its full picture.")),
            C.as_move("regional_employers",
                      coordinate_of(entry, soc=top_occ[0]) if top_occ else coordinate_of(entry),
                      "See the regional employers hiring for these occupations."),
        ]
        coord = coordinate_of(entry, top6=program)
        coord.region = region_disp
        return AnalysisEnvelope(
            form="pathway", coordinate=coord,
            data=DataBlock(summary=summary, rows=rows, more=more,
                           sorted_by=SortAxis(key="annual_openings", label="Annual openings",
                                              unit="openings/yr", direction="higher")),
            framing=_framing("pathway", salience),
            licensing=_licensing("pathway",
                                 licensed=["The occupations this TOP6 program prepares students for, ranked by annual openings — with median wage and the regional gap shown alongside each — and the program's own supply.",
                                           "Addressable demand is the sum-across pool the program competes for — a graduate is qualified for these occupations, not assigned to one."]),
            next_moves=next_moves,
            view_link=V.view_link("pathway", instance_id=sel.instance_id, member_id=entry["member_id"],
                                  sector_id=entry["sector_id"], top6=program),
            provenance=P.build_provenance(
                ["annual_openings", "annual_wage", "projected_supply", "gap"],
                scope_granularity=f"demand {region_g}; supply {region_supply_g}; member {inst_g}",
                vintages={"demand": P.COE_DEMAND_VINTAGE, "projected_supply": supply_v}),
        )

    # occupation
    # supply/gap resolve through canonical.supply — coherent with analyze_gap (this tool
    # previously computed gap = regional − INSTITUTIONAL supply, the exact conflation the
    # gap description forbids; fixed here).
    rspec = sel.spec
    occ = build_landscape_occupation(occupation, spec=rspec, college=None, include_employers=False)
    member_colleges = rspec.colleges
    region_colleges = region_member(rspec.resolve_region()).colleges
    recent = CAN.recent_award_years()
    region_g = _regional(occ.region_display)
    inst_g = _institutional(entry, len(member_colleges))
    region_supply_g = f"regional ({occ.region_display}) — all {len(region_colleges)} colleges"
    supply_v = CAN.vintage(recent)
    gap_v = f"{P.COE_DEMAND_VINTAGE} vs {supply_v}"    # supply side now DataMart, not the COE window
    regional_supply = CAN.supply(region_colleges, occupation, spec=rspec)
    member_supply = CAN.supply(member_colleges, occupation, spec=rspec)
    summary = {
        "regional_demand": P.q("annual_openings", occ.annual_openings, granularity=region_g, unit="openings/yr"),
        "annual_wage": P.q("annual_wage", occ.annual_wage, granularity=region_g, unit="USD/yr (occ. median)"),
        "regional_supply": P.q("projected_supply", regional_supply, granularity=region_supply_g, unit="completions/yr", vintage=supply_v),
        "member_supply": P.q("projected_supply", member_supply, granularity=inst_g, unit="completions/yr", vintage=supply_v),
        "gap": P.q("gap", CAN.gap(occ.annual_openings, regional_supply),
                   granularity=f"{region_g} − {region_supply_g}", unit="openings/yr", vintage=gap_v),
    }
    tops = sorted(occ.feeding_tops, key=lambda t: t.projected_supply, reverse=True)
    rows = [Row(label=f"{t.top6} {t.name}", values={
        "projected_supply": P.q("projected_supply", t.projected_supply, granularity=inst_g, unit="completions/yr", vintage=supply_v),
        "enrollment": P.q("enrollment", t.enrollment_total, granularity=inst_g, unit="enrolled"),
        "colleges_with_program": _derived(CAN.colleges_with_program(member_colleges, t.top6),
                                          unit="colleges", granularity=inst_g),
        "colleges_actively_awarding": _derived(CAN.colleges_actively_awarding(member_colleges, t.top6),
                                               unit="colleges (recent)", granularity=inst_g),
    }, roster=_program_roster(member_colleges, t.top6, inst_g)) for t in tops[:_TOP_N]]
    more = _drill("pathway", entry, remaining=len(tops) - _TOP_N, soc=occupation) if len(tops) > _TOP_N else None
    salience = [C.SAL_PROJECTED_NOT_ACTUAL, C.SAL_LOSSY_CROSSWALK] if len(occ.feeding_tops) >= 4 else [C.SAL_PROJECTED_NOT_ACTUAL]
    coord = coordinate_of(entry, soc=occupation)
    coord.region = occ.region_display
    return AnalysisEnvelope(
        form="pathway", coordinate=coord,
        data=DataBlock(summary=summary, rows=rows, more=more),
        framing=_framing("pathway", salience),
        licensing=_licensing("pathway",
                             licensed=["The programs that feed this occupation, the regional demand for it, and the regional supply gap.",
                                       "member_supply is this member's share of that regional supply."]),
        next_moves=C.build_next_moves("pathway", entry, soc=occupation),
        view_link=V.view_link("pathway", instance_id=sel.instance_id, member_id=entry["member_id"],
                              sector_id=entry["sector_id"], soc=occupation),
        provenance=P.build_provenance(
            ["annual_openings", "annual_wage", "projected_supply", "gap"],
            scope_granularity=f"demand {region_g}; supply {region_supply_g}; member share {inst_g}",
            vintages={"demand": P.COE_DEMAND_VINTAGE, "projected_supply": supply_v}),
    )


# ── regional employers ─────────────────────────────────────────────────────

def analyze_regional_employers(member: str, sector: str, *, soc: Optional[str] = None) -> AnalysisEnvelope:
    sel = select(member, sector)
    if sel is None:
        return gate_envelope("regional_employers", member, sector,
                             reason=f"No live coordinate for ({member!r}, {sector!r}). Confirm the member id and its live sectors via list_institutions.")
    entry = sel.entry
    er = build_landscape_employers(sel.spec)
    region_g = _regional(er.region_display)

    employers = er.employers
    if soc is not None:
        employers = [e for e in employers if soc in e.socs]
    ranked = sorted(employers, key=lambda e: e.relevance, reverse=True)

    summary = {
        "candidate_employers": P.q("candidate_employers", er.total, granularity=region_g, unit="employers"),
        "shown": _derived(min(er.shown, len(ranked)), unit="employers plotted", granularity=region_g),
    }
    rows = [Row(label=(e.display_name or e.name), values={
        "employer_relevance": P.q("employer_relevance", round(e.relevance, 3),
                                  granularity=region_g, unit="Σ OES staffing share"),
        "occupations_hired": _derived(e.soc_count, unit="target SOCs", granularity="BLS OES"),
    }) for e in ranked[:_TOP_N]]
    more = _drill("regional_employers", entry, remaining=len(ranked) - _TOP_N, soc=soc) if len(ranked) > _TOP_N else None

    coord = coordinate_of(entry, soc=soc)
    coord.region = er.region_display
    return AnalysisEnvelope(
        form="regional_employers", coordinate=coord,
        data=DataBlock(summary=summary, rows=rows, more=more),
        framing=_framing("regional_employers", []),
        licensing=_licensing("regional_employers",
                             licensed=["Regional employers ranked by OES staffing share for the target occupations."],
                             not_licensed=["'shown' is a geocoded shortlist, not the whole candidate pool ('total')."]),
        next_moves=C.build_next_moves("regional_employers", entry, soc=soc),
        view_link=V.view_link("regional_employers", instance_id=sel.instance_id, member_id=entry["member_id"],
                              sector_id=entry["sector_id"]),
        provenance=P.build_provenance(
            ["candidate_employers", "employer_relevance"],
            scope_granularity=region_g,
            vintages={"employer_relevance": P.OES_VINTAGE}),
    )


# ── occupation profile (occupation-first entry; sector-agnostic) ───────────

_OCC_EMP_N = 3  # top employers surfaced inline; the full shed is a next-move


def occupation_profile(member: str, occupation: str) -> AnalysisEnvelope:
    """The regional picture of one occupation, entered from the institution (which
    supplies the region), not a sector. Composes: regional demand (openings, wage,
    employment, growth) · the region's crosswalk feeders + COE projected supply
    (regional total and the member's share) + the gap · the top regional employers
    · the sector(s) the occupation belongs to. Sector-agnostic — feeders come from
    the raw TOP→SOC crosswalk over the region's offered programs, not a sector's
    scoped TOP set."""
    from partnerships.members import region_member
    from partnerships.graph_reads import regional_demand
    from partnerships.sectors import SECTORS
    from ontology.crosswalks import load_top_titles
    from ontology.regions import COE_REGION_DISPLAY
    from ontology.schema import get_driver

    sel = select_member(member)
    if sel is None:
        return gate_envelope("occupation_profile", member, "",
                             reason=(f"No institution matching {member!r}. Use list_institutions (optionally with a name filter) to find its member id, then retry with that id — the tools take the id, not the display name."
                                     if not sectors_for_member(member) else
                                     f"Could not resolve institution {member!r}."))
    sects = sectors_for_member(member)      # the occupation's classifying sectors, used below
    entry, spec0 = sel.entry, sel.spec
    region, region_disp = sel.region, sel.region_display
    member_colleges, region_colleges = sel.member_colleges, sel.region_colleges

    with get_driver().session() as session:
        demand = regional_demand(session, region, [occupation]).get(occupation, {})
        if not demand:
            return gate_envelope(
                "occupation_profile", member, "", marker="unavailable",
                reason=f"No regional demand data for occupation {occupation!r} in {region_disp}.")
        edu_row = session.run(
            "MATCH (o:Occupation {soc_code:$s}) RETURN o.education_level AS e", s=occupation).single()
        emp_rows = session.run(
            "MATCH (r:Region {name:$region})<-[:IN_MARKET]-(e:Employer)-[h:HIRES_FOR]->"
            "(o:Occupation {soc_code:$s}) "
            "RETURN coalesce(e.display_name, e.name) AS name, h.pct_total AS pct "
            "ORDER BY pct DESC, name ASC LIMIT $n", region=region, s=occupation, n=_OCC_EMP_N).data()

    education = edu_row["e"] if edu_row else None
    # Supply + feeders resolve through the ONE canonical resolver — is_vocational
    # crosswalk feeders (excludes non-CTE noise like Liberal Arts → Machinists) and
    # DataMart 3-yr-avg completions, coherent with the gap/pathway tools.
    recent = CAN.recent_award_years()
    regional_supply = CAN.supply(region_colleges, occupation)
    member_supply = CAN.supply(member_colleges, occupation)
    openings = demand.get("annual_openings")
    gap = CAN.gap(openings, regional_supply)
    in_sectors = [SECTORS[sid].label for sid in SECTORS if occupation in set(SECTORS[sid].socs)]

    region_g = _regional(region_disp)
    region_supply_g = f"regional ({region_disp}) — all {len(region_colleges)} colleges"
    inst_g = _institutional(entry, len(member_colleges))
    supply_v = CAN.vintage(recent)
    gap_v = f"{P.COE_DEMAND_VINTAGE} vs {supply_v}"    # supply side now DataMart, not the COE window
    titles = load_top_titles()

    summary = {
        "occupation_title": QualifiedValue.ok(demand.get("title") or occupation,
                                              source="coe", granularity=f"SOC {occupation}"),
        "typical_education": (P.q("typical_education", education, granularity=f"SOC {occupation}")
                              if education else
                              P.q("typical_education", None, granularity=f"SOC {occupation}",
                                  status="unavailable")),
        "annual_openings": P.q("annual_openings", openings, granularity=region_g, unit="openings/yr"),
        "annual_wage": P.q("annual_wage", demand.get("annual_wage"), granularity=region_g,
                           unit="USD/yr (occ. median)"),
        "regional_employment": P.q("regional_employment", demand.get("employment"),
                                   granularity=region_g, unit="jobs"),
        "growth_rate": P.q("growth_rate", demand.get("growth_rate"), granularity=region_g, unit="5-yr %"),
        "regional_supply": P.q("projected_supply", regional_supply, granularity=region_supply_g,
                               unit="completions/yr", vintage=supply_v),
        "member_supply": P.q("projected_supply", member_supply, granularity=inst_g,
                             unit="completions/yr", vintage=supply_v),
        "gap": P.q("gap", gap, granularity=f"{region_g} − {region_supply_g}", unit="openings/yr",
                   vintage=gap_v),
    }
    if emp_rows:
        summary["top_employers"] = QualifiedValue.ok(
            ", ".join(e["name"] for e in emp_rows), source="graph_bls",
            granularity=f"regional ({region_disp}) — top {len(emp_rows)} by OES staffing share")

    # Supporting programs = the SOC's ACTIVE feeders — is_vocational crosswalk feeders with a
    # completer over the recent window (matches program_pathways' builder gate, so a dormant
    # program on the books like 123000 Nursing is excluded here exactly as it is there).
    # Counts are PROGRAM-grain via the ONE canonical roster (fixes the course-based undercount).
    supporting = sorted(CAN.active_feeders(region_colleges, occupation),
                        key=lambda t: (-CAN.colleges_actively_awarding(region_colleges, t),
                                       -CAN.colleges_with_program(region_colleges, t), t))
    rows = [Row(label=f"{t} {titles.get(t, '')}".strip(), values={
                "colleges_with_program": _derived(CAN.colleges_with_program(region_colleges, t),
                                                  unit="colleges", granularity=region_supply_g),
                "colleges_actively_awarding": _derived(CAN.colleges_actively_awarding(region_colleges, t),
                                                       unit="colleges (recent)", granularity=region_supply_g),
            }, roster=_program_roster(region_colleges, t, region_supply_g)) for t in supporting[:_TOP_N]]

    # A resolvable coordinate for the view-link + next-moves: the occupation's own
    # sector that the member runs, else the member's first live sector.
    member_sids = {e["sector_id"] for e in sects}
    occ_sids = [sid for sid in SECTORS if occupation in set(SECTORS[sid].socs)]
    nav_sid = next((sid for sid in occ_sids if sid in member_sids), sects[0]["sector_id"])
    nav_entry = find_scope(entry["member_id"], nav_sid) or entry
    coord = coordinate_of(nav_entry, soc=occupation)
    coord.region = region_disp

    licensed = ["Regional demand for the occupation vs total regional projected completions feeding it."]
    licensed.append(
        f"Classified in the {', '.join(in_sectors)} sector(s), by the region's sector definitions."
        if in_sectors else
        "Not classified as middle-skill in the region's sector definitions.")

    return AnalysisEnvelope(
        form="occupation_profile", coordinate=coord,
        data=DataBlock(summary=summary, rows=rows),
        framing=_framing("occupation_profile",
                         [C.SAL_LOSSY_CROSSWALK] if len(supporting) >= 4 else []),
        licensing=_licensing("occupation_profile", licensed=licensed),
        next_moves=[   # form = the verb the model routes to; the coordinate carries entity/lens
            C.as_move("regional_employers", coord,
                      "See the full set of regional employers hiring for this occupation."),
            C.as_move("gap", coordinate_of(nav_entry),
                      "See the whole supply–demand gap for this sector."),
        ],
        view_link=V.view_link("occupation_profile", instance_id=nav_entry["id"],
                              member_id=nav_entry["member_id"], sector_id=nav_entry["sector_id"],
                              soc=occupation),
        provenance=P.build_provenance(
            ["annual_openings", "annual_wage", "growth_rate", "regional_employment",
             "projected_supply", "gap"],
            scope_granularity=f"demand {region_g}; supply {region_supply_g}; member share {inst_g}",
            vintages={"demand": P.COE_DEMAND_VINTAGE, "projected_supply": supply_v}),
    )


# ── unmet demand (greenfield gaps; member-scoped, sector-agnostic) ─────────

# The quality-demand gate — three explicit, legible, tunable judgment thresholds (plus the
# PROMOTION_SOCS not-trainable exclusion the gap view already applies). A greenfield
# occupation (member supply == 0, not a promotion role) is surfaced ONLY if it clears ALL THREE.
# The greenfield gates (_CC_SERVABLE_EDUCATION / _WAGE_FLOOR / _OPENINGS_FLOOR) are the versioned
# predicate set — imported at the top of this module from partnerships.predicates (K2 single home).


def unmet_demand(member: str) -> AnalysisEnvelope:
    """Greenfield high-opportunity gaps: the occupations the member's region DEMANDS but
    the member supplies ZERO completers for — regional demand with no local pipeline.
    Sector-agnostic (the region is derived from the institution, exactly as
    occupation_profile does it); filtered to community-college-servable education
    (_CC_SERVABLE_EDUCATION), a living-wage floor (_WAGE_FLOOR) and a meaningful-openings
    floor (_OPENINGS_FLOOR), then ranked by opportunity (annual openings × median wage).
    The complement of the member-anchored gap view: gap is scoped to occupations the
    member already serves, this surfaces exactly the ones it does not."""
    from ontology.regions import COE_REGION_DISPLAY
    from ontology.schema import get_driver
    from partnerships.sectors import PROMOTION_SOCS

    # Resolve member → region + colleges WITHOUT a sector (occupation_profile's path):
    # any live sector suffices to obtain the spec, from which the region and the member's
    # colleges derive. An institution that matches no coordinate gates back to Tier 0.
    sel = select_member(member)
    if sel is None:
        return gate_envelope("unmet_demand", member, "",
                             reason=(f"No institution matching {member!r}. Use list_institutions (optionally with a name filter) to find its member id, then retry with that id — the tools take the id, not the display name."
                                     if not sectors_for_member(member) else
                                     f"Could not resolve institution {member!r}."))
    entry, spec0 = sel.entry, sel.spec
    region, region_disp = sel.region, sel.region_display
    member_colleges = sel.member_colleges

    with get_driver().session() as session:
        demand_rows = session.run(
            "MATCH (rg:Region {name:$region})-[d:DEMANDS]->(o:Occupation) "
            "RETURN o.soc_code AS soc, o.title AS title, o.education_level AS edu, "
            "d.annual_openings AS openings, d.annual_wage AS wage, d.growth_rate AS growth",
            region=region).data()

    recent = CAN.recent_award_years()
    supply_v = CAN.vintage(recent)
    region_g = _regional(region_disp)
    inst_g = _institutional(entry, len(member_colleges))

    # Greenfield + quality gate. Supply resolves through the ONE canonical resolver
    # (CAN.supply): member supply == 0 ⇔ no completer over the occupation's is_vocational
    # feeders feeds it — the same function the gap tool uses, so no sibling tool can disagree
    # about zero-supply. An occupation the member already supplies (>0) is not greenfield.
    survivors: list[dict] = []
    for r in demand_rows:
        if CAN.supply(member_colleges, r["soc"]) != 0:
            continue
        if r["soc"] in PROMOTION_SOCS:
            continue    # supervisor/manager/promotion roles are reached by experience, not a
                        # program a CC can launch — excluded exactly as the member gap view does,
                        # so "greenfield" never suggests a curriculum that can't exist.
        if r["edu"] not in _CC_SERVABLE_EDUCATION:
            continue
        if (r["wage"] or 0) < _WAGE_FLOOR:
            continue
        if (r["openings"] or 0) < _OPENINGS_FLOOR:
            continue
        survivors.append(r)
    survivors.sort(key=lambda r: (r["openings"] or 0, r["wage"] or 0), reverse=True)   # by openings; wage breaks ties
    n_unmet = len(survivors)

    # Greenfield is member-wide across ALL the member's sectors, so the coordinate carries NO sector —
    # navigate(lens=greenfield) drops any sector it was handed (greenfield is not sector-scoped), and a
    # sector on the coordinate would falsely imply the list was filtered to it (the diagnosis mislabel).
    coord = coordinate_of(entry)
    coord.region = region_disp
    coord.sector, coord.sector_label = "", ""

    summary = {
        "n_unmet": _derived(n_unmet, unit="occupations",
                            granularity=f"{region_g} demand unserved by {inst_g}"),
        "member_colleges": _derived(len(member_colleges), unit="colleges", granularity=inst_g),
    }

    rows = [Row(label=f"{r['soc']} {r['title']}", values={
        "annual_openings": P.q("annual_openings", r["openings"], granularity=region_g, unit="openings/yr"),
        "annual_wage": P.q("annual_wage", r["wage"], granularity=region_g, unit="USD/yr (occ. median)"),
        "growth_rate": (P.q("growth_rate", r["growth"], granularity=region_g, unit="5-yr %")
                        if r["growth"] is not None else
                        P.q("growth_rate", None, granularity=region_g, unit="5-yr %", status="unavailable")),
        "typical_education": P.q("typical_education", r["edu"], granularity=f"SOC {r['soc']}"),
        # member_supply resolves through CAN.supply — 0 by the greenfield gate, stated (not
        # hardcoded) so the zero is self-evidently the resolver's, not an invented number.
        "member_supply": P.q("projected_supply", CAN.supply(member_colleges, r["soc"]),
                             granularity=inst_g, unit="completions/yr", vintage=supply_v),
    }) for r in survivors[:_TOP_N]]

    more = None
    if n_unmet > _TOP_N:
        # unmet_demand cannot be re-scoped to one row (it is member-only), so the drill points
        # at occupation_profile for the first occupation past the cap — the callable entry to
        # any surfaced greenfield role.
        nxt = survivors[_TOP_N]["soc"]
        more = More(
            remaining=n_unmet - _TOP_N,
            drill=C.as_move("occupation_profile", coordinate_of(entry, soc=nxt),
                            (f"{n_unmet - _TOP_N} more greenfield occupations; "
                             f"navigate to any surfaced SOC drills into one.")))

    if n_unmet == 0:
        licensed = [f"No community-college-servable, living-wage (≥ ${_WAGE_FLOOR:,}), "
                    f"meaningful-demand (≥ {_OPENINGS_FLOOR} openings/yr) occupation the "
                    f"{region_disp} region demands is currently unserved by "
                    f"{entry['member_label']}: every quality greenfield role already has local "
                    f"supply, or none clears the thresholds. This is an explicit empty result, "
                    f"not a claim the region has no unmet demand at other education/wage levels."]
    else:
        licensed = ["The occupations this member's region demands that the member currently "
                    "graduates no completers for, filtered to community-college-servable "
                    f"education, living-wage (≥ ${_WAGE_FLOOR:,}), and meaningful-demand "
                    f"(≥ {_OPENINGS_FLOOR} openings/yr) roles, ranked by annual openings "
                    "(median wage shown alongside each)."]
    not_licensed = ["It does not assert the member SHOULD launch these — only that regional "
                    "demand exists and the member's own supply is zero; feasibility, cost, "
                    "and mission fit are out of scope.",
                    "'member supply == 0' is a 3-yr-average DataMart figure over the occupation's "
                    "is_vocational feeders — a program with enrollment but no completer in the "
                    "window reads as zero here, and locally-approved certificates are excluded."]

    top_soc = survivors[0]["soc"] if survivors else None
    return AnalysisEnvelope(
        form="unmet_demand", coordinate=coord,
        data=DataBlock(summary=summary, rows=rows, more=more,
                       sorted_by=SortAxis(key="annual_openings", label="Annual openings",
                                          unit="openings/yr", direction="higher")),
        framing=_framing("unmet_demand", [C.SAL_PROJECTED_NOT_ACTUAL, C.SAL_LOSSY_CROSSWALK]),
        licensing=_licensing("unmet_demand", licensed=licensed, not_licensed=not_licensed),
        next_moves=C.build_next_moves("unmet_demand", entry, soc=top_soc),
        # No dashboard view corroborates a region-wide greenfield list — view_link returns an
        # explicit 'unavailable' marker (unmet_demand is unmapped in viewlink), never a broken link.
        view_link=V.view_link("unmet_demand", instance_id=entry["id"],
                              member_id=entry["member_id"], sector_id=entry["sector_id"]),
        provenance=P.build_provenance(
            ["annual_openings", "annual_wage", "growth_rate", "typical_education", "projected_supply"],
            scope_granularity=f"demand {region_g}; supply {inst_g}",
            vintages={"demand": P.COE_DEMAND_VINTAGE, "projected_supply": supply_v}),
    )


# ── member portfolio (member-anchor orientation; the TOP of the descent) ───

def member_portfolio(member: str) -> AnalysisEnvelope:
    """The member-anchor orientation — the top of the descent, ONE call for the whole institution
    across every sector it runs, so a portfolio question never has to loop a sector tool. Per
    sector: total regional demand vs the region's projected completions, the member's own supply
    and its share, and the gap (one row each) — plus an institution-wide total over the DEDUPED
    union of all its sectors' occupations (an occupation in two sectors counted once). Pure
    Regime-A sums; sector-WIDE per row. The per-sector and per-occupation views are turn-by-turn
    drills the practitioner chooses (via next-moves), not steps taken here."""
    from ontology.regions import COE_REGION_DISPLAY
    from ontology.schema import get_driver
    from partnerships.graph_reads import regional_demand
    from partnerships.sectors import SECTORS

    sel = select_member(member)
    if sel is None:
        return gate_envelope("member_portfolio", member, "",
                             reason=(f"No institution matching {member!r}. Use list_institutions (optionally with a name filter) to find its member id, then retry with that id — the tools take the id, not the display name."
                                     if not sectors_for_member(member) else
                                     f"Could not resolve institution {member!r}."))
    sects = sectors_for_member(member)
    entry, spec0 = sel.entry, sel.spec
    region, region_disp = sel.region, sel.region_display
    member_colleges, region_colleges = sel.member_colleges, sel.region_colleges

    # Each sector's occupations, and the DISTINCT union across sectors (Regime A across sectors too).
    sector_socs = {e["sector_id"]: list(SECTORS[e["sector_id"]].addressable_socs) for e in sects}
    all_socs = sorted({s for socs in sector_socs.values() for s in socs})

    # Each sector's canonical spec — the SAME in_scope feeder rule sector_overview resolves — so a
    # per-sector row below EQUALS its sector_overview drill, and the institution-wide total shares
    # that rule (one voice: the member-anchor orientation and the sector drill can't disagree on a
    # sector's supply/gap). resolve() is cached per (member, sector).
    sector_spec: dict = {}
    for e in sects:
        r = scope_for(member, e["sector_id"])
        sector_spec[e["sector_id"]] = resolve(r[0]) if r else None
    sector_specs = [(sector_socs[e["sector_id"]], sector_spec[e["sector_id"]]) for e in sects]

    with get_driver().session() as session:
        demand = regional_demand(session, region, all_socs)   # one query for the union

    recent = CAN.recent_award_years()
    supply_v = CAN.vintage(recent)
    region_g = _regional(region_disp)
    region_supply_g = f"regional ({region_disp}) — all {len(region_colleges)} colleges"
    inst_g = _institutional(entry, len(member_colleges))
    gap_v = f"{P.COE_DEMAND_VINTAGE} vs {supply_v}"

    def demand_sum(socs):
        return int(round(sum((demand.get(s, {}).get("annual_openings") or 0) for s in socs)))

    total_demand = demand_sum(all_socs)
    total_regional_supply = CAN.supply_over_sector_specs(region_colleges, sector_specs)
    total_member_supply = CAN.supply_over_sector_specs(member_colleges, sector_specs)

    summary = {
        "sectors": _derived(len(sects), unit="sectors the member runs", granularity=inst_g),
        "regional_demand": P.q("annual_openings", total_demand, granularity=f"{region_g}, all sectors", unit="openings/yr"),
        "regional_supply": P.q("projected_supply", total_regional_supply, granularity=region_supply_g, unit="completions/yr", vintage=supply_v),
        "member_supply": P.q("projected_supply", total_member_supply, granularity=inst_g, unit="completions/yr", vintage=supply_v),
        "gap": P.q("gap", int(round(total_demand - total_regional_supply)),
                   granularity=f"{region_g} − {region_supply_g}, all sectors", unit="openings/yr", vintage=gap_v),
        "member_share_of_supply": (
            _derived(round(total_member_supply / total_regional_supply, 3), unit="fraction of regional supply", granularity=inst_g)
            if total_regional_supply else
            QualifiedValue.gated("unavailable", unit="fraction of regional supply", granularity=inst_g)),
    }

    # Rows: one per sector, ranked by the sector's gap — the whole institution at a glance.
    sect_rows = []
    for e in sects:
        socs = sector_socs[e["sector_id"]]
        d = demand_sum(socs)
        rspec_e = sector_spec[e["sector_id"]]
        r_supply = CAN.supply_over_socs(region_colleges, socs, spec=rspec_e)
        m_supply = CAN.supply_over_socs(member_colleges, socs, spec=rspec_e)
        sect_rows.append((e["sector_label"], e["sector_id"], d, r_supply, m_supply, int(round(d - r_supply))))
    sect_rows.sort(key=lambda t: t[5], reverse=True)
    rows = [Row(label=label, values={
        "regional_demand": P.q("annual_openings", d, granularity=region_g, unit="openings/yr"),
        "regional_supply": P.q("projected_supply", r_supply, granularity=region_supply_g, unit="completions/yr", vintage=supply_v),
        "member_supply": P.q("projected_supply", m_supply, granularity=inst_g, unit="completions/yr", vintage=supply_v),
        "gap": P.q("gap", g, granularity="regional openings − regional supply", unit="openings/yr", vintage=gap_v),
    }) for (label, sid, d, r_supply, m_supply, g) in sect_rows]

    # Next-moves point the practitioner DOWN one level — the descent is theirs to walk, not taken here.
    top = sect_rows[0] if sect_rows else None
    top_entry = (find_scope(entry["member_id"], top[1]) or entry) if top else entry
    next_moves = [
        C.as_move("sector_overview", coordinate_of(top_entry),
                  (f"Drill into the widest-gap sector ({top[0]}) — its occupations, supply, and gaps."
                   if top else "Drill into a sector's occupations, supply, and gaps.")),
        C.as_move("unmet_demand", coordinate_of(entry),
                  "See the high-opportunity occupations across the region the member serves no one into."),
    ]

    coord = coordinate_of(entry)
    coord.region = region_disp
    return AnalysisEnvelope(
        form="member_portfolio", coordinate=coord,
        data=DataBlock(summary=summary, rows=rows),
        framing=_framing("member_portfolio", [C.SAL_PROJECTED_NOT_ACTUAL]),
        licensing=_licensing("member_portfolio",
                             licensed=["Each sector the member runs, one row: total regional demand vs the region's projected completions, the member's supply and its share, and the gap.",
                                       "The institution-wide totals are summed over the DEDUPED union of the member's sectors' occupations, so an occupation in two sectors is counted once."]),
        next_moves=next_moves,
        # No single dashboard view corroborates a cross-sector portfolio — an honest 'unavailable'
        # marker (member_portfolio is unmapped in viewlink); each sector row corroborates via its
        # own sector_overview drill.
        view_link=V.view_link("member_portfolio", instance_id=entry["id"],
                              member_id=entry["member_id"], sector_id=entry["sector_id"]),
        provenance=P.build_provenance(
            ["annual_openings", "projected_supply", "gap"],
            scope_granularity=f"demand {region_g}; supply {region_supply_g}; member share {inst_g}",
            vintages={"demand": P.COE_DEMAND_VINTAGE, "projected_supply": supply_v}),
    )


# ── sector overview (sector-anchor orientation; the portfolio home base) ───

def sector_overview(member: str, sector: str) -> AnalysisEnvelope:
    """The sector-anchor orientation view — the home base a portfolio conversation descends from,
    PROGRAM-FORWARD because a practitioner's lever is the program, not the occupation. The summary
    is the sector aggregate (total regional demand vs the region's projected completions, the
    member's supply and its share); the rows are the member's PROGRAMS in the sector, each with its
    completions (supply) and its addressable demand (the χ↑ sum-across pool of openings across the
    occupations it feeds), ranked by that market. Occupations live in each program's addressable
    demand and are reached by drilling a program. Pure Regime-A sums, no allocation — the CTE sector
    is the crosswalk-closure of the PCAH classification, so the totals are defensible as summed
    (COE's own method)."""
    from ontology.regions import COE_REGION_DISPLAY
    from ontology.schema import get_driver
    from partnerships.graph_reads import regional_demand
    from partnerships.sectors import SECTORS

    sel = select(member, sector)                            # the one resolution path (Phase A)
    if sel is None:
        return gate_envelope("sector_overview", member, sector,
                             reason=f"No live coordinate for ({member!r}, {sector!r}). Confirm the member id and its live sectors via list_institutions.")
    entry, rspec = sel.entry, sel.spec
    region, region_disp = sel.region, sel.region_display
    member_colleges, region_colleges = sel.member_colleges, sel.region_colleges
    sector_socs, sector_label = sel.sector_socs, sel.sector_label

    with get_driver().session() as session:
        demand = regional_demand(session, region, sector_socs)

    recent = CAN.recent_award_years()
    supply_v = CAN.vintage(recent)
    region_g = _regional(region_disp)
    region_supply_g = f"regional ({region_disp}) — all {len(region_colleges)} colleges"
    inst_g = _institutional(entry, len(member_colleges))
    gap_v = f"{P.COE_DEMAND_VINTAGE} vs {supply_v}"

    # Regime A — plain sums over DISTINCT occupations / programs (each counted once), no allocation.
    total_demand = int(round(sum((d.get("annual_openings") or 0) for d in demand.values())))
    regional_supply = supply(sel, over="region")
    member_supply = supply(sel, over="member")
    # The member's programs in the sector = registered ∩ in_scope (adjudication C: 'on-the-books' — the
    # member has a Program node for it and it is in the sector's scope), with the supply-active subset
    # (currently graduating) as a stamped complement. Both are stamped so the two meanings that drifted
    # across tools (registered-ever vs recent-supply-active) are DECLARED, never one number that silently
    # means different things. Fixes the former mislabel where a curated spec counted the whole in_scope
    # crosswalk universe as "member programs".
    from ontology.crosswalks import load_top_titles as _load_top_titles
    _titles = _load_top_titles()
    # The member's programs in the sector (adjudication C), one birthplace shared with institution_overview.
    on_the_books, graduating = CAN.member_sector_programs(member_colleges, rspec)
    demand_by_soc = {s: (d.get("annual_openings") or 0) for s, d in demand.items()}

    summary = {
        "regional_demand": P.q("annual_openings", total_demand, granularity=region_g, unit="openings/yr"),
        "regional_supply": P.q("projected_supply", regional_supply, granularity=region_supply_g,
                               unit="completions/yr", vintage=supply_v),
        "member_supply": P.q("projected_supply", member_supply, granularity=inst_g,
                             unit="completions/yr", vintage=supply_v),
        "gap": P.q("gap", int(round(total_demand - regional_supply)),
                   granularity=f"{region_g} − {region_supply_g}", unit="openings/yr", vintage=gap_v),
        "member_share_of_supply": (
            _derived(round(member_supply / regional_supply, 3), unit="fraction of regional supply",
                     granularity=inst_g)
            if regional_supply else
            QualifiedValue.gated("unavailable", unit="fraction of regional supply", granularity=inst_g)),
        "member_programs": _derived(len(on_the_books), unit="TOP6 programs the member runs",
                                    granularity=f"{inst_g} · on-the-books (registered ∩ in_scope)"),
        "member_programs_active": _derived(len(graduating), unit="TOP6 programs currently graduating",
                                           granularity=f"{inst_g} · supply-active (recent completer)"),
        "sector_occupations": _derived(len(sector_socs), unit="SOCs",
                                       granularity=f"{sector_label} sector (PCAH)"),
    }
    # Phase B — the sector decomposed into legible WHATs, so a narrowed figure reads as WHY it's small:
    # in_demand ("is there a market?" — regional openings + near-living-wage + non-declining) vs served
    # ("is the member in it?" — reachable + actively graduating), each a subset of the full sector; the
    # dashboard's "effective" set is their intersection. Added where the sector RULE makes the split
    # meaningful; a curated spec (SVAMP) carries its charter as one authored set, so it is omitted.
    if getattr(sel.raw_spec.soc_rule, "active", False):
        _lenses = sector_lenses(sel.raw_spec)
        summary["in_demand_occupations"] = _derived(
            len(_lenses["in_demand"]), unit="SOCs",
            granularity="in a real, quality market (regional openings + near-living-wage + non-declining)")
        summary["served_occupations"] = _derived(
            len(_lenses["served"]), unit="SOCs",
            granularity="the member reaches with a program and actively graduates into")
        summary["in_demand_openings"] = P.q("annual_openings",
            int(round(sum(demand_by_soc.get(s, 0) for s in _lenses["in_demand"]))),
            granularity=f"{region_g} — the in-demand occupations", unit="openings/yr")
        summary["served_openings"] = P.q("annual_openings",
            int(round(sum(demand_by_soc.get(s, 0) for s in _lenses["served"]))),
            granularity=f"{region_g} — the occupations the member serves", unit="openings/yr")

    # Rows: PROGRAM-FORWARD — the member's programs in the sector, each with its supply
    # (completions) and its ADDRESSABLE DEMAND (the χ↑ sum-across pool of openings across the
    # occupations it feeds), ranked by that market. The practitioner's lever is the program, so the
    # program is the row and the decision object; occupations live in each program's addressable
    # demand and are reached by drilling a program (program_pathways). All canonical, no allocation.
    prog = []
    for top6 in on_the_books:
        occ_socs, addr = CAN.addressable_demand(top6, sector_socs, demand_by_soc)
        prog.append((f"{top6} {_titles.get(top6, top6)}", top6,
                     CAN.supply_over_tops(member_colleges, [top6]), addr, len(occ_socs)))
    prog.sort(key=lambda r: r[3], reverse=True)
    rows = [Row(label=label, values={
        "member_supply": P.q("projected_supply", p_supply, granularity=inst_g, unit="completions/yr", vintage=supply_v),
        "addressable_demand": P.q("annual_openings", addr, granularity=f"{region_g} — the occupations this program feeds", unit="openings/yr"),
        "occupations_fed": _derived(n_occ, unit="SOCs", granularity="TOP→CIP→SOC crosswalk"),
        "colleges_with_program": _derived(CAN.colleges_with_program(member_colleges, top6), unit="colleges", granularity=inst_g),
    }) for (label, top6, p_supply, addr, n_occ) in prog[:_TOP_N]]

    more = None
    if len(prog) > _TOP_N:
        nxt = prog[_TOP_N][1]
        more = More(remaining=len(prog) - _TOP_N,
                    drill=C.as_move("pathway", coordinate_of(entry, top6=nxt),
                                    (f"{len(prog) - _TOP_N} more programs the member runs; "
                                     f"crosswalk on any TOP6 drills into its occupations.")))

    # Program-first descent: the primary next move is drilling a PROGRAM (the practitioner's lever),
    # then the occupation-level gaps, then greenfield.
    top_prog = prog[0] if prog else None
    next_moves = [
        C.as_move("pathway",
                  coordinate_of(entry, top6=top_prog[1]) if top_prog else coordinate_of(entry),
                  (f"Drill into a program — e.g. {top_prog[0]} — for the occupations it prepares "
                   f"students for and their demand." if top_prog else
                   "Drill into a program for the occupations it prepares students for.")),
        C.as_move("gap", coordinate_of(entry),
                  "See the sector's occupation-level supply–demand gaps directly."),
        C.as_move("unmet_demand", coordinate_of(entry),
                  "See high-opportunity occupations across the region the member serves no one into."),
    ]

    coord = coordinate_of(entry)
    coord.region = region_disp
    return AnalysisEnvelope(
        form="sector_overview", coordinate=coord,
        data=DataBlock(summary=summary, rows=rows, more=more),
        framing=_framing("sector_overview", [C.SAL_PROJECTED_NOT_ACTUAL]),
        licensing=_licensing("sector_overview",
                             licensed=["The sector's total regional demand vs total regional projected completions with the member's supply and share (summary), then the member's PROGRAMS — each with its completions and its addressable demand (the openings across the occupations it feeds).",
                                       "Program-forward: a program's addressable demand is a sum-across pool it competes for, shared with other programs, not exclusive — drill a program to see the occupations behind it."]),
        next_moves=next_moves,
        view_link=V.view_link("sector_overview", instance_id=sel.instance_id, member_id=entry["member_id"],
                              sector_id=entry["sector_id"]),
        provenance=P.build_provenance(
            ["annual_openings", "projected_supply", "gap"],
            scope_granularity=f"demand {region_g}; supply {region_supply_g}; member share {inst_g}",
            vintages={"demand": P.COE_DEMAND_VINTAGE, "projected_supply": supply_v}),
    )


FORM_FUNCS = {
    "member_portfolio": member_portfolio,
    "sector_overview": sector_overview,
    "compare": compare,
    "gap": analyze_gap,
    "coverage": analyze_coverage,
    "pathway": analyze_pathway,
    "regional_employers": analyze_regional_employers,
    "occupation_profile": occupation_profile,
    "unmet_demand": unmet_demand,
}
