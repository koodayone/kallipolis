# Deployment

Kallipolis runs in a deliberately simple production shape: a static atlas on Cloudflare Pages, a single Compute Engine VM hosting the FastAPI backend and Neo4j, and the landing page on Cloudflare Pages unchanged. This document describes the shape that exists today — the preview deployment that serves the pre-pilot GTM motion — along with the operational primitives that keep it running: TLS termination, secrets, backups, and the deploy loop.

## The essence

The deployment is an intentional minimum. Three hosts, one graph, one VM. The atlas ships as static HTML/JS/CSS with no server runtime. The backend sits behind Caddy for automatic TLS. Secrets live in GCP Secret Manager and are materialized into a local `.env` at boot. Nightly `neo4j-admin database dump` backups write to Cloud Storage with a 30-day nearline / 90-day delete lifecycle. Total steady-state cost is around $19/mo plus LLM variable spend. The shape is designed to migrate cleanly to managed services when pilot volume makes the current shape a constraint rather than a virtue.

## Production topology

| Host | Purpose | Where it runs |
|---|---|---|
| `https://kallipolis.us` | Landing page | Cloudflare Pages |
| `https://app.kallipolis.us` | Atlas preview (static Next.js export) | Cloudflare Pages |
| `https://api.kallipolis.us` | FastAPI backend + Neo4j | GCP Compute Engine VM |

The atlas is built via `NEXT_STATIC_EXPORT=true npm run build` — a flag read by `atlas/next.config.ts` that enables `output: "export"` for production while keeping `next dev` in the standard server-rendered mode for local work. The build emits a pure static bundle to an `out/` directory under `atlas/` that Cloudflare Pages serves directly from its edge network.

The backend runs under Docker Compose on the VM: `docker-compose.yml` at the repository root defines two services, `neo4j` (pinned to `neo4j:5.18-community`) and `backend` (built from `backend/Dockerfile`). Both have `restart: unless-stopped` so a VM reboot brings them back up; the backend binds to `127.0.0.1:8000` so only Caddy on the same host can reach it, never the public internet directly.

## VM specifics

The VM is a single `e2-medium` Compute Engine instance in `us-central1-a` with a static external IP and a 40 GB standard persistent disk. DNS for `api.kallipolis.us` points at the static IP directly through Cloudflare DNS with the proxy disabled, so Caddy on the VM terminates TLS rather than Cloudflare's edge. Two systemd units — `kallipolis-env.service` and `kallipolis.service` — enforce boot-time ordering: the first materializes `/opt/kallipolis/.env` from Secret Manager, the second runs `docker compose up -d` against the repo at `/opt/kallipolis/`. SSH is through IAP only; no public port 22.

## TLS termination and reverse proxy

Caddy 2.11 on the VM reverse-proxies `api.kallipolis.us` to `http://127.0.0.1:8000` and provisions Let's Encrypt certificates automatically via the HTTP-01 challenge on first request. The Caddyfile is three lines of directive plus a global `email` block at `/etc/caddy/Caddyfile`. Cert renewal happens on Caddy's own schedule without intervention.

The `reverse_proxy` directive sets `X-Forwarded-Proto: https` on upstream requests, and uvicorn is launched with `--proxy-headers --forwarded-allow-ips=*` so FastAPI's automatic trailing-slash redirects use the correct scheme. Without that flag, uvicorn constructs redirect URLs with `http://` (the scheme it directly sees) and the browser refuses to follow the scheme downgrade from an HTTPS page.

## Secrets handling

Four secrets live in GCP Secret Manager, scoped to the `kallipolis-preview` project:

| Secret | Role |
|---|---|
| `NEO4J_PASSWORD` | Neo4j bolt credentials |
| `ANTHROPIC_API_KEY` | Claude access for NL→Cypher and narrative generation |
| `GEMINI_API_KEY` | Gemini access for ETL pipeline extractions |
| `CORS_ORIGINS` | Comma-separated origins the FastAPI CORS middleware allows; production value is `https://app.kallipolis.us` |

The VM's service account (`kallipolis-vm@kallipolis-preview.iam.gserviceaccount.com`) has `roles/secretmanager.secretAccessor` scoped to these four secrets only. On boot, the `kallipolis-env.service` systemd unit runs a secrets-loader script on the VM that calls `gcloud secrets versions access latest` for each secret and writes the values to a local `.env` file with mode 600. The backend's Docker Compose reads that `.env` via Compose's standard environment-variable interpolation — no secret values are baked into the image or committed to the repository.

Secret rotation is a two-step: add a new version in Secret Manager, then `systemctl restart kallipolis-env.service kallipolis.service` on the VM.

## Deploy loop

Changes flow through `git push` to `main`. Two different paths from there:

- **Atlas.** Cloudflare Pages watches the repo and auto-deploys on push. Build command is `npm ci && npm run build` under `atlas/`; output directory is `out`. The production environment variables `NEXT_STATIC_EXPORT=true`, `NEXT_PUBLIC_AUTH_ENABLED=false`, and `NEXT_PUBLIC_API_URL=https://api.kallipolis.us` are set in the Pages project settings and baked into the client bundle at build time.

- **Backend.** Manual SSH + rebuild: `gcloud compute ssh kallipolis-api --zone=us-central1-a --tunnel-through-iap` followed by `cd /opt/kallipolis && git pull --rebase && docker compose up -d --build backend`. The `--build` flag rebuilds the backend image against the current `backend/requirements.txt` and `backend/Dockerfile`; `docker compose` swaps the container without restarting Neo4j.

This asymmetry is intentional. The atlas is a static bundle — safe to auto-deploy on every push. The backend carries session state in Docker volumes and memory-resident Neo4j driver pools; a manual step ensures no unintended restart mid-request.

## Data lifecycle

The graph is the most expensive artifact this project produces. Pipeline runs cost real LLM dollars and produce hand-curated state that cannot be cheaply re-derived. This section is the operator handbook for that artifact: where it lives, how to snapshot it, how to restore it, how to migrate it to prod, and what to do when something is wrong. Designed to be readable end-to-end by a fresh operator (or another Claude session) and used as a copy-pasteable runbook.

### Persistence model

| Layer | Data location | Survives | Does NOT survive |
|---|---|---|---|
| Local Docker volume | Named volume `kallipolis_neo4j_data` at `/var/lib/docker/volumes/kallipolis_neo4j_data/_data` | Container restarts, `docker compose down`, daemon restarts | `docker compose down -v`, `docker volume rm`, Docker Desktop reset, disk failure |
| Local snapshots | Files under `backups/` in the repo (gitignored) | Anything that doesn't `rm` the directory | `rm -rf backups/`, `git clean -fdx` from repo root, disk failure |
| Local snapshots offsite | `gs://kallipolis-backups-preview/local/` (uploaded ad-hoc) | Anything that doesn't delete the GCS object | Manual deletion, lifecycle expiry (30d nearline / 90d delete) |
| Prod Docker volume | Named volume `kallipolis_neo4j_data` on the VM | VM reboots, container restarts, `docker compose down` | `docker compose down -v`, VM destroy |
| Prod snapshots offsite | `gs://kallipolis-backups-preview/neo4j-<timestamp>.dump` from the nightly cron | Anything that doesn't delete the GCS object | Manual deletion, lifecycle expiry (30d nearline / 90d delete) |

Two important asymmetries:

1. **Local has no automated backup.** Prod has the nightly cron uploading to GCS. Local depends on operator discipline — every meaningful pipeline run should produce a fresh snapshot via the procedure below.
2. **Snapshots are versioned by git SHA.** The dump file alone is opaque; the manifest written alongside it captures the git SHA of the code that produced the graph, the node/relationship counts at snapshot time, the dump SHA-256 checksum, and the neo4j version. A snapshot without its manifest is significantly less useful — always keep the pair together.

### Nightly prod cron

A root crontab entry on the VM fires the backup script at 09:15 UTC nightly. The script — `scripts/neo4j-backup.sh` in this repo, deployed to /opt/kallipolis/scripts/ via the standard git pull on the VM — stops the Neo4j container, dumps via a throwaway helper container into /opt/kallipolis/backups/, restarts Neo4j, and uploads the dump to `gs://kallipolis-backups-preview/neo4j-<UTC-timestamp>.dump`. The local copy is removed after a successful upload to keep the VM's 40 GB disk from filling. The GCS bucket has a 30-day nearline / 90-day delete lifecycle policy.

Logs land in `/var/log/kallipolis/neo4j-backup-<YYYY-MM>.log`. Failure handling: an EXIT trap in the script ensures Neo4j is brought back up even on dump failure, and writes a `FAILED` line to the log so non-success is obvious on next inspection.

Backend downtime per run is approximately 30 seconds — acceptable in the preview's low-traffic reality. For higher-availability operation, the backup would shift to an online dump via the enterprise Neo4j feature, or the deployment would move to managed Neo4j Aura.

To install or rotate the cron entry on the VM:

```bash
gcloud compute ssh kallipolis-api --zone=us-central1-a --tunnel-through-iap
# On the VM:
cd /opt/kallipolis && git pull --rebase   # ensures scripts/neo4j-backup.sh is current
sudo chmod +x /opt/kallipolis/scripts/neo4j-backup.sh
echo '15 9 * * * /opt/kallipolis/scripts/neo4j-backup.sh' | sudo crontab -
sudo crontab -l    # verify
sudo /opt/kallipolis/scripts/neo4j-backup.sh    # manual test run; verifies end-to-end
gsutil ls -l gs://kallipolis-backups-preview/ | tail -5    # confirm a fresh object landed
```

### Take a local snapshot

When to run this: after any pipeline run that meaningfully changes the graph; before any prod migration; before any risky local operation that might corrupt data; on any cadence that matches "I cannot afford to lose this" — at minimum weekly during active development.

Downtime: ~5–10 seconds (neo4j stop + dump + restart). Backend on `localhost:8000` returns errors during that window.

```bash
cd /Users/dayonekoo/Desktop/code/kallipolis

# 1. Establish the snapshot identity
TS=$(date -u +%Y-%m-%dT%H-%MZ)
SHA=$(git rev-parse --short HEAD)
DUMP_NAME="neo4j-${TS}--${SHA}.dump"
MANIFEST_NAME="neo4j-${TS}--${SHA}.manifest.json"
mkdir -p backups

# 2. Ensure the destination is writable by the helper container's
#    process. The neo4j image's process maps to UID 7474 on the host;
#    without this chown the dump fails with AccessDeniedException.
sudo chown 7474:7474 backups 2>/dev/null || chown 7474:7474 backups

# 3. Stop neo4j (downtime starts here)
docker compose stop neo4j

# 4. Offline dump via helper container, writing directly to the host backups dir
docker run --rm \
  -v kallipolis_neo4j_data:/data \
  -v "$(pwd)/backups":/out \
  neo4j:5.18-community \
  neo4j-admin database dump neo4j --to-path=/out --overwrite-destination=true

# 5. Rename to the versioned filename
mv backups/neo4j.dump "backups/${DUMP_NAME}"

# 6. Restart neo4j (downtime ends)
docker compose up -d neo4j
```

The dump file is now in `backups/`. Next, write the manifest. The manifest format is JSON with these fields:

| Field | Source | Why it matters |
|---|---|---|
| `schema_version` | Literal `1` for now | Lets future format changes be detected |
| `snapshot_timestamp_utc` | `date -u +%Y-%m-%dT%H:%MZ` | Identifies when this state existed |
| `dump_file` | The `.dump` filename | Pairs the manifest to its dump |
| `dump_size_bytes` | `stat -f%z <dump>` | Sanity check on file integrity |
| `dump_sha256` | `shasum -a 256 <dump>` | Detects bit-rot or transfer corruption |
| `neo4j_version` | Image tag (`5.18-community` → `5.18.x`) | Restoring requires same major version |
| `neo4j_image` | Literal `neo4j:5.18-community` | Pin for restore |
| `git_sha` | `git rev-parse HEAD` | Code that produced this graph |
| `git_branch` | `git branch --show-current` | Branch context |
| `node_counts` | Cypher: `MATCH (n) UNWIND labels(n) AS l RETURN l, count(*)` | Lets a restore be verified by re-running the same query |
| `relationship_counts` | Cypher: `MATCH ()-[r]->() RETURN type(r), count(*)` | Same |
| `known_data_realities` | Hand-noted | Pre-existing data quirks worth flagging (e.g. courses missing top_code) |
| `created_by` | Operator name or session description | Provenance |
| `notes` | Free text | Why this snapshot exists |

After the dump completes, populate the manifest by running the queries in the table against the (just-restarted) neo4j and assembling the JSON. Verify both files are present and the dump size is plausible (graphs around the current shape produce ~500 MB dumps):

```bash
ls -lh backups/
# Expect: ~500MB *.dump file + a small *.manifest.json file
```

Optionally, push the snapshot pair to GCS for offsite redundancy:

```bash
gsutil cp "backups/${DUMP_NAME}" "backups/${MANIFEST_NAME}" \
  gs://kallipolis-backups-preview/local/
```

### Restore from a local snapshot

When to run this: local Docker volume corrupted, schema regression to investigate, want to roll back to a known-good earlier state.

The restore replaces the contents of the local `kallipolis_neo4j_data` volume with the dump's contents. Any local changes since the snapshot are lost — verify you have a fresh snapshot of current state first if you might want to recover anything.

```bash
cd /Users/dayonekoo/Desktop/code/kallipolis
DUMP_NAME=neo4j-2026-04-30T02-20Z--b8b509f.dump  # adjust to the snapshot you're restoring

# 1. Verify the dump's checksum against its manifest before loading
shasum -a 256 "backups/${DUMP_NAME}"
# Compare to dump_sha256 in the matching manifest

# 2. Stop neo4j and the backend (the load wipes the volume contents)
docker compose stop neo4j backend

# 3. Load via helper container — overwrite-destination=true wipes the existing graph
docker run --rm \
  -v kallipolis_neo4j_data:/data \
  -v "$(pwd)/backups":/in \
  neo4j:5.18-community \
  bash -c "cp /in/${DUMP_NAME} /tmp/neo4j.dump && neo4j-admin database load neo4j --from-path=/tmp --overwrite-destination=true"

# 4. Restart
docker compose up -d

# 5. Verify counts match the manifest
NEO4J_PW=$(grep '^NEO4J_PASSWORD=' .env | cut -d'=' -f2-)
docker exec kallipolis-neo4j-1 cypher-shell -u neo4j -p "$NEO4J_PW" --format plain \
  "MATCH (n) UNWIND labels(n) AS l RETURN l, count(*) AS c ORDER BY c DESC"
# Compare to node_counts in the manifest
```

### Push local → prod

When to run this: the local graph has evolved (new colleges onboarded, pipeline methodology updated, employer data re-validated) and prod should mirror it. Preview carries no user-generated data, so any time is a valid maintenance window.

Prod downtime: ~30 seconds during the load step. The backend container stays up but returns errors on queries.

The flow has six steps. Steps 1–2 are local-only and reversible. Steps 3–4 are prod read-only. Step 5 is the destructive prod write — this is the boundary where an operator should pause and confirm intent before executing.

**Step 1 — Take a fresh local snapshot.** Per the procedure above. This is both your migration source AND your local rollback point. Do not skip even if you took one yesterday.

**Step 2 — Optional: push the snapshot pair to GCS.** Per the GCS upload step in the snapshot procedure. Gives you an offsite copy of local state that does not depend on the prod migration succeeding.

**Step 3 — Verify the prod backup cron has fired recently.** Lists the GCS objects sorted by time:

```bash
gsutil ls -l gs://kallipolis-backups-preview/ | tail -10
```

If the most recent prod backup is fresh enough (within 24h), it serves as your prod rollback point. If not, take a defensive prod backup explicitly:

```bash
gcloud compute ssh kallipolis-api --zone=us-central1-a --tunnel-through-iap \
  --command='sudo /opt/kallipolis/scripts/neo4j-backup.sh'
```

(Adjust the script path if it differs on the VM. The cron's script is the source of truth for the right command.)

**Step 4 — SCP the local dump to the VM.** Note: `/tmp` on the VM is ephemeral (tmpfs). Move the dump into the data volume promptly after upload — don't let it sit in `/tmp` across a VM reboot or you'll lose it.

```bash
DUMP_NAME=neo4j-2026-04-30T02-20Z--b8b509f.dump  # adjust
gcloud compute scp --zone=us-central1-a --tunnel-through-iap \
  "backups/${DUMP_NAME}" \
  "kallipolis-api:/tmp/${DUMP_NAME}"
```

**Step 5 — Load the dump on prod.** This is the destructive step. The `--overwrite-destination=true` flag wipes the existing prod graph contents.

The load command requires the file to be named exactly `<dbname>.dump` (i.e. `neo4j.dump`), not the versioned filename — staging it in a fresh dir under that fixed name is the cleanest pattern. The destination dir also needs the neo4j-container UID (7474) as owner, same as the snapshot procedure.

```bash
gcloud compute ssh kallipolis-api --zone=us-central1-a --tunnel-through-iap
# Once on the VM:
DUMP_NAME=neo4j-2026-04-30T02-20Z--b8b509f.dump
cd /opt/kallipolis

# Stage the dump as neo4j.dump in a fresh dir owned by the container UID
sudo rm -rf /opt/kallipolis/load-staging
sudo mkdir -p /opt/kallipolis/load-staging
sudo cp "/tmp/${DUMP_NAME}" /opt/kallipolis/load-staging/neo4j.dump
sudo chown -R 7474:7474 /opt/kallipolis/load-staging

# Stop neo4j and load
sudo docker compose stop neo4j
sudo docker run --rm \
  -v kallipolis_neo4j_data:/data \
  -v /opt/kallipolis/load-staging:/in \
  neo4j:5.18-community \
  neo4j-admin database load neo4j --from-path=/in --overwrite-destination=true

# Restart and clean up staging
sudo docker compose up -d neo4j
sudo rm -rf /opt/kallipolis/load-staging
```

The dump format leaves auth alone — prod's `NEO4J_PASSWORD` survives the load, so no credential reset is needed.

**Step 6 — Verify prod counts match local.** SSH stays open; run from the VM:

```bash
NEO4J_PW=$(grep '^NEO4J_AUTH=' /opt/kallipolis/.env | cut -d'=' -f2- | cut -d'/' -f2-)
docker exec kallipolis-neo4j-1 cypher-shell -u neo4j -p "$NEO4J_PW" --format plain \
  "MATCH (n) UNWIND labels(n) AS l RETURN l, count(*) AS c ORDER BY c DESC"
```

Compare to the `node_counts` field in the local manifest. They should match exactly. Then hit `https://api.kallipolis.us/health` from your laptop — should return `{"status":"ok"}`. If both pass, the migration is complete; close the SSH session.

### Recovery scenarios

| Scenario | Symptoms | Playbook |
|---|---|---|
| Local Docker volume corrupted or accidentally `down -v`'d | `docker compose up -d` brings up an empty neo4j; backend logs show "Neo4j is empty"; API returns no data | Restore from the most recent local snapshot per § Restore. If no local snapshot exists, pull the most recent prod backup from GCS (`gsutil cp gs://kallipolis-backups-preview/neo4j-<latest>.dump backups/`) and treat it as a local snapshot to restore — note this is prod state, not necessarily your latest local state |
| Prod neo4j wedged or returning errors | `https://api.kallipolis.us/health` returns 5xx; SSH to VM shows backend in restart loop | SSH to VM. `docker compose ps` to see container state. `docker logs kallipolis-backend-1 --tail 50` and `docker logs kallipolis-neo4j-1 --tail 50` for diagnosis. If neo4j data is intact: `docker compose restart`. If neo4j data is corrupted: `gsutil ls -l gs://kallipolis-backups-preview/` to find latest backup, then run § Push local → prod steps 4–6 with the GCS dump as the source |
| Prod migration partially completed (load failed mid-flight) | Prod neo4j won't start; cypher-shell errors on connect | The `--overwrite-destination=true` flag means the prior prod state is gone. Re-run § Push local → prod step 5 with the same dump (idempotent). If that also fails, fall back to the prod-backup recovery flow in the row above |
| Snapshot file present but manifest missing | A `.dump` file in `backups/` with no matching `.manifest.json` | The dump is still loadable, but its provenance is unknown. Check `git log` for the period it was likely produced. Restore in a sandbox volume first (don't overwrite working state) and inspect counts before promoting |

### Notes

- The `backups/` directory is gitignored. Snapshots and manifests live there but never reach the repo. Push to GCS for offsite.
- `git clean -fdx` from the repo root will delete `backups/` because the `-x` flag removes ignored files. Be cautious with that command.
- The manifest format is versioned (`schema_version: 1`). If the format ever changes incompatibly, bump the version and document the migration in this section.

## Preview-mode posture

The atlas deploys with authentication disabled. The root route renders the State Atlas directly; no login page exists. Save actions on the partnership flow are disabled with a tooltip directing prospects to contact for pilot activation. Seeded partnerships — one curated partnership per featured college, committed as a typed TypeScript module at `atlas/preview/seededPartnerships.ts` — back the Manage Mode view so visitors can see the full artifact shape without generating anything themselves. Live generation flows still work: any visitor can invoke the streaming partnership proposal endpoint and watch a proposal materialize against real data.

This posture is appropriate for the current stage. Authentication, server-side persistence, and per-user state will return when the first pilot signs and the product takes on real institutional users. The code path for those features is intentionally present in skeleton form (the `SessionDraftsProvider` context, the `NEXT_PUBLIC_AUTH_ENABLED` flag) so activation is additive rather than a refactor.

## Cost envelope

Steady-state fixed cost runs around $19/mo: $17 for the VM under the GCP sustained-use discount, $1–2 for persistent disk, and pennies for Cloud Storage. The $300 GCP trial credit covers the first 90 days entirely. LLM usage is the variable component — roughly $0.05–0.25 per generated partnership and $0.15–0.30 per generated SWP project, bounded in practice by the volume of prospect engagement during the preview window. Cloudflare Pages is on its free tier for static hosting.

## Where to go next

- [System Overview](./system-overview.md) — The four components and how they relate in memory, not in deployment
- [Graph Model](./graph-model.md) — What Neo4j holds that this deployment is built around
- [AI Integration](./ai-integration.md) — The LLM calls that the backend depends on
