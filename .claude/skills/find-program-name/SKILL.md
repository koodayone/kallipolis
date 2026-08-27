---
name: find-program-name
description: >
  Use this skill to resolve the human-facing program name a California Community College markets
  for a (college, TOP6) pair — what replaces the bureaucratic state CIP/TOP6 label (e.g.
  "Machining and Machine Tools") with the college's real brand ("CNC Machinist") in the report's
  College Program Alignment crosswalk. It anchors on regionalcte.org (the CA Regional Consortia
  program-recommendation system — the authoritative college<->TOP<->program-name link), confirms
  the current name on the college's own catalog, and writes the result to the
  backend/partnerships/program_display_names.json cache. Triggers: "find the program name",
  "enrich the crosswalk names", "what does <college> call its <TOP> program", "refresh the
  program-name cache", or while wiring human-facing names into a pathway report.
---

# Find Program Name — the college's real brand for a (college × TOP) program

The graph carries the *state taxonomy* name for a program (the CIP/TOP6 label, e.g. "Manufacturing
and Industrial Technology"). A coordinator or the public knows the *college's brand* ("Smart
Manufacturing Technology"). This skill resolves that brand for a (college, TOP6) pair and caches it,
so the crosswalk speaks the audience's language instead of Sacramento's.

## The one hard rule

Report ONLY a name you actually saw on the college's own catalog. NEVER infer a name
from a job title or the report's SOC — that is the seductive failure mode (matching "094500" to
"Semiconductor Processing" because the SOC is semiconductor, rather than because Foothill's catalog
says so). A wrong program name tells an expert your analysis invents things; it is worse than the
dull-but-correct CIP label. When you cannot confirm, the answer is `null` + `confidence: low`, and
the report falls back to the CIP name.

## Why regionalcte.org is the anchor

regionalcte.org is the system of record for the *regional-recommendation* step every new CTE program
must pass. Each record carries `(college, TOP6, real program title, award type, region)` — exactly
the link we need. Caveats that shape HOW we use it: (1) it only logs programs that went through
regional recommendation (newer CTE), so a long-standing program may be absent — the college catalog
is the second leg that covers those; (2) the whole app is Cloudflare-walled (403 to non-browser
clients) with opaque token URLs and no public bulk export, so in practice it is reached via **Google's
index** (`site:regionalcte.org/browse "<College>" <TOP6>`), and the college's own catalog is the
accessible workhorse that confirms the name and its currency.

## Process (one agent per (college, TOP6); fan out in parallel)

Give the finder agent ONLY: the college, the TOP6 code, and the state CIP/TOP6 name. Deliberately
withhold the SOC/job title so it cannot cheat by matching the name to the role. The validated prompt:

> Find the public-facing program name **{COLLEGE}** uses under California TOP code **{TOP6}** (state
> taxonomy name: "**{CIP_NAME}**"). College domain: {DOMAIN}.
> PRIMARY: regionalcte.org (authoritative college↔TOP↔name; Cloudflare-walled but Google-indexed) —
> query `site:regionalcte.org/browse "{COLLEGE}" {TOP6}` (+ area-word variants). CONFIRM + check
> currency on {COLLEGE}'s own catalog/site. Do NOT infer a name from any job title/SOC — only report
> a name you actually saw. If {TOP6} maps to several programs, list them and flag which best matches
> "{CIP_NAME}". If nothing clear: `confidence: low`, `program_name: null`. Keep the reply under ~120
> words: one line of reasoning, then a `RESULT` block with `program_name / award_type / source_url /
> confidence / note`.

Confidence calibration: **high** = read directly on the college's official catalog and/or
regionalcte.org; **medium** = name confirmed on the college site but the TOP↔name link inferred from
search snippets (Cloudflare blocked the direct regionalcte.org read); **low** = uncertain → `null`.

## Output — the cache

Write each result to `backend/partnerships/program_display_names.json` under
`names["<exact graph college name>|<TOP6>"] = {name, cip, award_type, confidence, url}`. The report
loads this and renders `name` in the crosswalk; any (college, TOP6) absent from the cache falls back
to the CIP/TOP6 name. Eyeball the `medium`s before trusting them in a shipped doc.

## Cost & the bulk alternative

Measured ~20–28k tokens and ~1 min per program (≈16 tool calls). For the dozen programs in one
report that is a ~one-time pass, then cached — never re-paid unless refreshed. If you ever need the
WHOLE state table (all colleges, every TOP) rather than a report's handful, the two routes are: a
headless-browser crawl of regionalcte.org (the repo already has Playwright; Cloudflare is the
obstacle), or emailing support@regionalcte.org for export/API access — which collapses the crawl
into a single authenticated download. Do not attempt a plain-HTTP scrape; it 403s at the edge.
