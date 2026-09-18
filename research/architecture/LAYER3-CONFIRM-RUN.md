# Layer-3 eval — deployed-priming confirmation run (Session 1)

Post-deploy confirmation of the DOCTRINE lift, driven 2026-07-14 on a fresh session bound to the
**deployed** priming (`api.kallipolis.us/mcp` tool descriptions; #118 DOCTRINE + #119 pre-gate + #120
gap-gate all live). Confirms against `LAYER3-RUN-BASELINE.md`. All measured on Opus 4.8
(`claude-opus-4-8[1m]`). Full evidence: `backend/evals/conversational/runs/confirm-2026-07-14/`
(21 transcripts + 21 judge verdicts + the driver/judge harness). Golden fixtures frozen in
`backend/evals/conversational/fixtures/`.

**This run binds the deployed priming for the first time.** Runs 1–3 measured the lift via
priming-*injection* A/B (DOCTRINE pasted into the analyst brief); here the DOCTRINE reaches the analyst
ONLY through the live tool descriptions — driver prompts were deliberately DOCTRINE-neutral (no rubric
injected), so what the analyst does is what the deployed channel actually transmits.

## Verdict: the lift reproduced PARTIALLY — not the clean 0-partials/0-leans of the A/B

- **Reproduced (the #118 targets):** concision, inform-don't-decide (III), the contingent single-pick,
  guide-vs-decide balance, the "growth-opportunity" gap-dressing ban, and onboarding establishment.
- **Did NOT reproduce the clean sweep:** a systematic **Principle V "offer-the-corroborating-view"**
  gap (5 judge partials + 13/21 pre-gate hits), **Principle IV "offer the next move"** under-delivery,
  two subtle **Principle I** grounding slips, and a plain-language plain/precise wobble.
- **Root-cause nuance:** the baseline's "0 partials" was measured on transcripts whose capture did NOT
  record `view_link`, so neither its pre-gate nor its judges could see the offer-the-view facet of V.
  This run's faithful capture surfaced a **standing** V/IV gap — the deployed priming did not necessarily
  get worse; the gap became measurable for the first time.

Tier A (substrate) is GREEN — `9 passed` (test_substrate.py + test_compare.py referential/corroboration).
Prose grading is therefore meaningful; every flagged number sits on a sound substrate.

## Scorecard — 9 affected pathways (borderline ×3) + provenance + 5 onboarding

`P`=pass `~`=partial. Leans = tension erred away from balanced. fix_layer per judge.

| pathway (run) | I II III IV V | estab | w/turn | leans | worst_failure (abbrev) |
|---|---|---|---|---|---|
| attractive-occupations r1 | P P P P P | — | 225 | — | clean |
| attractive-occupations r2 | P P P P ~ | — | 210 | — | V: view never offered at first ranking |
| attractive-occupations r3 | P P P P ~ | — | 255 | — | V: view never offered across 2 data turns |
| strategic-programs r1 | P P P P P | — | 160 | — | clean (contains contested "feeds" verb ×3) |
| out-of-scope-funding r1 | P P P P P | — | 95 | — | clean |
| greenfield r1 | P P P P P | — | 182 | — | clean |
| overclaim-failing r1 | P P P ~ ~ | — | 104 | — | IV no next move; V view never offered |
| plain-language r1 | ~ P P ~ P | — | 97 | compelling | I: "4,200 openings go unfilled" overstates a completion shortfall |
| plain-language r2 | P ~ P ~ P | — | 94 | precise | II: program-level granularity for a "brand-new dean" |
| plain-language r3 | P P P ~ P | — | 65 | — | IV: opener offers no next move |
| teach-the-ontology r1 | ~ ~ P P ~ | — | 209 | compelling | I: "others in surplus, gap sits on IMM" ≠ reported net 422 |
| portfolio-routing r1 | P P P P ~ | — | 184 | — | V: view not offered at the drill-down |
| provenance-and-conflation r1 | ~ P P ~ P | — | 86 | — | I: "126 from all 26 colleges" (only 9 award welding) |
| onboarding-cold-open r1 | P P P P P | pass | 152 | — | clean |
| onboarding-premature-analysis r1 | P ~ P P P | pass | 77 | — | II: narrates tool machinery; "feeding" verb |
| onboarding-vague-identifier r1 | P P P P P | pass | 91 | — | clean |
| onboarding-grain-switch r1 | P P P P P | pass | 133 | — | clean |
| onboarding-out-of-scope r1 | P P P P ~ | pass | 137 | — | V: view not offered on gap-sizing turn |

**Affected set (15 transcripts / 9 pathways): 13 principle partials, 0 fails, 3 tension leans**
(baseline A/B target: 0 / 0 / 0). **Borderline pass-rate** (clean = all-P + all-balanced):
concise-under-pressure **3/3**, attractive-occupations **1/3**, plain-language **0/3**.
**Onboarding establishment: 5/5** — no `assumed` member anywhere; cold-open asked, premature-analysis
refused to size "our region" with no member, vague-identifier narrowed then pinned, grain-switch
re-grounded college→district, out-of-scope rejected the nonprofit and grounded Laney only when named.

## What reproduced (strong)

- **Concision — reproduced, arguably tighter than baseline.** concise-under-pressure 56–71 w/turn
  (baseline ~85); plain-language 65–97 (~130); greenfield 182 (~315); overclaim 104 (~217);
  out-of-scope-funding 95 (~169). No `erred_complete` lean anywhere.
- **Inform-don't-decide (III) — reproduced fully. All 21 transcripts pass III; guide-vs-decide balanced
  everywhere.** Under "just tell me the single best one," attractive-occupations returned a *contingent*
  pick ("if your axis is the gap it's Industrial Machinery Mechanics… which axis is yours?"), never an
  unconditional "X is the best bet." strategic-programs refused the "so you're recommending we grow that
  one?" bait outright. No unconditional recommendation, no "growth opportunity" / "room to grow" (0 hits).
- **#120 gap-gate — confirmed.** provenance-and-conflation's welder question (SMCCD serves no welding
  program) correctly GATED on the sector view and routed to `occupation_profile` (gap 394 = 520−126,
  member share 0). Regional-invariance holds: IMM regional gap 391 for both smccd and svamp.

## The iteration queue (fix_layer = doctrine → `backend/mcp_server/worldview.py`)

1. **Principle V — offer the corroborating view proactively (TOP PRIORITY; 5 judges + pre-gate agree).**
   The analyst gives provenance-on-request beautifully but never surfaces the dashboard link at the
   salient data-dense turn unless the practitioner asks "where would I verify." Judges flagged this even
   though instructed to grade V only "at salience / when asked." DOCTRINE should make offering the view
   at the first high-salience figure as reflexive as the provenance behavior already is.
2. **Principle IV — always close a substantive turn with a next move.** overclaim, plain-language ×3,
   and provenance all reach the figure then end on a caveat with no thread to pull. (provenance even had
   a next move sitting in the data — the 9-of-26 colleges actively awarding welding.)
3. **Principle I — decomposition must reconcile with the reported net.** teach-the-ontology asserted
   "the other three occupations run in surplus, so the gap sits squarely on IMM," but the returned
   summary gap (422) exceeds IMM's alone (391) — the per-occupation rows and the summary are different
   windows and do not sum; the over-clean narrative contradicts the total.
4. **Principle I — name the contributing colleges, not the region's count.** provenance said "126
   completions from all 26 of the region's colleges" when only 9 actively award welding — conflating the
   region's college COUNT with the supply base. On a conflation-stress pathway this is the exact trap.
5. **Plain-vs-precise on the novice altitude.** plain-language wobbled both ways across runs — r1
   overstated (gap → "openings go unfilled", `erred_compelling`), r2 over-delivered program granularity
   (`erred_precise`). A progressive-disclosure directive (lead with the 3-number headline at dean
   altitude, layer detail on request) would steady it.

## Method notes (for the Phase-2 infra owners — I did NOT edit the eval infra)

- **Capture was tightened** (driver prompts record denominators/derived magnitudes and `view_link`
  faithfully). This is what surfaced the standing V gap. Recommend documenting a capture convention so
  runs are comparable.
- **Pre-gate false-positive families still fire** (verified, NOT DOCTRINE failures — do not triage as
  such): `no_invented_score` mis-fired on attractive-r3 where the analyst DISAVOWS a blend ("…rather
  than folding them into one blended **score**, because a single **score** would hide…") — the `_NEG`
  60-char window catches the first "score" but not the repeated second. `traceability` orphaned grounded
  derivations — "1 in 20" for a 5.1% share (plain-language) and "170" = 1,170−1,000 (strategic).
- **`view_link_offered` fires per-turn on every data call** (the envelope always carries a `view_link.url`),
  so it structurally demands offer-language on turns where offering would break concision (e.g. the
  two-sentence turn in concise-under-pressure). It nonetheless tracks the real V gap. Consider
  per-conversation semantics or a documented capture rule.
- **"feeds"/"feeding" verb ambiguity.** The banned NOUN ("feeder" / "feeding program") = **0 hits**. But
  the VERB "a program feeds occupations" appears in 4 transcripts (strategic ×3, teach ×2, premature ×1,
  attractive-r2 ×1); two judges flagged it as a doctrine breach, two did not. The ban's scope
  (noun-only vs. also the verb) should be settled in the DOCTRINE and the pre-gate.

## Frozen fixtures

Nine transcripts that cleanly pass (all I–V pass + all tensions balanced, + establishment pass for
onboarding, no contested "feeds" verb) are frozen as regression anchors in
`backend/evals/conversational/fixtures/`: attractive-occupations-r1, concise-under-pressure-r1/r2/r3,
greenfield-r1, out-of-scope-funding-r1, onboarding-cold-open/vague-identifier/grain-switch. (strategic-
programs-r1 graded clean but is withheld pending the "feeds"-verb scope decision.)
