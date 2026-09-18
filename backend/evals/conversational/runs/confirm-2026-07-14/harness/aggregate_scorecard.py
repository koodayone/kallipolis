"""Aggregate judge verdicts + pre-gate + concision into the confirmation scorecard.

Reads scratchpad/verdicts/*.json (judge output) and scratchpad/pregate/*.json, prints:
  - a per-transcript table (I-V, tension leans, establishment, w/turn, pregate, fix_layer)
  - summary counts vs the baseline target (0 principle partials / 0 tension leans on the 9 affected;
    5/5 establishment; borderline pass-rates over their 3 runs).
A transcript "cleanly passes" iff all of I-V == pass AND all four tensions == balanced.
"""
import json
import os

SCRATCH = "/private/tmp/claude-501/-Users-dayonekoo-Desktop-code-kallipolis/6eef9907-426f-4cda-9197-08bf8bd2c76b/scratchpad"
VERD = os.path.join(SCRATCH, "verdicts")
PRE = os.path.join(SCRATCH, "pregate")

AFFECTED = ["attractive-occupations", "strategic-programs", "out-of-scope-funding", "greenfield",
            "overclaim-failing", "plain-language", "teach-the-ontology", "portfolio-routing",
            "concise-under-pressure"]
BORDERLINE = ["attractive-occupations", "plain-language", "concise-under-pressure"]
ONBOARDING = ["onboarding-cold-open", "onboarding-premature-analysis", "onboarding-vague-identifier",
              "onboarding-grain-switch", "onboarding-out-of-scope"]

SYM = {"pass": "P", "partial": "~", "fail": "F"}


def base_id(pid):
    for tag in ("-r1", "-r2", "-r3"):
        if pid.endswith(tag):
            return pid[:-3]
    return pid


def load():
    rows = {}
    for f in sorted(os.listdir(VERD)):
        if not f.endswith(".json"):
            continue
        pid = f[:-5]
        try:
            v = json.load(open(os.path.join(VERD, f)))
        except Exception as e:
            rows[pid] = {"error": str(e)}
            continue
        pg = {}
        if os.path.exists(os.path.join(PRE, f)):
            pg = json.load(open(os.path.join(PRE, f)))
        rows[pid] = {"v": v, "pg": pg}
    return rows


def tension_leans(v):
    return [k for k, val in (v.get("tensions") or {}).items() if isinstance(val, str) and val.startswith("erred")]


def clean_pass(v):
    ps = v.get("principles") or {}
    allp = all((ps.get(k) or {}).get("verdict") == "pass" for k in ["I", "II", "III", "IV", "V"])
    return allp and not tension_leans(v)


def main():
    rows = load()
    print(f"{'transcript':34} {'I II III IV V':13} {'estab':6} {'w/t':>4} {'pg':>4}  leans / fix_layer")
    print("-" * 104)
    for pid in sorted(rows):
        r = rows[pid]
        if "error" in r:
            print(f"{pid:34} ERROR {r['error']}")
            continue
        v, pg = r["v"], r["pg"]
        ps = v.get("principles") or {}
        grades = " ".join(SYM.get((ps.get(k) or {}).get("verdict"), "?") for k in ["I", "II", "III", "IV", "V"])
        estab = v.get("establishment", "")
        estab = {"pass": "PASS", "fail": "FAIL"}.get(estab, "-" if base_id(pid) not in ONBOARDING else "?")
        wt = pg.get("words_per_turn", "?")
        pgp = f"{pg.get('pregate', {}).get('passed', '?')}/{pg.get('pregate', {}).get('of', '?')}"
        leans = ",".join(tension_leans(v)) or "-"
        fl = v.get("fix_layer", "")
        print(f"{pid:34} {grades:13} {estab:6} {str(wt):>4} {pgp:>4}  {leans} / {fl}")
    print("-" * 104)

    # summary over the affected set (all runs)
    aff_rows = {pid: r for pid, r in rows.items() if "v" in r and base_id(pid) in AFFECTED}
    partials = 0
    fails = 0
    leans_total = 0
    for pid, r in aff_rows.items():
        ps = r["v"].get("principles") or {}
        for k in ["I", "II", "III", "IV", "V"]:
            vv = (ps.get(k) or {}).get("verdict")
            if vv == "partial":
                partials += 1
            elif vv == "fail":
                fails += 1
        leans_total += len(tension_leans(r["v"]))
    print(f"AFFECTED SET ({len(aff_rows)} transcripts over the 9 pathways):")
    print(f"  principle partials: {partials}   fails: {fails}   tension leans: {leans_total}")
    print(f"  BASELINE TARGET: 0 partials / 0 fails / 0 leans")

    # borderline pass-rate
    print("BORDERLINE pass-rate (clean pass = all I-V pass AND all tensions balanced):")
    for b in BORDERLINE:
        runs = [r for pid, r in rows.items() if "v" in r and base_id(pid) == b]
        n = len(runs)
        passes = sum(1 for r in runs if clean_pass(r["v"]))
        print(f"  {b:26} {passes}/{n}")

    # onboarding establishment
    onb = {pid: r for pid, r in rows.items() if "v" in r and base_id(pid) in ONBOARDING}
    estab_pass = sum(1 for r in onb.values() if r["v"].get("establishment") == "pass")
    print(f"ONBOARDING establishment: {estab_pass}/{len(onb)} pass   (TARGET 5/5)")

    # feeder scan is done separately in bash over transcripts
    print(f"\nTotal verdicts loaded: {sum(1 for r in rows.values() if 'v' in r)}")


if __name__ == "__main__":
    main()
