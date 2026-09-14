#!/usr/bin/env python3
"""Render ONE report chart straight to PNG — the tight loop for tuning a plate.

The full path to see a chart change is: edit report.py, docker cp into the backend,
restart it, wait for health, run export.sh (fetch HTML, shoot three rasters, build a
docx, print a PDF, verify link parity), then open the PNG. About ninety seconds, and
almost none of it is the chart.

This imports the renderer in-process and shoots the one plate. About five seconds, no
container, no backend, no export. Use it while iterating on geometry; use export.sh
when you need the artifact.

    python3 tools/report-render/preview_chart.py wage 121000
    python3 tools/report-render/preview_chart.py wage 010900 -o /tmp/eh.png
    python3 tools/report-render/preview_chart.py wage all        # every eval TOP

The chart is rendered with the report's own _CSS so the plate matches the artifact —
same fonts, same widths. It is NOT a substitute for exporting: it skips the docx
raster path and the link-parity gate, which is where drift actually hides.
"""
import argparse
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(REPO, "backend"))

#: The TOP codes the shipped program evaluations cover.
EVAL_TOPS = ("121000", "010900", "126100", "010210")


def _wage_svg(top6: str) -> str:
    from ontology.programs import get_wage_outcomes
    from partnerships.lens import LensWage
    from partnerships.report import _wage_outcomes_svg
    rows = [LensWage(w["recipient_type"], w["wage_before"], w["wage_after_2"],
                     w["wage_after_5"], w["n"], w["window"])
            for w in get_wage_outcomes(top6)]
    if not rows:
        sys.exit(f"no wage rows for TOP {top6}")
    return _wage_outcomes_svg(rows, top6)


#: kind -> (renderer, css class). Add a line here when a new plate needs tuning.
KINDS = {"wage": (_wage_svg, "wgchart")}


def shoot(kind: str, key: str, out: str) -> None:
    render, cls = KINDS[kind]
    from partnerships.report import _CSS
    svg = render(key)
    html = (f"<!doctype html><meta charset=utf-8><style>{_CSS}"
            # white plate, no page chrome: we want the chart, not a page of report
            f"body{{background:#fff;margin:0}}.page{{margin:0;box-shadow:none;"
            f"min-height:0;padding:16px}}</style>"
            f'<div class="page"><div class="{cls}">{svg}</div></div>')
    with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False) as fh:
        fh.write(html)
        tmp = fh.name
    node = os.path.join(HERE, "shoot_xwalk_png.cjs")
    r = subprocess.run(["node", node, f"file://{tmp}", out, f".{cls}"],
                       capture_output=True, text=True)
    os.unlink(tmp)
    if r.returncode != 0:
        sys.exit(f"shoot failed: {r.stderr.strip()[:400]}")
    size = os.path.getsize(out)
    print(f"  {kind} {key:<8} -> {out}  ({size:,}b)")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("kind", choices=sorted(KINDS))
    ap.add_argument("key", help="TOP6 code, or 'all' for every evaluation TOP")
    ap.add_argument("-o", "--out", help="output PNG (default /tmp/<kind>-<key>.png)")
    a = ap.parse_args()
    keys = EVAL_TOPS if a.key == "all" else (a.key,)
    for k in keys:
        shoot(a.kind, k, a.out or f"/tmp/{a.kind}-{k}.png")


if __name__ == "__main__":
    main()
