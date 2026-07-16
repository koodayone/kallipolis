# Verb-Surface Validation Brief (post-#126)

**Read this first, then run the conversational eval (`/conversational-eval`).** It adds the
verb-surface-specific framing to the general protocol in `run.md` / `SKILL.md`. Full strategic context
lives in the memory `project_verb_surface_next_phase.md` (auto-loaded).

## What shipped (PR #126)
The 11 task-shaped MCP tools were replaced by the coordinate-algebra surface — **5 verbs**
(`orient · navigate · crosswalk · compare · sweep`) **+ `list_institutions`**. The kernel was unified
(one birthplace per figure; dashboard⇄MCP seam closed). The **curation layer** — the 11 internal
form-ids / designed views behind the verbs — is **UNCHANGED (inherited)**.

## The aim of this eval: DIAGNOSIS, not validation
You cannot "validate" a curation we intend to redesign. This run does two separable things:
1. **Ship-gate (transfers to the target):** does the analyst translate *intent → verb + coordinate*, and
   do the numbers hold? Surface + kernel — view-independent.
2. **Gap-map (drives the redesign):** where does the *legacy curation* under-serve the verb surface? This
   is the required input to the first-principles curation redesign — it is why running against the
   inherited views is correct, not wasted.

## Preconditions
- **Deployed surface = exactly 6 tools** (`orient · navigate · crosswalk · compare · sweep ·
  list_institutions`). Confirm via the connector. If you still see `supply_demand_gaps` /
  `occupation_profile` / `sector_overview` / etc., the deploy or your binding is stale — **STOP**.
- **Fresh session** (MCP tools + DOCTRINE bind at session start; a stale session tests the old surface).
- Seed graph up: `eval-neo4j` on `bolt://localhost:7691`.

## Run (per `SKILL.md`), with these emphases
1. **Tier A** substrate gate — green before grading any prose.
2. **Pathway loop** over the verb surface. **Force faithful tool-call capture** (verb + args + order);
   routing analysis depends on it, and self-report is the harness's main risk.
3. **Deterministic pre-gate (`checks.py`) is the PRIMARY signal.** Run **N reps/pathway** (tool selection
   is stochastic — one sample is noise). Focus on: routing loops (a whole-institution ask → one `orient`,
   not looped `navigate(sector=…)`), moves-to-target, selection validity, and whether it walked the
   next-moves.
4. **Judge** = backstop (predicted ≈flat — forms and figures didn't change; a prose-principle shift is a
   surprise worth halting on).
5. **A/B:** diff the deterministic metrics against the `#123` baseline (`LAYER3-RUN-BASELINE.md`).

## The hypothesis to target
The verb surface may **regress routing on portfolio / multi-sector asks**, because the `_ROUTING`
anti-loop steering ("reach for this FIRST… do NOT loop sector_overview") was deleted with the legacy
tools. Stress the portfolio pathways specifically.

## Triage EVERY finding before acting on it
- **Surface-mechanic** (a verb/description under-advertises — the model can't tell `navigate(lens=gaps)`
  is a thing) → **fix now.** If it's the lost steering, fold it into the `orient`/`navigate` descriptions
  (the **B′** run; B vs B′ isolates lost-hints from the abstraction itself).
- **Curation-artifact** (the finding exists only because two legacy views — e.g. `member_portfolio` vs
  `sector_overview` — sit at awkward granularity) → **DO NOT patch the description.** Log it for the
  redesign. Patching curation defects into verb descriptions would entrench the legacy view-set.

## Output
- **Ship verdict:** routing flat-or-better + judge flat ⇒ the affordance bet held; freeze the verb
  pathways as regression fixtures.
- **The gap-map:** which of the 11 inherited views are genuinely distinct designed answers, which are the
  same view under a lens, and which valuable regions of the ⟨member · sector · entity · lens · vintage⟩
  question space have **no** view at all — the input to the curation redesign (the actual product work).
