# Engine unification — checkpoint & deploy notes

Status: **complete.** `claude/coordinate-kernel`, ready to merge to `main`. Backend suite 304 green, docs audit
12/12. This is the sign-off summary for the live-surface changes; the engineering detail is in
`UNIFIED-ENGINE-PLAN.md`.

## What changes on the live surfaces (for sign-off)

1. **The MCP tool surface: 11 task-shaped tools → 6 verbs** (`orient`, `navigate`, `crosswalk`, `compare`,
   `sweep`, `list_institutions`). An agent/user reasons through the same coordinate with fewer, cleaner tools.
   No analytical answer is lost — the verbs are projections of the same engine.

2. **Every rule-bearing dashboard/analysis now counts a program as *active* if it has recent graduates OR
   current enrollment** (was: recent graduates only). Effects a user sees:
   - Programs that enroll students but haven't graduated a cohort yet now **appear** (they were hidden).
     Across the live instances this is a handful of rows each — real programs, not noise.
   - **Supply figures move only *up*, and only slightly** — a program's completions over the last 3 years now
     count consistently (before, an off-year could drop them). No enrollment ever enters a supply number.
   - Members now compute the **same regional figure for the same occupation** where they used to disagree
     (e.g. regional supply for Electrical Techs was 603/433/469 across three members; now uniformly 640.7).

3. **SVAMP specifically** — the dashboard **drops 13 empty program rows**: advanced-manufacturing program
   types no SVAMP college actually runs (0 graduates *and* 0 enrolled students — Welding, Marine Tech, …).
   **Every number is unchanged** — demand 2,700, supply, gap, employers, the 12 occupations. It is a strictly
   cleaner view. Coverage now distinguishes "graduating" from "enrolled, not yet graduating." *→ needs the
   SVAMP director's OK before deploy.*

4. **The MCP sector view** now decomposes demand into full-field / in-a-real-market / you-serve (additive —
   more context, nothing removed).

## Under the hood (no user-facing effect)

One engine (`select` + `aggregate`), zero special-cases, coherence structural (proven by the 640.7
convergence), a smaller system (the `predicate_version` stamp machinery deleted — every figure emits less),
and the ontology materialized into the graph as an inert foundation for the next thread.

## Deploy notes

- **Code-only for correctness.** The backend + MCP server read existing demand/awards/enrollment data; the
  active-gate + SVAMP changes need **no graph reload**.
- **The graph ontology (3a) is inert** — nothing reads it yet — so its nodes can land at the next scheduled
  reload; not on the critical path.
- Standard prod care applies (verify VM HEAD after deploy; the known repo-ownership / no-`| tail` gotchas).

## Explicitly deferred (the next thread, not this merge)

The **traversal capability** — an agent composing a WHAT as a graph walk, resolved by the same disciplined
engine — opens as its own thread. Its **step 1 is the read-swap** (teach `select` to resolve scope by
traversing `COVERS`/`SCOPES`), which is where the runtime's new dependency on the loaded ontology belongs.
Also deferred: enrichment (reasons on edges, the full pipeline connected), the self-serve authoring UI (N≥2),
freezing the MEASURE family, multi-region WHO.
