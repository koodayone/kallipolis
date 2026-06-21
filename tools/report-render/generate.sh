#!/usr/bin/env bash
# One-command workforce-pathway report generation: a role → .html + .docx + .pdf.
#
# Renders the backend's proposer-filled report (GET /partnerships/report/{member})
# through this harness. The backend must be running — it owns the graph that L1
# reads. The role is the "play": a title + sector + the SOCs it maps to.
#
# Usage:
#   generate.sh <member> <title> <sector> <socs> [out-basename] [author] [date]
# Example:
#   ./generate.sh svamp "Manufacturing Technician" adm "17-3026,51-9141,17-3024" \
#       /tmp/mt "Dayone Koo" "June 21, 2026"
#
# Deps: a running backend (API_BASE, default http://localhost:8000), node +
# Playwright (resolved from ../../atlas/node_modules by the .cjs), and a python3
# with python-docx + beautifulsoup4 for build_docx.py.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
API="${API_BASE:-http://localhost:8000}"

MEMBER="${1:?member}"; TITLE="${2:?title}"; SECTOR="${3:?sector}"; SOCS="${4:?socs}"
OUT="${5:-/tmp/report}"; AUTHOR="${6:-Kallipolis}"; DATE="${7:-}"

QS=$(python3 -c "import urllib.parse,sys; print(urllib.parse.urlencode({'title':sys.argv[1],'sector':sys.argv[2],'socs':sys.argv[3],'author':sys.argv[4],'date':sys.argv[5]}))" \
  "$TITLE" "$SECTOR" "$SOCS" "$AUTHOR" "$DATE")
URL="$API/partnerships/report/$MEMBER?$QS"

echo "1/4 fetch report HTML  ($MEMBER · $TITLE)"
curl -fsS "$URL" -o "$OUT.html"
echo "2/4 raster crosswalk"
node "$HERE/shoot_xwalk_png.cjs" "file://$OUT.html" "$OUT.crosswalk.png" >/dev/null
echo "3/4 build .docx"
python3 "$HERE/build_docx.py" "$OUT.html" "$OUT.docx" "$OUT.crosswalk.png" >/dev/null
echo "4/4 build .pdf"
node "$HERE/shoot_pdf.cjs" "file://$OUT.html" "$OUT.pdf" >/dev/null
echo "done → $OUT.html  $OUT.docx  $OUT.pdf"
