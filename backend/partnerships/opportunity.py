"""Occupation-centric partnership opportunity surfaces.

The post-shift Partnerships view: instead of (college, employer) ->
proposal, the unit of analysis is (college, occupation) -> opportunity
report. Each Strong Workforce sector contains the CTE-reachable
occupations the college's region demands; clicking an occupation
generates a multi-employer partnership opportunity report.

This module owns the composition: PCAH TOP->Sector mapping, TOP->CIP->SOC
chain, COE regional demand, college's PREPARES_FOR edges, and the
employer regional pivot all flow into the two public functions:

    build_sector_index(college)             -> SectorIndex
    build_opportunity_report(college, soc)  -> OpportunityReport

Per the institutional-deference principle: the sector->occupation
mapping comes from PCAH (Chancellor's Office Program and Course
Approval Handbook) walked through the TOP-CIP-SOC chain. A SOC may
appear under multiple sectors when its TOPs are claimed by more than
one. Same employer-agnostic prose frames the report in every case.
"""

from __future__ import annotations

import logging
from collections import defaultdict

from ontology.crosswalks import (
    _load_cip_to_soc,
    _load_pcah_cte_top6,
    _load_top_to_cip,
    cte_reachable_socs,
    load_top_titles,
    load_naics4_titles,
)
from ontology.oes import oes_socs_for_naics4
from ontology.regions import (
    COE_REGION_DISPLAY,
    COE_REGION_PRIORITY_SECTORS,
    COLLEGE_COE_REGION,
)
from ontology.schema import get_driver
from ontology.supply import get_coe_supply
from partnerships.gather import (
    _gather_aligned_curriculum,
    _gather_curriculum_crosswalk,
    _gather_student_pipeline,
)
from partnerships.models import (
    CurriculumCrosswalk,
    DepartmentEvidence,
    InstitutionalSources,
    OccupationEvidence,
    OpportunityReport,
    OpportunityRow,
    PartnershipOpportunityEmployer,
    SectorEntry,
    SectorIndex,
    StudentEvidence,
    StudentSummaryEvidence,
    SupplyEstimate,
    SwpEvidence,
)
from partnerships.opportunity_narrative import build_opportunity_narrative

logger = logging.getLogger(__name__)


# ── Sector inversion ────────────────────────────────────────────────────

# PCAH file includes an "Unassigned" bucket for CTE-classified TOPs that
# the Chancellor's Office does not place under any of the 12 Doing-What-
# MATTERS / Strong Workforce sectors. The Partnerships view is the SWP-
# sector navigation surface, so we exclude this bucket — those TOPs are
# still CTE-reachable (they appear via cte_reachable_socs) but they don't
# anchor a sector accordion of their own.
_PCAH_NON_SWP_SECTORS = {"Unassigned"}

_sector_to_top6: dict[str, list[str]] | None = None


def _load_sector_to_top6() -> dict[str, list[str]]:
    """Inverse of _load_pcah_cte_top6: sector -> sorted list of TOP6 codes.

    Filters out PCAH buckets that aren't one of the 12 SWP sectors.
    Cached at module level — the PCAH file is static and small.
    """
    global _sector_to_top6
    if _sector_to_top6 is not None:
        return _sector_to_top6
    top_to_sector = _load_pcah_cte_top6()
    inv: dict[str, list[str]] = defaultdict(list)
    for top6, sector in top_to_sector.items():
        if sector in _PCAH_NON_SWP_SECTORS:
            continue
        inv[sector].append(top6)
    for sector in inv:
        inv[sector].sort()
    _sector_to_top6 = dict(inv)
    return _sector_to_top6


def _sector_socs(sector: str) -> set[str]:
    """All SOCs reachable from the PCAH TOPs that belong to a sector,
    via the TOP->CIP->SOC chain. Matches the institutional crosswalk
    walk; no LLM, no heuristic."""
    sector_to_top6 = _load_sector_to_top6()
    top_to_cip = _load_top_to_cip()
    cip_to_soc = _load_cip_to_soc()
    socs: set[str] = set()
    for top6 in sector_to_top6.get(sector, []):
        for cip in top_to_cip.get(top6, set()):
            socs.update(cip_to_soc.get(cip, set()))
    return socs


# ── Sector index ────────────────────────────────────────────────────────


def build_sector_index(college: str) -> SectorIndex:
    """For a college, return every Strong Workforce sector that has at
    least one CTE-reachable, regionally-demanded occupation, with the
    occupations alphabetically listed under each.

    The intersection that scopes each sector accordion:
      1. SOCs reachable from this sector's PCAH TOPs (institutional)
      2. CTE-reachable union (filter by overall PCAH coverage)
      3. SOCs the college's COE region actually demands

    Per-occupation metadata (course_count, student_count, employer_count,
    demand figures) is gathered with three focused Cypher passes against
    the graph — one per metric — keyed by SOC.
    """
    coe_region = COLLEGE_COE_REGION.get(college, "")
    priority_sectors = set(COE_REGION_PRIORITY_SECTORS.get(coe_region, []))
    cte_socs = cte_reachable_socs()
    sector_to_top6 = _load_sector_to_top6()

    # The per-(college, soc) aggregates (course_count, employer_count,
    # student_count, top_codes) are precomputed onto OCCUPATION_PIPELINE
    # edges by partnerships.compute.materialize_occupation_pipeline at
    # pipeline reload time. Three queries that previously dominated this
    # endpoint at request time (1.3s p50 / 11s p95 for the student count
    # alone, on prod's e2-medium) collapse into a single edge read here.
    #
    # OCCUPATION_PIPELINE is sparse — edges exist only where the college
    # has at least one PREPARES_FOR-aligned course for the SOC, mirroring
    # the strict-filter gating below. SOCs the region demands but the
    # college doesn't institutionally connect to are still surfaced via
    # regional_socs (we want them in the dataset for diagnostics) but
    # filtered out at row construction.
    driver = get_driver()
    with driver.session() as session:
        # All SOCs the region demands, with metadata, plus the precomputed
        # alignment aggregates joined via OPTIONAL MATCH (so unaligned
        # SOCs still come through, with NULL aggregates that get filtered
        # by the strict-filter step).
        rows = session.run("""
            MATCH (col:College {name: $college})-[:IN_MARKET]->(r:Region)
                  -[d:DEMANDS]->(occ:Occupation)
            OPTIONAL MATCH (col)-[op:OCCUPATION_PIPELINE]->(occ)
            RETURN occ.soc_code AS soc_code,
                   occ.title AS title,
                   d.annual_openings AS annual_openings,
                   d.annual_wage AS annual_wage,
                   d.growth_rate AS growth_rate,
                   op.course_count AS course_count,
                   op.employer_count AS employer_count,
                   op.student_count AS student_count,
                   op.top_codes AS top_codes
        """, college=college).data()

    regional_socs = rows  # name preserved for the loop below; same shape +
                          # the four extra alignment fields
    course_count_by_soc = {r["soc_code"]: r.get("course_count") or 0 for r in rows}
    employer_count_by_soc = {r["soc_code"]: r.get("employer_count") or 0 for r in rows}
    student_count_by_soc = {r["soc_code"]: r.get("student_count") or 0 for r in rows}
    top_codes_by_soc: dict[str, set[str]] = {
        r["soc_code"]: {t for t in (r.get("top_codes") or []) if t}
        for r in rows
    }

    # Per-SOC supply estimates — projected program-completions the COE
    # publishes for the TOP6 codes the college's PREPARES_FOR-tagged
    # courses route through. Keyed off the course-derived TOP set rather
    # than the global TOP→CIP→SOC crosswalk so the index gap matches the
    # per-SOC report's "Workforce Gap" figure exactly. (The crosswalk
    # would over-attribute supply by including TOPs the college offers
    # in unrelated programs whose courses are not tagged for SOC prep.)
    has_supply_by_soc: dict[str, bool] = {}
    total_supply_by_soc: dict[str, float] = {}
    for r in regional_socs:
        soc = r["soc_code"]
        if soc in has_supply_by_soc:
            continue
        related_tops = top_codes_by_soc.get(soc, set())
        if not related_tops:
            has_supply_by_soc[soc] = False
            total_supply_by_soc[soc] = 0.0
            continue
        estimates, total_supply = get_coe_supply(related_tops, college)
        has_supply_by_soc[soc] = len(estimates) > 0
        total_supply_by_soc[soc] = total_supply

    # Build per-soc OpportunityRow once; same row instance can be reused
    # under multiple sectors.
    #
    # Two surface conditions, tagged via `alignment_status`:
    #
    # 1. "aligned" — the strict five-signal filter from before. Surfaces
    #    only SOCs where every clickable row produces a fully-populated
    #    Opportunity Report (no honest-absence branches in the LMI /
    #    curriculum / employer / supply sections), AND there's a
    #    positive workforce gap (regional demand > college supply). The
    #    gap > 0 requirement is the SWP fundability cut: Strong
    #    Workforce RFAs require demonstrated regional unmet demand as
    #    the proposal anchor.
    #
    # 2. "gap" — the college has NO institutionally aligned curriculum
    #    for this SOC (course_count = 0), but the SOC is regionally
    #    demanded AND globally CTE-reachable AND in this sector's PCAH
    #    classification. Surfaced so the college can see "no current
    #    pathway, but regional demand exists" as a consortia-level
    #    opportunity worth discussing. Per institutional-deference, the
    #    gap is real institutional signal — papering over it with
    #    silent omission misrepresents the workforce-alignment surface.
    rows_by_soc: dict[str, OpportunityRow] = {}
    for r in regional_socs:
        soc = r["soc_code"]
        if soc not in cte_socs:
            continue
        course_count = course_count_by_soc.get(soc, 0)
        student_count = student_count_by_soc.get(soc, 0)
        employer_count = employer_count_by_soc.get(soc, 0)
        has_supply = has_supply_by_soc.get(soc, False)
        annual_openings = r["annual_openings"] or 0
        total_supply = total_supply_by_soc.get(soc, 0.0)
        gap = int(round(annual_openings - total_supply))

        if course_count > 0:
            # Aligned candidate — retain the original strict five-signal
            # filter so every clickable aligned row populates fully.
            if (student_count == 0 or employer_count == 0
                    or not has_supply or gap <= 0):
                continue
            alignment_status = "aligned"
        else:
            # Gap candidate — surface when regional demand exists. The
            # college's per-row supply is 0 (no aligned TOPs), so
            # gap = annual_openings; we filter on annual_openings > 0
            # to drop SOCs with no regional demand signal at all.
            if annual_openings <= 0:
                continue
            alignment_status = "gap"

        rows_by_soc[soc] = OpportunityRow(
            soc_code=soc,
            title=r["title"] or soc,
            annual_openings=r["annual_openings"],
            annual_wage=r["annual_wage"],
            growth_rate=r.get("growth_rate"),
            course_count=course_count,
            student_count=student_count,
            employer_count=employer_count,
            gap=gap,
            alignment_status=alignment_status,
        )

    # Build sector entries. Sectors are alphabetical; within each
    # sector, aligned rows come first (sorted by gap descending —
    # largest unmet regional pipeline first), then gap rows (also
    # sorted by gap descending). Title is the deterministic tiebreaker.
    # The aligned-then-gap ordering surfaces the college's actionable
    # pathways at the top and consortia-level opportunities below,
    # without hiding either.
    sectors: list[SectorEntry] = []
    for sector in sorted(sector_to_top6.keys()):
        sector_soc_set = _sector_socs(sector)
        occupations = [
            rows_by_soc[soc] for soc in sector_soc_set
            if soc in rows_by_soc
        ]
        if not occupations:
            continue
        occupations.sort(key=lambda o: (
            0 if o.alignment_status == "aligned" else 1,
            -(o.gap or 0),
            o.title.lower(),
        ))
        sectors.append(SectorEntry(
            sector=sector,
            is_priority=sector in priority_sectors,
            occupations=occupations,
        ))

    return SectorIndex(college=college, sectors=sectors)


# ── Opportunity report ──────────────────────────────────────────────────


def _gather_partnership_opportunities(
    college: str, soc_code: str
) -> list[PartnershipOpportunityEmployer]:
    """Regional employers that hire for the SOC, sorted by NAICS-4
    industry share (BLS OEWS PCT_TOTAL).

    Industry share is the institutional measure of how prominent this
    role is within the employer's industry — a stable cross-employer
    sort key that surfaces the employers for whom this role is most
    central first.
    """
    naics_titles = load_naics4_titles()

    driver = get_driver()
    with driver.session() as session:
        rows = session.run("""
            MATCH (col:College {name: $college})-[:IN_MARKET]->(r:Region)
                  <-[:IN_MARKET]-(emp:Employer)-[:HIRES_FOR]->(occ:Occupation {soc_code: $soc})
            OPTIONAL MATCH (course:Course {college: $college})-[:PREPARES_FOR]->(occ)
            WITH emp, count(DISTINCT course) AS aligned_course_count
            RETURN emp.name AS name,
                   emp.sector AS sector,
                   COALESCE(emp.swp_sectors, []) AS swp_sectors,
                   emp.description AS description,
                   emp.website AS website,
                   emp.naics4 AS naics4,
                   aligned_course_count
        """, college=college, soc=soc_code).data()

    # Build a per-(naics4, soc) industry share map by descending into
    # the OEWS rows for each unique NAICS-4 just once.
    share_cache: dict[str, dict[str, float]] = {}

    def _share(naics4: str | None, soc: str) -> float | None:
        if not naics4:
            return None
        if naics4 not in share_cache:
            oes_rows = oes_socs_for_naics4(naics4)
            share_cache[naics4] = {
                r["soc"]: r["pct_total"] for r in oes_rows if r.get("pct_total")
            }
        return share_cache[naics4].get(soc)

    employers = [
        PartnershipOpportunityEmployer(
            name=r["name"],
            sector=r.get("sector"),
            swp_sectors=list(r.get("swp_sectors") or []),
            description=r.get("description"),
            website=r.get("website"),
            naics4=r.get("naics4"),
            naics_title=naics_titles.get(r.get("naics4")) if r.get("naics4") else None,
            industry_share=_share(r.get("naics4"), soc_code),
            aligned_course_count=r.get("aligned_course_count", 0),
        )
        for r in rows
    ]

    employers.sort(
        key=lambda e: (-(e.industry_share or 0.0), -(e.aligned_course_count or 0), e.name)
    )
    return employers


def _build_swp_evidence(
    college: str,
    soc_code: str,
    soc_title: str,
    annual_wage: int | None,
    annual_openings: int | None,
    growth_rate: float | None,
    curriculum_evidence: list[dict],
) -> SwpEvidence:
    """Tabular regional supply-demand evidence for the SOC.

    Mirrors _assemble_swp_evidence in generate.py but keyed off (college,
    soc) directly rather than running through an employer's hires set.
    """
    from ontology.supply import get_coe_supply

    coe_region = COLLEGE_COE_REGION.get(college, "")
    cip_soc = _load_cip_to_soc()
    cips_for_soc = sorted([cip for cip, socs in cip_soc.items() if soc_code in socs])

    occupations = [
        OccupationEvidence(
            title=soc_title,
            soc_code=soc_code,
            annual_wage=annual_wage,
            annual_openings=annual_openings,
            growth_rate=growth_rate,
            cip_codes=cips_for_soc,
        )
    ]
    total_demand = annual_openings or 0

    # TOP6 codes for the supply lookup come directly from the curriculum
    # evidence's `via_top` — already correctly computed by
    # _gather_aligned_curriculum from the PREPARES_FOR edges' `via_top`
    # property. Previously this code path went through
    # `lookup_top6(course_codes, college)` (MCF lookup), which silently
    # returned an empty set for any college using non-MCF course codes
    # (apprenticeships, college-specific renumbering, noncredit). The
    # silent empty drop was producing zero-supply renderings for SOCs
    # at colleges that genuinely had supply data — e.g. West Hills
    # Lemoore × 49-9041 had supply 3.83 in supply_by_top.csv but the
    # MCF lookup couldn't translate course codes like MM051D to a TOP6,
    # so the SWP block claimed zero. Using via_top directly bypasses
    # MCF entirely; the value was already computed upstream.
    top6_codes: set[str] = set()
    for dept_ev in curriculum_evidence:
        top6_codes.update(dept_ev.get("via_top", []))
    supply_data, total_supply = get_coe_supply(top6_codes, college)
    supply_estimates = [
        SupplyEstimate(
            top_code=s["top_code"],
            top_title=s["top_title"],
            award_level=s["award_level"],
            annual_projected_supply=s["annual_projected_supply"],
        )
        for s in supply_data
    ]
    gap = total_demand - total_supply

    sources = InstitutionalSources(
        coe_region=coe_region,
        coe_region_display=COE_REGION_DISPLAY.get(coe_region, coe_region),
    )

    return SwpEvidence(
        occupations=occupations,
        supply_estimates=supply_estimates,
        department_enrollments=[],  # populated below from gather.py output
        total_demand=total_demand,
        total_supply=total_supply,
        gap=gap,
        coe_region=coe_region,
        sources=sources,
    )


def build_opportunity_report(
    college: str,
    soc_code: str,
    sector_hint: str | None = None,
    top_prefix: str | None = None,
    cte_only: bool = False,
    exclude_tops: frozenset[str] | set[str] | None = None,
) -> OpportunityReport:
    """Assemble the full per-(college, soc) partnership opportunity report.

    Composes:
      - occupation metadata + regional demand (Neo4j + COE)
      - TOP-grouped curriculum coverage (existing _gather_aligned_curriculum)
      - student impact (existing _gather_student_pipeline)
      - regional employer set (Partnership Opportunities), sorted by
        NAICS industry share
      - deterministic narrative (employer-agnostic templates)

    `sector_hint` preserves the user's click-context sector when a SOC
    belongs to multiple PCAH sectors. If supplied and valid for this
    SOC, the report header and narrative use it; otherwise the default
    is the alphabetical first matching sector — same behavior as
    before. Invalid sector hints are silently ignored.

    `top_prefix` optionally scopes the curriculum crosswalk (and, through the
    hero TOP set it derives, the accordion + student pipeline) to a TOP
    division — the SVAMP 09-only lens. Default None ⇒ unscoped, so the
    per-college report is unchanged.

    `cte_only` optionally restricts that same crosswalk to CTE (career-
    technical) TOPs, dropping transfer/academic ones — the SVAMP workforce
    scope. Default False ⇒ the per-college report is unchanged.

    `exclude_tops` optionally drops named TOP6 codes from that same crosswalk
    (and everything the hero TOP set derives) — the SVAMP director's-mandate
    exclusions. Default None ⇒ the per-college report is unchanged.
    """
    driver = get_driver()
    with driver.session() as session:
        occ_row = session.run("""
            MATCH (col:College {name: $college})-[:IN_MARKET]->(r:Region)
                  -[d:DEMANDS]->(occ:Occupation {soc_code: $soc})
            RETURN occ.title AS title,
                   occ.description AS description,
                   d.annual_wage AS annual_wage,
                   d.annual_openings AS annual_openings,
                   d.growth_rate AS growth_rate,
                   d.employment AS employment,
                   COALESCE(r.display_name, r.name) AS region
            ORDER BY d.employment DESC
            LIMIT 1
        """, college=college, soc=soc_code).single()

        if not occ_row:
            # The SOC isn't demanded in the college's region. Fall back to
            # the Occupation node's own metadata so the report still
            # renders (the curriculum coverage section will speak for
            # itself).
            meta = session.run(
                "MATCH (occ:Occupation {soc_code: $soc}) "
                "RETURN occ.title AS title, occ.description AS description",
                soc=soc_code,
            ).single()
            if not meta:
                raise ValueError(f"Occupation {soc_code} not found in graph")
            soc_title = meta["title"] or soc_code
            description = meta.get("description")
            annual_wage = annual_openings = growth_rate = employment = None
            region = ""
        else:
            soc_title = occ_row["title"] or soc_code
            description = occ_row.get("description")
            annual_wage = occ_row["annual_wage"]
            annual_openings = occ_row["annual_openings"]
            growth_rate = occ_row.get("growth_rate")
            employment = occ_row.get("employment")
            region = occ_row["region"]

    # Curriculum crosswalk pathway — the section's hero visualization:
    # the full TOP × CIP institutional prep set with the college's
    # coverage marked. SAM-filtered to occupational (A/B/C/D) so the
    # universe reflects workforce-development scope rather than gen-ed
    # feeders. Computed first because its TOP universe is the canonical
    # "what counts as occupationally relevant" set — the accordion
    # below restricts to it for coherence.
    #
    # The hero visualization is keyed at TOP6 (the granularity at
    # which CCCCO PCAH actually maps to CIPs), but the accordion +
    # student pipeline downstream still filter at TOP4 — deliberately,
    # for two reasons: (1) accordion-hero coherence wants every TOP4
    # family in the hero to also show its taught courses below, and
    # (2) the synthetic student calibration carries an upstream MCF
    # vs DataMart top_code mismatch documented in _gather_student_
    # pipeline that the TOP4 widening absorbs. So we derive a TOP4
    # set from the TOP6 hero universe by truncation — preserving the
    # downstream filter semantics across the v3 hero shape change.
    curriculum_crosswalk = _gather_curriculum_crosswalk(college, soc_code, top_prefix=top_prefix, cte_only=cte_only, exclude_tops=exclude_tops)
    hero_top4s = {t["code"][:4] for t in curriculum_crosswalk.get("tops", [])}

    # Curriculum coverage — per-department accordion of the courses at
    # this college that institutionally prepare for the SOC, restricted
    # to TOPs in the hero universe. The restriction prevents the
    # inverse case where a college teaches a TOP for this SOC but the
    # TOP isn't in the system-wide SAM-occupational set (e.g. Butte's
    # Geography → Environmental Science Tech): without the filter the
    # accordion lists a department the hero can't represent.
    curriculum_evidence = _gather_aligned_curriculum(
        college, soc_code, hero_top4s=hero_top4s,
    )
    aligned_depts = [d["department"] for d in curriculum_evidence]

    # Student impact — hero-filtered to match the accordion. The
    # student pipeline computes its own prep TOP4 set from PREPARES_FOR
    # courses; passing `hero_top4s` intersects that set with the hero
    # universe so the headline count and top-N list never surface
    # students whose only "alignment" is via out-of-universe TOPs
    # (Butte/Geography → 19-4042 case).
    student_stats, top_students = _gather_student_pipeline(
        college, aligned_depts, soc_code, hero_top4s=hero_top4s
    )

    # Regional supply-demand evidence (SWP block).
    swp_evidence = _build_swp_evidence(
        college=college,
        soc_code=soc_code,
        soc_title=soc_title,
        annual_wage=annual_wage,
        annual_openings=annual_openings,
        growth_rate=growth_rate,
        curriculum_evidence=curriculum_evidence,
    )

    # Department enrollments — same query the employer-centric pipeline
    # ran inline; lifted here for the same evidence shape.
    if aligned_depts:
        from partnerships.models import DepartmentEnrollment
        with driver.session() as session:
            de_rows = session.run("""
                MATCH (dept:Department)-[:CONTAINS]->(c:Course {college: $college})
                      <-[:ENROLLED_IN]-(s:Student)
                WHERE dept.name IN $departments
                RETURN dept.name AS department, count(DISTINCT s) AS student_count
                ORDER BY student_count DESC
            """, college=college, departments=aligned_depts).data()
            swp_evidence.department_enrollments = [
                DepartmentEnrollment(department=r["department"], student_count=r["student_count"])
                for r in de_rows
            ]

    # Partnership opportunities — the new section.
    partnership_opportunities = _gather_partnership_opportunities(college, soc_code)

    # Sector this SOC primarily belongs to (for the report header).
    # When a SOC belongs to multiple PCAH sectors, the caller's
    # click-context sector wins (sector_hint), so a SOC viewed from
    # the ICT tab renders as ICT even if it also appears under
    # Agriculture. If no hint is supplied or the hint isn't actually
    # one of this SOC's sectors, fall back to the first alphabetically
    # — the legacy default the navigation surface still uses for
    # listing.
    sector_to_top6 = _load_sector_to_top6()
    matching_sectors = sorted(
        [s for s in sector_to_top6 if soc_code in _sector_socs(s)]
    )
    if sector_hint and sector_hint in matching_sectors:
        sector = sector_hint
    else:
        sector = matching_sectors[0] if matching_sectors else None

    # Is this sector a Strong Workforce Program priority for the college's
    # COE region? Same lookup pattern build_sector_index uses.
    coe_region = COLLEGE_COE_REGION.get(college, "")
    region_priority_sectors = set(COE_REGION_PRIORITY_SECTORS.get(coe_region, []))
    is_sector_priority = sector is not None and sector in region_priority_sectors

    # Narrative composition (employer-agnostic, deterministic).
    total_aligned_courses = sum(len(d.get("courses", [])) for d in curriculum_evidence)
    coe_region_display = swp_evidence.sources.coe_region_display or swp_evidence.coe_region
    narrative = build_opportunity_narrative(
        college=college,
        sector_display=sector or "",
        soc_code=soc_code,
        soc_title=soc_title,
        annual_wage=annual_wage,
        annual_openings=annual_openings,
        employment=employment,
        growth_rate=growth_rate,
        coe_region_display=coe_region_display,
        total_aligned_courses=total_aligned_courses,
        n_departments=len(curriculum_evidence),
        total_in_aligned_departments=student_stats.get("total_in_aligned_departments", 0),
        n_employer_opportunities=len(partnership_opportunities),
    )

    return OpportunityReport(
        college=college,
        sector=sector,
        is_sector_priority=is_sector_priority,
        soc_code=soc_code,
        soc_title=soc_title,
        description=description,
        regions=[region] if region else [],
        executive_summary=narrative["executive_summary"],
        occupational_demand=narrative["occupational_demand"],
        curriculum_alignment=narrative["curriculum_alignment"],
        student_impact=narrative["student_impact"],
        partnership_opportunities_narrative=narrative["partnership_opportunities"],
        opportunity_evidence=[
            OccupationEvidence(
                title=soc_title,
                soc_code=soc_code,
                annual_wage=annual_wage,
                employment=employment,
                annual_openings=annual_openings,
                growth_rate=growth_rate,
                cip_codes=swp_evidence.occupations[0].cip_codes if swp_evidence.occupations else [],
            )
        ],
        curriculum_evidence=[DepartmentEvidence(**d) for d in curriculum_evidence],
        curriculum_crosswalk=CurriculumCrosswalk(**curriculum_crosswalk),
        student_evidence=StudentEvidence(
            total_in_program=student_stats.get("total_in_program", 0),
            total_in_aligned_departments=student_stats.get("total_in_aligned_departments", 0),
            top_students=[StudentSummaryEvidence(**s) for s in top_students],
        ),
        swp_evidence=swp_evidence,
        partnership_opportunities=partnership_opportunities,
    )
