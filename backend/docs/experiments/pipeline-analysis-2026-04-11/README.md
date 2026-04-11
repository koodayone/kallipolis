# Pipeline parallelization analysis — 2026-04-11

Point-in-time experimental artifacts from a four-way parallelization experiment on the backend's entity generation pipelines. Four fresh Claude Code sessions were dispatched on 2026-04-11, one per pipeline, each with an identical constraint: read one feature directory end-to-end, evaluate quality and efficiency along whichever axes were meaningful for that specific pipeline, and produce a proposal document describing the current state and recommended improvements. The sessions ran in parallel and did not share context.

## What this directory contains

| File | Pipeline analyzed | Feature directory |
|---|---|---|
| [`students.md`](./students.md) | Synthetic student generation | `backend/students/` |
| [`courses.md`](./courses.md) | Catalog scraping and Gemini-mediated course extraction | `backend/courses/` |
| [`occupations.md`](./occupations.md) | COE parsing, skill assignment, and Neo4j loading | `backend/occupations/` |
| [`employers.md`](./employers.md) | EDD scraping, name cleanup, and cross-college merge | `backend/employers/` |

## What it is, and what it is not

**This is a historical record of one analytical pass.** The observations below reflect the state of the pipelines at 2026-04-11. Some of the in-scope improvements identified in each proposal have since been implemented in follow-up sessions; some of the coordination requests — cross-cutting concerns that could not be resolved inside a single feature directory — remain open as of the archive date and feed the shared-infrastructure refinement work that followed this experiment.

**This directory is not audited by `tools/docs-audit/`.** The documentation audit walks `docs/` at the repo root but does not walk `backend/docs/` — see `backend/docs/testing.md` and `backend/docs/structure-refactor.md` for the other unaudited backend-internal notes that live under the same tree. The reason this archive is unaudited is deliberate: its content is a snapshot of a specific moment, and forcing it to pass an audit that verifies code-grounded claims against the *current* code would require editing the archive every time the code drifts away from what was observed. That would defeat the purpose of archiving.

Treat these files the way you would treat an incident report, a design review record, or a meeting summary: useful for understanding the reasoning at the time, not a source of truth for the current code. If you need to know what a pipeline currently does, read the code. If you need to know what an earlier reader thought the pipeline did on a specific date and what they recommended changing, these documents are your reference.

## Why it exists as an archive rather than as live documentation

Two decisions shaped the archival form:

1. **Keeping the analysis durable.** The four proposals represented substantial analytical work — 1,084 lines of concrete observation, measurement, and recommendation, spread across the four pipelines. Losing that work to session ephemera would have meant re-deriving it from scratch the next time a contributor wanted to understand why a particular shared-infrastructure change was made. The archive preserves the analytical reasoning behind the follow-up work, which is often more valuable than the work itself.

2. **Not polluting feature directories with stale-prone prose.** The proposals initially lived alongside code as `backend/<feature>/improvement-proposal.md`. That location had two problems: the files would drift out of sync with the code they described on natural timescales, and they occupied the same filesystem space as audit-verified feature code, which blurred the distinction between "code with mechanical guarantees" and "prose that happens to be nearby." Moving the proposals into `backend/docs/experiments/` under a timestamped subdirectory names them explicitly as time-bound artifacts and removes them from the feature-local working sets.

## The experiment this archive records

For the broader context on why the experiment was run and what it was designed to test, see the conversation record — this archive is a narrow slice of a larger discussion about agentic-first development and whether the feature-primary backend refactor enabled parallel agentic work on non-overlapping scopes. The short version: yes, the parallelization worked, and the four proposals below are the evidence.
