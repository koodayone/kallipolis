"""Observable, resumable per-county EDD scrape (token-free, pure HTTP).

`scrape_region` writes its cache only once at the very end, so a mid-run
failure on a 12-county sweep loses everything. This wrapper scrapes one county
at a time, checkpointing each to its own cache file — which is also exactly the
grain we want for the (county × sector × size) distribution that sets the
enrichment budget.

Resumable: a county whose cache file already exists is skipped.

  python -m employers.scrape_bay_counties                 # all Bay counties, F+
  python -m employers.scrape_bay_counties Bay "San Benito" # just one (for testing)
"""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

from employers.edd_scrape import (
    CACHE_DIR,
    DEFAULT_MIN_SIZE,
    search_naics_codes,
)
from ontology.regions import COE_REGION_TO_COUNTIES

logging.basicConfig(level=logging.INFO, format="%(message)s", stream=sys.stdout)
log = logging.getLogger("bay_scrape")


def _county_cache(county: str, min_size: str) -> Path:
    return CACHE_DIR / f"edd_county_{county.lower().replace(' ', '_')}_{min_size.lower()}.json"


def main() -> None:
    region = sys.argv[1] if len(sys.argv) > 1 else "Bay"
    only = set(sys.argv[2].split(",")) if len(sys.argv) > 2 else None
    min_size = DEFAULT_MIN_SIZE

    counties = COE_REGION_TO_COUNTIES[region]
    if only:
        counties = [c for c in counties if c in only]

    CACHE_DIR.mkdir(exist_ok=True)
    log.info(f"=== {region}: {len(counties)} counties, min_size={min_size}+ ===")
    for i, county in enumerate(counties, 1):
        fp = _county_cache(county, min_size)
        if fp.exists():
            n = len(json.load(open(fp)))
            log.info(f"[{i}/{len(counties)}] {county}: cached ({n}) — skip")
            continue
        log.info(f"[{i}/{len(counties)}] {county}: scraping…")
        recs = search_naics_codes(county, None, min_size)
        for e in recs:
            e["county"] = county
        json.dump(recs, open(fp, "w"), indent=2)
        log.info(f"[{i}/{len(counties)}] {county}: {len(recs)} employers -> {fp.name}", )
    log.info("done")


if __name__ == "__main__":
    main()
