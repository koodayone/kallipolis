"""Run the canonical checks.py pre-gate on every captured transcript + compute concision stats.

Writes per-transcript pregate JSON to scratchpad/pregate/<id>.json and prints a summary table
(pre-gate pass count, analyst turns, words/turn) so the scorecard can compare to the baseline's
~-34% words/turn target.
"""
import importlib.util
import json
import os
import re
import sys

EVAL_DIR = "/Users/dayonekoo/Desktop/code/kallipolis/.claude/worktrees/eval-main/backend/evals/conversational"
SCRATCH = "/private/tmp/claude-501/-Users-dayonekoo-Desktop-code-kallipolis/6eef9907-426f-4cda-9197-08bf8bd2c76b/scratchpad"
TRANSCRIPTS = os.path.join(SCRATCH, "transcripts")
PREGATE = os.path.join(SCRATCH, "pregate")

spec = importlib.util.spec_from_file_location("checks", os.path.join(EVAL_DIR, "checks.py"))
checks = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checks)


def words(text):
    return len(re.findall(r"\S+", text or ""))


def main():
    os.makedirs(PREGATE, exist_ok=True)
    files = sorted(f for f in os.listdir(TRANSCRIPTS) if f.endswith(".json"))
    print(f"{'transcript':38} {'pregate':>8}  {'turns':>5} {'w/turn':>7}  failing_checks")
    print("-" * 90)
    rows = []
    for f in files:
        path = os.path.join(TRANSCRIPTS, f)
        try:
            t = json.load(open(path))
        except Exception as e:
            print(f"{f:38} LOAD-ERROR {e}")
            continue
        res = checks.run(t)
        analyst_turns = [x for x in t.get("turns", []) if x.get("role") == "analyst"]
        wc = [words(x.get("text", "")) for x in analyst_turns]
        wpt = round(sum(wc) / len(wc)) if wc else 0
        failing = [r["check"] + str(r["detail"]) for r in res["results"] if not r["pass"]]
        json.dump({"pregate": res, "words_per_turn": wpt, "analyst_turns": len(analyst_turns),
                   "word_counts": wc},
                  open(os.path.join(PREGATE, f), "w"), indent=1)
        pid = f[:-5]
        print(f"{pid:38} {res['passed']}/{res['of']:>6}  {len(analyst_turns):>5} {wpt:>7}  {'; '.join(failing) if failing else 'clean'}")
        rows.append((pid, res, wpt, wc))
    print("-" * 90)
    print(f"{len(rows)} transcripts pre-gated; per-transcript pregate JSON -> {PREGATE}")


if __name__ == "__main__":
    main()
