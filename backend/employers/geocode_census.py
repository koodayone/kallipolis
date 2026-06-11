"""Geocode employer addresses via the free, keyless US Census batch geocoder.

No API key, no tokens — the Census geocoder takes a CSV of addresses and returns
lat/lng. Merges results into geocode_cache.json keyed by emp_id (the key
load.py:_load_geocode_cache reads). Idempotent: skips already-geocoded emp_ids.

  python -m employers.geocode_census [region=Bay] [limit]
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import requests

_DIR = Path(__file__).parent
EMPLOYERS = _DIR / "employers.json"
CACHE = _DIR / "geocode_cache.json"
# The batch (multipart POST) endpoint 502s through the sandbox proxy; the
# oneline GET endpoint works, so we geocode one address at a time.
CENSUS = "https://geocoding.geo.census.gov/geocoder/locations/onelineaddress"


def _candidates(region: str | None, limit: int | None):
    d = json.load(open(EMPLOYERS))
    cache = json.load(open(CACHE)) if CACHE.exists() else {}
    rows = []
    for e in d:
        if region and region not in (e.get("regions") or []):
            continue
        a = e.get("address") or {}
        eid, street, city = a.get("emp_id"), a.get("street"), a.get("city")
        if not (eid and street and city):
            continue
        if str(eid) in cache and cache[str(eid)].get("lat") is not None:
            continue
        rows.append((str(eid), street, city, a.get("state") or "CA", a.get("zip") or ""))
        if limit and len(rows) >= limit:
            break
    return rows, cache


def _geocode_one(street, city, state, zip_) -> dict | None:
    addr = f"{street}, {city}, {state} {zip_}".strip()
    for attempt in (1, 2):
        try:
            r = requests.get(CENSUS, params={"address": addr, "benchmark": "Public_AR_Current", "format": "json"}, timeout=60)
            if r.status_code >= 500:
                time.sleep(2); continue
            m = r.json().get("result", {}).get("addressMatches", [])
            if not m:
                return None
            c = m[0]["coordinates"]
            return {"lat": c["y"], "lng": c["x"]}
        except Exception:  # noqa: BLE001
            time.sleep(2)
    return None


def main() -> None:
    region = sys.argv[1] if len(sys.argv) > 1 else "Bay"
    limit = int(sys.argv[2]) if len(sys.argv) > 2 else None
    rows, cache = _candidates(region, limit)
    print(f"{len(rows)} {region} employers need geocoding (have street+city, no cached coords)", flush=True)
    matched = 0
    for i, (eid, street, city, state, zip_) in enumerate(rows, 1):
        res = _geocode_one(street, city, state, zip_)
        if res:
            cache[eid] = res
            matched += 1
        if i % 25 == 0 or i == len(rows):
            json.dump(cache, open(CACHE, "w"), indent=2)
            print(f"  {i}/{len(rows)}  matched {matched}", flush=True)
        time.sleep(0.3)
    json.dump(cache, open(CACHE, "w"), indent=2)
    print(f"done: {matched}/{len(rows)} geocoded ({100 * matched // max(1, len(rows))}%); cache now {len(cache)} entries")


if __name__ == "__main__":
    main()
