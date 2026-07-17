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

> A program is a supporting program for an occupation when it is **(1) a workforce program** [`is_vocational`,
> a program property] that **(2) genuinely prepares for that occupation** [a real crosswalk edge] and is
> **(3) currently active** [completers **or** enrolled students in the window] — **minus** the querying
> member's `charter_excludes`.
>
> Eligibility and supply are separate: condition 3 decides whether the program *appears*; **only completers
> count toward the supply number.** Enrollment makes a live program visible (a Plastics program with 222
> students is training people whether or not its first cohort has graduated) without ever inflating supply.

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
  Collapse eligibility to the universal rule + `charter_excludes` at the pinned 3-yr producing gate; extract
  `Composition`; delete the forks; build the sector→occupation / sector→program membership edges (retiring
  `home_divisions`), the per-edge crosswalk-quality property (retiring `excluded_tops`), and the member
  charter (SVAMP). Numbers move — measured: SVAMP drops **3 zero-supply program rows** (supply-neutral),
  SMCCD-adm gains **+1 program / +1 served SOC** from the window pin, A′ collapses — as ONE signed diff,
  regenerated goldens, because it's now a single-location change. Sequenced B1–B4 under **Path forward** below.
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

## Phase B — the curation redesign

### Problem statement

**Every WHAT must have exactly one denotation; where two denotations are both wanted, they are two named
units — not one ambiguous word.** The sharpest, live instance: "sector" carries two denotations (full-PCAH
occupation-set vs rule-effective/served subset), which is why the dashboard and `sector_overview` diverge.
Resolution shape: one **sector node** (its full occupation membership, explicit graph facts) + a
**served/effective lens** (the derived reachable subset) — two labeled projections of one engine, each
saying which set it is. Ties together with the eligibility decision (universal rule + SVAMP charter) and
sector-as-node (explicit occupation + program membership). Phase-B because it moves live numbers — reserved
from Phase A by the discipline.

### Status — partial ship + a reverted over-reach (lesson banked)

The **sector demand decomposition** (full / in-demand / served / effective) is live on the MCP
`sector_overview` text surface, where numbers carry meaning with no chart to lean on: `smccd-adm` reads
full 8,150/49 → in-demand 2,420/7 · served 1,930/13 → effective 1,240/4. A dashboard "ladder" restating the
same split was built and then **reverted** — the demand treemap already *is* the demonstration (its tiles
sum to the headline), so the ladder only re-cluttered a deliberately-narrowed view. **Durable rule: resolve
a seam where meaning is carried by bare numbers (text / API), not where a visualization already carries it.**

### Pressure-test (measured against the live graph, before any code)

Grounding corrections to the summary above:
- The demand/served **rule is already universal** (`_DEFAULT_RULE`; `_SECTOR_RULES` is empty). The "many
  forks" was really **two**: the `vocational` mode flag and SVAMP's `soc_rule=None`.
- `excluded_tops` is **already physically split** — 14 crosswalk-noise TOPs on the *sector*, 2 charter TOPs
  on *SVAMP*, zero overlap.

Measured verdicts (all hold):
- **Program eligibility subtracts cleanly.** `is_vocational` explodes SVAMP's in-scope 67 → 271 (+204), but
  crosswalk-intersected with its 12 occupations it collapses to **23 = 23** — zero sneak-ins, zero drops.
  SVAMP's division-09 gate is provably **redundant** with crosswalk + noise-correction, so `top_divisions`
  can delete.
- **The charter is 3 load-bearing items.** Automotive, HVAC, **and** Biotech each `is_vocational` ∧ reach an
  AM occupation → each would re-enter without explicit exclusion. Biotech was hidden by the division gate; the
  charter grows 2 → 3 exactly when that gate drops.
- **The occupation axis subtracts too.** SVAMP's 12 ⊆ the sector's 49 (0 additions).

### The completers window — PINNED: 3 years

Today the *producing gate* uses **latest-year-only** while the *supply measure* is a **3-year mean**
(`_SUPPLY_YEARS = 3`) — so a program can be "supply-positive yet not-producing," and the gate flickers on
biennial cycles. This is an incoherence, not a preference. **Pin condition 3 to the 3-year window** (align the
gate with the measure). Scope: the *eligibility gate* only — `resolve`, `landscape_programs`,
`quantities._soc_feeders`, `active_feeders` (~4 duplicated sites → collapse into one `is_producing(3yr)`
predicate). The latest-year **"graduating this year"** reading stays 1-year as the stamped complement (the
existing `on_the_books` / `graduating` dual).

The window pin *saves* 093400 Electronics & Electric (0 latest-year, 1 in 3yr — the fragility, caught in a
live program). Under awards-only the pin would still drop 3 SVAMP programs (092400, 095200, 095420) — but
that number is a mirage: see the enrollment correction below, which is why condition 3 is *active*, not
awards-only. (An earlier note said "7 dormant"; that was the *retained* count recorded inverted.)

### Enrollment — condition 3 is "active," not "producing" (the correction that matters)

The three programs an awards-only rule would drop are **not dead** — measured, they hold ~480 currently-
enrolled students (Plastics 222 · Construction Crafts 139 · Engineering-Tech-General 121, all into 2025).
Awards-only would erase live training capacity and read a being-addressed gap as unaddressed. So condition 3
is **active = recent completers OR recent enrollment** (both at the 3-yr window); **supply stays completers-
only**. Consequences:
- **No lifecycle label.** "Enrolled, 0 recent completers" is ambiguous — genuinely new, *missing awards data*
  (the exports have holes both ways: Machining shows 49 grads/yr but 0 enrollment on record), or stalled. We
  can't tell, so we don't narrate it — we show the two grounded facts (enrolled N · completers M) and let the
  reader judge. This also dissolves the "zombie program" worry: there is no claim to be wrong about.
- **It's a union, not enrollment-first** — a program appears if *either* signal is present (so a
  producing-but-not-enrollment-reported program like Machining is never erased).
- **This is why enrollment is not scope creep but a requirement.** SVAMP shows enrolled programs today; an
  awards-only universal rule would either *regress* SVAMP (lose the 480 students) or keep it *forked*. The
  active rule lets SVAMP's behavior *become* the universal behavior — leveling up, not down.

**Corrected blast radius.** SVAMP drops **0** programs (its 3 non-graduating ones have enrollment → shown
active-not-graduating; only genuinely-dead rows, none AND no enrollment, would drop). The movement is the
other direction: **rule-bearing instances (SMCCD, BACCC) — which today drop enrollment-only programs — gain
"active-not-graduating" rows.** Supply numbers move nowhere. That measured, per-instance diff is Step 2's
sign-off artifact.

### SVAMP's occupation set is authored, not derived (the last pin, resolved)

No lens reproduces the curated 12. It *contains* the rule's effective core (all 4) but overlays the
director's judgment: **+8** below-threshold / single-college occupations (Machinists, Semiconductor, CNC×2,
Calibration, Eng-Techs…) and **−Welders** (real Bay demand, deliberately out of charter). Under the 3-year
window two of the "unserved" recover (Semiconductor, Calibration); **Machinists stays out for a real reason**
— only one SVAMP college graduates them, so it fails the ≥2-college consortium floor. That is precisely the
case where the director's local knowledge overrides the rule's signal. **Conclusion: the 12 is explicit
authored membership, not a rule output — and that is fine, because it is a subset of the grounded 49
(subtraction), so it feeds the one engine as data, never as a fork.**

### The Composition — one authoring mechanism for every member

The generalization (Dayone's): SVAMP is not special; it is the **first author** of a per-member composition
that any consortium can supply. Every member's scope is one small object:

```python
@dataclass(frozen=True)
class Composition:
    """How a member narrows a sector to its charter — the ONLY per-member scope knobs. Each is a SELECTION
    from a grounded universe, never a new fact or rule. None/empty ⇒ DERIVED by the universal lenses
    (today's behavior); a value ⇒ AUTHORED. The engine is identical either way; provenance is implicit."""
    occupations: tuple[str, ...] | None = None      # None → derived lens; tuple → authored ⊆ Sector.membership
    program_excludes: frozenset[str] = frozenset()  # charter subtraction ⊆ Sector.vocational universe
    program_includes: frozenset[str] = frozenset()  # (reserved, empty) additions ⊆ is_vocational; unused today
```

The 18-field `LandscapeSpec` sorts into four homes — a thin **Spec** (identity + WHO + employer config), a
reference to the grounded **Sector** (full membership + the universal rule + crosswalk-noise + home-divisions
+ swp_tag), a small **Composition**, and a **deleted** pile (the forks):

| current field(s) | → home |
|---|---|
| `id`, `name`, `accent`, `colleges`, `published`, `counties`, `top_n`, `employer_threshold`, `max_radius` | **Spec** |
| `sector`(label), `swp_tag`, `home_divisions`; full membership half of `socs`; crosswalk-noise half of `excluded_tops` | **Sector** |
| member subset of `socs`; charter half of `excluded_tops` | **Composition** |
| `soc_rule` (→ one universal rule), `vocational`, `cte_only`, `top_divisions` | **DELETE (forks)** |

**How the engine consumes it — identical for authored and derived:**

```python
def resolve_scope(colleges, sector_id, comp) -> ResolvedScope:
    sector = SECTORS[sector_id]                 # grounded: .membership, .rule, .crosswalk_noise, .home_div
    validate(comp, sector)                      # the guardrail (below)
    eligible = {t for t in offered_programs(colleges)          # (1) ONE universal program rule…
                if is_vocational(t) and t not in sector.crosswalk_noise
                and t not in comp.program_excludes              #     …minus the AUTHORED charter
                and is_producing(colleges, t, window=3)}        #     …at the pinned 3-yr gate
    occ = comp.occupations if comp.occupations is not None \    # (2) authored subset, else…
          else effective_lens(sector.membership, eligible, colleges)   #    …derived (today's effective set)
    return ResolvedScope(colleges, occ, eligible, sector)
```

Everything downstream — `select → subgraph`, `aggregate → value`, and the in-demand/served/effective
decomposition (now computed over `occ` as *annotations*: "of your 12, these 4 are in-market & served") — is
identical whether `occ` was authored or derived. **That is the one-engine invariant made structural.**

**The guardrail — why authoring can never become a fork:**

```python
def validate(comp, sector):
    assert comp.occupations is None or set(comp.occupations) <= set(sector.membership)   # select, don't invent
    assert comp.program_excludes <= sector.vocational_universe                            # subtract, don't invent
    assert comp.program_includes <= is_vocational_universe()                              # grounded additions only
```

There is **no field** for a new rule, threshold, occupation, or edge — every authorable value is a subset of
a grounded set, so the model *structurally cannot express a fork*. Authoring is expressively limited to
**selection from grounded facts**. Two invariants this preserves: **one denotation** ("AM" always = its 49-
occupation membership; a composition is a *labeled lens* over it, never a redefinition), and **transparency**
(an authored scope is an editorial choice, so it is *disclosed* — the principled version of "show the
narrowing," warranted for authored sets precisely because no chart derives them).

SVAMP and SMCCD, in the new model:

```python
Spec("smccd-adm", colleges=SMCCD, sector_id="adm", composition=Composition())              # fully derived
Spec("svamp", colleges=SVAMP, sector_id="adm", counties=("Santa Clara",),                  # authored, same shape
     composition=Composition(occupations=_AM_12,
                             program_excludes=frozenset({"094800","094600","043000"})))
```

SVAMP stops being a bespoke 18-field spec with `soc_rule=None` + `vocational=False`; it is the *same* thin
Spec plus a two-field Composition. The forks are deleted; the difference is data.

**Deleted throughout:** the stamp/`predicate_version` fields, any additivity-contract machinery, the
coherence-contract manifest, and the bespoke-spec registry. The refactor's net line count goes down.

## Path forward — sequencing to the realization

The organizing rule still governs: **never move code and numbers in the same step.** Phase B splits into
four moves, each shippable and guarded by the characterization net.

- **B1 — `Composition` as data (structural; numbers UNCHANGED).** Introduce `Composition`; migrate every
  member's scope onto it. Derived members (SMCCD, …) become `Composition()` (a pure rename, `occupations=None`).
  SVAMP's authored 12 + charter become a `Composition`, but a quarantined legacy shim keeps the engine
  computing SVAMP's *current* Mode-B numbers so output stays byte-identical. Outcome: one scope model, forks
  removed from the spec *shape*, numbers unchanged. Net-guarded. This is the "move code" step.
- **B2 — flip the universal rule (semantic; numbers CHANGE, ONE signed diff).** Remove the legacy shim: every
  member runs `is_vocational` + charter + the **active** gate (completers OR enrollment, 3-yr window); supply
  stays completers-only. Numbers move as measured *before flipping*: SVAMP drops **0** programs (its 3
  non-graduating ones stay, shown active-not-graduating), rule-bearing instances **gain** active-not-graduating
  rows, supply figures unchanged, A′ collapses. Regenerate goldens; director sign-off on the new "active" rows
  and SVAMP's status labels. This is the "move numbers" step, isolated.
- **B3 — selection into the graph (structural again; numbers UNCHANGED).** Move sector membership (occupation
  + program) and crosswalk-noise onto graph edges/properties — the sector-as-node endgame. Bootstrap the edges
  from the current computed sets so it is behavior-preserving; reconcile against an authority later. Net-guarded.
- **B4 — sector node + authored-scope disclosure.** Sector as a first-class node entering the coordinate as a
  WHAT-selector; surface the transparency disclosure for authored compositions ("tracks 12 of 49; −Welders;
  +Machinists beyond the market signal").

**Deferred, on purpose (no speculative tooling):** the self-serve *authoring UI*. Today the demand for
authoring is **N = 1** (SVAMP); we author its composition from the director's charter as data. The model is
fully general without the editor — add the editor when a second consortium actually needs to author
(`N ≥ 2`). Generalize the substrate now (free); defer the tool until the need is felt.

## Step 3 — the graph ontology (design)

Steps 1–2 cleaned the *engine*; Step 3 moves the *ontology it reads* from Python + CIP files into the graph,
so the sector boundary, the crosswalk, and each member's authored scope become **facts the engine traverses**
rather than logic it runs. The argument for doing it now is not elegance — it is the ceiling the code-based
ontology puts on three things the roadmap points straight at: **agentic reasoning** (the MCP agent can only
walk paths the verbs expose; a graph lets it answer questions no form anticipated), **new views** (a
cross-sector leaderboard or greenfield map is a query, not a bespoke form), and **authoring** (a `Composition`
in code needs a developer + deploy per edit; as graph edges the director self-serves, and "selection not
invention" stops being a runtime check and becomes structurally impossible — an edge can only point to a node
that exists). Foundations are cheapest to lay while the model is tiny (3 live sectors, ~97 occupations) and no
authored user data exists yet to migrate.

### Schema

New nodes: **`Sector{id,label,swp_tag}`** (first-class; enters the coordinate as the WHAT-selector);
**`ProgramFamily{top6,title,vocational}`** — the TOP-code program *type*, the grain the crosswalk and sector
membership live at (`Program-[:INSTANCE_OF]->ProgramFamily`; `vocational` was `is_vocational`);
**`Composition{member,sector}`** — a member×sector's authored narrowing (was the per-instance dataclass).

New edges:
- **`ProgramFamily-[:PREPARES_FOR]->Occupation`** — the faithful TOP→SOC crosswalk, materialized once (was
  `top6_to_soc`, in CIP files). Never hand-edited.
- **`Sector-[:CONTAINS]->Occupation`** — the sector's occupation membership (was `SECTORS[sid].socs`).
- **`Sector-[:OFFERS]->ProgramFamily`** — the sector's *program* membership: `vocational` families that prepare
  for a contained occupation, **minus the noise**, minus the home-division gate. Bootstrap verified exact
  (adm: 56 vocational-reaching → drop 14 noise → 42 offered). This edge *is* the noise-correction — a spurious
  family (Commercial Music for AM) simply has no `OFFERS` edge — which retires `excluded_tops` and the Step-2b
  mirror entirely.
- **`Composition-[:INCLUDES]->Occupation`** — the member's authored occupation subset (absent ⇒ derived, the
  default). SVAMP's 12.
- **`Composition-[:EXCLUDES{reason}]->ProgramFamily`** — the member's charter (SVAMP: Auto/HVAC/Biotech), each
  with a stated, queryable reason.

Eligibility becomes one traversal: a member×sector's supporting programs for an occupation = the colleges'
`Program`s whose `ProgramFamily` the `Sector` `OFFERS` and that `PREPARES_FOR` the occupation, minus the
`Composition`'s `EXCLUDES`, that are active (AWARDED/ENROLLED in window).

### Two design calls (the ones with tension)

1. **Noise is sector→program membership, not a universal crosswalk property.** An earlier note framed
   `excluded_tops` as a per-crosswalk-edge quality flag. But the exclusions are *sector-relative* — Commercial
   Music → 17-3023 is noise *for AM* (grads flow to media) yet a legitimate media program elsewhere. So the
   correction lives on `Sector-[:OFFERS]->ProgramFamily` (a curated membership), not on the universal
   `PREPARES_FOR` edge. The faithful crosswalk stays faithful; each sector says which of its links it counts.
2. **`ProgramFamily` exists to de-duplicate the TOP6 grain** — a top6 offered at five colleges is one family,
   one crosswalk edge, one OFFERS edge, not five.

**Edge-name note (shipped):** the schema above names `PREPARES_FOR`/`CONTAINS`/`OFFERS`; the course layer
already owns those, so the ontology ships as **`CROSSWALKS_TO`** (ProgramFamily→Occupation), **`COVERS`**
(Sector→Occupation), **`SCOPES`** (Sector→ProgramFamily).

### HOME_SECTOR — the DataVista classification layer (added; rejected as the supply set)

A third fact, distinct from both `COVERS` (occupation membership) and `SCOPES` (feeder set): the DataVista
(CCCCO PCAH) "TOP Codes to Sectors" publication assigns each TOP6 exactly one **home sector** (1:1; 274
families → 13 clusters). Materialized as **`ProgramFamily.home_sector`** (an our-Sector-id string, or
`unclassified`), git-authoritative from the already-committed `TOP Codes to Sectors.xlsx` via the existing
`_load_pcah_cte_top6` reader (already consumed by `opportunity.py`). A property, not an edge — one value per
family.

**Decision (measured): DataVista is the CLASSIFICATION authority, NOT the supply set.** Enshrining it as a
sector's program membership was rejected: a program has one home but *feeds* occupations across sectors, so
using it for supply drops legitimate cross-sector feeders. Measured across all sectors, **28% of feeder
memberships would drop** (48% for AM) — e.g. Electro-Mechanical (093500) is home ECU yet trains AM's
electro-mechanical techs. Concretely SVAMP-as-DataVista would **lose Mission College** (its only AM program
is home-filed elsewhere) and ~23% of supply. Occupation supply is a fact tied to the occupation, not a
classification choice — so the feeder `SCOPES` stays crosswalk-derived.

**What `home_sector` buys, all from one property + a partition of `SCOPES` by home-match:** a strict
**CCCCO-official lens** (`home_sector = sector`), **cross-sector-feeder disclosure** (`home_sector != sector`,
labeled with its real home), **charter auto-derivation** (SVAMP's Biotech/HVAC/Auto are exactly distant-home
feeders), and a **noise-audit signal** (12 of 14 AM noise codes are distant-home ICT/Business). AM partitions
42 feeders → 22 native + 19 cross-sector + 1 unclassified (095690, absent from DataVista). Loaded + reconciled
**FAITHFUL** in 3a; supply/colleges untouched.

### Git-authoritative vs graph-authoritative (the line that makes this a foundation, not a cache)

| fact | source of truth | in graph |
|---|---|---|
| crosswalk (`PREPARES_FOR`), `vocational` | **git** (CIP files, CCCCO taxonomy) | materialized, read-only |
| demand / awards / enrollment | **data exports** (COE, DataMart) | materialized, read-only |
| sector `CONTAINS` / `OFFERS` | **git** (bootstrapped from `in_scope`) | materialized, read-only |
| **`Composition` INCLUDES/EXCLUDES** | **graph** (the director edits it) | **authoritative** |

The value is the last row — the authored layer becomes editable data with a structural guardrail. Everything
above is a queryable materialized view of reviewed git/exports. The trap avoided: materializing git-truth with
*no* authoring layer would be a cache with a migration bill; the payoff is that authoring writes to the graph
while institutional truth stays git-reviewed (a graph→git export keeps the authored layer auditable).

### Phasing (byte-identical, then the value)

- **3a — materialize (no read change; numbers unchanged).** A committed loader builds every node/edge above
  *from the current code/files*, so the graph mirrors the code. Create the ~5% demand-less occupations as
  hollow `Occupation` nodes (soc+title, demand=0 — correct). A reconciliation test asserts graph == code for
  every sector / crosswalk / membership set.
- **3b — swap the reads (byte-identical, char-net-guarded).** One read at a time: `SECTORS[sid].socs` → the
  `CONTAINS` query; `in_scope` → the `OFFERS` traversal; `top6_to_soc` → `PREPARES_FOR`. At the end the engine
  reads the ontology from the graph, and the Python sector/crosswalk logic (`in_scope`, `excluded_tops`,
  `is_cte_top4_family`, `is_svamp_top`, the mirror) is deleted.
- **3c — flip the authored layer (the value; ships with the authoring UI, deferred to N≥2).** `Composition`
  becomes graph-authoritative: the director edits INCLUDES/EXCLUDES, the guardrail is structural, provenance
  rides each edge, and a graph→git export keeps the audit trail. Numbers move only when someone authors.

## Concluding the thread — the full closing map

To *truly* conclude the unified-engine thread, not just Step 3:

1. **Step 3 (above)** — the graph ontology. 3a/3b are byte-identical and retire the last Python sector/
   crosswalk logic + the `excluded_tops` mirror + `SVAMP_MANDATE` alias + `is_svamp_top` / `is_cte_top4_family`.
2. **Step 4 — sector as WHAT-selector + authored-scope disclosure.** With the sector a real node, finish it as
   the coordinate's WHAT-selector, and build the disclosure surface for authored scopes ("tracks 12 of 49;
   −Welders present-in-demand; +Machinists beyond the market signal") — the principled version of "show the
   narrowing," warranted because the scope is authored.
3. **The earned cleanup** — delete the coherence machinery the unification made unnecessary: the stamp /
   `predicate_version` fields (threaded through `provenance`/`envelope`), any additivity-contract remnants, and
   the corroboration test → now a *theorem* (identical coordinate ⇒ identical value, by construction; proven
   live by the 640.7 convergence). Net line count goes **down** — the whole point.
4. **Residues** — unify the member occupation set's two homes (`spec.socs` mirrors `composition.occupations`
   today; make the Composition authoritative), and retire the vestigial `top_divisions` / `cte_only` fields.
5. **Deferred beyond conclusion (own line, not blocking):** the self-serve authoring UI (N≥2), freezing the
   MEASURE family (confirm every figure maps to sum/difference/classify/rank/neighbors/attribute), and
   multi-region WHO.

Done state: one engine over one graph-native ontology; coherence structural at both the engine and ontology
layers; every consortium's view authored as data it cannot bend; the stamp/contract machinery deleted. The
plan doc becomes the record, and the corroboration test becomes a comment that says "see the theorem."

## 6. Decisions locked (from the deliberation)

1. Coordinate = `⟨WHO, WHAT, WHEN, MEASURE⟩`; region derived from WHO; WHAT is typed; MEASURE is a small
   fixed family.
2. Eligibility = universal three-condition rule + per-member `charter_excludes`; **subtraction, not fork.**
3. Automotive Technology *is* advanced manufacturing universally; SVAMP excludes it (and HVAC, Biotech) via
   a 3-item charter list — a genuine partnership scope, not a definition bug.
4. Sector = a native ontology node with explicit dual (occupation + program) membership, entering the
   coordinate as a WHAT-selector — edges, not rules.
5. Completers window = **3 years** for the eligibility gate (aligned with the supply mean); latest-year
   survives only as the separate "graduating this year" annotation.
6. Per-member scope = a **`Composition`** (authored occupation-subset + charter excludes/includes), validated
   as **selection from grounded facts** — authoring can subtract/select, never invent a rule, threshold,
   occupation, or edge. SVAMP is the first author; a self-serve authoring UI defers until a second consortium
   needs one (`N ≥ 2`).
7. Condition 3 = **active** (recent completers **OR** recent enrollment, 3-yr window), **not** completers-only;
   **supply stays completers-only**, so eligibility (does it appear) and supply (the quantity) are separate.
   No lifecycle label on enrollment-only programs — show the grounded facts (enrolled N · completers M), never
   narrate new/missing-data/stalled. This levels SVAMP's enrollment-awareness UP to universal instead of
   regressing it, which is what lets the fork delete cleanly.

## 7. Open questions

**Resolved this round (measured, pre-code):**
- ~~Completers window~~ → **pinned 3-year** (align gate with the supply mean; fixes the supply-positive-yet-
  not-producing incoherence).
- ~~SVAMP's occupation-set governance~~ → **authored membership** (no lens reproduces the 12; it is a valid
  subtraction from the 49, consumed as data, not a fork).
- ~~Dashboard scope in Phase A vs C~~ → **settled**: Phase A rewrote the MCP forms; the sector decomposition
  shipped on the MCP text surface; the dashboard needs no ladder (its treemap already demonstrates the total).

**Still open (resolve before/within their phase):**
- **Source of truth for sector→program membership** (B3). Bootstrap from the current computed `in_scope`
  sets, or source from an authority (CCCCO / regionalcte.org)? Likely: bootstrap, then reconcile.
- **The exact MEASURE family.** Enumerate and freeze the operation set (sum/difference/classify/rank/
  neighbors/attribute) and confirm every current figure maps to one — no residual bespoke measures.
- **Multi-region WHO.** Confirm `resolve_regions` handles demand summed over a region-set cleanly under the
  new `select`.
- **`derived` default semantics.** Whether `Composition(occupations=None)` resolves to today's `effective`
  set or a richer decomposed default — a UX call, does not block B1/B2.

## 8. Risks and sizing

- **Multi-week; Phase A is the bulk** (9 forms + the dashboard path). Bounded (reuses `quantities.py`
  primitives), staged (each phase shippable), and Phase A is number-preserving so its risk is contained.
- **Live prod, two surfaces.** MCP + dashboard share `quantities.py`, so they move together — but Phase B's
  number changes hit the live dashboard. Defensibility-sensitive: signed-off diffs, regenerated goldens,
  and awareness of any figure a stakeholder has already seen.
- **Number changes are real but small and measured** (superseding an earlier unmeasured "~2× swing"
  estimate). Program eligibility is byte-identical under the universal rule (23 = 23); the Automotive charter
  is already applied today, so it moves nothing; **supply figures do not move at all** (supply stays
  completers-only). The only movements are *which programs appear*: SVAMP drops 0 (the active gate keeps its
  enrolled programs), and rule-bearing instances gain active-not-graduating rows. Signed diff, regenerated
  goldens, director sign-off on the new rows + status labels.

## 9. Relationship to the rest

- **This IS the curation redesign's vehicle.** "Which views exist / what they contain" is selection; a new
  view becomes a projection over `select`/`aggregate`. The no-view regions from the diagnosis
  (sector-ranking, time-series, sector-greenfield, sector-wage) become cheap once the engine is unified.
- **The eval** stays as the behavioral gate; the coherence sweep (B-substrate) is *not built* — the refactor
  makes it unnecessary. The characterization net (Phase 0) is the refactor's own guard.
