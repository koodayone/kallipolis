# Unified Engine — plan

The refactor that collapses the analytical stack to one engine: `select(coordinate) → subgraph`,
`aggregate(subgraph, measure) → value`, and forms/dashboard as pure projections over them. It is the
vehicle for the curation redesign, not a separate elegance project. Its output is a **smaller** system —
the coherence apparatus (stamps, `predicate_version`, contract manifests) gets deleted, not extended.

Supersedes the contract-matrix approach (`COHERENCE-CONTRACT.md`, removed): once the engine is unified,
coherence is a property of the architecture (identical coordinate ⇒ identical value, by construction), not
a matrix anyone maintains.

## Why (the one-paragraph case)

Underneath 9 MCP forms, the dashboard build path, and a few bespoke specs, there are really two functions —
choose a slice of the graph, and aggregate it. They are tangled and duplicated, and every hard problem we've
hit (Finding C, the stamp machinery, the incomprehensibility, the four stalled "one voice" cycles) is a
symptom of that tangle. Unifying them makes the system hold-in-your-head comprehensible (three concepts:
verbs move, select expands, aggregate computes), makes coherence structural, and makes every future view a
cheap projection instead of a bespoke form with fresh C-risk. We're building more regardless, so the cost of
*not* doing this compounds with each new view.

## 1. The coordinate (the foundation)

> A **coordinate** is `⟨WHO, WHAT, WHEN, MEASURE⟩`:
> - **WHO** — a set of colleges (the supply scope). Its **region** (the demand/wage scope) is *derived*
>   from the college-set, not a separate axis. (Multi-region members derive a set of regions.)
> - **WHAT** — a *typed* entity-set: `(type ∈ {occupation, program, college}, the set)`. The type is the
>   anchor/direction; the crosswalk connects to the other end. Occupation-anchored and program-anchored
>   supply are genuinely different values — now *visibly* different WHATs, not a hidden predicate.
> - **WHEN** — a window of academic years (or N/A + a vintage, for point-in-time COE signals).
> - **MEASURE** — one of a small fixed family: **sum** (supply, demand) · **difference** (gap) ·
>   **classify** (coverage) · **rank** (compare = map-then-sort) · **neighbors** (crosswalk membership) ·
>   **attribute** (wage, growth, employment, employer staffing-share).
>
> A coordinate resolves to exactly one **subgraph** (a slice of college→program→occupation plus the
> region's demand/wage attributes); the measure is a pure operation over it. **Eligibility is not a
> coordinate dimension** — it is one universal predicate applied when the subgraph is built, minus each
> member's `charter_excludes`. Universal predicate + explicit subgraph ⇒ **identical coordinate ⇒ identical
> value, by construction.**

**Selectors name coordinates.** Practitioner vocabulary maps onto the coordinate through selectors, not new
axes: a *member* is a WHO-selector (→ college-set); a *sector* is a WHAT-selector (→ its occupation-set or
program-set); an *occupation*/*program* is an atomic WHAT. Selectors are graph reads, not rules.

**What this definition dissolves** (the validation that it's the right decomposition):
- **`predicate_version` disappears** — it existed only to tell apart multiple eligibility rules at one
  coordinate. One rule ⇒ nothing to stamp.
- **A′ disappears** — `occupation_profile`'s region-wide supply and a sector gap's supply differed *only*
  because one used `is_vocational` and the other `in_scope`. Same WHO + same WHAT + one rule ⇒ one value.
- **The two-demand seam becomes explicit** — full-sector vs served-occupations demand are two different
  WHATs (the full occupation-set vs the served subset), named, not a hidden ambiguity.

**Honest residuals** (hold in view, don't solve now): a *form* displays several coordinates (a gap view
shows the regional gap at WHO=region and the member's share at WHO=member); MEASURE is a small family, not
literally one sum; multi-region WHO derives a region *set*.

## 2. Eligibility (the one rule)

> A program counts as supply toward an occupation when it is **(1) a workforce program** [`is_vocational`,
> a program property] that **(2) genuinely prepares for that occupation** [a real crosswalk edge] and is
> **(3) actually producing** [completers in the window] — **minus** the querying member's `charter_excludes`.

The governing principle: **subtraction, not fork.** A per-member *exclusion* is a subtraction from one
universal computation — it cannot make two members' numbers incomparable, so it preserves the single engine.
A per-member *alternate rule* (a different base predicate, a different freshness gate, a bespoke scope) is a
fork — it recomputes by different logic and destroys coherence (the C class). The model permits **only
subtraction.**

**What forks get deleted:** `vocational=False` / `is_cte_top4_family` (SVAMP's looser base) → everyone uses
`is_vocational`; `soc_rule=None` (SVAMP's missing awards-gate) → everyone gets the universal producing-gate;
`is_svamp_top` (bespoke scope) → gone. SVAMP becomes the universal rule + `charter_excludes = [094800
Automotive, 094600 HVAC, 043000 Biotech]` and nothing else. (Decision on record: Automotive *is* advanced
manufacturing universally; SVAMP's charter excludes it — a genuine partnership scope, a 3-item list.)

## 3. Selection becomes graph facts (the ontology changes)

The point of "self-governing": the rules that shaped selection become **edges/properties the engine reads**,
not code it runs.

| today (a rule/spec) | becomes (a graph fact) |
|---|---|
| `home_divisions` (which programs belong to a sector) | explicit **sector→program** membership edges |
| sector `excluded_tops` (spurious crosswalk links) | a per-edge **crosswalk quality** property (universal) |
| `is_vocational` (workforce program) | a **program** property (already) |
| awards-active (producing) | a **data fact** (completions in the window) |
| SVAMP's bespoke exclusions | a **member** property (`charter_excludes`) |
| the region for demand | **derived** from WHO (the college-set's region(s)) |

**Sector is a first-class node** with explicit `CONTAINS` edges to **both** its occupations and its
program-families — its dual nature (demand side + supply side) is preserved, and its boundary is a fact, not
a division-code rule. It enters the coordinate as a WHAT-selector.

## 4. The architecture

- **`select(coordinate) → subgraph`** — the sole home of every rule; reads membership / classification /
  crosswalk / eligibility from the graph; emits the concrete `(college, program, occupation, year, qty)`
  tuples. Nothing downstream makes a "which counts" decision.
- **`aggregate(subgraph, measure) → value`** — the small measure family; pure.
- **forms = projections** — pick coordinates, call select+aggregate, arrange. A form may show several
  coordinates; it computes none itself.
- **dashboard = a projection too** (Phase C) — same select, same aggregate.

## 5. The phased plan (each phase ships coherent; the split is the discipline)

**The organizing rule: never move code and numbers in the same step.** Engine-unification changes no
numbers; rule-unification changes numbers deliberately and in isolation. Conflating them is why the last
four cycles stalled.

- **Phase 0 — Characterization net (no product change).** Snapshot every form's output across a
  representative coordinate spread (current goldens, widened). This is the oracle: Phase A must reproduce it
  byte-for-byte. Without it "pure refactor" is a hope; with it, it's provable.
- **Phase A — Unify the engine (structural; numbers UNCHANGED).** Extract one `select` and one `aggregate`;
  rewrite the 9 forms as projections. The bespoke specs still feed `select` at this stage, but are read in
  exactly one place. Characterization-guarded. **Delivers the two goals — comprehensibility and
  coherence-by-construction — at zero number risk.** Could stop here and have won most of it.
- **Phase B — Unify the rule + move selection into the graph (semantic; numbers CHANGE, signed-off).**
  Collapse eligibility to the universal rule + `charter_excludes`; delete the forks; build the sector→
  occupation / sector→program membership edges (retiring `home_divisions`), the per-edge crosswalk-quality
  property (retiring `excluded_tops`), and the member `charter_excludes` (SVAMP). Numbers move (SVAMP drops
  its 7 dormant programs; A′ collapses; any diverging member re-bases) — as ONE diff, regenerated goldens,
  because it's now a single-location change.
- **Phase C — DISSOLVED (investigated, recharacterized).** The mechanical "route the dashboard through
  `select`" is a **no-op**: the dashboard already resolves from the same `REGISTRY` that `select` reads, so
  `select().spec` IS the spec it already uses — routing changes nothing and does NOT make the corroboration
  test a theorem. The investigation found instead a real, uncaught **dashboard⇄MCP divergence at the sector
  aggregate**: the dashboard sums over `resolve(spec).socs` (rule-effective / served set — smccd-adm = 4
  SOCs, demand 1,240) while `sector_overview` sums over `SECTORS[sid].socs` (full PCAH — 49 SOCs, demand
  8,150). Same coordinate, ~5× apart, unlabeled, live. It is the diagnosis's **two-demand seam** across the
  surface boundary — NOT a compute bug (both correct over different occupation-sets), and NOT caught by the
  corroboration test (which checks per-occupation, never the sector aggregate). A **WHAT decision (Phase B /
  curation)**, not a refactor.

## Phase A — CLOSED

All nine analytical forms resolve through `select`/`select_member` (the duplicated preamble that caused C is
gone from the form layer); the C-relevant `supply` measure is the first `aggregate` function. Guarded
byte-for-byte by the Phase-0 characterization net; ~9 clean per-increment commits (`f7f7b6d2`→`63512a31`);
211 tests + net + Tier-A + 12 audit green throughout. The remaining `aggregate` measures (demand/gap/
per-program/portfolio-total) are diminishing-returns polish — the structural win (one selection + the supply
rule) is done. Phase C dissolved into Phase B.

## Phase B — the curation redesign (problem statement)

**Every WHAT must have exactly one denotation; where two denotations are both wanted, they are two named
units — not one ambiguous word.** The sharpest, live instance: "sector" carries two denotations (full-PCAH
occupation-set vs rule-effective/served subset), which is why the dashboard and `sector_overview` diverge.
Resolution shape: one **sector node** (its full occupation membership, explicit graph facts) + a
**served/effective lens** (the derived reachable subset) — two labeled projections of one engine, each
saying which set it is. Ties together with the eligibility decision (universal rule + SVAMP charter) and
sector-as-node (explicit occupation + program membership). Phase-B because it moves live numbers (labeling/
reconciling the dashboard's 1,240) — reserved from Phase A by the discipline.

**Deleted throughout:** the stamp/`predicate_version` fields, any additivity-contract machinery, the
coherence-contract manifest, and the bespoke-spec registry. The refactor's net line count goes down.

## 6. Decisions locked (from the deliberation)

1. Coordinate = `⟨WHO, WHAT, WHEN, MEASURE⟩`; region derived from WHO; WHAT is typed; MEASURE is a small
   fixed family.
2. Eligibility = universal three-condition rule + per-member `charter_excludes`; **subtraction, not fork.**
3. Automotive Technology *is* advanced manufacturing universally; SVAMP excludes it (and HVAC, Biotech) via
   a 3-item charter list — a genuine partnership scope, not a definition bug.
4. Sector = a native ontology node with explicit dual (occupation + program) membership, entering the
   coordinate as a WHAT-selector — edges, not rules.

## 7. Open questions (resolve before/within Phase B)

- **Source of truth for sector→program membership.** The explicit edges have to come from somewhere:
  bootstrap from the current computed `in_scope` sets, or source from an authority (CCCCO / regionalcte.org)?
  Bootstrapping is faster and behavior-preserving; sourcing is more defensible. Likely: bootstrap, then
  reconcile.
- **The exact MEASURE family.** Enumerate and freeze the operation set (sum/difference/classify/rank/
  neighbors/attribute) and confirm every current figure maps to one — no residual bespoke measures.
- **Multi-region WHO.** Confirm `resolve_regions` handles demand summed over a region-set cleanly under the
  new `select`.
- **Dashboard scope in Phase A vs C.** Whether Phase A rewrites only the MCP forms or also brings the
  dashboard's build path onto `select` immediately (bigger blast radius, but closes the seam sooner).

## 8. Risks and sizing

- **Multi-week; Phase A is the bulk** (9 forms + the dashboard path). Bounded (reuses `quantities.py`
  primitives), staged (each phase shippable), and Phase A is number-preserving so its risk is contained.
- **Live prod, two surfaces.** MCP + dashboard share `quantities.py`, so they move together — but Phase B's
  number changes hit the live dashboard. Defensibility-sensitive: signed-off diffs, regenerated goldens,
  and awareness of any figure a stakeholder has already seen.
- **Number changes are real** (SVAMP measured: ~2× swing on the seed, driven by the Automotive charter call
  + the dormant-program drop). Understood and intended, but gated.

## 9. Relationship to the rest

- **This IS the curation redesign's vehicle.** "Which views exist / what they contain" is selection; a new
  view becomes a projection over `select`/`aggregate`. The no-view regions from the diagnosis
  (sector-ranking, time-series, sector-greenfield, sector-wage) become cheap once the engine is unified.
- **The eval** stays as the behavioral gate; the coherence sweep (B-substrate) is *not built* — the refactor
  makes it unnecessary. The characterization net (Phase 0) is the refactor's own guard.
