# Local Neo4j snapshots

Directory holds local Neo4j dump files + manifests describing the graph
state at snapshot time. Files are gitignored — push to GCS
(`gs://kallipolis-backups-preview/`) for offsite redundancy. See
`docs/architecture/deployment.md` § Data lifecycle for the operator
playbook (snapshot, restore, push to prod, recovery).

Filename convention: `neo4j-<UTC-timestamp>--<git-sha>.dump` plus
`neo4j-<UTC-timestamp>--<git-sha>.manifest.json`.
