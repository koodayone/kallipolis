"""Load a college's courses from the cached enriched.json directly,
bypassing Stage 1 (PDF scrape via Gemini).

The pipeline's `--from-cache` flag checks for `{college}_raw.json`, not
`{college}_enriched.json`. Some colleges have only the enriched cache
(not the raw one), so passing --from-cache silently falls through to
re-scraping. This helper runs Stages 2.5 (department canonicalization)
and 3 (Neo4j load) directly against the enriched cache, which is the
only thing those stages actually depend on.

Also clears stale Course nodes for the college (those whose code is no
longer in the latest enriched cache) so dept fragmentation from prior
runs gets purged on every load. The base loader uses MERGE and never
deletes Course nodes — that creates "Unmapped: X" zombies whenever
a prior run used --allow-unmapped-departments and a later run with a
better overlay didn't see those courses again.

Usage:
    python tools/courses-audit/reload_from_enriched.py --college sbcc
    python tools/courses-audit/reload_from_enriched.py --college sbcc --allow-unmapped
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

# In-container layout puts backend at /app, not at REPO/backend.
# Detect by checking which path actually has the modules.
REPO = Path(__file__).resolve().parent.parent.parent
BACKEND = (
    REPO / "backend"
    if (REPO / "backend" / "ontology").is_dir()
    else Path("/app")
)
sys.path.insert(0, str(BACKEND))

from courses.extraction_filter import filter_extracted  # noqa: E402
from courses.load import load_college, CollegeConfig  # noqa: E402
from ontology.schema import get_driver, close_driver  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("reload")

CACHE_DIR = BACKEND / "pipeline" / "cache"


def load_college_config(college_key: str) -> CollegeConfig:
    """Resolve the CollegeConfig from catalog_sources.json for `college_key`."""
    src = BACKEND / "pipeline" / "catalog_sources.json"
    data = json.loads(src.read_text())
    default_region = data.get("region", "Unknown")
    info = data.get("colleges", {}).get(college_key)
    if not info:
        raise ValueError(f"Unknown college key: {college_key}")
    return CollegeConfig(
        name=info["name"],
        region=info.get("region", default_region),
        city=info.get("city", ""),
        state="California",
    )


def purge_stale_courses(college_name: str, live_codes: set[str]) -> int:
    """Delete Course nodes whose code is not in `live_codes` for this
    college. Returns the count removed. Idempotent."""
    from neo4j import GraphDatabase
    driver = get_driver()
    deleted = 0
    with driver.session() as s:
        # Get current codes in Neo4j for this college
        rows = s.run(
            "MATCH (c:Course {college: $col}) RETURN c.code AS code",
            col=college_name,
        ).data()
        existing = {r["code"] for r in rows}
        stale = existing - live_codes
        if not stale:
            return 0
        # Delete in chunks of 200
        stale_list = list(stale)
        for i in range(0, len(stale_list), 200):
            chunk = stale_list[i:i+200]
            r = s.run(
                "MATCH (c:Course {college: $col}) "
                "WHERE c.code IN $codes "
                "DETACH DELETE c "
                "RETURN count(c) AS n",
                col=college_name, codes=chunk,
            ).single()
            deleted += r["n"]
    return deleted


def cleanup_orphan_departments() -> int:
    """Remove Department nodes with no inbound CONTAINS edges. Same
    pass that load.py does at the end, but extracted so we can run it
    after surgical Course-node deletion too."""
    driver = get_driver()
    with driver.session() as s:
        r = s.run(
            "MATCH (d:Department) "
            "WHERE NOT (d)-[:CONTAINS]->(:Course) "
            "DETACH DELETE d "
            "RETURN count(d) AS n"
        ).single()
        return r["n"]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    ap.add_argument("--college", required=True, help="college key")
    args = ap.parse_args()

    config = load_college_config(args.college)
    enriched_cache = CACHE_DIR / f"{args.college}_enriched.json"
    if not enriched_cache.exists():
        logger.error(f"No enriched cache at {enriched_cache}")
        return 1

    courses = json.loads(enriched_cache.read_text())
    logger.info(f"Loaded {len(courses)} courses from {enriched_cache}")

    # Apply extraction filter (idempotent on clean caches).
    pre = len(courses)
    courses, dropped = filter_extracted(courses)
    if dropped:
        from collections import Counter
        rc = Counter(reason for _, reason in dropped)
        logger.info(f"Filter dropped {len(dropped)}/{pre}: {dict(rc)}")

    # Persist filtered list back to the cache so future runs see the
    # cleaned data. Department canonicalization happens inside
    # `load_college` from `Course.top_code` via the TOP4 manual table —
    # no per-college overlay involved.
    enriched_cache.write_text(json.dumps(courses, indent=2, ensure_ascii=False))

    # Stage 3: load.
    live_codes = {c["code"] for c in courses if c.get("code")}
    purged = purge_stale_courses(config.name, live_codes)
    if purged:
        logger.info(f"Purged {purged} stale Course node(s) not in latest enriched.json")

    driver = get_driver()
    try:
        stats = load_college(driver, config, courses)
    finally:
        close_driver()

    orphans = cleanup_orphan_departments()
    if orphans:
        logger.info(f"Deleted {orphans} orphan Department node(s)")

    logger.info(
        f"Done: {stats.courses_created} courses, "
        f"{stats.courses_with_top_code} top-coded, "
        f"{stats.departments_created} departments"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
