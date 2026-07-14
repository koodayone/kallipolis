# MCP Epistemic Self-Sufficiency — plan-mode prompt

Governing brief for a plan-mode session. Turn this into an architecturally excellent,
sequenced, behavior-preserving implementation plan. Companion to the prior
`Provenance Authority Decomposition` memo and `research/architecture/EVALS-APPROACH.md`.

## Objective

Make the Kallipolis MCP server **epistemically self-sufficient**: every fact an agent needs
to *read, cite, and navigate* a response correctly must arrive through a primitive whose
delivery guarantee matches its necessity — never through advisory server `instructions`,
opt-in prompts, or an unstated system decision. Two live failures motivate this and must both
be fixed:

- **Navigation is dark.** A valid dashboard `view_link` is generated on every applicable
  response, but the "offer it" nudge lives only in `instructions`/the `start-here` prompt, so
  the practitioner never gets the link. The "two-windows" experience silently doesn't work.
- **Provenance is ambiguous.** `projected_supply`'s authority collapses three distinct
  authorities (construct = COE, computation = Kallipolis, data = DataMart) into a scalar
  `"datamart"`, while the licensing prose *independently* restates "COE PROJECTED" — a
  decomposition an uninitiated agent reads as a contradiction (observed). A less-informed
  agent silently picks one authority and propagates it, wrong in either direction.

## Governing principle

**Place each piece of context in the primitive whose delivery guarantee matches its
necessity; the tool schema and the tool response are the only surfaces strong enough to carry
what the agent must never miss — nothing the agent needs may live out-of-band.** Delivery
guarantees, strongest to weakest: tool descriptions + tool responses (always injected/read) >
prompts (user-opt-in) > server `instructions` (advisory, client-dependent). The payload/schema
must be complete for a **context-free** agent — one that never read `instructions`, never
invoked `start-here`, and does not know the COE-replacement decision. Corollary (from the
provenance memo): **one writer per fact** — the structured schema is the single source of a
fact's lineage; prose points at it, never re-copies it.

## Evidence to read first

- `mcp_server/worldview.py` — states "tool descriptions are the primary priming channel," an
  intent the code violates; it fuses three jobs (orientation · voice · epistemic contract).
- `mcp_server/server.py` — `instructions=WORLDVIEW`, `_form_description` (already *composes*
  descriptions from `catalog.FORMS` — the pattern to extend), the single `@mcp.prompt`.
- `mcp_server/provenance.py` + `partnerships/lens.py` `FIELD_AUTHORITY` — the authority
  substrate is **shared** with the dashboard lens; changing its shape ripples to both.
- `mcp_server/catalog.py` `FORMS` — per-form guardrails; several are **stale** post-All-Awards
  (e.g. "not actual DataMart awards" — supply *is* DataMart completions now).
- The `Provenance Authority Decomposition` memo (its principle + three changes; two edits
  applied here: uniform authority, gap-as-composition).

## Workstream 1 — Doctrine: canonicalize, then decompose its agentic rendering

- **Canonicalize the doctrine.** Extract the *epistemic contract* (the reading-rules doctrine
  — carry source/granularity/vintage; projected-vs-actual; the gap is regional; wages are
  statewide; the crosswalk is many-to-many; **absent ≠ zero**; every claim traces to a figure)
  from where it is buried inside `worldview.py` into a **canonical, surface-agnostic
  statement**: `docs/domain/epistemic-contract.md`, under the docs-audit contract. This is
  Kallipolis's north star — the doctrine every surface (MCP now; reports, dashboard later)
  must honor. One writer.
- **Render it for the agentic surface, composed not copied.** Keep **one condensed per-call
  doctrine constant** (~6–8 lines: the *universal* rules only — voice, absent≠zero,
  trace-to-figures, and the navigation nudge). Have `_form_description` **prepend** it to every
  tool description, exactly as it already composes the per-form question/guardrail. Result: the
  reading contract reaches the model on *every* call, reliably, with **one writer**. The
  *field-specific* misreading-blockers (projected-vs-actual, regional-gap, wages-statewide)
  stay in the per-form guardrails — do not duplicate them into the shared constant.
- **Route by delivery need.** The worldview's **orientation** (WHAT YOU CAN DO, HOW TO BEGIN)
  is session-start onboarding → the `start-here` prompt. Server `instructions` may keep a
  preamble but must **load-bear nothing** — the acceptance test is a context-free agent that
  never receives it.
- **Accept the repetition.** MCP has no shared-tool-preamble primitive; the condensed doctrine
  will repeat across tool descriptions. This is bounded (injected once per conversation),
  reinforcing, and the price of the only reliable channel — condense, don't avoid.
- **Do NOT build a machine-consumable "principles object" all surfaces import.** The doctrine
  is shared as *canon* (a doc) and rendered per-surface (prose for the model, code for reports,
  UI for the dashboard) — enforcement mechanisms differ; a single runtime artifact is a false
  coupling. The only thing shared *literally* is the factual substrate (`FIELD_AUTHORITY`,
  vintages), which already is.

## Workstream 2 — Provenance: decompose authority in the payload (uniform, one writer)

- **Uniform structured authority (decided).** For fields whose construct/computation/data
  authorities diverge — in practice `projected_supply` and its `occupation_profile` equivalent
  — `field_authority` carries the three facets. Use a **uniform, unbranchable** representation:
  *always* structured, single-authority fields collapsing to equal facets (or an explicit
  "direct" marker). A consuming agent must never guess whether an authority is a string or an
  object. Because this substrate is shared with the dashboard lens, resolve the representation
  so **both consumers read one shape**; migrate the lens accordingly.
- **`gap` is compositional, not a triple (decided).** It is already `"derived"`. Model its
  provenance as `derived_from` its operands (`annual_openings` + `projected_supply`), so an
  agent traces it to each operand's authority — its "data" facet is two sources at once, which
  a flat construct/computation/data triple would misrepresent.
- **One writer for the licensing.** Rewrite the supply guardrail/licensing to *name the
  construct and point at the structured authority*, never restating a source: e.g. "projected
  completions per COE methodology (3-yr average), computed by Kallipolis from current DataMart
  vintages — do not read as a single-year raw award; see `latest_year_supply`." This also
  **corrects the stale post-All-Awards guardrails** ("not actual DataMart awards").

## Workstream 3 — Navigation: surface the `view_link` in-band

- The "offer the dashboard link" affordance must ride the always-delivered surface: a concise
  instruction in the shared doctrine constant (Workstream 1) and/or the `view_link` made
  prominent in the response's **text content**, not only `structuredContent`. A context-free
  agent must surface the URL from tool descriptions + response alone.

## Workstream 4 — Evals: deterministic gate + the first semantic harness

- **Deterministic invariants (CI-gating).** (a) For multi-authority derived fields the
  structured authority is present and well-formed; (b) no licensing string restates a source id
  already in `field_authority` (the mechanical "one writer" contract — a cheap substring check);
  (c) every non-`unmet_demand` form returns `view_link.status == "ok"`. These are the
  deterministic *pre-gate* the codebase's philosophy requires.
- **Semantic harness (periodic, non-blocking) — the codebase's first LLM-as-judge.** A
  context-free agent asked "explain where the supply figure comes from" must produce the
  construct/computation/data decomposition (fail on "from COE" or "DataMart awards"). Run it in
  a harness behind the deterministic gate — it measures the outcome; it does not flake CI.
  Introduce it deliberately, per `EVALS-APPROACH.md` (LLM-judge only behind a deterministic
  pre-gate).

## Explicit non-goals (scope discipline)

- **No resources.** A "retrievable methodology substrate" is client-controlled (the same
  variance biting us) and speculative; the structured payload + one-writer licensing must make
  provenance self-sufficient without a retrieval round-trip.
- **No `get_methodology`/`explain_provenance` meta-tool.** If the decomposition is in the
  payload, the agent already has it; a meta-tool bloats the domain tool list and invites noisy
  self-querying. Do not expand the tool count.
- **No rendered/user-facing prose change** beyond the guardrail rewrite.
- **No prose↔authority CI cross-check** (the memo's deferred item) — the deterministic
  "no double-write" check covers the common case; the full cross-check earns its cost only if
  drift recurs.
- **No shared runtime "principles object"** (Workstream 1).

## Acceptance

A **context-free agent**, given only a live response and the tool schema — never reading
`instructions`, never invoking `start-here`, ignorant of the COE-replacement decision —
1. surfaces the dashboard `view_link`,
2. explains supply's construct/computation/data decomposition correctly, and
3. never flags a false authority contradiction.
Plus: the deterministic invariants gate CI green; the semantic harness passes; characterization
goldens for existing computations remain byte-identical; the shared `FIELD_AUTHORITY` shape
change is coherent for **both** MCP and dashboard consumers; `docs-audit` passes with the new
doctrine doc.

## Forward references (named, not silent)

- **Reports and dashboard honor the same doctrine.** Out of scope here, but this plan names
  `epistemic-contract.md` as the shared canon so the report generator's suppression→unknown
  enforcement and the dashboard's provenance labels can later be re-derived from it, rather than
  drifting as independent copies. A separate thread.
- A shared-tool-preamble MCP primitive, if it ever lands, would relocate the repeated doctrine
  constant — do not design around a primitive that doesn't exist.
