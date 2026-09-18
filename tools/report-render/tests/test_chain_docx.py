# -*- coding: utf-8 -*-
"""Smoke tests for the TOP–CIP–SOC chain figure in tools/report-render/build_docx.py.

The fixture (`fixtures/chain_block.html`) is the page's own markup — the chain section of the
Foothill neurodiagnostic-technology evaluation (`partnerships.report._chain_section`) — saved
so this suite pins the HTML↔docx contract without importing the backend.

Coverage:
  - with a raster passed as the seventh argument the figure embeds as exactly one picture
  - without one the build still succeeds, the heading survives, and the caption's links are hyperlinks
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
FIXTURE = os.path.join(HERE, 'fixtures', 'chain_block.html')
W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'


def _png_1x1() -> bytes:
    """A valid one-pixel PNG, built rather than pasted so the fixture cannot rot."""
    import struct
    import zlib

    def chunk(tag, data):
        return struct.pack('>I', len(data)) + tag + data + struct.pack('>I', zlib.crc32(tag + data) & 0xffffffff)
    raw = zlib.compress(b'\x00\x00\x00\x00\xff')          # one row: filter 0, one RGBA pixel
    return (b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', 1, 1, 8, 6, 0, 0, 0))
            + chunk(b'IDAT', raw) + chunk(b'IEND', b''))


def _build(tmp, *extra):
    out = tmp / 'out.docx'
    r = subprocess.run([sys.executable, BUILD, FIXTURE, str(out), *extra], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    z = zipfile.ZipFile(out)
    return ET.fromstring(z.read('word/document.xml')), z.read('word/_rels/document.xml.rels').decode()


def test_chain_figure_embeds_as_one_picture_when_the_raster_is_given(tmp_path):
    png = tmp_path / 'chchart.png'
    png.write_bytes(_png_1x1())
    none = str(tmp_path / 'missing.png')
    root, _ = _build(tmp_path, none, none, none, none, str(png))
    assert len(list(root.iter(f'{W}drawing'))) == 1


def test_chain_section_survives_without_a_raster(tmp_path):
    root, rels = _build(tmp_path)
    texts = [''.join(t.text or '' for t in p.iter(f'{W}t')) for p in root.iter(f'{W}p')]
    assert any('TOP–CIP–SOC Crosswalk' in t for t in texts)
    assert len(list(root.iter(f'{W}drawing'))) == 0
    assert 'onetonline.org/link/summary/29-2099.01' in rels and 'nces.ed.gov' in rels
