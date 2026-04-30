#!/usr/bin/env bash
# Neo4j restore drill — proves that a backup in GCS can actually be
# restored end-to-end. Designed to be safe to run anytime: never
# touches the live kallipolis-neo4j-1 container or its
# kallipolis_neo4j_data volume.
#
# What it does:
#   1. Picks a GCS dump (defaults to most recent in
#      gs://kallipolis-backups-preview/).
#   2. Pulls it to a temp dir on disk.
#   3. Loads it into a SANDBOX Docker volume (different name).
#   4. Spins up a SANDBOX neo4j container on alternate ports
#      (7475 / 7688), so even if the live container is up, there
#      is no port collision and no shared volume.
#   5. Runs verification queries (node + relationship counts) and
#      prints them so the operator can compare to the dump's
#      manifest (or to the live db, or to remembered counts).
#   6. Tears down the sandbox container + volume + temp dir.
#
# Usage:
#   ./scripts/neo4j-restore-drill.sh                  # most recent
#   ./scripts/neo4j-restore-drill.sh <object-name>    # specific
#   ./scripts/neo4j-restore-drill.sh --keep           # don't tear down on exit
#
# Live neo4j is never touched. The script also defends against
# operator error: if SANDBOX_VOLUME ever resolves to a name
# containing "kallipolis_neo4j_data" without the "_drill" suffix,
# the script aborts before doing anything destructive.

set -euo pipefail

GCS_BUCKET=gs://kallipolis-backups-preview
SANDBOX_VOLUME=kallipolis_neo4j_data_drill
SANDBOX_CONTAINER=kallipolis-neo4j-drill
SANDBOX_HTTP_PORT=7475
SANDBOX_BOLT_PORT=7688
NEO4J_CONTAINER_UID=7474
DRILL_PASSWORD=drilltest_throwaway

# ── Safety guard: do not allow the sandbox name to ever match the
#    live volume name. A bug in this script that defaults
#    SANDBOX_VOLUME to "kallipolis_neo4j_data" would otherwise wipe
#    the live data. Catch it before any destructive step runs.
if [[ "$SANDBOX_VOLUME" != *"_drill"* ]]; then
    echo "ABORT: SANDBOX_VOLUME ($SANDBOX_VOLUME) does not contain _drill suffix"
    echo "Refusing to proceed; this would risk the live volume."
    exit 1
fi

# ── Argument parsing
GCS_OBJECT=""
KEEP_SANDBOX=false
for arg in "$@"; do
    case "$arg" in
        --keep) KEEP_SANDBOX=true ;;
        *)      GCS_OBJECT="$arg" ;;
    esac
done

# Pick the dump if not specified
if [ -z "$GCS_OBJECT" ]; then
    # Most recent top-level neo4j-*.dump (excludes the local/ subdir)
    GCS_OBJECT=$(gsutil ls "${GCS_BUCKET}/neo4j-*.dump" 2>/dev/null \
                 | sort \
                 | tail -1 \
                 | sed "s|${GCS_BUCKET}/||")
fi

if [ -z "$GCS_OBJECT" ]; then
    echo "ERROR: no GCS dump found in ${GCS_BUCKET}"
    exit 1
fi

# Drill dir lives inside the repo backups/ so Docker Desktop's
# user-mapping for bind mounts works (the system tmp dir at
# /var/folders/... has different ownership rules and the helper
# container can't read mounts there without an explicit chown that
# requires sudo on macOS). Cleaned up unconditionally on exit.
REPO_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
DRILL_DIR="${REPO_ROOT}/backups/.drill-$$-$(date +%s)"
mkdir -p "$DRILL_DIR"

echo "===================================================================="
echo "Neo4j restore drill"
echo "  source:           ${GCS_BUCKET}/${GCS_OBJECT}"
echo "  sandbox volume:   ${SANDBOX_VOLUME}"
echo "  sandbox container:${SANDBOX_CONTAINER}"
echo "  sandbox ports:    http ${SANDBOX_HTTP_PORT} / bolt ${SANDBOX_BOLT_PORT}"
echo "  drill dir:        ${DRILL_DIR}"
echo "  keep on exit:     ${KEEP_SANDBOX}"
echo "===================================================================="

# ── Cleanup function (runs on every exit unless --keep)
cleanup() {
    rc=$?
    echo ""
    if [ "$KEEP_SANDBOX" = true ] && [ $rc -eq 0 ]; then
        echo "=== Sandbox preserved (--keep) ==="
        echo "  container: docker exec -it ${SANDBOX_CONTAINER} cypher-shell -u neo4j -p ${DRILL_PASSWORD}"
        echo "  bolt:      bolt://localhost:${SANDBOX_BOLT_PORT}"
        echo "  to clean up later: docker stop ${SANDBOX_CONTAINER} && docker rm ${SANDBOX_CONTAINER} && docker volume rm ${SANDBOX_VOLUME}"
        echo "  drill PASSED"
        return
    fi
    echo "=== Cleanup ==="
    docker stop "${SANDBOX_CONTAINER}" >/dev/null 2>&1 || true
    docker rm "${SANDBOX_CONTAINER}" >/dev/null 2>&1 || true
    docker volume rm "${SANDBOX_VOLUME}" >/dev/null 2>&1 || true
    rm -rf "${DRILL_DIR}"
    if [ $rc -eq 0 ]; then
        echo "  drill PASSED — backup is restorable end-to-end"
    else
        echo "  drill FAILED (exit code $rc) — investigate"
    fi
}
trap cleanup EXIT

# ── 1. Pull the dump
echo ""
echo "=== 1. Pull dump from GCS ==="
gsutil cp "${GCS_BUCKET}/${GCS_OBJECT}" "${DRILL_DIR}/neo4j.dump"
ls -lh "${DRILL_DIR}/neo4j.dump"

# ── 2. Permissions: Docker Desktop's bind-mount user-mapping handles
# this for paths in the user's home; on a Linux VM we'd chown to 7474.
# Try chown but don't fail if it errors (macOS without passwordless sudo).
chown -R ${NEO4J_CONTAINER_UID}:${NEO4J_CONTAINER_UID} "${DRILL_DIR}" 2>/dev/null \
    || sudo -n chown -R ${NEO4J_CONTAINER_UID}:${NEO4J_CONTAINER_UID} "${DRILL_DIR}" 2>/dev/null \
    || true  # Docker Desktop user-mapping may make this unnecessary

# ── 3. Pre-clean any leftover sandbox from a previous failed run
echo ""
echo "=== 2. Reset sandbox volume + container ==="
docker stop "${SANDBOX_CONTAINER}" >/dev/null 2>&1 || true
docker rm "${SANDBOX_CONTAINER}" >/dev/null 2>&1 || true
docker volume rm "${SANDBOX_VOLUME}" >/dev/null 2>&1 || true
docker volume create "${SANDBOX_VOLUME}" >/dev/null

# ── 4. Load the dump into the sandbox volume
echo ""
echo "=== 3. Load dump into sandbox volume ==="
docker run --rm \
    -v "${SANDBOX_VOLUME}:/data" \
    -v "${DRILL_DIR}:/in" \
    neo4j:5.18-community \
    neo4j-admin database load neo4j \
        --from-path=/in --overwrite-destination=true

# ── 5. Spin up sandbox neo4j on alternate ports
echo ""
echo "=== 4. Start sandbox neo4j (ports ${SANDBOX_HTTP_PORT}/${SANDBOX_BOLT_PORT}) ==="
docker run -d \
    --name "${SANDBOX_CONTAINER}" \
    -v "${SANDBOX_VOLUME}:/data" \
    -e "NEO4J_AUTH=neo4j/${DRILL_PASSWORD}" \
    -p "${SANDBOX_HTTP_PORT}:7474" \
    -p "${SANDBOX_BOLT_PORT}:7687" \
    neo4j:5.18-community >/dev/null

echo "Waiting for sandbox neo4j to be ready..."
ready=false
for i in $(seq 1 60); do
    if docker exec "${SANDBOX_CONTAINER}" \
            cypher-shell -u neo4j -p "${DRILL_PASSWORD}" "RETURN 1" \
            >/dev/null 2>&1; then
        echo "  ready (after ${i} polls)"
        ready=true
        break
    fi
    sleep 2
done
if [ "$ready" = false ]; then
    echo "  TIMEOUT — sandbox neo4j never came up. Container logs:"
    docker logs "${SANDBOX_CONTAINER}" 2>&1 | tail -30
    exit 1
fi

# ── 6. Verify
echo ""
echo "=== 5. Verification: node counts ==="
docker exec "${SANDBOX_CONTAINER}" \
    cypher-shell -u neo4j -p "${DRILL_PASSWORD}" --format plain \
    "MATCH (n) UNWIND labels(n) AS l RETURN l, count(*) AS c ORDER BY c DESC"

echo ""
echo "=== 6. Verification: relationship counts ==="
docker exec "${SANDBOX_CONTAINER}" \
    cypher-shell -u neo4j -p "${DRILL_PASSWORD}" --format plain \
    "MATCH ()-[r]->() RETURN type(r) AS rel, count(*) AS c ORDER BY c DESC"

echo ""
echo "=== 7. Verification: spot-check schema constraints present ==="
docker exec "${SANDBOX_CONTAINER}" \
    cypher-shell -u neo4j -p "${DRILL_PASSWORD}" --format plain \
    "SHOW CONSTRAINTS YIELD name RETURN count(*) AS n_constraints"

echo ""
echo "===================================================================="
echo "Drill complete."
echo "  Compare counts above to the source dump's manifest, your live"
echo "  neo4j, or your last-known good state. The point: the GCS dump is"
echo "  restorable end-to-end. The sandbox will be torn down on exit"
echo "  unless you used --keep."
echo "===================================================================="
