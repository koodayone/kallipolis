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
  whitespace hole  (WARN) — page-foot whitespace beyond the budget AND not at a
                            section boundary. Keeping a block whole necessarily
                            costs white, so size alone says nothing: measured across
                            the four evaluations, every gap over 2.5in sits exactly
                            where the next page opens a new section, which reads as
                            deliberate. The same gap mid-section reads as a defect.
"""
import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
from html import unescape

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
#: CALIBRATED, not guessed, and re-derived after the prefix-matching false positives
#: above were removed. Across 36 headings in the four evaluations: BEFORE the fix,
#: seven sat under 1.5in with the worst at 0.44in; AFTER, none do and the tightest
#: anywhere is 1.57in. The two populations are cleanly separated — 1.14in is the
#: highest failing case — so 1.25 catches every one of the seven while leaving 0.32in
#: of headroom above the passing minimum, which is what keeps this from being flaky
#: under ordinary renderer variance.
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


def content_extent(pdf, dpi=50):
    """Per page, inches of empty space between the last INK and the bottom margin.

    Measured from pixels, not from the text layer. pdftotext cannot see images, so a
    page ending in a 3.52in chart reported a 3.52in "gap" while actually being full —
    wrong by up to 3.4in on exactly the pages this report cares about, and wrong in
    the direction that invents a whitespace problem where none exists.
    """
    tmp = tempfile.mkdtemp()
    root = os.path.join(tmp, 'pg')
    subprocess.run(['pdftoppm', '-gray', '-r', str(dpi), pdf, root],
                   check=True, capture_output=True)
    gaps = []
    for f in sorted(os.listdir(tmp)):
        raw = open(os.path.join(tmp, f), 'rb').read()
        toks, i = [], 0
        while len(toks) < 4:                       # P5, width, height, maxval
            j = i
            while raw[j:j + 1] not in b' \t\n\r':
                j += 1
            toks.append(raw[i:j])
            i = j + 1
            while raw[i:i + 1] in b' \t\n\r':
                i += 1
        w, h = int(toks[1]), int(toks[2])
        px = raw[len(raw) - w * h:]
        last = 0
        for y in range(h):
            if min(px[y * w:(y + 1) * w], default=255) < 245:   # 245: ignore JPEG-ish noise
                last = y
        gaps.append(max((h - last) / dpi - 0.55, 0.0))          # less the bottom margin
    shutil.rmtree(tmp, ignore_errors=True)
    return gaps


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
    gaps = content_extent(pdf)
    name = os.path.basename(docx)
    print(f'  {name}: {len(pages)} pages rendered')

    fails, holes = [], []
    wanted = headings_from(html) if html else []
    bottom = 0.55 * 72                       # the bottom margin build_docx sets
    tightest = (None, 99.0)
    seen = set()
    for pi, (h, lines) in enumerate(pages, 1):
        if not lines:
            continue
        for ym, yM, txt in lines:
            line = unescape(txt).strip()
            for head in wanted:
                # EXACT line, not a prefix. The Sources list cites sections by name
                # ("College Program Alignment & Supply Section: ..."), and a prefix
                # match flagged those citations as stranded headings — a false
                # positive at the foot of the last page, where every source entry
                # legitimately sits. The real heading was at the top of page 4 with
                # 9.70in beneath it.
                if line != head:
                    continue
                seen.add(head)
                below = (h - bottom - yM) / 72.0
                if below < tightest[1]:
                    tightest = (head, below)
                if below < MIN_BELOW_HEADING_IN:
                    fails.append(f'page {pi}: {head!r} has only {below:.2f}in beneath '
                                 f'it — what it introduces is overleaf')
    # A gap is only a defect if it is a HOLE. Measured across the four evaluations,
    # every gap over 2.5in sits where the next page opens a new section — the cost of
    # keeping an atomic figure whole, and it reads as deliberate sectioning. The same
    # gap in the MIDDLE of a section reads as something gone wrong. So the check is
    # not "how big" but "big, and not at a boundary".
    for pi, gap in enumerate(gaps[:-1], 1):  # the last page's gap is not a gap
        opens_section = bool(pages[pi][1]) and unescape(pages[pi][1][0][2]).strip() in wanted
        flag = ''
        if gap > max_gap:
            flag = ('  (section break)' if opens_section
                    else '  <-- HOLE: over budget and mid-section')
        print(f'    page {pi}: trailing gap {gap:.2f}in{flag}')
        if gap > max_gap and not opens_section:
            holes.append(f'page {pi}: {gap:.2f}in of white mid-section')

    # A heading the renderer wrapped would no longer match exactly, and would drop out
    # of the check in silence. Say so rather than report a clean run over less work.
    for miss in [w for w in wanted if w not in seen]:
        print(f'  WARN — heading {miss!r} never matched a rendered line; it may have '
              f'wrapped, and is NOT being checked', file=sys.stderr)

    for f in fails:
        print(f'  FAIL stranded — {f}', file=sys.stderr)
    for f in holes:
        print(f'  WARN whitespace — {f}', file=sys.stderr)
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
