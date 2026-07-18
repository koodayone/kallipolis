#!/usr/bin/env python3
"""Generate backend/partnerships/data/sector_socs.csv — occupation→sector membership.

METHODOLOGY — the defensible JOIN of two COE Bay Region publications, so the file is
derived and reproducible rather than a frozen hand-list that silently drifts:

    sector_socs.csv = { (sector, soc, title)
                        : soc ∈ the middle-skill occupation universe
                        , sector = the baccc_sectors crosstab that lists soc }

Two authorities, one join:
  1. WHICH occupations exist — the COE middle-skill DEMAND publication, materialized
     as backend/occupations/occupations.json (the 314-occupation universe, itself
     generated from ontology/occupational_demand_middle_skill.csv).
  2. WHICH sector each belongs to — the COE per-sector CROSSTABS (cc_dataset/
     baccc_sectors/, one file per CCCO sector), captured in
     backend/partnerships/data/coe_occupation_sector.csv. The crosstabs partition
     SOCs 1:1, so each occupation has exactly one sector.

Every universe occupation is categorized (universe ⊆ the sector map), so the sector
set exactly covers the universe — no orphans. We deliberately do NOT re-apply the
crosstabs' "Middle Skill" skill-level filter: the universe already scopes
middle-skill, and re-filtering there dropped in-demand, CC-served occupations the
universe keeps — e.g. School Bus (53-3051) and Shuttle Drivers (53-3053), fed by the
vocational Truck-and-Bus-Driving program (094750, home sector atl) and tagged "Below
Middle Skill" in the crosstab but present in the demand universe.

Usage:
    python scripts/generate_sector_socs.py           # regenerate and write the file
    python scripts/generate_sector_socs.py --check    # exit non-zero if it is stale
"""
import argparse
import csv
import json
import sys
from pathlib import Path

_BACKEND = Path(__file__).resolve().parent.parent / "backend"
_UNIVERSE = _BACKEND / "occupations" / "occupations.json"
_MAP = _BACKEND / "partnerships" / "data" / "coe_occupation_sector.csv"
_OUT = _BACKEND / "partnerships" / "data" / "sector_socs.csv"

# The 12 CCCO sectors the engine models, plus 'unassigned'. 'non_cte_stem' is a COE
# crosstab but not an engine sector (no CTE pathway) — a universe occupation must
# never resolve to it, and the guard below fails loudly if one does.
_ENGINE_SECTORS = {
    "adm", "atl", "agwet", "business", "ecu", "edhd", "health", "ict",
    "biotech", "public_safety", "retail", "unassigned",
}


def derive() -> list[tuple[str, str, str]]:
    """Return the sorted (sector_id, soc, title) rows: every universe occupation
    joined to its baccc_sectors sector. Title comes from the universe (occupations.json),
    the single source for occupation titles."""
    universe = {o["soc_code"]: o["title"] for o in json.loads(_UNIVERSE.read_text())}
    soc_to_sector = {}
    with _MAP.open() as f:
        for r in csv.DictReader(f):
            soc_to_sector[r["soc"]] = r["sector_id"]

    rows, missing, non_engine = [], [], []
    for soc, title in universe.items():
        sid = soc_to_sector.get(soc)
        if sid is None:
            missing.append(soc)
        elif sid not in _ENGINE_SECTORS:
            non_engine.append((soc, sid))
        else:
            rows.append((sid, soc, title))
    if missing:
        raise SystemExit(f"universe occupations absent from the COE sector map: {sorted(missing)}")
    if non_engine:
        raise SystemExit(f"universe occupations map to a non-engine sector: {non_engine}")
    return sorted(rows, key=lambda r: (r[0], r[1]))


def _render(rows: list[tuple[str, str, str]]) -> bytes:
    """Exact CSV bytes — header + rows, CRLF-terminated (the file's committed format).
    Byte-exact so the round-trip (write, then --check read) is stable across platforms
    without newline translation surprises."""
    import io
    sio = io.StringIO(newline="")
    w = csv.writer(sio)                       # csv default lineterminator is CRLF
    w.writerow(["sector_id", "soc", "title"])
    w.writerows(rows)
    return sio.getvalue().encode()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="exit non-zero if the file is stale")
    args = ap.parse_args()
    rendered = _render(derive())
    if args.check:
        if _OUT.read_bytes() != rendered:
            print("sector_socs.csv is STALE — run `python scripts/generate_sector_socs.py`", file=sys.stderr)
            sys.exit(1)
        print("sector_socs.csv is current.")
        return
    _OUT.write_bytes(rendered)
    n = rendered.count(b"\n") - 1
    print(f"wrote {_OUT.relative_to(_BACKEND.parent)} — {n} occupations")


if __name__ == "__main__":
    main()
