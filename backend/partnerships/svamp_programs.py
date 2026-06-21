"""SVAMP Programs lens — the supply-side, TOP6-centric view of the SVAMP
partnership landscape (the dual of the occupation-centric svamp.py).

THE anchoring invariant — supply and demand are owned by different axes:
  - SUPPLY (awards, enrollment) is OWNED BY PROGRAMS (TOP6) and is additive
    across the five member colleges. A program's awards-per-year and
    enrollment-per-term sum cleanly across colleges (institutional).
  - DEMAND (annual openings/wages) is OWNED BY OCCUPATIONS (SOC) and is
    regional. The TOP-CIP-SOC crosswalk is many-to-many, so demand is shown
    per SOC as a RELATIONSHIP (the SOCs a program feeds) and is NEVER summed
    across those SOCs into a per-program demand or gap number — that would
    double-count. There is deliberately no gap field in this surface.

Scope = the SVAMP program universe: every TOP6 in DIVISION 09 (Engineering &
Industrial Technologies — see svamp.SVAMP_TOP_DIVISION) whose TOP-CIP-SOC
crosswalk intersects the twelve SVAMP SOCs, minus the director's-mandate
exclusions (svamp.SVAMP_MANDATE_EXCLUDED_TOPS — division-09 programs whose
employment flows run to other industry verticals). The 09 scope is the
consortium's programmatic domain per the SVAMP director — a categorical
division filter applied on top of the faithful crosswalk (the crosswalk itself
is never edited), so non-engineering feeders it legitimately links (e.g.
Commercial Music → 17-3029) fall out of scope rather than being hand-curated
away; the mandate exclusions are the same authority refining its own scope
where the division proxy over-includes. Reuses svamp.py's
scope constants/helpers, the Program (TOP6) AWARDED/ENROLLED graph reads,
get_wage_outcomes (TOP6-grain statewide), and the TOP-CIP-SOC crosswalk in
ontology.crosswalks.
"""

from __future__ import annotations

import re
from typing import Callable

from pydantic import BaseModel

from ontology.crosswalks import (
    _load_top_to_cip,
    top6_to_soc,
    load_top_titles,
    top6_to_cips_for_soc,
    load_cip_titles,
)
from ontology.regions import COE_REGION_DISPLAY
from ontology.schema import get_driver
from ontology.programs import get_wage_outcomes
from ontology.supply import get_coe_supply
from partnerships.gather import _gather_curriculum_crosswalk
from partnerships.graph_reads import latest_academic_year, regional_demand
from partnerships.models import CurriculumCrosswalk, PartnershipOpportunityEmployer
from partnerships.opportunity import _gather_partnership_opportunities
from partnerships.opportunity_narrative import build_occupational_demand
from partnerships.svamp import (
    AWARD_YEARS_SHOWN,
    _term_excluded,
    _term_sort_key,
    SvampWage,
)
from partnerships.landscape import LandscapeSpec, SVAMP_SPEC


# ── Response shapes ───────────────────────────────────────────────────────


class TopSummary(BaseModel):
    """One TOP6 in the supply treemap universe. `awards_total` /
    `enrollment_total` are the latest-period magnitudes SUMMED across the five
    colleges (additive supply). `soc_count` is the crosswalk cardinality — how
    many of the twelve SVAMP SOCs this program feeds — a relationship measure,
    never a demand figure."""
    top6: str
    name: str
    awards_total: int = 0          # Σ latest award-year awards across colleges
    enrollment_total: int = 0      # Σ latest term enrollment across colleges
    n_colleges_offering: int = 0   # # member colleges with ≥1 course for this TOP
    soc_count: int = 0


class ProgramCoverageCell(BaseModel):
    """One (college, TOP) cell of the supply coverage matrix — the dual of the
    occupations grid cell. The cell keys on *activity*, not catalog presence:
    `enrolled` = the college has ENROLLED enrollment under this TOP; `awards` =
    its latest-award-year credentials (0 if none). The frontend derives the
    coverage level from the pair — covered = enrolled & awards (a full pipeline),
    partial = one signal but not the other, gap = neither. `teaches` (≥1 tagged
    09 course) is retained as the catalog signal that drives `n_colleges_offering`
    but no longer gates the cell — a program can confer (095630) or enroll
    (095200) without a course tagged to its own code, owing to the parent-code
    tagging seam, and still belongs on the supply grid."""
    college: str
    top6: str
    teaches: bool = False
    enrolled: bool = False
    awards: int = 0


class ProgramCoverageMatrix(BaseModel):
    colleges: list[str]                 # colleges order — matrix columns
    cells: list[ProgramCoverageCell]    # flat (college × TOP) coverage


class ProgramsLandscape(BaseModel):
    region: str
    region_display: str
    sector: str
    latest_award_year: str | None = None  # most recent reported award year (supply lead)
    n_colleges: int
    tops: list[TopSummary]
    matrix: ProgramCoverageMatrix | None = None  # per-(college, TOP) coverage grid
    # True for rule-bearing instances (BACCC, sector-derived SMCCD): the coverage
    # cell is gated on AWARDS — enrollment without a completer is not realized
    # supply, so it reads as a gap, not "partial" (a cell with awards but no current
    # enrollment stays partial — real-but-thinning supply). The curated SVAMP
    # instance carries no rule and keeps the enrolled-OR-awarded coverage.
    coverage_awards_only: bool = False


class OccupationDemand(BaseModel):
    """A SOC this TOP feeds, with its REGIONAL demand. Listed per SOC; the
    openings are the single regional value — never summed across the SOCs a
    program feeds, never multiplied by the college count."""
    soc_code: str
    title: str
    annual_wage: int | None = None
    annual_openings: int | None = None


class ProgramCrosswalkCip(BaseModel):
    code: str
    title: str = ""


class ProgramCrosswalkSoc(BaseModel):
    """A SVAMP SOC this TOP feeds, tagged with the CIPs that bridge the TOP to
    it (the right column of the TOP-anchored pathway)."""
    code: str
    title: str
    cips: list[str] = []   # CIPs (of this TOP) that bridge to this SOC


class ProgramCrosswalk(BaseModel):
    """TOP-anchored TOP-CIP-SOC pathway — the dual of the occupation report's
    SOC-anchored curriculum_crosswalk. One focused TOP fans out through its
    bridging CIPs to the SVAMP SOCs it prepares students for. Faithful to the
    institutional crosswalk (PCAH TOP-CIP + NCES CIP-SOC); the SOC set is the
    09-scoped relevant SOCs the program feeds."""
    top6: str
    top_name: str
    cips: list[ProgramCrosswalkCip] = []   # union of bridging CIPs (middle column)
    socs: list[ProgramCrosswalkSoc] = []   # relevant SVAMP SOCs (right column)


class CollegeSeries(BaseModel):
    """One college's supply series for the focused TOP, aligned to the report's
    shared award-year / enrollment-term axis. (Summing across colleges yields
    the consortium total — the chart's default aggregated line.)"""
    college: str
    vals: list[int | None] = []


class AwardTypeSeries(BaseModel):
    """One (college, credential-type) awards series for the focused TOP, aligned
    to the report's award_years axis — the per-type decomposition of
    awards_by_college (a college's types sum to its flat series each year).
    `award_type` is the DataMart credential-type name verbatim (e.g.
    "Certificate requiring 16 to fewer than 30 semester units"); series are
    ordered by credential weight — degrees, then certificates, then noncredit
    awards, larger bands first within each class (_award_type_sort_key)."""
    college: str
    award_type: str
    vals: list[int] = []


class EnrollmentCreditSeries(BaseModel):
    """One (college, credit-family) enrollment series for the focused TOP,
    aligned to enrollment_terms — the per-family decomposition of
    enrollment_by_college (a college's families sum to its flat series each
    term). `credit_type` is the DataMart family verbatim ("Credit - Degree
    Applicable" / "Credit - Not Degree Applicable" / "Non-Credit"), in that
    order (_credit_type_sort_key). The decomposition is the integrity guarantee
    for mixing families in the flat series: credit and noncredit headcounts are
    not the same kind of number (noncredit sections are open-entry/repeatable),
    so the blend must always be one click from its parts."""
    college: str
    credit_type: str
    vals: list[int | None] = []


class ProgramCourse(BaseModel):
    code: str
    name: str
    description: str = ""
    learning_outcomes: list[str] = []
    top_code: str | None = None


class CollegeCourses(BaseModel):
    """Per-school curriculum for the focused TOP. All five colleges are listed
    (empty `courses` ⇒ the college teaches no course tagged with this TOP), so
    the accordion can render the gap colleges dimmed — consortium coverage at a
    glance."""
    college: str
    courses: list[ProgramCourse] = []


class ProgramReport(BaseModel):
    top6: str
    name: str
    region: str
    region_display: str
    sector: str
    award_years: list[str] = []
    enrollment_terms: list[str] = []
    occupations: list[OccupationDemand] = []         # demand only, per SOC, never summed
    enrollment_by_college: list[CollegeSeries] = []  # aligned to enrollment_terms
    awards_by_college: list[CollegeSeries] = []       # aligned to award_years
    awards_by_type: list[AwardTypeSeries] = []        # per-(college, credential-type) decomposition
    enrollment_by_credit: list[EnrollmentCreditSeries] = []  # per-(college, credit-family) decomposition
    wages: list[SvampWage] = []
    curriculum_by_college: list[CollegeCourses] = []
    crosswalk: ProgramCrosswalk | None = None  # TOP-anchored TOP-CIP-SOC pathway
    college: str | None = None  # set ⇒ targeted (college, TOP) slice; None ⇒ consortium


class SvampOccupationReport(BaseModel):
    """The SVAMP aggregated-occupation report — the dual of ProgramReport. One
    SOC, read consortium-wide: regional demand (occupation-grain wage),
    consortium supply (Σ COE-projected completions over the colleges for the
    SOC's 09 feeding TOPs) and the resulting GAP, the feeding programs sized by
    awards, per-college award/enrollment series + curriculum, and the
    SOC-anchored crosswalk marked taught-by-any-member-college.

    The gap lives here — the occupation axis owns demand — whereas the program
    report stays gap-less. A feeding TOP serves multiple SOCs; its supply/awards
    count toward EACH SOC it feeds and are never netted across SOCs."""
    soc_code: str
    title: str
    description: str | None = None         # occupation description (Occupation node)
    sector: str
    region: str
    region_display: str
    occupational_demand: str = ""          # regional-demand narrative (shared composer)
    annual_openings: int | None = None     # regional demand, taken once
    annual_wage: int | None = None         # occupation-grain demand wage
    growth_rate: float | None = None
    employment: int | None = None          # regional current employment
    consortium_supply: float = 0.0          # Σ over colleges of COE-projected completions
    gap: int = 0                            # annual_openings − consortium_supply
    award_years: list[str] = []
    enrollment_terms: list[str] = []
    feeding_tops: list[TopSummary] = []     # the SOC's 09 feeding TOPs, consortium awards
    awards_by_college: list[CollegeSeries] = []      # Σ over feeding TOPs, per college
    enrollment_by_college: list[CollegeSeries] = []
    curriculum_by_college: list[CollegeCourses] = []
    crosswalk: CurriculumCrosswalk | None = None     # SOC-anchored, consortium-union taught
    # Regional employers hiring for this SOC (HIRES_FOR, region-scoped) — the
    # same candidate-partner set the per-college targeted report surfaces,
    # viewed at the consortium grain. Employers are regional, so the set is
    # identical regardless of which member college is the lens.
    partnership_opportunities: list[PartnershipOpportunityEmployer] = []
    partnership_opportunities_narrative: str = ""


# ── Scope ─────────────────────────────────────────────────────────────────


def relevant_tops(spec: LandscapeSpec = SVAMP_SPEC) -> dict[str, set[str]]:
    """The SVAMP program universe: {top6 -> the SVAMP SOCs it feeds} for every
    TOP6 in DIVISION 09 (Engineering & Industrial Technologies — see
    svamp.SVAMP_TOP_DIVISION) whose TOP-CIP-SOC crosswalk intersects the twelve
    SVAMP SOCs, minus the director's-mandate exclusions (both applied via
    is_svamp_top). The filters are scope on the faithful crosswalk (the
    crosswalk is never edited), reflecting the consortium's programmatic
    domain per the SVAMP director."""
    all_top6 = list(_load_top_to_cip().keys())
    targets = set(spec.socs)
    universe = {
        top6: (socs & targets)
        for top6, socs in top6_to_soc(all_top6).items()
        if (socs & targets) and spec.in_scope(top6)
    }
    # Rule-bearing instances apply the supply gate at the PROGRAM grain too:
    # awards are the supply metric, so a program with no awarded completer in any
    # member college (enrollment-only) is not realized supply and never enters the
    # matrix/treemap/counts. This matches resolve()'s occupation-grain awards gate
    # (active_tops), and because every surviving occupation already requires an
    # awards-bearing feeder, dropping award-less programs cannot orphan a row.
    # The curated SVAMP spec carries no rule and keeps the full universe.
    rule = spec.soc_rule
    if rule is not None and rule.active and universe:
        awarded = _awarded_tops(spec, universe)
        universe = {t: s for t, s in universe.items() if t in awarded}
    return universe


def _awarded_tops(spec: LandscapeSpec, tops) -> set[str]:
    """TOP6s with >=1 awarded completer in the LATEST reported year, in any member
    college — the supply gate's program grain. Matches resolve()'s active_tops and
    the coverage-matrix's latest-year cells, so a kept TOP is exactly one with
    current supply; a program last awarded in an older year is dormant and drops
    (e.g. 210530 Industrial & Transportation Security, which last awarded a
    completer in 2023-24)."""
    with get_driver().session() as session:
        latest = latest_academic_year(session)
        rows = session.run(
            "MATCH (p:Program)-[a:AWARDED]->(ay:AcademicYear) "
            "WHERE p.college IN $colleges AND p.top6 IN $tops "
            "AND ay.year = $latest AND coalesce(a.count, 0) > 0 "
            "RETURN DISTINCT p.top6 AS top6",
            colleges=list(spec.colleges), tops=list(tops), latest=latest,
        ).data()
    return {r["top6"] for r in rows}


# ── Builders (I/O) ──────────────────────────────────────────────────────────


def build_programs_landscape(spec: LandscapeSpec = SVAMP_SPEC) -> ProgramsLandscape:
    colleges = list(spec.colleges)
    region = spec.resolve_region()
    universe = relevant_tops(spec)
    tops = list(universe.keys())
    titles = load_top_titles()
    driver = get_driver()

    with driver.session() as session:
        # Awards per (college, top6, year) and enrollment per (college, top6,
        # term), scoped to the relevant TOPs + member colleges.
        awards_rows = session.run(
            """
            MATCH (pr:Program)-[a:AWARDED]->(ay:AcademicYear)
            WHERE pr.college IN $colleges AND pr.top6 IN $tops
            RETURN pr.college AS college, pr.top6 AS top6, ay.year AS year,
                   toInteger(sum(coalesce(a.count, 0))) AS awards
            """,
            colleges=colleges, tops=tops,
        ).data()
        enroll_rows = session.run(
            """
            MATCH (pr:Program)-[e:ENROLLED]->(t:Term)
            WHERE pr.college IN $colleges AND pr.top6 IN $tops
            RETURN pr.college AS college, pr.top6 AS top6, t.term AS term,
                   toInteger(sum(e.count)) AS count
            """,
            colleges=colleges, tops=tops,
        ).data()
        # Per-(college, TOP) course counts — drives both n_colleges_offering
        # and the coverage matrix (teaches = n > 0). 09-scoped via `tops`.
        course_rows = session.run(
            """
            MATCH (c:Course)
            WHERE c.college IN $colleges AND c.top_code IN $tops
            RETURN c.college AS college, c.top_code AS top6,
                   count(DISTINCT c.code) AS n
            """,
            colleges=colleges, tops=tops,
        ).data()

    return _assemble_landscape(
        region=region,
        region_display=COE_REGION_DISPLAY.get(region, region),
        universe=universe,
        titles=titles,
        awards_rows=awards_rows,
        enroll_rows=enroll_rows,
        coverage_rows=course_rows,
        spec=spec,
    )


def build_program_report(top6: str, college: str | None = None, *, spec: LandscapeSpec = SVAMP_SPEC) -> ProgramReport:
    """The TOP6 program report. `college=None` ⇒ the consortium-aggregated view
    (per-college series across all members). `college` set ⇒ the targeted
    (college, TOP) slice: award / enrollment / curriculum scoped to that one
    college, while demand (Occupations Served), the TOP-anchored crosswalk, and
    the statewide TOP6-grain wages are unchanged."""
    colleges = list(spec.colleges)
    region = spec.resolve_region()
    universe = relevant_tops(spec)
    socs = sorted(universe.get(top6, set()))
    titles = load_top_titles()
    driver = get_driver()
    colleges_filter = [college] if college else colleges

    with driver.session() as session:
        demand_rows = list(regional_demand(session, region, socs).values())
        # Grouped by credential type (the AWARDED edge key) — the assembly
        # derives both the flat per-college series (summing types back out)
        # and the per-(college, type) decomposition from these rows.
        awards_rows = session.run(
            """
            MATCH (pr:Program {top6: $top6})-[a:AWARDED]->(ay:AcademicYear)
            WHERE pr.college IN $colleges
            RETURN pr.college AS college, ay.year AS year,
                   a.award_type AS award_type,
                   toInteger(sum(coalesce(a.count, 0))) AS awards
            """,
            top6=top6, colleges=colleges_filter,
        ).data()
        # Grouped by credit family (the ENROLLED edge key) — the assembly
        # derives both the flat per-college series (summing families back out)
        # and the per-(college, family) decomposition from these rows.
        enroll_rows = session.run(
            """
            MATCH (pr:Program {top6: $top6})-[e:ENROLLED]->(t:Term)
            WHERE pr.college IN $colleges
            RETURN pr.college AS college, t.term AS term,
                   e.credit_type AS credit_type,
                   toInteger(sum(e.count)) AS count
            """,
            top6=top6, colleges=colleges_filter,
        ).data()
        course_rows = session.run(
            """
            MATCH (c:Course)
            WHERE c.college IN $colleges AND c.top_code = $top6
            RETURN c.college AS college, c.code AS code, c.name AS name,
                   coalesce(c.description, '') AS description,
                   coalesce(c.learning_outcomes, []) AS learning_outcomes,
                   c.top_code AS top_code
            ORDER BY c.college, c.code
            """,
            top6=top6, colleges=colleges_filter,
        ).data()

    name = titles.get(top6) or top6
    # TOP-anchored crosswalk, over the SVAMP SOCs this program feeds (demanded),
    # in the same openings-desc order as the occupations table.
    socs_ordered = [
        (r["soc_code"], r.get("title") or r["soc_code"])
        for r in sorted(demand_rows, key=lambda r: -(r.get("annual_openings") or 0))
    ]
    crosswalk = _build_program_crosswalk(top6, name, socs_ordered)

    return _assemble_program_report(
        top6=top6,
        name=name,
        region=region,
        region_display=COE_REGION_DISPLAY.get(region, region),
        demand_rows=demand_rows,
        awards_rows=awards_rows,
        enroll_rows=enroll_rows,
        course_rows=course_rows,
        wage_fn=get_wage_outcomes,
        crosswalk=crosswalk,
        college=college,
        spec=spec,
    )


def _build_program_crosswalk(
    top6: str, top_name: str, socs: list[tuple[str, str]]
) -> ProgramCrosswalk:
    """Assemble the TOP-anchored pathway: the focused TOP → its bridging CIPs →
    each relevant SVAMP SOC. `socs` is [(soc_code, title)] in display order.
    Bridging CIPs per (TOP, SOC) come from the PCAH TOP-CIP + NCES CIP-SOC
    crosswalk (top6_to_cips_for_soc); CIP titles from NCES. The middle column is
    the union of those CIPs. Crosswalk-faithful — no curation."""
    cip_titles = load_cip_titles()
    cip_union: dict[str, str] = {}
    soc_rows: list[ProgramCrosswalkSoc] = []
    for soc, title in socs:
        cips = top6_to_cips_for_soc(top6, soc)
        soc_rows.append(ProgramCrosswalkSoc(code=soc, title=title, cips=cips))
        for c in cips:
            cip_union[c] = cip_titles.get(c, "")
    return ProgramCrosswalk(
        top6=top6,
        top_name=top_name,
        cips=[ProgramCrosswalkCip(code=c, title=t) for c, t in sorted(cip_union.items())],
        socs=soc_rows,
    )


def build_svamp_occupation(
    soc: str, *, spec: LandscapeSpec = SVAMP_SPEC, college: str | None = None,
    include_employers: bool = True,
) -> SvampOccupationReport:
    """Consortium aggregated-occupation report for one SOC — the dual of
    build_program_report. Reuses the program supply machinery (the SOC's 09
    feeding TOPs, their per-college awards/enrollment/courses), get_coe_supply
    for the consortium completions, and the SOC-anchored crosswalk in
    consortium-union mode (taught by any member college).

    `college` scopes ONLY the SOC-anchored crosswalk's taught/active marking to
    that one member college — for the dashboard's college-scope occupation view,
    where the pathway must light just the selected school's feeding TOPs, not the
    consortium union. Every other field stays consortium-grain (the dashboard's
    college scope reads the per-college landscape cell for its awards/enrollment
    charts, and the regional-demand quartet is scope-invariant). Omitted ⇒ the
    consortium-union crosswalk, unchanged."""
    colleges = list(spec.colleges)
    region = spec.resolve_region()
    universe = relevant_tops(spec)
    feeding = sorted(t for t, socs in universe.items() if soc in socs)
    titles = load_top_titles()
    driver = get_driver()

    with driver.session() as session:
        demand = regional_demand(session, region, [soc]).get(soc)
        awards_rows = session.run(
            """
            MATCH (pr:Program)-[a:AWARDED]->(ay:AcademicYear)
            WHERE pr.college IN $colleges AND pr.top6 IN $tops
            RETURN pr.college AS college, pr.top6 AS top6, ay.year AS year,
                   toInteger(sum(coalesce(a.count, 0))) AS awards
            """,
            colleges=colleges, tops=feeding,
        ).data()
        enroll_rows = session.run(
            """
            MATCH (pr:Program)-[e:ENROLLED]->(t:Term)
            WHERE pr.college IN $colleges AND pr.top6 IN $tops
            RETURN pr.college AS college, pr.top6 AS top6, t.term AS term,
                   toInteger(sum(e.count)) AS count
            """,
            colleges=colleges, tops=feeding,
        ).data()
        course_rows = session.run(
            """
            MATCH (c:Course)
            WHERE c.college IN $colleges AND c.top_code IN $tops
            RETURN c.college AS college, c.top_code AS top6, c.code AS code, c.name AS name,
                   coalesce(c.description, '') AS description,
                   coalesce(c.learning_outcomes, []) AS learning_outcomes, c.top_code AS top_code
            ORDER BY c.college, c.code
            """,
            colleges=colleges, tops=feeding,
        ).data()

    # Consortium supply: Σ over members of COE-projected completions for the
    # feeding TOPs (the per-SOC slice of combined_supply). Delegated so the
    # member iteration lives in the helper, never shadowing `college` here.
    consortium_supply = _consortium_supply(feeding, colleges)

    # SOC-anchored crosswalk, 09 + CTE-scoped minus the director's-mandate
    # exclusions. _crosswalk_taught_scope picks consortium-union vs single-
    # college taught marking from `college`; everything else is regional.
    taught_college, union_colleges = _crosswalk_taught_scope(college, colleges)
    crosswalk = _gather_curriculum_crosswalk(
        # Vocational instances have no division prefix; "" matches all top_codes
        # and cte_only (True for them) keeps the gather helper's CTE filter.
        taught_college, soc,
        top_prefix=(spec.top_divisions[0] if spec.top_divisions else ""),
        union_colleges=union_colleges, cte_only=spec.cte_only,
        exclude_tops=spec.excluded_tops,
    )

    report = _assemble_occupation(
        soc=soc,
        title=(demand["title"] if demand else None) or soc,
        description=demand["description"] if demand else None,
        region=region,
        region_display=COE_REGION_DISPLAY.get(region, region),
        annual_openings=demand["annual_openings"] if demand else None,
        annual_wage=demand["annual_wage"] if demand else None,
        growth_rate=demand["growth_rate"] if demand else None,
        employment=demand["employment"] if demand else None,
        consortium_supply=consortium_supply,
        feeding=feeding,
        universe=universe,
        titles=titles,
        awards_rows=awards_rows,
        enroll_rows=enroll_rows,
        course_rows=course_rows,
        crosswalk=crosswalk,
        spec=spec,
    )
    # Partnership Opportunities — regional employers hiring for this SOC. The
    # gather is region-scoped (any member college resolves to the same Bay
    # market), so this is the consortium-grain view of the same candidate set
    # the per-college targeted report surfaces. aligned_course_count (the only
    # college-specific field) is not rendered, so the passed college is moot.
    #
    # Skipped when include_employers is False: the dashboard occupations lens
    # never renders this list, and the unbounded regional gather (hundreds of
    # employers, each with description/website) is the dominant cost and ~94% of
    # the payload weight of this report. Opting out keeps the field at its empty
    # default for that surface; the report surfaces keep the default (True).
    if include_employers:
        report.partnership_opportunities = _gather_partnership_opportunities(colleges[0], soc)
        report.partnership_opportunities_narrative = (
            f"Regional employers hiring for {report.title}, ranked by how central the role "
            f"is to each firm's industry — candidate partners for the consortium's colleges "
            f"to build or deepen this pathway."
        )
    return report


# ── Assembly (pure — no I/O, so the invariants are unit-testable) ────────────


def _consortium_supply(
    feeding: list[str],
    colleges: tuple[str, ...] | list[str],
    supply_fn: Callable[[set[str], str], tuple[list, float]] = get_coe_supply,
) -> float:
    """Σ over member colleges of COE-projected completions for the SOC's
    feeding TOPs — the per-SOC slice of the consortium supply (institutional,
    additive). Pure (supply_fn injectable) so the institutional-sum invariant
    is unit-testable without a graph, mirroring svamp._assemble_landscape.

    Owning the member iteration HERE is the point: it keeps the loop variable
    out of any builder that also carries a single-college `college` scope
    argument, so the two can never collide (see the engine convention in
    landscape.py — the `for college in colleges` shadow that this helper
    retired)."""
    feeding_set = set(feeding)
    if not feeding_set:
        return 0.0
    return sum(supply_fn(feeding_set, member)[1] for member in colleges)


def _crosswalk_taught_scope(
    college: str | None, colleges: tuple[str, ...] | list[str],
) -> tuple[str, list[str] | None]:
    """The (taught-college, union-colleges) arguments for the SOC-anchored
    crosswalk's taught/active marking. A single `college` lights only its own
    feeding TOPs (the single-college branch, union_colleges=None); None ⇒ the
    consortium union over every member. Pure and named so the consortium-vs-
    college contract is one unit-testable decision, not an inline ternary at
    the I/O call site."""
    if college:
        return (college, None)
    return ("", list(colleges))


def _award_years_axis(years: set[str]) -> list[str]:
    """Most-recent AWARD_YEARS_SHOWN reported award years, chronologically."""
    return sorted(years)[-AWARD_YEARS_SHOWN:]


def _enroll_terms_axis(terms: set[str]) -> list[str]:
    """Chronologically-sorted enrollment terms, excluding structurally-low
    summer terms and the export-boundary terms (svamp._term_excluded)."""
    return sorted({t for t in terms if not _term_excluded(t)}, key=_term_sort_key)


# Credential classes in display order: degrees, then certificates, then
# noncredit awards (matched as substrings of the DataMart name).
_AWARD_TYPE_CLASSES = ("associate", "certificate", "noncredit")


def _award_type_sort_key(award_type: str) -> tuple[int, int, str]:
    """Credential-weight ordering for the per-type award series: degrees first,
    then certificates, then noncredit awards; within a class, larger bands first
    (the first number in the DataMart name is the band's lower bound — degrees
    carry none and tie-break by name)."""
    low = award_type.lower()
    rank = next((i for i, k in enumerate(_AWARD_TYPE_CLASSES) if k in low),
                len(_AWARD_TYPE_CLASSES))
    m = re.search(r"\d+", award_type)
    return (rank, -int(m.group()) if m else 0, award_type)


# Credit families in display order: degree-applicable credit leads (the
# traditional pipeline), then non-degree-applicable credit, then noncredit.
_CREDIT_FAMILY_ORDER = ("Credit - Degree Applicable", "Credit - Not Degree Applicable", "Non-Credit")


def _credit_type_sort_key(credit_type: str) -> tuple[int, str]:
    """Fixed family ordering for the per-family enrollment series; unknown
    families sort last by name."""
    try:
        return (_CREDIT_FAMILY_ORDER.index(credit_type), credit_type)
    except ValueError:
        return (len(_CREDIT_FAMILY_ORDER), credit_type)


def _assemble_landscape(
    region: str,
    region_display: str,
    universe: dict[str, set[str]],
    titles: dict[str, str],
    awards_rows: list[dict],
    enroll_rows: list[dict],
    coverage_rows: list[dict] | None = None,
    *,
    spec: LandscapeSpec = SVAMP_SPEC,
) -> ProgramsLandscape:
    """Size each relevant TOP by latest-period supply SUMMED across colleges.

    awards_total = Σ over colleges of the latest reported award-year's awards
    (annual conferred, mirroring the demand treemap's annual-openings sizing).
    enrollment_total = the PEAK consortium term enrollment (max over terms of the
    across-colleges sum) — the single latest term is too sparsely reported to
    size by, whereas peak term is non-zero for any program with enrollment and
    reads as the program's enrollment scale. Both are additive (program-owned).
    soc_count is the crosswalk cardinality (a relationship, not demand).
    """
    colleges = list(spec.colleges)
    latest_year = max((r["year"] for r in awards_rows if r["year"]), default=None)

    awards_total: dict[str, int] = {}
    for r in awards_rows:
        if r["year"] == latest_year:
            awards_total[r["top6"]] = awards_total.get(r["top6"], 0) + (r["awards"] or 0)

    # Σ enrollment across colleges per (top, term), then peak term per top.
    per_top_term: dict[tuple[str, str], int] = {}
    for r in enroll_rows:
        term = r["term"]
        if not term or _term_excluded(term):
            continue
        per_top_term[(r["top6"], term)] = per_top_term.get((r["top6"], term), 0) + (r["count"] or 0)
    enroll_total: dict[str, int] = {}
    for (top6, _term), c in per_top_term.items():
        enroll_total[top6] = max(enroll_total.get(top6, 0), c)

    # Per-(college, TOP) coverage → n_colleges_offering + the coverage matrix.
    coverage_rows = coverage_rows or []
    teaches: set[tuple[str, str]] = {
        (r["college"], r["top6"]) for r in coverage_rows if (r.get("n") or 0) > 0
    }
    n_colleges_by_top: dict[str, int] = {}
    for _c, _t in teaches:
        n_colleges_by_top[_t] = n_colleges_by_top.get(_t, 0) + 1
    # Per-(college, TOP) latest-year awards for the matrix cells.
    awards_cell: dict[tuple[str, str], int] = {}
    for r in awards_rows:
        if r["year"] == latest_year:
            awards_cell[(r["college"], r["top6"])] = r["awards"] or 0
    # Per-(college, TOP) enrollment presence — any non-excluded term with a
    # positive count. Drives the cell's "active pipeline" signal (same term
    # exclusion as enroll_total above, for consistency).
    enrolled_cell: set[tuple[str, str]] = {
        (r["college"], r["top6"])
        for r in enroll_rows
        if (r["count"] or 0) > 0
        and r["term"]
        and not _term_excluded(r["term"])
    }

    tops = [
        TopSummary(
            top6=top6,
            name=titles.get(top6) or top6,
            awards_total=awards_total.get(top6, 0),
            enrollment_total=enroll_total.get(top6, 0),
            n_colleges_offering=n_colleges_by_top.get(top6, 0),
            soc_count=len(socs),
        )
        for top6, socs in universe.items()
    ]
    # Rank by supply (awards primary), then enrollment, then breadth — the
    # treemap reads strongest-supply-first like the demand treemap.
    tops.sort(key=lambda t: (-t.awards_total, -t.enrollment_total, -t.soc_count, t.top6))

    # Coverage matrix — one cell per (member college × relevant TOP), so gap
    # cells (no enrollment, no awards) are present for the grid to render.
    cells = [
        ProgramCoverageCell(
            college=college,
            top6=top6,
            teaches=(college, top6) in teaches,
            enrolled=(college, top6) in enrolled_cell,
            awards=awards_cell.get((college, top6), 0),
        )
        for top6 in universe
        for college in colleges
    ]
    matrix = ProgramCoverageMatrix(colleges=list(colleges), cells=cells)

    return ProgramsLandscape(
        region=region,
        region_display=region_display,
        sector=spec.sector,
        latest_award_year=latest_year,
        n_colleges=len(colleges),
        tops=tops,
        matrix=matrix,
        coverage_awards_only=(spec.soc_rule is not None and spec.soc_rule.active),
    )


def _assemble_program_report(
    top6: str,
    name: str,
    region: str,
    region_display: str,
    demand_rows: list[dict],
    awards_rows: list[dict],
    enroll_rows: list[dict],
    course_rows: list[dict],
    wage_fn: Callable[[str], list],
    crosswalk: ProgramCrosswalk | None = None,
    college: str | None = None,
    *,
    spec: LandscapeSpec = SVAMP_SPEC,
) -> ProgramReport:
    """Pure assembly of a TOP report.

    - occupations: one row per crosswalk SOC, demand taken once (regional);
      never summed across SOCs, never multiplied by college count.
    - awards_by_college / enrollment_by_college: one series per college that has
      data, aligned to the shared axes (a college without a given year/term ⇒ 0
      awards / None enrollment). Summing across colleges (client-side) gives the
      aggregated consortium line. awards_rows may carry one row per (college,
      year, award_type); the flat per-college series sums the types back out.
    - awards_by_type: the per-(college, credential-type) decomposition of the
      flat series, in credential-weight order (_award_type_sort_key). Rows
      without an award_type (pre-split callers) simply yield no decomposition.
    - enrollment_by_credit: the per-(college, credit-family) decomposition of
      the flat enrollment series, in fixed family order (_credit_type_sort_key).
      enroll_rows may carry one row per (college, term, credit_type); the flat
      series sums the families back out — so the flat line is ALL instructional
      activity (credit + noncredit), with the decomposition as the integrity
      guarantee. Rows without a credit_type yield no decomposition.
    - curriculum_by_college: all five colleges, empty where untaught.
    - NO gap or per-program demand field by construction.
    """
    colleges = list(spec.colleges)
    occupations = [
        OccupationDemand(
            soc_code=r["soc_code"],
            title=r.get("title") or r["soc_code"],
            annual_wage=r.get("annual_wage"),
            annual_openings=r.get("annual_openings"),
        )
        for r in sorted(demand_rows, key=lambda r: -(r.get("annual_openings") or 0))
    ]

    award_years = _award_years_axis({r["year"] for r in awards_rows if r["year"]})
    enrollment_terms = _enroll_terms_axis({r["term"] for r in enroll_rows if r["term"]})

    # Flat per-college totals (summing the credential types back out) and the
    # per-(college, type) decomposition from the same rows.
    awards_by: dict[str, dict[str, int]] = {}
    by_type: dict[tuple[str, str], dict[str, int]] = {}
    for r in awards_rows:
        year, n = r["year"], r["awards"] or 0
        cby = awards_by.setdefault(r["college"], {})
        cby[year] = cby.get(year, 0) + n
        if r.get("award_type"):
            tby = by_type.setdefault((r["college"], r["award_type"]), {})
            tby[year] = tby.get(year, 0) + n
    # Flat per-college enrollment (summing the credit families back out) and
    # the per-(college, family) decomposition from the same rows.
    enroll_by: dict[str, dict[str, int]] = {}
    by_credit: dict[tuple[str, str], dict[str, int]] = {}
    for r in enroll_rows:
        term, n = r["term"], r["count"] or 0
        eby = enroll_by.setdefault(r["college"], {})
        eby[term] = eby.get(term, 0) + n
        if r.get("credit_type"):
            fby = by_credit.setdefault((r["college"], r["credit_type"]), {})
            fby[term] = fby.get(term, 0) + n

    # Series ordered by colleges, only for colleges that have data.
    awards_by_college = [
        CollegeSeries(college=c, vals=[awards_by[c].get(y, 0) for y in award_years])
        for c in colleges if c in awards_by
    ]
    types_of: dict[str, list[str]] = {}
    for c, at in by_type:
        types_of.setdefault(c, []).append(at)
    awards_by_type = [
        AwardTypeSeries(
            college=c, award_type=at,
            vals=[by_type[(c, at)].get(y, 0) for y in award_years],
        )
        for c in colleges
        for at in sorted(types_of.get(c, []), key=_award_type_sort_key)
    ]
    enrollment_by_college = [
        CollegeSeries(college=c, vals=[enroll_by[c].get(t) for t in enrollment_terms])
        for c in colleges if c in enroll_by
    ]
    families_of: dict[str, list[str]] = {}
    for c, ct in by_credit:
        families_of.setdefault(c, []).append(ct)
    enrollment_by_credit = [
        EnrollmentCreditSeries(
            college=c, credit_type=ct,
            vals=[by_credit[(c, ct)].get(t) for t in enrollment_terms],
        )
        for c in colleges
        for ct in sorted(families_of.get(c, []), key=_credit_type_sort_key)
    ]

    courses_by: dict[str, list[ProgramCourse]] = {}
    for r in course_rows:
        courses_by.setdefault(r["college"], []).append(ProgramCourse(
            code=r["code"], name=r.get("name") or r["code"],
            description=r.get("description") or "",
            learning_outcomes=list(r.get("learning_outcomes") or []),
            top_code=r.get("top_code"),
        ))
    curriculum_by_college = [
        CollegeCourses(college=c, courses=courses_by.get(c, []))
        for c in colleges
    ]

    return ProgramReport(
        top6=top6,
        name=name,
        region=region,
        region_display=region_display,
        sector=spec.sector,
        award_years=award_years,
        enrollment_terms=enrollment_terms,
        occupations=occupations,
        enrollment_by_college=enrollment_by_college,
        awards_by_college=awards_by_college,
        awards_by_type=awards_by_type,
        enrollment_by_credit=enrollment_by_credit,
        wages=[SvampWage(**w) for w in wage_fn(top6)],
        curriculum_by_college=curriculum_by_college,
        crosswalk=crosswalk,
        college=college,
    )


def _assemble_occupation(
    soc: str,
    title: str,
    description: str | None,
    region: str,
    region_display: str,
    annual_openings: int | None,
    annual_wage: int | None,
    growth_rate: float | None,
    employment: int | None,
    consortium_supply: float,
    feeding: list[str],
    universe: dict[str, set[str]],
    titles: dict[str, str],
    awards_rows: list[dict],
    enroll_rows: list[dict],
    course_rows: list[dict],
    crosswalk: dict,
    *,
    spec: LandscapeSpec = SVAMP_SPEC,
) -> SvampOccupationReport:
    """Pure assembly of the aggregated-occupation report (no I/O — supply and
    the crosswalk are computed in build_svamp_occupation and passed in).

    - feeding_tops: the SOC's 09 feeding TOPs, each summarized like the supply
      treemap (awards summed across colleges latest year; peak-term enrollment).
    - awards_by_college / enrollment_by_college: SUMMED over the feeding TOPs
      per college, aligned to the shared axes (the consortium's supply in the
      occupation's feeding programs). A feeding TOP that serves other SOCs
      contributes here too — that is intentional and is never netted across SOCs.
    - gap = annual_openings − consortium_supply (occupation axis owns the gap).
    """
    colleges = list(spec.colleges)
    latest_year = max((r["year"] for r in awards_rows if r["year"]), default=None)
    awards_total: dict[str, int] = {}
    for r in awards_rows:
        if r["year"] == latest_year:
            awards_total[r["top6"]] = awards_total.get(r["top6"], 0) + (r["awards"] or 0)
    per_top_term: dict[tuple[str, str], int] = {}
    for r in enroll_rows:
        term = r["term"]
        if not term or _term_excluded(term):
            continue
        per_top_term[(r["top6"], term)] = per_top_term.get((r["top6"], term), 0) + (r["count"] or 0)
    enroll_peak: dict[str, int] = {}
    for (top6, _term), c in per_top_term.items():
        enroll_peak[top6] = max(enroll_peak.get(top6, 0), c)
    colleges_by_top: dict[str, set] = {}
    for r in course_rows:
        colleges_by_top.setdefault(r["top6"], set()).add(r["college"])

    feeding_tops = [
        TopSummary(
            top6=t, name=titles.get(t) or t,
            awards_total=awards_total.get(t, 0),
            enrollment_total=enroll_peak.get(t, 0),
            n_colleges_offering=len(colleges_by_top.get(t, set())),
            soc_count=len(universe.get(t, set())),
        )
        for t in feeding
    ]
    feeding_tops.sort(key=lambda x: (-x.awards_total, -x.enrollment_total, -x.soc_count, x.top6))

    award_years = _award_years_axis({r["year"] for r in awards_rows if r["year"]})
    enrollment_terms = _enroll_terms_axis({r["term"] for r in enroll_rows if r["term"]})

    # Per-college series = Σ over feeding TOPs (occupation supply, additive).
    awards_by: dict[str, dict[str, int]] = {}
    for r in awards_rows:
        awards_by.setdefault(r["college"], {})
        awards_by[r["college"]][r["year"]] = awards_by[r["college"]].get(r["year"], 0) + (r["awards"] or 0)
    enroll_by: dict[str, dict[str, int]] = {}
    for r in enroll_rows:
        enroll_by.setdefault(r["college"], {})
        enroll_by[r["college"]][r["term"]] = enroll_by[r["college"]].get(r["term"], 0) + (r["count"] or 0)
    awards_by_college = [
        CollegeSeries(college=c, vals=[awards_by[c].get(y, 0) for y in award_years])
        for c in colleges if c in awards_by
    ]
    enrollment_by_college = [
        CollegeSeries(college=c, vals=[enroll_by[c].get(t) for t in enrollment_terms])
        for c in colleges if c in enroll_by
    ]

    courses_by: dict[str, list[ProgramCourse]] = {}
    for r in course_rows:
        courses_by.setdefault(r["college"], []).append(ProgramCourse(
            code=r["code"], name=r.get("name") or r["code"],
            description=r.get("description") or "",
            learning_outcomes=list(r.get("learning_outcomes") or []),
            top_code=r.get("top_code"),
        ))
    curriculum_by_college = [
        CollegeCourses(college=c, courses=courses_by.get(c, []))
        for c in colleges
    ]

    occupational_demand = build_occupational_demand(
        soc_code=soc,
        soc_title=title,
        annual_wage=annual_wage,
        annual_openings=annual_openings,
        employment=employment,
        growth_rate=growth_rate,
        coe_region_display=region_display,
    )

    return SvampOccupationReport(
        soc_code=soc,
        title=title,
        description=description,
        sector=spec.sector,
        region=region,
        region_display=region_display,
        occupational_demand=occupational_demand,
        annual_openings=annual_openings,
        annual_wage=annual_wage,
        growth_rate=growth_rate,
        employment=employment,
        consortium_supply=round(consortium_supply, 2),
        gap=int(round((annual_openings or 0) - consortium_supply)),
        award_years=award_years,
        enrollment_terms=enrollment_terms,
        feeding_tops=feeding_tops,
        awards_by_college=awards_by_college,
        enrollment_by_college=enrollment_by_college,
        curriculum_by_college=curriculum_by_college,
        crosswalk=CurriculumCrosswalk(**crosswalk),
    )
