---
name: conversational-eval
description: >
  Use this skill when the user asks to "run the conversational eval", "evaluate the analyst",
  "grade the MCP conversations", "run the pathway eval", or wants to score the Kallipolis MCP
  analyst's conversational behavior against the constitution and iterate on it. It runs the
  subscription-only conversational evaluation defined in backend/evals/conversational/: the Tier A
  substrate gate, then the pathway matrix driven by subagents against the live MCP tools, the
  deterministic pre-gate, the layer-aware judge, and a per-principle scorecard that is the iteration
  queue. MUST be invoked from a FRESH session (MCP tools + DOCTRINE bind at conversation start).
---

# Run the conversational eval

Evaluate the Kallipolis MCP analyst's conversational behavior against the constitution and produce
the iteration queue. Everything runs on the Claude Code **subscription via subagents — no API key**.
The spec and data live in `backend/evals/conversational/`; read `run.md`, `constitution.md`,
`judge.md`, and `pathways.py` there before starting. All commands below run from the repo root.

## Preconditions
- **Fresh session, latest `main`.** MCP tools and their DOCTRINE bind at session start, so only a
  session opened after the latest deploy tests the *current* priming. If a stale binding is
  unavoidable, say so in the report — you would be grading the old priming, which invalidates the
  DOCTRINE-driven results.
- The live Kallipolis connector (`api.kallipolis.us/mcp`) is connected (subagents reach it).
- The seed graph is up: the `eval-neo4j` docker container on `bolt://localhost:7691` (its password is
  a local dev credential — override via `NEO4J_PASSWORD`; the local default is `evalpass123`).

## Step 1 — Tier A gates everything (the substrate must be sound first)
A failure here is a computation / envelope / data bug — **stop and fix it, never grade prose on a
broken substrate** (you would tune the prompt against a wrong number). From the repo root:
```
cd backend
PYTHONPATH="$(pwd)" NEO4J_URI="bolt://localhost:7691" NEO4J_USERNAME="neo4j" \
  NEO4J_PASSWORD="${NEO4J_PASSWORD:-evalpass123}" \
  .venv/bin/python -m pytest evals/conversational/test_substrate.py \
  mcp_server/test_compare.py -k "corroboration or referential" -q
```
Known-and-guarded seams are logged in `evals/conversational/SUBSTRATE-QUEUE.md` (they pass within
their band). Proceed only on a green Tier A.

## Step 2 — Tier B: the pathway loop (subagents, in parallel)
For each pathway in `backend/evals/conversational/pathways.py`, spawn a subagent that has the live
Kallipolis MCP tools. It plays a workforce-development practitioner at the pathway's member/sector —
opens with `seed`, then sends each `follow_up` — and answers as the analyst using the tools. It
returns a structured transcript in the shape `checks.py` documents (each analyst turn's prose + the
tool calls it made + the key figures it read + whether a `sorted_by`/`view_link` was present),
written to a scratch dir, e.g. `transcripts/<pathway_id>.json`.

## Step 3 — grade
Deterministic pre-gate (from `backend/`): `.venv/bin/python evals/conversational/checks.py transcripts/*.json`.
Then spawn one judge subagent per transcript with `judge.md` + `constitution.md` + the transcript +
its pre-gate result; collect the JSON verdicts.

## Step 4 — report the scorecard (the iteration queue)
Per-principle pass / partial / fail (I ground · II plain · III inform-don't-decide · IV teach ·
V trust) across the pathways, the four tension leans, and the failing transcripts with
`worst_failure` + `fix_layer`. **`fix_layer = doctrine` → the priming; anything else
(data / computation / envelope / guardrail) → the substrate.** DOCTRINE fixes land in
`backend/mcp_server/worldview.py`; substrate fixes go back into the stack.

Expect the first run to shake out the transcript-capture faithfulness (Step 2) as much as grade the
model — the v1 caveat. Start with the 12 pathways; widen once the plumbing holds.
