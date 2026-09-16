"""A local canvas for iterating on the Curriculum Alignment section.

The section depends on two files, not on the graph: the saved alignment
(`saved_reports/<roster>.alignment.json`) and the report definition
(`saved_reports/<roster>.json`, for the editorial paragraph). So it can be rendered on
its own, from the branch, without Neo4j — exactly as `report.py` will render it inside
the full report, same CSS, same builders.

    cd backend && uvicorn partnerships.alignment_canvas:app --reload --port 8010
    open http://localhost:8010/

The page polls `/hash` and reloads itself when the alignment file, the definition, or
any of the rendering modules change, so an edit to `alignment_plate.py`, a re-run of
`python -m partnerships.alignment …`, or a hand-edit to the saved alignment shows up
without touching the browser. `?college=<college_key>` shows one plate;
`?appendix=0` hides the evidence table.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse

from partnerships import alignment as A
from partnerships import alignment_plate as P
from partnerships import report as R

app = FastAPI(title="Curriculum alignment canvas")
_HERE = Path(__file__).parent
_WATCH = [_HERE / "alignment.py", _HERE / "alignment_plate.py", _HERE / "report.py"]


def _paths(roster: str) -> list[Path]:
    return _WATCH + [A.SAVED / f"{roster}.alignment.json", A.SAVED / f"{roster}.json",
                     A.DATA / f"{roster.replace('-', '_')}.json"]


def _hash(roster: str) -> str:
    h = hashlib.sha1()
    for p in _paths(roster):
        h.update(f"{p}:{p.stat().st_mtime_ns if p.exists() else 0}".encode())
    return h.hexdigest()[:12]


def _rosters() -> list[str]:
    return sorted(p.name[: -len(".alignment.json")] for p in A.SAVED.glob("*.alignment.json"))


_TOOLBAR = """
<div style="position:fixed;top:10px;right:10px;z-index:9;background:#11131c;color:#cdd5e4;font:12px/1.4 -apple-system,system-ui,sans-serif;padding:8px 12px;border-radius:8px;display:flex;gap:10px;align-items:center;box-shadow:0 2px 12px rgba(0,0,0,.35)">
  <span style="opacity:.7">canvas</span>
  <select id="c-roster" onchange="go()" style="font:inherit;background:#1c2030;color:#e6ecf7;border:1px solid #2a2f3e;border-radius:5px;padding:3px 6px">{roster_opts}</select>
  <select id="c-college" onchange="go()" style="font:inherit;background:#1c2030;color:#e6ecf7;border:1px solid #2a2f3e;border-radius:5px;padding:3px 6px">{college_opts}</select>
  <label style="display:flex;gap:4px;align-items:center"><input id="c-appx" type="checkbox" {appx_checked} onchange="go()"> appendix</label>
  <label style="display:flex;gap:4px;align-items:center" title="internal review only — off in the report"><input id="c-gaps" type="checkbox" {gaps_checked} onchange="go()"> gaps</label>
  <span id="c-status" style="opacity:.55">live</span>
</div>
<script>
const HASH = "{hash}";
function go(){{ const r=document.getElementById('c-roster').value, c=document.getElementById('c-college').value, a=document.getElementById('c-appx').checked?1:0, g=document.getElementById('c-gaps').checked?1:0;
  location.href = `/?roster=${{r}}&college=${{c}}&appendix=${{a}}&gaps=${{g}}`; }}
async function poll(){{ try {{ const r = await fetch('/hash?roster={roster}'); const j = await r.json();
  if (j.hash !== HASH) location.reload(); document.getElementById('c-status').textContent='live'; }}
  catch(e) {{ document.getElementById('c-status').textContent='server restarting…'; }} setTimeout(poll, 1500); }}
poll();
</script>"""


@app.get("/hash")
def hash_(roster: str = "svamp-manufacturing-technician"):
    return JSONResponse({"hash": _hash(roster)})


@app.get("/", response_class=HTMLResponse)
def canvas(roster: str = "svamp-manufacturing-technician", college: str = "", appendix: int = 1, gaps: int = 0):
    al = A.load_alignment(roster)
    if al is None:
        return HTMLResponse(f"<p>No saved alignment for <b>{roster}</b>. Run "
                            f"<code>python -m partnerships.alignment {roster}</code>.</p>", status_code=404)
    defn = {}
    dp = A.SAVED / f"{roster}.json"
    if dp.exists():
        defn = json.loads(dp.read_text())
    spec = R.ReportSpec(org_name=defn.get("title", roster), org_short="", lede="",
                        curriculum_alignment=roster, curriculum_note=defn.get("curriculum_note", ""),
                        curriculum_show_gaps=bool(gaps))
    # Optionally narrow to one plate by re-using the section builder on a filtered copy.
    if college:
        keep = [p for p in al.plates if p.member_id == college or p.college.lower().startswith(college.lower())]
        al_view = A.Alignment(al.roster_id, al.generated, al.onet_vintage, keep)
        orig = A.load_alignment
        A.load_alignment = lambda _r: al_view          # the builder reads through this seam
        try:
            parts, appx = R._curriculum_section(spec)
        finally:
            A.load_alignment = orig
    else:
        parts, appx = R._curriculum_section(spec)
    body = "\n".join(parts + (appx if appendix else []))
    colleges = [("", "all colleges")] + [(p.member_id, p.college) for p in al.plates]
    toolbar = _TOOLBAR.format(
        roster_opts="".join(f'<option value="{r}" {"selected" if r == roster else ""}>{r}</option>' for r in _rosters()),
        college_opts="".join(f'<option value="{k}" {"selected" if k == college else ""}>{v}</option>' for k, v in colleges),
        appx_checked="checked" if appendix else "", gaps_checked="checked" if gaps else "", hash=_hash(roster), roster=roster)
    return HTMLResponse(
        '<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">'
        f'<title>Curriculum alignment · {roster}</title><style>{R._CSS}</style></head>'
        f'<body>{toolbar}<div class="page" id="page">'
        f'<div class="title">{R._esc(defn.get("title", roster))} · Curriculum Alignment canvas</div>'
        f'<div class="byline">{R._esc(al.onet_vintage)} · alignment generated {R._esc(al.generated)} · '
        f'{len(al.plates)} plates · edit alignment_plate.py, report.py or the saved alignment and this page reloads</div>'
        f'{body}</div></body></html>')
