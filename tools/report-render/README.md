# report-render

Build scripts that turn a **report HTML one-pager** into an editable `.docx` and
a pixel-perfect `.pdf`. Rescued from an ephemeral `/tmp` working set; this is the
back half of a future "title → report" framework (the front half — generating
the HTML from a `dossier` projection — does not exist yet; see below).

## The model: one source, two artifacts

The single source of truth is the **report HTML** (e.g.
`research/swp-strategy/svamp-pathway-49-9041-doc.html`). It is a self-contained,
browser-editable document: a `#page` div whose blocks follow fixed CSS
conventions, plus a toolbar/autosave script. Two artifacts derive from it:

- **`.pdf`** — Chromium print-to-PDF of the `?clean` page. Vector, exact, text
  selectable. The canonical-fidelity reference.
- **`.docx`** — a *native* python-docx build, element by element (real Word
  tables/paragraphs/hyperlinks), so it survives the Google-Docs paste. The one
  un-nativeable element — the SVG crosswalk funnel — is embedded as a high-DPI
  PNG. Editable, unlike a full-page raster.

Rationale: Pandoc/htmldocx drop CSS+SVG; LibreOffice `--convert-to` mangles
flex/SVG and Google Docs reflows it further. A controlled native build keeps the
docx both faithful **and** editable, with the PDF as the absolute-fidelity net.

## The HTML's CSS contract (what build_docx.py maps)

`build_docx.py` walks `#page` in order and dispatches on class/tag:

| HTML | → Word primitive |
|---|---|
| `.title` / `.subtitle` | title + accent rule / lede paragraph |
| `h1` | section heading |
| `p` (`.tnar`, `.tnote`, plain) | styled paragraphs; `<b>`/`<a>` become bold runs / hyperlinks |
| `table.dem` | demand band table |
| `table.live` | live-postings table (left SOC-color accent bars `lc1/lc2/lc3`) |
| `table.cmpgrid` | competency grid (colored `c1h/c2h/c3h` headers, `sec`/`descrow` rows) |
| `table.trend` | award / enrollment trend tables |
| `.xwrap` | embeds the crosswalk PNG |
| `.emps` / `.footer` | employer list / sourced footer |

A new title reuses this harness **only if its HTML follows the same contract.**

## Pipeline

```bash
cd tools/report-render
SRC=../../research/swp-strategy/svamp-pathway-49-9041-doc.html

# 1. (optional) live edit-and-show — autosaves the browser edits back to SRC
python3 docserver.py "$SRC" 8787      # open http://localhost:8787/

# 2. raster the SVG crosswalk for embedding (writes /tmp/crosswalk.png)
node shoot_xwalk_png.cjs "file://$PWD/$SRC?clean"

# 3. build the native .docx (reads /tmp/crosswalk.png)
python3 build_docx.py "$SRC" ../../research/swp-strategy/OUT.docx

# 4. build the PDF anchor
node shoot_pdf.cjs "file://$PWD/$SRC?clean" ../../research/swp-strategy/OUT.pdf

# review screenshot any time
node shoot_doc.cjs "file://$PWD/$SRC"        # writes /tmp/doc.png
```

All scripts take argv overrides; bare defaults reproduce the
"Manufacturing Technician" build.

## Deps

- python-docx, beautifulsoup4 (`pip install python-docx beautifulsoup4`)
- Playwright + Chromium, resolved from `atlas/node_modules` (already installed
  for the atlas frontend).

## Not yet built: the adapter

This harness renders a hand-authored HTML. To make "give me a title → get a
report" real, the missing piece is a generator that emits this HTML from a
`backend/partnerships/dossier.py` projection (grounded SOCs, demand, supply,
employers) instead of hand-typed numbers. That adapter belongs next to
`dossier.py`, not here.
