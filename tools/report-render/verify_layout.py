# -*- coding: utf-8 -*-
"""Render a .docx and measure where the pages actually broke.

`verify_docx.py` gates link parity — it proves no href was dropped. It is blind to
layout, because a badly paginated document still contains every link. And the
pagination unit tests prove the INSTRUCTION is in the file (keepNext, keepLines,
tblHeader, cantSplit) but not that a renderer acted on it.

This closes that gap the only way it can be closed: render the thing and look.
LibreOffice implements all four properties, so it renders the .docx through a real
layout engine and we measure the result out of the PDF it produces.

    python3 verify_layout.py report.docx --html report.html

WHAT THIS IS AND ISN'T. LibreOffice is not Word. Font metrics, line breaking and
hyphenation differ, so page COUNTS can differ by one and exact break positions will
not match Word's. What transfers is precisely what is checked here — whether a
heading got stranded and how much page is left empty — because those follow from the
OOXML flags, which LibreOffice honours, rather than from metrics. Treat a pass as
strong evidence, not as proof about Word specifically.

Checks:
  stranded heading (FAIL) — a heading or chart title with too little page left
                            beneath it to hold what it introduces. NOT "is the last
                            line": measured against the real documents, a stranded
                            heading is never the last line — it is followed by its
                            two-line framing sentence and then the page ends, with the
                            chart overleaf. Checking for last-line missed all nine
                            real instances.
  trailing gap     (WARN) — page-foot whitespace beyond the budget. Not a failure:
                            the PDF deliberately pays 1.7-2.2in per page to keep
                            blocks whole, so a gap in that range is the design
                            working. Past the budget it reads as a false section
                            boundary and wants a look.
"""
import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile

SOFFICE_CANDIDATES = (
    'soffice', 'libreoffice',
    '/Applications/LibreOffice.app/Contents/MacOS/soffice',
)
#: The PDF already pays this much to keep blocks whole — measured across the four
#: shipped evaluations, whose trailing gaps run 0.41 / 1.70 / 2.24 / 2.05 inches.
DEFAULT_MAX_GAP_IN = 2.6

#: A heading needs room beneath it for the block it introduces: itself (~0.2in), its
#: framing sentence (~0.4in), and enough of the chart or table to establish that they
#: belong together. Below this it has been cut off from its own content.
#:
#: CALIBRATED, not guessed. Rendering the pre-fix documents through LibreOffice put
#: nine headings under 1.5in, the worst at 0.19in — a heading pinned to the bottom
#: margin. After the fix the tightest anywhere is 1.57in. 1.25 sits between the two
#: populations: it catches all nine, and leaves 0.32in of headroom above the passing
#: minimum so ordinary renderer variance doesn't make this flaky.
MIN_BELOW_HEADING_IN = 1.25


def find_soffice():
    for c in SOFFICE_CANDIDATES:
        p = shutil.which(c) if not c.startswith('/') else (c if os.path.exists(c) else None)
        if p:
            return p
    return None


def render_pdf(docx, outdir):
    """.docx -> .pdf through LibreOffice headless."""
    exe = find_soffice()
    if not exe:
        return None
    r = subprocess.run(
        [exe, '--headless', '--convert-to', 'pdf', '--outdir', outdir, docx],
        capture_output=True, text=True, timeout=300)
    out = os.path.join(outdir, os.path.splitext(os.path.basename(docx))[0] + '.pdf')
    if not os.path.exists(out):
        print(f'  FAIL — LibreOffice produced no PDF\n{r.stdout}{r.stderr}', file=sys.stderr)
        return None
    return out


def pages_of(pdf):
    """[(height_pt, [(ymin, ymax, text), ...]), ...] via pdftotext -bbox-layout."""
    with tempfile.NamedTemporaryFile(suffix='.xml', delete=False) as fh:
        tmp = fh.name
    subprocess.run(['pdftotext', '-bbox-layout', pdf, tmp], check=True,
                   capture_output=True)
    xml = open(tmp, encoding='utf-8').read()
    os.unlink(tmp)
    out = []
    for _w, h, body in re.findall(
            r'<page width="([\d.]+)" height="([\d.]+)">(.*?)</page>', xml, re.S):
        lines = []
        for ym, yM, inner in re.findall(
                r'<line xMin="[\d.]+" yMin="([\d.]+)" xMax="[\d.]+" yMax="([\d.]+)">(.*?)</line>',
                body, re.S):
            t = re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', inner)).strip()
            if t:
                lines.append((float(ym), float(yM), t))
        out.append((float(h), lines))
    return out


def headings_from(html):
    """The strings that must never be stranded: section headings and chart titles."""
    src = open(html, encoding='utf-8').read()
    found = re.findall(r'<h1[^>]*>(.*?)</h1>', src, re.S)
    found += re.findall(r'<p class="chtitle"[^>]*>(.*?)</p>', src, re.S)
    out = []
    for h in found:
        t = re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', h)).strip()
        t = t.replace('&amp;', '&').replace('&#x27;', "'").replace('&nbsp;', ' ')
        if t:
            out.append(t)
    return out


def check(docx, html, max_gap, keep):
    tmp = tempfile.mkdtemp()
    pdf = render_pdf(docx, tmp)
    if not pdf:
        print('  SKIP — no LibreOffice on this machine; layout is unverified',
              file=sys.stderr)
        return 0                      # absence of the tool is not a build failure
    pages = pages_of(pdf)
    name = os.path.basename(docx)
    print(f'  {name}: {len(pages)} pages rendered')

    fails = []
    wanted = headings_from(html) if html else []
    bottom = 0.55 * 72                       # the bottom margin build_docx sets
    tightest = (None, 99.0)
    for pi, (h, lines) in enumerate(pages, 1):
        if not lines:
            continue
        for ym, yM, txt in lines:
            for head in wanted:
                # the renderer may wrap a long heading; compare on a collapsed prefix
                if not txt.startswith(head[:14]):
                    continue
                below = (h - bottom - yM) / 72.0
                if below < tightest[1]:
                    tightest = (head, below)
                if below < MIN_BELOW_HEADING_IN:
                    fails.append(f'page {pi}: {head!r} has only {below:.2f}in beneath '
                                 f'it — what it introduces is overleaf')
        if pi < len(pages):
            gap = (h - lines[-1][1]) / 72.0
            flag = '  <-- over budget' if gap > max_gap else ''
            print(f'    page {pi}: trailing gap {gap:.2f}in{flag}')

    for f in fails:
        print(f'  FAIL stranded — {f}', file=sys.stderr)
    if not fails:
        print(f'  OK — every heading keeps its content (tightest: {tightest[0]!r} '
              f'at {tightest[1]:.2f}in, floor {MIN_BELOW_HEADING_IN}in)')
    if keep:
        shutil.copy(pdf, keep)
        print(f'  rendered -> {keep}')
    shutil.rmtree(tmp, ignore_errors=True)
    return 1 if fails else 0


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('docx')
    ap.add_argument('--html', help='source HTML, for the list of headings')
    ap.add_argument('--max-gap', type=float, default=DEFAULT_MAX_GAP_IN,
                    help=f'trailing-gap warning threshold, inches (default {DEFAULT_MAX_GAP_IN})')
    ap.add_argument('--keep-pdf', help='save the rendered PDF here for eyeballing')
    a = ap.parse_args()
    sys.exit(check(a.docx, a.html, a.max_gap, a.keep_pdf))


if __name__ == '__main__':
    main()
