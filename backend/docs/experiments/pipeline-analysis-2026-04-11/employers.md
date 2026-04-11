> **Point-in-time experimental artifact** (2026-04-11). This document was produced by a parallel Claude Code session analyzing `backend/employers/` during a four-way pipeline parallelization experiment. The observations below reflect the state of the code at that date. Some of the in-scope improvements identified here have since been implemented; some of the coordination requests remain open. **This document is not audited and is not a source of truth for the current code.** See [README.md](./README.md) for context.

# Employers pipeline — improvement proposal

This is an analysis pass of `backend/employers/` against the quality and
efficiency axes that matter for the EDD → name cleanup → LLM enrichment →
merge flow. It proposes concrete changes; it does not implement them.

## 1. Current state

### Module shape

| File | Role |
|---|---|
| `edd_scrape.py` | HTTP + regex scraper against EDD ALMIS (`empResults.aspx`, `countymajorer.asp`). Defines `COUNTY_CODES`, `METRO_COUNTIES`, `CTE_NAICS_CODES`, `SIZE_CODES`. |
| `generate.py` | Orchestrator. Cleans names, deduplicates branches, assigns NAICS-derived sectors and fallback SOC codes, runs Gemini cleanup, formats, and merges into `employers.json`. |
| `load.py` | Neo4j loader — `MERGE` Employer nodes, `IN_MARKET` edges to Region, `HIRES_FOR` edges to Occupation. |
| `api.py` | FastAPI routes: `GET /`, `GET /{name}`, `POST /query`. |
| `query.py` | LLM → Cypher translator, validated by `llm.query_engine.validate_cypher`. |
| `models.py` | Pydantic schemas. |
| `test_generate.py` | 21 passing unit tests over 4 pure helpers. |
| `employers.json` | Persisted merged employer pool (1510 lines, shared across colleges). |
| `cache/` | Per-county EDD scrape caches (`edd_deep_<counties>.json`), plus a few per-college filtered-occupation snapshots. |

### Flow, six stages (from `generate_for_college`)

1. **Resolve scope** — college → primary OEWS metro → COE region → search
   counties (via `COLLEGE_SEARCH_COUNTIES` override or default metro counties).
2. **Scrape EDD** — for each county, iterate ~140 CTE NAICS 4-digit codes,
   apply size filter `>= G` (250+), paginate up to 10 pages each. Parse
   rows with a single compiled regex; extract ASP.NET `__VIEWSTATE` /
   `__EVENTVALIDATION` via separate regex. Cache the combined county list
   to `cache/edd_deep_<counties>.json`.
3. **Clean + branch-dedup** — regex abbreviation table, strip corporate
   suffixes, collapse by normalized-name key keeping the largest size entry.
4. **Sector + fallback SOC** — NAICS-2 → sector label; NAICS-2 → list of SOC
   major groups → first 10 regional SOC codes.
5. **LLM cleanup (Gemini)** — batches of 30. Prompt embeds the *full*
   regional occupation list each batch. Gemini returns cleaned name +
   one-sentence description + 3–8 SOC codes (or `REMOVE`). Validated
   against the regional SOC set. A second dedup pass runs over post-rename
   names.
6. **Format + merge** — `_format_for_json` builds the final records;
   `_merge_employers` unions by normalized name, growing the `regions` and
   `occupations` arrays when an employer already exists.

### Test coverage today

`test_generate.py` exercises four pure helpers: `_clean_employer_name`,
`_normalize_name`, `_size_sort_key`, `_deduplicate_branches`. 21 tests,
all passing (`python3 -m pytest employers/` → 21 passed in 0.02s). No
coverage of `_assign_soc_codes`, `_format_for_json`, `_merge_employers`,
or any scraper helper. The most consequential semantic behavior — the
region/SOC-union merge described in `docs/pipeline/employer-generation.md`
— has zero test coverage.

---

## 2. Evaluation

### 2a. Quality axes

**Scraper robustness — fragile by design.** `edd_scrape.py` parses EDD's
ASP.NET output with two hand-rolled regexes: `_ROW_PATTERN` for the
result table and `_extract_form_state` for `__VIEWSTATE` et al. Any
change to the row markup (column order, class name, `amp;` escaping) or
the form-state rendering silently produces zero rows. The only signal
is a smaller cache file. `deep_search` catches every exception and
returns `[]`, so a broken selector, a network flap, and an empty result
set are indistinguishable to the caller. The pipeline doc
(`known sharp edges`) acknowledges this but the code does not fail loud.

**Name cleaning coverage — narrow.** `_ABBREVIATIONS` lists ~26 tokens.
A sample walk of cached EDD rows surfaces many more that occur at scale:
`Assn`, `Sys`, `Hlth`, `Comnty`, `Fdn`, `Bros`, `Srvc`/`Srvcs`, `Rltrs`,
`Prod`/`Prods`, `Mgmt`, `Assoc`, `Ind`, `Rsrch`, `Inst`, `Lbry`, `Dvlpmt`,
`Govt`, `Pub`, `Sch`, `Dist`. These survive into the cleaned list and
into `_normalize_name`, which means branch dedup *fails silently* for
two records where one side used an expanded form and the other used
an abbreviation not in the table. The Gemini step then gets asked to
rename the survivors, which works, but not before the dedup key has
already let two branches through as "distinct" employers.

**Branch dedup key is too narrow.** `_normalize_name` strips the five
legal suffixes and lowercases — nothing else. Two records for the same
employer that differ only in a trailing city tag (`Kaiser Permanente`
vs `Kaiser Permanente Los Angeles`) are keyed as distinct and both
survive stage 3. They only collapse in `_merge_employers`
*after* Gemini has rewritten them, i.e., two LLM cleanup requests get
spent on what should have been one row. The post-rename dedup inside
`_llm_cleanup` uses `emp["name"].lower()` rather than
`_normalize_name`, so it is yet another third normalization scheme.
Three different keys for "same employer" is a bug surface.

**False-positive handling is all-or-nothing on the LLM.** Staffing
agencies, internal departments, foundations, and branches-of-branches
are removed only if Gemini returns `REMOVE`. The pipeline *actively
queries* NAICS 5613 (Employment Services / Staffing) in stage 2 and
then relies on Gemini to throw those rows away in stage 5. That is
tokens spent on guaranteed discards and a correctness risk if Gemini
misses one. A cheap pre-filter — "drop NAICS 5613 outright" and
"drop names starting with `Dept Of` or ending in ` Foundation`" —
would remove most of these deterministically.

**LLM-assigned SOC validation is correct but parsing is brittle.**
`emp["soc_codes"] = valid` trusts only SOC codes present in the
regional occupation set — good. But the parse is
`s.split(":")[0].strip()`, which handles `"11-3121: Human Resources
Managers"` but *not* `"11-3121 - Human Resources Managers"` or
`"SOC 11-3121"`. The actual Gemini response shape depends on the
model's stochastic formatting; a small drift invalidates the whole
batch silently (the code path falls through to the NAICS-derived
fallback SOC list, which is much noisier).

**LLM failure mode is lossy.** `_llm_cleanup`'s try/except on the
Gemini call returns the uncleaned batch on any exception. There is no
retry, no backoff, no partial-progress persistence. A transient 429 or
503 from Gemini converts 30 employers to their uncleaned state
irreversibly — they will carry the fallback NAICS-derived SOC codes
into the merged `employers.json`, and the next run against the same
cache will read them back from the merged file already-committed.

**Dead code is confusing the docstring.** `_select_employers` (line 197,
the sector-diversity selector) is defined and documented in the module
docstring ("5. Select with sector diversity") but is never called from
`generate_for_college`. The `--target` CLI flag is similarly unused for
selection; it is passed through but has no effect. A reader trying to
map docstring → behavior will chase this for ten minutes.

**Merge semantics have no regression test.** The region-union and
SOC-union behavior described as "the most subtle of the merge
semantics" in `docs/pipeline/employer-generation.md` is implemented in
`_merge_employers` but not tested. A regression there corrupts the
shared `employers.json` in a way that is hard to notice until a
coordinator sees an employer on a map in the wrong region.

**Regional filter has a surprising exclusion list.** Stage 4 filters
`regional_occupations` by dropping five `education_level` values —
including `Master's degree` and `Doctoral or professional degree`. The
rationale ("career-track CTE roles") is reasonable but undocumented
anywhere in code or docs, and the NAICS fallback pool is reduced
accordingly. If the filtered set becomes empty for a rural region, the
fallback SOCs become empty and the employer reaches Gemini with no
prior assignment. No assertion catches this.

### 2b. Efficiency axes

**Scraper throughput.** The per-college cost is roughly
`|counties| × |CTE_NAICS_CODES| × (1 GET + 1 POST + ≤10 POST pages) × 0.3–0.5s sleep`.
For a 2-county metro that is ~140 × 2 × (2 + small-page-average) requests,
serialized with a 0.5s sleep between NAICS codes and 0.3s between pages.
Typical single-college wall time is in the tens of minutes for a dense
metro. Opportunities:

- **Per-metro cache keying.** `deep_cache` is keyed by the
  underscore-joined county list. In `generate_all`, `metro_done` is
  tracked to avoid re-scraping, but the cache *filename* depends on
  the college's `COLLEGE_SEARCH_COUNTIES` override — so two colleges
  in the same metro with different override lists write to different
  files and cannot share. The shared-pool design described in the
  pipeline doc is only effective when override counties match exactly.
- **Sector queries instead of 4-digit queries.** Many 4-digit NAICS
  queries within a sector return small overlapping result sets that
  get deduplicated in-memory. Querying each sector once by the 2-digit
  `naicsect` (which the EDD URL already accepts) would return the
  same pool in one-seventh the requests for manufacturing, one-tenth
  for healthcare. The current code uses both parameters, so the
  4-digit is the binding constraint.
- **Staffing-agency NAICS (5613) is both wasted throughput and a
  false-positive vector.** Dropping it from `CTE_NAICS_CODES` saves
  every county query for that sector and eliminates a class of LLM
  removals.
- **Fragile silent-truncation risk from `max_pages_per_code=10`.**
  Dense counties (Los Angeles × healthcare) overflow. There is no
  detection, so the pool silently caps at page 10.

**Gemini token cost.** The prompt for each 30-employer batch embeds
the *full* regional occupation list (typically 300–700 SOC rows, each
~40 chars). This is ~15–30k input tokens *per batch*, dominating the
cost. For a metro yielding 1,000 post-dedup employers, that is ~34
batches × 20k tokens ≈ 680k input tokens per run, repeated for each
college because there is no prompt-level caching.

Three independent wins are available:

1. **Gemini context caching.** `gemini-2.5-flash` supports explicit
   context caching for ≥32k-token shared prefixes. The regional
   occupation list is the obvious cache target: build a `CachedContent`
   once per `(metro, filtered_occupations)`, then spend per-batch
   tokens only on the 30 employer names and response schema. Expected
   input-token reduction of ~90% per batch.
2. **Larger batch size.** Batch size is 30. Gemini 2.5 Flash's 1M
   context trivially accommodates 200-employer batches even with the
   full occupation list inline. Moving from 30 → 150 cuts the number
   of requests fivefold and the per-batch overhead accordingly. The
   response size scales, so `max_output_tokens=65536` is already
   sized generously.
3. **Retry with backoff.** Wrapping the Gemini call in a retry
   decorator (exponential backoff, two attempts) would recover the
   transient 429/503 cases that currently drop an entire batch to
   fallback.

**`employers.json` merge cost.** Linear scan per insert against an
indexed dict — fine at current scale (<2000 records). No action.

---

## 3. Recommended improvements

Ordered by value-per-effort. Every item below is scoped to
`backend/employers/` unless flagged as a coordination request (§4).

### 3.1 Correctness and clarity — low risk, high value

**C1. Delete `_select_employers` and update the module docstring.**
The selector is dead code and the `--target` CLI flag is a no-op. Delete
both; remove the "5. Select with sector diversity" bullet from the module
docstring and from the pipeline doc's description of stage 4 if it is
echoed there. (Checked — the pipeline doc does not mention sector
selection as a stage, so no doc edit is required beyond the module
docstring.) Zero behavioral change, eliminates reader confusion.

**C2. Unify the three normalization schemes.** There are three keys in
flight: `_normalize_name` (used by stage-3 dedup and merge),
`(name.lower(), city.lower())` (used by scraper dedup), and
`emp["name"].lower()` (used by post-LLM dedup). Consolidate on a single
`_canonical_key(name)` that lowercases, strips suffixes, strips a
trailing location tag (`- Los Angeles`, `, San Jose`), and collapses
whitespace. Apply uniformly in all three call sites. This closes the
"same employer, three different keys" hole and is the precondition for
C3.

**C3. Expand the abbreviation table and make it data-driven.** Move
`_ABBREVIATIONS` into a module-level dict (or a small JSON file under
`employers/`) and add the missing entries observed in the cached EDD
rows: `Assn`, `Assoc`, `Sys`, `Hlth`, `Comnty`, `Fdn`, `Bros`, `Srvc`/
`Srvcs`, `Rltrs`, `Prod`/`Prods`, `Mgmt`, `Ind`, `Rsrch`, `Inst`,
`Dvlpmt`, `Govt`, `Pub`, `Sch`, `Dist`, and the half-dozen LA-specific
entries already present are not enough for other metros. The pure-
function nature is preserved so existing tests continue to pass; add
new parametrized tests for each new entry.

**C4. Deterministic pre-filters for guaranteed discards.** Before the
LLM step, drop rows whose NAICS4 is in a small "never-employer" set
(`5613` staffing is the primary one, possibly `5614`), and rows whose
name matches a small regex set (`^Dept Of`, `^County Of`, trailing
` Foundation` when parent is a distinct row, etc.). Cheaper than
letting Gemini decide and closes the LLM-miss correctness risk.

**C5. Make the Gemini failure path recoverable.** Replace the single
`try/except` in `_llm_cleanup` with:
- a retry loop (exponential backoff, 2 retries) around
  `client.models.generate_content`;
- on final failure, raise a typed exception that the orchestrator
  catches per-batch and logs with the batch's employer names, so a
  re-run can target just the failed batches;
- never return the uncleaned batch silently.

**C6. Robustify the LLM SOC-code parser.** Accept `soc_code`,
`"11-3121"`, `"11-3121: Title"`, `"11-3121 - Title"`, `"SOC 11-3121"`.
A single regex `r"\d{2}-\d{4}"` applied to the returned string handles
all variants and is forward-compatible with drift in Gemini output
formatting.

**C7. Fail loud on scraper regression.** In `_parse_employer_rows`,
after extracting rows, assert that at least *some* recognizable column
markers are present in the source HTML when the row count is zero. Log
a warning distinguishing "legitimate empty result set" from "markup
shifted, selector no longer matches" by checking for the presence of
the result table container. Same for `_extract_form_state` —
differentiate "no form state on page" from "page structure changed".

**C8. Document the `_EXCLUDE_EDUCATION` filter in-place.** Either move
it to a module-level constant with a one-line comment explaining the
CTE-outcome rationale, or (preferred) promote the rationale to a
one-sentence note in the pipeline doc's stage-4 description. This is a
small edit but the current inline set in the middle of
`generate_for_college` is easy to miss.

### 3.2 Efficiency — medium effort

**E1. Gemini context caching for the occupation list.** For each
`(metro, filtered_occupations)` pair, create a `CachedContent` with
the occupation list and reuse its cache name across batches. Expected
input token savings: ~80–90% per batch. This is the single largest
cost lever and is entirely local to `_llm_cleanup`.

**E2. Raise `BATCH_SIZE` from 30 to 100–150.** Gemini 2.5 Flash with
1M context handles it trivially; response size stays under the current
`max_output_tokens=65536` at 150 employers. Cuts per-run Gemini
request count by 5x and amortizes network overhead.

**E3. Drop NAICS 5613 (and 5614) from `CTE_NAICS_CODES`.** Both
removes a class of false positives and eliminates a per-county scrape
round-trip for those codes. This is the cheapest single efficiency win.

**E4. Per-metro cache key.** Change the cache filename from
`edd_deep_<search_counties>.json` to `edd_deep_<metro>.json` when no
per-college override is present, so that two default-metro colleges
in the same OEWS metro share one scrape. Keep the per-college key
for colleges with `COLLEGE_SEARCH_COUNTIES` overrides. Requires a
one-time cache migration or a cold scrape.

**E5. Detect pagination truncation.** If `max_pages` is hit *and* the
last page contains a "Next" link, log a warning so the operator knows
the pool is incomplete. Do not silently cap.

### 3.3 Test coverage gaps — additive, no risk

The current test file covers ~25% of the functions in `generate.py`.
The highest-value additions, each a new `TestX` class in
`test_generate.py`:

**T1. `TestMergeEmployers`** — cover the region-union, SOC-union,
and normalized-name-collision semantics explicitly. This is the single
most load-bearing untested function (the pipeline doc devotes a
section to its semantics).

**T2. `TestAssignSocCodes`** — cover the 3/2-digit NAICS prefix
fallback, the 10-code cap, and the empty-occupations-by-group case.

**T3. `TestFormatForJson`** — cover LLM-provided description
pass-through, the fallback description builder (name + city + county +
industry + size), and the COE region resolution from
`OEWS_METRO_TO_COE`.

**T4. `TestCanonicalKey`** — once C2 lands, the new unified key needs
direct tests for suffix stripping, trailing-location stripping, and
collision cases like `Kaiser Permanente` vs `Kaiser Permanente, Fresno`.

**T5. HTML-fixture tests for `_parse_employer_rows` and
`_extract_form_state`.** Checkpoint one sample page under
`employers/fixtures/edd_sample.html` (or inline as a Python triple-
string constant) and assert the parse output. This is the first line
of defense against the silent scraper regression in C7.

Abbreviation table tests (C3) are additive parametrized cases under
the existing `TestCleanEmployerName` class.

Test file conventions: each new test class lives inside
`test_generate.py`, the module docstring's Coverage list is updated in
the same commit, and the file continues to satisfy the
`backend_test_docstrings` audit check.

### Expected impact

| Lever | Axis | Expected effect |
|---|---|---|
| C1 delete dead selector | Clarity | Reader friction − |
| C2 unified key | Correctness | Dedup false-negatives ~0 |
| C3 abbrev table | Correctness | Branch dedup recall ↑ |
| C4 pre-filter | Cost + correctness | LLM waste ↓, false positives ↓ |
| C5 retry/backoff | Correctness | Silent LLM losses ↓ |
| C6 SOC parser | Correctness | Robust to Gemini drift |
| C7 loud scraper | Detectability | Silent pipeline breaks ↓ |
| C8 doc inline filter | Clarity | Reader friction − |
| E1 Gemini caching | Cost | Input tokens −80–90% per run |
| E2 batch size 30→150 | Cost | Request count −80% |
| E3 drop 5613/5614 | Cost + correctness | Scrape calls ↓, LLM wastes ↓ |
| E4 metro cache key | Cost | Shared-metro re-runs free |
| E5 pagination warning | Detectability | Silent truncation ↓ |
| T1–T5 tests | Regression safety | Merge-semantics guarded |

---

## 4. Coordination requests (touching shared infrastructure — flagged, not attempted)

None of the following are in-scope for this analysis pass per the
constraint "do not modify any files outside `backend/employers/`." I
surface them so the operator can decide whether to open parallel work.

**CR-1. Region filter lives in `backend/ontology/regions.py`.** The
current stage-4 occupation filter uses `COLLEGE_COE_REGION` and a local
`_EXCLUDE_EDUCATION` set. Any change to the COE-region crosswalk (e.g.,
if a college is remapped) is explicitly called out in the task prompt
as a cross-pipeline coordination concern. No change is proposed here,
but any future improvement that wants to *derive* the exclusion list
from ontology-level metadata (e.g., an `is_cte_track` flag on
occupations) would have to touch `backend/ontology/` or
`backend/occupations/`.

**CR-2. Gemini context-caching client configuration.** The Gemini
client is constructed ad-hoc inside `_llm_cleanup`. If the broader
backend moves toward a shared Gemini client with caching + retry
configured in `backend/llm/`, the employers pipeline would consume it
rather than reinventing retry and caching locally. This is a shared-
infrastructure question, not something to fix inside `employers/`.
Flag only — do not act.

**CR-3. `pipeline/run.py` orchestration vs. per-college caching.**
The metro-level cache sharing in `generate_all` (`metro_done` set)
lives in `generate.py` but is conceptually an orchestration concern.
If `pipeline/run.py` grows a unified cache strategy, the per-metro
caching in E4 should migrate there rather than staying in
`generate.py`. Flag only — in scope fix still belongs here for now.

**CR-4. `docs/pipeline/employer-generation.md` — documentation drift.**
The pipeline doc describes stage 4 as "Assign sector and SOC codes"
but does not mention `_select_employers` at all. After C1 deletes the
dead selector, no doc change is needed — but the pipeline doc should
eventually pick up the merge-semantics test coverage note and the
Gemini caching change once E1 lands. Both are documentation edits
outside `backend/employers/` and require the docs audit to pass.

---

## 5. Scope guardrails honored in this proposal

- No files outside `backend/employers/` proposed for modification in
  the "improvements" section; any such change is surfaced in §4 only.
- `ontology/regions.py` untouched — the `COLLEGE_COE_REGION` and
  `OEWS_METRO_TO_COE` tables continue to be the authority.
- `llm/` untouched — the employers pipeline continues to construct its
  own Gemini client for now; shared-client consolidation is a CR.
- `pipeline/run.py` and `pipeline/reload.py` untouched.
- Docs-audit-sensitive conventions preserved: the new tests in §3.3
  update the `test_generate.py` module docstring's Coverage list in
  the same commit they are added, per `backend/docs/testing.md`.
- No commit is proposed. This document is the deliverable.
