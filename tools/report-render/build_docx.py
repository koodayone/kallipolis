# -*- coding: utf-8 -*-
"""Native, controlled HTML->DOCX build of a SVAMP-style workforce one-pager.

Single source = the rendered report HTML (a `#page` div whose blocks use the
report's CSS conventions: `.title`, `.subtitle`, `h1`, `p`, `table.dem|live|
cmpgrid|trend`, `.xwrap`, `.emps`, `.footer`). Every element is mapped to a
native Word primitive; the only un-nativeable element (the SVG crosswalk) is
embedded as a high-DPI PNG. Produces an editable, faithful .docx that survives
the Google-Docs paste cleanly (native tables are the one richly-supported
primitive).

Usage:
    python3 build_docx.py [SRC.html] [OUT.docx] [CROSSWALK.png]

Defaults reproduce the "Manufacturing Technician" build. SRC must be the HTML
that shoot_xwalk_png.cjs already rasterized into CROSSWALK (default
/tmp/crosswalk.png) — run that shooter first.

Deps: python-docx, beautifulsoup4.
"""
import sys

import docx
from docx import Document
from docx.shared import Pt, RGBColor, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from docx.opc.constants import RELATIONSHIP_TYPE as RT
from bs4 import BeautifulSoup

_RESEARCH = '/Users/dayonekoo/Desktop/code/kallipolis/research/swp-strategy'
SRC = sys.argv[1] if len(sys.argv) > 1 else f'{_RESEARCH}/svamp-pathway-49-9041-doc.html'
OUT = sys.argv[2] if len(sys.argv) > 2 else f'{_RESEARCH}/svamp-pathway-manufacturing-technician.docx'
XWALK = sys.argv[3] if len(sys.argv) > 3 else '/tmp/crosswalk.png'
FONT = 'Arial'

TEAL, BLUE, RED = '2a9d8f', '2e74b5', 'cc3333'
DARK, BODY, MUT = '2a3450', '33405a', '9099ab'
HFILL, TOTFILL, SECFILL = 'eef1f6', 'f2f6fc', 'eef1f6'
SOCCOL = {'lc1': TEAL, 'lc2': BLUE, 'lc3': RED, 'c1h': TEAL, 'c2h': BLUE, 'c3h': RED}

soup = BeautifulSoup(open(SRC, encoding='utf-8').read(), 'html.parser')
page = soup.find(id='page')
doc = Document()
st = doc.styles['Normal']
st.font.name = FONT
st.font.size = Pt(10)
st.font.color.rgb = RGBColor.from_string(BODY)
sec = doc.sections[0]
sec.page_width, sec.page_height = Inches(8.5), Inches(11)
sec.left_margin = sec.right_margin = Inches(0.7)
sec.top_margin = sec.bottom_margin = Inches(0.55)
CONTENT_W = 7.1


# ---------- low-level helpers ----------
def shade(cell, hexc):
    sh = OxmlElement('w:shd'); sh.set(qn('w:val'), 'clear'); sh.set(qn('w:fill'), hexc)
    cell._tc.get_or_add_tcPr().append(sh)


def left_accent(cell, hexc, sz=24):
    tcPr = cell._tc.get_or_add_tcPr()
    borders = OxmlElement('w:tcBorders')
    b = OxmlElement('w:left'); b.set(qn('w:val'), 'single'); b.set(qn('w:sz'), str(sz))
    b.set(qn('w:space'), '0'); b.set(qn('w:color'), hexc)
    borders.append(b); tcPr.append(borders)


def grid(tbl, hexc='dfe3ea'):
    t = tbl._tbl
    el = OxmlElement('w:tblBorders')
    for edge in ('top', 'left', 'bottom', 'right', 'insideH', 'insideV'):
        e = OxmlElement('w:' + edge); e.set(qn('w:val'), 'single'); e.set(qn('w:sz'), '4')
        e.set(qn('w:space'), '0'); e.set(qn('w:color'), hexc); el.append(e)
    t.tblPr.append(el)


def cellpad(cell, top=40, bottom=40, left=80, right=80):
    tcPr = cell._tc.get_or_add_tcPr()
    m = OxmlElement('w:tcMar')
    for k, v in (('top', top), ('bottom', bottom), ('left', left), ('right', right)):
        e = OxmlElement('w:' + k); e.set(qn('w:w'), str(v)); e.set(qn('w:type'), 'dxa'); m.append(e)
    tcPr.append(m)


def run(p, text, size=10, bold=False, color=BODY, italic=False):
    r = p.add_run(text); r.font.name = FONT; r.font.size = Pt(size)
    r.font.bold = bold; r.font.italic = italic; r.font.color.rgb = RGBColor.from_string(color)
    return r


def hyperlink(p, url, text, color=BLUE, size=9):
    r_id = p.part.relate_to(url, RT.HYPERLINK, is_external=True)
    link = OxmlElement('w:hyperlink'); link.set(qn('r:id'), r_id)
    rr = OxmlElement('w:r'); rPr = OxmlElement('w:rPr')
    for tag, val in (('w:color', color),):
        e = OxmlElement(tag); e.set(qn('w:val'), val); rPr.append(e)
    u = OxmlElement('w:u'); u.set(qn('w:val'), 'single'); rPr.append(u)
    sz = OxmlElement('w:sz'); sz.set(qn('w:val'), str(int(size * 2))); rPr.append(sz)
    rf = OxmlElement('w:rFonts'); rf.set(qn('w:ascii'), FONT); rf.set(qn('w:hAnsi'), FONT); rPr.append(rf)
    rr.append(rPr); t = OxmlElement('w:t'); t.set(qn('xml:space'), 'preserve'); t.text = text; rr.append(t)
    link.append(rr); p._p.append(link)


def para(space_before=2, space_after=4):
    p = doc.add_paragraph(); pf = p.paragraph_format
    pf.space_before = Pt(space_before); pf.space_after = Pt(space_after); pf.line_spacing = 1.12
    return p


def runs_from(el, p, size=10, color=BODY):
    """emit a <p>'s inline content as runs, honoring <b> and <a>."""
    for node in el.children:
        nm = getattr(node, 'name', None)
        if nm is None:
            txt = str(node).replace('\xa0', ' ')
            if txt.strip():
                run(p, txt, size=size, color=color)
        elif nm == 'b':
            run(p, node.get_text(' ', strip=True), size=size, bold=True, color=DARK)
        elif nm == 'a':
            hyperlink(p, node.get('href', ''), node.get_text(' ', strip=True), size=size)
        else:
            run(p, node.get_text(' ', strip=True), size=size, color=color)


def rows_of(table):
    out = []
    for tr in table.find_all('tr'):
        cells = []
        for c in tr.find_all(['th', 'td'], recursive=False):
            cells.append({'text': c.get_text(' ', strip=True).replace('\xa0', ' '), 'th': c.name == 'th',
                          'colspan': int(c.get('colspan', 1)), 'cls': c.get('class', []), 'el': c})
        if cells:
            out.append({'cells': cells, 'cls': tr.get('class', [])})
    return out


# ---------- block builders ----------
def add_title(text):
    p = para(0, 2); p.paragraph_format.space_after = Pt(2)
    run(p, text.replace('\xa0', '').strip(), size=20, bold=True, color=DARK)
    # accent rule
    hr = para(0, 6); pPr = hr._p.get_or_add_pPr(); b = OxmlElement('w:pBdr')
    bot = OxmlElement('w:bottom'); bot.set(qn('w:val'), 'single'); bot.set(qn('w:sz'), '10')
    bot.set(qn('w:space'), '2'); bot.set(qn('w:color'), BLUE); b.append(bot); pPr.append(b)


def add_lede(text):
    p = para(0, 8); runs = text.strip()
    run(p, runs, size=10.5, color=BODY)


def add_heading(text):
    p = para(8, 3); run(p, text.replace('\xa0', '').strip(), size=13, bold=True, color=BLUE)


def std_table(rows, widths=None, header=True, num_from=2, totalcls='tot'):
    ncol = max(sum(c['colspan'] for c in r['cells']) for r in rows)
    tbl = doc.add_table(rows=0, cols=ncol); tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    grid(tbl)
    for r in rows:
        cells = tbl.add_row().cells
        ci = 0
        istot = totalcls in r['cls']
        ishdr = all(c['th'] for c in r['cells']) and r is rows[0]
        for c in r['cells']:
            cell = cells[ci]
            for j in range(1, c['colspan']):
                cell.merge(cells[ci + j])
            p = cell.paragraphs[0]; p.paragraph_format.space_before = Pt(1); p.paragraph_format.space_after = Pt(1)
            isnum = ci >= num_from
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER if isnum else WD_ALIGN_PARAGRAPH.LEFT
            col = MUT if c['text'] in ('—', '-') else (DARK if (ishdr or istot) else BODY)
            run(p, c['text'], size=8.5, bold=(ishdr or istot), color=col)
            if ishdr:
                shade(cell, HFILL)
            if istot:
                shade(cell, TOTFILL)
            cellpad(cell)
            ci += c['colspan']
    return tbl


def add_trend(table):
    rows = rows_of(table)
    tbl = doc.add_table(rows=0, cols=6); tbl.alignment = WD_TABLE_ALIGNMENT.CENTER; grid(tbl)
    for ri, r in enumerate(rows):
        cells = tbl.add_row().cells
        istot = 'tot' in r['cls']; ishdr = ri == 0
        for ci, c in enumerate(r['cells']):
            cell = cells[ci]; p = cell.paragraphs[0]
            p.paragraph_format.space_before = Pt(1); p.paragraph_format.space_after = Pt(1)
            if ci == 0 and not ishdr and not istot:
                b = c['el'].find('b'); span = c['el'].find('span')
                run(p, (b.get_text(strip=True) if b else c['text']), size=9, bold=True, color=DARK)
                if span:
                    p2 = cell.add_paragraph(); p2.paragraph_format.space_before = Pt(0); p2.paragraph_format.space_after = Pt(0)
                    run(p2, span.get_text(' ', strip=True), size=7.5, color=MUT)
            else:
                p.alignment = WD_ALIGN_PARAGRAPH.LEFT if ci == 0 else WD_ALIGN_PARAGRAPH.CENTER
                col = MUT if c['text'] in ('—', '-') else (DARK if (ishdr or istot) else BODY)
                run(p, c['text'], size=8.5, bold=(ishdr or istot), color=col)
            if ishdr:
                shade(cell, HFILL)
            if istot:
                shade(cell, TOTFILL)
            cellpad(cell)


def add_live(table):
    rows = rows_of(table)
    tbl = doc.add_table(rows=0, cols=3); tbl.alignment = WD_TABLE_ALIGNMENT.CENTER; grid(tbl)
    for ri, r in enumerate(rows):
        cells = tbl.add_row().cells
        ishdr = ri == 0
        accent = next((SOCCOL[c] for c in r['cls'] if c in SOCCOL), None)
        for ci, c in enumerate(r['cells']):
            cell = cells[ci]; p = cell.paragraphs[0]
            p.paragraph_format.space_before = Pt(1); p.paragraph_format.space_after = Pt(1)
            if ishdr:
                run(p, c['text'], size=8, bold=True, color='5a6577'); shade(cell, HFILL)
            elif ci == 0:  # occupation + SOC sub
                b = c['el'].find('span')
                txt = c['el'].get_text('\n', strip=True).split('\n')
                run(p, txt[0], size=9, bold=True, color=DARK)
                if len(txt) > 1:
                    p2 = cell.add_paragraph(); p2.paragraph_format.space_before = Pt(0); p2.paragraph_format.space_after = Pt(0)
                    run(p2, txt[1], size=7.5, color=MUT)
            elif ci == 1:
                run(p, c['text'], size=9, bold=True, color=DARK)
            else:
                a = c['el'].find('a')
                if a:
                    hyperlink(p, a.get('href', ''), a.get_text(' ', strip=True).replace('↗', '').strip() + '  ↗', size=9)
                else:
                    run(p, c['text'], size=9, color=BODY)
            if ci == 0 and accent:
                left_accent(cell, accent)
            cellpad(cell)


def add_cmpgrid(table):
    rows = rows_of(table)
    tbl = doc.add_table(rows=0, cols=3); tbl.alignment = WD_TABLE_ALIGNMENT.CENTER; grid(tbl)
    for ri, r in enumerate(rows):
        cells = tbl.add_row().cells
        issec = 'sec' in r['cls']; isdesc = 'descrow' in r['cls']
        if issec:  # section divider, colspan 3
            cell = cells[0]; cell.merge(cells[1]); cell.merge(cells[2])
            p = cell.paragraphs[0]; run(p, r['cells'][0]['text'].upper(), size=8, bold=True, color=MUT); shade(cell, SECFILL); cellpad(cell); continue
        for ci, c in enumerate(r['cells']):
            cell = cells[ci]; p = cell.paragraphs[0]
            p.paragraph_format.space_before = Pt(1); p.paragraph_format.space_after = Pt(1)
            if ri == 0:  # colored occupation headers
                hexc = next((SOCCOL[x] for x in c['cls'] if x in SOCCOL), HFILL)
                lines = c['el'].get_text('\n', strip=True).split('\n')
                run(p, lines[0], size=9, bold=True, color='ffffff')
                if len(lines) > 1:
                    p2 = cell.add_paragraph(); p2.paragraph_format.space_before = Pt(0); p2.paragraph_format.space_after = Pt(0)
                    run(p2, lines[1], size=7, color='ffffff')
                shade(cell, hexc)
            else:
                run(p, c['text'], size=8.5, color=(MUT if isdesc else BODY), italic=isdesc)
            cellpad(cell)


def add_emps(div):
    p = para(2, 4)
    for node in div.children:
        nm = getattr(node, 'name', None)
        if nm == 'br':
            p = para(1, 2); continue
        if nm is None:
            t = str(node).replace('\xa0', ' ')
            if t.strip():
                run(p, t, size=10, color=BODY)
        elif nm == 'span' and 'e' in node.get('class', []):
            run(p, node.get_text(' ', strip=True), size=10, bold=True, color=DARK)
        elif nm == 'a':
            hyperlink(p, node.get('href', ''), node.get_text(' ', strip=True), size=9)
        else:
            run(p, node.get_text(' ', strip=True), size=10, color=BODY)


def add_footer(div):
    para(6, 2)
    for line in div.get_text('\n', strip=True).split('\n'):
        if not line.strip():
            continue
        p = doc.add_paragraph(); p.paragraph_format.space_before = Pt(0); p.paragraph_format.space_after = Pt(1)
        run(p, line.strip(), size=7.5, color=MUT, italic=True)


def add_image():
    p = para(4, 4); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.add_run().add_picture(XWALK, width=Inches(CONTENT_W))


# ---------- ordered walk ----------
def emit(el):
    nm = getattr(el, 'name', None)
    if nm is None:
        return
    cls = el.get('class', [])
    if 'title' in cls:
        add_title(el.get_text(' ', strip=True))
    elif 'subtitle' in cls:
        t = el.get_text(' ', strip=True)
        if t:
            add_lede(t)
    elif nm == 'h1':
        add_heading(el.get_text(' ', strip=True))
    elif nm == 'p':
        t = el.get_text(' ', strip=True)
        if not t:
            return
        if 'tnote' in cls:
            p = para(1, 4); run(p, t, size=8.5, color=MUT, italic=True)
        elif 'tnar' in cls:
            p = para(6, 2); run(p, t, size=10, color='46536b')
        else:
            p = para(2, 5); runs_from(el, p, size=10.5)
    elif nm == 'table':
        if 'dem' in cls:
            std_table(rows_of(el))
        elif 'live' in cls:
            add_live(el)
        elif 'cmpgrid' in cls:
            add_cmpgrid(el)
        elif 'trend' in cls:
            add_trend(el)
    elif 'xwrap' in cls:
        add_image()
    elif 'emps' in cls:
        add_emps(el)
    elif 'footer' in cls:
        add_footer(el)
    elif 'demstat' in cls:
        pass
    else:
        for ch in el.children:
            emit(ch)


for child in page.children:
    emit(child)

doc.save(OUT)
print('saved', OUT)
print('paragraphs:', len(doc.paragraphs), '| tables:', len(doc.tables))
