#!/bin/bash
# Run optimized PDF pipeline for all 26 Bay Area colleges in parallel.
# Limits concurrency to 5 at a time to avoid Gemini rate limits.
#
# Usage: cd backend && bash run_all.sh

set -e

COLLEGES=(
  alameda berkeleycc cabrillo canada ccsf chabot citrus
  contracosta csm deanza diablo evergreen foothill gavilan
  laney laspositas losmedanos marin merritt mission napavalley
  ohlone sanjosecity santarosa skyline solano westvalley
)

MAX_PARALLEL=5
LOG_DIR="pipeline/logs"
mkdir -p "$LOG_DIR"

echo "Starting pipeline for ${#COLLEGES[@]} colleges (max $MAX_PARALLEL parallel)..."
echo ""

running=0
for college in "${COLLEGES[@]}"; do
  echo "[START] $college"
  python3 -m pipeline.run --college "$college" --scrape-only \
    > "$LOG_DIR/${college}.log" 2>&1 &

  running=$((running + 1))

  if [ "$running" -ge "$MAX_PARALLEL" ]; then
    wait -n  # Wait for any one job to finish
    running=$((running - 1))
  fi
done

# Wait for all remaining jobs
wait

echo ""
echo "All pipelines complete. Checking results..."
echo ""

# Summary
for college in "${COLLEGES[@]}"; do
  log="$LOG_DIR/${college}.log"
  if grep -q "Stage 1 complete" "$log" 2>/dev/null; then
    courses=$(grep "Stage 1 complete" "$log" | grep -o '[0-9]* courses')
    echo "  [OK]   $college: $courses"
  elif grep -q "No course pages" "$log" 2>/dev/null; then
    echo "  [FAIL] $college: no course pages detected"
  else
    tail -1 "$log" 2>/dev/null | sed "s/^/  [FAIL] $college: /"
  fi
done
