"""SVAMP — the aggregated partnership landscape for the Silicon Valley
Advanced Manufacturing consortium.

Bespoke prototype surface (not a general framework, not an ontology unit).
It aggregates the existing per-(college, occupation) partnership machinery
across a fixed set of five member colleges and twelve advanced manufacturing
occupations into one landscape, then drills back into the unchanged
OpportunityReport.

THE aggregation invariant — two pillars are regional, two are institutional:
  - DEMAND (annual openings/wages): REGIONAL. All five colleges sit in the
    same COE region ("Bay"), so the regional demand for a SOC is one shared
    number — read ONCE per SOC, summed across the twelve occupations. It is
    never multiplied by the college count.
  - EMPLOYERS (candidate partners): REGIONAL. The consortium employer count is
    the DISTINCT set of regional employers hiring for any of the twelve SOCs
    (a union), never a sum of per-cell employer counts.
  - SUPPLY (projected program completions) and STUDENTS: INSTITUTIONAL. They
    are summed across the member colleges.
  - Consortium gap = (Σ regional demand over the 12 SOCs) − (Σ supply over all
    college×SOC cells). NOT the sum of per-college gaps.

Reuses the same graph patterns and helpers as opportunity.py: the
College→IN_MARKET→Region→DEMANDS→Occupation demand read, the precomputed
OCCUPATION_PIPELINE alignment edge, get_coe_supply for projected completions,
and the regional HIRES_FOR employer pivot.
"""

from __future__ import annotations

from typing import Callable

from pydantic import BaseModel

from ontology.regions import (
    COE_REGION_DISPLAY,
    COE_REGION_PRIORITY_SECTORS,
)
from ontology.crosswalks import top6_to_soc, _load_top_to_cip
from ontology.schema import get_driver
from ontology.supply import get_coe_supply
from ontology.programs import get_wage_outcomes

from partnerships.landscape import LandscapeSpec, SVAMP_SPEC

# ── Scope ─────────────────────────────────────────────────────────────────
# The SVAMP scope now lives as SVAMP_SPEC in landscape.py — the single source,
# alongside the other landscape instances (SMCCD, …). The module-level names
# below remain as back-compat aliases for the existing importers
# (svamp_programs, svamp_employers, the tests); the builders in this file read
# from `spec`, not from these names.

SVAMP_COLLEGES: list[str] = list(SVAMP_SPEC.colleges)
SVAMP_SOCS: list[str] = list(SVAMP_SPEC.socs)

# Enrollment terms are NOT a fixed list: the course-section exports span ~5
# years and colleges run different calendars (quarter vs. semester), so the
# term axis is the chronologically-sorted union of whatever Term nodes exist,
# computed per landscape (mirroring award_years). This orders "Season YYYY"
# labels: Winter < Spring < Summer < Fall within a year.
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

# Canonical PCAH Strong Workforce sector these occupations sit under. Passed
# as the leaf report's sector hint so the drill-down renders in the same
# sector framing as the consortium. (Matches the label in regions.py /
# the PCAH TOP-Codes-to-Sectors mapping.)
SVAMP_SECTOR: str = SVAMP_SPEC.sector

# Award trend window: show the most recent N award years, matching the ~5-year
# span of the enrollment chart. The full history remains in the graph.
AWARD_YEARS_SHOWN: int = 5

# SVAMP scopes its program / supply universe to TOP division 09 — "Engineering
# and Industrial Technologies" in the Chancellor's Office TOP taxonomy, the
# consortium's programmatic domain per the SVAMP director — AND to CTE (career-
# technical) programs only, excluding transfer/academic ones (e.g. 090100
# Engineering, General (Transfer)), per the CCCCO PCAH CTE designation. Both are
# categorical, institutional scopes applied on top of the faithful TOP-CIP-SOC
# crosswalk — the crosswalk is never edited (no per-edge curation), so
# non-engineering feeders it legitimately links (e.g. Commercial Music →
# 17-3029, CIS → 17-3023) and transfer majors simply fall out of the
# consortium's workforce view. Enforced consortium-wide: the Programs lens
# universe (svamp_programs.relevant_tops), this landscape's per-cell supply /
# awards / coverage, and the occupation drill report's curriculum pathway
# (build_opportunity_report's top_prefix + cte_only) all restrict to 09xx CTE
# TOPs. DEMAND and the candidate-employer set are NOT scoped — they are
# occupation- and region-owned, not program-owned.
SVAMP_TOP_DIVISION: str = SVAMP_SPEC.top_division

# Programs the SVAMP director's advanced manufacturing mandate excludes, even
# though they sit in division 09 and the crosswalk legitimately links them to
# SVAMP SOCs. The SOC link is occupation-category truth, but the employment
# flows run to other industry verticals — automotive completers to dealerships,
# shops, and fleet operations; HVAC completers to commercial/residential
# building trades — none of which are in the AM-scoped employer set this report
# pairs supply with. Scope decision per the SVAMP director (the same authority
# behind SVAMP_SOCS and the 09 domain); the crosswalk itself is never edited.
# Boundary programs the director has NOT ruled on stay in (e.g. 094840
# Alternative Fuels & Advanced Transportation, 094610 Energy Systems) — add
# them here if the mandate later excludes them.
SVAMP_MANDATE_EXCLUDED_TOPS: frozenset[str] = SVAMP_SPEC.excluded_tops


def is_svamp_top(top6: str | None) -> bool:
    """True iff a TOP6 is in SVAMP's scoped program universe. Back-compat alias
    for SVAMP_SPEC.in_scope (svamp_programs and the tests import this name); see
    LandscapeSpec.in_scope for the predicate — configured TOP division + CTE
    family test, minus the director's mandate exclusions."""
    return SVAMP_SPEC.in_scope(top6)


# ── Response shapes ───────────────────────────────────────────────────────


class SvampWage(BaseModel):
    """Pooled statewide award-cohort wage outcome for a TOP6 program, by
    recipient type. Display-only; medians are non-additive — never summed."""
    recipient_type: str
    wage_before: int | None = None
    wage_after_2: int | None = None
    wage_after_5: int | None = None
    n: int | None = None
    window: str = ""


class SvampProgram(BaseModel):
    """A TOP6 program (DataMart actuals) that prepares for this cell's SOC at
    this college. Awards/enrollment are institutional ground truth; wages are
    pooled statewide at the TOP6 grain."""
    top6: str
    name: str
    awards_recent: int = 0                 # actual completions, latest award year
    awards: list[int] = []                 # completions per landscape award_years
    enrollment: list[int | None] = []      # per landscape enrollment_terms
    wages: list[SvampWage] = []


class SvampCell(BaseModel):
    """One (college, occupation) cell of the landscape.

    `annual_openings` is the REGIONAL demand for the SOC — identical across
    all member colleges by construction (they share one COE region). Alignment
    depth (none/partial/strong) is left to the frontend to derive from
    `course_count`. `supply` is this college's COE-projected program
    completions for the SOC; `gap` = regional openings − this college's supply.

    `awards_recent` and `programs` are the additive DataMart enrichment:
    actual completions (a ground-truth complement to projected `supply`) and
    the per-program award/enrollment/wage detail for the cell's TOP6 programs.
    """
    soc_code: str
    title: str
    annual_openings: int | None = None
    annual_wage: int | None = None
    growth_rate: float | None = None
    course_count: int = 0
    student_count: int = 0
    supply: float = 0.0
    gap: int = 0
    awards_recent: int = 0                 # Σ actual awards over this cell's programs
    # Activity-based coverage (the dual of the Programs grid cell), routed off
    # the crosswalking programs rather than the course pipeline so credentials
    # that confer without a tagged course (095630 → Machinists) still count:
    # `enrolled` = any feeding 09∩CTE program has enrollment at this college;
    # `feeding_awards` = latest-year awards summed over the feeding set. The
    # frontend derives covered = enrolled & feeding_awards>0; partial = one;
    # gap = neither — identical predicate to the Programs lens.
    enrolled: bool = False
    feeding_awards: int = 0
    programs: list[SvampProgram] = []


class SvampCollege(BaseModel):
    name: str
    cells: list[SvampCell]  # one per SVAMP_SOCS, in scope order


class SvampAggregate(BaseModel):
    """Consortium-level rollup. See the module docstring for the
    regional-vs-institutional rules these fields obey."""
    regional_demand_total: int      # Σ regional openings over the 12 SOCs (once)
    combined_supply_total: float    # Σ supply over all college×SOC cells
    gap: int                        # regional_demand_total − combined_supply_total
    candidate_employers: int        # DISTINCT regional employers hiring any SOC
    occupations_taught: int         # # of the 12 SOCs ≥1 college aligns to
    # Σ actual awards (DataMart) over DISTINCT (college, TOP6) programs in scope
    # — counted once per program, NOT summed per cell (a TOP6 serves multiple
    # SOCs, so per-cell summing would double-count).
    combined_awards: int = 0
    n_colleges: int
    n_occupations: int


class SvampLandscape(BaseModel):
    region: str
    region_display: str
    sector: str
    # True when the consortium sector is a Strong Workforce priority sector for
    # the region (per PCAH regional consortium designation). Drives the
    # "Regional Priority Sector" tag in the report header.
    is_sector_priority: bool = False
    # Deterministic two-sentence thesis establishing the aggregated report's
    # nature (composed server-side, mirroring opportunity_narrative.py).
    executive_summary: str = ""
    # Sorted award-year axis (e.g. ["2015-2016", …, "2024-2025"]) shared by
    # every program's `awards` series — the x-axis for the awards trend chart.
    award_years: list[str] = []
    # Chronologically-sorted enrollment-term axis (e.g. ["Winter 2021", …,
    # "Fall 2025"]) shared by every program's `enrollment` series. The union
    # across colleges; a chart for one college trims the terms it never runs.
    enrollment_terms: list[str] = []
    colleges: list[SvampCollege]
    aggregate: SvampAggregate


def _build_executive_summary(spec: LandscapeSpec, region_display: str, agg: "SvampAggregate") -> str:
    """The occupations (demand) lens thesis: what the report examines and the
    shared regional demand total. Supply framing — the credentials member
    colleges award — belongs on the Programs lens, not here, so the occupations
    view reads unambiguously as the demand side of the landscape."""
    s1 = (
        f"This view examines the regional demand landscape across the "
        f"{agg.n_occupations} {spec.sector.lower()} occupations the "
        f"{spec.name} targets in the "
        f"{region_display} regional labor market."
    )
    s2 = (
        f"Regional demand for these occupations totals "
        f"{agg.regional_demand_total:,} openings per year."
    )
    return f"{s1} {s2}"


# ── Builder ───────────────────────────────────────────────────────────────


def _resolve_region() -> str:
    """The shared COE region for the SVAMP consortium. Back-compat wrapper for
    SVAMP_SPEC.resolve_region (svamp_employers imports this name); the
    one-region assertion lives in LandscapeSpec.resolve_region."""
    return SVAMP_SPEC.resolve_region()


def _soc_feeding_tops(spec: LandscapeSpec) -> dict[str, set[str]]:
    """{target SOC -> the in-scope TOP6 programs that crosswalk to it}. The
    inverse of svamp_programs.relevant_tops (kept local to avoid a svamp ↔
    svamp_programs import cycle; both apply the same division + CTE-family scope
    to the faithful TOP-CIP-SOC crosswalk, which is never edited). Drives the
    per-cell activity coverage: a SOC is fed by these programs regardless of
    whether any course is tagged to their code (the 095630 parent-code seam)."""
    all_top6 = list(_load_top_to_cip().keys())
    targets = set(spec.socs)
    feed: dict[str, set[str]] = {soc: set() for soc in spec.socs}
    for top6, socs in top6_to_soc(all_top6).items():
        inter = socs & targets
        if inter and spec.in_scope(top6):
            for soc in inter:
                feed[soc].add(top6)
    return feed


def build_svamp_landscape() -> SvampLandscape:
    """Back-compat 0-arg entry for the SVAMP instance (api.py imports this)."""
    return build_landscape(SVAMP_SPEC)


def build_landscape(spec: LandscapeSpec) -> SvampLandscape:
    region = spec.resolve_region()
    driver = get_driver()

    with driver.session() as session:
        # 1) Regional demand, read ONCE per SOC (shared across all colleges).
        demand_rows = session.run(
            """
            MATCH (r:Region {name: $region})-[d:DEMANDS]->(occ:Occupation)
            WHERE occ.soc_code IN $socs
            RETURN occ.soc_code AS soc_code,
                   occ.title AS title,
                   d.annual_openings AS annual_openings,
                   d.annual_wage AS annual_wage,
                   d.growth_rate AS growth_rate
            """,
            region=region, socs=list(spec.socs),
        ).data()
        demand_by_soc = {r["soc_code"]: r for r in demand_rows}

        # 2) Per-college alignment (precomputed OCCUPATION_PIPELINE edge),
        #    joined onto the regional demand so every demanded SOC comes
        #    through even where the college has no aligned curriculum.
        #    SVAMP-scoped to TOP division 09 (see SVAMP_TOP_DIVISION):
        #    course_count_09 recounts the aligned courses under 09, and
        #    top_codes is filtered to 09 below — so the grid's supply / awards
        #    and gap shading reflect the consortium's Engineering & Industrial
        #    Technology program domain (the full faithful crosswalk still backs
        #    the unchanged per-college report). The edge's own course_count /
        #    top_codes are deliberately not used here.
        align_by_college: dict[str, dict[str, dict]] = {}
        for college in spec.colleges:
            rows = session.run(
                """
                MATCH (col:College {name: $college})-[:IN_MARKET]->(r:Region)
                      -[:DEMANDS]->(occ:Occupation)
                WHERE occ.soc_code IN $socs
                OPTIONAL MATCH (col)-[op:OCCUPATION_PIPELINE]->(occ)
                OPTIONAL MATCH (c09:Course {college: $college})-[:PREPARES_FOR]->(occ)
                      WHERE c09.top_code STARTS WITH $top_division
                        AND NOT c09.top_code IN $excluded
                WITH occ, op, count(DISTINCT c09) AS course_count_09
                RETURN occ.soc_code AS soc_code,
                       course_count_09 AS course_count,
                       op.student_count AS student_count,
                       op.top_codes AS top_codes
                """,
                college=college, socs=list(spec.socs),
                top_division=spec.top_division,
                excluded=sorted(spec.excluded_tops),
            ).data()
            align_by_college[college] = {
                r["soc_code"]: {
                    "course_count": r["course_count"] or 0,
                    "student_count": r["student_count"],
                    "top_codes": [t for t in (r["top_codes"] or []) if spec.in_scope(t)],
                }
                for r in rows
            }

        # 3) DISTINCT regional employers hiring for ANY of the SOCs (union).
        emp_row = session.run(
            """
            MATCH (r:Region {name: $region})<-[:IN_MARKET]-(emp:Employer)
                  -[:HIRES_FOR]->(occ:Occupation)
            WHERE occ.soc_code IN $socs
            RETURN count(DISTINCT emp) AS n
            """,
            region=region, socs=list(spec.socs),
        ).single()
        candidate_employers = (emp_row["n"] if emp_row else 0) or 0

        # 4) Program (TOP6) actuals — DataMart awards + enrollment series, per
        #    (college, top6). Additive enrichment; absent for colleges/TOP6s the
        #    DataMart exports don't cover (the overlay is sparser than the
        #    curriculum-alignment shading by design).
        # Awards per (college, top6, year) — one row per reported AcademicYear
        # so each program carries a full award-year series. Programs with no
        # AWARDED edge still come through (OPTIONAL MATCH ⇒ null year, dropped).
        program_data: dict[tuple[str, str], dict] = {}
        for r in session.run(
            """
            MATCH (pr:Program) WHERE pr.college IN $colleges
            OPTIONAL MATCH (pr)-[a:AWARDED]->(ay:AcademicYear)
            RETURN pr.college AS college, pr.top6 AS top6, pr.name AS name,
                   ay.year AS year,
                   toInteger(sum(coalesce(a.count, 0))) AS awards
            """,
            colleges=list(spec.colleges),
        ).data():
            entry = program_data.setdefault(
                (r["college"], r["top6"]),
                {"name": r["name"], "awards_by_year": {}, "enroll": {}},
            )
            if r["year"]:
                entry["awards_by_year"][r["year"]] = r["awards"]
        for r in session.run(
            """
            MATCH (pr:Program)-[e:ENROLLED]->(t:Term) WHERE pr.college IN $colleges
            RETURN pr.college AS college, pr.top6 AS top6, t.term AS term,
                   toInteger(sum(e.count)) AS count
            """,
            colleges=list(spec.colleges),
        ).data():
            entry = program_data.get((r["college"], r["top6"]))
            if entry is not None:
                entry["enroll"][r["term"]] = r["count"]

    return _assemble_landscape(
        spec=spec,
        region=region,
        region_display=COE_REGION_DISPLAY.get(region, region),
        demand_by_soc=demand_by_soc,
        align_by_college=align_by_college,
        candidate_employers=candidate_employers,
        program_data=program_data,
        soc_feeding=_soc_feeding_tops(spec),
    )


def _build_program(
    college: str, top6: str, entry: dict, award_years: list[str],
    enrollment_terms: list[str], wage_fn,
) -> SvampProgram:
    """Compose a SvampProgram from fetched program_data + the (pooled, TOP6-
    grain) wage lookup. `awards` aligns to the shared `award_years` axis (a year
    with no AWARDED edge ⇒ 0 conferred); `enrollment` aligns to the shared
    `enrollment_terms` axis (a term this program/college never runs ⇒ None, so
    the chart can trim it); `awards_recent` is the latest year's total. wage_fn
    is called only for real programs, so callers that pass empty program_data
    (e.g. the unit test) incur no I/O."""
    by_year = entry.get("awards_by_year", {})
    enroll = entry.get("enroll", {})
    latest = award_years[-1] if award_years else None
    return SvampProgram(
        top6=top6,
        name=entry.get("name") or top6,
        awards_recent=int(by_year.get(latest) or 0) if latest else 0,
        awards=[int(by_year.get(y) or 0) for y in award_years],
        enrollment=[enroll.get(term) for term in enrollment_terms],
        wages=[SvampWage(**w) for w in wage_fn(top6)],
    )


def _assemble_landscape(
    region: str,
    region_display: str,
    demand_by_soc: dict[str, dict],
    align_by_college: dict[str, dict[str, dict]],
    candidate_employers: int,
    supply_fn: Callable[[set[str], str], tuple[list, float]] = get_coe_supply,
    program_data: dict[tuple[str, str], dict] | None = None,
    wage_fn: Callable[[str], list] = get_wage_outcomes,
    soc_feeding: dict[str, set[str]] | None = None,
    *,
    spec: LandscapeSpec = SVAMP_SPEC,
) -> SvampLandscape:
    """Pure assembly of the landscape from already-fetched graph data.

    Separated from the I/O so the regional-vs-institutional aggregation
    invariant is unit-testable without a graph. `supply_fn` is injectable for
    the same reason; in production it is `get_coe_supply`.

    - Regional demand is taken ONCE per SOC from `demand_by_soc` and summed
      across the 12 occupations — never multiplied by the college count.
    - Supply is summed across every (college, SOC) cell (institutional).
    - `candidate_employers` is the pre-deduplicated regional union, passed
      through as-is (never a sum of per-cell counts).
    """
    program_data = program_data or {}
    soc_feeding = soc_feeding or {}
    # Shared award-year axis: the sorted union of every program's reported
    # years (YYYY-YYYY sorts chronologically), windowed to the most recent
    # AWARD_YEARS_SHOWN so the awards trend spans the same ~5 years as the
    # enrollment chart (the full history stays in the graph). Each program's
    # `awards` series aligns to this; awards_recent / combined_awards are the
    # LATEST year only.
    award_years = sorted({
        y for e in program_data.values() for y in e.get("awards_by_year", {})
    })[-AWARD_YEARS_SHOWN:]
    latest_year = award_years[-1] if award_years else None
    # Shared enrollment-term axis: the chronologically-sorted union of every
    # program's reported terms, excluding the structurally-low summer terms
    # and the export-boundary terms (_term_excluded). Each program's
    # `enrollment` aligns to this.
    enrollment_terms = sorted(
        {t for e in program_data.values() for t in e.get("enroll", {})
         if not _term_excluded(t)},
        key=_term_sort_key,
    )
    colleges: list[SvampCollege] = []
    combined_supply_total = 0.0
    socs_taught: set[str] = set()
    # DISTINCT (college, top6) programs in scope — combined_awards sums over
    # these once, never per-cell (a TOP6 serves multiple SOCs).
    scoped_programs: set[tuple[str, str]] = set()

    for college in spec.colleges:
        align = align_by_college.get(college, {})
        cells: list[SvampCell] = []
        for soc in spec.socs:
            demand = demand_by_soc.get(soc, {})
            a = align.get(soc, {})
            course_count = (a.get("course_count") or 0)
            student_count = (a.get("student_count") or 0)
            top_codes = {t for t in (a.get("top_codes") or []) if t}
            # The SOC's full crosswalking program set (09∩CTE), independent of
            # whether a course is tagged to each program's own code — the supply
            # basis for both this cell's coverage and its program detail. A
            # superset of the course-routed top_codes.
            feeding = soc_feeding.get(soc, set())

            supply = 0.0
            if top_codes:
                _, supply = supply_fn(top_codes, college)
            combined_supply_total += supply
            if course_count > 0:
                socs_taught.add(soc)

            # DataMart program actuals for the programs SUPPLYING this occupation
            # — routed off the feeding set (unioned with the course-routed
            # top_codes so nothing previously shown is dropped), so a program that
            # confers without a tagged course (095630 → Machinists) still appears
            # in the cell's program detail. Per-cell awards display = sum over
            # these programs; the consortium total dedups across cells via
            # scoped_programs.
            programs: list[SvampProgram] = []
            for top6 in sorted(feeding | top_codes):
                entry = program_data.get((college, top6))
                if entry is not None:
                    programs.append(_build_program(
                        college, top6, entry, award_years, enrollment_terms, wage_fn))
                    scoped_programs.add((college, top6))
            awards_recent = sum(p.awards_recent for p in programs)

            # Activity coverage over the feeding set, routed off the Program
            # nodes. enrolled = any feeding program has non-summer enrollment
            # here; feeding_awards = latest-year awards summed over the feeding set.
            enrolled = any(
                count > 0
                for t in feeding
                for term, count in program_data.get((college, t), {}).get("enroll", {}).items()
                if not _term_excluded(term)
            )
            feeding_awards = sum(
                int(program_data.get((college, t), {}).get("awards_by_year", {}).get(latest_year) or 0)
                for t in feeding
            ) if latest_year else 0

            annual_openings = demand.get("annual_openings")
            gap = int(round((annual_openings or 0) - supply))
            cells.append(SvampCell(
                soc_code=soc,
                title=demand.get("title") or soc,
                annual_openings=annual_openings,
                annual_wage=demand.get("annual_wage"),
                growth_rate=demand.get("growth_rate"),
                course_count=course_count,
                student_count=student_count,
                supply=round(supply, 2),
                gap=gap,
                awards_recent=awards_recent,
                enrolled=enrolled,
                feeding_awards=feeding_awards,
                programs=programs,
            ))
        colleges.append(SvampCollege(name=college, cells=cells))

    # Consortium awards: each scoped program counted once (institutional, but
    # de-duplicated across the SOCs a TOP6 serves), latest reported year only.
    combined_awards = sum(
        int(program_data[k].get("awards_by_year", {}).get(latest_year) or 0)
        for k in scoped_programs
    ) if latest_year else 0

    # Regional demand summed ONCE over the 12 SOCs (not per college).
    regional_demand_total = int(round(sum(
        (demand_by_soc.get(soc, {}).get("annual_openings") or 0) for soc in spec.socs
    )))

    aggregate = SvampAggregate(
        regional_demand_total=regional_demand_total,
        combined_supply_total=round(combined_supply_total, 2),
        gap=int(round(regional_demand_total - combined_supply_total)),
        candidate_employers=candidate_employers,
        occupations_taught=len(socs_taught),
        combined_awards=combined_awards,
        n_colleges=len(spec.colleges),
        n_occupations=len(spec.socs),
    )

    is_sector_priority = spec.sector in set(COE_REGION_PRIORITY_SECTORS.get(region, []))

    return SvampLandscape(
        region=region,
        region_display=region_display,
        sector=spec.sector,
        is_sector_priority=is_sector_priority,
        executive_summary=_build_executive_summary(spec, region_display, aggregate),
        award_years=award_years,
        enrollment_terms=enrollment_terms,
        colleges=colleges,
        aggregate=aggregate,
    )
