# MCP Comparison Layer — plan-mode prompt

Governing brief for a plan-mode session. Turn this into an architecturally excellent,
sequenced, behavior-preserving implementation plan. Companion to
`docs/architecture/supply-demand-construct.md` (the construct the measures derive from),
`docs/architecture/mcp-server.md` (the conversational layer this extends), and
`docs/domain/epistemic-contract.md` (the reading doctrine the ranking rules extend).

## Objective

Generalize comparison from a single unit type into a **unit-parametric comparison algebra**
over the ontology's primitives, so that a practitioner's natural-language ranking questions —
*"which occupations are attractive," "which of my programs should I grow," "how does my
college compare to its peers"* — resolve into **defensible ranked views**: every ranking is
by a real, named, traceable axis, and no fuzzy predicate is ever silently turned into a
hidden ranking.

The engine for this already exists and was built for exactly this extension. `compare` is a
registry-driven engine — `{unit_type → {criterion → Criterion}}` + a generic `compare()` that
resolves a peer set, computes every admissible criterion per unit (the full profile), and
ranks by the chosen one. Today it registers **only `unit_type="program"`** (a member's
programs, 10 criteria). Occupations are ranked only by *fixed* axes buried inside individual
forms (`supply_demand_gaps` by gap size; `unmet_demand` by opportunity); colleges and members
cannot be compared at all. So the intellectual work here is **not new machinery** — it is the
measure algebra, the peer-set model, and the predicate-resolution behavior that let the
existing engine span the whole spine. A plan that invents a parallel system, or a
form-per-comparison, has failed.

## Governing principles (settled — enforce, do not re-litigate)

1. **Unit-parametric algebra, one engine.** New `unit_type` registry entries in `compare.py`,
   each inheriting the parametrized eval battery — never a parallel engine, never a
   form-per-comparison. "Adding a comparison is a registry entry (data), not code" is the
   existing design commitment; honor it.
2. **Named-axis under no-composite.** Every sort key is a quantity that already exists with a
   name, unit, source, and vintage. Three legitimate forms: a plain count/sum, a ratio taken
   at the unit's own grain, or a directly-measured outcome. **Forbidden is the composite** — a
   number manufactured by choosing weights to blend other measures, or by aggregating a finer
   grain upward with weights. The operational test the design must apply to every proposed
   axis: *does producing this number require choosing a weight that isn't itself a measured
   fact?* If yes, it is a composite — a value judgment wearing the costume of a measurement —
   and `_register` must raise on it (it already does for `composite=True`).
3. **Never reify a predicate into a hidden ranking.** The value judgment of what a fuzzy word
   ("attractive," "strategic") means belongs to the practitioner, surfaced by the model —
   never frozen, invisibly, in the server. Behavior: **rank-by-default-and-disclose, scaled to
   how defensible the default is.** A canonical-reading predicate (high-paying→wage,
   underserved→gap, in-demand→openings) ranks by its named axis and *discloses* it. A
   compound-conventional predicate ranks by a primary named axis, flagged as *one* reading,
   with the full profile visible. **When no defensible default exists, present the axes — never
   pick arbitrarily.** That degenerate rule is load-bearing: it is the seam where
   default-and-disclose would otherwise decay into a hidden ranking. This is a doctrine +
   tool-description layer on top of the engine's existing full-profile return — not new engine
   logic.
4. **Comparability = analogous units only.** A comparison is well-formed only over units of the
   same grain in a well-defined, stated peer set. Cross-scope comparison (a college against the
   region's colleges) uses **share / normalization** (the shipped `supply_share`), never raw
   counts a size difference would distort, and is framed as **positioning / coverage — never
   competition.** In a collaborative community-college system, "who else serves this" is
   coverage, not rivalry.
5. **Shipped vocabulary only.** `supply_share` and `coverage`. There is no "market share," no
   "competitive," and no distinct "concentration" operator anywhere in the code — do not
   introduce them. "How many colleges provide this" is a plainly-named facet of the roster, not
   a market-structure metric.

## Evidence to read first

- `backend/mcp_server/compare.py` — the engine. `Criterion` (carries `composite: bool`),
  `REGISTRY`, `PEER_SET`, `CompareContext` (shared inputs resolved once), `compare()`, and
  `_register` (raises on `composite=True`). The `_PROGRAM` entry is the template a new unit
  type imitates. Note the "full profile per unit, sorted by the chosen criterion" return — the
  basis of principle 3's default-and-disclose.
- `backend/mcp_server/test_compare.py` — the eval battery **parametrized over the registry**
  (independent-oracle correctness, cross-tool referential integrity, law/bounds,
  authority-trace, ranking monotonicity, the structural no-composite gate). A new unit type
  inherits all of it automatically. **This is the trust deliverable** — a criterion cannot ship
  until it passes; the plan must keep it the gate.
- `backend/mcp_server/forms.py` — the fixed-axis rankings that already exist: `analyze_gap`
  (occupations by gap), `unmet_demand` (occupations by opportunity = openings × wage),
  `sector_overview` (programs by addressable demand), `program_pathways` (a program's
  occupations by opportunity). The unify-vs-federate question (Workstream 4) lives here.
- `backend/partnerships/quantities.py` — the canonical resolvers every criterion composes
  (`gap`, `coverage`, `supply_over_tops`, `addressable_demand`, `program_socs`, the roster/
  feeder helpers, the enrollment/award trend helpers). New measures **compose these**;
  reimplementing a quantity breaks referential integrity by construction.
- `docs/architecture/supply-demand-construct.md` — where the measures come from: §1–2 the two
  sides and the χ projections; §5 the anchor framings (sector/program/occupation) and
  intent-conditional entry; §8 why sum-across pools carry no penalty. This grounds *what
  measures are native to which unit*. **Note §7 still uses the stale "market share / supply
  concentration / competitive overlap" terms — a companion consolidation renames these to
  supply-share/coverage/cross-institution; the plan should assume the corrected vocabulary.**
- `docs/architecture/mcp-server.md` — the conversational layer this extends: the
  `{anchor × operation}` grid, the descent, the response envelope, the DOCTRINE priming
  channel (where principle 3's behavior is taught to the model).
- `docs/domain/epistemic-contract.md` — the reading doctrine the named-axis / no-reification
  rules are a specialization of.

## Workstream 1 — The unit primitives: new registry entries + peer sets

- Add `occupation` and `college` as `unit_type` entries — the two the current question space
  demands. Occupation's peer set is the sector's occupations; the college peer set is the
  region's colleges (or, when the member is a district or consortium, its own colleges) — the
  **cross-institution comparison** that is the real "L2" work, now expressed in the existing
  engine.
- **The peer-set model is the core design.** Leave the mechanism free, but pin the invariants:
  the set is analogous-units-only, well-defined, and *stated in the response* (a practitioner
  must be able to see whose numbers are in the comparison). Cross-scope peer sets normalize by
  share (principle 4).
- Member (district/consortium), employer, and sector unit types are **out of scope now** (named
  in forward references) — build only what the question space demands.

## Workstream 2 — The measure algebra per unit (native, no-composite)

- Enumerate the admissible named axes per new unit type, each a count / same-grain ratio /
  measured outcome, **composed from `quantities.py`**, each passing the operational test in
  principle 2. Derive them from the construct (`supply-demand-construct.md`): an occupation
  carries openings, median wage, projected growth, employment, its regional supply and gap;
  wage lands **natively** on occupations (it cannot on programs without a composite — that
  asymmetry is a feature, and the wage-on-occupations axis is the payoff).
- Define, per unit type: the **default axis** (the sensible sort when the practitioner names
  none) and a **predicate→axis lexicon** (the canonical readings — high-paying→wage,
  underserved→gap, in-demand→openings) that principle 3 defaults from.
- Every new axis registers with `composite=False` and inherits the battery. If a tempting
  measure cannot register without `composite=True`, it is not an axis — surface its components
  as separate axes instead.

## Workstream 3 — Predicate resolution behavior (the never-reify layer)

- Implement rank-by-default-and-disclose (principle 3) as a **doctrine + tool-description**
  concern, not engine logic: the response always carries the full named-axis profile; the
  response always **names the axis it sorted by**; the model is taught (via the DOCTRINE
  channel and the `compare` description) to disclose the axis, treat a compound predicate as
  one reading, and **present the axes rather than pick when no defensible default exists.**
- The design must make the sorted axis a **structured, surfaced field** (not only prose), so a
  context-free agent reads which axis produced the order — consistent with the epistemic
  self-sufficiency principle (nothing the agent must not miss lives out-of-band).

## Workstream 4 — Federate the entry points, unify the ranking vocabulary (decided)

- **Decision: federate, do not collapse.** The curated descent forms (`supply_demand_gaps`,
  `unmet_demand`, `sector_overview`, `program_pathways`) STAY. Their filters, framing,
  guardrails, `view_link`s, and next-moves are irreducible and must NOT be collapsed into
  `compare` calls (that would drop the greenfield filter, the sector framing, the descent
  wiring). But their internal ranking routes through the SAME criterion vocabulary the
  `compare` registry defines, so a ranking axis (`gap`, `addressable_demand`, …) is defined
  ONCE and cannot drift between `compare` and a form. Reject both extremes: collapsing forms
  into `compare` (loses filters/framing) and letting forms keep hand-rolled sort keys (drift).
  Acceptance test: a form's ordering by axis X equals `compare(unit, criterion=X)` on the same
  set.
- **Decompose the "opportunity" sort (decided).** `unmet_demand` and `program_pathways`
  currently rank by "opportunity = annual openings × median wage" — the pattern principle 3
  forbids: it reifies a compound predicate into a single product, buries the volume-vs-pay
  tradeoff, and imposes an order neither named axis gives. Replace it: rank by the two named
  axes (annual openings, median wage) with a disclosed default and both visible. The composite
  "opportunity" product is retired as a sort key and must not reappear as a hidden default. (If
  the annual earnings-flow — openings × wage — is genuinely wanted, it may return only as an
  explicitly *named*, disclosed axis, never as the silent "opportunity" order.) This changes the
  order these two forms return, so the plan sequences it as a deliberate, tested behavior change
  with updated characterization goldens.

## Workstream 5 — The operation vocabulary

- Rank (top-k) exists. Assess whether the question space demands **filter** (threshold —
  "occupations above $X wage") and **pairwise compare** ("A vs. B"). Build only operations real
  NL questions require; do not speculatively add an operation algebra.

## Workstream 6 — Evals

- New unit types inherit the parametrized battery automatically — verify the parametrization
  actually generalizes (peer-set fixtures for occupation and college).
- Add the never-reify checks: (a) the structural no-composite gate already covers principle 2;
  (b) a deterministic check that every ranked response carries its sorted-axis field; (c) a
  semantic harness (behind the deterministic gate, per the codebase's LLM-judge discipline)
  that a compound-predicate question yields a disclosed axis or a surfaced fork — never a bare
  ordering with no named axis.

## Explicit non-goals (scope discipline)

- **No parallel engine, no form-per-comparison.** Extend the registry.
- **No composite / score / index / weighting.** Structurally forbidden; if a measure needs a
  chosen weight, split it into named axes.
- **No "market share," "competitive," "concentration" vocabulary** — anywhere, including tool
  descriptions and framing.
- **No clarifying-question gate** on fuzzy words — that reintroduces the blank prompt the
  descent exists to prevent. Default-and-disclose; present-the-axes only when no default is
  defensible.
- **No speculative unit types or operations** — occupation and college first, driven by the
  actual question space; employer/sector and filter/pairwise only when a real question demands
  them.
- **No reimplemented quantities** — compose `quantities.py`, or referential integrity breaks.
- **No new document-generation or dashboard work** — this is the conversational comparison
  surface only.

## Acceptance

1. *"Which occupations are attractive?"* returns the sector's occupations with their full
   named-axis profile, ranked by a **disclosed** default (or the fork surfaced when the reading
   is genuinely ambiguous) — never a hidden composite score.
2. *"How does my college compare to its peers?"* returns a **share-normalized,
   positioning-framed** comparison across the region's colleges, the peer set stated.
3. Occupation and college register as new `unit_type`s; each inherits the full eval battery and
   passes it; `_register` still raises on any `composite=True`; every ranked response names its
   sorted axis in a structured field.
4. Referential integrity holds: a unit's numbers are identical across `compare` and the descent
   forms (the shared `quantities.py`), pinned by tests.
5. Vocabulary is supply-share / coverage throughout; the doc consolidation removing
   market-share / competitive / concentration has landed.
6. Existing characterization goldens remain byte-identical for unchanged computations;
   `docs-audit` passes.

## Forward references (named, not silent)

- **Doc consolidation — DONE.** `supply-demand-construct.md` §7–9, `mcp-server.md`, and the
  `project_mcp_server` memory have been consolidated to supply-share / coverage /
  cross-institution; the stale "market share / supply concentration / competitive overlap" terms
  are retired ("supply concentration" dropped — it is subsumed by cross-college coverage). The
  evidence base this prompt points at reads clean.
- **Member (district/consortium), employer, and sector unit types** are the next registry
  entries after occupation and college — same shape, deferred until a question demands them.
- **The dashboard honoring the same comparison vocabulary** — a separate thread; named so the
  ranking axes and the supply-share/coverage terms can later be re-derived as shared canon
  rather than drifting as independent copies.
