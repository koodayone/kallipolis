# Confirmation run — 2026-07-14 (deployed-priming, Session 1)

Full evidence for the post-deploy DOCTRINE confirmation. Scorecard narrative + verdict:
`research/architecture/LAYER3-CONFIRM-RUN.md`.

- `transcripts/` — 21 model-under-test captures (9 affected pathways with the 3 borderline ×3,
  provenance-and-conflation, 5 onboarding). Driver prompts were DOCTRINE-neutral: the priming reached
  the analyst only through the live MCP tool descriptions.
- `verdicts/` — one judge verdict per transcript (constitution I–V + four tensions + establishment for
  onboarding), graded against the latest-main `judge.md` / `constitution.md`.
- `scorecard.json` — machine-readable grades, tension leans, `fix_layer`, `words_per_turn`, pre-gate.
- `harness/` — the generators that produced this run (driver prompts, judge prompts, pre-gate + stats,
  aggregation, assembly). Re-runnable against `pathways.py`.

Tier A gate: `9 passed` (test_substrate.py + test_compare.py referential/corroboration). Seed graph:
`eval-neo4j` on `bolt://localhost:7691`. Headline: the lift reproduced PARTIALLY — concision /
inform-don't-decide / contingent-pick / onboarding all held; a standing Principle V "offer-the-view"
gap (+ IV next-move, two I slips) surfaced once capture recorded `view_link` faithfully.
