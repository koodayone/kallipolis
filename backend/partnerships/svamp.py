"""SVAMP — the aggregated partnership landscape for the Silicon Valley
Advanced Manufacturing consortium.

Bespoke prototype surface (not a general framework, not an ontology unit).
It aggregates the existing per-(college, occupation) partnership machinery
across a fixed set of five member colleges and twelve advanced-manufacturing
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
    COLLEGE_COE_REGION,
)
from ontology.schema import get_driver
from ontology.supply import get_coe_supply

# ── Scope (fixed for this consortium prototype) ───────────────────────────

SVAMP_COLLEGES: list[str] = [
    "De Anza College",
    "Evergreen Valley College",
    "Foothill College",
    "Mission College",
    "Ohlone College",
]

# The twelve advanced-manufacturing occupations the consortium targets.
SVAMP_SOCS: list[str] = [
    "17-3023", "17-3024", "17-3026", "17-3027", "17-3028", "17-3029",
    "49-9041", "49-9043", "51-4041", "51-9141", "51-9161", "51-9162",
]

# Canonical PCAH Strong Workforce sector these occupations sit under. Passed
# as the leaf report's sector hint so the drill-down renders in the same
# sector framing as the consortium. (Matches the label in regions.py /
# the PCAH TOP-Codes-to-Sectors mapping.)
SVAMP_SECTOR: str = "Advanced Manufacturing"


# ── Response shapes ───────────────────────────────────────────────────────


class SvampCell(BaseModel):
    """One (college, occupation) cell of the landscape.

    `annual_openings` is the REGIONAL demand for the SOC — identical across
    all member colleges by construction (they share one COE region). Alignment
    depth (none/partial/strong) is left to the frontend to derive from
    `course_count`. `supply` is this college's projected program completions
    for the SOC; `gap` = regional openings − this college's supply.
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
    colleges: list[SvampCollege]
    aggregate: SvampAggregate


def _build_executive_summary(region_display: str, agg: "SvampAggregate") -> str:
    """The aggregated report's two-sentence thesis, employer-agnostic.

    S1 names what the report examines (consortium + occupations + region).
    S2 carries the regional-vs-institutional aggregation thesis: shared
    regional demand, summed institutional supply, the combined gap, and the
    regional employer set — the basis for a multi-college partnership strategy.
    """
    s1 = (
        f"This report examines the aggregated partnership landscape across the "
        f"{agg.n_colleges} member colleges of the Silicon Valley Advanced "
        f"Manufacturing Partnership consortium for {agg.n_occupations} "
        f"advanced-manufacturing occupations in the {region_display} regional "
        f"labor market."
    )
    s2 = (
        f"Regional demand for these occupations totals "
        f"{agg.regional_demand_total:,} openings per year; the consortium's "
        f"colleges collectively supply ~{round(agg.combined_supply_total):,} "
        f"completions against that shared demand."
    )
    return f"{s1} {s2}"


# ── Builder ───────────────────────────────────────────────────────────────


def _resolve_region() -> str:
    """The shared COE region for the consortium. Asserts all member colleges
    map to the same region — the precondition that makes regional demand a
    single shared number per SOC."""
    regions = {COLLEGE_COE_REGION.get(c, "") for c in SVAMP_COLLEGES}
    regions.discard("")
    if len(regions) != 1:
        raise ValueError(
            f"SVAMP member colleges must share one COE region; got {regions or 'none'}"
        )
    return next(iter(regions))


def build_svamp_landscape() -> SvampLandscape:
    region = _resolve_region()
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
            region=region, socs=SVAMP_SOCS,
        ).data()
        demand_by_soc = {r["soc_code"]: r for r in demand_rows}

        # 2) Per-college alignment (precomputed OCCUPATION_PIPELINE edge),
        #    joined onto the regional demand so every demanded SOC comes
        #    through even where the college has no aligned curriculum.
        align_by_college: dict[str, dict[str, dict]] = {}
        for college in SVAMP_COLLEGES:
            rows = session.run(
                """
                MATCH (col:College {name: $college})-[:IN_MARKET]->(r:Region)
                      -[:DEMANDS]->(occ:Occupation)
                WHERE occ.soc_code IN $socs
                OPTIONAL MATCH (col)-[op:OCCUPATION_PIPELINE]->(occ)
                RETURN occ.soc_code AS soc_code,
                       op.course_count AS course_count,
                       op.student_count AS student_count,
                       op.top_codes AS top_codes
                """,
                college=college, socs=SVAMP_SOCS,
            ).data()
            align_by_college[college] = {r["soc_code"]: r for r in rows}

        # 3) DISTINCT regional employers hiring for ANY of the SOCs (union).
        emp_row = session.run(
            """
            MATCH (r:Region {name: $region})<-[:IN_MARKET]-(emp:Employer)
                  -[:HIRES_FOR]->(occ:Occupation)
            WHERE occ.soc_code IN $socs
            RETURN count(DISTINCT emp) AS n
            """,
            region=region, socs=SVAMP_SOCS,
        ).single()
        candidate_employers = (emp_row["n"] if emp_row else 0) or 0

    return _assemble_landscape(
        region=region,
        region_display=COE_REGION_DISPLAY.get(region, region),
        demand_by_soc=demand_by_soc,
        align_by_college=align_by_college,
        candidate_employers=candidate_employers,
    )


def _assemble_landscape(
    region: str,
    region_display: str,
    demand_by_soc: dict[str, dict],
    align_by_college: dict[str, dict[str, dict]],
    candidate_employers: int,
    supply_fn: Callable[[set[str], str], tuple[list, float]] = get_coe_supply,
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
    colleges: list[SvampCollege] = []
    combined_supply_total = 0.0
    socs_taught: set[str] = set()

    for college in SVAMP_COLLEGES:
        align = align_by_college.get(college, {})
        cells: list[SvampCell] = []
        for soc in SVAMP_SOCS:
            demand = demand_by_soc.get(soc, {})
            a = align.get(soc, {})
            course_count = (a.get("course_count") or 0)
            student_count = (a.get("student_count") or 0)
            top_codes = {t for t in (a.get("top_codes") or []) if t}

            supply = 0.0
            if top_codes:
                _, supply = supply_fn(top_codes, college)
            combined_supply_total += supply
            if course_count > 0:
                socs_taught.add(soc)

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
            ))
        colleges.append(SvampCollege(name=college, cells=cells))

    # Regional demand summed ONCE over the 12 SOCs (not per college).
    regional_demand_total = int(round(sum(
        (demand_by_soc.get(soc, {}).get("annual_openings") or 0) for soc in SVAMP_SOCS
    )))

    aggregate = SvampAggregate(
        regional_demand_total=regional_demand_total,
        combined_supply_total=round(combined_supply_total, 2),
        gap=int(round(regional_demand_total - combined_supply_total)),
        candidate_employers=candidate_employers,
        occupations_taught=len(socs_taught),
        n_colleges=len(SVAMP_COLLEGES),
        n_occupations=len(SVAMP_SOCS),
    )

    is_sector_priority = SVAMP_SECTOR in set(COE_REGION_PRIORITY_SECTORS.get(region, []))

    return SvampLandscape(
        region=region,
        region_display=region_display,
        sector=SVAMP_SECTOR,
        is_sector_priority=is_sector_priority,
        executive_summary=_build_executive_summary(region_display, aggregate),
        colleges=colleges,
        aggregate=aggregate,
    )
