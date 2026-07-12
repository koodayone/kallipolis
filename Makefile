# Kallipolis dev loop. CI pins Python 3.11 (uv); mirror it locally so the system
# python3 (often 3.9, which crashes on the backend's PEP-604 annotations) isn't used.
# Prefers python3.11, falls back to python3 (the conftest guard then errors clearly).
PY := $(shell command -v python3.11 2>/dev/null || command -v python3)

.PHONY: help test docs-audit evals
help:  ## List targets
	@grep -E '^[a-z-]+:.*##' $(MAKEFILE_LIST) | sed 's/:.*## /\t/'

test:  ## Backend unit suite (graph tests skip without a reachable Neo4j)
	cd backend && $(PY) -m pytest

docs-audit:  ## Deterministic documentation audit (blocks merge)
	$(PY) tools/docs-audit/audit.py

# The single required correctness gate (Phase 1, WIP): the deterministic audit +
# the graph-backed invariants. Graph invariants need a reachable Neo4j (seeded in
# CI; locally: a docker-compose.override.yml or socat forward to the compose db).
evals: docs-audit test  ## Full eval gate (audit + tests)
