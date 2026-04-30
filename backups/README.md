# Local Neo4j snapshots

Directory holds local Neo4j dump files + manifests describing the
graph state at snapshot time. All artifacts here are gitignored —
push to GCS at `gs://kallipolis-backups-preview/local/` for offsite
redundancy.

See `docs/architecture/deployment.md` § Data lifecycle for the
operator playbook (snapshot, restore, push to prod, recovery) and
the manifest schema.

Filename convention: `neo4j-<UTC-timestamp>--<git-sha>.dump` plus
`neo4j-<UTC-timestamp>--<git-sha>.manifest.json`.
