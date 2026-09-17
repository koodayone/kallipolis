"""A local canvas for iterating on the Curriculum Alignment section.

The section depends on files, not on the graph: the roster (`data/<roster>.json`), its
program records (`data/programs/<ref>.json`), their saved readings
(`saved_reports/alignment/<ref>.json`) and the report definition (`saved_reports/<roster>.json`,
for the editorial paragraph). So it can be rendered on its own, without Neo4j — exactly as
`report.py` renders it inside the full report, same CSS, same builders. An evaluation's
roster shares its def slug, so `?roster=<def slug>` shows that evaluation's section.

    cd backend && uvicorn partnerships.alignment_canvas:app --reload --port 8010
    open http://localhost:8010/

The page polls `/hash` and reloads itself when the roster, a record, a reading, the
definition, or any of the rendering modules change, so an edit to `alignment_plate.py`, a
re-run of `python -m partnerships.alignment run …`, or a hand-edit to a saved reading shows
up without touching the browser. `?college=<college_key>` shows one plate;
`?appendix=0` hides the appendix; `?gaps=1` turns on the internal gap annotations.

`?clean=1` drops the toolbar, the reload script and the dev byline and titles the page as
a standalone document — the input for a section-only .docx/.pdf via tools/report-render:

    curl -s 'http://localhost:8010/?clean=1' -o out/alignment.html
    python3 tools/report-render/build_docx.py out/alignment.html out/alignment.docx
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
    ps = _WATCH + [A.SAVED / f"{roster}.json", A.DATA / f"{roster.replace('-', '_')}.json"]
    try:
        for e in A.load_roster(roster)["programs"]:
            ps += [A.PROGRAMS / f"{e['program']}.json", A.STORE / f"{e['program']}.json"]
    except (OSError, KeyError, ValueError):
        pass
    return ps


def _hash(roster: str) -> str:
    h = hashlib.sha1()
    for p in _paths(roster):
        h.update(f"{p}:{p.stat().st_mtime_ns if p.exists() else 0}".encode())
    return h.hexdigest()[:12]


def _rosters() -> list[str]:
    out = []
    for p in sorted(A.DATA.glob("*.json")):
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
        except ValueError:
            continue
        if isinstance(d, dict) and "programs" in d and "id" in d:
            out.append(d["id"])
    return out


def _generated(roster: dict) -> str:
    """The latest reading date across the roster's programs (the byline)."""
    dates = []
    for e in roster["programs"]:
        p = A.STORE / f"{e['program']}.json"
        if p.exists():
            dates.append(json.loads(p.read_text(encoding="utf-8")).get("generated", ""))
    return max(dates, default="")


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
def canvas(roster: str = "svamp-manufacturing-technician", college: str = "", appendix: int = 1, gaps: int = 0,
           clean: int = 0):
    try:
        roster_d, plates = A.view_roster(roster)
    except OSError:
        roster_d, plates = {}, []
    if not plates:
        return HTMLResponse(f"<p>No saved readings for <b>{roster}</b>. Run "
                            f"<code>python -m partnerships.alignment run {roster}</code>.</p>", status_code=404)
    defn = {}
    dp = A.SAVED / f"{roster}.json"
    if dp.exists():
        defn = json.loads(dp.read_text())
    spec = R.ReportSpec(org_name=defn.get("title", roster), org_short="", lede="",
                        curriculum_alignment=roster, curriculum_note=defn.get("curriculum_note", ""),
                        curriculum_show_gaps=bool(gaps))
    # Optionally narrow to one program's plates by re-using the section builder on a filtered view.
    if college:
        keep = [p for p in plates if p.member_id == college or p.college.lower().startswith(college.lower())]
        orig = A.view_roster
        A.view_roster = lambda _r: (roster_d, keep)          # the builder reads through this seam
        try:
            parts, appx, _ = R._curriculum_section(spec)
        finally:
            A.view_roster = orig
    else:
        parts, appx, _ = R._curriculum_section(spec)
    generated = _generated(roster_d)
    body = "\n".join(parts + (appx if appendix else []))
    colleges = [("", "all colleges")] + list(dict.fromkeys((p.member_id, p.college) for p in plates))
    toolbar = _TOOLBAR.format(
        roster_opts="".join(f'<option value="{r}" {"selected" if r == roster else ""}>{r}</option>' for r in _rosters()),
        college_opts="".join(f'<option value="{k}" {"selected" if k == college else ""}>{v}</option>' for k, v in colleges),
        appx_checked="checked" if appendix else "", gaps_checked="checked" if gaps else "", hash=_hash(roster), roster=roster)
    if clean:
        # A standalone document: the section as the report would print it, titled like a
        # report, no dev chrome. What tools/report-render turns into a .docx / .pdf.
        from datetime import date as _date
        gen = _date.fromisoformat(generated).strftime("%B %-d, %Y") if generated else ""
        org = defn.get("org_name") or defn.get("member", "").upper()
        return HTMLResponse(
            '<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">'
            f'<title>{R._esc(defn.get("title", roster))} · Curriculum Alignment</title><style>{R._CSS}</style></head>'
            f'<body><div class="page" id="page">'
            f'<div class="title">{R._esc(org + " : " if org else "")}{R._esc(defn.get("title", roster))} · Curriculum Alignment</div>'
            f'<div class="byline">{R._esc(defn.get("author", "Kallipolis"))} · {R._esc(gen)} · {R._esc(A.ONET_VINTAGE)}</div>'
            f'{body}</div></body></html>')
    return HTMLResponse(
        '<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">'
        f'<title>Curriculum alignment · {roster}</title><style>{R._CSS}</style></head>'
        f'<body>{toolbar}<div class="page" id="page">'
        f'<div class="title">{R._esc(defn.get("title", roster))} · Curriculum Alignment canvas</div>'
        f'<div class="byline">{R._esc(A.ONET_VINTAGE)} · readings to {R._esc(generated)} · '
        f'{len(plates)} plates · edit alignment_plate.py, report.py, a record or a saved reading and this page reloads</div>'
        f'{body}</div></body></html>')
