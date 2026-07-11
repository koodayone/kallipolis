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
  tables/paragraphs/hyperlinks), so it survives the Google-Docs paste. Even the
  SVG crosswalk is reconstructed as a native, fully-clickable table — every
  program-name link stays live — with the high-DPI PNG kept only as a fallback
  if the SVG can't be parsed. Editable, unlike a full-page raster.

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
| `.xwrap` | native crosswalk table — converge-to-target box (1 SOC) or program×SOC matrix (≥2 SOCs); PNG fallback only if the SVG won't parse |
| `.byline` / `.srcdash` / `.srcsec` / `.srclist` | byline + sourced footer blocks |
| `.emps` / `.footer` | employer list / sourced footer |

A new title reuses this harness **only if its HTML follows the same contract.**

## Pipeline

The canonical flow is **def-driven**: a saved report definition
(`backend/partnerships/saved_reports/{slug}.json`) → verified `.docx` + `.pdf`, one command:

```bash
cd tools/report-render
./export.sh svamp-industrial-machinery-mechanic          # → out/{slug}.docx + .pdf
./export.sh foothill-manufacturing-technician ~/Desktop  # 2nd arg overrides the out dir
```

`export.sh` renders the backend's clean `?raw=1` HTML, builds the docx + PDF, and **gates** on
`verify_docx.py` (link parity — every HTML link must survive into the Word doc; a drop fails the
build). It refuses to run while a `{slug}.edited.html` shadows the def (the def is truth —
consolidate + revert first). Needs a running backend (`API_BASE`, default `http://localhost:8000`).
Artifacts land in `out/` (gitignored). Exits non-zero on: missing def, edited.html present, backend
down, or a real link drop.

The lower-level steps `export.sh` orchestrates (for debugging, or rendering a hand-authored HTML
that follows the CSS contract):

```bash
SRC=out/svamp-industrial-machinery-mechanic.html
node shoot_xwalk_png.cjs "file://$PWD/$SRC" /tmp/crosswalk.png  # raster crosswalk (fallback net only)
python3 build_docx.py "$SRC" /tmp/OUT.docx /tmp/crosswalk.png   # native .docx
node shoot_pdf.cjs "file://$PWD/$SRC" /tmp/OUT.pdf              # PDF anchor
python3 verify_docx.py "$SRC" /tmp/OUT.docx                     # link-parity check
node shoot_doc.cjs "file://$PWD/$SRC"                           # review screenshot → /tmp/doc.png
```

`generate.sh <member> <title> <sector> <socs> …` is the legacy ad-hoc path (renders from the
query-param proposer endpoint, no saved def). All scripts take argv overrides.

## Deps

- python-docx, beautifulsoup4 (`pip install python-docx beautifulsoup4`)
- Playwright + Chromium, resolved from `atlas/node_modules` (already installed
  for the atlas frontend).

## The adapter (now built)

This harness once rendered only hand-authored HTML. The backend's
`partnerships.report.build_report_html` (filled by `propose_spec` from the L1 lens) now **is**
the generator — "give me a (member, role) → get a report" is real via the saved-report definition
and `export.sh`. The crosswalk renders as a native, clickable Word table (no rasterization); the
`/tmp/crosswalk.png` raster survives only as a parse-failure fallback for `build_docx.py`.
