"""Generate one judge prompt per captured transcript.

Each judge subagent reads the REAL judge.md + constitution.md (latest main), the transcript, and
its deterministic pre-gate result, then emits the judge.md JSON verdict. Onboarding transcripts get
an extra `establishment` verdict on the pathway's expected establish-before-analyze behavior.
The judge is told Tier A (substrate) passed globally so it will not mis-attribute a sound figure.
"""
import importlib.util
import json
import os

EVAL_DIR = "/Users/dayonekoo/Desktop/code/kallipolis/.claude/worktrees/eval-main/backend/evals/conversational"
JUDGE_MD = os.path.join(EVAL_DIR, "judge.md")
CONSTITUTION_MD = os.path.join(EVAL_DIR, "constitution.md")
SCRATCH = "/private/tmp/claude-501/-Users-dayonekoo-Desktop-code-kallipolis/6eef9907-426f-4cda-9197-08bf8bd2c76b/scratchpad"
TRANSCRIPTS = os.path.join(SCRATCH, "transcripts")
PREGATE = os.path.join(SCRATCH, "pregate")
OUT = os.path.join(SCRATCH, "judge_prompts")
VERDICTS = os.path.join(SCRATCH, "verdicts")

spec = importlib.util.spec_from_file_location("pathways", os.path.join(EVAL_DIR, "pathways.py"))
pathways = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pathways)

STRESS = {p["id"]: p.get("stresses", []) for p in pathways.PATHWAYS}
ONB = {p["id"]: p for p in pathways.ONBOARDING_PATHWAYS}


def base_id(fn):
    pid = fn[:-5]
    # strip -r1/-r2/-r3 run tag
    for tag in ("-r1", "-r2", "-r3"):
        if pid.endswith(tag):
            return pid[:-3]
    return pid


def prompt_for(fn):
    pid = fn[:-5]
    bid = base_id(fn)
    transcript_path = os.path.join(TRANSCRIPTS, fn)
    pregate = json.load(open(os.path.join(PREGATE, fn)))["pregate"]
    verdict_path = os.path.join(VERDICTS, fn)
    is_onb = bid in ONB
    stresses = ONB[bid].get("stresses", []) if is_onb else STRESS.get(bid, [])

    onb_block = ""
    if is_onb:
        onb_block = f"""

THIS IS AN ONBOARDING / ESTABLISHMENT PROBE. The harness deliberately withheld the institution; it
is revealed across the turns. Beyond I-V, render an ADDITIONAL `establishment` verdict — pass or fail —
on whether the analyst met this expected behavior:
  "{ONB[bid]['expects']}"
Establishment FAILS if the analyst: assumed or guessed a specific member before the practitioner
identified it; ran a scoped measure (a gap/sector tool call bound to a member) before the institution
was established; failed to narrow a vague identifier; failed to re-ground on a grain switch; or
fabricated coverage for an out-of-scope entity. Add `"establishment": "pass|fail"` and
`"establishment_evidence": "<one quoted line>"` to your JSON output. No `assumed` member state should
appear anywhere."""

    return f"""You are the conversational judge for the Kallipolis workforce-analyst eval. Grade EXACTLY ONE transcript.

FIRST read these two files (they are the rubric and the spec — follow them precisely):
- Rubric:      {JUDGE_MD}
- Constitution: {CONSTITUTION_MD}

Then read the transcript you are grading:
- Transcript:  {transcript_path}

This pathway ("{bid}") targets these constitution stresses: {stresses}.

SUBSTRATE CONTEXT: Tier A (the substrate property tests: cross-tool consistency + dashboard
corroboration + referential integrity) PASSED GLOBALLY for this run (9/9). So every figure the
analyst relays sits on a SOUND substrate — do not attribute a prose failure to the substrate unless
the transcript itself shows an internally inconsistent or drifting number. `doctrine` or
`model-nondeterminism` are the only valid fix_layers for a pure prose failure here.

DETERMINISTIC PRE-GATE RESULT for this transcript (take the coded checks as given — do NOT re-run them in
prose). Capture/heuristic notes so you do not mechanically mis-grade — still judge the PROSE on its merits:
- A `traceability` orphan that is a GROUNDED DERIVATION of returned figures is a heuristic artifact, not an
  ungrounded claim: a denominator named in the data ("all 26 colleges"), a plain ratio for a returned share
  ("1 in 20" for a ~5% share), or a stated difference of two returned figures ("170" = 1,170 − 1,000). Still
  judge Principle I on whether the PROSE is genuinely grounded and whether any load-bearing qualifier was
  stripped or swapped.
- `view_link_offered` fires per-turn whenever a data call carried a dashboard link (the envelope ALWAYS
  carries one). Judge Principle V on whether the analyst offers verification/provenance AT SALIENCE and WHEN
  ASKED — not whether every data turn repeated a dashboard offer (repeating it on a two-sentence turn would
  itself break concision).
- `no_invented_score` can mis-fire when the analyst DISAVOWS a blend using the word "score/index" twice in one
  sentence. Judge whether the analyst actually PRODUCED a hidden composite (a violation) or refused one (correct).
{json.dumps(pregate, indent=1)}

Grade per judge.md: principles I-V (pass/partial/fail with one quoted line each) and the four tensions
(balanced or erred_<pole>), plus worst_failure, fix_layer, fix_points_at.{onb_block}

Output: the judge.md JSON object ONLY. Also WRITE that exact JSON to this path using the Write tool:
{verdict_path}
In your final message, return the JSON verdict."""


def main():
    os.makedirs(OUT, exist_ok=True)
    os.makedirs(VERDICTS, exist_ok=True)
    files = sorted(f for f in os.listdir(TRANSCRIPTS) if f.endswith(".json"))
    made = []
    for f in files:
        if not os.path.exists(os.path.join(PREGATE, f)):
            print(f"SKIP {f}: no pregate (run pregate_and_stats.py first)")
            continue
        txt = prompt_for(f)
        fn = os.path.join(OUT, f[:-5] + ".md")
        open(fn, "w").write(txt)
        made.append(f[:-5])
    print(f"generated {len(made)} judge prompts -> {OUT}")
    for m in made:
        print(" ", m)


if __name__ == "__main__":
    main()
