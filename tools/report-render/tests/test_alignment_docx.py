# -*- coding: utf-8 -*-
"""Smoke tests for the curriculum-alignment and living-wage forms in tools/report-render/build_docx.py.

The fixture (`fixtures/alignment_block.html`) is the page's own markup — a certificate-column
block from `partnerships.alignment_plate.occupation_block` with its description and key, and a
demand table with the living-wage columns from `partnerships.report._demand_table` — saved so
this suite pins the HTML↔docx contract without importing the backend.

Coverage:
  - a course chip is a shaded run — white bold code on the column's colour — and a linked one is a hyperlink
  - the block's key chip takes the colour it is given
  - the excerpt's caption and sentence carry a left rule in the tier's shade
  - the block head (description, key, title) binds forward to its table
  - tables draw hairline rows and no vertical rules; the header row repeats
  - the demand table's hourly and living-wage columns survive into the docx
"""
import os
import subprocess
import sys
import xml.etree.ElementTree as ET
import zipfile

import pytest

pytest.importorskip('docx', reason='pip install -r tools/report-render/requirements.txt')
pytest.importorskip('bs4', reason='pip install -r tools/report-render/requirements.txt')

HERE = os.path.dirname(os.path.abspath(__file__))
BUILD = os.path.join(os.path.dirname(HERE), 'build_docx.py')
FIXTURE = os.path.join(HERE, 'fixtures', 'alignment_block.html')
W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'


@pytest.fixture(scope='module')
def built(tmp_path_factory):
    out = tmp_path_factory.mktemp('docx') / 'out.docx'
    r = subprocess.run([sys.executable, BUILD, FIXTURE, str(out)], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    z = zipfile.ZipFile(out)
    return ET.fromstring(z.read('word/document.xml')), z.read('word/_rels/document.xml.rels').decode()


def _text(el):
    return ''.join(t.text or '' for t in el.iter(f'{W}t'))


def test_chips_are_shaded_runs_and_linked(built):
    root, rels = built
    shd = [r for r in root.iter(f'{W}r') if r.find(f'{W}rPr/{W}shd') is not None]
    texts = [_text(r).strip() for r in shd]
    assert texts == ['CODE', 'RSPT 50A', 'RSPT 70A'], texts
    assert {r.find(f'{W}rPr/{W}shd').get(f'{W}fill') for r in shd} == {'c98a1b', 'b1122b'}   # key colour; the column's --c
    assert all(r.find(f'{W}rPr/{W}color').get(f'{W}val') == 'ffffff' and r.find(f'{W}rPr/{W}b') is not None for r in shd)
    assert any(h.find(f'{W}r/{W}rPr/{W}shd') is not None for h in root.iter(f'{W}hyperlink'))
    assert 'https://x/50a' in rels and 'https://x/70a' in rels


def test_excerpt_carries_a_left_rule_in_the_tier_shade(built):
    root, _ = built
    ruled = [p for p in root.iter(f'{W}p') if p.find(f'{W}pPr/{W}pBdr/{W}left') is not None]
    colours = [p.find(f'{W}pPr/{W}pBdr/{W}left').get(f'{W}color') for p in ruled]
    assert colours == ['2a3450', '2a3450', '7a869a', '7a869a']          # caption + sentence per row; commit dark, cover grey
    assert _text(ruled[0]) == 'COURSE OBJECTIVE' and 'aerosol' in _text(ruled[1])


def test_block_head_binds_forward(built):
    root, _ = built
    body = root.find(f'{W}body')
    for key in ('Assesses patients', 'CODE', 'Respiratory Therapists'):
        p = next(p for p in body.iter(f'{W}p') if key in _text(p))
        assert p.find(f'{W}pPr/{W}keepNext') is not None, key


def test_tables_are_hairline_rows_with_repeating_headers(built):
    root, _ = built
    tbls = list(root.iter(f'{W}tbl'))
    assert len(tbls) == 2
    for tbl in tbls:
        b = {e.tag.split('}')[1]: e.get(f'{W}val') for e in tbl.find(f'{W}tblPr/{W}tblBorders')}
        assert b == {'top': 'single', 'bottom': 'single', 'insideH': 'single', 'left': 'nil', 'right': 'nil', 'insideV': 'nil'}
        assert tbl.find(f'{W}tr').find(f'{W}trPr/{W}tblHeader') is not None


def test_demand_columns_survive(built):
    root, _ = built
    xml = _text(root)
    assert 'Median hourly' in xml and 'vs. living wage' in xml and '$29.46' in xml and '−$8.54' in xml
