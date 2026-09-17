# -*- coding: utf-8 -*-
"""Unit tests for the .docx pagination contract — tools/report-render/build_docx.py.

The report states its pagination ONCE, in CSS, in `report.py`'s `@media print`.
Chromium speaks CSS so the PDF honoured all of it; this builder walks the DOM and
never reads the stylesheet, so every rule was dropped. The shipped .docx files carried
`keepNext=0  tblHeader=0  cantSplit=0` and Word paginated by greedy overflow — every
good break in them was luck.

These tests are written against what a READER experiences, not against attribute
counts, because the attributes are only the mechanism:

  - a heading must never be stranded from the thing it names
  - a number must never appear under no column header
  - a sentence must never break through its own middle inside a block
  - a row must never split across pages through its own middle

Two of them are NEGATIVE, and those are the ones that encode the judgement rather than
the mechanics. Whitespace is not free: past about two inches a gap reads as a section
boundary that isn't there, so "bind everything" is a worse document, not a safer one.
The negative tests exist to stop a later reader of this file from "finishing the job".

Coverage:
  - a block's non-final elements bind forward; the final one deliberately does not
  - blocks never chain into each other (which would make the document one atom)
  - every table header row repeats on overflow
  - a long table's interior stays splittable — the repeated header is what makes that safe
  - a short table moves whole, every row but the last binding forward
  - paragraphs inside a block resist breaking through their own middle
  - an oversized block is left unbound and says so, rather than being silently dropped
  - every `.blk` in the source produces a bound group in the output
"""
import base64
import os
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
import zipfile

import pytest

# build_docx.py runs in a subprocess under THIS interpreter, so its deps must be
# importable here. They are export-tooling deps, deliberately absent from the backend
# runtime — see tools/report-render/requirements.txt.
pytest.importorskip('docx', reason='pip install -r tools/report-render/requirements.txt')
pytest.importorskip('bs4', reason='pip install -r tools/report-render/requirements.txt')

HERE = os.path.dirname(os.path.abspath(__file__))
BUILD = os.path.join(os.path.dirname(HERE), 'build_docx.py')
W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'

#: A 1x1 PNG. build_docx embeds charts as rasters, and a block containing one is the
#: expensive case the whole trade-off turns on, so the fixtures need a real image.
PNG_1X1 = base64.b64decode(
    b'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==')


def _page(*blocks):
    return f'<div id="page">{"".join(blocks)}</div>'


def blk(*parts):
    return f'<div class="blk">{"".join(parts)}</div>'


#: heading + framing sentence + the chart it names — the canonical unit.
CHART_BLOCK = blk(
    '<p class="chtitle">Annual Awards vs. Annual Openings</p>',
    '<p class="tnar">Credentials awarded per year across colleges offering this '
    'program, set against regional annual openings for target occupations.</p>',
    '<div class="awchart"><svg></svg></div>')

#: a long table — more rows than the builder will keep whole — which must stay splittable.
LONG_TABLE_BLOCK = blk(
    '<p class="tnar">Award trends for each member-college program.</p>',
    '<table class="trend"><tr><th>College</th><th>2021</th><th>2022</th></tr>'
    + ''.join(f'<tr><td>College {i}</td><td>{i}</td><td>{i + 1}</td></tr>' for i in range(12))
    + '</table>')

#: a narration and the table it introduces.
TABLE_BLOCK = blk(
    '<p class="tnar">Award trends for each member-college program.</p>',
    '<table class="trend"><tr><th>College</th><th>2021</th><th>2022</th></tr>'
    '<tr><td>Foothill College</td><td>12</td><td>14</td></tr>'
    '<tr><td>De Anza College</td><td>9</td><td>11</td></tr></table>')


def build(tmp_path, html, png_height_px=None):
    """Run the real entry point; return (document.xml, combined output).

    Output is merged because the oversized-block notice goes to stderr — export.sh
    sends this script's stdout to /dev/null."""
    src = tmp_path / 'src.html'
    src.write_text(html, encoding='utf-8')
    png = tmp_path / 'chart.png'
    png.write_bytes(_tall_png(png_height_px) if png_height_px else PNG_1X1)
    out = tmp_path / 'out.docx'
    r = subprocess.run(
        [sys.executable, BUILD, str(src), str(out), str(png), str(png), str(png), str(png)],
        capture_output=True, text=True)
    assert r.returncode == 0, f'build_docx failed:\n{r.stderr}'
    xml = zipfile.ZipFile(out).read('word/document.xml').decode()
    return xml, r.stdout + r.stderr


def _tall_png(px):
    """A 1-pixel-wide PNG `px` tall. build_docx scales images to the content width, so
    an extreme aspect ratio is how a fixture forces a block past a page."""
    import struct
    import zlib

    def chunk(tag, data):
        c = tag + data
        return struct.pack('>I', len(data)) + c + struct.pack('>I', zlib.crc32(c))

    raw = b''.join(b'\x00\x00' for _ in range(px))  # filter byte + 1 grey pixel per row
    return (b'\x89PNG\r\n\x1a\n'
            + chunk(b'IHDR', struct.pack('>IIBBBBB', 1, px, 8, 0, 0, 0, 0))
            + chunk(b'IDAT', zlib.compress(raw))
            + chunk(b'IEND', b''))


# ── reading the output ───────────────────────────────────────────────────────
# Parsed, not regexed. python-docx writes empty paragraphs self-closed (`<w:p/>`) and
# nests paragraphs inside table cells, so a source-text scan either misses elements or
# runs past their end into the next one.

def body_items(xml):
    """Block-level children of the body, in document order."""
    body = ET.fromstring(xml).find(f'{W}body')
    return [el for el in body if el.tag in (f'{W}p', f'{W}tbl')]


def is_table(el):
    return el.tag == f'{W}tbl'


def rows_of(tbl):
    return tbl.findall(f'{W}tr')


def binds_forward(el):
    """Does this element keep itself on the same page as the one after it?"""
    if el.tag == f'{W}p':
        return el.find(f'{W}pPr/{W}keepNext') is not None
    last = rows_of(el)[-1:]                       # a table binds forward via its last row
    return bool(last) and last[0].find(f'.//{W}keepNext') is not None


def has(el, tag):
    return el.find(f'.//{W}{tag}') is not None


def text_of(el):
    return ''.join(t.text or '' for t in el.iter(f'{W}t'))


# ── the promises ─────────────────────────────────────────────────────────────

def test_a_heading_is_never_stranded_from_what_it_names(tmp_path):
    """THE defect this file exists for. "Wage Outcomes" sat at the foot of a page with
    its chart overleaf, because the `.blk` boundary was walked straight through and
    the grouping lost."""
    xml, _ = build(tmp_path, _page(CHART_BLOCK))
    items = body_items(xml)
    assert len(items) >= 2, 'the fixture block did not emit'
    for i, it in enumerate(items[:-1]):
        assert binds_forward(it), f'element {i} of the block does not bind to the next'


def test_the_last_element_of_a_block_is_deliberately_left_unbound(tmp_path):
    """Subtle and load-bearing. If the final element bound forward too, every block
    would chain into the next and the whole document would become ONE atom — which
    Word, being taller than a page, would then ignore in its entirety. The fix would
    silently undo itself."""
    xml, _ = build(tmp_path, _page(CHART_BLOCK))
    assert not binds_forward(body_items(xml)[-1]), \
        'the block chains into whatever follows it'


def test_two_blocks_do_not_fuse_into_one(tmp_path):
    """The same property observed end-to-end: a document of two blocks must contain a
    legal break BETWEEN them."""
    xml, _ = build(tmp_path, _page(CHART_BLOCK, TABLE_BLOCK))
    items = body_items(xml)
    assert not all(binds_forward(i) for i in items), \
        'no legal page break anywhere in the document'


def test_a_number_never_appears_under_no_column_header(tmp_path):
    """A table that spills onto the next page shows its continuation with no header
    row unless w:tblHeader says otherwise. In the enrolment table that is bare counts
    under no term at all — numbers a reader cannot interpret."""
    xml, _ = build(tmp_path, _page(TABLE_BLOCK))
    tbl = next(t for t in body_items(xml) if is_table(t))
    assert has(rows_of(tbl)[0], 'tblHeader'), 'the header row does not repeat on overflow'


def test_a_row_never_splits_through_its_own_middle(tmp_path):
    xml, _ = build(tmp_path, _page(TABLE_BLOCK))
    tbl = next(t for t in body_items(xml) if is_table(t))
    rows = rows_of(tbl)
    assert rows, 'no rows'
    for i, r in enumerate(rows):
        assert has(r, 'cantSplit'), f'row {i} may break through its middle'


def test_a_sentence_does_not_break_through_its_own_middle_inside_a_block(tmp_path):
    """keepNext binds the LAST line of a paragraph to the FIRST of the next, so it
    alone would still let a three-line narration split 1/2 — heading and chart
    correctly together, and the sentence introducing them cut in half. `break-inside:
    avoid` means both properties; expressing one leaves the gap half-closed."""
    xml, _ = build(tmp_path, _page(CHART_BLOCK))
    texty = [p for p in body_items(xml) if not is_table(p) and text_of(p).strip()]
    assert texty, 'no text paragraphs in the block'
    for p in texty:
        assert has(p, 'keepLines'), \
            f'{text_of(p)[:40]!r} may split mid-sentence'


# ── the judgement, guarded ───────────────────────────────────────────────────

def test_a_long_table_interior_stays_splittable(tmp_path):
    """NEGATIVE, and the more important half of the design.

    Making a LONG table atomic is the obvious-looking "improvement" and it is wrong: a
    header row that reprints already makes a split table readable anywhere, so binding
    the interior buys nothing and costs most of a page of white every time the table
    doesn't fit. Whitespace is not free — past ~2in a gap reads as a section boundary
    that isn't there. (Word would ignore a chain that tall anyway.)"""
    xml, _ = build(tmp_path, _page(LONG_TABLE_BLOCK))
    tbl = next(t for t in body_items(xml) if is_table(t))
    rows = rows_of(tbl)
    assert len(rows) > 10, 'fixture needs more rows than keep_whole binds'
    for i, r in enumerate(rows[:-1]):
        assert not has(r, 'keepNext'), \
            f'row {i} binds forward — a long table was made atomic'


def test_a_short_table_moves_whole(tmp_path):
    """The page's `table.dem, table.live, table.trend {break-inside: avoid}`: a table of a
    few rows moves to the next page whole rather than leaving one row behind under its
    header. Every row but the last binds forward; the last is left free so the table can
    still begin a fresh page itself."""
    xml, _ = build(tmp_path, _page(TABLE_BLOCK))
    tbl = next(t for t in body_items(xml) if is_table(t))
    rows = rows_of(tbl)
    assert len(rows) >= 3, 'fixture needs an interior row'
    for i, r in enumerate(rows[:-1]):
        assert has(r, 'keepNext'), f'row {i} of a short table does not bind forward'
    assert not has(rows[-1], 'keepNext'), 'the last row must stay free'


def test_an_oversized_block_is_left_unbound_and_says_so(tmp_path):
    """Word silently ignores a keepNext chain taller than the page: no binding, no
    warning, and a layout that looks exactly like the bug. So an oversized block must
    be declined deliberately AND audibly — a silent cap here would read as "covered"
    when it isn't."""
    xml, out = build(tmp_path, _page(CHART_BLOCK), png_height_px=4000)
    assert 'exceeds' in out, f'no notice that the block was left unbound:\n{out}'
    items = body_items(xml)
    assert not any(binds_forward(i) for i in items), \
        'an unhonourable chain was bound anyway'


def test_a_block_that_fits_is_bound_rather_than_declined(tmp_path):
    """Guards the guard above: if the height estimate drifted upward, every block
    would be quietly declined and all the tests that assert binding would be the only
    thing standing between us and silently shipping the original bug."""
    _, out = build(tmp_path, _page(CHART_BLOCK))
    assert 'exceeds' not in out, f'an ordinary block was declined:\n{out}'


def test_every_block_in_the_source_produces_a_bound_group(tmp_path):
    """No `.blk` may be lost between the HTML and the docx, whatever it contains."""
    html = _page(CHART_BLOCK, TABLE_BLOCK, CHART_BLOCK)
    xml, _ = build(tmp_path, html)
    assert html.count('class="blk"') == 3
    # three groups, each binding forward at least once → at least three keepNext runs
    assert len(re.findall(r'w:keepNext', xml)) >= 3, 'a block produced no grouping'


def test_content_survives_the_grouping(tmp_path):
    """Pagination must not cost text. The dispatch-branch bug that hid an entire chart
    from eleven documents passed every gate it had, because nothing asserted the
    content was still there."""
    xml, _ = build(tmp_path, _page(CHART_BLOCK, TABLE_BLOCK))
    allbody = ' '.join(text_of(el) for el in body_items(xml))
    for phrase in ('Annual Awards', 'Foothill College', 'De Anza College'):
        assert phrase in allbody, f'{phrase!r} was lost'


@pytest.mark.parametrize('html', [
    _page(),                                    # nothing at all
    _page(blk()),                               # an empty block
    _page(blk('<p class="tnar"></p>')),         # a block whose only part rendered empty
])
def test_degenerate_blocks_do_not_crash_the_build(tmp_path, html):
    """`_block()` is called with conditional parts (`... if spec.award_note else ''`),
    so an empty block is a real input, not a hypothetical."""
    build(tmp_path, html)
