> **Point-in-time experimental artifact** (2026-04-11). This document was produced by a parallel Claude Code session analyzing `backend/occupations/` during a four-way pipeline parallelization experiment. The observations below reflect the state of the code at that date. Some of the in-scope improvements identified here have since been implemented; some of the coordination requests remain open. **This document is not audited and is not a source of truth for the current code.** See [README.md](./README.md) for context.

# Occupations pipeline — improvement proposal

Analysis of `backend/occupations/` as of 2026-04-11. This document is a
proposal, not an implementation. It describes the pipeline's current state,
the quality and efficiency axes it was evaluated against, the concrete
improvements recommended, and the coordination requests for anything that
would touch shared infrastructure.

## 1. Current state

### Scope

`backend/occupations/` owns the industry-side data for Stage 5 of the
pipeline (per `docs/pipeline/overview.md`). It is the sole source of
`Region` and `Occupation` nodes and of the `DEMANDS` and `REQUIRES_SKILL`
edges defined in `docs/architecture/graph-model.md`.

### File inventory

| File | Role | Status |
|---|---|---|
| `generate.py` | Parse COE CSV → `occupations.json` (merges prior skills/descriptions) | Active |
| `descriptions.py` | Hybrid description generator: SPECIFIC_DESCRIPTIONS dict (~320 hand entries) + title-pattern templates | Active |
| `assign_skills.py` | Gemini Flash batch skill assignment against `ontology/skills.UNIFIED_TAXONOMY` | Active |
| `load.py` | Neo4j loader: Region, Occupation, DEMANDS, REQUIRES_SKILL, and College↔Region IN_MARKET | Active |
| `api.py` | FastAPI routes: `/overview`, `/{soc_code}`, `/query` | Active |
| `query.py` | NL→Cypher translator prompt + dispatcher | Active |
| `models.py` | Pydantic schemas for the routes | Active |
| `coe_parser.py` | Earlier COE CSV parser that writes `coe_parsed.json` | **Dead** — output not consumed; logic duplicated in `generate.py` |
| `oews_parser.py` | EDD OEWS XLSX parser across 30 metros | **Dead** — `docs/pipeline/overview.md` §Stage 5 states "an earlier OEWS-based pipeline has been retired" |
| `coe_parsed.json` | Output of `coe_parser.py` | **Dead artifact** |
| `oews_parsed.json` | Output of `oews_parser.py` | **Dead artifact** |
| `occupations_pre_expansion.json` | Pre-expansion snapshot (724 occs) | Scratch / untracked |
| `occupations.json` | Canonical input to `load.py` (797 occs) | Active |

### Data shape (measured from `occupations.json`)

- **797 SOC codes**, each carrying `regions` entries for all 10 COE regions (`Bay`, `CA` statewide, `CVML`, `FN`, `GS`, `IE/D`, `LA`, `OC`, `SCC`, `SD/I`). Region coverage is 100% dense — every SOC has a demand row in every region.
- After `load.py`'s workforce-band education filter (excludes "No formal educational credential", "High school diploma or equivalent", "Some college, no degree", "Master's degree", "Doctoral or professional degree"), **279** occupations remain to be loaded. The other 518 are parsed, described, skill-assigned, and then dropped at load time.
- Education distribution after filter: Bachelor's (180), Postsecondary nondegree award (50), Associate's (48), and one `"N/A"` (SOC 55-9999).
- Skill assignment quality on the loaded 279:
  - **13 occupations have zero skills** despite being in the loaded band (e.g. `11-1011 Chief Executives`, `11-1021 General and Operations Managers`, `11-1031 Legislators`, `13-1028 Buyers and Purchasing Agents`, `17-2021 Agricultural Engineers`).
  - **78 of 279 (28%) have fewer than 6 skills**, even though the system prompt says "at least 6".
  - 13 of 279 have empty descriptions.
  - Unique skills assigned across the loaded set: 312 (of a taxonomy that is larger than this; see §3.2).
  - Skill-frequency top-5: Data Analysis (50), Project Management (44), Regulatory Compliance (44), Troubleshooting (37), Administration & Management (29).
- Average skills per loaded occupation: 5.8 (below the prompt floor).

### Existing tests

`cd backend && python3 -m pytest occupations/` collects **zero** tests. There is no `test_*.py` file anywhere under `backend/occupations/`. The whole pipeline is untested at the unit level.

## 2. Quality evaluation

### 2.1 COE region coverage — **good**

The parser honors the nine COE regions plus `CA` statewide. The measured density (797 × 10 = 7,970 region-SOC rows) matches what `docs/pipeline/overview.md` promises ("~800 SOC codes across nine COE regions plus statewide"). No missing regions, no unknown regions.

### 2.2 SOC code correctness — **good, with one typed edge case**

- SOC codes are taken as-is from the COE `SOC` column and used as `soc_code UNIQUE` keys in Neo4j. The COE feed is the canonical authority per the data-authority architecture, so treating it as ground truth is right.
- One untyped row: SOC `55-9999` has `education_level == "N/A"`, which currently slips through the workforce-band filter because `"N/A"` is not in the exclusion set. It then gets loaded with a `None`-equivalent education level. Minor, but worth a guard.

### 2.3 Skill assignment fidelity — **the main quality gap**

The skill assignment layer is where the product doc (`docs/product/occupations.md`, §"the pressure point is the skills association layer") explicitly locates the methodological weak point, and the current implementation shows the symptoms:

1. **The ≥6 skills instruction is treated as advisory.** 28% of loaded occupations violate it; 13 end up with zero skills. The prompt states "at least 6", but the response is accepted without a size check. The only validation is `s in UNIFIED_TAXONOMY`, which silently drops off-taxonomy terms and can leave the count at 0.
2. **Off-taxonomy drops are not retried.** When Gemini invents a skill name, the term is logged and dropped; the occupation is not resubmitted with a "the following terms were not in the vocabulary, please choose replacements" turn. This is the dominant cause of the sub-6 tail.
3. **Unmapped occupations are not retried.** When a batch errors (JSON parse fail, rate-limit exhaustion), the batch returns `{}` and every occupation in it is silently left with whatever skills it already had from a prior run. There is no per-occupation retry queue.
4. **No size-aware logging.** The stats print `updated` and `unmapped`, but neither metric reflects post-validation skill count. A reviewer cannot tell from the log that 28% of occupations are below the floor.
5. **The prompt does not carry the occupation description.** It carries only title + 200 chars of description. Since `descriptions.py` produces many template-generated descriptions that are nearly redundant with the title ("Performs tasks and duties in ..."), the model is effectively working from titles alone for the long tail, which concentrates skill assignments on a few generic terms. The top-5 distribution (Data Analysis, Project Management, Regulatory Compliance, Troubleshooting, Administration & Management) is consistent with "generic signals from short titles".

### 2.4 Crosswalk edge cases — **out of scope here, but one observation**

The TOP→CIP→SOC crosswalk lives in `ontology/crosswalks.py` and is read by `partnerships/` and `pipeline/` work, not by `backend/occupations/` itself. The occupations pipeline does not currently use the crosswalk to validate that a SOC code is reachable from any TOP4 — which means the load set can include SOC codes that no community college curriculum can realistically map to (the 13 zero-skill cases above are a symptom). The right place to address this is a coordination request, not this pipeline (see §4).

### 2.5 DEMANDS edge properties — **schema drift bug**

Cross-checking `load.py`, `api.py`, `query.py`, and `docs/architecture/graph-model.md`:

- `graph-model.md` defines `DEMANDS` properties as `employment, annual_wage, growth_rate, annual_openings` and places `education_level` on the `Occupation` **node**.
- `load.py::_create_demands` correctly sets only the four edge properties and `_create_occupations` correctly sets `education_level` on the node.
- **`api.py::get_labor_market_overview` reads `d.education_level`** (line 34), not `occ.education_level`. This returns `null` for every row.
- **`api.py::get_occupation_detail`'s region query also reads `d.education_level`** (line 108).
- **`query.py::OCCUPATION_QUERY_PROMPT` tells the NL→Cypher generator that `education_level` is a property of `DEMANDS`** (lines 23-26 schema block) and all four in-prompt examples return `occ.education_level` — so the examples are correct but the schema documentation inside the prompt contradicts itself.

Net effect: every `/overview` and `/{soc_code}` response currently returns `education_level: null`. The models.py `OccupationMatch.education_level` is `Optional[str]`, so this is a silent correctness bug, not a runtime error. This is inside `backend/occupations/` and is in scope for this pipeline to fix.

### 2.6 Description generation quality — **acceptable for specific, weak for pattern tail**

`descriptions.py` has two paths:

1. ~320 hand-written `SPECIFIC_DESCRIPTIONS` entries keyed by SOC. These read cleanly and carry real informational content.
2. A title-pattern fallback that substitutes tokens ("managers", "technicians", "analysts", ...). The generated text is often ungrammatical or circular: `"Plans, directs, and coordinates operations in chief executives"`, `"Performs tasks and duties in ..."`. When a description is short and weak, it does nothing for the skill-assignment prompt and visibly degrades the UI.

## 3. Efficiency evaluation

### 3.1 CSV parsing — **negligible, but duplicated**

The COE CSV has ~8k rows. `generate.py` parses it in well under a second. The concern is not speed; it is that `coe_parser.py` duplicates the same parse and emits `coe_parsed.json`, which nothing consumes. This is dead weight in the feature directory.

### 3.2 Gemini token cost for skill assignment — **~65% wasted**

Measured from `assign_skills.py`:

- Batch size 20, 797 occupations → 40 batches.
- System instruction includes the full `UNIFIED_TAXONOMY` as a bulleted list. The taxonomy is ~400 terms; at ~6 tokens each that is ~2.4k tokens of stable prefix per request (plus the instruction wrapper).
- Workforce-band filter happens **only inside `load.py`**. Assignment runs against all 797 occupations but only 279 are actually loaded. **~65% of output tokens (skill lists for occupations that will be dropped) are pure waste**, and the matching share of input tokens is wasted too.
- `thinking_budget=0` is set, which is correct for this task.
- No explicit Gemini context-cache reference is used for the taxonomy-bearing system prompt. At 40 batches per run with identical prefixes, a cache hit would roughly halve the input-token bill.

### 3.3 Batch size and concurrency tuning — **fine, not a bottleneck**

`BATCH_SIZE=20` and `CONCURRENCY=10` with `max_output_tokens=8192` are reasonable. 8192 output tokens is enough for 20 occupations × ~10 skills × 2 tokens/skill. The retry loop handles 429s with exponential backoff up to 5 attempts. No issue here.

### 3.4 Cache behavior and idempotent reload cost — **partial**

- `generate.py` preserves existing `skills` and `description` from an existing `occupations.json` when regenerating from CSV. Good.
- There is no explicit hash of (title, description) → skills cache, so any re-run of `assign_skills.py` re-assigns **every** occupation from scratch instead of only the ones whose input changed.
- `load.py` uses `MERGE` for Region, Occupation, and DEMANDS, which means a reload with shrunk skill lists will leave **stale `REQUIRES_SKILL` edges** behind. `pipeline/reload.py` clears the whole graph upfront so this is not felt in normal operations, but `load.py::load_industry` called standalone is not idempotent in the shrink direction.

### 3.5 Neo4j write cost — **acceptable**

The loader batches in groups of 500 and runs four `UNWIND`-driven writes. With ~279 occupations × 10 regions ≈ 2,790 DEMANDS edges and ~1,600 REQUIRES_SKILL edges, the whole load finishes in a few seconds. Not a hotspot.

## 4. Recommendations

These are grouped by cost and value. All of them are implementable entirely inside `backend/occupations/` unless called out.

### R1. Delete the retired OEWS path and the unused COE parser (low cost, high clarity)

- Remove `oews_parser.py` and `oews_parsed.json`. The pipeline overview explicitly states OEWS has been retired; keeping the module is a trap for readers.
- Remove `coe_parser.py` and `coe_parsed.json`. `generate.py` duplicates the same CSV parse and is the real entry point.
- Remove `occupations_pre_expansion.json` (it is scratch and already untracked in git).

**Impact:** feature directory shrinks by ~250 lines and two large JSON blobs; no behavior change.

### R2. Move the workforce-band filter upstream (medium cost, high efficiency)

- Apply the education-band exclusion in `generate.py` before writing `occupations.json`, not in `load.py`. Add the `"N/A"` case to the exclusion set (picks up SOC `55-9999`).
- Consequence: `occupations.json` becomes the set of occupations the pipeline actually loads (~279 instead of 797), and `assign_skills.py` and `descriptions.py` only operate on that set.

**Impact:**
- ~65% reduction in Gemini token cost per skill-assignment run.
- Clearer provenance: every row in `occupations.json` is a row the graph sees.
- Eliminates the current situation where the log line "Generated 797 occupations" is immediately followed at load time by "Workforce development band: 279 occupations (from 797)".

### R3. Add a post-assignment validation and retry loop (medium cost, high quality)

Replace the silent accept in `assign_skills.py` with a two-stage loop:

1. Run the current batched assignment.
2. After merging results, compute the set of occupations where the post-taxonomy-filtered skill count is below a floor (recommend 6, matching the prompt). Build a retry batch of just those.
3. Send them back to Gemini with a prompt variant that carries the current skill list and says "the following terms were not accepted because they are not in the vocabulary; select replacements from the vocabulary below so that the total is at least 6".
4. Cap at 2 retry passes to bound cost.
5. Emit a post-run report: `(total loaded, below floor, zero skills, off-taxonomy term frequency)`.

**Impact:** direct reduction of the 28% sub-6 tail and the 13 zero-skill cases. This targets the exact quality axis `docs/product/occupations.md` names as the methodological pressure point.

### R4. Feed real context into the skill-assignment prompt (low cost, medium quality)

The current prompt sends `title` + 200 chars of description. For occupations whose description came from the title-pattern fallback (§2.6), this is effectively title-only. Concrete changes:

- Send the full description, not a 200-char truncation. Descriptions generated by `descriptions.py` are 1-2 sentences, not paragraphs.
- Include `education_level` in the per-occupation line so the model can distinguish e.g. "Registered Nurses (Bachelor's)" from "Licensed Practical and Licensed Vocational Nurses (Postsecondary nondegree award)".
- Consider adding the COE-published median wage for the CA statewide row as a soft signal of occupation level.

**Impact:** breaks the generic-skill clustering (Data Analysis, Project Management, Regulatory Compliance dominating) that titles alone produce.

### R5. Fix the `education_level` DEMANDS-vs-Occupation bug (low cost, correctness)

Within `backend/occupations/`:

- `api.py::get_labor_market_overview`: change `d.education_level AS education_level` to `occ.education_level AS education_level` (line 34).
- `api.py::get_occupation_detail` region query: change `d.education_level AS education_level` to `occ.education_level AS education_level` (line 108). Also move the return out of the `DEMANDS` block if it conceptually belongs on the node only.
- `query.py::OCCUPATION_QUERY_PROMPT`: move `education_level: string, typical entry-level education` from the `DEMANDS` property list to the `Occupation` node list. Update example queries to use `occ.education_level` (they already do — only the schema documentation inside the prompt contradicts this).

**Impact:** `/overview` and `/{soc_code}` responses stop returning `education_level: null`. NL query generator is no longer told something false about the graph.

### R6. Improve the description fallback (medium cost, medium quality)

The hand-written path in `SPECIFIC_DESCRIPTIONS` is fine. The pattern fallback is the weak link. Two options, pick one:

- **Cheap:** fold the weakest patterns into a one-shot Gemini call that takes `(soc_code, title, taxonomy-agnostic context)` and returns a 1-2 sentence workforce-description for any occupation `SPECIFIC_DESCRIPTIONS` doesn't cover. Cache the result in `occupations.json` so it is a one-time cost. The loaded band is ~279 occupations, so this is a single ~300-call run.
- **Cheaper but lower quality:** keep the patterns and fix the worst grammatical cases (e.g., `"in chief executives"` → `"as a chief executive"`).

Given R3 and R4 both lean on descriptions being informative, the Gemini-one-shot path pays for itself.

### R7. Add unit tests (low cost, permanent value)

Per `backend/docs/testing.md`, tests target pure logic. The occupations pipeline has several clean extraction targets:

| File | Candidate pure function | What the test guards |
|---|---|---|
| `generate.py` | `_parse_row(row: dict) -> tuple[str, str, dict]` (extract current inline parsing) | Correct numeric coercion; `None` on missing cells; stable row→occupation shape; new `"N/A"` education guard |
| `descriptions.py` | `generate_description(soc_code, title)` already exists | `SPECIFIC_DESCRIPTIONS` hits; pattern fallback for `managers`, `technicians`, `analysts`, `all other`; grammatical outputs |
| `assign_skills.py` | `_filter_to_taxonomy(skills: list[str], taxonomy: set) -> tuple[list, list]` (extract from the current inline validation) | Valid skills kept; invalid skills separated; empty input returns `([], [])` |
| `assign_skills.py` | A new `_below_floor(occupations, floor=6) -> list[SOC]` for the retry queue | Counts correctly; handles missing `skills` key |
| `load.py` | Pure helper `_partition_by_education_band(occupations, exclude)` if R2 keeps a helper form | Inclusion/exclusion symmetric with the docs-product "workforce band" definition |

Each file gets its own `test_<file>.py` colocated, with the top-of-file docstring + `Coverage:` block that `backend_test_docstrings` enforces. Aim for ~25 tests total; this suite is small and pays back every time `generate.py` touches the CSV or `descriptions.py` gains a pattern.

### R8. Introduce an input-hash cache for skill assignment (optional, medium cost)

Hash `(soc_code, title, description, education_level, taxonomy_version)` and store a per-row skill cache keyed by the hash. On re-run, only rows whose hash changed go to Gemini. This is the cleanest way to make `assign_skills.py` idempotent and make the pipeline re-runnable during taxonomy evolution without re-paying for the unchanged 95%.

Only worth doing after R2, R3, R4 land — those change the input shape, which would invalidate early cache entries anyway.

## 5. Coordination requests

These are changes whose value lives outside `backend/occupations/` and therefore must not be made in this session.

### C1. Crosswalk-aware load set (touches `ontology/crosswalks.py` and `pipeline/`)

**Request:** filter the loaded occupation set to SOC codes that are reachable from **any** `TOP4` code in at least one college's calibration, via the TOP→CIP→SOC chain in `ontology/crosswalks.py`. Occupations that no community college curriculum can reach (e.g., `11-1011 Chief Executives`, `11-1031 Legislators`) are dead weight on the graph and concentrate the zero-skill tail observed in §2.3.

**Why surfaced, not implemented:** the crosswalk is a cross-pipeline concern — `partnerships/compute.py` and `pipeline/reload.py` both rely on it, and the right place for a "loadable SOC" helper is inside `ontology/`.

### C2. Taxonomy coverage audit (touches `ontology/skills.py`)

**Request:** produce the distribution of how many times each `UNIFIED_TAXONOMY` term was assigned to any occupation or course. Terms with zero occupation coverage and zero course coverage are candidates for removal or merger; terms whose coverage is dominated by one side (e.g. assigned to 50 occupations but 0 courses) are candidates for better cross-side balance. This is what `docs/product/the-skills-taxonomy.md` calls "the same refinement that would strengthen the courses methodology".

**Why surfaced, not implemented:** `ontology/skills.py` is the single source of taxonomy truth and is a cross-pipeline concern.

### C3. `graph-model.md` clarification on `education_level` placement (touches `docs/architecture/graph-model.md`)

**Request:** after R5 lands, add an explicit line to the `Occupation` row in the graph-model doc clarifying that `education_level` lives on the node (not the edge). The table already says this, but the fact that `api.py` and `query.py` both drifted suggests the placement is easy to miss when reading the doc.

**Why surfaced, not implemented:** `docs/` changes must go through the docs audit and are scoped to a coordination request.

### C4. `pipeline/reload.py` call-site review (touches `pipeline/reload.py`)

**Request:** confirm the reload path invokes `assign_skills.py` after `generate.py` and before `load.py`. From a read of `generate.py`'s "preserve existing skills" branch it is possible to reload the graph from a freshly regenerated `occupations.json` that was never re-assigned — if so, the 48 zero-skill occupations measured in §1 could be an artifact of that sequencing.

**Why surfaced, not implemented:** orchestration is outside the occupations feature.

## 6. Expected impact summary

| Recommendation | Quality | Efficiency | Clarity | Cost |
|---|---|---|---|---|
| R1 Delete dead code | — | — | high | low |
| R2 Upstream workforce-band filter | medium | high (~65% token save) | high | medium |
| R3 Validation + retry loop | high (target the pressure point) | mild cost | medium | medium |
| R4 Richer prompt context | medium | — | — | low |
| R5 Fix `education_level` bug | correctness | — | medium | low |
| R6 Description fallback → Gemini one-shot | medium | — | medium | medium |
| R7 Unit tests | regression floor | — | high | low |
| R8 Input-hash cache | — | medium (reload) | — | medium |
| C1 Crosswalk-reachable SOC filter | high | medium | high | depends on shared infra |
| C2 Taxonomy coverage audit | high | — | high | depends on shared infra |
| C3 Doc clarification | — | — | medium | trivial |
| C4 Reload sequencing review | correctness | — | medium | trivial |

The highest-leverage pipeline-local sequence is **R1 → R5 → R2 → R4 → R3 → R7**. R1 clears the decks; R5 is a one-line correctness fix; R2 shrinks the working set so R3 and R4 operate on the occupations that actually get loaded; R3 and R4 together attack the skill-assignment tail that `docs/product/occupations.md` names as the load-bearing quality axis; R7 locks the wins in.

R6 and R8 are reasonable follow-ups but can wait.

C1 is the single largest outside-pipeline lever. It is the only change that would meaningfully reduce the "skills assigned to occupations no college can reach" noise, and it is a precondition for the skill-gap-identification capability the product doc identifies as the unique value the refinement unlocks.
