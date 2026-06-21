"""Partnership endpoints — sector index and per-occupation opportunity reports.

The Partnerships surface is occupation-centric: SOCs are organized under
the 12 PCAH-classified Strong Workforce sectors and each report frames
the regional employer set as candidate partners for a multi-employer
engagement around the occupational pathway.

Serving-layer cache: when the precomputed cache files (built by
partnerships.precompute) exist on disk, we read them directly and skip
the 6–8 Cypher queries per request that produced the slow tail
(p99=60s, max=469s on prod). Cache misses fall through to the live
compute path — fully graceful, no behavior change.

Cache hits return gzipped JSON files unchanged (Cache-Control header
allows browser/CDN to cache as well). Cache misses run the live path
and return as before.

Sector hint handling for opportunity reports: the cache is keyed by
(college, SOC) with the alphabetically-default sector baked in. When
a request comes with a `sector` hint that doesn't match the default,
we fall through to live compute — the narrative text uses the sector
name in its templating, so a simple field swap would be incorrect.
This covers the dominant case (default-tab clicks) fast while
preserving correctness on cross-sector deep-links.
"""

import gzip
import json
import logging
import os
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel

from partnerships.models import OpportunityReport, SectorIndex
from partnerships.opportunity import build_opportunity_report, build_sector_index
from partnerships.svamp import SvampLandscape, build_landscape
from partnerships.landscape import REGISTRY, LandscapeSpec, routable_specs
from partnerships.registry import has_supply, live_catalog, spec_for
from partnerships.resolve import resolve
from partnerships.clusters import cluster_expanded_spec, consortium_clusters
from partnerships.lens import build_lens
from partnerships.sectors import SECTORS
from partnerships.svamp_employers import SvampEmployersResult, build_svamp_employers
from partnerships.svamp_programs import (
    ProgramReport,
    ProgramsLandscape,
    SvampOccupationReport,
    build_program_report,
    build_programs_landscape,
    build_svamp_occupation,
)
from partnerships.precompute import (
    CACHE_SCHEMA_VERSION,
    manifest_path,
    opportunity_path,
    overlay_path,
    sectors_path,
)

logger = logging.getLogger(__name__)
router = APIRouter()

# Cache directory — same env var the build job uses. Default mirrors
# the systemd-managed prod location.
CACHE_DIR = Path(os.environ.get(
    "KALLIPOLIS_CACHE_DIR", "/var/lib/kallipolis/cache"
))

# Per-SOC list of valid sectors, sorted alphabetically. Loaded at
# startup from the precompute build's overlay table. Used to determine
# the default sector for a SOC (first in the sorted list) so we can
# decide whether the incoming request's sector hint matches what was
# baked into the cached file.
#
# If the overlay file doesn't exist (cache directory empty, fresh
# deploy before the first build), this stays empty. The serving
# layer then treats every request as a cache miss and falls through
# to live compute — same behavior as before precompute existed.
_OVERLAY: dict[str, list[str]] = {}
_CACHE_VERSION_OK: bool = False

# When the cache is not yet usable, periodically retry loading
# metadata so a build that finishes mid-process becomes visible
# without requiring a backend restart. 60 second cooldown keeps the
# fail-fallback path's overhead negligible (one os.stat per minute,
# not per request).
import time as _time
_LAST_LOAD_ATTEMPT: float = 0.0
_LOAD_RETRY_SECONDS: float = 60.0

# Browser-side cache TTL. Five minutes balances freshness against
# absorbing repeat-view traffic at the CDN/browser layer. Underlying
# data updates monthly, so this is conservative.
CACHE_CONTROL_HEADER = "public, max-age=300, stale-while-revalidate=600"


def _load_cache_metadata() -> None:
    """Populate module-level overlay + version validity from disk.

    Called once at module import. Re-importable / re-callable for
    tests. Failures are tolerated — the serving layer just falls
    through to live compute when the cache isn't usable.
    """
    global _OVERLAY, _CACHE_VERSION_OK
    try:
        manifest = json.loads(manifest_path(CACHE_DIR).read_text())
        version = manifest.get("schema_version", -1)
        if version != CACHE_SCHEMA_VERSION:
            logger.warning(
                "Cache schema version mismatch: cache=%s, code=%s. "
                "Treating cache as missing.",
                version, CACHE_SCHEMA_VERSION,
            )
            _CACHE_VERSION_OK = False
            return
        _CACHE_VERSION_OK = True
    except FileNotFoundError:
        logger.info(
            "No precompute manifest at %s. Cache disabled; "
            "all requests will use live compute.",
            manifest_path(CACHE_DIR),
        )
        _CACHE_VERSION_OK = False
        return
    except Exception as e:
        logger.warning("Failed to load cache manifest: %s. Cache disabled.", e)
        _CACHE_VERSION_OK = False
        return

    try:
        _OVERLAY = json.loads(overlay_path(CACHE_DIR).read_text())
        logger.info("Loaded precompute cache: %d SOCs in overlay, schema_version=%d",
                    len(_OVERLAY), CACHE_SCHEMA_VERSION)
    except FileNotFoundError:
        logger.warning("Cache manifest present but overlay missing — cache disabled.")
        _CACHE_VERSION_OK = False
    except Exception as e:
        logger.warning("Failed to load overlay: %s. Cache disabled.", e)
        _CACHE_VERSION_OK = False


def _default_sector_for(soc_code: str) -> Optional[str]:
    """Returns the alphabetically-first PCAH sector for a SOC, or None
    if the SOC has no PCAH classification. Matches the default-sector
    logic in build_opportunity_report so we can tell whether a cached
    report (built with sector_hint=None) is correct for a given
    incoming request."""
    sectors = _OVERLAY.get(soc_code, [])
    return sectors[0] if sectors else None


def _ensure_cache_metadata_loaded() -> None:
    """Cache metadata loads at module import, but a fresh backend
    started before the first precompute build will start with the
    cache disabled. Retry the load every _LOAD_RETRY_SECONDS so a
    build that finishes mid-process becomes visible without a
    backend restart."""
    global _LAST_LOAD_ATTEMPT
    if _CACHE_VERSION_OK:
        return
    now = _time.monotonic()
    if now - _LAST_LOAD_ATTEMPT < _LOAD_RETRY_SECONDS:
        return
    _LAST_LOAD_ATTEMPT = now
    _load_cache_metadata()


def _try_serve_sectors(college: str) -> Optional[Response]:
    """If a precomputed sectors index exists for this college, return
    it as a Response (decompressed JSON). Returns None on cache miss
    so caller falls through to live compute."""
    _ensure_cache_metadata_loaded()
    if not _CACHE_VERSION_OK:
        return None
    path = sectors_path(CACHE_DIR, college)
    if not path.exists():
        return None
    try:
        raw_gz = path.read_bytes()
        body = gzip.decompress(raw_gz)
        return Response(
            content=body,
            media_type="application/json",
            headers={"Cache-Control": CACHE_CONTROL_HEADER, "X-Cache": "HIT"},
        )
    except Exception as e:
        logger.warning("Cache read failed for sectors %r: %s. Falling through.",
                       college, e)
        return None


def _try_serve_opportunity(
    college: str, soc_code: str, sector_hint: Optional[str],
) -> Optional[Response]:
    """If a precomputed opportunity report exists for this exact
    (college, SOC, sector) tuple, return it. Otherwise None to fall
    through.

    The cache is built per-tuple — one file per (college, SOC, sector)
    combination — so every navigable URL has a corresponding cached
    file regardless of which sector tab the user navigated from. The
    sector key is determined by:
      - sector_hint if provided and valid for this SOC, else
      - the alphabetically-first sector for this SOC (matches the
        default-resolution logic in build_opportunity_report)

    For SOCs with no PCAH classification, the file is keyed under
    the sentinel sector slug `_default`.
    """
    _ensure_cache_metadata_loaded()
    if not _CACHE_VERSION_OK:
        return None

    # Resolve the effective sector exactly the way the live path would,
    # so the cached file we look up corresponds to the report that
    # would have been generated.
    valid_sectors = _OVERLAY.get(soc_code, [])
    if sector_hint and sector_hint in valid_sectors:
        effective_sector: Optional[str] = sector_hint
    elif valid_sectors:
        effective_sector = valid_sectors[0]
    else:
        effective_sector = None

    path = opportunity_path(CACHE_DIR, college, soc_code, effective_sector)
    if not path.exists():
        return None
    try:
        raw_gz = path.read_bytes()
        body = gzip.decompress(raw_gz)
        return Response(
            content=body,
            media_type="application/json",
            headers={"Cache-Control": CACHE_CONTROL_HEADER, "X-Cache": "HIT"},
        )
    except Exception as e:
        logger.warning(
            "Cache read failed for opportunity %r/%r/%r: %s. Falling through.",
            college, soc_code, effective_sector, e,
        )
        return None


# Load on import so the first request doesn't pay this cost.
_load_cache_metadata()


@router.get("/sectors", response_model=SectorIndex)
def get_partnership_sectors(college: str):
    """Returns the Strong Workforce sector accordion for a college:
    every PCAH-classified sector with at least one CTE-reachable,
    regionally-demanded occupation, alphabetically ordered.

    Per the institutional-deference principle: the sector→occupation
    mapping comes from the Chancellor's Office Program and Course
    Approval Handbook (PCAH) walked through the TOP-CIP-SOC chain.
    A SOC may appear under multiple sectors — institutional reality,
    not a partition.
    """
    cached = _try_serve_sectors(college)
    if cached is not None:
        return cached

    try:
        return build_sector_index(college)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


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
    if not top_prefix and not cte_only and not exclude_tops:
        cached = _try_serve_opportunity(college, soc_code, sector)
        if cached is not None:
            return cached

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
            return build_svamp_occupation(
                soc, spec=resolve(spec), college=college, include_employers=employers)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    def get_employers():
        try:
            return build_svamp_employers(resolve(spec))
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    router.add_api_route(
        f"/{sid}", get_landscape, methods=["GET"],
        response_model=SvampLandscape, name=f"get_{sid}_landscape",
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
        response_model=SvampOccupationReport, name=f"get_{sid}_occupation",
        description="Aggregated-occupation report — one SOC read consortium-wide: "
                    "regional demand, consortium supply and the resulting gap. "
                    "`employers=false` skips the regional Partnership Opportunities "
                    "gather (the report's dominant cost) for surfaces that don't render it.")
    router.add_api_route(
        f"/{sid}/employers", get_employers, methods=["GET"],
        response_model=SvampEmployersResult, name=f"get_{sid}_employers",
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
        return build_svamp_occupation(
            soc, spec=_resolved_dynamic_spec(instance_id), college=college
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def get_dynamic_employers(instance_id: str):
    try:
        return build_svamp_employers(_resolved_dynamic_spec(instance_id))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


router.add_api_route(
    "/{instance_id}", get_dynamic_landscape, methods=["GET"],
    response_model=SvampLandscape, name="get_dynamic_landscape",
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
    response_model=SvampOccupationReport, name="get_dynamic_occupation")
router.add_api_route(
    "/{instance_id}/employers", get_dynamic_employers, methods=["GET"],
    response_model=SvampEmployersResult, name="get_dynamic_employers")


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


class MemberClusterSectorsModel(BaseModel):
    member: str
    sectors: list[str]


def get_member_cluster_sectors(member_id: str) -> MemberClusterSectorsModel:
    """The sectors where this member belongs to a consortium cluster — its real
    industry targets. A school-lens industry with no cluster membership renders an
    empty (pool-less) dashboard, so the rail uses this to hide it. A member is in a
    sector iff one of its colleges feeds a BACCC cluster there."""
    probe = spec_for(f"{member_id}-adm")  # any sector resolves the member's colleges
    member_colleges = set(probe.colleges) if probe else set()
    if not member_colleges:
        return MemberClusterSectorsModel(member=member_id, sectors=[])
    try:
        clusters = consortium_clusters("baccc")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    sectors = sorted({
        c.sector_id for c in clusters
        if any(sp.college in member_colleges for f in c.feeders for sp in f.by_college)
    })
    return MemberClusterSectorsModel(member=member_id, sectors=sectors)


router.add_api_route(
    "/{member_id}/cluster-sectors", get_member_cluster_sectors, methods=["GET"],
    response_model=MemberClusterSectorsModel, name="get_member_cluster_sectors",
    description="Sectors where the member is in a consortium cluster — its industry "
                "targets, for the school-lens rail (hides industries with no cluster).")


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
