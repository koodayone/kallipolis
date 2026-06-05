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

from partnerships.models import OpportunityReport, SectorIndex
from partnerships.opportunity import build_opportunity_report, build_sector_index
from partnerships.svamp import SvampLandscape, build_svamp_landscape
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
):
    """Returns the per-(college, occupation) partnership opportunity
    report. Composed deterministically from the institutional graph:
    regional demand (COE), TOP-grouped curriculum coverage, student
    impact, regional employer set sorted by NAICS industry share, and
    employer-agnostic narrative pointing to the multi-employer
    engagement opportunity the data identifies.

    The optional `sector` query parameter preserves the user's click
    context: SOCs that belong to multiple PCAH sectors render with
    whichever sector they were navigated from, rather than being
    re-resolved alphabetically. Invalid sectors (not actually one of
    the SOC's PCAH sectors) are ignored — the report falls back to
    the alphabetical default.

    The optional `top_prefix` and `cte_only` query parameters scope the
    curriculum pathway to a TOP division and/or to CTE programs (the SVAMP
    09-only, career-technical lens). The precomputed cache is built unscoped,
    so a scoped request bypasses it and composes live; unscoped requests
    (every per-college report) keep the cache fast-path unchanged.
    """
    if not top_prefix and not cte_only:
        cached = _try_serve_opportunity(college, soc_code, sector)
        if cached is not None:
            return cached

    try:
        return build_opportunity_report(
            college, soc_code, sector_hint=sector, top_prefix=top_prefix, cte_only=cte_only,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/svamp", response_model=SvampLandscape)
def get_svamp_landscape():
    """Returns the aggregated partnership landscape for the Silicon Valley
    Advanced Manufacturing consortium: five member colleges × twelve
    advanced-manufacturing occupations over one shared COE region.

    Bespoke, deterministic, read-only. Demand and the candidate employer set
    are regional (read once / deduped); supply and students are institutional
    (summed across colleges). The per-(college, occupation) leaf reuses the
    existing /partnerships/opportunity/{soc} report unchanged.
    """
    try:
        return build_svamp_landscape()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/svamp/programs", response_model=ProgramsLandscape)
def get_svamp_programs():
    """The SVAMP Programs lens — the supply-side TOP6 universe (every TOP that
    crosswalks to the twelve SVAMP SOCs), each sized by latest-period supply
    summed across the member colleges. Powers the supply treemap + picker."""
    try:
        return build_programs_landscape()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/svamp/program/{top6}", response_model=ProgramReport)
def get_svamp_program(top6: str, college: str | None = None):
    """A single TOP6 program report: the SOCs it feeds (regional demand, never
    summed), per-college award/enrollment series, statewide wage outcomes, and
    the per-school course curriculum for the TOP.

    Optional `college` scopes the report to one member college (the targeted
    college × program view); omitted ⇒ the consortium-aggregated view."""
    try:
        return build_program_report(top6, college=college)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/svamp/occupation/{soc}", response_model=SvampOccupationReport)
def get_svamp_occupation(soc: str):
    """The SVAMP aggregated-occupation report — the dual of the program report.
    One SOC read consortium-wide: regional demand, consortium supply and the
    resulting gap, the 09 programs feeding it (sized by awards), per-college
    award/enrollment series + curriculum, and the SOC-anchored crosswalk marked
    taught-by-any-member-college."""
    try:
        return build_svamp_occupation(soc)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
