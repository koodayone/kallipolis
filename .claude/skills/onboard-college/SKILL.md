---
name: onboard-college
description: >
  This skill should be used when the user asks to "onboard a college", "add a new college",
  "load College X into the graph", "run the pipeline for College X", or "set up College X in
  Kallipolis". It orchestrates the full six-stage onboarding pipeline — curriculum extraction,
  student generation, employer generation, employer validation, employer load, and partnership
  alignment precompute — for a single California community college identified by its college
  key in catalog_sources.json. The skill invokes the validate-employers skill automatically
  between employer generation and employer load, so the operator never has to remember the
  validation step.
---

# Onboard a College

Bring a new California community college into the Kallipolis graph end-to-end. This skill
owns the operator-facing workflow for new-college work: preflight verification, curriculum
extraction and skill enrichment, synthetic student generation, employer scrape and cleanup,
employer validation, employer load, partnership alignment precompute, and a final graph-state
verification. It is the default entry point for running the pipeline for a college that has
not yet been loaded.

## Context

The Kallipolis backend pipeline has six stages. Running them in order, with the correct
arguments, with the right caching flags, and with the mandatory `validate-employers` step
between employer generation and employer load, is tribal knowledge scattered across multiple
Python entry points and a pipeline documentation tree. This skill centralizes that knowledge
so the operator can say "onboard College X" and the sequence runs without any per-step
decisions.

The critical non-obvious step is stage 4 — `validate-employers`. When run directly via
`python3 -m employers.generate`, the employer pipeline writes records to `employers.json`
with no `website` field. The `validate-employers` skill is what fetches and verifies each
employer's web presence, applies the five viability criteria, and enriches the surviving
records. Skipping this step silently corrupts the partnership landscape with unverified,
potentially closed or sub-departmental entries. This skill makes that step impossible to
skip in the normal workflow.

## Input

The skill takes one required argument: the **college key** used in
`backend/pipeline/catalog_sources.json`. Examples: `desert`, `mtsac`, `foothill`. The key
is typically the short form of the college name (all lowercase, no spaces, no punctuation).

If the operator says "onboard College of the Desert" or "run the pipeline for Mt. San
Jacinto," resolve the college name to the key by reading `backend/pipeline/catalog_sources.json`
and matching on the `name` field. If the match is unambiguous, proceed with the resolved key.
If the match is ambiguous or the college is not in the catalog, stop and report which keys
are available so the operator can disambiguate.

## Cost and wall-time expectations

Surface these to the operator at the start of the skill so they know what they are committing
to. Employer work is regional: if another college in the same COE region has already been
onboarded, stages 3–5 (employer generation, validation, load) short-circuit via the regional
cache. Only the first college in a given region pays the full employer cost.

- **First college in a region, no caches**: ~45–75 minutes total wall time. Dominated by PDF
  extraction (~17 min) and regional EDD scrape (~15–40 min depending on region size — Bay has
  12 counties, FN has 14, whereas LA and OC are single-county). Costs on the order of a few
  dollars in Gemini tokens.
- **Subsequent college in an already-onboarded region**: ~5–10 minutes total wall time.
  The regional employer cache is reused as-is; no re-scrape, no re-validation, no re-load.
  Only curriculum and students are college-specific.
- **Fully cached re-run (everything already generated)**: ~2–5 minutes total wall time. All
  stages short-circuit.
- **Network dependencies**: live access to the EDD ALMIS database for the regional employer
  scrape, live access to the Gemini API for curriculum and employer cleanup, live access to
  each employer's website for the validation step.

## Stage 0 — Preflight verification

Before running any Bash command, verify all preconditions. If any check fails, report the
failing preconditions with absolute paths, stop, and tell the operator exactly what to fix
before re-invoking the skill. Do not proceed to any downstream stage on a failed preflight.

The checks, in order:

1. **College key exists in the catalog.** Read `backend/pipeline/catalog_sources.json` and
   confirm the key appears under `colleges`. Resolve the human-readable `name` field.
   Confirm the entry has a `catalog_pdf_url` field. If the entry has no `region` field,
   warn the operator that the college will inherit the top-level default region (cosmetic
   for the College node's `region` property, but the Neo4j IN_MARKET edge is driven by
   `COLLEGE_COE_REGION` instead).

2. **Region mapping exists.** Read `backend/ontology/regions.py` (or import and inspect)
   and confirm the human-readable college name is a key in `COLLEGE_COE_REGION` (maps to
   a COE region code: Bay, CVML, FN, GS, IE/D, LA, OC, SCC, or SD/I). If missing, stop
   and tell the operator the exact file and dict name to edit. Record the resolved COE
   region code — stages 3–5 are keyed by it.

3. **Student calibration files exist.** Verify these three paths, substituting `{key}`:
   - `backend/ontology/calibrations/{key}.json` — 2-digit TOP code enrollment distribution
   - `backend/ontology/calibrations/top4/{key}.json` — 4-digit TOP code calibration
   - `backend/ontology/mastercoursefiles/MasterCourseFile_{key}.csv` — institutional MCF

   All three are required for stage 2 (student generation). If any is missing, stop and
   point the operator at the `backend/ontology/calibrations/` tree.

4. **Environment variables are set.** Read `.env` at the repo root and confirm
   `GEMINI_API_KEY`, `ANTHROPIC_API_KEY`, and `NEO4J_URI` are all present. If any are
   missing, stop and tell the operator to update `.env`.

5. **Neo4j is reachable.** Run a minimal Cypher query (`MATCH (c:College) RETURN count(c)`)
   via a small Python one-liner through the Bash tool. If the driver cannot connect, stop
   and tell the operator that Neo4j needs to be running before the skill can proceed.

Only after all five checks pass, proceed to Stage 1.

## Stage 1 — Curriculum extraction and Neo4j load

Run the curriculum pipeline. If `backend/pipeline/cache/{key}_enriched.json` exists, reuse
the prior Gemini extraction; otherwise run a fresh extraction against the PDF catalog.

- **Fresh**: `cd backend && python3 -m pipeline.run --college {key}`
- **Cached**: `cd backend && python3 -m pipeline.run --college {key} --from-cache`

Run the command via the `Bash` tool in the background (wall time can be ~17 min fresh).
When the command completes, confirm the log contains `Stage 3 complete: LoadStats(...)`
with non-zero `courses_created` and `departments_created`. Report the course count and
department count to the operator.

If the command fails — PDF unreachable, Gemini quota exhausted, Neo4j connection lost —
report the error and stop. The operator can re-invoke the skill after resolving the
underlying issue; on retry, the `{key}_enriched.json` cache (if it was produced before
the failure) will short-circuit this stage.

## Stage 2 — Student generation

Run the student generator. Always use `--from-cache` because Stage 1 just produced the
enriched file.

- `cd backend && python3 -m pipeline.run --college {key} --generate-students --from-cache`

Wall time is ~90 seconds — run in the foreground with a generous timeout. Confirm the log
shows `Complete: N students, M enrollments, success rate: P%`. The calibration-match line
(`success rate: synthetic=P%, target=P%, diff=X%`) should show `diff` within ±0.5% of the
target; if it deviates more than ±1%, flag it to the operator as a calibration drift
signal (not a failure, but worth a manual check).

Report student count, enrollment count, and top-5 TOP4 share deltas to the operator.

## Stage 3 — Employer generation (regional)

Employers are generated at the COE region level. Every college in a region shares the same
employer pool, so this stage is a **no-op** when another college in the same region has
already been onboarded.

Let `{code}` be the COE region code resolved in preflight (e.g., `Bay`, `SCC`, `IE/D`).

First, check whether the region has already been generated. If both
`backend/employers/cache/edd_region_{code_slug}_f.json` exists AND `employers.json` already
contains entries tagged with `{code}`, skip this stage and Stage 4 (validate) — there are
no new employers to generate or validate. Report the count of employers currently tagged
with `{code}` in `employers.json` to the operator, then proceed directly to Stage 5 (which
is idempotent) to ensure the graph reflects the file.

If the region has not yet been generated, run the regional pipeline:

- **Fresh**: `cd backend && python3 -m employers.generate --region {code}`
- **Cached** (regional raw cache present, but LLM cleanup needs re-running):
  `cd backend && python3 -m employers.generate --region {code} --no-scrape`

Wall time varies by region size (number of counties × NAICS codes):
- 1–3 county regions (LA, OC, SD/I, SCC, IE/D): ~8–15 min fresh
- 8+ county regions (GS, Bay, CVML, FN): ~25–45 min fresh
- Cached: ~2–5 min (Gemini cleanup only)

Run in the background. The `{code_slug}` is `{code}` lowercased with `/` replaced by `_`
(e.g., `SD/I` → `sd_i`).

Confirm the log shows `Merge: N new, M updated. Total: T` with non-zero N. Also confirm
Gemini context cache creation (`Gemini context cache created: cachedContents/...`) and
non-zero occupation assignment counts. If the log shows `No GEMINI_API_KEY — skipping
LLM cleanup`, the `.env` loading failed silently — stop and report the issue; do not
proceed to validation because the employer records will have no descriptions and only
fallback SOC codes.

## Stage 4 — Validate employers (via Skill tool)

This is the critical step that prior manual runs have silently skipped. Invoke the
`validate-employers` skill via the Skill tool, passing the college's COE region code
(resolved during preflight from `COLLEGE_COE_REGION`) as the argument so the
validation scope matches the generation scope:

> Use the Skill tool with `skill: "validate-employers"` and `args` set to the region
> code string (e.g., `"Bay"`, `"SCC"`, `"IE/D"`, `"SD/I"`, `"FN"`).

The skill reads `backend/employers/employers.json` directly, filters to employers
that are tagged with the passed region AND have no `website` key (i.e., never
previously attempted — see the skill's three-state `website` field semantics),
fetches and verifies each candidate URL, applies the five viability criteria, and
writes the enriched and filtered list back to the same file. Wall time: ~5–15
minutes depending on the number of new employers (per-employer WebFetch
verification with rate limiting).

Passing the region is what prevents validation from re-attempting stragglers from
other regions that were never validated under the older workflow. Without the
region arg, the skill falls back to all-missing-website across the file, which is
the right default for ad-hoc invocations but wrong during onboarding.

When the skill completes, confirm that it reported a validation summary (assessed /
retained / removed counts). Spot-check `employers.json` to confirm the new records
for this region now have `website` fields populated. If the skill reports zero
assessed or aborts early, stop and report the issue; do not proceed to load
unvalidated data.

## Stage 5 — Employer load

Push the validated employer list into Neo4j:

- `cd backend && python3 -m employers.load`

Wall time: ~30 seconds for a typical college. Confirm the log shows `Created N Employer
nodes`, `Created M IN_MARKET edges`, and `Created K HIRES_FOR edges` with all counts
non-zero. Report the counts to the operator.

## Stage 6 — Partnership alignment precompute

Run the partnership precompute as a one-shot via Bash:

```
cd backend && python3 -c "
from dotenv import load_dotenv
from pathlib import Path
load_dotenv(Path('/Users/dayonekoo/Desktop/code/kallipolis/.env'))
import logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
from ontology.schema import get_driver, close_driver
from partnerships.compute import precompute_partnership_alignment
driver = get_driver()
try:
    stats = precompute_partnership_alignment(driver, ['{college_name}'])
    print(f'Stats: {stats}')
finally:
    close_driver()
"
```

Substitute `{college_name}` with the human-readable name resolved during preflight
(e.g., `College of the Desert`), not the key. Wall time is 1–3 seconds. Confirm the
output shows `wrote N PARTNERSHIP_ALIGNMENT edges` with N > 0. If N is zero, the most
likely cause is that the College → Region IN_MARKET edge is missing — this should not
happen after commit `69c4ba0` because `ensure_college_region_link` is now called
automatically from `load_college`, but if it does, run this one-shot as a fallback:

```
python3 -c "
from dotenv import load_dotenv; from pathlib import Path
load_dotenv(Path('/Users/dayonekoo/Desktop/code/kallipolis/.env'))
from ontology.schema import get_driver
from ontology.regions import ensure_college_region_link
driver = get_driver()
ensure_college_region_link(driver, '{college_name}')
"
```

Then re-run the precompute.

## Stage 7 — Final verification

Run one Cypher query via Bash that reports the end-to-end graph state for the onboarded
college, and present it to the operator as a summary table:

```
cd backend && python3 -c "
from dotenv import load_dotenv
from pathlib import Path
load_dotenv(Path('/Users/dayonekoo/Desktop/code/kallipolis/.env'))
from ontology.schema import get_driver
driver = get_driver()
with driver.session() as s:
    name = '{college_name}'
    courses = s.run('MATCH (c:Course {college: \$name}) RETURN count(c) AS n', name=name).single()['n']
    students = s.run('MATCH (st:Student)-[:ENROLLED_IN]->(c:Course {college: \$name}) RETURN count(DISTINCT st) AS n', name=name).single()['n']
    edge = s.run('MATCH (c:College {name: \$name})-[:IN_MARKET]->(r:Region) RETURN r.name AS region', name=name).single()
    employers = s.run('MATCH (c:College {name: \$name})-[:IN_MARKET]->(r:Region)<-[:IN_MARKET]-(e:Employer) RETURN count(DISTINCT e) AS n', name=name).single()['n']
    alignments = s.run('MATCH (c:College {name: \$name})-[pa:PARTNERSHIP_ALIGNMENT]->() RETURN count(pa) AS n, avg(pa.alignment_score) AS avg, max(pa.alignment_score) AS max', name=name).single()
    top = s.run('MATCH (c:College {name: \$name})-[pa:PARTNERSHIP_ALIGNMENT]->(e:Employer) RETURN e.name AS employer, e.sector AS sector, pa.alignment_score AS score ORDER BY pa.alignment_score DESC LIMIT 5', name=name).data()
    print(f'Courses: {courses}')
    print(f'Students: {students}')
    print(f'Region: {edge[\"region\"] if edge else None}')
    print(f'Employers in region: {employers}')
    print(f'Alignment edges: {alignments[\"n\"]}, avg {alignments[\"avg\"]:.2f}, max {alignments[\"max\"]:.2f}')
    print('Top 5:')
    for t in top:
        print(f'  {t[\"employer\"]:40s} [{t[\"sector\"]:20s}] {t[\"score\"]:.2f}')
driver.close()
"
```

Present the results to the operator. All counts should be non-zero. If any are zero or
missing, diagnose by comparing against the earlier stage outputs and report the
discrepancy.

## Failure recovery

Each stage, on failure, reports its error and stops. Because each stage writes a cache
or a graph state that the next stage reads, re-invoking the skill after fixing the
underlying issue will skip the stages that already succeeded and retry from the failing
one. This is the natural resume mechanism; no explicit state file is maintained.

Specific failure classes:

- **Preflight fails**: operator edits the named config file and re-runs.
- **Stage 1 PDF unreachable**: operator verifies the URL in `catalog_sources.json`, or
  downloads the PDF manually to `backend/pipeline/cache/{key}_catalog.pdf` and re-runs
  with `--from-cache` behavior implicit via the cache detection.
- **Stage 3 EDD scrape network failure**: operator retries — the partial cache file is
  valid if it contains any rows, and the scraper's per-NAICS loop is resumable.
- **Stage 4 (`validate-employers`) aborts mid-run**: operator re-invokes the skill; it
  will pick up from the unvalidated employers on the next pass.
- **Stage 6 (`precompute_partnership_alignment`) writes zero edges**: check the
  College → Region IN_MARKET edge (see the Stage 6 fallback one-shot). After commit
  `69c4ba0` this should not occur for new colleges, but the fallback is present as a
  defensive measure.

## Constraints

- The skill does not modify `backend/ontology/regions.py`, `backend/pipeline/catalog_sources.json`,
  or any calibration or MCF file. Configuration changes are outside the skill's scope;
  they are decisions that deserve human approval.
- The skill does not drop, clear, or mutate existing Neo4j state beyond what the
  underlying scripts already do. In particular, it does not run `pipeline/reload.py`,
  which clears the entire graph.
- The skill does not commit to git or push. Any resulting file changes (new entries in
  `employers.json`) are left in the working tree for the operator to review and commit.
- The skill runs the raw Python scripts as-is without modifying them. If the scripts
  need fixing, that is a separate change outside the skill's scope.

## What this skill does not replace

The raw Python scripts remain supported for testing, partial re-runs, and anything that
does not fit the full onboarding sequence. `python3 -m pipeline.run --college {key}` is
still the right command for iterating on curriculum extraction. `python3 -m
employers.generate --region {code}` is still the right command for iterating on the
employer pipeline at a regional scope. The skill is the default workflow; the scripts are
the escape hatch.

## Related

- `docs/pipeline/overview.md` — high-level description of the six pipeline stages.
- `docs/pipeline/employer-generation.md` — detailed treatment of the employer stage.
- `.claude/skills/validate-employers/SKILL.md` — the validation skill this skill invokes.
