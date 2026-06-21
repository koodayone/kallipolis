---
name: find-live-postings
description: >
  Use this skill to evidence a role's live employer demand — for the role-selection workbench
  (test 5: do attractive employers post this title for these SOCs?) or the report's Employer
  Evidence section. It searches CareerOneStop per SOC (occupations.jobs.search_postings),
  scrapes the public CareerOneStop job site per SOC (tools/jobs/scrape_jobs.cjs — keyless),
  judges each listing on employer recognizability and SEMANTIC similarity to the chosen role
  title, and selects the single best-evidencing posting per SOC — or reports NONE, which is a
  signal the role is weak for that SOC. Triggers: "find live postings", "evidence the role",
  "fill employer evidence", "validate the role title against postings".
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
4. Select the SINGLE strongest posting per SOC — a recognizable employer AND a close title
   match — discarding stale (outside the recency window) or out-of-region listings. If nothing
   clears a sensible bar, record **NONE** for that SOC.
5. Write the selections into `ReportSpec.live_postings` as
   `{soc: LivePosting(employer, title, url)}` using the posting's REAL employer, title, and URL.

## Output

- The curated `{soc -> LivePosting}` for `ReportSpec.live_postings`.
- A one-line per-SOC verdict for the role workbench: `employer · title · match-strength`, or
  `NONE`. The NONE lines are the role's weak spots — surface them, don't hide them.
