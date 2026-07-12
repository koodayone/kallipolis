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
from mcp_server.scope import coordinate_of, gate_envelope, scope_for

_TOP_N = 8  # progressive-disclosure row cap (summary-first; drill on request)

_GAP_VINTAGE = f"{P.COE_DEMAND_VINTAGE} vs {P.COE_SUPPLY_VINTAGE}"


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
    return More(
        remaining=remaining,
        drill=NextMove(
            form=form, coordinate=coordinate_of(entry, soc=soc, top6=top6),
            rationale=f"{remaining} more rows; re-call {form} scoped to one row to drill in."),
    )


# ── gap ───────────────────────────────────────────────────────────────────

def analyze_gap(member: str, sector: str, *, soc: Optional[str] = None) -> AnalysisEnvelope:
    resolved = scope_for(member, sector)
    if resolved is None:
        return gate_envelope("gap", member, sector,
                             reason=f"No live coordinate for ({member!r}, {sector!r}).")
    spec, entry = resolved
    resolved_spec = resolve(spec)
    land = build_landscape(resolved_spec)
    agg = land.aggregate

    # Match the grain: a regional gap compares regional demand against TOTAL
    # regional supply — every college in the member's COE region — not the
    # member's supply alone (else one college is asked to satisfy a whole
    # region's openings). The member's own supply is surfaced separately as its
    # share. Same supply DEFINITION as the member number (build_landscape /
    # course-aligned TOPs); only the college axis widens — a frozen-spec twin,
    # memoized like any other landscape.
    region_land = build_landscape(dataclasses.replace(
        resolved_spec, colleges=region_member(resolved_spec.resolve_region()).colleges))
    region_agg = region_land.aggregate

    region_g = _regional(land.region_display)
    inst_g = _institutional(entry, agg.n_colleges)
    region_supply_g = f"regional ({land.region_display}) — Σ {region_agg.n_colleges} colleges"
    awards_v = _awards_window(land.award_years)

    # Per-SOC: member supply Σ over the member's colleges; regional supply Σ over
    # every college in the region; gap = regional openings − regional supply.
    per_soc: dict[str, dict] = {}
    for col in land.colleges:
        for cell in col.cells:
            r = per_soc.setdefault(cell.soc_code, {"title": cell.title,
                                                   "openings": cell.annual_openings,
                                                   "member_supply": 0.0, "actual": 0})
            r["member_supply"] += cell.supply
            r["actual"] += cell.awards_recent
            if r["openings"] is None:
                r["openings"] = cell.annual_openings
    region_supply_by_soc: dict[str, float] = {}
    for col in region_land.colleges:
        for cell in col.cells:
            region_supply_by_soc[cell.soc_code] = \
                region_supply_by_soc.get(cell.soc_code, 0.0) + cell.supply
    for s, r in per_soc.items():
        r["regional_supply"] = region_supply_by_soc.get(s, 0.0)
        r["gap"] = int(round((r["openings"] or 0) - r["regional_supply"]))

    summary = {
        "regional_demand": P.q("annual_openings", agg.regional_demand_total,
                               granularity=region_g, unit="openings/yr"),
        "regional_supply": P.q("projected_supply", round(region_agg.combined_supply_total, 1),
                               granularity=region_supply_g, unit="completions/yr"),
        "member_supply": P.q("projected_supply", round(agg.combined_supply_total, 1),
                             granularity=inst_g, unit="completions/yr"),
        "gap": P.q("gap", int(round(agg.regional_demand_total - region_agg.combined_supply_total)),
                   granularity=f"{region_g} − {region_supply_g}", unit="openings/yr", vintage=_GAP_VINTAGE),
        "actual_awards": P.q("actual_awards", agg.combined_awards,
                             granularity=inst_g, unit="awards", vintage=awards_v),
    }

    items = sorted(per_soc.items(), key=lambda kv: kv[1]["gap"], reverse=True)
    if soc is not None:
        items = [(s, r) for s, r in items if s == soc]
    window = items if soc is not None else items[:_TOP_N]
    rows = [Row(label=f"{s} {r['title']}", values={
        "regional_demand": P.q("annual_openings", r["openings"], granularity=region_g, unit="openings/yr"),
        "regional_supply": P.q("projected_supply", round(r["regional_supply"], 1), granularity=region_supply_g, unit="completions/yr"),
        "member_supply": P.q("projected_supply", round(r["member_supply"], 1), granularity=inst_g, unit="completions/yr"),
        "gap": P.q("gap", r["gap"], granularity="regional openings − regional supply", unit="openings/yr", vintage=_GAP_VINTAGE),
        "actual_awards": P.q("actual_awards", r["actual"], granularity=inst_g, unit="awards", vintage=awards_v),
    }) for s, r in window]
    more = None
    if soc is None and len(items) > _TOP_N:
        more = _drill("gap", entry, remaining=len(items) - _TOP_N, soc=items[_TOP_N][0])

    salience = [C.SAL_PROJECTED_NOT_ACTUAL]
    if 0 < agg.combined_awards < 5 * max(1, agg.n_colleges):
        salience.append(C.SAL_SMALL_N)

    coord = coordinate_of(entry, soc=soc)
    coord.region = land.region_display
    return AnalysisEnvelope(
        form="gap", coordinate=coord,
        data=DataBlock(summary=summary, rows=rows, more=more),
        framing=_framing("gap", salience),
        licensing=_licensing("gap",
                             licensed=["Regional annual openings vs total regional projected completions, per occupation.",
                                       "member_supply is this member's own share of that regional supply."],
                             not_licensed=["Regional supply sums colleges with aligned curriculum (course-routed TOPs) for the occupation; a college that confers in a feeding program without a tagged course can be undercounted."]),
        next_moves=C.build_next_moves("gap", entry, soc=soc),
        view_link=V.view_link("gap", instance_id=spec.id, member_id=entry["member_id"],
                              sector_id=entry["sector_id"], soc=soc),
        provenance=P.build_provenance(
            ["annual_openings", "projected_supply", "actual_awards", "gap"],
            scope_granularity=f"demand {region_g}; supply {region_supply_g}; member share {inst_g}",
            vintages={"demand": P.COE_DEMAND_VINTAGE, "projected_supply": P.COE_SUPPLY_VINTAGE,
                      "actual_awards": awards_v}),
    )


# ── coverage ──────────────────────────────────────────────────────────────

def analyze_coverage(member: str, sector: str) -> AnalysisEnvelope:
    resolved = scope_for(member, sector)
    if resolved is None:
        return gate_envelope("coverage", member, sector,
                             reason=f"No live coordinate for ({member!r}, {sector!r}).")
    spec, entry = resolved
    pl = build_programs_landscape(resolve(spec))
    inst_g = _institutional(entry, pl.n_colleges)
    awards_v = (f"DataMart awards — {pl.latest_award_year}" if pl.latest_award_year
                else "DataMart awards — vintage unavailable")

    covered = partial = uncovered = 0
    if pl.matrix:
        for c in pl.matrix.cells:
            has_award, has_enroll = c.awards > 0, c.enrolled
            if has_award and has_enroll:
                covered += 1
            elif has_award or has_enroll:
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
        "colleges_offering": _derived(t.n_colleges_offering, unit="colleges", granularity=inst_g),
        "occupations_fed": _derived(t.soc_count, unit="SOCs", granularity="TOP→CIP→SOC crosswalk"),
    }) for t in tops[:_TOP_N]]
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
    occ = build_landscape_occupation(occupation, spec=resolve(spec), college=None, include_employers=False)
    region_g = _regional(occ.region_display)
    inst_g = _institutional(entry, len(spec.colleges))
    summary = {
        "regional_demand": P.q("annual_openings", occ.annual_openings, granularity=region_g, unit="openings/yr"),
        "annual_wage": P.q("annual_wage", occ.annual_wage, granularity=region_g, unit="USD/yr (occ. median)"),
        "projected_supply": P.q("projected_supply", round(occ.consortium_supply, 1), granularity=inst_g, unit="completions/yr"),
        "gap": P.q("gap", occ.gap, granularity=f"{region_g} − {inst_g}", unit="openings/yr", vintage=_GAP_VINTAGE),
    }
    tops = sorted(occ.feeding_tops, key=lambda t: t.awards_total, reverse=True)
    rows = [Row(label=f"{t.top6} {t.name}", values={
        "actual_awards": P.q("actual_awards", t.awards_total, granularity=inst_g, unit="awards"),
        "enrollment": P.q("enrollment", t.enrollment_total, granularity=inst_g, unit="enrolled"),
        "colleges_offering": _derived(t.n_colleges_offering, unit="colleges", granularity=inst_g),
    }) for t in tops[:_TOP_N]]
    more = _drill("pathway", entry, remaining=len(tops) - _TOP_N, soc=occupation) if len(tops) > _TOP_N else None
    salience = [C.SAL_PROJECTED_NOT_ACTUAL, C.SAL_LOSSY_CROSSWALK] if len(occ.feeding_tops) >= 4 else [C.SAL_PROJECTED_NOT_ACTUAL]
    coord = coordinate_of(entry, soc=occupation)
    coord.region = occ.region_display
    return AnalysisEnvelope(
        form="pathway", coordinate=coord,
        data=DataBlock(summary=summary, rows=rows, more=more),
        framing=_framing("pathway", salience),
        licensing=_licensing("pathway",
                             licensed=["The programs that feed this occupation and the regional demand for it."]),
        next_moves=C.build_next_moves("pathway", entry, soc=occupation),
        view_link=V.view_link("pathway", instance_id=spec.id, member_id=entry["member_id"],
                              sector_id=entry["sector_id"], soc=occupation),
        provenance=P.build_provenance(
            ["annual_openings", "annual_wage", "projected_supply", "actual_awards", "gap"],
            scope_granularity=f"demand {region_g}; supply {inst_g}",
            vintages={"demand": P.COE_DEMAND_VINTAGE, "projected_supply": P.COE_SUPPLY_VINTAGE}),
    )


# ── employer shed ─────────────────────────────────────────────────────────

def analyze_employer_shed(member: str, sector: str, *, soc: Optional[str] = None) -> AnalysisEnvelope:
    resolved = scope_for(member, sector)
    if resolved is None:
        return gate_envelope("employer_shed", member, sector,
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
    more = _drill("employer_shed", entry, remaining=len(ranked) - _TOP_N, soc=soc) if len(ranked) > _TOP_N else None

    coord = coordinate_of(entry, soc=soc)
    coord.region = er.region_display
    return AnalysisEnvelope(
        form="employer_shed", coordinate=coord,
        data=DataBlock(summary=summary, rows=rows, more=more),
        framing=_framing("employer_shed", []),
        licensing=_licensing("employer_shed",
                             licensed=["Regional employers ranked by OES staffing share for the target occupations."],
                             not_licensed=["'shown' is a geocoded shortlist, not the whole candidate pool ('total')."]),
        next_moves=C.build_next_moves("employer_shed", entry, soc=soc),
        view_link=V.view_link("employer_shed", instance_id=spec.id, member_id=entry["member_id"],
                              sector_id=entry["sector_id"]),
        provenance=P.build_provenance(
            ["candidate_employers", "employer_relevance"],
            scope_granularity=region_g,
            vintages={"employer_relevance": P.OES_VINTAGE}),
    )


FORM_FUNCS = {
    "gap": analyze_gap,
    "coverage": analyze_coverage,
    "pathway": analyze_pathway,
    "employer_shed": analyze_employer_shed,
}
