---
name: find-live-postings
description: >
  Use this skill to evidence a role's live employer demand — for the role-selection workbench
  (test 5: do attractive employers post this title for these SOCs?) or the report's Employer
  Evidence section. It searches CareerOneStop per SOC (occupations.jobs.search_postings),
  scrapes the public CareerOneStop job site per SOC (tools/jobs/scrape_jobs.cjs — keyless),
  judges each listing on employer recognizability and SEMANTIC similarity to the chosen role
  title, and selects the best-evidencing postings per SOC — one per distinct employer, written as
  a LIST — or reports NONE, which is a signal the role is weak for that SOC. Triggers: "find live
  postings", "evidence the role", "fill employer evidence", "validate the role title against
  postings".
---

# Find Live Job Postings — the role's credibility anchor

For a chosen role (a title + its SOCs) and a region, find the REAL, current postings that best
evidence that *attractive employers hire for this role*. This is the credibility anchor of both
the role workbench (test 5) and the report's Employer Evidence section, and the one test that
can *fail* a role.

## The one hard rule

Postings must be REAL and CURRENT. Never fabricate a posting, employer, or link; never cite a
listing the search did not return. A stale or invented posting is worse than none — it breaks
the report's credibility spine. When nothing qualifies, the answer is **NONE**.

## NONE is a result, not a failure

If no recognizable employer in the region is posting the role title for a SOC, that is strong
evidence the role is WEAK for that SOC — maybe the SOC doesn't belong under this title, or the
title is wrong. Report it plainly; it *sharpens* the role selection, it doesn't break the skill.
NONE verdicts are the methodology's most informative output.

## Process

1. Take the role (title + SOCs) and the region (zip + radius; default radius 25 mi).
2. Pull the listings for each SOC (structured, real) from the PUBLIC CareerOneStop job site —
   no API key, no NLx agreement needed:
   ```bash
   node tools/jobs/scrape_jobs.cjs 17-3026 94022 25
   # → JSON: [{soc, title, employer, location, date, url}, ...]
   ```
   It drives the public site with Playwright (the listings are JS-rendered; the gated Jobs
   *API* would need NLx — this public path does not). If the scrape returns nothing, report
   that — do not invent postings. (zip + radius set the geography; the search is geo-filtered.)
3. Judge each listing on two axes — this is where your capability is essential:
   - **Employer recognizability** — an attractive, name-brand employer (Nvidia, Applied
     Materials, Northrop Grumman, Intel, J&J) vs a staffing agency or unknown. Bigger brand →
     stronger partnership signal.
   - **Semantic title match** — does the posting title *mean the same role* as the chosen
     title? Judge MEANING, not string overlap: "Manufacturing Technician" ≈ "Mask Manufacturing
     Technician" ≈ "Manufacturing Test Technician" (strong); "Process Operator" / "Assembler"
     (weak); a different domain (no match).
4. Select the strongest postings per SOC — **one per DISTINCT employer**, ordered strongest
   first — discarding stale (outside the recency window) or out-of-region listings. If nothing
   clears a sensible bar, record **NONE** for that SOC. `live_postings` is typed
   `dict[str, list[LivePosting]]`: `_employer_table` renders one row per posting and `rowspan`s
   the occupation cell, so a SOC with several recognizable employers reads as breadth of demand
   (see `svamp-industrial-machinery-mechanic`: 6 employers under 49-9041). Do NOT collapse to a
   single posting — that under-uses the schema and understates the employer base.
   **How far to stretch the title — three cases, in order of how often they come up.**
   - **LATERAL (same job, different employer vocabulary) → always take it.** When employers do
     not post the SOC's own title (49-9041 "Industrial Machinery Mechanics" — nobody advertises
     that; Applied Materials posts "Common Equipment Technician III"), semantic judgment is doing
     ESSENTIAL work and adjacent titles belong. Refusing here yields an empty table.
   - **VERTICAL (a different tier of the same vertical) → take it when the report is a PATHWAY,
     and say so.** 37-1012 is a First-Line Supervisor SOC, but no Bay employer posts a supervisor
     title — BrightView and Six Flags post "Landscaper I" / "Landscaper". Those are the jobs a
     Horticulture completer actually enters, with the supervisor seat as the promotion above
     them, which is exactly the `sectors.PROMOTION_SOCS` doctrine (the CC produces the line
     worker; the employer promotes). Carry them — but the occupation cell will print the SOC's
     formal title beside an entry-level posting title, so the framing must live in `lede` /
     `demand_note`. **Better still, when the report carries BOTH tiers as SOCs, place each
     posting on the SOC matching its tier** (the Foothill Veterinary report: Vet Assistant
     listings evidence 31-9096, the licensed-tech listing evidences 29-2056) — then no stretch
     is needed at all.
   - **SIDEWAYS INTO A DIFFERENT OCCUPATION → refuse.** When employers post the title verbatim
     (29-1126, where "Respiratory Care Practitioner" is the California licensure term and
     Stanford/Kaiser/Dignity all post it), any stretch is UNFORCED. Adjacent *specialties* that
     merely often employ the credential (Polysomnographic Technologist, Certified Hyperbaric
     Technologist) are a different occupation with its own certification. The table has no
     "adjacent" affordance: every row silently asserts *this employer hires for this role*.
     Three airtight rows beat five arguable ones — one challengeable row taints the rest.
     Career-breadth belongs in prose.
   **A NONE verdict renders as a BLANK ROW — write nothing.** A SOC with no curated posting
   renders `— —` (no employer, no link): the occupation stays visible in the table and the
   absence of evidence is the finding. Do NOT explain it in prose. The 37-3012 NONE was first
   written up as a clause in `demand_note` ("No current Bay Area postings were returned for SOC
   37-3012") and cut — it sat in the *demand* section while describing *employer* evidence, which
   read as confusing rather than informative. The blank row is self-explanatory where it appears.
   (Until 2026-08-27 the renderer filled the empty employer cell with the lens's top-ranked
   regional hirer — Coke Farm for 37-3012. That put "this employer posted this job" and "BLS
   staffing patterns rank this employer for this occupation" in one column, separated only by a
   missing link. Fixed in `_employer_table`; do not reintroduce an employer name without a
   posting behind it.)
5. Write the selections into `ReportSpec.live_postings` as
   `{soc: [LivePosting(employer, title, url), ...]}` using each posting's REAL employer, title,
   and URL. The def loader normalizes a bare dict to a one-element list, so a single posting
   still renders — but author the LIST form.

## Output

- The curated `{soc -> [LivePosting, ...]}` for `ReportSpec.live_postings`.
- A one-line per-SOC verdict for the role workbench: `employer · title · match-strength` per
  selected posting, or `NONE`. The NONE lines are the role's weak spots — surface them, don't
  hide them.

## Running from a high-latency connection

`scrape_jobs.cjs` waits for `networkidle`, which never settles within its timeout on a
trans-Pacific link (the page itself is fine — it returns 200 in ~1.5s). If `page.goto` times
out, that is the cause, not a block: re-run with `waitUntil: 'domcontentloaded'` and a longer
timeout rather than concluding the site is unreachable.
