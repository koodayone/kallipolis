"""Assemble the confirmation-run deliverables into the worktree.

- runs/confirm-2026-07-14/  : full run evidence (21 transcripts + 21 verdicts + pregate + generators)
- fixtures/                 : the 9 golden (cleanly-passing, feeds-verb-free) regression fixtures
- scorecard.json           : machine-readable grades for every transcript
"""
import json
import os
import shutil

SCRATCH = "/private/tmp/claude-501/-Users-dayonekoo-Desktop-code-kallipolis/6eef9907-426f-4cda-9197-08bf8bd2c76b/scratchpad"
WT = "/Users/dayonekoo/Desktop/code/kallipolis/.claude/worktrees/layer3-confirm"
EVAL = os.path.join(WT, "backend/evals/conversational")
RUN = os.path.join(EVAL, "runs/confirm-2026-07-14")
FIX = os.path.join(EVAL, "fixtures")

T = os.path.join(SCRATCH, "transcripts")
V = os.path.join(SCRATCH, "verdicts")
P = os.path.join(SCRATCH, "pregate")

GOLDEN = [
    "attractive-occupations-r1", "concise-under-pressure-r1", "concise-under-pressure-r2",
    "concise-under-pressure-r3", "greenfield-r1", "out-of-scope-funding-r1",
    "onboarding-cold-open-r1", "onboarding-vague-identifier-r1", "onboarding-grain-switch-r1",
]

SYM = {"pass": "P", "partial": "~", "fail": "F"}


def grade_row(pid):
    v = json.load(open(os.path.join(V, pid + ".json")))
    pg = json.load(open(os.path.join(P, pid + ".json")))
    ps = v.get("principles", {})
    return {
        "pathway": pid,
        "principles": {k: (ps.get(k) or {}).get("verdict") for k in ["I", "II", "III", "IV", "V"]},
        "grade_str": " ".join(SYM.get((ps.get(k) or {}).get("verdict"), "?") for k in ["I", "II", "III", "IV", "V"]),
        "establishment": v.get("establishment"),
        "tensions": v.get("tensions"),
        "leans": [k for k, val in (v.get("tensions") or {}).items() if isinstance(val, str) and val.startswith("erred")],
        "worst_failure": v.get("worst_failure"),
        "fix_layer": v.get("fix_layer"),
        "fix_points_at": v.get("fix_points_at"),
        "words_per_turn": pg.get("words_per_turn"),
        "pregate": f"{pg['pregate']['passed']}/{pg['pregate']['of']}",
    }


def main():
    for d in (RUN, os.path.join(RUN, "transcripts"), os.path.join(RUN, "verdicts"),
              os.path.join(RUN, "harness"), FIX):
        os.makedirs(d, exist_ok=True)

    ids = sorted(f[:-5] for f in os.listdir(T) if f.endswith(".json"))
    scorecard = {"run": "confirm-2026-07-14", "model": "claude-opus-4-8[1m]",
                 "priming": "deployed (api.kallipolis.us/mcp tool descriptions; #118/#119/#120 live)",
                 "tierA": "9 passed (test_substrate.py + test_compare.py referential/corroboration)",
                 "transcripts": []}
    for pid in ids:
        shutil.copy(os.path.join(T, pid + ".json"), os.path.join(RUN, "transcripts", pid + ".json"))
        shutil.copy(os.path.join(V, pid + ".json"), os.path.join(RUN, "verdicts", pid + ".json"))
        scorecard["transcripts"].append(grade_row(pid))
    json.dump(scorecard, open(os.path.join(RUN, "scorecard.json"), "w"), indent=1)

    # copy harness (reproducibility)
    for fn in ("gen_driver_prompts.py", "gen_judge_prompts.py", "pregate_and_stats.py",
               "aggregate_scorecard.py", "assemble.py"):
        src = os.path.join(SCRATCH, fn)
        if os.path.exists(src):
            shutil.copy(src, os.path.join(RUN, "harness", fn))

    # golden fixtures
    fix_rows = []
    for pid in GOLDEN:
        shutil.copy(os.path.join(T, pid + ".json"), os.path.join(FIX, pid + ".json"))
        fix_rows.append(grade_row(pid))
    json.dump({"frozen": "2026-07-14", "model": "claude-opus-4-8[1m]",
               "criterion": "all of I-V == pass AND all four tensions balanced (+ establishment pass for onboarding); no contested 'feeds' verb",
               "fixtures": fix_rows},
              open(os.path.join(FIX, "fixtures.json"), "w"), indent=1)

    print("assembled:")
    print("  run evidence ->", RUN, f"({len(ids)} transcripts+verdicts)")
    print("  golden fixtures ->", FIX, f"({len(GOLDEN)})")
    for r in fix_rows:
        print("   ", r["pathway"], r["grade_str"], "estab:", r["establishment"], "w/t:", r["words_per_turn"])


if __name__ == "__main__":
    main()
