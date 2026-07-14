#!/usr/bin/env bash
# Neo4j page-cache warmup — pulls the entire graph store into Neo4j's
# off-heap page cache so the FIRST user query after a restart hits warm
# pages instead of the disk.
#
# Why this exists: Neo4j's page cache lives in the Neo4j *process* and is
# emptied on every restart (the nightly backup stops/starts neo4j; so do
# VM reboots and crashes). On the pd-standard (HDD) prod disk a cold
# traversal is thousands of ~14ms random reads = tens of seconds; the same
# query warm is sub-second. The whole graph is ~200MB against a 4GB page
# cache, so one sequential-ish scan makes ALL subsequent reads warm and
# nothing ever evicts. Warming after each restart converts "first user
# pays 20s" into "this script pays a few seconds, off the critical path".
#
# APOC is not installed on prod, so we warm with plain Cypher store scans
# rather than apoc.warmup.run:
#   - count(n) / count(r)            → node store + relationship store
#   - UNWIND keys(x) ... count(x[k]) → property records + string/array
#                                       dynamic stores (materializing each
#                                       value forces the dynamic-store read)
# Range indexes (~16MB) are left to warm organically on first real queries;
# they are small and their B-tree pages go hot within the first few hits.
#
# Idempotent and best-effort: safe to run any number of times; a warm
# cache just makes it finish in ~1s. Never fails its caller — the backup
# script calls it with `|| true`.
#
# Manual:   sudo /opt/kallipolis/scripts/warmup-neo4j.sh
# Override for local testing:
#   ENV_FILE=./.env NEO4J_CONTAINER=kallipolis-neo4j-1 ./scripts/warmup-neo4j.sh

set -uo pipefail

NEO4J_CONTAINER="${NEO4J_CONTAINER:-kallipolis-neo4j-1}"
ENV_FILE="${ENV_FILE:-/opt/kallipolis/.env}"
READY_TRIES="${READY_TRIES:-60}"      # × 2s = up to 120s waiting for neo4j
READY_SLEEP=2

log() { echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) warmup: $*"; }

# ── Resolve the neo4j password from the .env (NEO4J_AUTH=neo4j/<pw> on
#    prod, NEO4J_PASSWORD=<pw> locally) ──────────────────────────────────
resolve_pw() {
    local pw=""
    if [ -f "$ENV_FILE" ]; then
        pw=$(grep -E '^NEO4J_AUTH=' "$ENV_FILE" 2>/dev/null | head -1 | cut -d= -f2- | sed 's#^neo4j/##')
        [ -z "$pw" ] && pw=$(grep -E '^NEO4J_PASSWORD=' "$ENV_FILE" 2>/dev/null | head -1 | cut -d= -f2-)
    fi
    printf '%s' "$pw"
}

PW="$(resolve_pw)"
if [ -z "$PW" ]; then
    log "ERROR could not read neo4j password from $ENV_FILE — aborting (no-op)"
    exit 0   # best-effort: never break a caller
fi

cyq() {  # run one cypher statement, print plain result to stdout
    docker exec "$NEO4J_CONTAINER" cypher-shell -u neo4j -p "$PW" --format plain "$1" 2>&1
}

# ── Wait for neo4j to accept queries (fresh container needs ~10-30s) ─────
log "waiting for $NEO4J_CONTAINER to accept queries"
ready=0
for _ in $(seq 1 "$READY_TRIES"); do
    if docker exec "$NEO4J_CONTAINER" cypher-shell -u neo4j -p "$PW" "RETURN 1;" >/dev/null 2>&1; then
        ready=1; break
    fi
    sleep "$READY_SLEEP"
done
if [ "$ready" -ne 1 ]; then
    log "ERROR neo4j not ready after $((READY_TRIES * READY_SLEEP))s — aborting (no-op)"
    exit 0
fi

# ── The warmup scans, timed individually for observability ──────────────
run_scan() {
    local label="$1" cypher="$2" t0 t1 out val rc
    t0=$(date +%s.%N)
    out="$(cyq "$cypher")"; rc=$?
    t1=$(date +%s.%N)
    if [ $rc -ne 0 ] || printf '%s' "$out" | grep -qiE 'error|exception|failed'; then
        log "WARN scan '$label' did not complete cleanly :: $(printf '%s' "$out" | tail -1)"
        return 1
    fi
    val=$(printf '%s' "$out" | tail -1 | tr -d ' ')
    local dur; dur=$(awk -v s="$t0" -v e="$t1" 'BEGIN{ printf "%.1f", e-s }')
    printf '%s warmup:   %-18s value=%-12s %5ss\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$label" "$val" "$dur"
    return 0
}

log "starting store scans (container=$NEO4J_CONTAINER)"
WARM_T0=$(date +%s.%N)
run_scan "nodes"      'MATCH (n) RETURN count(n) AS c;'
run_scan "node_props" 'MATCH (n) UNWIND keys(n) AS k RETURN count(n[k]) AS c;'
run_scan "rels"       'MATCH ()-[r]->() RETURN count(r) AS c;'
run_scan "rel_props"  'MATCH ()-[r]->() UNWIND keys(r) AS k RETURN count(r[k]) AS c;'
WARM_T1=$(date +%s.%N)
TOTAL=$(awk -v s="$WARM_T0" -v e="$WARM_T1" 'BEGIN{ printf "%.1f", e-s }')
log "complete in ${TOTAL}s"
