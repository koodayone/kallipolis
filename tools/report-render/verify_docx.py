# -*- coding: utf-8 -*-
"""Verify a build_docx.py .docx faithfully captured its source report HTML — the
docx-drift defense. The .docx is a SECOND renderer that maps HTML -> Word by CSS
class, so a new section or link pattern can be silently dropped or flattened. This
check is derived purely from the two artifacts (no coupling to build_docx's
handler list):

  link parity  (FAIL) — every unique external href in #page is a live hyperlink in
                        the docx. The one that actually matters; it gates the export.
                        (No crosswalk special-case: the PNG fallback re-emits its
                        links via add_xwalk_legend, so parity holds either way.)
  headings     (WARN) — every #page <h1> section heading survives as a paragraph.

(Table count is deliberately NOT checked: the .xwrap crosswalk is an SVG in the HTML
but a native table in the docx, so the docx always has exactly one more table —
build_docx.py prints its own "tables: N" for a sanity glance.)

Exit 1 only on a real link drop. Usage: verify_docx.py <SRC.html> <OUT.docx>

Deps: python-docx, beautifulsoup4.
"""
import html as _html
import re
import sys
import zipfile

from bs4 import BeautifulSoup
from docx import Document


def _norm(u: str) -> str:
    # BeautifulSoup hands back unescaped hrefs (& ), the docx rels store &amp; —
    # unescape both sides so the careeronestop-style &-laden URLs compare equal.
    return _html.unescape((u or "").strip())


def _docx_link_targets(path: str) -> set[str]:
    z = zipfile.ZipFile(path)
    names = z.namelist()
    rels_name = next((n for n in names if n.endswith("document.xml.rels")), None)
    if not rels_name:
        return set()
    rels = z.read(rels_name).decode("utf-8")
    return {_norm(t) for t in re.findall(r'Target="([^"]+)"', rels) if t.startswith("http")}


def main(src: str, out: str) -> int:
    page = BeautifulSoup(open(src, encoding="utf-8").read(), "html.parser").find(id="page")
    if page is None:
        print("  FAIL — no #page div in the source HTML", file=sys.stderr)
        return 1

    html_links = {_norm(a.get("href")) for a in page.find_all("a")
                  if (a.get("href") or "").startswith("http")}
    docx_links = _docx_link_targets(out)
    missing = sorted(h for h in html_links if h not in docx_links)

    docx_text = "\n".join(p.text for p in Document(out).paragraphs)
    lost_headings = [t for t in (h.get_text(" ", strip=True) for h in page.find_all("h1"))
                     if t and t not in docx_text]

    print(f"  link parity : {len(html_links) - len(missing)}/{len(html_links)} HTML links present in docx")
    if lost_headings:
        print(f"  WARN headings: not found in docx -> {lost_headings}")

    if missing:
        print(f"  FAIL link drift — {len(missing)} link(s) dropped by the docx renderer:")
        for m in missing:
            print(f"    - {m}")
        return 1
    print("  OK — every HTML link survives in the docx")
    return 0


if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.exit("usage: verify_docx.py <SRC.html> <OUT.docx>")
    sys.exit(main(sys.argv[1], sys.argv[2]))
