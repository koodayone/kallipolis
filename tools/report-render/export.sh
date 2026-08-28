#!/usr/bin/env bash
# Phase-5 deliverable: a saved-report DEFINITION -> verified .docx + .pdf, one command.
#
# Renders the def-driven report from the running backend's clean (?raw=1) view, runs
# it through the native-docx + PDF harness, then GATES on a link-parity check (the
# docx-drift defense — a dropped link fails the build instead of shipping silently).
#
# The def is the single source of truth: this refuses to export while a hand-edited
# {slug}.edited.html shadows it (?raw=1 serves edited.html when present) — consolidate
# the edits into the def and revert first (Phase 4).
#
# Usage:   export.sh <slug> [out-dir]
# Example: ./export.sh svamp-industrial-machinery-mechanic
#          ./export.sh foothill-manufacturing-technician ~/Desktop
#
# Deps: a running backend (API_BASE, default http://localhost:8000); node + Playwright
# (resolved from ../../atlas/node_modules by the .cjs); python3 with python-docx +
# beautifulsoup4 for build_docx.py / verify_docx.py.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
REPO="$(cd "$HERE/../.." && pwd)"
API="${API_BASE:-http://localhost:8000}"

SLUG="${1:?usage: export.sh <slug> [out-dir]}"
OUTDIR="${2:-$HERE/out}"
SAVED="$REPO/backend/partnerships/saved_reports"
OUT="$OUTDIR/$SLUG"

# --- preflight: cheapest / most-likely-to-fail first ---
[ -f "$SAVED/$SLUG.json" ] || { echo "✗ no saved-report def: $SAVED/$SLUG.json" >&2; exit 1; }
if [ -f "$SAVED/$SLUG.edited.html" ]; then
  echo "✗ $SLUG.edited.html exists — the def is not truth yet." >&2
  echo "  Consolidate the hand-edits into the def, then revert (remove edited.html) — Phase 4." >&2
  echo "  (?raw=1 serves edited.html when present, so export would ship the stale edited copy.)" >&2
  exit 1
fi
curl -fsS -o /dev/null "$API/health" 2>/dev/null \
  || { echo "✗ backend not reachable at $API (start it, or set API_BASE)" >&2; exit 1; }

mkdir -p "$OUTDIR"
echo "export $SLUG  (backend $API -> $OUTDIR)"

echo "1/4 fetch clean HTML  (?raw=1, def-driven)"
curl -fsS "$API/partnerships/report/saved/$SLUG?raw=1" -o "$OUT.html"

echo "2/4 raster crosswalk  (fallback net)"
node "$HERE/shoot_xwalk_png.cjs" "file://$OUT.html" "$OUT.crosswalk.png" >/dev/null 2>&1 \
  || echo "    (raster skipped — the native crosswalk doesn't need it)"
# The awards-vs-demand chart has no native Word equivalent, so it is ALWAYS embedded
# as a raster (same harness, different selector). Absent -> build_docx omits it and the
# caption still carries the reading.
node "$HERE/shoot_xwalk_png.cjs" "file://$OUT.html" "$OUT.awchart.png" ".awchart" >/dev/null 2>&1 \
  || echo "    (no awards chart in this report)"

echo "3/4 build .docx"
python3 "$HERE/build_docx.py" "$OUT.html" "$OUT.docx" "$OUT.crosswalk.png" "$OUT.awchart.png" >/dev/null

echo "4/4 build .pdf"
node "$HERE/shoot_pdf.cjs" "file://$OUT.html" "$OUT.pdf" >/dev/null

echo "verify  (docx-drift defense)"
python3 "$HERE/verify_docx.py" "$OUT.html" "$OUT.docx"

echo "done -> $OUT.docx  $OUT.pdf"
