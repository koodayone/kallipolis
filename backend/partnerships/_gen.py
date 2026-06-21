import json, os, sys, traceback
from partnerships.landscape import MEMBERS
from partnerships import members as members_mod
from partnerships.dossier import opportunity_dossier

os.makedirs("/tmp/dossiers", exist_ok=True)
log = open("/tmp/dossiers/_progress.log", "w")
out = []
for name in MEMBERS["baccc"].colleges:
    mid = members_mod.college_member(name).id
    try:
        d = opportunity_dossier(mid)
        json.dump(d, open(f"/tmp/dossiers/{mid}.json", "w"))
        tops = sorted((c for ind in d["industries"] for c in ind["clusters"]),
                      key=lambda c: -c["priority_score"])
        out.append({"college": name, "mid": mid,
                    "top": [tops[0]["label"][:22], tops[0]["priority_score"], tops[0]["college_role"]] if tops else None})
        log.write(f"ok {mid} {len(d['industries'])} industries\n"); log.flush()
    except Exception:
        traceback.print_exc(file=log); log.flush()
        out.append({"college": name, "mid": mid, "top": None, "error": True})
json.dump(out, open("/tmp/dossiers/_summary.json", "w"))
log.write(f"DONE {len([o for o in out if o.get('top')])} of {len(out)}\n"); log.flush()
print("DONE")
