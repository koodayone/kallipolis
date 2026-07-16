# Verb-Surface Diagnosis (post-#126, deployed surface)

Diagnosis run of the conversational eval against the **deployed** coordinate-algebra surface
(`orient · navigate · crosswalk · compare · sweep · list_institutions`). Per
`VERB-SURFACE-VALIDATION-BRIEF.md`, this is **diagnosis, not validation**: a genuine ship-gate
(routing + kernel, view-independent) plus a gap-map of where the *inherited* curation under-serves the
verb surface. Model under test: Opus 4.8, subscription subagents, live prod connector. All figures below
are from the captured transcripts + direct connector probes.

## SHIP VERDICT: SHIP — the affordance bet held.

- **Precondition:** connector = **exactly the 6 verbs**, 0 legacy tools, across all 32 naive subagents
  (each verified its toolset and would have aborted on any legacy tool). Live surface healthy
  (`list_institutions` → 140 members; `orient` → `member_portfolio`).
- **Tier A substrate gate:** GREEN (12 passed) — numbers sound + cross-tool + dashboard-consistent on
  the golden coords. Prose grading is meaningful.
- **Routing (the hypothesis):** **FALSIFIED in the good direction.** Refined seed-turn metric →
  **0 / 32 whole-institution asks looped sectors.** Every portfolio/whole-institution seed routed to
  `orient` once — including the two adversarial stress probes explicitly built to tempt per-sector
  looping ("sector-by-sector breakdown… one by one" on the 11-sector `baccc` and `smccd`). The deleted
  `_ROUTING` anti-loop steering was **re-encoded into `orient`'s `framing.meaning` + `next_moves`**
  ("answers a whole-institution portfolio question in ONE call; the per-sector / per-occupation views are
  drills"), and the model reads it. No B′ arm needed.
- **Judge (backstop, 8 transcripts on the interpretive dims):** **0 fails, 0 tension leans.** Principle
  passes 7–8/8 on every principle; the 3 sub-pass partials are minor and none trace to the abstraction or
  the lost steering (see Findings C, doctrine nits). Prose is concise (judges: "headline-first, one caveat
  then stop") — no verbosity regression vs the #123 baseline's −34% words/turn.

Routing flat-or-better **and** judge flat ⇒ the abstraction (5 verbs + list helper over one coordinate)
carries intent → verb+coordinate at least as well as the 11 task-shaped tools. **Freeze the verb pathways
as regression fixtures.**

---

## Deterministic scorecard (checks.py PRIMARY, 32 transcripts)

| check | PASS | reading |
|---|---|---|
| **routing (refined seed-loop)** | **32/32** | no whole-institution ask fanned >1 sector |
| routing (checks.py raw) | 28/32 | the 4 "fails" are false positives — turn-3 **same-sector drills** counted as loops |
| no_invented_score | 32/32* | 2 flagged are the analyst *refusing* to blend ("a blended index would bury…") — negation just outside the regex window |
| axis_named | 26/32 | 6 misses = analyst named a *different valid* axis than `sorted_by` (e.g. ranked by coverage, not gap) |
| traceability | 6/32 | **capture artifact, not fabrication** — "all **26** colleges" (a grain phrase), quoted thresholds ($50k, 100 openings), and a lossy `figures` dict (analyst recited orient's Ag 4,500 but logged only `ag_gap`) |
| view_link_offered | 8/32 | self-reported + heuristic; `orient`/greenfield forms carry **no** view, so nothing to offer there — see Finding G |

**Metamorphic invariants (Tier C):** regional-invariance machinists **355 = 355** (smccd anchor ==
svamp anchor) HOLDS; grain-nesting **skyline adm supply 71.7 ≤ smccd 200.3** HOLDS. Establish-before-analyze:
**5/5** onboarding probes established the institution before analyzing (zero premature analysis; the
`premature-analysis` probe made 0 tool calls on turn 1).

**Judge tally (8):** I 7P·1partial · II 8P · III 8P · IV 7P·1partial · V 7P·1partial · tensions all
balanced. Partials: overclaim I (demand→"shortfall" rhetorical upgrade), two-demand IV (didn't proactively
offer the alternate reading), portfolio-routing rep1 V (**= Finding C**, independently caught blind).

---

## FINDINGS (triaged per the brief)

### C — Substrate/kernel (PRIORITIZE): `orient` and `navigate` disagree on the same sector's supply/gap
The migration's headline residual, now with a conversational receipt. `member_portfolio` (orient) computes
each sector's regional supply as `supply_over_socs(region, socs)` **ungated** (`forms.py:909`), while
`sector_overview` (navigate) uses `supply_over_socs(region, sector_socs, spec=rspec)` **gated by in_scope**
(`forms.py:995`). Same coordinate, same label ("regional supply — all 26 colleges"), **different measure**
(orient includes cross-sector program spillover; navigate doesn't), empty stamp (`predicate_version:""`).

- Systemic, not one sector: (smccd, business) orient 6,793 / gap 49,067 vs navigate 5,294 / gap 50,566;
  (smccd, adm) orient 3,923 / gap 4,227 vs navigate 2,163 / gap 5,987. Flagged **independently by ~6
  subagents** and by the blind rep1 judge as V figure-drift.
- **Non-deterministically reconciled:** rep3/baccc/overclaim *named* the discrepancy; rep1 *silently
  shifted* 703→427 across turns. You cannot rely on the analyst to paper over a substrate contradiction —
  which is exactly why "one voice" must be guaranteed by construction, not vigilance.
- This is the deferred **K1-purity / §6.2 aggregation-path** residual. **Tier A does not catch it** — the
  5 golden coords don't cover `member_portfolio`'s per-sector supply (coverage hole).
- **Fix (substrate, not description):** unify the sector-level figure to one birthplace (thread `spec` /
  the gated rule into member_portfolio's per-sector rows, matching the dashboard), **or** stamp the two as
  distinct measures so the surface can mark the difference. Do **not** solve this by telling the analyst to
  reconcile it — that's the fragile path rep1 fell off.

### D — Surface-mechanic (fix now): `compare` under-advertises its unit_type × criterion menu
The model repeatedly guesses the natural word and gets gated, then self-heals: `unit_type=sector`→gated,
`unit_type=institution`→gated (valid: program/occupation/college); `criterion=gap`→gated (valid:
`addressable_gap`), `criterion=wage`→gated (`median_wage`), `criterion=supply`→gated (`sector_supply`).
Costs a round-trip and risks a dead-end. **Fix:** list the admissible unit_type × criteria menu in
`compare`'s description. (Reveals a no-view region — see Gap-Map #1.)

### E — Surface-mechanic (fix now): `navigate(lens=greenfield)` silently ignores `sector` and mislabels the coordinate
`navigate(sector=business, lens=greenfield)` and `navigate(sector=adm, lens=greenfield)` return the
**identical** member-wide 59-occupation list (Customer Service Reps 5,450, Truck Drivers 3,680, Nursing
Assistants 3,570 …), and **both stamp the returned coordinate `sector:"adm"`** regardless of what was
passed. `unmet_demand` is member-anchored by design, but the verb accepts `sector=` and drops it silently —
a least-astonishment violation that made 4 subagents hand-filter cross-sector spillover under an ADM query.
**Fix:** reject/warn that greenfield is member-wide, or scope it to the sector's occupations; fix the
mislabeled coordinate either way.

### F — Surface-mechanic (fix now): `orient`/`navigate` resolve only bare member_ids, not display names
"San Mateo County CCD", "Cañada College", "Skyline College", "Laney College" all **gate**; only `smccd`,
`canada`, `skyline`, `laney` resolve. Establish-before-analyze still PASSES (the flow recovers via
`list_institutions` → id → orient), but at 1–2 dead-ends of friction per cold open. **Fix:** fuzzy-resolve a
label in the gate, or name the resolved id in the gate message.

### G — Doctrine (minor): offer-the-view behavior is inconsistent
The #124 mechanical fix is **confirmed deployed** — `compare` now emits a view_link
(`preview.kallipolis.us/smccd-adm?lens=programs`), as do the `navigate` sector/gaps/occupation views. The
residual is behavioral: when a view_link is present, the analyst often offers a *next move* instead of the
*corroborating dashboard*. Judges still rate interpretive V pass (provenance + coordinate-naming strong);
`member_portfolio` and `unmet_demand` legitimately have **no** view. Re-characterize the standing finding:
mechanism closed, prose-consistency residual open (doctrine).

### Other doctrine nits (minor, none migration-caused)
- **demand→"shortfall"** rhetorical upgrade without a returned gap figure (overclaim I-partial).
- **offer the alternate reading proactively** on a two-reading seam, not only after the practitioner
  disambiguates (two-demand IV/VI-partial).
- **"feeds N openings"** verb brushes the banned feeder imagery (out-of-scope-funding).
- **"dominant supplier"** for a ~30% share — bound standing language to the actual share (strategic rep2 V).

### Eval-harness calibration (not product)
- `checks.py routing` over-counts turn-3 same-sector drills → scope it to **seed-turn distinct-sector
  fan-out** (the 4 raw "fails" are all healthy drills).
- `semantic_checks.golden_traversal` cites **legacy form names** → can't match verb calls (form:False
  everywhere); update goldens to verb+lens. `two-demand` served-regex + `no_invented_score` negation-window
  need widening.
- `traceability` figures-capture is lossy (self-report) → tighten the capture schema or port to
  server-side capture for the CI gate.
- **Tier A coverage hole:** add `member_portfolio` per-sector supply to the corroboration golden set (would
  have caught Finding C).

---

## THE GAP-MAP — the 11 inherited views under the verb surface (input to the curation redesign)

`navigate` already absorbs **6 of the 11** form-ids via lens/entity, and the model invokes the lenses
correctly (gaps · greenfield · coverage · employers · entity=occupation all exercised). So "collapse to a
lens" is largely **already done and validated**; the redesign work is the twins and the holes.

### Survive as genuinely distinct designed answers
| view | reached by | why distinct |
|---|---|---|
| `member_portfolio` | orient | whole-institution, all sectors, ONE call — the top of the descent |
| `pathway` | crosswalk | the TOP→CIP→SOC join *traversal* itself (needs a program or occupation anchor) |
| `compare` | compare | turns a measure into a *ranking* by a named criterion |
| `occupation_profile` | navigate `entity=<soc>` (sector-agnostic) | occupation-anchored, region-wide entry point |
| `coverage` | navigate `lens=coverage` | college × occupation Covered/Partial/Gap legibility |
| `regional_employers` | navigate `lens=employers` | distinct data (BLS OES staffing) — the convening list |

### Collapse candidate — the awkward-granularity twins (the redesign crux)
- **`member_portfolio` per-sector row ⇄ `sector_overview` summary.** Both answer "this sector's regional
  demand/supply/gap + member share," but via different feeder rules (Finding C) and different anchors
  (member-anchored occupation-walk vs sector-anchored program-forward). **Make the sector-level figure ONE
  coordinate value; let `sector_overview` = that value + the program rows.** This is the "two legacy views
  at awkward granularity" the brief named — and the fix for Finding C.
- **`sector_overview` (program-cut) vs `gap` (served-occupation-cut) vs `unmet_demand` (unserved-occupation-cut)**
  are three partitions of one sector. Coherent as lenses; keep them, but the redesign should make the
  *cut* legible (program vs served vs unserved) rather than leave it implicit in lens names.

### No-view regions — valuable question-space with no view (the build list)
1. **Portfolio-level sector ranking** — "which sector should we prioritize?" `compare` has **no `sector`
   unit_type**, so every portfolio prioritization ask gated; the analyst eyeballs `orient`'s rows. HIGH
   value — it's the natural portfolio follow-up. → add a sector unit_type to compare, or a ranked lens on orient.
2. **Time-series / vintage / trend** — "is that current?", "is the trend real?" `sweep(over: vintage)` is a
   **reserved, unbuilt verb**. The algebra predicts it; nothing answers a temporal question today.
3. **Sector-scoped greenfield** — "unserved occupations *within* Advanced Manufacturing." greenfield is
   member-wide only (Finding E); the cross-sector fan-out (nursing, trucking under an ADM query) is the symptom.
4. **Job-quality / wage at sector grain** — wage lives only at occupation grain (occupation_profile,
   compare `median_wage`). "Which sectors pay best?" has no view.
5. *(Out of ontology, correctly refused: cost / funding / feasibility — not a gap to fill.)*

### Verb-surface coverage summary
- `orient` → member_portfolio (+ establish). `navigate` → sector_overview · gap · coverage · unmet_demand ·
  regional_employers · occupation_profile (the poly-lens verb — 6 forms). `crosswalk` → pathway.
  `compare` → compare. `list_institutions` → list_scopes. `sweep` → **reserved (no form)**.
- Affordance is now separable from capability: every named entry-point is a (verb, coordinate-region) label
  over one kernel. The redesign earns each named affordance back from *this* gap-map, not the armchair.
