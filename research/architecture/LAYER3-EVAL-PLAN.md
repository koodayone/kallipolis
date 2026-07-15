# Layer 3 — Tier C: Semantic Classification & Answer Defensibility (final plan)

> Produced by the Plan agent from `LAYER3-EVAL-PLAN-PROMPT.md`; refined after the two roadmap items
> were fed in. This supersedes the first draft. One crux (the 6th article) is left as an OPEN
> DECISION for the user — see §Crux 6.

## Thesis
Tier A already proves coordinate identity **as a property of the computation** (`test_compare.py`
referential tests: a program's addressable demand is one value across `compare`/`sector_overview`/
`supply_demand_gaps` because all resolve through the same `canonical` functions). Tier C tests what
Tier A structurally cannot: given a **natural-language question**, does the *analyst* route to the
right form, grain, direction, and comparison class — and can a dean reconstruct the answer? A
misroute yields a perfectly-grounded number (passes I–V) that answers a differently-scoped question.
Invisible today. The unit of a Tier-C eval is the **walk**, not the number.

## Crux resolutions (defended)
1. **Ground truth** — three-source mix: **thin catalog-cited goldens** (classification), **metamorphic
   invariants** (trust, need no golden), **seam-adversarial** (ambiguous joins). Anti-bias rule: *a
   golden facet must cite a `catalog.FORMS`/`EDGES` line* — the author points at the algebra the
   server ships, doesn't invent "correct." A reviewer audits the golden by reading the cited line.
2. **Laws → checks** — a `LAWS` manifest (id → check_fn → relation {=,≤,⊆,⊇,membership} → tolerance →
   per-transcript | metamorphic-group). Coordinate identity (=, 2% band), regional invariance (=),
   grain nesting (≤, share∈[0,1]), forward/reverse (**⊇ membership + looseness flag, never
   magnitude**), absence≠zero (boolean), establish-order (generalizes `checks.routing`).
3. **Coverage** — seam-weighted covering set **~20 probes**; C/D/E axes covered *incidentally* by the
   7 seam groups; `test_algebra_coverage` mechanically asserts sufficiency (every law→group, every
   seam→probe, every form→golden). Minimality gate audits bloat.
4. **Seed vs live (evolved from draft 1)** — **capture LIVE** (routing is a property of the deployed
   priming); classification checks are **graph-agnostic** (check traversal *shape*), so they hard-gate
   live. **Metamorphic invariants are intra-run relational** — compare two live transcripts to *each
   other* (regional gap at member A == member B), so they need no seed. Only the *figure-oracle*
   anchors to seed, in a **headless CI port** that drives golden coordinates through `forms.py`
   directly (reusing `characterization.capture`). Net: no new server infra; routing tested under real
   priming; deterministic figure gate deferred to CI.
5. **Capture faithfulness** — classification gates on discrete **call-shape** (reliable self-report;
   the model just made the call, judge cross-checks prose). Extend the capture: subagent echoes the
   envelope's **`Coordinate` per call** (copies a structured field, faithful — pre-stages server-side
   capture). Figures never trusted from self-report; figure-metamorphics guarded on-demand, hard-gated
   only in the forms-direct CI oracle.
6. **⟵ OPEN DECISION — 6th article?** The plan's two runs disagreed; this is the one genuine fork.
   - **Draft-1 position:** NO — extend I ("answer at the coordinate asked") + V (defensibility) by one
     clause each. Classification is the *precondition* of I; a number at the wrong scope is ungrounded,
     not a peer failure. Occam.
   - **Final position:** YES — **Article VI (Classification)**, distinct from I; fold defensibility into
     V. Argument: a misroute passes I *perfectly* (every figure traces) while answering the wrong
     question → distinct failure mode → distinct article. **Precedent:** the onboarding probes already
     grade an `establishment` verdict *outside* I–V; Article VI generalizes it (establish-before-
     analyze = the special case where the coordinate is the anchor).
   - **Draft VI text:** "Answer the question asked, at the right coordinate. Route every question to
     the traversal that answers it — the right tool(s), grain, direction, comparison class. When one
     question maps to two correctly-scoped readings, name which you took and offer the other. Establish
     the institution before any scoped measure."
7. **Integration** — reuse the subagent loop, judge pattern, scorecard, goldens. New: `semantic_pathways.py`,
   `semantic_checks.py` (+ the cross-transcript **metamorphic runner** — the one new primitive),
   `semantic_judge.md`, `docs/domain/generator-algebra.md`. `fix_layer` adds **`routing-hint`**
   (`server._ROUTING`) as a first-class fix target — a misroute is fixed there or in a `FORMS`
   guardrail, NOT the converged DOCTRINE.
8. **Spec home** — `docs/domain/generator-algebra.md` (prose canon, *cites* `catalog`/`compare`/
   `envelope`, never restates — the "one writer" discipline) + the `LAWS` manifest in code, cross-
   audited so it can't decay.

## checks.py Phase-0 fixes (both plan runs agree, verbatim)
1. `axis_named`: `len(w) >= 3` (unbreaks the 3-char axis "gap").
2. `no_invented_score`: flag only a ranking *basis*, not a negated/refusing use ("won't reduce to one score").
3. `traceability`: strip SOC `\d{2}-\d{4}` + TOP6 `\d{6}` before scanning; compare on signed `abs()`.
Each ships with a crafted-transcript unit test → the pre-gate becomes a real gate.

## Coverage set (~20 probes, seam-grouped)
S1 two-demand (marquee) · S2 forward/reverse · S3 grain/regional-invariance (reuse onboarding-grain-switch)
· S4 comparison-class (incl. "best"-bait) · S5 absence-vs-zero · S6 non-summable addressable · S7
establish (reuse the 5 `ONBOARDING_PATHWAYS` verbatim) · form top-up (unmet_demand, regional_employers,
member_portfolio). **Phase-1 first slice = S1 + S3 + S7.**

## Phased build (each independently verifiable)
- **Phase 0 (0.5d)** — the three `checks.py` fixes + unit tests. No new surface.
- **Phase 1 (2–3d)** — S1 + S3 + S7 end-to-end: ~7 probes, `semantic_checks.py` (coordinate identity,
  part≤whole, regional invariance, establish-order) + metamorphic runner + `LAWS` + coverage test; the
  Article-VI edit (pending §Crux-6 decision) + `semantic_judge.md`; `generator-algebra.md` skeleton.
  Done when S1 fails an analyst that gives one number without naming the fork, and regional-invariance
  fails an analyst whose two anchors disagree. **Already catches a real seam (the 8,150-vs-1,240).**
- **Phase 2 (2–3d)** — widen to all 7 seams + form top-up; `test_algebra_coverage` green.
- **Phase 3 (2d)** — headless CI port: forms-direct figure oracle as a hard gate + server-side
  `Coordinate` logging; wire into `make evals`/unit-tests.

## Roadmap alignment (context, NOT build scope)
1. **Dashboard⇄MCP feeder unification** — the **coordinate-identity law is the specification** for it.
   Framed as the **two-window** invariant: the second window is the **dashboard offered via `view_link`**,
   not just cross-tool MCP consistency. Tier C's coordinate-identity metamorphic includes the dashboard
   leg (reuse `test_substrate.test_dashboard_mcp_corroboration`'s both-paths `capture` oracle), so the
   eval *measures the gap the unification closes* → drives `_CORROBORATION_BAND` to 0. Witness: RN
   29-1141 baccc/health (688.7 vs 688.0).
2. **Deep-link / panel-addressable defensibility** — the judge already scores
   `view_addresses_coordinate: ok|coarser|absent`. Today `viewlink.py` is mostly lens+filter (only
   `coverage` carries a `panel`); the roadmap (deeper traversal → `/landscape/foothill/adm?panel=programs.awards`)
   tightens `coarser`→`ok` at depth. Designed as a **threshold change, not a schema change**.

## Risks
Ground-truth bias (catalog-citation rule + metamorphic-no-golden backbone). Capture faithfulness
(call-shape gates classification; figures guarded→CI-oracle). Many-to-many (⊇ + flag, encoded in
tolerance so no one tightens it). Live/seed divergence (metamorphics are intra-run relational →
graph-agnostic). Routing non-determinism (guarded-not-hard-fail on first observation; `fix_layer:
model-nondeterminism`).

## Critical files
NEW `semantic_pathways.py`, `semantic_checks.py`, `semantic_judge.md`, `docs/domain/generator-algebra.md`
· EDIT `checks.py` (Phase 0), `constitution.md` (+Article VI or +2 clauses), `judge.md`
· REUSE `characterization.py` (`capture` oracle), `pathways.py`/`ONBOARDING_PATHWAYS`
· SOURCE OF TRUTH `catalog.py` (FORMS/EDGES/_ROUTING), `test_compare.py` (the invariants Tier C lifts).
