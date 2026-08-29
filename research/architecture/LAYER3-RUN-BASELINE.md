# Layer-3 eval — run baseline (the target to confirm against)

Runs 1–3 (prose) + onboarding + the semantic first slice were driven 2026-07-14. Raw transcripts were
session-scratch; this distills the grades + findings so a fresh `/conversational-eval` session has a real
before/after reference and can freeze fixtures. All measured on Opus 4.8 (`claude-opus-4-8[1m]`).

**Method caveat:** runs 1–3 measured the DOCTRINE lift via **priming-injection A/B** — the revised DOCTRINE
was injected into the analyst's brief; the live connector still served the old one. The confirmation run binds
to the **deployed** DOCTRINE (now live, PR #118) for the first time — that is what it validates.

## Prose eval (constitution I–V) — the 9-pathway affected set

Run 1 baseline (all 12 pathways): **54/60 principle-grades pass, 6 partial, 0 fail.** Dominant weakness =
verbosity (5 pathways `erred_complete`, ~500 words/turn) + inform-don't-decide (III) leaks under pressure.

Arc on the 9 affected pathways — grades (I·II·III·IV·V) run1 → latest, + words/turn:

| pathway | run 1 | latest (run 2/3) | words/turn | lift |
|---|---|---|---|---|
| attractive-occupations | P P ~ P P | **P P P P P** (run2) | 426 → ~258 | III fixed; guide+concise leans gone |
| strategic-programs | P ~ P P P | **P P P P P** (run2) | 408 → ~273 | II fixed; complete lean gone |
| out-of-scope-funding | P ~ P P P | **P P P P P** (run2) | 346 → ~169 | II fixed; complete lean gone |
| greenfield | P P P P P | P P P P P (run2) | 543 → ~315 | complete lean gone |
| overclaim-failing | P P P P P | P P P P P (run2) | 339 → ~217 | complete lean gone |
| plain-language | P P ~ P P | P P ~ P P → **P P P P P** (run3) | ~130 | III fixed in run 3 (softened-gloss ban) |
| teach-the-ontology *(canary)* | P P P P P | P P P P P (run2) | 417 → ~339 | no regression |
| portfolio-routing *(canary)* | P P P P P | P P P P P (run2) | 477 → ~297 | no regression |
| concise-under-pressure | P P P ~ P | (run2 I~ V~) → **P P P P P** (run3) | ~85 | IV fixed; run-2 grain overreach fixed in run 3 |

**Net (affected set): 5 principle partials → 0; 6 tension leans → 0; −34% words/turn.** All fix_layers were
`doctrine` except cross-institution's I-partial (`model-nondeterminism`, a one-off, not re-run → the only
remaining partial across all 12 at latest).

**Confirmation target (Session 1):** reproduce **0 partials / 0 leans** on these 9 against the deployed
DOCTRINE — specifically no "feeder"/"feeding program" language, a *contingent* pick under a forced "just tell
me the single best one" (not an unconditional "X is the best bet"), and concision holding *without dropping a
load-bearing caveat*. Run the borderline ones (attractive, plain-language, concise-under-pressure) **≥3×** —
model-nondeterminism is real (the cross-institution slip was a one-off), so a single pass can mislead.

## Onboarding (establish-before-analyze) — 5 probes
All 5 establishment **PASS**: cold-open (asked), premature-analysis (refused to analyze "our region" with no
member — zero tool calls turn 1), vague-identifier (narrowed `asked→establishing→established`, no early guess),
grain-switch (re-grounded college→district; regional gap invariant, share grows), out-of-scope (rejected the
nonprofit + redirected to Peralta, no fabricated coverage). **No `assumed` state anywhere.** Target: still 5/5.

## Semantic first slice (Tier C, Article VI)
- **regional_invariance_51-4041:** was **FAIL** — smccd 422 vs svamp 355 for the same regional machinists gap.
  Root cause = the `supply_demand_gaps` unserved-occupation bug (**fixed, PR #120**). Post-fix target: **PASS**
  (smccd now gates → `occupation_profile` = 355, matching svamp).
- **grain_nesting_51-4041:** **PASS** (skyline 23 ≤ smccd 28.3).
- **two-demand:** **PASS** (surfaced 8,150 full-sector vs 1,240 served, named which is which).

## Semantic Phase 2 (Tier C) — coordinate_identity + forward_reverse, driven live 2026-07-15
Driven against the live connector (seed graph on `bolt://localhost:7691`), member `deanza × adm`, SOC 51-4041
(fed by TOP 095630). The **integration was closed first** — `run.md` now drives the semantic probes and grades
with `semantic_judge.md` as a first-class A→B→C step, so Article VI is exercised by a run rather than shipped-
but-ungraded. Capture faithfulness confirmed on the first probe before fan-out.

- **coordinate_identity_openings_51-4041 (metamorphic, tool-independence):** **3/3 pairs PASS.** Machinists'
  regional openings read **510** via `occupation_profile` (role A) AND **510** via a `compare(unit_type=
  occupation, criterion=regional_openings)` row (role B) — the coordinate-aware extractor matched SOC 51-4041
  before asserting equality, so it did not collide with the two-demand seam. Routing was deterministic across
  all 6 transcripts (occupation_profile vs compare, never crossed). This is the two-window invariant's MCP leg;
  the dashboard leg is its acceptance test for the unification.
- **forward_reverse (⊇ membership, per-transcript):** **2/2 PASS.** Forward `program_pathways(095630)` named 12
  occupations incl 51-4041; reverse `program_pathways(soc=51-4041)` returned 095630 — the edge is bidirectionally
  present (`forward_reverse_membership` ✓, 1 edge checked, 0 violations). The many-to-many looseness was flagged
  in prose both runs ("a graduate is qualified for the pool, not slotted into a single role") → judge
  `crosswalk_looseness_flagged: yes`. Reverse correctly reported the **regional** gap (355), not the member's
  share — no grain swap.
- **Judge (Article VI + defensibility), 2 transcripts graded:** classification **PASS** on both; the loop
  surfaced two minor **defensibility** nits (both `fix_layer: doctrine`, not substrate/routing): (1) the
  `compare` path reported `view_link=false`, so the corroborating dashboard — the two-window second window —
  was not offered (`view_addresses_coordinate: absent`); (2) De Anza's own supply shown as both 49 (latest year)
  and ~44 (3-yr annualized) without naming them as distinct measures. Iteration-queue items, not Phase-2 blockers.
- **Deterministic gate:** `pytest evals/conversational/test_semantic.py` — **32 checks green** (coverage requires
  the two new laws' probes + the metamorphic pair completeness; functional tests for the coordinate-aware
  extractor, the two-demand non-collision guard, and forward/reverse membership).

## Shipped
DOCTRINE tuned (#118), pre-gate fixed + Article VI + Tier-C first slice (#119), gap bug fixed (#120) — all
merged to `main` (`d4f8092`) and deployed to prod. Tier-C Phase 2 (coordinate_identity + forward_reverse +
absence_not_zero, the run.md integration, and the covering-set widening to ~20 probes) is the next slice.
