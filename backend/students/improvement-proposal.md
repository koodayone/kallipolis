# Students pipeline — improvement proposal

*Analysis-only pass. No code changes. Scope: `backend/students/`.*

## 1. Current state

The students feature is four files plus a test:

| File | Role |
|---|---|
| `generate.py` | End-to-end synthetic student generator + Neo4j loader (~660 lines) |
| `load` → same file | `load_students()` batch-writes enrollments and materializes derived fields |
| `helpers.py` | `compute_gpa`, `compute_primary_focus` — pure functions used by the loader and the API |
| `api.py` | FastAPI router: list / detail / NL query |
| `query.py` | LLM-backed Cypher generator for student queries |
| `models.py` | Pydantic schemas |
| `test_helpers.py` | 12 unit tests — all passing |

### Pipeline flow (per college)

Invoked from `pipeline/run.py` as Stage 4 after courses + skills are loaded:

1. **Calibration load** — reads two JSONs per college:
   - `ontology/calibrations/<key>.json` for `enrollment`, `ft_ratio`, `retention_rate` (plus unused 2-digit TOP data).
   - `ontology/calibrations/top4/<key>.json` for per-4-digit-TOP-code grade distributions and enrollment shares.
2. **Prefix → TOP4 mapping** — built from the college's own Master Course File CSV (`~/Desktop/cc_dataset/mastercoursefiles/MasterCourseFile_<key>.csv`), with a system-wide fallback at `ontology/calibrations/prefix_to_top4.json`. Aliases and "ENGL C" → "ENGL" concurrent-enrollment variants are resolved by `_resolve_prefix`.
3. **Course pool building** — each enriched course is assigned to its TOP4's pool, skipping non-credit and zero-unit courses. The authoritative TOP4 → department name mapping is derived from the pool contents (most common department per pool).
4. **Student loop** — for each of `num_students`:
   - Assign primary TOP4 by enrollment-share weighted draw.
   - Sample FT/PT via `ft_ratio`.
   - Pick a starting season from `START_TERM_WEIGHTS` and walk forward through a fixed 9-term sequence (2022 Fall → 2024 Spring), breaking on a retention coin flip.
   - Per term, draw `FT_LOADS`/`PT_LOADS` courses with `PRIMARY_STICKINESS = 0.60` from the primary pool, else from a share-weighted random TOP4. Enforce `DEPT_CAP = 6`, `taken_codes` dedup, and a `FT_UNIT_CAP`/`PT_UNIT_CAP` per-term unit ceiling.
   - Sample each grade from that TOP4's DataMart grade distribution (Pass/No Pass uses a hardcoded `{P: 0.85, NP: 0.15}`).
5. **Neo4j load** — `DETACH DELETE` existing students for the college in 1000-row batches, then `UNWIND` enrollments in `BATCH_SIZE = 500` writes with `MERGE (Student) ... CREATE (Student)-[:ENROLLED_IN]->(Course)`. Runs a blanket `MERGE` to materialize `HAS_SKILL` from completed enrollments. Finally, it **re-reads every student's enrollments from Neo4j** and re-`SET`s `gpa`, `primary_focus`, `courses_completed` per student in 500-row batches.
6. **Validation** — logs the synthetic success rate against the weighted DataMart target, diff only.

### What works

- Pure-logic helpers are tested and passing (`pytest students/` → 12/12).
- Calibration data exists for the full CCC system: 128 2-digit calibrations, 179 TOP4 calibrations. Foothill's TOP4 file is well-shaped.
- Deterministic seed path is threaded end-to-end (`Random(seed)` is the only RNG; `uuid5(NAMESPACE, ...)` for student IDs).
- The feature directory conforms to `backend/README.md` conventions — `generate.py`, `api.py`, `query.py`, `helpers.py`, `models.py`, colocated `test_helpers.py` — so feature-primary audits pass.

## 2. Quality and efficiency evaluation

### Quality — correctness and calibration fidelity

**Q1. Summer is dead code.** `START_TERM_WEIGHTS` gives Summer 5% weight and `SUMMER_ENROLLMENT_RATE = 0.15` filters summer terms from the active sequence, but `_build_term_sequence()` only emits `{year}-Fall`, `{year}-Winter`, `{year+1}-Spring` — no Summer term is ever produced. Two consequences:

- 5% of students whose starting season rolls "Summer" fail the `term.endswith(start_season)` lookup and silently start at `start_idx = 0` (Fall 2022) instead. This is a miscalibration of the starting-cohort distribution.
- `SUMMER_ENROLLMENT_RATE` and the `-Summer` filter are unreachable.

**Q2. `RETAKE_RATE = 0.05` is dead code.** Defined at module top, never referenced. `taken_codes` is a strict per-student set with no bypass. Retakes — a real phenomenon the constant acknowledges — do not occur.

**Q3. Every student starts in 2022.** `start_idx` is computed by scanning `all_terms` for the *first* term ending in the chosen season, so every Fall starter starts at `all_terms[0]` (Fall 2022), every Winter starter at `all_terms[1]`, etc. There is no multi-year cohort spread. A population generated with `num_students = 14135` has zero students who began in 2023 or 2024. For a 3-year window with fall-to-winter retention ~93%, the resulting persistence distribution is heavily skewed toward the first year rather than spread across cohorts.

**Q4. Retention semantics are conflated.** `retention_rate` is documented and sourced as the college's fall-to-winter retention rate (Foothill: 0.9275) — a one-step figure. It is applied as a per-term geometric decay across nine terms. This is not the same thing as "fall-to-winter retention," and the two numbers happen to be compatible only because per-term retention is already naturally high. It should either (a) be documented as "per-term retention coin-flip" (which is what the code actually does) or (b) be replaced with a per-term rate derived from multi-term persistence data.

**Q5. Retention loop has a structural off-by-one bias.** The loop starts at `max_terms = 1` unconditionally, then flips. First-term retention is therefore 100%, which slightly inflates the first-term population.

**Q6. Calibration validation is aggregate-only.** The validation step compares the population's total success rate against the DataMart-weighted target and logs a single diff. It does not validate:

- Per-TOP4 enrollment share drift (DEPT_CAP and unit caps can and do deflect draws).
- Per-TOP4 success-rate fidelity (the claim in `docs/pipeline/student-generation.md` that "every course's grade is sampled from the empirical distribution for that course's TOP code" is structurally true at draw time but the aggregate assertion doesn't verify it survived the sampling).
- Primary-focus distribution drift vs. the declared primary-TOP4 distribution.

**Q7. `DEFAULT_GRADES` fallback is not a distribution of the college.** When TOP4 calibration is missing, every enrollment draws from a hardcoded `{A: .55, B: .18, C: .08, D: .02, F: .07, W: .07, P: .01}`. This is neither DataMart-derived nor per-college. In the fallback path the documentation's structural-fidelity claim breaks cleanly — worth surfacing that the fallback is a stub, not a backoff.

**Q8. `primary_focus` is double-derived inconsistently.** At generation time, the authoritative TOP4 → department name comes from the course pools (most common department per TOP4). But `api.py`'s `GET /{student_uuid}` ignores the materialized `primary_focus` and **recomputes it** from the live enrollment list on every request, using a plain max-by-department count. Two systems of record for the same field. This also means the detail endpoint can disagree with the list endpoint.

**Q9. GPA is computed twice on the same student.** `load_students` calls `compute_gpa(grades)` against the re-read Neo4j payload. `api.py`'s detail endpoint calls `compute_gpa` again against a different re-read. Both use the same helper, so they agree — but both ignore the in-memory grades produced in `generate_students`.

**Q10. Skill materialization is binary.** `MERGE (st)-[:HAS_SKILL]->(s)` with no count / strength / recency property. A student who completed one welding course and a student who completed four welding courses are indistinguishable in the graph. Whether this is a bug depends on how partnership generation reads the edge — but it is a lossy projection of the underlying evidence.

**Q11. Untested surface area is large.** `test_helpers.py` only covers `compute_gpa` and `compute_primary_focus`. The entire generator — ~660 lines of pure logic with no Neo4j dependencies — has no unit tests. Specifically:

- `_parse_units` — handles `"4.5"`, `"1-2"`, `"3unit(s)"`. Untested; "1-2" case averages via a second regex pass that could silently misparse.
- `_course_prefix`, `_resolve_prefix` — the "ENGL C" concurrent-enrollment carve-out has a "space required" guard specifically because of `"AGTC"`, which is exactly the kind of rule a test should pin.
- `_build_term_sequence` — would catch Q1 immediately.
- `_build_top4_course_pools` — can be tested with a fake calibration and a tiny course list.
- The main `generate_students` function itself is deterministic given a seed and takes plain-dict inputs; a fixture-based test would catch Q1/Q2/Q3 and freeze algorithmic behavior against regressions.

### Efficiency

**E1. Post-hoc Neo4j read-back is wasted work.** `load_students` writes enrollments, then *reads every student's enrollments back out of Neo4j* via `MATCH (st)-[e:ENROLLED_IN]->(c {college: $inst}) ... RETURN st.uuid, collect(...)` purely to compute `gpa`, `primary_focus`, `courses_completed` — all of which are trivially computable from the in-memory `GeneratedStudent.enrollments` that was just written. For a 14k student college, that's one full enrollment read-back round-trip whose only output is three derived fields, followed by 28+ batched `SET` queries. On `foothill` this doubles the Neo4j round-trip count for the load stage.

**E2. Inner-loop allocations in the hot path.** The per-enrollment draw allocates a fresh `available = [c for c in pool if ...]` list comprehension, sometimes twice (if the first pool is exhausted). For `num_students × avg_courses_per_student` enrollments and pools that often contain dozens of courses, this is O(students × courses/student × pool_size). Not catastrophic at 14k students but a clean target for batching or a per-student mutable mask.

**E3. `rng.choices(valid_codes, weights=top4_weights, k=1)` recomputes cumulative weights every call.** `random.choices` accepts `cum_weights` to skip the cumulative-sum step; precomputing once would noticeably cut per-draw overhead. Same pattern appears 2–3× per enrollment.

**E4. MCF prefix map is re-parsed per call.** `_load_college_prefix_map` has no memoization. For a single-college run this is fine; for the reload path that iterates all colleges (`pipeline/reload.py`), it's N re-parses. Low cost, easy fix with `functools.lru_cache`.

**E5. `_FALLBACK_PREFIX_TOP4` module-global mutable cache.** Lazy-init via a module-level dict is the Python idiom this replaces. Swap for `@lru_cache`.

**E6. Clear-existing-students loop.** Already batched at 1000, fine. Nothing to do.

**E7. Write batch size 500.** Reasonable for Neo4j's default driver; unlikely to be the bottleneck given E1 exists.

**E8. `MERGE (s:Student {uuid: row.uuid})` per row in the enrollment write path.** Each batch MERGEs then MATCHes the course by `{code, college}`. Since UUIDs are freshly generated (and the entire college's students were just deleted), the MERGE could be a `CREATE` with a pre-write of student nodes, cutting one index probe per enrollment. Marginal.

### Algorithmic fidelity concerns beyond bugs

- **60/40 split is only approximately calibrated.** The 40% random-draw is weighted by enrollment share *excluding* TOP4s that have no courses. If a DataMart TOP4 has real enrollment but no matching catalog courses (unmapped prefixes), its share is silently redistributed across the remaining TOP4s. This is the right call — you can't sample a course you don't have — but the redistribution is not reported.
- **DEPT_CAP conflict with primary stickiness.** A student concentrating in Accounting hits `DEPT_CAP = 6` in Accounting and the generator silently redirects to a random TOP4 for the rest of their course history. For highly concentrated programs this caps concentration at 6, which is actually lower than a realistic upper-division courseload of 8–12 in a 3-year window. Consider raising the cap or making it TOP4-aware instead of department-aware.

## 3. Concrete improvements

Grouped by impact and ordered roughly by cost. All are confined to `backend/students/` unless flagged as coordination.

### Tier 1 — correctness bugs (low cost, high impact)

1. **Fix Q1: remove dead Summer handling or implement it.** Either drop `SUMMER_ENROLLMENT_RATE` and the `Summer` weight from `START_TERM_WEIGHTS`, or extend `_build_term_sequence` to emit a Summer term per year and let the existing filter do its job. Decide based on whether the DataMart calibration actually includes Summer enrollments for the college. Expected impact: restores the documented 5% Summer-start cohort and eliminates the silent "start at Fall 2022 instead" fallback.
2. **Fix Q3: spread start cohorts across years.** Pick a starting `(year, season)` jointly rather than just a season, weighted so the population includes students who began in 2022, 2023, and 2024. Expected impact: the persistence curve actually reflects a steady-state enrollment; today the population is dominated by 2022 starters.
3. **Fix Q2: decide on retakes.** Either implement `RETAKE_RATE` (remove from `taken_codes` with 5% probability per course) or delete the constant. Leaving dead constants in a calibration-heavy file is a correctness smell.
4. **Fix Q5: seed the retention loop from zero.** Start `max_terms = 0` and let the first coin flip decide whether the student persists beyond their first term. Low impact but correct.
5. **Drop or per-college-ify `DEFAULT_GRADES`.** Replace with a "no fallback available — log and skip" path, or compute a per-college default from the 2-digit `grade_distribution` in the existing calibration JSON. Pure fallback stubs shouldn't silently shape the output.

### Tier 2 — efficiency

6. **Eliminate the post-write read-back (E1).** Compute `gpa`, `primary_focus`, `courses_completed` in `generate_students` directly from `GeneratedStudent.enrollments` and `top4_to_dept`, return them on the dataclass, and set them in the same `UNWIND` batch that creates the student node. Cuts one full-population Neo4j round-trip from every load. This is the single highest-value efficiency change and is purely local.
7. **Precompute `cum_weights` for the TOP4 draw (E3).** One-time cost at generation start, saves ~2 cumulative sums per enrollment.
8. **Memoize `_load_college_prefix_map` (E4) and replace `_FALLBACK_PREFIX_TOP4` global with `lru_cache` (E5).** Cleanup, not hot-path; buy it if you're already in the file.

### Tier 3 — legibility and testability

9. **Add unit tests for the generator.** Target in priority order: `_parse_units`, `_course_prefix` + `_resolve_prefix`, `_build_term_sequence`, `_build_top4_course_pools` (fixture-based), and a small-fixture `generate_students` test that pins the grade-sampling behavior and primary-TOP4 selection for a fixed seed. Follow the existing `test_helpers.py` docstring and class-grouping conventions documented in `backend/docs/testing.md`.
10. **Split `generate.py` into smaller modules inside `students/`.** Suggested shape:
    - `students/calibration.py` — `_load_calibration`, `_load_top4_calibration`, prefix-map loaders.
    - `students/pools.py` — pool building, TOP4 → department derivation.
    - `students/generate.py` — core student loop only.
    - `students/load.py` — Neo4j writer.
    Each becomes independently testable, and `generate.py` drops from ~660 lines to something readable in one screen. File layout stays feature-primary.
11. **Remove `api.py`'s recomputation of `primary_focus` and `gpa` in the detail endpoint.** Read the materialized fields; keep the live re-aggregation only if the endpoint has a separate contract to show "as of right now."

### Tier 4 — observability and fidelity

12. **Expand the validation step.** Add to `GenerationStats` and log:
    - Per-TOP4 share delta (synthetic share − DataMart share) with top-5 largest absolute deltas.
    - Per-TOP4 success-rate delta.
    - Total redistribution weight (sum of enrollment share for TOP4s dropped because they had no courses).
    Gives the honesty-of-methodology claim from `docs/product/students.md` something concrete to stand on, without changing the algorithm.
13. **Report course-pool coverage.** The current log line `Course pools: N courses across M/K TOP4 codes (U unmapped)` is good; add the names of unmapped prefixes and the share of total catalog units they represent. Turns unmapped prefixes from a silent 3% tail into an actionable list.

### Not recommending

- **DDD refactor of the student module.** `MVP Sequencing` in memory notes DDD is deferred. Splitting into calibration/pools/generate/load (Tier 3 #10) is the right altitude for now.
- **Rewriting to numpy-vectorized sampling.** The hot path is not hot enough to justify the dependency. Precomputing `cum_weights` captures most of the win.
- **Introducing a background worker or async generation.** The pipeline is offline batch; not worth the complexity.

## 4. Expected impact summary

| Change | Correctness | Perf | Testability |
|---|---|---|---|
| Fix Summer dead code (Q1) | Restores 5% Summer cohort | — | — |
| Spread start cohorts (Q3) | Persistence curve reflects steady state | — | — |
| Retention loop off-by-one (Q5) | Minor fidelity improvement | — | — |
| Eliminate Neo4j read-back (E1) | — | ~1 full-population round-trip removed per load | — |
| Precompute `cum_weights` (E3) | — | Modest hot-loop win | — |
| Split `generate.py` (T3 #10) | — | — | Each stage becomes independently testable |
| Generator unit tests (T3 #9) | Freezes current behavior against drift | — | Large coverage gain |
| Validation expansion (T4 #12) | Makes fidelity claims auditable | — | — |

## 5. Coordination requests

The following touch shared infrastructure and are flagged rather than attempted:

- **Adding `strength` / `count` to `HAS_SKILL`** (Q10) is a graph-model change. It would affect `docs/architecture/graph-model.md`, potentially the partnerships and occupations reads, and the atlas's skill-surface components. Needs a design decision on whether skill evidence should be graded by exposure count. Flagging, not changing.
- **Calibration JSON schema clarification** for `retention_rate` (Q4): the field is consumed in `students/generate.py` but lives in `backend/ontology/calibrations/*.json`. If we decide to rename or re-derive it, that's an ontology-level change and should be coordinated with the calibration prep scripts in `pipeline/` that write these files.
- **Recomputation in `api.py`'s detail endpoint** (Q8) reads from Neo4j using fields that Tier 1 / Tier 2 would change. The endpoint is inside `backend/students/` so this is in-scope — but a downstream atlas component may depend on the current recomputation behavior for real-time consistency. Flag before removing.
- **Multi-year start cohort** (Tier 1 #2) changes the term strings stored on `ENROLLED_IN` edges, which affects any existing query that assumes terms `{2022-Fall, 2022-Winter, ..., 2024-Spring}`. `query.py`'s LLM prompt mentions "Fall 2024" as an example. Flag for coordinated update of the prompt examples when this change lands.
- **Adding a `Summer` term** (Tier 1 #1, option A) has the same downstream-term-string concern as the point above.

## 6. Test baseline

```
cd backend && python3 -m pytest students/
============================== 12 passed in 0.01s ==============================
```

All existing tests pass. No regressions would be introduced by the proposal; the Tier 3 test additions are the forcing function that will *find* regressions when Tier 1 fixes land.
