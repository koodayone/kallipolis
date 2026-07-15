# Running the conversational eval (fresh session, subscription-only)

## Faithfulness first
Run this from a **fresh Claude Code session started after the DOCTRINE deploy.** MCP tools bind at
conversation start, so only a fresh session primes the model-under-test with the *current* DOCTRINE;
a stale session tests the old priming.

## The loop — all on the subscription, no API key
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

## v1 caveats — shake these out on the first run
- The model-under-test reports its own tool calls/figures; **step 1's capture faithfulness is the
  main thing to validate.** If it's lossy, tighten the return schema.
- `checks.py` traceability is a rounding-tolerant heuristic — expect to tune its false-positive rate.
- Start with these 12 pathways; widen the matrix once the plumbing holds.

## Later: the CI gate
This form runs on-demand in Claude Code. To gate PRs automatically (headless, no Claude Code), port
step 1 to a small Anthropic-API harness in `backend/evals/` that drives the same `pathways.py` with
the current tool definitions — reusing `checks.py` and `judge.md` unchanged.
