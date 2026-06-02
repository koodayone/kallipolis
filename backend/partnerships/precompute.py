"""Precompute partnership reports to gzipped JSON on disk.

For every (college, SOC) pair where the OCCUPATION_PIPELINE edge exists,
write the full opportunity report. For every college, write the sectors
index. Files are gzipped JSON at deterministic paths under a cache
directory. The serving layer (partnerships.api) reads these directly,
falling back to the live compute path when a file is absent.

Universe enumeration: one Cypher query against OCCUPATION_PIPELINE edges,
which are themselves materialized at pipeline reload time. The set of
edges is exactly the set of (college, SOC) pairs where the report has
meaningful content (course_count > 0). SOCs the region demands but
the college doesn't institutionally connect to are not in this set —
matching the strict-filter semantics in build_sector_index.

sector_hint handling: the opportunity report is precomputed with no
hint (alphabetical default). The serving layer overlays sector_hint
at request time using `_overlay.json` ({soc_code: [valid sectors]})
plus existing in-memory region-priority lookups. Cache key is just
(college, SOC) — not (college, SOC, sector) — which keeps the universe
~12x smaller.

Output layout:
    {out_dir}/_manifest.json                           — build metadata
    {out_dir}/_overlay.json                            — soc -> sorted sectors
    {out_dir}/<college-slug>/sectors.json.gz           — sector index
    {out_dir}/<college-slug>/opportunity/<soc>.json.gz — opportunity report

Usage (from inside the backend container or local with API_DB env set):
    python -m partnerships.precompute --out /var/lib/kallipolis/cache
    python -m partnerships.precompute --out /tmp/cache --limit 10
    python -m partnerships.precompute --out /tmp/cache --college "Foothill College"
    python -m partnerships.precompute --out /tmp/cache --sectors-only
"""

from __future__ import annotations

import argparse
import gzip
import json
import logging
import os
import re
import sys
import threading
import time
import traceback
import unicodedata
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from neo4j import Driver

from ontology.schema import close_driver, get_driver
from partnerships.opportunity import (
    _load_sector_to_top6,
    _sector_socs,
    build_opportunity_report,
    build_sector_index,
)

logger = logging.getLogger(__name__)

# Bump on any breaking change to the cached JSON shape. The serving
# layer reads this from _manifest.json at startup and treats all cache
# as missing if it disagrees — preventing "serve old shape to clients"
# after a code-only deploy that changed the response model.
#
# v2: per-(college, SOC, sector) cache key. v1 was per-(college, SOC)
# with sector-as-overlay, which had a catastrophic cache miss on
# non-default sector navigation paths — measured 56s tails. v2 builds
# the full sector × pair universe so every navigable URL is a cache HIT.
#
# v3: two report-shape changes that invalidate v2 caches:
#   (a) OpportunityRow.alignment_status — "aligned" | "gap". Sector
#       index now surfaces SOCs with regional demand but no aligned
#       curriculum (course_count = 0) as a workforce-gap signal,
#       rather than silently dropping them.
#   (b) CurriculumCrosswalk.tops keyed at TOP6 instead of TOP4 —
#       matches the actual granularity of CCCCO PCAH's TOP→CIP
#       crosswalk. Each TOP6's CIPs are bridged individually rather
#       than rolled up to a 4-digit family.
CACHE_SCHEMA_VERSION = 3

# Default parallelism for the build. Neo4j queries are I/O-bound from
# the Python side (GIL releases on bolt socket reads), so threads
# scale well. Empirically ~8 threads keeps a single local Neo4j busy
# without OOM'ing its 2GB default heap; >16 risks contention. Overridable
# via --parallelism.
DEFAULT_PARALLELISM = 8

# Stats mutation requires synchronization under threading.
_stats_lock = threading.Lock()


# ── Path helpers (shared with serving layer) ───────────────────────────


def college_slug(college: str) -> str:
    """Deterministic filesystem-safe slug from a canonical college name.

    Examples:
        'Foothill College'      -> 'foothill-college'
        'Cañada College'        -> 'canada-college'
        'Mt. San Antonio College' -> 'mt-san-antonio-college'

    Strips diacritics via NFKD normalization, lowercases, collapses
    non-alphanumeric runs to a single hyphen. Stable across platforms
    and Python versions — same input always produces same output.
    """
    s = unicodedata.normalize("NFKD", college).encode("ascii", "ignore").decode()
    s = s.lower()
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s


def sectors_path(out_dir: Path, college: str) -> Path:
    """Filesystem path to the precomputed sectors index for a college."""
    return out_dir / college_slug(college) / "sectors.json.gz"


def sector_slug(sector: str | None) -> str:
    """Slugify a sector name for use in a filename. Reuses the
    college-slug logic. None maps to '_default' for SOCs with no PCAH
    classification."""
    if sector is None:
        return "_default"
    return college_slug(sector)


def opportunity_path(out_dir: Path, college: str, soc: str, sector: str | None) -> Path:
    """Filesystem path to a precomputed opportunity report for a
    specific (college, SOC, sector) tuple.

    The sector is part of the cache key because the opportunity report's
    narrative bakes in the sector name (executive_summary references it
    by display name). v1 of the cache keyed by (college, SOC) only and
    relied on a serve-time overlay; that produced cache misses on
    non-default-sector navigation, with the live fallback path costing
    tens of seconds. v2 keys by tuple, so every navigable URL is a HIT.
    """
    return (
        out_dir / college_slug(college) / "opportunity"
        / f"{soc}__{sector_slug(sector)}.json.gz"
    )


def manifest_path(out_dir: Path) -> Path:
    return out_dir / "_manifest.json"


def overlay_path(out_dir: Path) -> Path:
    return out_dir / "_overlay.json"


# ── Build job ──────────────────────────────────────────────────────────


@dataclass
class BuildStats:
    started_at: str = ""
    finished_at: str = ""
    schema_version: int = CACHE_SCHEMA_VERSION
    colleges_seen: int = 0
    sectors_written: int = 0
    sectors_failed: int = 0
    opportunities_written: int = 0
    opportunities_failed: int = 0
    total_bytes_gz: int = 0
    timings_ms: list[int] = field(default_factory=list)
    failures: list[dict] = field(default_factory=list)


def enumerate_universe(driver: Driver) -> tuple[list[str], list[tuple[str, str]]]:
    """Walk the graph for the build set.

    Returns (colleges, (college, soc) pairs):
      - colleges: every College node — used for the sectors index. A
        college with zero OCCUPATION_PIPELINE edges still gets a
        sectors index (the index will simply have no surfaced
        sectors). This matches today's API behavior.
      - opportunity_pairs: every (college, SOC) where an
        OCCUPATION_PIPELINE edge exists. This is exactly the set the
        sector index surfaces; reports outside this set are accessible
        only via deep-linking and fall through to the live path.
    """
    with driver.session() as session:
        college_rows = session.run(
            "MATCH (c:College) RETURN c.name AS name ORDER BY c.name"
        ).data()
        colleges = [r["name"] for r in college_rows]

        pair_rows = session.run("""
            MATCH (c:College)-[:OCCUPATION_PIPELINE]->(occ:Occupation)
            RETURN c.name AS college, occ.soc_code AS soc
            ORDER BY c.name, occ.soc_code
        """).data()
        pairs = [(r["college"], r["soc"]) for r in pair_rows]

    return colleges, pairs


def build_overlay() -> dict[str, list[str]]:
    """Build the soc_code -> sorted matching sectors table.

    Computed once globally (no per-college dependence). Mirrors the
    matching-sectors logic in build_opportunity_report. The serving
    layer reads this to decide whether a sector_hint is valid for a
    given SOC.
    """
    sector_to_top6 = _load_sector_to_top6()
    overlay: dict[str, set[str]] = {}
    for sector in sector_to_top6:
        for soc in _sector_socs(sector):
            overlay.setdefault(soc, set()).add(sector)
    return {soc: sorted(s) for soc, s in overlay.items()}


def _write_gzip_atomic(path: Path, payload_bytes: bytes) -> int:
    """Atomically write gzipped bytes. Temp file in same dir to keep
    the rename atomic; partial writes never become visible. Returns
    bytes written (gzipped)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    compressed = gzip.compress(payload_bytes, compresslevel=6)
    tmp.write_bytes(compressed)
    os.replace(tmp, path)
    return len(compressed)


def _pydantic_json_bytes(model) -> bytes:
    """Serialize a Pydantic model to UTF-8 JSON bytes. Uses
    model_dump_json for stable serialization (datetimes, enums, etc.
    handled the same as the FastAPI endpoint would)."""
    return model.model_dump_json().encode("utf-8")


def _build_one_sector_index(college: str, out_dir: Path, stats: BuildStats) -> None:
    t0 = time.monotonic()
    try:
        report = build_sector_index(college)
        path = sectors_path(out_dir, college)
        n_bytes = _write_gzip_atomic(path, _pydantic_json_bytes(report))
        elapsed_ms = int((time.monotonic() - t0) * 1000)
        with _stats_lock:
            stats.sectors_written += 1
            stats.total_bytes_gz += n_bytes
            stats.timings_ms.append(elapsed_ms)
        logger.info(
            "  sectors  %-35s %5d ms  %6d B",
            college[:35], elapsed_ms, n_bytes,
        )
    except Exception as e:
        with _stats_lock:
            stats.sectors_failed += 1
            stats.failures.append({
                "kind": "sectors", "college": college, "error": str(e),
                "trace": traceback.format_exc(limit=3),
            })
        logger.warning("  sectors  %-35s FAILED: %s", college[:35], e)


def _build_one_opportunity(
    college: str, soc: str, sector: str | None,
    out_dir: Path, stats: BuildStats,
) -> None:
    t0 = time.monotonic()
    try:
        # Pass the specific sector as sector_hint so the report's
        # narrative bakes in the right display name. The cached file is
        # then complete for that exact navigation path.
        report = build_opportunity_report(college, soc, sector_hint=sector)
        path = opportunity_path(out_dir, college, soc, sector)
        n_bytes = _write_gzip_atomic(path, _pydantic_json_bytes(report))
        elapsed_ms = int((time.monotonic() - t0) * 1000)
        with _stats_lock:
            stats.opportunities_written += 1
            stats.total_bytes_gz += n_bytes
            stats.timings_ms.append(elapsed_ms)
        sec_short = (sector or "(no-sector)")[:30]
        logger.info(
            "  oppty    %-30s %-10s %-30s %5d ms  %6d B",
            college[:30], soc, sec_short, elapsed_ms, n_bytes,
        )
    except Exception as e:
        with _stats_lock:
            stats.opportunities_failed += 1
            stats.failures.append({
                "kind": "opportunity", "college": college, "soc": soc,
                "sector": sector,
                "error": str(e), "trace": traceback.format_exc(limit=3),
            })
        logger.warning(
            "  oppty    %-30s %-10s %-30s FAILED: %s",
            college[:30], soc, (sector or "(no-sector)")[:30], e,
        )


def _warm_module_caches() -> None:
    """Pre-populate module-level lazy-loaded singletons before spawning
    threads. _load_sector_to_top6, _load_cip_to_soc, etc. cache on
    first call; without warming, multiple threads could race the
    initial population. After this call all subsequent reads are pure
    cache hits with no mutation."""
    from ontology.crosswalks import (
        _load_cip_to_soc, _load_pcah_cte_top6, _load_top_to_cip,
        cte_reachable_socs, load_naics4_titles, load_top_titles,
    )
    _load_sector_to_top6()
    _load_pcah_cte_top6()
    _load_top_to_cip()
    _load_cip_to_soc()
    cte_reachable_socs()
    load_top_titles()
    load_naics4_titles()


def build_all(
    driver: Driver,
    out_dir: Path,
    college_filter: Optional[str] = None,
    sectors_only: bool = False,
    limit: Optional[int] = None,
    parallelism: int = DEFAULT_PARALLELISM,
) -> BuildStats:
    """Run the full precompute build against the current graph state.

    Parallelized via ThreadPoolExecutor. Neo4j queries are I/O-bound
    (the GIL releases on bolt socket reads), so threads scale well
    without the per-process driver lifecycle complexity multiprocessing
    would impose. The Neo4j Python driver itself is thread-safe; each
    query opens its own session internally via get_driver().

    `college_filter` (canonical name): restrict the build to one
    college. Useful for incremental rebuilds after a single-college
    data refresh.
    `sectors_only`: skip the opportunity reports. Fast smoke test.
    `limit`: cap the number of opportunity reports written. Sampling
    test for local development.
    `parallelism`: number of worker threads. Default 8. >16 risks
    Neo4j heap pressure on a 2GB-default deployment.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    stats = BuildStats(started_at=datetime.now(timezone.utc).isoformat())

    colleges, pairs = enumerate_universe(driver)

    if college_filter:
        colleges = [c for c in colleges if c == college_filter]
        pairs = [(c, s) for c, s in pairs if c == college_filter]
        if not colleges and not pairs:
            logger.warning(
                "No matches for college_filter=%r. Check name spelling.",
                college_filter,
            )

    stats.colleges_seen = len(colleges)
    logger.info(
        "Universe: %d colleges, %d (college, SOC) opportunity pairs  "
        "(parallelism=%d)",
        len(colleges), len(pairs), parallelism,
    )

    # Overlay table — soc_code -> sorted matching sectors. Computed
    # once, written once. Independent of Neo4j (pure file lookups +
    # PCAH parsing).
    overlay = build_overlay()
    overlay_path(out_dir).write_text(json.dumps(overlay, sort_keys=True))
    logger.info("Wrote overlay: %d SOCs", len(overlay))

    # Write a partial manifest immediately. The serving layer requires
    # _manifest.json to exist before it will trust the cache. Without
    # this, an interrupted build leaves a directory full of valid
    # cache files that the serving layer ignores. The manifest gets
    # rewritten at end with full stats; if the build is interrupted,
    # the partial manifest still lets the serving layer use whatever
    # files made it to disk.
    _write_manifest_partial(out_dir, stats, parallelism)

    # Warm module-level caches once before spawning workers.
    logger.info("Warming module caches...")
    _warm_module_caches()

    # Sectors indexes — one per college.
    logger.info("─── Sectors indexes (%d, %d threads) ───",
                len(colleges), parallelism)
    with ThreadPoolExecutor(max_workers=parallelism) as ex:
        futures = [
            ex.submit(_build_one_sector_index, c, out_dir, stats)
            for c in colleges
        ]
        for _ in as_completed(futures):
            pass  # work already counted into stats; just wait

    # Opportunity reports — one per (college, SOC, sector) tuple.
    # SOC may appear under multiple PCAH sectors; each needs its own
    # cached file because the report's narrative bakes in the sector
    # display name. SOCs with no PCAH classification get a single file
    # keyed under the literal sector "_default".
    if not sectors_only:
        tuples: list[tuple[str, str, str | None]] = []
        for college, soc in pairs:
            valid_sectors = overlay.get(soc, [])
            if not valid_sectors:
                tuples.append((college, soc, None))
            else:
                for sector in valid_sectors:
                    tuples.append((college, soc, sector))
        target_tuples = tuples if limit is None else tuples[:limit]
        logger.info(
            "─── Opportunity reports (%d tuples = %d pairs × avg %.2f sectors, %d threads) ───",
            len(target_tuples), len(pairs),
            len(target_tuples) / max(1, len(pairs)), parallelism,
        )
        with ThreadPoolExecutor(max_workers=parallelism) as ex:
            futures = [
                ex.submit(_build_one_opportunity, c, s, sec, out_dir, stats)
                for c, s, sec in target_tuples
            ]
            for _ in as_completed(futures):
                pass

    stats.finished_at = datetime.now(timezone.utc).isoformat()

    # Manifest. Written last so a missing-or-stale manifest signals
    # "build did not finish" to the serving layer.
    manifest = {
        "schema_version": CACHE_SCHEMA_VERSION,
        "started_at": stats.started_at,
        "finished_at": stats.finished_at,
        "colleges_seen": stats.colleges_seen,
        "sectors_written": stats.sectors_written,
        "sectors_failed": stats.sectors_failed,
        "opportunities_written": stats.opportunities_written,
        "opportunities_failed": stats.opportunities_failed,
        "total_bytes_gz": stats.total_bytes_gz,
        "n_failures": len(stats.failures),
        "p50_ms": _percentile(stats.timings_ms, 50),
        "p95_ms": _percentile(stats.timings_ms, 95),
        "p99_ms": _percentile(stats.timings_ms, 99),
        "max_ms": max(stats.timings_ms) if stats.timings_ms else 0,
    }
    manifest_path(out_dir).write_text(json.dumps(manifest, indent=2, sort_keys=True))

    # Failure detail goes to a sibling file (kept separate so the
    # success manifest stays small and easy to eyeball).
    if stats.failures:
        (out_dir / "_failures.json").write_text(
            json.dumps(stats.failures, indent=2)
        )

    logger.info("=" * 60)
    logger.info("BUILD COMPLETE")
    logger.info("  Sectors:        %d written, %d failed",
                stats.sectors_written, stats.sectors_failed)
    logger.info("  Opportunities:  %d written, %d failed",
                stats.opportunities_written, stats.opportunities_failed)
    logger.info("  Total bytes (gz): %.1f MB", stats.total_bytes_gz / (1024 * 1024))
    logger.info("  Timings: p50=%d ms  p95=%d ms  p99=%d ms  max=%d ms",
                manifest["p50_ms"], manifest["p95_ms"],
                manifest["p99_ms"], manifest["max_ms"])
    if stats.failures:
        logger.warning("  %d failures recorded — see %s",
                       len(stats.failures), out_dir / "_failures.json")
    return stats


def _percentile(values: list[int], p: int) -> int:
    if not values:
        return 0
    s = sorted(values)
    k = max(0, min(len(s) - 1, int(len(s) * p / 100)))
    return s[k]


def _write_manifest_partial(out_dir: Path, stats: BuildStats, parallelism: int) -> None:
    """Write a partial-build manifest at build start so the serving
    layer's `_CACHE_VERSION_OK` check passes even during an in-progress
    build. Overwritten with full stats at build end."""
    manifest_path(out_dir).write_text(json.dumps({
        "schema_version": CACHE_SCHEMA_VERSION,
        "status": "in_progress",
        "started_at": stats.started_at,
        "colleges_seen": stats.colleges_seen,
        "parallelism": parallelism,
    }, indent=2, sort_keys=True))


# ── CLI ────────────────────────────────────────────────────────────────


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out", type=Path,
        default=Path(os.environ.get(
            "KALLIPOLIS_CACHE_DIR", "/var/lib/kallipolis/cache"
        )),
        help="Output directory for the precomputed cache",
    )
    parser.add_argument(
        "--college", default=None,
        help="Canonical college name to restrict the build to "
             "(e.g. 'Foothill College'). Default: all colleges.",
    )
    parser.add_argument(
        "--sectors-only", action="store_true",
        help="Skip opportunity reports; only build the per-college sectors "
             "indexes. Fast smoke test (~30 s for 116 colleges).",
    )
    parser.add_argument(
        "--limit", type=int, default=None,
        help="Cap the number of opportunity reports written. "
             "Useful for local smoke testing.",
    )
    parser.add_argument(
        "--parallelism", type=int, default=DEFAULT_PARALLELISM,
        help=f"Worker thread count. Default {DEFAULT_PARALLELISM}. "
             "Threads are I/O-bound on Neo4j queries so scaling is "
             "roughly linear up to ~16; beyond that, Neo4j heap "
             "pressure dominates.",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)-7s %(message)s",
        datefmt="%H:%M:%S",
    )

    driver = get_driver()
    try:
        build_all(
            driver=driver,
            out_dir=args.out,
            college_filter=args.college,
            sectors_only=args.sectors_only,
            limit=args.limit,
            parallelism=args.parallelism,
        )
    finally:
        close_driver()
    return 0


if __name__ == "__main__":
    sys.exit(main())
