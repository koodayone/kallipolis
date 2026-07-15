# Layer 3 / Tier C — Phase 2 handoff (resume here)

Written to preserve the context to finish Phase 2, which we paused mid-thread when the Phase-1 live run
found a real substrate bug (fixed in PR #120). Read `LAYER3-EVAL-PLAN.md` (the full plan) and
`LAYER3-EVAL-PLAN-PROMPT.md` (the charge) alongside this.

## Where we are (shipped + deployed)
- **Phase 0** (PR #118/#119): `checks.py` false-positives fixed (`axis_named` "gap", `no_invented_score`
  polarity, `traceability` SOC/TOP/date/sign). Green.
- **Phase 1** (PR #119): **Article VI** (`constitution.md`, "answer at the right coordinate"),
  `semantic_pathways.py` (first slice S1 two-demand + S3 regional-invariance/grain-nesting; S7 reuses
  `ONBOARDING_PATHWAYS`), `semantic_checks.py` (the `LAWS` manifest, per-transcript classification checks,
  the cross-transcript **metamorphic runner** with a seed-oracle hook), `semantic_judge.md`,
  `docs/domain/generator-algebra.md`. 83 tests green.
- **The bug it found** (PR #120): `supply_demand_gaps(member, sector, soc=X)` for an occupation the member
  doesn't serve shipped the served-sector summary under the occupation's coordinate (smccd read 422 as the
  machinists gap; true = 355). The `regional_invariance` metamorphic probe caught it (smccd 422 ≠ svamp 355),
  invisible to prose I–V. Fixed: gate + route to `occupation_profile`; `test_gap_soc_query_never_bare_summary`.
- **All merged to main (`d4f8092`) and deployed to prod** (VM `kallipolis-api`, `docker compose up -d --build
  backend`); the container serves the new DOCTRINE + gap fix. The **behavioral re-run of #118's DOCTRINE lift
  must run in a FRESH `/conversational-eval` session** (MCP priming binds at session start; the priming-injection
  A/B already predicts 5→0 partials, −34% words).

## What Phase 2 is
Two laws, already **scaffolded in the `LAWS` manifest** (`backend/evals/conversational/semantic_checks.py`,
`status: "phase-2"`) but not yet given probes or check bodies. They are subtler than the Phase-1 laws because
they need richer extraction than a numeric pair comparison.

### Law A — `coordinate_identity` (relation `=`)
**Asserts:** a measure at a coordinate is one value however reached. Machinists' regional openings (~510) is the
same via `occupation_profile(51-4041)`, the `supply_demand_gaps` 51-4041 row, and a `compare(unit_type=occupation,
criterion=openings)` row.
**Differs from `regional_invariance`:** regional-invariance holds the coordinate fixed and varies *who asks*
(smccd vs svamp → grain routing); coordinate-identity holds the coordinate fixed and varies *which tool answers*
(→ tool routing).
**Subtleties to handle when building it:**
1. **Induce two paths.** Design a probe pair whose two questions naturally route to *different* tools but land on
   the *same* coordinate (e.g. "openings for machinists?" → `occupation_profile`; "rank the sector's occupations
   by openings" → `compare`, then read the 51-4041 row). Or catch a within-conversation restatement.
2. **Coordinate-aware figure match.** Confirm both paths reached the *identical* coordinate (same SOC, same region)
   from each call's `args` before asserting equality — the Phase-1 `_figure_by_key` keyword match is not enough.
3. **Must NOT false-fire at the two-demand seam.** `sector_overview` demand (~8,150) and `supply_demand_gaps`
   demand (~1,240) both sound like "the sector's demand" but are *different coordinates* (full-sector vs served) —
   coordinate-identity must recognize that and stay silent, or it collides with S1.
**Load-bearing connection:** it is the conversational lift of `test_compare.py`'s referential-integrity tests
(server-level), AND **the spec for the dashboard⇄MCP unification** — "the MCP number and the dashboard number for
the same coordinate are equal" is coordinate-identity with the dashboard as the second path. Frame it as the
**two-window** invariant (the dashboard the analyst offers via `view_link` is the second window), reusing
`test_substrate.test_dashboard_mcp_corroboration`'s both-paths `capture` oracle. Closing the two-feeder-definition
seam (`SUBSTRATE-QUEUE.md` #1; RN 688.7 vs 688.0) drives its band to 0.

### Law B — `forward_reverse` (relation `⊇` set-membership, NEVER magnitude)
**Asserts:** if program P `PREPARES` occupation O (forward, `program_pathways` with a program arg), then going
reverse from O (`program_pathways` with a soc arg / `occupation_profile` feeder rows), O's feeder set contains P.
**Why membership, not magnitude:** the TOP→CIP→SOC crosswalk is many-to-many and lossy — you can assert the *edge*
is bidirectionally present; you can assert nothing about counts. Encode `relation: subset` in `LAWS` so no one
tightens it into a false numeric equality.
**Subtleties:**
1. **Set relation on named entities, not numbers.** Extract the set of occupations named as "what P prepares for"
   and the set of programs named as "what feeds O", and check the P–O edge is in both — parsing program names / SOCs
   from prose or tool rows, harder than reading a figure.
2. **The analyst legitimately compresses** (names 2 of 8 mapped occupations). So verify only that *every edge the
   analyst asserts forward is corroborated in reverse* — a soft membership check over asserted edges.
3. **Interpretive half.** Article-VI defensibility here = flagging the looseness (`catalog.SAL_LOSSY_CROSSWALK` —
   "graduates compete across all of these, not exclusive to one"). So forward_reverse is part deterministic (edge
   membership) + part judge (was the many-to-many caveat surfaced).

## Concrete build steps (Phase 2)
1. **Probes** (`semantic_pathways.py`): add S2 forward/reverse pair (e.g. Machining program → occupations; machinists
   51-4041 → programs) and a coordinate-identity pair (openings for one SOC via `occupation_profile` vs via `compare`).
   Seed-resident coordinates (smccd/svamp/deanza × adm × served SOCs, e.g. deanza serves 51-4041).
2. **Checks** (`semantic_checks.py`): implement `coordinate_identity` in `run_group` with a coordinate-aware extractor
   (match SOC+region before equality); implement `forward_reverse` as a per-transcript set-membership check over
   named edges. Add the two-demand non-collision guard to coordinate_identity.
3. **Judge** (`semantic_judge.md`): already carries classification + defensibility; add the crosswalk-looseness-flag
   check to defensibility for forward_reverse.
4. **Coverage** (`test_semantic.test_*`): flip the two laws' `status` to phase-2-active; the coverage test then
   *requires* their probes — that is the gate that keeps them honest.
5. **Widen** the covering set to the remaining seams (S4 comparison-class, S5 absence-vs-zero, S6 non-summable) per
   the plan's Phase-2 target (~20 probes, `test_algebra_coverage` green).
6. **Docs** (`docs/domain/generator-algebra.md`): the laws are already in the invariant table; fill their
   probe/check references as they're built (audit-verified).

## Roadmap pull (when to build it)
Don't build Phase 2 reflexively — the natural pull is the **dashboard⇄MCP unification**: `coordinate_identity` becomes
its acceptance test (drive the corroboration band to 0). The **deep-link / panel-addressable URL** roadmap
(`/landscape/foothill/adm?panel=programs.awards`) is the defensibility-at-depth extension — the judge already scores
`view_addresses_coordinate: ok|coarser|absent`; tightening `coarser→ok` at depth is a threshold change, touching
`viewlink.py` + the atlas landscape route.

## How to run
- **Deterministic** (checks + `test_algebra_coverage`): headless, no connector — `pytest evals/conversational/test_semantic.py`.
- **Behavioral** (drive probes, judge): a **fresh** Claude Code session with the Kallipolis connector (MCP binds at
  start), following `backend/evals/conversational/run.md`'s Tier-C section pattern. The seed graph must be up
  (`eval-neo4j` on `bolt://localhost:7691`).
