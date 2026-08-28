"""Partnership endpoints — the per-occupation opportunity report and the
aggregated member×sector landscapes.

The per-occupation report (`/opportunity/{soc}`) frames the regional employer
set as candidate partners for a multi-employer engagement around the occupational
pathway. It is live-computed and embedded, not standalone — the landscape
occupation drill (`LandscapeReport` → `OpportunityReportBody`) renders it inline;
the former standalone accordion + report route were retired into the landscape.
"""

import json
import logging
import os
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel

from partnerships.models import OpportunityReport
from partnerships.opportunity import build_opportunity_report
from partnerships.landscape_build import Landscape, build_landscape
from partnerships.landscape import REGISTRY, LandscapeSpec, routable_specs
from partnerships.registry import has_supply, live_catalog, spec_for
from partnerships.resolve import resolve
from partnerships.clusters import cluster_expanded_spec, consortium_clusters
from partnerships.lens import build_lens
from partnerships.sectors import SECTORS
from partnerships.landscape_employers import LandscapeEmployersResult, build_landscape_employers
from partnerships.landscape_programs import (
    ProgramReport,
    ProgramsLandscape,
    LandscapeOccupationReport,
    build_program_report,
    build_programs_landscape,
    build_landscape_occupation,
)

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/opportunity/{soc_code}", response_model=OpportunityReport)
def get_partnership_opportunity(
    soc_code: str,
    college: str,
    sector: str | None = None,
    top_prefix: str | None = None,
    cte_only: bool = False,
    exclude_tops: str | None = None,
):
    """Returns the per-(college, occupation) partnership opportunity
    report. Composed deterministically from the institutional graph:
    regional demand (COE), TOP-grouped curriculum coverage, regional
    employer set sorted by NAICS industry share, and employer-agnostic
    narrative pointing to the multi-employer engagement opportunity the
    data identifies.

    The optional `sector` query parameter preserves the user's click
    context: SOCs that belong to multiple PCAH sectors render with
    whichever sector they were navigated from, rather than being
    re-resolved alphabetically. Invalid sectors (not actually one of
    the SOC's PCAH sectors) are ignored — the report falls back to
    the alphabetical default.

    The optional `top_prefix`, `cte_only`, and `exclude_tops` (comma-separated
    TOP6 codes — the SVAMP director's-mandate exclusions) query parameters
    scope the curriculum pathway (the SVAMP 09-only, career-technical lens).
    The precomputed cache is built unscoped, so a scoped request bypasses it
    and composes live; unscoped requests (every per-college report) keep the
    cache fast-path unchanged.
    """
    try:
        return build_opportunity_report(
            college, soc_code, sector_hint=sector, top_prefix=top_prefix, cte_only=cte_only,
            exclude_tops=frozenset(t.strip() for t in exclude_tops.split(",") if t.strip()) if exclude_tops else None,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Aggregated partnership landscapes (SVAMP, SMCCD, …) ────────────────────
# One generic engine parameterized by LandscapeSpec; each registered instance
# gets the same five routes under its own /<id> prefix. /svamp stays byte-
# identical (it is SVAMP_SPEC); adding an instance is one REGISTRY entry — no
# new route code. All paths stay nested under the /partnerships router, so the
# vocabulary_alignment / backend_layout audits (which scope to top-level
# surfaces) are unaffected.
def _register_landscape_routes(spec: LandscapeSpec) -> None:
    sid = spec.id

    # resolve() narrows the spec's SOCs to its sector rule's effective set
    # (demand floor / reachable / non-empty); identity for curated/no-rule specs.
    # Applied here so every endpoint for the instance stays consistent.
    def get_landscape():
        try:
            return build_landscape(resolve(spec))
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    def get_programs():
        try:
            return build_programs_landscape(resolve(spec))
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    def get_program(top6: str, college: str | None = None):
        try:
            return build_program_report(top6, college=college, spec=resolve(spec))
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    def get_occupation(soc: str, college: str | None = None, employers: bool = True):
        try:
            return build_landscape_occupation(
                soc, spec=resolve(spec), college=college, include_employers=employers)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    def get_employers():
        try:
            return build_landscape_employers(resolve(spec))
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    router.add_api_route(
        f"/{sid}", get_landscape, methods=["GET"],
        response_model=Landscape, name=f"get_{sid}_landscape",
        description=f"Aggregated partnership landscape for {spec.name} — member "
                    "colleges × target occupations over one shared COE region. "
                    "Demand and employers regional; supply institutional.")
    router.add_api_route(
        f"/{sid}/programs", get_programs, methods=["GET"],
        response_model=ProgramsLandscape, name=f"get_{sid}_programs",
        description="Programs lens — the supply-side TOP6 universe, each sized by "
                    "latest-period supply summed across the member colleges.")
    router.add_api_route(
        f"/{sid}/program/{{top6}}", get_program, methods=["GET"],
        response_model=ProgramReport, name=f"get_{sid}_program",
        description="A single TOP6 program report. Optional `college` scopes to one "
                    "member college; omitted ⇒ the consortium-aggregated view.")
    router.add_api_route(
        f"/{sid}/occupation/{{soc}}", get_occupation, methods=["GET"],
        response_model=LandscapeOccupationReport, name=f"get_{sid}_occupation",
        description="Aggregated-occupation report — one SOC read consortium-wide: "
                    "regional demand, consortium supply and the resulting gap. "
                    "`employers=false` skips the regional Partnership Opportunities "
                    "gather (the report's dominant cost) for surfaces that don't render it.")
    router.add_api_route(
        f"/{sid}/employers", get_employers, methods=["GET"],
        response_model=LandscapeEmployersResult, name=f"get_{sid}_employers",
        description="Employers lens — geocoded regional employers hiring for the "
                    "target occupations; reports shown-of-total (no silent truncation).")


# routable_specs() (not REGISTRY directly) so draft instances — defined but
# without graph data in this environment — register only where
# KALLIPOLIS_DRAFT_LANDSCAPES is set. Prod exposes published instances only.
for _landscape_spec in routable_specs():
    _register_landscape_routes(_landscape_spec)


# ── Landscape index — the live (member, sector) catalog ──────────────────────
# Every college/district member that runs >=1 feeding program per sector (the
# publish predicate), for the frontend's instance list + generated-route params.
# Registered BEFORE the dynamic /{instance_id} so "landscapes" isn't swallowed.
@router.get("/landscapes", name="get_landscape_index")
def get_landscape_index():
    try:
        instances = live_catalog()
        return {"count": len(instances), "instances": instances}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Generated member×sector instances (any college / district / region) ──────
# The pinned instances above keep their explicit literal routes (byte-identical).
# This dynamic family resolves any OTHER "{member}-{sector}" id on demand from
# the member catalog (registry.spec_for), gated by has_supply (live iff the
# member offers a feeding program). It is registered LAST so the static routes
# (/sectors, /opportunity) and the pinned literal routes win by match order; the
# dynamic param route only catches what they don't.
def _resolved_dynamic_spec(instance_id: str) -> LandscapeSpec:
    spec = spec_for(instance_id)
    if spec is None:
        raise HTTPException(status_code=404, detail=f"Unknown landscape '{instance_id}'")
    # Pinned instances are always live; a generated one must clear the supply gate.
    if instance_id not in REGISTRY and not has_supply(spec):
        raise HTTPException(
            status_code=404, detail=f"No feeding program for '{instance_id}'"
        )
    # Single-college lens → expand to the college's cluster consortium: the
    # co-member schools become the matrix columns and the cluster occupations the
    # rows, so the school reads itself inside its partnership pool. The dashboard
    # is unchanged; only the spec's college/SOC scope widens. Multi-college
    # instances (districts, SVAMP/BACCC/SMCCD) are untouched.
    if len(spec.colleges) == 1:
        sector_id = next(
            (sid for sid in SECTORS if instance_id.endswith(f"-{sid}")), None
        )
        if sector_id:
            spec = cluster_expanded_spec(spec, sector_id)
    return resolve(spec)


def get_dynamic_landscape(instance_id: str):
    try:
        return build_landscape(_resolved_dynamic_spec(instance_id))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def get_dynamic_programs(instance_id: str):
    try:
        return build_programs_landscape(_resolved_dynamic_spec(instance_id))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def get_dynamic_program(instance_id: str, top6: str, college: str | None = None):
    try:
        return build_program_report(
            top6, college=college, spec=_resolved_dynamic_spec(instance_id)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def get_dynamic_occupation(instance_id: str, soc: str, college: str | None = None):
    try:
        return build_landscape_occupation(
            soc, spec=_resolved_dynamic_spec(instance_id), college=college
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def get_dynamic_employers(instance_id: str):
    try:
        return build_landscape_employers(_resolved_dynamic_spec(instance_id))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


router.add_api_route(
    "/{instance_id}", get_dynamic_landscape, methods=["GET"],
    response_model=Landscape, name="get_dynamic_landscape",
    description="Generated member×sector landscape — any college/district/region "
                "the member catalog resolves, live iff it has a feeding program.")
router.add_api_route(
    "/{instance_id}/programs", get_dynamic_programs, methods=["GET"],
    response_model=ProgramsLandscape, name="get_dynamic_programs")
router.add_api_route(
    "/{instance_id}/program/{top6}", get_dynamic_program, methods=["GET"],
    response_model=ProgramReport, name="get_dynamic_program")
router.add_api_route(
    "/{instance_id}/occupation/{soc}", get_dynamic_occupation, methods=["GET"],
    response_model=LandscapeOccupationReport, name="get_dynamic_occupation")
router.add_api_route(
    "/{instance_id}/employers", get_dynamic_employers, methods=["GET"],
    response_model=LandscapeEmployersResult, name="get_dynamic_employers")


# ── Occupational clusters — connected-component target clusters ───────────────
# Two endpoints over partnerships.clusters (connected components on shared awarded
# feeder TOPs, aggregated across every PCAH sector for a member, e.g. "baccc"):
#   /{member}/clusters       — the visualization payload (all the numbers)
#   /{member}/cluster-supply — the school×TOP supply detail, kept SEPARATE so the
#                              map stays light and the tuple list loads on demand.
# Two segments with literal tails ("clusters" / "cluster-supply"), so they never
# collide with the single-segment dynamic /{instance_id} family above.
class ClusterOccupationModel(BaseModel):
    soc: str
    title: str
    annual_openings: int
    annual_wage: int
    growth_rate: float
    admitted: bool


class ClusterFeederModel(BaseModel):
    top6: str
    name: str
    awards: int
    colleges: int


class ClusterModel(BaseModel):
    id: str
    label: str
    sector_id: str
    sector_label: str
    accent: str
    demand: int
    supply: int
    gap: int
    coverage: float
    n_colleges: int
    n_programs: int
    wage_low: int
    wage_high: int
    occupations: list[ClusterOccupationModel]
    feeders: list[ClusterFeederModel]


class ClusterMapModel(BaseModel):
    member: str
    n_clusters: int
    n_occupations: int
    total_demand: int
    total_supply: int
    total_gap: int
    clusters: list[ClusterModel]


class ClusterSupplyTupleModel(BaseModel):
    college: str
    top6: str
    program: str
    awards: int


class ClusterSupplyModel(BaseModel):
    id: str
    label: str
    sector_id: str
    supply: int
    tuples: list[ClusterSupplyTupleModel]


class ClusterSupplyMapModel(BaseModel):
    member: str
    clusters: list[ClusterSupplyModel]


def _sector_label(sid: str) -> str:
    s = SECTORS.get(sid)
    return s.label if s else sid


def _sector_accent(sid: str) -> str:
    s = SECTORS.get(sid)
    return getattr(s, "accent", None) or "#9aa3b2"


def get_consortium_clusters(member_id: str) -> ClusterMapModel:
    """Whole-consortium occupational-cluster map: every connected-component
    cluster across the member's PCAH sectors, gap-sorted, with demand / supply /
    gap / coverage and the member occupations (wage, openings, growth)."""
    try:
        clusters = consortium_clusters(member_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    if not clusters:
        raise HTTPException(status_code=404, detail=f"No clusters for '{member_id}'")
    models = [
        ClusterModel(
            id=cl.key, label=cl.label, sector_id=cl.sector_id,
            sector_label=_sector_label(cl.sector_id), accent=_sector_accent(cl.sector_id),
            demand=cl.demand, supply=cl.supply, gap=cl.gap, coverage=cl.coverage,
            n_colleges=cl.n_colleges, n_programs=len(cl.feeders),
            wage_low=cl.wage_low, wage_high=cl.wage_high,
            occupations=[ClusterOccupationModel(
                soc=o.soc, title=o.title, annual_openings=o.annual_openings,
                annual_wage=o.annual_wage, growth_rate=o.growth_rate, admitted=o.admitted,
            ) for o in cl.occupations],
            feeders=[ClusterFeederModel(
                top6=f.top6, name=f.name, awards=f.awards, colleges=f.colleges,
            ) for f in cl.feeders],
        )
        for cl in clusters
    ]
    return ClusterMapModel(
        member=member_id, n_clusters=len(models),
        n_occupations=sum(len(m.occupations) for m in models),
        total_demand=sum(m.demand for m in models),
        total_supply=sum(m.supply for m in models),
        total_gap=sum(m.gap for m in models),
        clusters=models,
    )


def get_consortium_cluster_supply(member_id: str) -> ClusterSupplyMapModel:
    """The school×TOP supply tuples behind every cluster — (member college,
    feeder program, latest-year awards). Separate from /clusters so the map
    payload stays light and this loads on demand."""
    try:
        clusters = consortium_clusters(member_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    if not clusters:
        raise HTTPException(status_code=404, detail=f"No clusters for '{member_id}'")
    models = []
    for cl in clusters:
        tuples = [
            ClusterSupplyTupleModel(
                college=sp.college, top6=f.top6, program=f.name, awards=sp.awards)
            for f in cl.feeders for sp in f.by_college
        ]
        tuples.sort(key=lambda t: -t.awards)
        models.append(ClusterSupplyModel(
            id=cl.key, label=cl.label, sector_id=cl.sector_id, supply=cl.supply,
            tuples=tuples))
    return ClusterSupplyMapModel(member=member_id, clusters=models)


router.add_api_route(
    "/{member_id}/clusters", get_consortium_clusters, methods=["GET"],
    response_model=ClusterMapModel, name="get_consortium_clusters",
    description="Whole-consortium occupational-cluster map (connected components on "
                "shared feeder programs) with demand/supply/gap per cluster.")
router.add_api_route(
    "/{member_id}/cluster-supply", get_consortium_cluster_supply, methods=["GET"],
    response_model=ClusterSupplyMapModel, name="get_consortium_cluster_supply",
    description="School×TOP supply tuples behind each cluster — separate endpoint, "
                "loaded on demand.")


# ── L1 lens — the neutral substrate both artifacts render from ────────────────
class LensMemberOut(BaseModel):
    id: str
    name: str
    kind: str


class LensSliceOut(BaseModel):
    kind: str
    id: str
    label: str
    title: str | None = None


class LensScopeOut(BaseModel):
    member: LensMemberOut
    regions: list[str]
    slice: LensSliceOut
    partner_universe: list[str]


class LensFeederOut(BaseModel):
    college: str
    top6: str
    program: str
    awards: int
    is_member: bool


class LensEmployerOut(BaseModel):
    name: str
    naics4: str | None = None
    relevance: float


class LensOccupationOut(BaseModel):
    soc: str
    title: str
    description: str | None = None
    region: str
    annual_openings: int
    median_wage: int
    growth_rate: float
    member_feeds: bool
    feeders: list[LensFeederOut]
    employers: list[LensEmployerOut]


class LensProgramOut(BaseModel):
    college: str
    top6: str
    program: str
    is_member: bool
    socs: list[str]
    awards: dict[str, int]
    enrollment: dict[str, int]


class LensSourceOut(BaseModel):
    id: str
    authority: str
    role: str


class LensModelOut(BaseModel):
    scope: LensScopeOut
    occupations: list[LensOccupationOut]
    programs: list[LensProgramOut]
    award_years: list[str]
    enrollment_terms: list[str]
    field_authority: dict[str, str]
    sources: list[LensSourceOut]


def get_member_lens(member_id: str, sector: str) -> LensModelOut:
    """L1 lens — the neutral, provenance-carrying projection of the ontology over a
    `(member, sector)` scope: occupations ranked by annual openings, each with its
    regional demand, the partner graph (which consortium schools feed it), and its
    employers. The dashboard renders from this; the report renders from the same
    builder. No opinionated score, no cross-occupation supply sum."""
    try:
        lens = build_lens(member_id, sector=sector)
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return LensModelOut(**lens.to_dict())


router.add_api_route(
    "/{member_id}/lens", get_member_lens, methods=["GET"],
    response_model=LensModelOut, name="get_member_lens",
    description="L1 lens — the neutral substrate (occupation-grain, openings-ranked, "
                "partner graph + employers + provenance) that the dashboard and the "
                "report both render from. Requires a ?sector= query param.")


# ── Report HTML — the proposer-filled workforce-pathway report for a role ─────
def get_report_html(member_id: str, title: str, sector: str, socs: str,
                    author: str = "Kallipolis", date: str = "") -> Response:
    """Render a workforce-pathway report to HTML for a (member, role). The role is
    the play: ``title`` + ``sector`` + comma-separated ``socs``. propose_spec
    auto-fills the rest from L1; build_report_html renders it. Returns text/html —
    the report-render harness rasterizes it to .docx/.pdf, or a browser views it."""
    from partnerships.report import Play, build_report_html, propose_spec

    play = Play(id=title.lower().replace(" ", "-"), title=title, sector=sector,
                socs=tuple(s.strip() for s in socs.split(",") if s.strip()))
    try:
        lens = build_lens(member_id, play=play)
        spec = propose_spec(member_id, play, lens=lens, author=author, date=date)
        html = build_report_html(member_id, play, spec, lens=lens)
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return Response(content=html, media_type="text/html")


router.add_api_route(
    "/report/{member_id}", get_report_html, methods=["GET"],
    name="get_report_html",
    description="Workforce-pathway report HTML for a (member, role). Role = ?title= "
                "+ ?sector= + ?socs= (comma-separated SOCs). The proposer auto-fills "
                "the report; the report-render harness turns the HTML into .docx/.pdf.")


class PostingOverride(BaseModel):
    employer: str
    title: str
    url: str


class ReportRequest(BaseModel):
    title: str
    sector: str
    socs: str
    author: str = "Kallipolis"
    date: str = ""
    # Curation overrides from the report-time skills ("data proposes, skill
    # confirms"). Empty → the proposer's defaults stand. live_postings is the
    # find-live-postings skill's selected postings, keyed by SOC.
    live_postings: dict[str, PostingOverride] | None = None


def post_report_html(member_id: str, req: ReportRequest) -> Response:
    """Like the GET, but layers curation OVERRIDES onto the proposed spec — e.g.
    the find-live-postings skill's selected live postings replacing the proposer's
    generic default. Empty overrides == the GET behavior."""
    import dataclasses

    from partnerships.report import LivePosting, Play, build_report_html, propose_spec

    play = Play(id=req.title.lower().replace(" ", "-"), title=req.title, sector=req.sector,
                socs=tuple(s.strip() for s in req.socs.split(",") if s.strip()))
    try:
        lens = build_lens(member_id, play=play)
        spec = propose_spec(member_id, play, lens=lens, author=req.author, date=req.date)
        if req.live_postings:
            lp = {soc: [LivePosting(p.employer, p.title, p.url)] for soc, p in req.live_postings.items()}
            spec = dataclasses.replace(spec, live_postings=lp)
        html = build_report_html(member_id, play, spec, lens=lens)
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return Response(content=html, media_type="text/html")


router.add_api_route(
    "/report/{member_id}", post_report_html, methods=["POST"], name="post_report_html",
    description="Same as GET /report/{member}, but the JSON body may carry curation "
                "overrides — live_postings (the find-live-postings skill's picks) layered "
                "onto the proposed spec. Empty overrides behave like the GET.")


# Editorial fields a saved-report definition may override on the proposed spec —
# the prose/curation the dialectic refines (everything in ReportSpec that is words
# or selection, never data).
_SPEC_OVERRIDE_FIELDS = (
    "org_name", "org_short", "lede", "byline", "demand_note", "alignment_note",
    "competency_note", "award_note", "enrollment_note", "dashboard_url",
    # Program evaluations only: the TOP6 under evaluation. Its presence is the trigger
    # for the "Awards Offered" section — role-report defs omit it entirely.
    "program_top",
)


def _saved_dir():
    from pathlib import Path
    return Path(__file__).resolve().parent / "saved_reports"


def _generated_report_html(slug: str) -> str:
    """Render the CLEAN report HTML from its saved definition (play + editorial/
    curation overrides), read fresh per call. What the ?raw view and the docx render
    consume — no edit affordances."""
    import dataclasses
    import json

    from partnerships.report import (CompetencyColumn, LivePosting, Play,
                                      build_report_html, propose_spec)

    path = _saved_dir() / f"{slug}.json"
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"no saved report '{slug}'")
    d = json.loads(path.read_text())
    play = Play(id=slug, title=d["title"], sector=d["sector"], socs=tuple(d["socs"]))
    member = d["member"]
    # Charter partners (the def's partnership) join the supply scope so a member the
    # cluster pool doesn't reach (e.g. Evergreen Valley) is readable — carried by
    # enrollment when its award data is missing.
    charter: tuple[str, ...] = ()
    if d.get("partnership"):
        from partnerships.registry import spec_for
        ps = spec_for(d["partnership"])
        charter = tuple(ps.colleges) if ps else ()
    lens = build_lens(member, play=play, extra_colleges=charter)
    spec = propose_spec(member, play, lens=lens,
                        author=d.get("author", "Kallipolis"), date=d.get("date", ""))
    over = {k: d[k] for k in _SPEC_OVERRIDE_FIELDS if d.get(k) is not None}
    if d.get("live_postings"):
        # a SOC may carry a single posting (dict) or several (list) — normalize to a list
        over["live_postings"] = {
            soc: [LivePosting(p["employer"], p["title"], p["url"])
                  for p in (plist if isinstance(plist, list) else [plist])]
            for soc, plist in d["live_postings"].items()}
    if d.get("competencies"):
        # the curate-competencies skill's cut (shared core + distinctions), overriding
        # the deterministic distinctiveness default; the grid aligns these by sharing.
        over["competencies"] = [
            CompetencyColumn(soc=soc, description=c.get("description", ""),
                             knowledge=c.get("knowledge", []), skills=c.get("skills", []),
                             abilities=c.get("abilities", []), technology=c.get("technology", []))
            for soc, c in d["competencies"].items()
        ]
    # Partner selection (drives BOTH the crosswalk and the trend tables): an explicit
    # def.programs override wins (incl. strategic adds); else the size-∪-charter rule.
    # Applied even WITHOUT a charter — "BACCC breadth by size" is the norm — so a plain
    # member report shows the award-proven partner set (one strongest program per
    # college, ≥ the floor), not every 0-award program that happens to feed the SOC.
    if d.get("programs"):
        over["programs"] = [tuple(x) for x in d["programs"]]
    else:
        from partnerships.report import select_partner_programs
        over["programs"] = sorted(select_partner_programs(
            lens.programs, charter, min_awards=int(d.get("partner_min_awards", 50))))
        if charter:
            chosen_colleges = {c for c, _ in over["programs"]}
            over["charter_gaps"] = tuple(c for c in charter if c not in chosen_colleges)
    if over:
        spec = dataclasses.replace(spec, **over)
    return build_report_html(member, play, spec, lens=lens)


# Injected ONLY into the editable view (never ?raw or the docx render): makes the
# prose directly editable in the browser, locks the data tables/figures, and saves
# the cleaned document back — so language tweaks need no agent round-trip.
_EDIT_TOOLBAR = """
<div id="kp-editbar" contenteditable="false" style="position:fixed;top:12px;right:12px;z-index:99999;background:#11131c;color:#cdd5e4;font:13px/1.4 -apple-system,system-ui,sans-serif;padding:9px 12px;border-radius:9px;box-shadow:0 4px 16px rgba(0,0,0,.35);display:flex;gap:10px;align-items:center">
  <span id="kp-status" style="opacity:.65">edit prose &middot; &#8984;S saves</span>
  <button onclick="kpSave()" style="background:#3b82f6;color:#fff;border:0;border-radius:6px;padding:5px 13px;font:inherit;cursor:pointer">Save</button>
  <button onclick="kpRevert()" style="background:transparent;color:#8a94ab;border:1px solid #2a2f3e;border-radius:6px;padding:5px 10px;font:inherit;cursor:pointer">Revert</button>
</div>
<script id="kp-editscript">
(function(){
  document.body.contentEditable = 'true';
  document.querySelectorAll('table, svg, img, figure, #kp-editbar').forEach(function(e){ e.contentEditable='false'; });
  // contenteditable swallows link clicks — restore navigation (open in a new tab)
  document.addEventListener('click', function(ev){
    var a = ev.target.closest && ev.target.closest('a[href]');
    if (a && !a.closest('#kp-editbar')) {
      var href = a.getAttribute('href');
      if (href && href.charAt(0) !== '#') { ev.preventDefault(); window.open(a.href, '_blank', 'noopener'); }
    }
  }, true);
  function st(t,c){ var s=document.getElementById('kp-status'); s.textContent=t; s.style.color=c||'#cdd5e4'; }
  document.body.addEventListener('input', function(){ st('unsaved\\u2026','#f59e0b'); });
  window.kpSave = async function(){
    var d = document.documentElement.cloneNode(true);
    ['#kp-editbar','#kp-editscript'].forEach(function(s){ var n=d.querySelector(s); if(n) n.remove(); });
    d.querySelectorAll('[contenteditable]').forEach(function(e){ e.removeAttribute('contenteditable'); });
    try { var r = await fetch(location.pathname.replace(/\\/$/,'')+'/save',{method:'POST',headers:{'Content-Type':'text/html'},body:'<!DOCTYPE html>\\n'+d.outerHTML});
      st(r.ok?'saved \\u2713':'save failed', r.ok?'#22c55e':'#ef4444'); }
    catch(e){ st('save failed','#ef4444'); }
  };
  window.kpRevert = async function(){
    if(!confirm('Discard your edits and regenerate from the definition + data?')) return;
    await fetch(location.pathname.replace(/\\/$/,'')+'/revert',{method:'POST'}); location.reload();
  };
  window.addEventListener('keydown', function(e){ if((e.metaKey||e.ctrlKey)&&e.key==='s'){ e.preventDefault(); window.kpSave(); }});
})();
</script>
"""


def get_saved_report(slug: str, raw: int = 0) -> Response:
    """The dialectical surface. Serves a saved report's HTML; if a hand-EDITED
    version exists it serves that, else renders from the def (read fresh, so agentic
    def edits show on refresh). The default view injects an edit toolbar — click into
    the prose, type, ⌘S — so language tweaks self-serve; ?raw=1 is the clean
    artifact for the docx render."""
    edited = _saved_dir() / f"{slug}.edited.html"
    clean = edited.read_text(encoding="utf-8") if edited.exists() else _generated_report_html(slug)
    if raw:
        return Response(content=clean, media_type="text/html")
    return Response(content=clean.replace("</body>", _EDIT_TOOLBAR + "</body>", 1),
                    media_type="text/html")


async def save_report(slug: str, request: Request) -> dict:
    """Persist the hand-edited report HTML the edit view POSTs, so prose edits survive
    a refresh. Subsequent views serve the edited version until Revert regenerates."""
    if not (_saved_dir() / f"{slug}.json").exists():
        raise HTTPException(status_code=404, detail=f"no saved report '{slug}'")
    body = (await request.body()).decode("utf-8")
    (_saved_dir() / f"{slug}.edited.html").write_text(body, encoding="utf-8")
    return {"status": "saved", "bytes": len(body)}


def revert_report(slug: str) -> dict:
    """Discard the hand-edited version — the next view regenerates from def + data."""
    p = _saved_dir() / f"{slug}.edited.html"
    if p.exists():
        p.unlink()
    return {"status": "reverted"}


router.add_api_route("/report/saved/{slug}", get_saved_report, methods=["GET"],
                     name="get_saved_report",
                     description="Editable report view (dialectical surface). ?raw=1 = clean artifact.")
router.add_api_route("/report/saved/{slug}/save", save_report, methods=["POST"],
                     name="save_report", description="Persist the hand-edited report HTML.")
router.add_api_route("/report/saved/{slug}/revert", revert_report, methods=["POST"],
                     name="revert_report", description="Discard edits; regenerate from the def.")
