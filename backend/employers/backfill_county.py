"""Backfill `county` onto existing employers' address blocks.

`county` is the EDD scrape grain and the filter key for the county-configurable
map, but generate.py only started persisting it now — the already-generated
employers lack it. This re-attaches it from the scrape caches:
  1. emp_id -> county   (exact; the stable EDD key)
  2. city   -> county   (fallback, built from all cache (city,county) pairs)

Idempotent and backs up first. Coverage is bounded by which scrape caches are
still on disk: the Bay per-county caches cover the Bay fully; regions whose
caches were rotated away can only be filled when re-scraped.

  python -m employers.backfill_county
"""

from __future__ import annotations

import glob
import json
from collections import Counter
from pathlib import Path

_DIR = Path(__file__).parent
EMPLOYERS = _DIR / "employers.json"


def main() -> None:
    id2c: dict[str, str] = {}
    city2c: dict[str, str] = {}
    for fp in glob.glob(str(_DIR / "cache" / "*.json")):
        try:
            d = json.load(open(fp))
        except Exception:  # noqa: BLE001
            continue
        for r in (d if isinstance(d, list) else list(d.values())):
            if not isinstance(r, dict) or not r.get("county"):
                continue
            if r.get("emp_id"):
                id2c[str(r["emp_id"])] = r["county"]
            if r.get("city"):
                city2c.setdefault(r["city"].strip().lower(), r["county"])

    employers = json.load(open(EMPLOYERS))
    backup = _DIR / "employers.pre-county-backfill.json"
    if not backup.exists():
        json.dump(employers, open(backup, "w"), indent=2)
        print(f"backed up -> {backup.name}")

    by_id = by_city = 0
    tot = Counter(); got = Counter()
    for e in employers:
        addr = e.get("address")
        for r in e.get("regions", []) or ["?"]:
            tot[r] += 1
        if not isinstance(addr, dict) or addr.get("county"):
            if isinstance(addr, dict) and addr.get("county"):
                for r in e.get("regions", []) or ["?"]:
                    got[r] += 1
            continue
        eid = str(addr.get("emp_id") or "")
        county = id2c.get(eid)
        if county:
            by_id += 1
        elif addr.get("city"):
            county = city2c.get(addr["city"].strip().lower())
            if county:
                by_city += 1
        if county:
            addr["county"] = county
            for r in e.get("regions", []) or ["?"]:
                got[r] += 1

    json.dump(employers, open(EMPLOYERS, "w"), indent=2)
    filled = sum(1 for e in employers if (e.get("address") or {}).get("county"))
    print(f"county filled: {filled}/{len(employers)}  (by emp_id={by_id}, by city={by_city})")
    print("coverage by region (with county / total):")
    for r, c in tot.most_common():
        print(f"  {r:8} {got[r]:4d}/{c:<4d} ({100*got[r]//c if c else 0}%)")


if __name__ == "__main__":
    main()
