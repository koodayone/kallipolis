#!/usr/bin/env bash
# Neo4j backup script — runs nightly via cron, also runnable manually.
#
# Stops the kallipolis-neo4j-1 container, dumps the database via a
# throwaway helper container, restarts neo4j, uploads the dump to
# GCS at gs://kallipolis-backups-preview/neo4j-<UTC-timestamp>.dump,
# and removes the local copy. Total downtime is approximately 30
# seconds (the neo4j stop / dump / start window).
#
# Lifecycle: GCS bucket has a 30-day-nearline / 90-day-delete
# lifecycle policy, so this script does not need to manage rotation.
#
# Manual invocation: sudo /opt/kallipolis/scripts/neo4j-backup.sh
# Cron invocation: 15 9 * * *  /opt/kallipolis/scripts/neo4j-backup.sh
#
# Failure handling: if any step fails, an EXIT trap ensures neo4j
# is restarted before exiting (prod doesn't get left stopped on
# script failure). The trap also logs FAILED to make non-success
# obvious in the log.

set -euo pipefail

BACKUP_DIR=/opt/kallipolis/backups
GCS_BUCKET=gs://kallipolis-backups-preview
COMPOSE_DIR=/opt/kallipolis
NEO4J_CONTAINER_UID=7474
TIMESTAMP=$(date -u +%Y%m%dT%H%M%SZ)
DUMP_NAME="neo4j-${TIMESTAMP}.dump"

LOG_DIR=/var/log/kallipolis
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/neo4j-backup-$(date -u +%Y-%m).log"
exec >> "$LOG_FILE" 2>&1

echo "===================================================================="
echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) backup starting (pid=$$)"
echo "  dump: ${DUMP_NAME}"
echo "  gcs:  ${GCS_BUCKET}/${DUMP_NAME}"
echo "===================================================================="

# Ensure backup dir exists with ownership the neo4j helper container
# can write to (the container's process maps to UID 7474 on the host;
# without this chown, the dump fails with AccessDeniedException).
mkdir -p "$BACKUP_DIR"
chown "${NEO4J_CONTAINER_UID}:${NEO4J_CONTAINER_UID}" "$BACKUP_DIR"

# EXIT trap: always try to bring neo4j back up, even on script failure.
# Prod cannot tolerate being left in a stopped state if the dump errors.
on_exit() {
    rc=$?
    if [ $rc -ne 0 ]; then
        echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) FAILED with exit code $rc — recovering"
    fi
    cd "$COMPOSE_DIR"
    docker compose up -d neo4j || echo "WARN: docker compose up failed in trap"
    if [ $rc -ne 0 ]; then
        echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) FAILED — neo4j restart attempted; check container state manually"
    fi
}
trap on_exit EXIT

# 1. Stop neo4j (downtime starts)
cd "$COMPOSE_DIR"
echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) stopping neo4j"
docker compose stop neo4j

# 2. Dump via helper container (offline; requires neo4j stopped)
echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) dumping"
docker run --rm \
    -v kallipolis_neo4j_data:/data \
    -v "${BACKUP_DIR}":/out \
    neo4j:5.18-community \
    neo4j-admin database dump neo4j --to-path=/out --overwrite-destination=true

# 3. Rename to timestamped name. The dump command writes <dbname>.dump
# (i.e. neo4j.dump); we want a timestamped name in GCS so backups don't
# overwrite each other.
mv "${BACKUP_DIR}/neo4j.dump" "${BACKUP_DIR}/${DUMP_NAME}"

# 4. Restart neo4j (downtime ends; trap will also do this on any exit
# but explicit success path keeps the log readable)
echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) restarting neo4j"
docker compose up -d neo4j

# 5. Upload to GCS (the VM's service account has bucket write access)
echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) uploading to GCS"
gsutil cp "${BACKUP_DIR}/${DUMP_NAME}" "${GCS_BUCKET}/${DUMP_NAME}"

# 6. Remove local copy — GCS is the durable store; keeping local copies
# would fill the VM's 40GB disk over time (each dump is ~525MB).
rm -f "${BACKUP_DIR}/${DUMP_NAME}"

echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) backup complete"
