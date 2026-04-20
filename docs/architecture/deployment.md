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

The atlas is built via `NEXT_STATIC_EXPORT=true npm run build` — a flag read by `atlas/next.config.ts` that enables `output: "export"` for production while keeping `next dev` in the standard server-rendered mode for local work. The build output is a pure static bundle under `atlas/out/` that Cloudflare Pages serves directly from its edge network.

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

## Backups

A cron job on the VM fires a backup script nightly at 09:15 UTC (02:15 Pacific). The script stops the Neo4j container, runs `neo4j-admin database dump` against the stopped volume via a throwaway helper container, copies the dump to a tmpfs path, restarts Neo4j, and uploads the file to `gs://kallipolis-backups-preview/neo4j-<timestamp>.dump`. The bucket has a lifecycle policy that moves objects to Nearline storage after 30 days and deletes them after 90, so backup storage cost stays bounded.

Backend downtime during a backup is approximately 30 seconds (the Neo4j stop/dump/start window). The backend container stays up but returns errors on queries during that window; in the preview's low-traffic reality, this is acceptable. For higher-availability operation, the backup would shift to an online dump via the enterprise Neo4j feature, or the deployment would move to managed Neo4j Aura.

## Deploy loop

Changes flow through `git push` to `main`. Two different paths from there:

- **Atlas.** Cloudflare Pages watches the repo and auto-deploys on push. Build command is `npm ci && npm run build` under `atlas/`; output directory is `out`. The production environment variables `NEXT_STATIC_EXPORT=true`, `NEXT_PUBLIC_AUTH_ENABLED=false`, and `NEXT_PUBLIC_API_URL=https://api.kallipolis.us` are set in the Pages project settings and baked into the client bundle at build time.

- **Backend.** Manual SSH + rebuild: `gcloud compute ssh kallipolis-api --zone=us-central1-a --tunnel-through-iap` followed by `cd /opt/kallipolis && git pull --rebase && docker compose up -d --build backend`. The `--build` flag rebuilds the backend image against the current `backend/requirements.txt` and `backend/Dockerfile`; `docker compose` swaps the container without restarting Neo4j.

This asymmetry is intentional. The atlas is a static bundle — safe to auto-deploy on every push. The backend carries session state in Docker volumes and memory-resident Neo4j driver pools; a manual step ensures no unintended restart mid-request.

## Data refresh

The Neo4j graph on the VM is a snapshot of the local development graph. When the local graph evolves — new colleges onboarded, pipeline methodology updated, employer data re-validated — the production graph is refreshed via dump/load, not by re-running the pipeline against production:

1. Local: `docker compose stop neo4j && docker run --rm -v kallipolis_neo4j_data:/data neo4j:5.18-community neo4j-admin database dump neo4j --to-path=/data/dumps --overwrite-destination=true`, then extract the dump file from the volume.
2. Transfer: `gcloud compute scp --zone=us-central1-a --tunnel-through-iap neo4j.dump kallipolis-api:/tmp/`.
3. VM: `docker compose stop neo4j`, copy the dump into the volume via a helper container, `neo4j-admin database load neo4j --from-path=/data/dumps --overwrite-destination=true`, `docker compose up -d`.
4. Verify node and relationship counts match the local source.

Preview carries no user-generated data, so any time is a valid maintenance window.

## Preview-mode posture

The atlas deploys with authentication disabled. The root route renders the State Atlas directly; no login page exists. Save actions on the partnership and SWP flows are disabled with a tooltip directing prospects to contact for pilot activation. Seeded partnerships and SWP artifacts — three curated partnerships per college and one SWP project per college, committed as typed TypeScript modules at `atlas/preview/seededPartnerships.ts` and `atlas/preview/seededSwpProjects.ts` — back the Manage Mode view so visitors can see the full artifact shape without generating anything themselves. Live generation flows still work: any visitor can invoke the streaming partnership proposal endpoint and watch a proposal materialize against real data.

This posture is appropriate for the current stage. Authentication, server-side persistence, and per-user state will return when the first pilot signs and the product takes on real institutional users. The code path for those features is intentionally present in skeleton form (the `SessionDraftsProvider` context, the `NEXT_PUBLIC_AUTH_ENABLED` flag) so activation is additive rather than a refactor.

## Cost envelope

Steady-state fixed cost runs around $19/mo: $17 for the VM under the GCP sustained-use discount, $1–2 for persistent disk, and pennies for Cloud Storage. The $300 GCP trial credit covers the first 90 days entirely. LLM usage is the variable component — roughly $0.05–0.25 per generated partnership and $0.15–0.30 per generated SWP project, bounded in practice by the volume of prospect engagement during the preview window. Cloudflare Pages is on its free tier for static hosting.

## Where to go next

- [System Overview](./system-overview.md) — The four components and how they relate in memory, not in deployment
- [Graph Model](./graph-model.md) — What Neo4j holds that this deployment is built around
- [AI Integration](./ai-integration.md) — The LLM calls that the backend depends on
