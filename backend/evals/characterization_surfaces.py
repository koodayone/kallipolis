"""Phase-0 characterization net — freezes the FULL serialized output of every analytical SURFACE
(the 9 MCP forms + the dashboard build path) at a coordinate spread, so the Phase-A engine-unification
refactor is verifiable BYTE-FOR-BYTE (numbers + structure unchanged). Companion to
``characterization.py`` (which pins the underlying quantities); this pins the surfaces on BOTH sides of
the dashboard⇄MCP seam we're closing in Phase A.

It is a behavioral snapshot, not an assertion of correctness — Phase A must reproduce it exactly; Phase B
regenerates it as a signed-off diff (the set of deliberately-changed numbers).

Regenerate (after an INTENDED change, against the reachable graph — the seed in CI or a forwarded compose):
    NEO4J_URI=bolt://localhost:7691 NEO4J_USERNAME=neo4j NEO4J_PASSWORD=… python3.11 -m evals.characterization_surfaces
Verify (the Phase-A guard): pytest evals/test_characterization_surfaces.py
"""
import json
from pathlib import Path

from mcp_server import forms as F
from mcp_server.scope import scope_for
from partnerships.resolve import resolve
from partnerships.landscape_build import build_landscape, sector_demand_decomposition
from partnerships.landscape_programs import build_landscape_occupation
from partnerships.landscape_employers import build_landscape_employers

SNAP_DIR = Path(__file__).parent / "char_surfaces"

# The spread — member kinds (college/district/consortium incl. the bespoke svamp/baccc) × sectors that
# exercise different sector rules × golden SOCs. Widen as coverage gaps surface; every form is hit.
MEMBER_SECTORS = [
    ("smccd", "adm"), ("svamp", "adm"), ("baccc", "health"), ("deanza", "adm"),
    ("skyline", "adm"), ("ccsf", "adm"), ("smccd", "business"),
]
SOCS = {"adm": ["51-4041", "17-3023"], "health": ["29-1141"], "business": ["43-4051"]}
COMPARE = [("program", "addressable_gap"), ("occupation", "supply_gap"), ("college", "sector_supply")]


def _canon(x, nd=1):
    """Round floats (kill repr noise) so a byte diff means a real change, not a float artifact."""
    if isinstance(x, bool):
        return x
    if isinstance(x, float):
        return round(x, nd)
    if isinstance(x, dict):
        return {k: _canon(v, nd) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [_canon(v, nd) for v in x]
    return x


def _dump(obj):
    if obj is None:
        return None
    if hasattr(obj, "model_dump"):
        return _canon(obj.model_dump(mode="json"))
    if hasattr(obj, "__dict__"):
        return _canon({k: _dump(v) for k, v in vars(obj).items()})
    return _canon(obj)


def _safe(fn):
    try:
        return _dump(fn())
    except Exception as e:  # captured so a bad coord/signature is a visible fixture, not a crash
        return {"ERROR": f"{type(e).__name__}: {e}"}


def surfaces() -> dict:
    """{key: thunk} for every surface at the spread — the 9 MCP forms + the dashboard builds."""
    out = {}
    for m in sorted({m for m, _ in MEMBER_SECTORS}):
        out[f"orient__{m}"] = lambda m=m: F.member_portfolio(m)              # member_portfolio
        out[f"greenfield__{m}"] = lambda m=m: F.unmet_demand(m)              # unmet_demand
    for (m, s) in MEMBER_SECTORS:
        out[f"sector__{m}_{s}"] = lambda m=m, s=s: F.sector_overview(m, s)
        out[f"gaps__{m}_{s}"] = lambda m=m, s=s: F.analyze_gap(m, s)         # sector-level gaps
        out[f"coverage__{m}_{s}"] = lambda m=m, s=s: F.analyze_coverage(m, s)
        for ut, crit in COMPARE:
            out[f"compare__{m}_{s}_{ut}_{crit}"] = (
                lambda m=m, s=s, ut=ut, crit=crit: F.compare(m, unit_type=ut, criterion=crit, sector=s))
        for soc in SOCS.get(s, []):
            out[f"gap__{m}_{s}_{soc}"] = lambda m=m, s=s, soc=soc: F.analyze_gap(m, s, soc=soc)
            out[f"occprofile__{m}_{soc}"] = lambda m=m, soc=soc: F.occupation_profile(m, soc)
            out[f"employers__{m}_{s}_{soc}"] = (
                lambda m=m, s=s, soc=soc: F.analyze_regional_employers(m, s, soc=soc))
            out[f"pathway_occ__{m}_{s}_{soc}"] = (
                lambda m=m, s=s, soc=soc: F.analyze_pathway(m, s, occupation=soc))
        r = scope_for(m, s)                                                 # dashboard side of the seam
        if r:
            spec = resolve(r[0])
            out[f"dash_landscape__{m}_{s}"] = lambda spec=spec: build_landscape(spec)
            # The dashboard's full sector-demand decomposition (attached to the route response, read from
            # the UNRESOLVED spec) — the same birthplace the MCP sector view projects; guards both agree.
            out[f"dash_sectordemand__{m}_{s}"] = lambda raw=r[0]: sector_demand_decomposition(raw)
            out[f"dash_employers__{m}_{s}"] = lambda spec=spec: build_landscape_employers(spec)
            for soc in SOCS.get(s, []):
                out[f"dash_occ__{m}_{s}_{soc}"] = (
                    lambda soc=soc, spec=spec: build_landscape_occupation(soc, spec=spec, include_employers=False))
    return out


def capture() -> dict:
    return {k: _safe(thunk) for k, thunk in surfaces().items()}


def write(snap: dict) -> None:
    SNAP_DIR.mkdir(exist_ok=True)
    for k, v in snap.items():
        (SNAP_DIR / f"{k}.json").write_text(json.dumps(v, indent=1, sort_keys=True) + "\n")


def _blob(v) -> str:
    return json.dumps(v, sort_keys=True)


if __name__ == "__main__":
    a = capture()
    b = capture()                                     # self-consistency: the oracle must be deterministic
    unstable = sorted(k for k in a if _blob(a[k]) != _blob(b[k]))
    errs = sorted(k for k, v in a.items() if isinstance(v, dict) and "ERROR" in v)
    write(a)
    print(f"captured {len(a)} surfaces to {SNAP_DIR.name}/  |  errored={len(errs)}  non-deterministic={len(unstable)}")
    for k in errs:
        print(f"  ERROR      {k}: {a[k]['ERROR']}")
    for k in unstable:
        print(f"  UNSTABLE   {k}")
