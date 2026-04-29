# Kallipolis

## Orientation

If you need broad context on the project, read `docs/README.md` — it is an annotated index of every doc in the documentation tree with a one-line description of each.

## Documentation work

Before creating or modifying any file under `docs/`, read `docs/conventions.md`. It is the contract for voice, altitude, structural patterns, and the structured forms (file paths, schema tables, API tables, model names, numerical constants, relationship tables) the documentation audit verifies.

After any doc change, run the audit:

```bash
python3 tools/docs-audit/audit.py
```

A failing audit blocks merge to `main`. Resolve failures before considering the change complete.

## Backend and frontend structural work

Before adding a new feature directory (backend or atlas), a new URL route, a new product doc under `docs/product/`, or any other surface form tied to an ontology unit, read the "Feature-primary layout and vocabulary alignment" section in `docs/conventions.md`. The feature-primary layout and the cross-stack vocabulary alignment are enforced by two audit checks — `backend_layout` and `vocabulary_alignment` — that will block merge to `main` on any violation. That section also documents the workflow for adding a new unit, adding a meta doc, and adding an exemption.

## Reasoning hygiene

Before quoting an API cost projection above ~$5, run a small calibration (5–20 calls on the actual workload) to get a measured per-call cost. Multiply through to project. Refuse to extrapolate from an unmeasured estimate.

Never derive per-call cost by dividing aggregate spend by call count when other activities share the same budget window — that conflates activities and produces fake numbers.

When a measurement disagrees with a prior estimate, halt before continuing to act. Re-derive the estimate from first principles, name what was wrong, re-state the recommendation, then continue. Surprises that go unexamined turn into compounded mistakes.

Claims about system behavior — rate limits, throttling, peak hours, performance bottlenecks — require an empirical test in this session OR an explicit "I'm guessing" caveat. "It's probably peak hours" is not allowed as a confident assertion.
