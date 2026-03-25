#!/bin/bash
# Run optimized PDF pipeline for all Bay Area colleges in parallel.
# Limits concurrency to 5 at a time to avoid Gemini rate limits.
#
# Usage: cd backend && bash run_all.sh

COLLEGES=(
  alameda berkeleycc cabrillo canada ccsf chabot citrus
  contracosta csm deanza diablo evergreen foothill gavilan
  laney laspositas losmedanos marin merritt mission napavalley
  ohlone sanjosecity santarosa skyline solano westvalley
)

MAX_PARALLEL=3
LOG_DIR="pipeline/logs"
mkdir -p "$LOG_DIR"

echo "Starting pipeline for ${#COLLEGES[@]} colleges (max $MAX_PARALLEL parallel)..."
echo ""

pids=()

for college in "${COLLEGES[@]}"; do
  # Wait if we've hit the concurrency limit
  while [ ${#pids[@]} -ge $MAX_PARALLEL ]; do
    new_pids=()
    for pid in "${pids[@]}"; do
      if kill -0 "$pid" 2>/dev/null; then
        new_pids+=("$pid")
      fi
    done
    pids=("${new_pids[@]}")
    if [ ${#pids[@]} -ge $MAX_PARALLEL ]; then
      sleep 2
    fi
  done

  echo "[START] $college"
  python3 -m pipeline.run --college "$college" --scrape-only \
    > "$LOG_DIR/${college}.log" 2>&1 &
  pids+=($!)
done

# Wait for all remaining jobs
echo ""
echo "All jobs launched. Waiting for completion..."
for pid in "${pids[@]}"; do
  wait "$pid" 2>/dev/null
done

echo ""
echo "All pipelines complete. Results:"
echo ""

# Summary
pass=0
fail=0
for college in "${COLLEGES[@]}"; do
  log="$LOG_DIR/${college}.log"
  if grep -q "Stage 1 complete" "$log" 2>/dev/null; then
    courses=$(grep "Stage 1 complete" "$log" | grep -o '[0-9]* courses')
    echo "  [OK]   $college: $courses"
    pass=$((pass + 1))
  elif grep -q "No course pages" "$log" 2>/dev/null; then
    echo "  [FAIL] $college: no course pages detected"
    fail=$((fail + 1))
  else
    last=$(tail -1 "$log" 2>/dev/null)
    echo "  [FAIL] $college: ${last:0:80}"
    fail=$((fail + 1))
  fi
done

echo ""
echo "Done: $pass passed, $fail failed out of ${#COLLEGES[@]} colleges"
