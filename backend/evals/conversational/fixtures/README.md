# Conversational-eval regression fixtures

Frozen transcripts that cleanly passed the confirmation run (Session 1, 2026-07-14, deployed priming,
Opus 4.8). A fixture "cleanly passes" = all of constitution I–V graded `pass`, all four tensions
`balanced`, establishment `pass` for onboarding pathways, and no contested "feeds"-verb usage.

Use them as regression anchors: re-drive the same pathway on a future priming and a judged verdict that
drops any I–V to partial/fail (or leans a tension) is a regression to investigate. Grades and per-turn
word counts are recorded in `fixtures.json`; the source run and full scorecard are in
`../runs/confirm-2026-07-14/` and `research/architecture/LAYER3-CONFIRM-RUN.md`.

Transcript shape is the one `checks.py` documents. These are model-under-test captures (the analyst
reports its own tool calls/figures); trust-but-cross-check with the judge, per the run's v1 caveat.
