---
name: evaluate-program
description: >
  Use this skill to produce a PROGRAM EVALUATION report — an evidence pack for one
  (college, TOP6) program, angled at the CCC program-review cycle: throughput (enrollment
  vs awards), the destination occupations the program's crosswalk actually reaches, live
  employer demand, competency targets for curriculum alignment, and peer standing against
  other colleges running the same TOP. The subject is the PROGRAM, not a job title.
  Triggers: "evaluate the program", "program evaluation for <college> <TOP>", "program
  review report", "how is <college>'s <program> doing". Sits ALONGSIDE create-report
  (which is role-first and outward-facing); this one is program-first and inward-facing.
---

# Evaluate Program — the program-first evidence pack

`create-report` answers *"is there demand for this role, and who supplies it?"* for an
outward audience. This skill answers a different question for a different reader:

> **"How is this program performing, and what does the evidence say about it?"**

Subject = **(college, TOP6)**. Audience = deans, program review, curriculum committee.
Same substrate (L1 lens → def → `build_report_html`), inverted unit of analysis.

## The two hard rules

1. **Evidence-forward, NO verdict.** Never write "at risk", "underperforming", "should be
   sunset". Present throughput, trend, destination health and peer standing so the judgment
   is obvious — and leave it to the reader. This is the house posture (*data proposes, human
   confirms*), and it is what makes the document usable inside an institutional process
   rather than something to argue with.
2. **The destination SOCs are DERIVED, not authored.** In a role report the author picks the
   SOCs, which silently filters crosswalk junk. Here the program picks them, so the filter
   must be explicit (below).

## Deriving the destination occupations

```
destinations(TOP6) = crosswalk(TOP6)
                     ∩ SECTORS[home_sector_by_top6(TOP6)].socs     # middle-skill membership
                     − ALL_OTHER_SOCS − PROMOTION_SOCS − EXPERIENCE_5YR_SOCS
```

Reuses the guards that already exist (`partnerships.sectors`) rather than inventing a rule.
Validated 2026-08-27 — it reproduces hand-authored SOC sets exactly:

| TOP | raw | derived | what the filter removes |
|---|---|---|---|
| 121000 Respiratory Care/Therapy | 4 | **1** (29-1126) | Postsecondary Teachers, "All Other", 99-9999 |
| 010210 Veterinary Technician | 10 | **2** (29-2056, 31-9096) | managers, receptionists, teachers |
| 126100 Community Health Care Worker | 5 | **1** (21-1094) | managers, 99-9999 |
| 093400 Electronics & Electric Tech | 21 | **7** | managers, first-line supervisors, degreed engineers, professors |

`093400` is the stress case — 21 raw SOCs down to 7 coherent technician occupations. Run any
new program through it and eyeball the dropped list before trusting the kept one.

If the derived set is EMPTY, that is a finding, not a failure: the program has no middle-skill
destination in its own sector. Report it plainly.

## Sections — same evidence as the role report, re-angled

The renderer needs NO code changes for v1. The subject shift is carried by `org_name` +
`title`; the re-angling is carried entirely by the prose override fields.

| Section | Role report frames it as | Program evaluation frames it as |
|---|---|---|
| Header | "{College} Workforce Pathway : {Role}" | **"{College} Program Evaluation : {Program} (TOP {n})"** (set `org_name`) |
| Demand | "is there demand for this role" | **destination-market health** — where completers go, is it growing |
| Employer Evidence | "prominent employers want this — partner with us" | **destination employers + advisory-committee candidates**; a NONE verdict is a real signal about the destination market |
| Competencies | "here is what the role demands" | **curriculum-alignment target** — what the course outline must cover |
| Alignment / crosswalk | many colleges → one occupation | **this program → its destination occupations** |
| Award + enrollment trends | supply context | **THROUGHPUT — the core section.** Enrollment vs awards is the completion story |
| Sources | same | same |

**Do not cut Employer Evidence or Competencies.** They are more load-bearing here than in the
role report: program review requires labor-market justification (SWP / Perkins), those named
employers are the advisory-committee shortlist, and the KSA grid is the curriculum-alignment
target. The persuasion lives in the *prose wrapper*, not the evidence — rewrite the wrapper.

## Voice — the prose rules

The generated prose runs verbose by default. These are the corrections applied 2026-08-27, in
priority order. They cut roughly half the words without losing a fact.

1. **No meta-commentary about the document.** Never "It reports the evidence; it does not render
   a judgment", never "read together, these are the program's throughput record". Evidence-forward
   is the POSTURE — announcing it wastes a sentence and sounds defensive.
2. **No methodology in reader-facing prose.** Which SOCs the crosswalk dropped and why belongs in
   the def's `_comment`, not the page. The reader wants the finding, not the derivation.
3. **Name it directly.** "leads to SOC 29-1126" — not "leads to a single middle-skill destination
   occupation in the Centers of Excellence middle-skill universe".
4. **No characterization.** Drop "growing and high-wage", "steady", "the region's largest
   producer". State the figure and let it land: *"conferred 48 awards in 2024–25, against 68 in
   2020–21."*
5. **No cross-document superlatives.** "the highest median of any occupation in Foothill's
   evaluations to date" assumes a reader who has read the others. Each report stands alone.
6. **Short sentences.** Two plain sentences beat one stacked with an em-dash and a semicolon.
7. **Name the TOP exactly once in the lede, never in `title`.** `title` reaches the masthead,
   where a code is clutter — keep it to the program's own name. But the lede's first sentence
   SHOULD carry `(TOP nnnnnn)`: it is the key a reader needs to find the program in DataMart or
   in program-review paperwork, and it bridges the college's brand to the state label the peer
   table keys on. That bridge matters most where the two diverge — Foothill markets `010900` as
   "Environmental Horticulture and Design" while the state calls it "Horticulture", so without
   the code the document is unlookuppable. Naming a TOP again later is fine when the TOP is the
   subject: *"The set of colleges offering TOP 010900 in the Bay Area"*.
8. **A table caption describes the table; it does not restate the table.** The award and
   enrollment notes are captions — *"Award trends for each member-college program. Empty cells
   indicate no data reported via DataMart."* Do NOT narrate the figures ("conferred 48 awards
   against 68 five years earlier, while Skyline moved from 70 to 84"). The reader is looking at
   the numbers. Restating them is the most common way this document gets bloated, and it quietly
   turns a caption into an argument.
9. **A section whose table speaks for itself needs no note at all.** `competency_note` is empty
   on the Foothill 121000 evaluation: the KSA grid is self-explanatory and the intro only
   described what the reader can see. Empty notes render as nothing — no orphan paragraph.
10. **Situate, do not rank.** Write peers as context, never as a contest: *"in the context of
    other colleges offering the same program"*, NOT *"compared against"*. This is not a
    tightening — comparative framing implies a standing to be judged against, which smuggles
    back the verdict the whole document is built to withhold. Same reason "the region's largest
    producer" was cut from the award caption: the table already ranks; the prose need not.
11. **Keep the trust links.** They cost no words and the credibility spine requires them. Prefer
    the house formula: *"[According to the Centers of Excellence](url), this occupation demands
    roughly N openings a year at a median salary of $X."*

**The canonical lede**, settled over four rounds of editing — start here rather than composing:

> This evaluation assembles labor-market supply and demand evidence for {College}'s {Program}
> program (TOP {nnnnnn}). It covers regional occupational demand targeted by the program, and the
> program's award and enrollment trends in the context of other colleges offering the same program
> in the region.

Note *"labor-market supply and demand"*, not *"labor-market and supply"* — the earlier draft
implicitly equated "labor market" with demand alone and left supply dangling beside it. The two
axes are supply (programs, awards, enrollment) and demand (occupations, openings, wage); name both.

Worked example — 61 words to 32, same facts:

> ~~Foothill's Respiratory Therapy program leads to a single middle-skill destination occupation in
> the Centers of Excellence middle-skill universe. The crosswalk from TOP 121000 also reaches
> Postsecondary Teachers and a residual "all other" classification; both fall outside that universe
> and are excluded here. The destination market is growing and high-wage: 210 openings a year in the
> Bay Area at a $132,040 median, the highest median of any occupation in Foothill's
> advanced-manufacturing, agriculture or health evaluations to date.~~
>
> Foothill's Respiratory Therapy program leads to SOC 29-1126 via the TOP–CIP–SOC crosswalk.
> According to the Centers of Excellence, this occupation demands roughly 210 openings a year at a
> median salary of $132,040.

**Where the analysis actually lives.** Not in the prose — in the tables, side by side. Foothill
121000 shows 630 enrolled against 48 awarded, and 48 awarded against 68 five years earlier. Every
draft of this report that *narrated* those figures got cut. The evaluation's job is to put the
right tables next to each other and get out of the way.

**Caveats.** Awards and enrollment come from different DataMart reports counting different things,
so the two series are not a completion rate. That caveat was drafted into `enrollment_note` and cut
— the captions stayed plain. Worth knowing the exposure: a reader who divides 48 by 630 gets a
figure the data does not support. If a future evaluation needs the guard, it belongs as one clause
in the caption, never a sentence of its own.

## Where the concision comes from

Not from dropping sections — from the subject narrowing to one program at one college:
peers become a compact benchmark rather than a full alignment diagram, and the two trend
tables read as one throughput story.

## Process

0. **Intake** — `member` + `TOP6`. That is the whole editorial decision.
1. **Derive** the destination SOCs (rule above). Eyeball the dropped list.
2. **Scaffold** a def via `report.scaffold_report_def(member, title, sector, socs)` where
   `sector` = the TOP's home sector and `title` = the college's real program name from
   `program_display_names.json` + `(TOP {n})`. Set `org_name` to
   `"{College} Program Evaluation"` so the masthead reads program-first.
3. **Enrich** — reuse `find-program-name` (the subject program AND the peers),
   `find-live-postings`, `curate-competencies`, exactly as create-report does.
4. **Caption the trend tables** — `award_note` / `enrollment_note` say what the table is and note
   that empty cells mean no data reported. They do NOT narrate the figures (rule 8). The
   throughput finding comes from the two tables sitting next to each other, not from prose.
5. **Render + review**, then export via `tools/report-render/export.sh` as usual.

## Known v2 candidates (deliberately NOT built)

Bare-bones by intent — the use case is early. Worth adding only once real program reviews
have been run through it: a merged enrollment-vs-awards throughput table (currently two
tables), a program-identity header block (award types, accreditation), and a completion-rate
figure. Do not build these speculatively.
