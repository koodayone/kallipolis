---
name: create-report
description: >
  Use this skill to create a workforce-pathway report end to end — a college/partnership
  report for a role (a title + its SOCs), like the Foothill "Manufacturing Technician" report.
  It orchestrates the layered report engine: scaffold the def, preview + curate the partner set,
  run the three enrichment skills (find-program-name, find-live-postings, curate-competencies),
  compose, then refine on the dialectic surface and consolidate. Triggers: "create a report",
  "new pathway report for <college> <role>", "generate a <role> report", "build the report for
  <member>". Pairs with: find-program-name, find-live-postings, curate-competencies.
---

# Create Report — the report engine, end to end

A report is generated, not written. The engine is layered and **def-driven**:

```
L0 ontology (Neo4j) ──build_lens──▶ L1 lens ──┬─▶ dashboard (explore)
                                              └─▶ report (persuade): def + propose_spec → build_report_html
```

**The invariant that governs everything:** the **def** (`backend/partnerships/saved_reports/{slug}.json`)
is the single source of truth. Every step either *proposes into the def* or *renders from it* — nothing
appears in the report that isn't traceable to the def or the lens. A scaffolded def renders a *complete*
report immediately (propose_spec fills every field); enrichment and curation only *refine* it.

**The seam to protect:** automate the plumbing, keep the judgment human. Three kinds of step —
*deterministic* (lens, partner-selection, render), *agentic* (the enrichment skills, which propose),
*editorial* (intake, curation knobs, prose voice). The agent drives the first two seamlessly; every
**GATE** below is a deliberate human act. Never emit an unowned document.

## The pipeline

### Phase 0 — Intake  ·  HUMAN decides
The irreducible editorial decision: **what the report is about.** Collect `member` (e.g. `foothill`),
`title` (the role, e.g. `Manufacturing Technician`), `sector` (e.g. `adm`), `socs` (the SOCs the role
maps to — authored on the PLAY, independent of the dashboard's sector rule, so no `sectors.py` edit is
needed for the report), optional `partnership` (charter, e.g. `svamp`), `author`, `date`.

### Phase 1 — Scaffold + partner preview  ·  deterministic, then GATE
1. `report.scaffold_report_def(member, title, sector, socs, partnership=…, author=…, date=…)` → write
   it to `saved_reports/{slug}.json` (slug = `report.report_slug(member, title)`).
2. Preview the partner set: `build_lens(member, play=Play(...), extra_colleges=charter)` then
   `select_partner_programs(lens.programs, charter, min_awards)`.
3. **GATE:** review the partner colleges. Tune `partner_min_awards` (the ≥-awards floor),
   `partnership` (the charter), or add a strategic college via an explicit `programs` override.
   Norm = BACCC breadth by size; charter = the exception; charter members with missing awards are
   carried by enrollment.

### Phase 2 — Enrich  ·  agentic (proposes), then GATE each
Run in parallel; write each result back into the def / cache:
- **find-program-name** (the partner programs) → `program_display_names.json` cache. GATE: eyeball the
  `medium`-confidence names + verified links.
- **find-live-postings** (socs + region) → def `live_postings` `{soc:{employer,title,url}}`. GATE: the
  NONE verdicts and the employer choices (real + recognizable, never fabricated).
- **curate-competencies** (socs) → def `competencies`. GATE: the KSA cut + the narrative.

### Phase 3 — Compose + render  ·  deterministic
Prose is auto-proposed by `propose_spec` with trust links baked in (O*NET, COE, DataMart, dashboard);
the def carries the enrichments + any prose overrides. Render at `…/report/saved/{slug}` (cp the def
into the container; rebuild the backend only if code changed).

**Before trusting ANY re-render, check for `{slug}.edited.html`** — the route serves it in preference
to the def, so a def change renders as a no-op and you will debug the wrong layer. Merely OPENING the
dialectic surface can create one (the page saves on input), so the shadow appears without a deliberate
edit. `ls` the saved_reports dir in the CONTAINER (that is what the route reads), not just the repo.
When one exists, diff it against a fresh generation before removing it —
`from partnerships.api import _generated_report_html` renders the def-driven HTML directly — then
consolidate any real prose edits and `POST …/revert`. Same trap, three places it bites: a silent
no-op re-render (Phase 3), a stale surface (Phase 4), a refused export (Phase 5).

### Phase 4 — Refine  ·  the dialectic surface, HUMAN voice
Open the endpoint; edit prose directly (⌘S saves to `{slug}.edited.html`; links open in a new tab).
**Consolidate:** read `{slug}.edited.html`, port any prose hand-edits into the def, then *revert*
(remove the edited.html) so the def is truth again. A stale edited.html masks def changes — always
diff before reverting (the alignment-note lesson).

### Phase 5 — Finalize
`tools/report-render/export.sh {slug}` → the verified `.docx` + `.pdf` deliverable: it renders the clean
`?raw=1` HTML, builds the native-crosswalk docx + the Playwright PDF, and **gates** on a link-parity check
(the docx-drift defense — a dropped link fails the build). **Precondition: the def is truth** — consolidate
any `{slug}.edited.html` into the def and revert first; export.sh refuses while an `edited.html` shadows the
def (`?raw=1` would serve the stale edit). Artifacts land in `tools/report-render/out/` (gitignored).
Commit the def + the program-name cache — **never** the binaries (regenerable from the def via `export.sh`).

## The def schema (the single source of truth)
Scaffolded (Phase 1): `member, title, sector, socs, author, date` (+ `partnership, partner_min_awards`).
Enrichments (Phase 2, written by the skills): `live_postings`, `competencies`.
Optional overrides (fall through to propose_spec when absent): `lede`, `demand_note`, `alignment_note`,
`competency_note`, `award_note`, `enrollment_note` (prose — embed trust links as `[label](url)` markdown,
rendered by `report._linkify`); `programs` (explicit `[[college,top6],…]` partner/strategic override);
`dashboard_url` (the tailored "{org} {sector} Dashboard" link).

## The credibility spine (hard rules)
1. **Data proposes, human confirms** — every field has a data default; the human owns the judgment gates.
2. **Real + verified** — postings real (find-live-postings), program names confirmed on an authority
   (find-program-name), every claim links to a named source. A fabricated trust link is worse than none.
3. **The def is truth** — regenerate from it; consolidate hand-edits; revert is safe.
4. **One substrate** — report and dashboard both render from the lens; they cannot disagree.

## How to evolve (extension points — keep each change localized)
- **New report** → run Phases 0–5.
- **New section** → a `_section` builder + a `*_note` field (linkify-aware) + a line in `build_report_html`.
- **New enrichment** → a skill (proposes) + a def field + a render hook + a GATE — never auto-trust it.
- **New trust link** → a row in `_sources_section`, or inline `[label](url)` in a note.
- **New partner knob** → `select_partner_programs` + a def param.
- **Export fidelity (the docx-drift trap)** → `.pdf` is a faithful Playwright print of the HTML
  (`shoot_pdf.cjs`, zero maintenance). `.docx` (`tools/report-render/build_docx.py`) is a *second*
  renderer that re-parses the HTML and maps elements **by CSS class** — so any new section or link
  pattern needs a matching handler there, or it is silently dropped/flattened in the Word doc.
  `tools/report-render/verify_docx.py` now automates the hyperlink-parity diff and **gates** `export.sh`
  (a dropped link fails the build, and it warns on a lost `<h1>` heading) — so the trap can no longer
  ship silently. A new *section* still needs its build_docx handler; after adding one, eyeball the docx.
