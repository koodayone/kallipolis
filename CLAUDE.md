# Kallipolis

## Orientation

If you need broad context on the project, read `docs/README.md` — it is an annotated index of every doc in the documentation tree with a one-line description of each.

## Documentation work

Before creating or modifying any file under `docs/`, read `docs/conventions.md`. It is the contract for voice, altitude, structural patterns, and the structured forms (file paths, schema tables, API tables, model names, numerical constants, relationship tables) the documentation audit verifies.

After any doc change, run the audit:

```bash
python3 tools/docs-audit/audit.py
```

A failing audit blocks merge to `main`. Resolve failures before considering the change complete.
