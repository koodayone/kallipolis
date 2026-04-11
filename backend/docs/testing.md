# Backend testing

This document is the contract for how tests are written and organized in the backend. It is load-bearing for the test suite's legibility and for the documentation audit that verifies it. Read this before adding a new test file, moving tests around, or changing the test conventions.

The backend test suite is deliberately narrow right now. It exercises pure logic — the `helpers.py` in each feature, the `validate_cypher` safety gate in `llm/query_engine.py`, the string normalizers in `ontology/mcf_lookup.py`, the JSON parser and narrative-field helpers in `partnerships/`, and the name-cleaning and deduplication helpers in `employers/generate.py`. It does not exercise Neo4j, the Anthropic or Gemini APIs, the FastAPI routers, or any integration flow. Adding those is a future commitment; the conventions below are designed so the pass is cheap to start and the suite can grow without losing legibility.

## Philosophy

**Tests exercise units, not features.** A test file targets one module, one exported function, or one small cluster of related functions. A feature can have many test files, each focused. This keeps individual test files small and keeps the relationship between "what is this testing?" and "what does this file contain?" obvious from the filename alone.

**Test names read as specifications.** A reader skimming the test file or running `python -m pytest -v` should see sentences describing what the unit does, not noun phrases describing what the test is. `test_returns_four_when_all_grades_are_a` is a specification. `test_all_a_returns_four` is less clear; `test_all_a` would be worse. Python's identifier rules constrain the form — you cannot use spaces or quotes in function names — but the goal is still that reading the function name out loud produces a sentence about the unit's behavior.

**Pure logic first.** Anything that can be tested without Neo4j, without an LLM, without a network call, is tested that way. Integration tests that require live infrastructure live at `backend/tests/integration/` and are not part of the unit suite or CI. This is a sequencing decision, not a permanent rule — when the unit suite is load-bearing and the failure modes of integration tests are well understood, adding CI-gated integration runs becomes viable.

## Framework

**pytest** is the test runner. Standard Python testing framework, native fixture support, excellent parametrization, readable error output, and zero ceremony around test discovery. The configuration lives at `backend/pyproject.toml` under `[tool.pytest.ini_options]`.

Tests are picked up by the pattern `test_*.py`, discovered recursively from the directories listed in `testpaths`. The `testpaths` list is explicit (`students`, `courses`, `occupations`, `employers`, `partnerships`, `strong_workforce`, `ontology`, `llm`) rather than a glob — adding a new feature directory requires updating the list, which is a deliberate forcing function that prevents silent test coverage gaps.

## File organization

**Tests colocate with the source files they exercise.** A test for `helpers.py` lives at `test_helpers.py` in the same folder. This matches the feature-primary principle documented in [`docs/conventions.md`](../../docs/conventions.md) and mirrors the atlas's colocation convention. A feature's tests are part of the feature they exercise, not a centralized parallel tree.

Colocation has three concrete benefits. A reader looking at a feature folder sees which files have tests and which don't without navigating to a separate tree. An agent changing a file can find its test without a search. Moving or renaming a feature moves its tests atomically.

The one exception — integration tests that span multiple features — lives at `backend/tests/integration/` because those tests are not feature-local by definition. A test exercising partnerships, occupations, and students simultaneously doesn't belong to any one feature, so it goes in a category directory that names what it is rather than where in the feature tree it "attaches." This is not a per-ecosystem exception; the same semantic rule applies to any future atlas integration tests.

## Top-of-file module docstring with Coverage section

**Every `test_*.py` file in a feature directory begins with a module docstring that names the unit under test and lists the coverage areas.** This is the mechanism for per-feature legibility: a reader can open any test file and understand in plain language what it guards without running pytest and without reading every `def test_*` function.

The docstring has a fixed shape:

```python
"""Unit tests for <module name> — <one-line description of what the unit does>.

<optional: one or two paragraphs of context about why these tests
matter, what makes this unit worth guarding, what mocking pattern
is used, etc.>

Coverage:
  - <first coverage area, phrased as an outcome>
  - <second coverage area>
  - <third coverage area>
"""
```

**The docstring is required.** The documentation audit has a check (`backend_test_docstrings`) that scans every backend test file and fails if it is missing the module-level docstring or the `Coverage:` label. Missing docstrings block merge to `main`.

**Why the docstring matters when individual `test_*` function names already exist.** The function names tell you what a specific test asserts; the docstring tells you what the file as a whole guards. A reader skimming the suite wants "the helpers test file covers the GPA derivation, the primary-focus derivation, and their empty-input defaults" as a single sentence, not as an inference from twelve individual function names. The docstring is the summary index; the function names are the line items.

**How to update it.** When you add a test that covers a new area, add a bullet to the Coverage list in the same commit. When you remove or refactor a test, update the list. Drift is possible — the audit only checks that the header exists, not that its contents match the tests — so the convention relies on author discipline at write time. Reviewers should reject test PRs where the Coverage list does not match what the tests assert.

## Test naming convention

- **`class` names group related assertions within a file.** Test classes are named `Test<Subject>` where `<Subject>` is the function, method, or behavior cluster under test. Examples: `TestComputeGpa`, `TestReadOnlyEnforcement`, `TestDeduplicateBranches`.
- **`def test_*` names read as specifications.** A good test function name reads as the sentence "the unit ... when ...". Examples: `test_returns_four_when_all_grades_are_a`, `test_rejects_lowercase_write_keywords`, `test_collapses_duplicate_names_to_the_largest_size`.
- **Avoid meta-phrasing.** `test_tests_X`, `test_should_X`, and `test_verifies_X` all add noise. Write the specification directly: `test_X_when_Y` or `test_X_with_Y`.

The goal is that `python -m pytest -v` produces output a non-author can read to understand what the suite covers. Python's identifier rules restrict the form (no spaces, no quotes), so names end up as `snake_case_with_underscores_between_words`, but they should still read as grammatical sentences about unit behavior.

## Mocking pattern

Most backend pure-logic tests need no mocking — `compute_gpa`, `validate_cypher`, `_extract_json`, `_clean_employer_name` all take plain arguments and return plain values. When mocking is unavoidable (e.g., patching Neo4j driver calls in a future integration test), use `unittest.mock.patch` or `pytest-mock` conventions. Avoid module-scope patching when a narrower `with patch(...)` block will work — narrower scopes make tests more self-contained and easier to read.

## Out of scope (for now)

The following are deliberately not tested yet. They belong in future sessions:

- **Neo4j integration.** Any code path that hits `get_driver()` or issues Cypher queries at runtime. The integration tests under `backend/tests/integration/` cover some of this but they are not wired into CI and require a live database.
- **LLM calls.** Any code path that calls `anthropic.Anthropic` or the Gemini client. Testing these would require either live API keys (expensive and slow) or elaborate mocking of the client library (brittle and low-signal).
- **FastAPI routers.** Each feature's `api.py` is exercised indirectly through integration tests but has no dedicated unit tests. Adding those would require `TestClient` setup and fixture management.
- **Pipeline orchestration.** `pipeline/run.py` and `pipeline/reload.py` are integration-level concerns and are not unit tested.

## Canonical commands

```bash
# Run the full suite once (via pyproject.toml testpaths discovery)
cd backend && python3 -m pytest

# Verbose output — prints every test function name
cd backend && python3 -m pytest -v

# Run one feature's tests only
cd backend && python3 -m pytest students/

# Run integration tests (requires Neo4j + ANTHROPIC_API_KEY)
cd backend && python3 -m pytest tests/integration/
```

## When you add a new test file

1. **Create it next to the source file**, not in a central `tests/` folder. A test for `backend/students/helpers.py` goes at `backend/students/test_helpers.py`.
2. **Name it `test_<source>.py`.** pytest's default discovery pattern.
3. **Start with the module docstring.** Copy the shape above and fill in the unit name, context paragraph, and Coverage bullets.
4. **Write `class Test*` groupings and `def test_*` functions as specifications.** Read the function name out loud to check that it reads as a sentence.
5. **Run `python3 -m pytest`** to verify the harness picks it up.
6. **Run `python3 tools/docs-audit/audit.py`** to verify the docstring passes the `backend_test_docstrings` check.
7. **Include the test file's additions in the same commit** as the source change it covers, or the commit that introduces the unit being tested.

If the test is for a new feature directory that is not yet in `backend/pyproject.toml`'s `testpaths` list, add the directory name to `testpaths` in the same commit. Without that addition, pytest will not discover the new feature's tests.

## Where to go next

- [`docs/conventions.md`](../../docs/conventions.md) — the repo-wide contract for file layout, vocabulary alignment, and test location rules that both backend and atlas honor.
- [`backend/README.md`](../README.md) — the backend orientation document with the quick-start commands.
- [`atlas/docs/testing.md`](../../atlas/docs/testing.md) — the atlas's parallel testing conventions document.
- [`tools/docs-audit/checks/backend_test_docstrings.py`](../../tools/docs-audit/checks/backend_test_docstrings.py) — the audit check that enforces the module docstring convention.
