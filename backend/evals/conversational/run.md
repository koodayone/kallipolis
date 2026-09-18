# Running the conversational eval (fresh session, subscription-only)

## Faithfulness first
Run this from a **fresh Claude Code session started after the DOCTRINE deploy.** MCP tools bind at
conversation start, so only a fresh session primes the model-under-test with the *current* DOCTRINE;
a stale session tests the old priming.

## Tier A gates this — the substrate must be sound first
Run the substrate property tests BEFORE any conversation:
```
pytest backend/evals/conversational/test_substrate.py \
       backend/mcp_server/test_compare.py -k "referential or corroboration"
```
They assert the numbers are correct, consistent across tools, and consistent with the dashboard (the
two-window invariant). **If any fail, stop and fix the computation / envelope / data — never grade
prose on a broken substrate** (you'd tune the prompt against a wrong number). The loop below is
meaningful only on a green Tier A.

## Tier B — the prose loop (constitution I–V), all on the subscription, no API key
For each pathway in `pathways.py`:

1. **Drive + capture (model-under-test).** Spawn a subagent with the Kallipolis MCP tools connected.
   Give it the pathway's `seed`, then each `follow_up` in turn, speaking as a workforce-development
   practitioner (member/sector from the pathway). It answers as the analyst, calling the tools. Have
   it return a structured transcript in the shape `checks.py` documents — each analyst turn's prose +
   the tool calls it made + the key figures it read + whether a `sorted_by` / `view_link` was present
   — and write it to `transcripts/<pathway_id>.json`. Run the pathways in parallel.

2. **Deterministic pre-gate.** `python backend/evals/conversational/checks.py transcripts/*.json`.

3. **Judge (interpretive).** Spawn one judge subagent per transcript with `judge.md` + `constitution.md`
   + the transcript + its pre-gate result. Collect the JSON verdicts.

4. **Scorecard.** Aggregate: per-principle pass/partial/fail across the matrix, the tension lean, and
   the failing transcripts with `worst_failure` + `fix_points_at`. **That list is the iteration
   queue:** fix the DOCTRINE / form-guardrail line it points at (`backend/mcp_server/worldview.py`,
   `catalog.py`), redeploy, re-run the same pathways, confirm the lift. Freeze passing pathways as
   regression fixtures.

## Tier C — the semantic loop (Article VI classification + defensibility)
Tier B grades *how* the analyst speaks (I–V, `judge.md`); Tier C grades *whether the question routed
to the right coordinate* — the generator-algebra walk (`docs/domain/generator-algebra.md`), scored on
**Article VI (classification)** and the **defensibility** clause of **V** by a second judge
(`semantic_judge.md`). Two judges, two pathway sets, one `constitution.md` (all six principles). Run
Tier C after Tier B on the **same** fresh session; the offline coverage gate (`pytest
backend/evals/conversational/test_semantic.py`) must be green first — it is the headless, connector-free
check that every `LAWS` entry has a probe and every metamorphic group is a complete pair.

The probes are `semantic_pathways.SEMANTIC_PATHWAYS` (+ `pathways.ONBOARDING_PATHWAYS` for S7, already
green). A probe's `kind` sets how it is driven and graded:

1. **Drive + capture (model-under-test).** As Tier B — spawn a practitioner subagent per probe, feed the
   `seed` then each `follow_up`, capture the transcript in the `checks.py` shape. Tier C needs each call's
   **`args`** (the coordinate: `member`, `sector`, `soc`/`occupation`, `program`/`top6`) and **`figures`**
   captured faithfully — the classification checks read call-shape, not prose. Two extra rules:
   - **Metamorphic groups** (`kind: "metamorphic"`, paired by `metamorphic_group` + `role` A/B): drive
     BOTH roles as INDEPENDENT conversations — the invariant only bites across the matched pair. Run each
     group **≥3×**: routing is non-deterministic, so a single pass can mislead (a real seam was caught on a
     pair that disagreed only intermittently).
   - **Onboarding** (S7): the harness must NOT reveal the member in the brief — it is withheld and surfaces
     across turns (`reveal`); the pass condition is establish-before-analyze, graded by `establish_order` +
     the judge's establishment read.

2. **Deterministic pre-gate** (`semantic_checks.py`, run BEFORE the judge):
   - per-transcript: `python backend/evals/conversational/semantic_checks.py transcripts/<id>.json`
     (`golden_traversal`, `establish_order`, `coordinate_named`, and the seam checks the probe selects —
     `surfaced_both_demands`, `forward_reverse_membership`).
   - metamorphic: for each COMPLETE group, `semantic_checks.run_group(group_id, invariant, {"A": txA,
     "B": txB})` — the cross-transcript relation (`=`, `≤`). It is GUARDED on self-reported figures: a
     `pass: False` on real figures is a **mis-scoped number** (the misroute this tier exists to catch — name
     it in the scorecard); a `pass: None` (a figure was not captured) is a capture gap, NOT a fail.
     `coordinate_identity`'s group is the **two-window** invariant — the same coordinate reached two ways;
     its CI hard-gate swaps the self-report for the `evals.characterization.capture` both-paths oracle
     (`test_substrate.test_dashboard_mcp_corroboration`), with the dashboard as the second window.

3. **Judge (interpretive).** Spawn one `semantic_judge.md` subagent per transcript with `constitution.md`
   + `docs/domain/generator-algebra.md` + the transcript + its pre-gate result (per-transcript results AND
   the group's metamorphic verdict). It grades **Article VI + defensibility only** — it does NOT
   re-litigate the deterministic checks, nor the prose I–V (`judge.md` owns those). For `forward_reverse`
   it also scores whether the many-to-many crosswalk looseness was flagged (`catalog.SAL_LOSSY_CROSSWALK`).

4. **Scorecard by seam.** Aggregate classification + defensibility per **seam** (`two_demand`,
   `grain_transitions`, `forward_reverse`, `coordinate_identity`, establish), each metamorphic group's
   verdict, and the failing probes' `worst_failure` + `fix_points_at`. A classification miss's `fix_layer`
   is **`routing-hint`** (`server._ROUTING`) or **`form-guardrail`** (`catalog.FORMS`) — the converged
   DOCTRINE is not re-tuned for a misroute. That list is Tier C's iteration queue; freeze passing probes.

**A full run is A → B → C.** Tier A (`test_substrate.py` + `test_compare.py`) proves the substrate; Tier B
grades the prose; Tier C grades the walk. All three share the one `constitution.md`, and a Tier-C
metamorphic FAIL on real figures is a substrate/routing bug surfaced conversationally, not a prose fix.

## v1 caveats — shake these out on the first run
- The model-under-test reports its own tool calls/figures; **step 1's capture faithfulness is the
  main thing to validate.** If it's lossy, tighten the return schema.
- `checks.py` traceability is a rounding-tolerant heuristic — expect to tune its false-positive rate.
- Start with these 12 pathways; widen the matrix once the plumbing holds.

## Later: the CI gate
This form runs on-demand in Claude Code. Part of Tier C already gates PRs headless today:
`test_semantic.py` runs the `LAWS`-manifest/coverage checks and the check functions with no connector,
so a probe or law that loses its pair breaks the build. To gate the *behavioral* run automatically
(headless, no Claude Code), port the drive+capture step to a small Anthropic-API harness in
`backend/evals/` that drives the same `pathways.py` + `semantic_pathways.py` with the current tool
definitions — reusing `checks.py`/`judge.md` (Tier B) and `semantic_checks.py`/`semantic_judge.md`
(Tier C) unchanged, and swapping each metamorphic group's self-report for the
`evals.characterization.capture` figure oracle so the figure relations hard-gate.
