# Plan-mode charge: a foundational evaluation methodology for semantic classification & answer defensibility over the Kallipolis ontology

You are designing — **not implementing** — the foundational evaluation methodology that gives us
high confidence that the *combinatorial space of questions* a workforce practitioner can ask over
the Kallipolis ontology is (a) **classified correctly** — every question routes to the right
ontological traversal, at the right grain and direction — and (b) **answered defensibly** — with
epistemic rigor and language that builds institutional trust, such that a dean could reconstruct and
defend the answer to a board.

Produce an engineering plan an experienced developer could execute. Optimize for *foundational* —
this becomes the third pillar of our eval architecture and we will build on it for a long time.

---

## 1. Where this sits — the three-layer model, and what is already proven

Our evaluation stack has three layers. Two are built and green; the third is what you are designing.

- **Layer 1 — Substrate (computation).** `backend/evals/conversational/test_substrate.py` +
  `backend/mcp_server/test_compare.py` (corroboration/referential). Asserts the numbers are correct,
  cross-tool consistent, and consistent with the dashboard (the two-window invariant). GREEN.
- **Layer 2 — Prose (behavior).** The conversational constitution
  (`backend/evals/conversational/constitution.md`), five principles + four tensions, graded by a
  layer-aware judge (`judge.md`) over scripted conversational pathways (`pathways.py`), with a
  deterministic pre-gate (`checks.py`). Three tuning runs closed all partials/leans on the affected
  set; the DOCTRINE in `backend/mcp_server/worldview.py` is converged. GREEN.
- **Layer 3 — Semantic classification & defensibility.** *Largely untested.* The existing
  conversational pathways are a convenience sample at a single coordinate (`smccd`/`svamp × adm`) and
  assume the right tool was already chosen — they stress *how the analyst speaks*, not *whether the
  question was routed correctly across the ontology*. The one real Layer-3 probe so far is the
  onboarding set (`ONBOARDING_PATHWAYS` in `pathways.py`): 5 pathways testing "establish the
  institution before analyzing." All 5 passed — evidence the *establish-before-analyze* law holds,
  and a template for what a Layer-3 probe looks like. **This layer is otherwise a gap.**

**Honest framing (do not manufacture urgency):** we have *no evidence Layer 3 is broken* — the
routing/onboarding probes we have run passed. This is *proactive* coverage of the space that most
directly governs institutional trust, done before it breaks in front of a customer. The plan should
reflect that posture: rigor and coverage, not alarm.

---

## 2. The conceptual frame — the ontology as a typed generator algebra

Treat the ontology as an algebra. A practitioner's question is a request to evaluate a **measure at a
coordinate**, sometimes over a **comparison class**; answering it is a **walk** over typed objects
via typed operations. The methodology's job is to verify the analyst's walks respect the algebra's
*laws* in conversation. Use this as your working vocabulary (refine it against the source):

- **Objects (typed nodes):** Institution `{grain: college | district | consortium}`, Program (TOP6),
  Occupation (SOC), Sector, Employer; crosswalk intermediary CIP.
- **Relations (edges):** `HAS`(institution→program), `IN-SECTOR`, `PREPARES`(program→occupation via
  TOP→CIP→SOC, **many-to-many**), `DEMANDS`(region→occupation), `SUPPLIES`(region's colleges→
  occupation), `HIRES`(employer→occupation).
- **Measures at a coordinate:** openings, median wage, growth, enrollment, awards/completions (member
  & regional), gap, share, addressable demand — each carrying a *coordinate* (grain, region, entity,
  measure, vintage, authority).
- **Operations (the 11 tools) as typed functors:** `list_institutions`, `institution_overview`,
  `member_portfolio`, `sector_overview`, `program_coverage`, `program_pathways` (forward & reverse),
  `occupation_profile`, `supply_demand_gaps`, `unmet_demand`, `regional_employers`, `compare`
  (unit_type × criterion). Their static identity, adjacency edges (the "what to ask next"), and
  guardrails live in `backend/mcp_server/catalog.py` (`FORMS`) — **read this; it is the algebra's
  spec already half-written.**
- **Laws / invariants (must-agree, the trust backbone):**
  - *Coordinate identity:* a measure at a coordinate is one value however reached (an occupation's
    regional openings via `occupation_profile` = via a `supply_demand_gaps` row = via a `compare`
    row).
  - *Regional invariance:* an occupation's regional gap is invariant to which member anchors the
    query (Bay-Area demand − all-26-colleges supply).
  - *Grain nesting / part ≤ whole:* a district's college supplies sum to the district's; member share
    = member supply ÷ regional supply; served-occupation demand ≤ full-sector demand; a program's
    addressable demand ⊆ its sector's demand; **addressable pools are NOT summable (they overlap).**
  - *Forward/reverse consistency:* if program P `PREPARES` occupation O, then O's feeder-program set
    contains P — set membership, with many-to-many looseness, **not** magnitude equality.
  - *Absence semantics:* gated/blank = unknown, never 0; a member with no program = structural 0,
    distinct from unknown.
  - *Establish-before-analyze:* no measure is defined without an institution coordinate.
- **Forbidden compositions:** summing overlapping addressable-demand pools; reading a member's
  latest-year as a regional trend; comparing across grains without re-scoping; analyzing a scoped
  question ("our region") before the anchor is established.

---

## 3. What "good" means — the two evaluation dimensions Layer 3 adds

Beyond the constitution's I–V, Layer 3 grades two dimensions the current rubric does not capture:

- **Classification correctness.** Did the question route to the correct traversal — right tool(s),
  right grain (college/district/consortium/region), right direction (forward/reverse), right
  comparison class? A mis-classification produces a plausible, wrong-scoped number and is invisible
  to I–V (they assume the right data was fetched). *The plan must decide whether this is a **6th
  constitutional article** or a facet of Principle I, and justify the choice.*
- **Defensibility / interpretability.** Can the practitioner reconstruct *why the answer is what it
  is* — which measure, which grain, which authority, as of when — well enough to defend it to a
  board? Concretely: does the answer name its coordinate; flag which reading it chose at an ambiguous
  seam; stay stable under rephrasing?

---

## 4. The known seams — the joins where classification and trust actually break

Coverage must be *weighted toward these*, each a deliberate probe (extend the list from `catalog.py`
edges + `SUBSTRATE-QUEUE.md`). Observed, not hypothetical:

1. **The two-demand seam.** "What's the demand for my sector?" maps to `sector_overview` (full-sector,
   ADM ≈ 8,150/yr) *or* `supply_demand_gaps` (served-occupations, ≈ 1,240/yr) — one natural-language
   question, two correctly-scoped-but-different numbers. (Also logged in `SUBSTRATE-QUEUE.md` as the
   feeder-resolution seam.)
2. **Forward/reverse crosswalk.** program→occupations vs occupation→programs; the fan-out is wide and
   lossy, so the reverse read is looser — must be flagged, not asserted as exact.
3. **Grain transitions.** college ↔ district ↔ consortium; the regional gap is invariant while member
   supply/share change (onboarding-grain-switch passed this — reuse as a seed).
4. **Comparison classes.** `compare` across the wrong unit_type (college vs district), or on an
   unstated axis; symmetry and like-for-like basis (e.g. consistent program-count basis).
5. **Absence vs zero.** gated/suppressed/no-program readings.
6. **Non-summable aggregation.** addressable-demand pools; many-to-many double-counting.
7. **Establish-before-analyze.** scoped questions with no anchor; out-of-scope entities.

---

## 5. Hard design questions the plan MUST resolve (this is the crux — a mediocre plan skips these)

1. **Ground-truth for classification without baking in authors' bias.** How do you define "the
   correct traversal" for a probe? Weigh three sources and choose a backbone: (a) **golden traversal
   per probe** (author-specified correct tool/grain/direction, checked against captured tool_calls —
   like the substrate goldens); (b) **metamorphic/differential invariants** across related probes
   (need no single golden — the §2 laws); (c) **seam-adversarial** probes where the correct behavior
   is to *disambiguate*. Recommend the mix and which is load-bearing.
2. **How the §2 invariants become executable checks.** Which are deterministic from a captured
   transcript (extend `checks.py`) vs interpretive (judge)? State each invariant's check and its
   tolerance/direction (equality, ⊆, ≤, set-membership) — the many-to-many ones are inexact by design.
3. **Coverage design.** Formalize the generator axes and derive a **minimal covering set** (each
   axis-value ≥ once, each named seam probed) — a covering-array/pairwise approach, NOT the Cartesian
   product. Give the target probe count and the selection rule. Justify why it is sufficient.
4. **Seed graph vs live connector.** Golden traversals need a stable graph (the `eval-neo4j` seed on
   `bolt://localhost:7691`); real routing happens live (`api.kallipolis.us/mcp`). Decide what runs
   where: deterministic invariants and golden-classification on seed; behavioral routing on live?
   Note the current harness drives live subagents while Tier A runs on seed — reconcile.
5. **Capture faithfulness for classification.** Grading classification needs the analyst's *actual*
   tool calls (tool, grain, direction) — self-report is the v1 model and is more reliable for
   call-shape than for figures, but decide whether Layer 3 needs server-side capture to be trustworthy
   as a gate.
6. **The 6th-article question.** Is "Classification / answer-the-question-asked-at-the-right-coordinate"
   a new constitutional article, or Principle I extended? Decide and specify the constitution edit.
7. **Integration & minimality.** How this becomes **Tier C** without duplicating Tier A/B: what is
   reused (the subagent harness, judges, the pre-gate pattern), what is genuinely new (a semantic
   pathway schema with golden traversals + metamorphic groups, invariant checks, the classification/
   defensibility rubric). Keep the moving parts minimal.
8. **Where the spec lives.** The generator algebra should be written down once, operationally — every
   element mapping to a probe or a check — likely alongside `docs/domain/epistemic-contract.md`. Avoid
   an academic artifact no one runs against.

---

## 6. Constraints & non-goals

- **Occam / no speculative machinery.** Prefer reuse over invention, flat over nested, fewest moving
  parts. Every abstraction must map to a probe or a check. No combinatorial-explosion matrix. (See
  `CLAUDE.md` reasoning-hygiene + the project's Occam and no-speculative-tooling norms.)
- **Deterministic-first.** Whatever code can verify, code verifies (`research/architecture/
  EVALS-APPROACH.md`); the judge spends only on the irreducibly interpretive. Fix the known
  `checks.py` false-positives (axis_named "gap" length bug, no_invented_score polarity, traceability
  date/SOC-code/negative-magnitude fragments) as part of making the pre-gate a real gate.
- **Reuse the existing harness.** Subagents drive pathways against the tools; judges grade; the skill
  (`.claude/skills/conversational-eval/`) + `run.md` orchestrate. Extend, don't fork.
- **Subscription-only, subagent-driven.** No new API-key dependency for the on-demand form; note a
  path to a headless CI port (as `run.md` already anticipates).
- **Non-goals:** re-tuning the converged prose DOCTRINE; re-deriving Layer-1 computation; building UI;
  a full formal-methods proof system. This is an *evaluation* methodology, not a type checker for the
  server.

---

## 7. Required plan deliverables

The plan should specify, concretely enough to execute:

1. **The generator-algebra spec** — objects, relations, measures, operations, invariants (with
   check-shape + tolerance), forbidden compositions — and where it lives as a doc.
2. **The semantic-coverage matrix** — the covering-set design, the axes, the target probe list
   (grouped by generator coverage + seam), and the data structure (a `SEMANTIC_PATHWAYS` analogue to
   `pathways.py`, carrying golden traversal + metamorphic group id per probe).
3. **The deterministic classification/invariant checks** — module design (extend `checks.py` or a new
   `semantic_checks.py`), each §2 law as a check over captured transcripts, plus the `checks.py`
   false-positive fixes.
4. **The classification + defensibility judge rubric** — the two new dimensions, the verdict schema
   (mirroring `judge.md` + the onboarding `establishment` key), and the 6th-article decision.
5. **The run harness integration** — how Tier C is invoked (seed vs live split), how it composes with
   Tier A/B, the skill/`run.md` changes, and the CI-gate path.
6. **A phased build order** — smallest first-slice that proves the approach end-to-end on 2–3 seams,
   then widen; each phase independently verifiable.
7. **Risks & open questions** — especially ground-truth bias, capture faithfulness as a gate, and
   many-to-many inexactness; how each is mitigated or explicitly deferred.

---

## 8. Read these first (repo root)

- **Eval:** `backend/evals/conversational/{constitution.md, judge.md, pathways.py, checks.py, run.md,
  SUBSTRATE-QUEUE.md}`, `backend/evals/goldens/*.json`, `research/architecture/EVALS-APPROACH.md`.
- **MCP server (the algebra):** `backend/mcp_server/{catalog.py (FORMS, edges, guardrails), envelope.py
  (the epistemic-contract envelope / NextMove), forms.py, scope.py (coordinate_of), worldview.py
  (DOCTRINE), compare.py, provenance.py, server.py}`.
- **Domain/architecture:** `docs/domain/{epistemic-contract.md, glossary.py→glossary.md,
  data-authorities.md, overview.md}`, `docs/architecture/{supply-demand-construct.md, mcp-server.md,
  graph-model.md}`.
- Read `docs/README.md` first for the annotated doc index; obey `docs/conventions.md` if the plan
  touches `docs/`.

## 9. Quality bar

An excellent plan resolves every §5 crux with a defended choice (not a menu), gives a covering set
that a reviewer can see is *sufficient without being bloated*, makes the invariants executable, and
lands the smallest end-to-end first slice that would already catch a real seam. It should read as a
foundation we extend for years — legible, minimal, and rigorous — the same standard the ontology
itself is held to.
