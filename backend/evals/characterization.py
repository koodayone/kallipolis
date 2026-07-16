"""Characterization goldens — freeze the computed quantities at the golden coordinates, from
BOTH code paths, so the dashboard⇄MCP corroboration is legible and any drift is a reviewable diff.

For each (member, sector, soc) we capture the same figures two ways:
  • builder  — the dashboard/report path (`build_landscape_occupation`): consortium_supply and
               gap = openings − consortium_supply.
  • canonical — the MCP resolver path (`mcp_server.canonical` → `partnerships.quantities`): supply
               (DataMart graph, COE's 3-yr averaging method), feeders, active_feeders, the roster.

Both paths now resolve supply through the SAME graph resolver (`quantities.supply_fn_graph`, shipped
as S3 — the builder no longer reads the COE CSV), so at the golden coordinates they agree by
construction (`test_substrate.test_dashboard_mcp_corroboration`). The one residual is feeder-set
granularity: `quantities.feeders` counts a general TOP as a feeder where the builder's
`LandscapeSpec.in_scope` counts only the specific child (RN 29-1141: TOP 123000 vs 123010 → 688.7 vs
688.0). That crosswalk-granularity call is the open substrate item (`SUBSTRATE-QUEUE.md #1`); closing
it drives `_CORROBORATION_BAND` to 0.

Refresh after an INTENDED change (regenerates goldens/*.json against the reachable graph — the
seed in CI, or a socat-forwarded compose Neo4j locally):

    NEO4J_URI=bolt://localhost:7687 NEO4J_USERNAME=neo4j NEO4J_PASSWORD=… \\
        python3.11 -m evals.characterization
"""
import json
from pathlib import Path

from mcp_server import canonical as CAN
from mcp_server.scope import scope_for
from partnerships.resolve import resolve
from partnerships.landscape_programs import relevant_tops, build_landscape_occupation

# The golden set — the coordinates the referential-integrity invariants already pin, plus
# siblings across members. soc 51-4041 (Machinists, an adm feeder) and 29-1141 (RN, health).
GOLDEN_COORDS = [
    ("deanza", "adm", "51-4041"),   # test_cross_tool_referential_integrity's coordinate
    ("svamp", "adm", "51-4041"),
    ("smccd", "adm", "51-4041"),
    ("ccsf", "adm", "51-4041"),
    ("baccc", "health", "29-1141"), # test_offering_referential_integrity's coordinate
]
GOLDENS_DIR = Path(__file__).parent / "goldens"

# The comparison engine's ranked output — (member, sector, unit_type, criterion). A behavioral
# snapshot so ANY change to a ranking, a criterion's value, or the registry trips the golden diff.
COMPARE_GOLDEN_COORDS = [
    ("svamp", "adm", "program", "addressable_gap"),
    ("smccd", "adm", "program", "supply_share"),
]


def _roster_summary(colleges, top6: str) -> dict:
    """The canonical per-college roster, reduced to the counts + named set that diverged in
    #103 (occupation_profile counted Program nodes; the builders counted 09 courses)."""
    cells = CAN.college_roster(colleges, top6)
    return {
        "n_with_program": sum(1 for c in cells if c.has_program),
        "n_active": sum(1 for c in cells if c.awards > 0),
        "n_covered": sum(1 for c in cells if c.coverage == "covered"),
        "colleges_with_program": sorted(c.college for c in cells if c.has_program),
    }


def capture(member: str, sector: str, soc: str) -> dict:
    """Both paths' quantities at one coordinate. Resolves the spec exactly as the tools do
    (`resolve(scope_for(...))`), so the captured figures are the ones the surfaces serve."""
    r = scope_for(member, sector)
    if not r:
        return {"member": member, "sector": sector, "soc": soc, "in_scope": False}
    spec = resolve(r[0])
    colleges = sorted(spec.colleges)
    socs = sorted(spec.socs)

    # canonical (MCP) — fresh DataMart graph, COE's 3-yr method
    feeders = sorted(CAN.feeders(colleges, soc))
    canon = {
        "supply_3yr": CAN.supply(colleges, soc),
        "supply_1yr": CAN.supply(colleges, soc, years=CAN.recent_award_years(1)),
        "sector_supply_over_socs": CAN.supply_over_socs(colleges, socs),
        "feeders": feeders,
        "active_feeders": sorted(CAN.active_feeders(colleges, soc)),
        "rosters": {t: _roster_summary(colleges, t) for t in feeders},
    }

    # builder (dashboard/report) — stale COE CSV path
    universe = relevant_tops(spec)
    feeding = sorted(t for t, s in universe.items() if soc in s)
    rep = build_landscape_occupation(soc, spec=spec, include_employers=False)
    builder = {
        "consortium_supply": rep.consortium_supply,
        "gap": rep.gap,
        "annual_openings": rep.annual_openings,
        "feeding_tops": feeding,
    }

    return {
        "member": member, "sector": sector, "soc": soc, "in_scope": True,
        "colleges_n": len(colleges), "socs_n": len(socs),
        "canonical": canon, "builder": builder,
    }


def golden_path(member: str, sector: str, soc: str) -> Path:
    return GOLDENS_DIR / f"{member}_{sector}_{soc}.json"


def capture_compare(member: str, sector: str, unit_type: str, criterion: str) -> dict:
    """The comparison engine's ranked output, reduced to {ranked labels, {label: {criterion: value}}}
    — a behavioral snapshot that any ranking/criterion/registry change trips."""
    from mcp_server import forms as F
    env = F.compare(member, unit_type=unit_type, criterion=criterion, sector=sector)
    base = {"member": member, "sector": sector, "unit_type": unit_type, "criterion": criterion}
    if env.licensing.gates:
        return {**base, "gated": True}
    return {
        **base, "gated": False,
        "ranked": [r.label for r in env.data.rows],
        "values": {r.label: {k: qv.value for k, qv in r.values.items()} for r in env.data.rows},
    }


def compare_golden_path(member: str, sector: str, unit_type: str, criterion: str) -> Path:
    return GOLDENS_DIR / f"compare_{member}_{sector}_{unit_type}_{criterion}.json"


def main():
    GOLDENS_DIR.mkdir(exist_ok=True)
    for coord in GOLDEN_COORDS:
        data = capture(*coord)
        golden_path(*coord).write_text(json.dumps(data, indent=1, sort_keys=True) + "\n")
        c, b = data.get("canonical", {}), data.get("builder", {})
        print(f"  {'_'.join(coord):26} canon.supply={c.get('supply_3yr')!s:>7}  "
              f"builder.supply={b.get('consortium_supply')!s:>7}  builder.gap={b.get('gap')}")
    for coord in COMPARE_GOLDEN_COORDS:
        data = capture_compare(*coord)
        compare_golden_path(*coord).write_text(json.dumps(data, indent=1, sort_keys=True) + "\n")
        print(f"  compare {'_'.join(coord):34} ranked={data.get('ranked', 'GATED')}")


if __name__ == "__main__":
    main()
