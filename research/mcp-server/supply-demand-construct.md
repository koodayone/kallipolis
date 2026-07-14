# The Supply–Demand Construct — the cornerstone of the Kallipolis intelligence layer

A formal design spec. Workforce development, reduced to its load-bearing relation, is the
alignment of institutional **supply** (what colleges produce) with labor-market **demand** (what
the region hires). Every analysis Kallipolis performs — at the grain of a program, an occupation,
a sector, a college, or a region — is one view of a single relation:

> **supply against demand, projected across the TOP→CIP→SOC crosswalk, bounded by a sector,
> qualified by decision-modifiers, and compared against a reference set.**

This document formalizes that construct so that every form in the MCP conversational layer is an
*instantiation* of it rather than an independent feature — and so that its expressiveness and its
defensibility come from the same mechanism. Companion to `PLAN-PROMPT-epistemic-self-sufficiency.md`
and the canonical reading doctrine in `docs/domain/epistemic-contract.md`.

## The essence

Supply and demand at a single point is two numbers and a subtraction — not expressive. The
expressiveness comes from the **crosswalk that projects the relation across grains**, and the
defensibility comes from the **sector that bounds the projection to authority-backed edges**. The
cornerstone is therefore not "supply/demand" alone but the inseparable triple
**⟨relation, crosswalk operator, sector container⟩**, qualified into decisions and compared across
reference sets. Bounded enough to be defensible, generative enough to answer the practitioner's
whole question-space.

## 1. The two sides

- **Demand** is a property of **occupations** (SOC). Authority: Centers of Excellence, regional. An
  occupation carries {annual openings, projected growth, median wage, employment} as of a COE
  vintage, for the region. Demand is **regional by construction** — COE regionalizes; there is no
  institutional demand.
- **Supply** is a property of **programs** (TOP6). Authority: CCCCO DataMart completions (All
  Awards), as a 3-year projected average. A program carries completions per college per year.
  Supply is **institutional by construction** — specific colleges produce it.

The two sides live on different node types, in different authorities, at different grains. They do
not meet directly. What joins them is the crosswalk.

## 2. The crosswalk operator χ

The TOP→CIP→SOC crosswalk, **bounded to CTE by the PCAH sector classification** (the `is_vocational`
gate), is the operator χ that transports a quantity between the supply and demand sides:

- **χ↑ (demand projection): SOC → TOP.** A program's *addressable demand* is the full demand of the
  occupations it qualifies graduates for: `addressable_demand(program) = Σ_{soc ∈ χ(program)} demand(soc)`
  — the pool it is eligible to compete for (§8).
- **χ↓ (supply projection): TOP → SOC.** An occupation's *supply* is the completions of every program
  that qualifies for it: `supply(occupation) = Σ_{top ∈ χ⁻¹(occupation)} completions(top)`.

χ is **many-to-many by design**: a program genuinely qualifies graduates for several occupations, and
an occupation is genuinely served by several programs — an authoritative classification, not an
approximation. This is the source of the construct's expressiveness (one relation, projectable to any
anchor), and because these projections are *pools*, they are summed at full value, carrying no
epistemic penalty (§8). χ is the spine; supply and demand are what it carries.

## 3. The sector as the defensibility container

A **sector** is not a label on top of programs. It is the **crosswalk-closure of a PCAH-authorized
seed**: the set of TOP programs the Program and Course Approval Handbook designates as a labor-market
domain, together with the SOC occupations those programs reach through χ. Sector membership is
therefore **crosswalk-justified, not asserted** — a program or occupation is "in Health" because the
authorized crosswalk places it there.

This gives the sector three epistemic roles no other grain has:

1. **Defensibility boundary.** Across sectors, χ is noise (Liberal Arts → Machinists). Within a
   sector, χ is a coherent, authority-backed mapping. The sector is what makes a projection
   *defensible* — the containment that keeps the fan-out honest. Every projection in §2 is
   implicitly *within a sector*.
2. **Orientation altitude.** The practitioner reasons in sectors ("our Health programs"), not in TOP
   or SOC codes. The sector-anchored view of supply against demand is where a conversation should
   *begin its analysis* — it frames the space before disaggregating.
3. **Pedagogical surface.** The sector-anchored view is where the ontology becomes *visible*: "your
   five Manufacturing programs feed these twelve occupations; here is how your supply maps against
   the region's demand across them." The practitioner learns the ontology — the program↔occupation
   relation, projected-vs-actual, regional-vs-institutional — by *seeing a sector composed*.

## 4. Scope: (sector, member-set, region)

A supply–demand relation is evaluated within a **scope**:

- **Sector** — the domain (bounds χ).
- **Member-set** (supply extent) — {a single college | a consortium/district | all colleges in the
  region}. Determines whose completions count as supply, and is what makes *market-share* and
  *concentration* comparisons possible (§7).
- **Region** (demand extent) — the region the member sits in. Demand is regional, so the demand
  extent is (almost always) the region.

Scope is the conversation's memory: (member-set, sector) is what the practitioner establishes before
analysis, echoed on every response.

## 5. Anchor: three framings within scope

Within a scope, the **anchor** selects the altitude of the relation. The three are not separate
analyses — they are three projections of one relation within one scope.

| Anchor | Supply | Demand | The question it answers |
|---|---|---|---|
| **Sector** (aggregate) | Σ completions over the sector's programs | Σ openings over the sector's occupations | "How does my [sector] portfolio stack up against regional demand?" — the **orientation** view |
| **Program** (TOP6) | the program's completions | χ↑ addressable demand of its occupations | "Should I grow / start this program?" — the **narratively attractive** view |
| **Occupation** (SOC) | χ↓ supply of its feeding programs | the occupation's regional openings | "Is there a gap for this occupation?" — the **canonical gap** view |

The entry altitude is **intent-conditional**: a *portfolio / orientation* intent ("where am I best
positioned?", "how is my Health portfolio doing?") begins at the **sector-anchor home base** and
disaggregates from there; an *anchor-named* intent ("is there a gap for RNs?", "which employers hire
welders?") enters directly at the anchor its question names. The sector is universal *scope*, but
only conditional *scaffolding*.

## 6. Qualifiers: from gap to decision

A raw gap (demand > supply) is not yet a decision — a gap in a low-wage, declining, non-priority
occupation is a gap to *ignore*. The relation becomes decision-grade only when qualified by
{growth, wage, regional priority, college strength/share, openings volume}. Qualifiers are
**first-class**, not decoration: `unmet_demand` already encodes a wage floor, an openings floor, and
an education gate — it is *qualified* supply/demand. The construct's qualifiers must be as formalized
as the gap itself.

## 7. Comparison: the relational operators

The practitioner's real questions are comparative — they set the member's relation against a
reference set:

- **Market share of supply** — member supply ÷ region supply, within a sector-occupation. "Are we a
  significant supplier?"
- **Supply concentration** — how few colleges supply a demand target. "Do only a couple of schools
  serve this?"
- **Competitive overlap** — which other colleges serve the same targets. "Who else is in this?"

These are the **L2 synthesis forms**. They are not new primitives — they are the supply–demand
relation evaluated across a member-set instead of a single anchor.

## 8. The fan-out is not lossiness — it is a qualification classification, and you sum across

The TOP→CIP→SOC crosswalk is an authoritative **qualification** classification, not a probabilistic
estimate. It asserts that a graduate of a program is *qualified for* the occupations it maps to — all
of them — not that a graduate is fractionally distributed among them. Under that (correct) reading,
summing is exactly right and the fan-out carries no epistemic penalty:

- **A program's addressable demand** = the full sum of its qualified occupations' openings — the pool
  its graduates are eligible to compete for.
- **An occupation's supply** = the full sum of completions from every program that qualifies for it —
  the pool of newly-credentialed people who can fill it.

Both are *pools*, not exclusive assignments, and a pool is sized by summing. There is no
double-counting to avoid: the only operation that would double-count — summing program-addressable-
demands *across* programs into one figure — is not a meaningful quantity and is never performed. A
scope aggregate (sector demand, sector supply) is the sum of its **distinct** occupations' openings
and its **distinct** programs' completions, each real entity counted once at full value — which is
not discounting, only not counting one occupation twice because two programs reach it.

**Summing across is also what makes it defensible — because it is the authority's method.** The
Centers of Excellence sum across; Kallipolis's supply story is "COE's Annual Projected Supply method,
reconstructed on fresher, more complete data." Any fractional re-allocation would make our numbers
*diverge from COE's published ones* and break corroboration with the authority the number rests on.
Matching the institutional method, not out-analyzing it, is what "defensible" means here.

**Contestedness is a separate, cleanly-handled question.** An addressable pool is shared — other
colleges' graduates compete for the same openings. That is not expressed by discounting the demand;
it is exactly what the **comparison operators** (§7) express: market share (a member's supply ÷ the
region's supply into an occupation) and concentration say *how much of the pool a member can capture*.
So the construct carries two clean, fully-summed numbers — the pool (sum-across, COE-corroborated) and
the share of it (the comparison) — never one muddied allocated figure.

The fan-out's **width** is therefore descriptive context, not a reliability caveat: a program mapping
to many occupations is a broad credential; one mapping to few is specialized. Surface it as
information, not as a warning.

Beyond the fan-out, the construct inherits the contract's remaining obligations: **projected ≠
actual** (a 3-year supply projection vs a single year), **regional ≠ institutional** (the gap is
regional; a college's supply is its share), **absent ≠ zero** (a suppressed cell is unknown), and
**bind** every quantity to source · granularity · vintage — all deterministic in
`backend/partnerships/quantities.py`.

## 9. How this strengthens the MCP conversational layer

1. **The conversation gets a principled shape — a program-first descent.** The catalog's
   `next_moves` are soft determinism: guide rails, not a script. For an *existing-portfolio* intent
   the descent walks the ontology's spine in the practitioner's own order —

   > orient → **member_portfolio** (all sectors) → **sector_overview** (the member's programs + the
   > demand they address) → a **program** (its desirable occupations, ranked by demand/wage/gap) → a
   > single **occupation** → the **employers** behind it.

   It is **program-first** by design: the program is the practitioner's *lever* (they run, fund, and
   start programs; SWP funds programs), the occupation its *justification*. So `sector_overview` is
   program-**forward** — its rows are the member's programs, each carrying completions (supply) **and**
   addressable demand (the χ↑ sum over its occupations, so the program view stays supply/demand-
   grounded, not supply-only); occupations live in that addressable demand and are drilled from a
   program. The *greenfield* intent ("what should I offer that I don't?") has no program yet, so it
   enters occupation-first via `unmet_demand` — intent-conditional entry (§5), program-first for what
   exists, occupation-first for what's missing. Each node answers one question at its scope; the
   descent is turn-by-turn and practitioner-driven, never an open graph traversal.
2. **The forms become a systematic enumeration, not a wishlist.** Every form is a cell of
   {anchor × operation}. The current six map cleanly — gap = occupation-anchor; coverage =
   occupation × member-set comparison; pathway = the χ projection made explicit; occupation_profile =
   occupation-anchor full view; unmet_demand = occupation-anchor with supply = 0, qualified;
   regional_employers = the demand side's detail. The **missing** cells are the roadmap — most
   importantly the **sector-anchor aggregate** (the orientation view, today present on the dashboard
   but absent as a conversational form) and the **comparison operators** (market share, concentration).
3. **It educates by construction.** Because the sector-anchor view composes programs and occupations
   through the visible crosswalk, the practitioner learns the ontology's shape and its epistemic
   seams *by being oriented*. Pedagogy is a property of starting at the sector, not a separate mode.

## 10. Boundary: what is not the cornerstone

Supply/demand is the *first* organizing principle, not the only capability. A periphery attaches to
it but is not it: occupational KSAs, title selection for employer outreach, program-strengthening
advice, live postings (absent data). These *contextualize* a supply–demand decision; they do not
participate in the relation. The cornerstone claim is that every *analytical* move is a projection of
the construct — not that every capability is.
