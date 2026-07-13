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
from partnerships.resolve import resolve

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
)
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
    tool = C.tool_name(form)   # the drill pointer is a call target — public tool name, not the form-id
    return More(
        remaining=remaining,
        drill=NextMove(
            form=tool, coordinate=coordinate_of(entry, soc=soc, top6=top6),
            rationale=f"{remaining} more rows; re-call {tool} scoped to one row to drill in."),
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
        next_moves=[NextMove(form=C.tool_name("orient"), coordinate=coord,
                             rationale="See which sectors this member actually runs programs in.")],
        view_link=V.view_link(form, instance_id=entry["id"], member_id=entry["member_id"],
                              sector_id=entry["sector_id"]),
    )


_ROSTER_N = 12   # named colleges inline per program; the count field discloses any remainder


def _program_roster(colleges, top6: str, granularity: str) -> list[Row]:
    """Top-N named colleges offering a program (Defect 2) — label + Covered/Partial/Gap class
    + latest-year awards, from the ONE canonical roster. A college with blank DataMart awards
    stays in the roster (its class shows the absence) rather than silently dropping the way
    OES-suppressed employers do; the row's count field discloses any remainder beyond top-N."""
    return [Row(label=cell.college, values={
        "coverage": QualifiedValue.ok(cell.coverage, source="datamart", granularity=granularity),
        "actual_awards": P.q("actual_awards", cell.awards, granularity=granularity, unit="awards (latest yr)"),
    }) for cell in CAN.college_roster(colleges, top6)[:_ROSTER_N]]


# ── gap ───────────────────────────────────────────────────────────────────

def analyze_gap(member: str, sector: str, *, soc: Optional[str] = None) -> AnalysisEnvelope:
    resolved = scope_for(member, sector)
    if resolved is None:
        return gate_envelope("gap", member, sector,
                             reason=f"No live coordinate for ({member!r}, {sector!r}).")
    spec, entry = resolved
    resolved_spec = resolve(spec)
    land = build_landscape(resolved_spec)   # SOC universe + regional demand (scope-invariant)
    agg = land.aggregate

    # Supply resolves through the ONE canonical resolver (canonical.supply): DataMart
    # 3-yr-avg completions over is_vocational crosswalk feeders. Regional supply (every
    # college in the member's COE region) is the gap denominator; the member's own supply
    # is its share; the latest single year is the trend. All come from the same function,
    # so no sibling tool can disagree. Demand + the SOC set come from the landscape.
    region = resolved_spec.resolve_region()
    member_colleges, region_colleges = resolved_spec.colleges, region_member(region).colleges
    recent, latest = CAN.recent_award_years(), CAN.recent_award_years(1)

    region_g = _regional(land.region_display)
    inst_g = _institutional(entry, agg.n_colleges)
    region_supply_g = f"regional ({land.region_display}) — all {len(region_colleges)} colleges"
    supply_v, latest_v = CAN.vintage(recent), CAN.vintage(latest)
    gap_v = f"{P.COE_DEMAND_VINTAGE} vs {supply_v}"    # supply side now DataMart, not the COE window

    per_soc: dict[str, dict] = {}
    for col in land.colleges:
        for cell in col.cells:
            r = per_soc.get(cell.soc_code)
            if r is None:
                r = per_soc[cell.soc_code] = {
                    "title": cell.title, "openings": cell.annual_openings,
                    "member_supply": CAN.supply(member_colleges, cell.soc_code),
                    "regional_supply": CAN.supply(region_colleges, cell.soc_code),
                    "latest": CAN.supply(member_colleges, cell.soc_code, years=latest)}
            if r["openings"] is None:
                r["openings"] = cell.annual_openings
    for r in per_soc.values():
        r["gap"] = CAN.gap(r["openings"], r["regional_supply"])

    if not per_soc:   # member serves no qualifying occupation here — gate, never 0-readable
        return _empty_member_sector("gap", entry, land.region_display)

    socs = list(per_soc)
    agg_region_supply = CAN.supply_over_socs(region_colleges, socs)
    summary = {
        "regional_demand": P.q("annual_openings", agg.regional_demand_total,
                               granularity=region_g, unit="openings/yr"),
        "regional_supply": P.q("projected_supply", agg_region_supply,
                               granularity=region_supply_g, unit="completions/yr", vintage=supply_v),
        "member_supply": P.q("projected_supply", CAN.supply_over_socs(member_colleges, socs),
                             granularity=inst_g, unit="completions/yr", vintage=supply_v),
        "gap": P.q("gap", int(round(agg.regional_demand_total - agg_region_supply)),
                   granularity=f"{region_g} − {region_supply_g}", unit="openings/yr", vintage=gap_v),
        "latest_year_supply": P.q("latest_year_supply", CAN.supply_over_socs(member_colleges, socs, years=latest),
                                  granularity=inst_g, unit="completions", vintage=latest_v),
    }

    items = sorted(per_soc.items(), key=lambda kv: kv[1]["gap"], reverse=True)
    if soc is not None:
        items = [(s, r) for s, r in items if s == soc]
    window = items if soc is not None else items[:_TOP_N]
    rows = [Row(label=f"{s} {r['title']}", values={
        "regional_demand": P.q("annual_openings", r["openings"], granularity=region_g, unit="openings/yr"),
        "regional_supply": P.q("projected_supply", r["regional_supply"], granularity=region_supply_g, unit="completions/yr", vintage=supply_v),
        "member_supply": P.q("projected_supply", r["member_supply"], granularity=inst_g, unit="completions/yr", vintage=supply_v),
        "gap": P.q("gap", r["gap"], granularity="regional openings − regional supply", unit="openings/yr", vintage=gap_v),
        "latest_year_supply": P.q("latest_year_supply", r["latest"], granularity=inst_g, unit="completions", vintage=latest_v),
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
                             not_licensed=["Supply is a 3-yr average of CO-approved completions (DataMart) over the occupation's CTE feeder programs — it excludes locally-approved certificates and is not the single most recent year (latest_year_supply)."]),
        next_moves=C.build_next_moves("gap", entry, soc=soc),
        view_link=V.view_link("gap", instance_id=spec.id, member_id=entry["member_id"],
                              sector_id=entry["sector_id"], soc=soc),
        provenance=P.build_provenance(
            ["annual_openings", "projected_supply", "latest_year_supply", "gap"],
            scope_granularity=f"demand {region_g}; supply {region_supply_g}; member share {inst_g}",
            vintages={"demand": P.COE_DEMAND_VINTAGE, "projected_supply": supply_v,
                      "latest_year_supply": latest_v}),
    )


# ── coverage ──────────────────────────────────────────────────────────────

def analyze_coverage(member: str, sector: str) -> AnalysisEnvelope:
    resolved = scope_for(member, sector)
    if resolved is None:
        return gate_envelope("coverage", member, sector,
                             reason=f"No live coordinate for ({member!r}, {sector!r}).")
    spec, entry = resolved
    rspec = resolve(spec)
    member_colleges = list(rspec.colleges)
    pl = build_programs_landscape(rspec)
    if not pl.tops:   # member offers no program in this sector — gate, never 0-readable
        return _empty_member_sector("coverage", entry, pl.region_display)
    inst_g = _institutional(entry, pl.n_colleges)
    awards_v = (f"DataMart awards — {pl.latest_award_year}" if pl.latest_award_year
                else "DataMart awards — vintage unavailable")

    covered = partial = uncovered = 0
    if pl.matrix:
        # One coverage predicate (quantities.coverage). NOTE: this preserves the current
        # ruleless (enrolled-OR-awarded) classification. On rule-bearing instances (BACCC,
        # sector-derived SMCCD) the dashboard matrix uses awards_only — an enrolled-but-not-
        # awarding cell is a gap, not partial — and this MCP count still diverges from it.
        # Passing awards_only=pl.matrix.coverage_awards_only closes that gap; deferred to the
        # S7 sign-off because it moves the reported counts on those instances.
        for c in pl.matrix.cells:
            cls = CAN.coverage(c.enrolled, c.awards)
            if cls == "covered":
                covered += 1
            elif cls == "partial":
                partial += 1
            else:
                uncovered += 1

    summary = {
        "member_colleges": _derived(pl.n_colleges, unit="colleges", granularity=inst_g),
        "programs": _derived(len(pl.tops), unit="TOP6 programs", granularity=inst_g),
        "covered_cells": P.q("coverage", covered, granularity=inst_g, unit="college×program cells", vintage=awards_v),
        "partial_cells": P.q("coverage", partial, granularity=inst_g, unit="college×program cells", vintage=awards_v),
        "gap_cells": P.q("coverage", uncovered, granularity=inst_g, unit="college×program cells", vintage=awards_v),
    }

    tops = sorted(pl.tops, key=lambda t: t.awards_total, reverse=True)
    rows = [Row(label=f"{t.top6} {t.name}", values={
        "actual_awards": P.q("actual_awards", t.awards_total, granularity=inst_g, unit="awards", vintage=awards_v),
        "enrollment": P.q("enrollment", t.enrollment_total, granularity=inst_g, unit="enrolled"),
        "colleges_with_program": _derived(CAN.colleges_with_program(member_colleges, t.top6),
                                          unit="colleges", granularity=inst_g),
        "colleges_actively_awarding": _derived(CAN.colleges_actively_awarding(member_colleges, t.top6),
                                               unit="colleges (latest yr)", granularity=inst_g),
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
        view_link=V.view_link("coverage", instance_id=spec.id, member_id=entry["member_id"],
                              sector_id=entry["sector_id"]),
        provenance=P.build_provenance(
            ["coverage", "actual_awards", "enrollment"],
            scope_granularity=inst_g,
            vintages={"actual_awards": awards_v}),
    )


# ── pathway (program ↔ occupation, exactly-one-of) ────────────────────────

def analyze_pathway(member: str, sector: str, *, program: Optional[str] = None,
                    occupation: Optional[str] = None) -> AnalysisEnvelope:
    resolved = scope_for(member, sector)
    if resolved is None:
        return gate_envelope("pathway", member, sector,
                             reason=f"No live coordinate for ({member!r}, {sector!r}).")
    spec, entry = resolved

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
        pr = build_program_report(program, None, spec=resolve(spec))
        n_cips = len(pr.crosswalk.cips) if pr.crosswalk else 0
        summary = {
            "program": QualifiedValue.ok(pr.name, source="datamart", granularity="TOP6 program"),
            "occupations_fed": _derived(len(pr.occupations), unit="SOCs", granularity="TOP→CIP→SOC crosswalk"),
            "bridging_cips": _derived(n_cips, unit="CIPs", granularity="TOP→CIP→SOC crosswalk"),
        }
        occs = sorted(pr.occupations, key=lambda o: (o.annual_openings or 0), reverse=True)
        rows = [Row(label=f"{o.soc_code} {o.title}", values={
            "annual_openings": P.q("annual_openings", o.annual_openings, granularity=_regional(pr.region_display), unit="openings/yr"),
            "annual_wage": P.q("annual_wage", o.annual_wage, granularity=_regional(pr.region_display), unit="USD/yr (occ. median)"),
        }) for o in occs[:_TOP_N]]
        more = _drill("pathway", entry, remaining=len(occs) - _TOP_N, top6=program) if len(occs) > _TOP_N else None
        salience = [C.SAL_LOSSY_CROSSWALK] if len(pr.occupations) >= 4 else []
        coord = coordinate_of(entry, top6=program)
        coord.region = pr.region_display
        return AnalysisEnvelope(
            form="pathway", coordinate=coord,
            data=DataBlock(summary=summary, rows=rows, more=more),
            framing=_framing("pathway", salience),
            licensing=_licensing("pathway",
                                 licensed=["The occupations this TOP6 program prepares students for, via the crosswalk."]),
            next_moves=C.build_next_moves("pathway", entry, top6=program),
            view_link=V.view_link("pathway", instance_id=spec.id, member_id=entry["member_id"],
                                  sector_id=entry["sector_id"], top6=program),
            provenance=P.build_provenance(
                ["annual_openings", "annual_wage"],
                scope_granularity=_regional(pr.region_display),
                vintages={"demand": P.COE_DEMAND_VINTAGE}),
        )

    # occupation
    # supply/gap resolve through canonical.supply — coherent with analyze_gap (this tool
    # previously computed gap = regional − INSTITUTIONAL supply, the exact conflation the
    # gap description forbids; fixed here).
    rspec = resolve(spec)
    occ = build_landscape_occupation(occupation, spec=rspec, college=None, include_employers=False)
    member_colleges = rspec.colleges
    region_colleges = region_member(rspec.resolve_region()).colleges
    recent, latest = CAN.recent_award_years(), CAN.recent_award_years(1)
    region_g = _regional(occ.region_display)
    inst_g = _institutional(entry, len(member_colleges))
    region_supply_g = f"regional ({occ.region_display}) — all {len(region_colleges)} colleges"
    supply_v, latest_v = CAN.vintage(recent), CAN.vintage(latest)
    gap_v = f"{P.COE_DEMAND_VINTAGE} vs {supply_v}"    # supply side now DataMart, not the COE window
    regional_supply = CAN.supply(region_colleges, occupation)
    member_supply = CAN.supply(member_colleges, occupation)
    summary = {
        "regional_demand": P.q("annual_openings", occ.annual_openings, granularity=region_g, unit="openings/yr"),
        "annual_wage": P.q("annual_wage", occ.annual_wage, granularity=region_g, unit="USD/yr (occ. median)"),
        "regional_supply": P.q("projected_supply", regional_supply, granularity=region_supply_g, unit="completions/yr", vintage=supply_v),
        "member_supply": P.q("projected_supply", member_supply, granularity=inst_g, unit="completions/yr", vintage=supply_v),
        "gap": P.q("gap", CAN.gap(occ.annual_openings, regional_supply),
                   granularity=f"{region_g} − {region_supply_g}", unit="openings/yr", vintage=gap_v),
        "latest_year_supply": P.q("latest_year_supply", CAN.supply(member_colleges, occupation, years=latest),
                                  granularity=inst_g, unit="completions", vintage=latest_v),
    }
    tops = sorted(occ.feeding_tops, key=lambda t: t.awards_total, reverse=True)
    rows = [Row(label=f"{t.top6} {t.name}", values={
        "actual_awards": P.q("actual_awards", t.awards_total, granularity=inst_g, unit="awards"),
        "enrollment": P.q("enrollment", t.enrollment_total, granularity=inst_g, unit="enrolled"),
        "colleges_with_program": _derived(CAN.colleges_with_program(member_colleges, t.top6),
                                          unit="colleges", granularity=inst_g),
        "colleges_actively_awarding": _derived(CAN.colleges_actively_awarding(member_colleges, t.top6),
                                               unit="colleges (latest yr)", granularity=inst_g),
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
        view_link=V.view_link("pathway", instance_id=spec.id, member_id=entry["member_id"],
                              sector_id=entry["sector_id"], soc=occupation),
        provenance=P.build_provenance(
            ["annual_openings", "annual_wage", "projected_supply", "latest_year_supply", "actual_awards", "gap"],
            scope_granularity=f"demand {region_g}; supply {region_supply_g}; member share {inst_g}",
            vintages={"demand": P.COE_DEMAND_VINTAGE, "projected_supply": supply_v, "latest_year_supply": latest_v}),
    )


# ── regional employers ─────────────────────────────────────────────────────

def analyze_regional_employers(member: str, sector: str, *, soc: Optional[str] = None) -> AnalysisEnvelope:
    resolved = scope_for(member, sector)
    if resolved is None:
        return gate_envelope("regional_employers", member, sector,
                             reason=f"No live coordinate for ({member!r}, {sector!r}).")
    spec, entry = resolved
    er = build_landscape_employers(resolve(spec))
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
        view_link=V.view_link("regional_employers", instance_id=spec.id, member_id=entry["member_id"],
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
    from ontology.crosswalks import load_top_titles, top6_to_soc
    from ontology.regions import COE_REGION_DISPLAY
    from ontology.schema import get_driver

    sects = sectors_for_member(member)
    if not sects:
        return gate_envelope("occupation_profile", member, "",
                             reason=f"No institution matching {member!r}. Establish it first.")
    resolved = scope_for(member, sects[0]["sector_id"])
    if resolved is None:
        return gate_envelope("occupation_profile", member, "",
                             reason=f"Could not resolve institution {member!r}.")
    spec0, entry = resolved
    region = spec0.resolve_region()
    region_disp = COE_REGION_DISPLAY.get(region, region)
    member_colleges = list(spec0.colleges)
    region_colleges = list(region_member(region).colleges)

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
            "ORDER BY pct DESC LIMIT $n", region=region, s=occupation, n=_OCC_EMP_N).data()

    education = edu_row["e"] if edu_row else None
    # Supply + feeders resolve through the ONE canonical resolver — is_vocational
    # crosswalk feeders (excludes non-CTE noise like Liberal Arts → Machinists) and
    # DataMart 3-yr-avg completions, coherent with the gap/pathway tools.
    recent, latest = CAN.recent_award_years(), CAN.recent_award_years(1)
    regional_supply = CAN.supply(region_colleges, occupation)
    member_supply = CAN.supply(member_colleges, occupation)
    latest_supply = CAN.supply(member_colleges, occupation, years=latest)
    openings = demand.get("annual_openings")
    gap = CAN.gap(openings, regional_supply)
    in_sectors = [SECTORS[sid].label for sid in SECTORS if occupation in set(SECTORS[sid].socs)]

    region_g = _regional(region_disp)
    region_supply_g = f"regional ({region_disp}) — all {len(region_colleges)} colleges"
    inst_g = _institutional(entry, len(member_colleges))
    supply_v, latest_v = CAN.vintage(recent), CAN.vintage(latest)
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
        "latest_year_supply": P.q("latest_year_supply", latest_supply, granularity=inst_g,
                                  unit="completions", vintage=latest_v),
    }
    if emp_rows:
        summary["top_employers"] = QualifiedValue.ok(
            ", ".join(e["name"] for e in emp_rows), source="graph_bls",
            granularity=f"regional ({region_disp}) — top {len(emp_rows)} by OES staffing share")

    # Supporting programs = the SOC's ACTIVE feeders — is_vocational crosswalk feeders that
    # awarded a completer in the latest year (matches program_pathways' builder gate, so a
    # dormant program on the books like 123000 Nursing is excluded here exactly as it is there).
    # Counts are PROGRAM-grain via the ONE canonical roster (fixes the course-based undercount).
    supporting = sorted(CAN.active_feeders(region_colleges, occupation),
                        key=lambda t: (-CAN.colleges_actively_awarding(region_colleges, t),
                                       -CAN.colleges_with_program(region_colleges, t), t))
    rows = [Row(label=f"{t} {titles.get(t, '')}".strip(), values={
                "colleges_with_program": _derived(CAN.colleges_with_program(region_colleges, t),
                                                  unit="colleges", granularity=region_supply_g),
                "colleges_actively_awarding": _derived(CAN.colleges_actively_awarding(region_colleges, t),
                                                       unit="colleges (latest yr)", granularity=region_supply_g),
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
        next_moves=[   # form = the callable tool name the model routes to, not the internal id
            NextMove(form=C.tool_name("regional_employers"), coordinate=coord,
                     rationale="See the full set of regional employers hiring for this occupation."),
            NextMove(form=C.tool_name("gap"), coordinate=coordinate_of(nav_entry),
                     rationale="See the whole supply–demand gap for this sector."),
        ],
        view_link=V.view_link("occupation_profile", instance_id=nav_entry["id"],
                              member_id=nav_entry["member_id"], sector_id=nav_entry["sector_id"],
                              soc=occupation),
        provenance=P.build_provenance(
            ["annual_openings", "annual_wage", "growth_rate", "regional_employment",
             "projected_supply", "latest_year_supply", "gap"],
            scope_granularity=f"demand {region_g}; supply {region_supply_g}; member share {inst_g}",
            vintages={"demand": P.COE_DEMAND_VINTAGE, "projected_supply": supply_v, "latest_year_supply": latest_v}),
    )


# ── unmet demand (greenfield gaps; member-scoped, sector-agnostic) ─────────

# The quality-demand gate — three explicit, legible, tunable judgment thresholds (plus the
# PROMOTION_SOCS not-trainable exclusion the gap view already applies). A greenfield
# occupation (member supply == 0, not a promotion role) is surfaced ONLY if it clears ALL THREE.
_CC_SERVABLE_EDUCATION = frozenset({           # BLS entry-level education a community college can
    "High school diploma or equivalent",       # actually credential into — the middle-skill band.
    "Postsecondary nondegree award",           # EXCLUDES Bachelor's/Master's/Doctoral (out of a CC's
    "Some college, no degree",                 # award authority) and "No formal educational
    "Associate's degree",                      # credential" (nothing to launch a program for).
})
_WAGE_FLOOR = 50_000     # living-wage floor (USD/yr, occ. median) — screens out low-wage demand.
_OPENINGS_FLOOR = 100    # meaningful-demand floor (annual regional openings) — screens out thin demand.


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
    sects = sectors_for_member(member)
    if not sects:
        return gate_envelope("unmet_demand", member, "",
                             reason=f"No institution matching {member!r}. Establish it first.")
    resolved = scope_for(member, sects[0]["sector_id"])
    if resolved is None:
        return gate_envelope("unmet_demand", member, "",
                             reason=f"Could not resolve institution {member!r}.")
    spec0, entry = resolved
    region = spec0.resolve_region()
    region_disp = COE_REGION_DISPLAY.get(region, region)
    member_colleges = list(spec0.colleges)

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
    survivors.sort(key=lambda r: (r["openings"] or 0) * (r["wage"] or 0), reverse=True)
    n_unmet = len(survivors)

    coord = coordinate_of(entry)
    coord.region = region_disp

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
            drill=NextMove(form=C.tool_name("occupation_profile"),
                           coordinate=coordinate_of(entry, soc=nxt),
                           rationale=(f"{n_unmet - _TOP_N} more greenfield occupations; "
                                      f"occupation_profile on any surfaced SOC drills into one.")))

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
                    f"(≥ {_OPENINGS_FLOOR} openings/yr) roles, ranked by opportunity "
                    "(annual openings × median wage)."]
    not_licensed = ["It does not assert the member SHOULD launch these — only that regional "
                    "demand exists and the member's own supply is zero; feasibility, cost, "
                    "and mission fit are out of scope.",
                    "'member supply == 0' is a 3-yr-average DataMart figure over the occupation's "
                    "is_vocational feeders — a program with enrollment but no completer in the "
                    "window reads as zero here, and locally-approved certificates are excluded."]

    top_soc = survivors[0]["soc"] if survivors else None
    return AnalysisEnvelope(
        form="unmet_demand", coordinate=coord,
        data=DataBlock(summary=summary, rows=rows, more=more),
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


FORM_FUNCS = {
    "gap": analyze_gap,
    "coverage": analyze_coverage,
    "pathway": analyze_pathway,
    "regional_employers": analyze_regional_employers,
    "occupation_profile": occupation_profile,
    "unmet_demand": unmet_demand,
}
