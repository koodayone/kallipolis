# Substrate queue — known Tier-A items, guarded but not yet closed

Findings the substrate invariants (`test_substrate.py`, `mcp_server/test_compare.py`) surfaced but
that are scoped as their own efforts rather than patched inline. Each is **guarded** — the invariant
asserts agreement within a tolerance, so a gross regression fails CI — until it's closed. Closing an
item means driving its tolerance to zero.

## 1. Unify occupation feeder resolution (dashboard ⇄ MCP)
*Guarded by `test_dashboard_mcp_corroboration` · band = 1.0 completion.*

**Seam.** The MCP resolves an occupation's feeder programs via the is_vocational TOP→SOC crosswalk
(`quantities.feeders`); the dashboard builder uses `LandscapeSpec.in_scope`. Where they disagree on a
marginal program, supply — and therefore the gap — differ. Observed: RN (`29-1141`) at `baccc`/health —
the crosswalk counts TOP `123000` (generic Nursing) as an RN feeder; `in_scope` does not; a 0.7/yr
supply difference (688.7 MCP vs 688.0 dashboard). This is the "two CTE/feeder definitions coexist"
duplication, not rounding.

**Decision needed (correctness, not cosmetics).** Which rule is authoritative — *does generic Nursing
prepare RNs?* Settle it on the crosswalk data, applied across **all** occupations, not just this one.

**Fix shape.** One shared feeder-resolution rule beneath both surfaces (referential integrity by
construction). Then regenerate the characterization goldens and tighten `_CORROBORATION_BAND` toward 0.

**Why it damages trust if left.** The whole two-window pitch is "verify with your own eyes"; a dashboard
that shows a different number than the analyst quietly erodes exactly that. Small here (0.7), but the
rule can diverge more for other occupations.
