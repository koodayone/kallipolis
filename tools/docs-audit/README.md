# Kallipolis Documentation Audit

A deterministic verification tool that catches drift between the Kallipolis documentation and the codebase. The audit reads code-grounded claims from the docs (in the structured forms specified by [`docs/conventions.md`](../../docs/conventions.md)) and verifies each one against the actual code.

## What this is for

The documentation in `docs/` makes many claims about what the code does — file paths, schema structures, API endpoints, model names, numerical constants. As the code changes, these claims can drift out of sync silently. The audit prevents that drift from accumulating by checking the documentation against the code on every commit.

The audit is the trust foundation that makes the documentation safe to load as runtime context for AI agents. When the audit passes, the documentation is verified to be consistent with the code, which means an agent loading docs as context is loading verified information.

## Running the audit

From the repository root:

```bash
python tools/docs-audit/audit.py
```

This runs all checks and reports the results. Exit code is `0` if all checks pass, `1` if any check fails, `2` if the invocation itself was invalid.

To run a single check:

```bash
python tools/docs-audit/audit.py --check file_paths
```

## Running the audit's own tests

The audit is itself a piece of code that needs its own tests. To run them:

```bash
pip install pytest
pytest tools/docs-audit/tests/
```

## Architecture

The audit is built around small focused checks. Each check is a single file in `checks/` with a clear responsibility: it knows where its target claims live in the documentation, how to extract them, and how to verify them against the code.

```
tools/docs-audit/
├── audit.py           # Entry point
├── checks/            # Individual check modules
│   ├── base.py        # Check base class, CheckResult, Status
│   └── file_paths.py  # File path references resolve
├── lib/
│   └── reporter.py    # Output formatting
└── tests/             # Audit's own test suite
```

## Adding a new check

1. Create a new file in `checks/` (e.g., `checks/api_endpoints.py`)
2. Subclass `Check` from `checks.base`
3. Implement the `run(repo_root)` method, returning a `CheckResult`
4. Register the check in `audit.py` by adding it to `ALL_CHECKS`
5. Add unit tests in `tests/test_<check_name>.py`
6. Verify the check passes against the current repo, then commit

The conventions the audit relies on are codified in [`docs/conventions.md`](../../docs/conventions.md). When you add a new check, also document the convention it relies on in that file.

## Design principles

- **Deterministic.** No LLM calls. Every check is regex, AST parsing, or filesystem operations. Determinism is what makes the audit trustworthy as testing infrastructure.
- **Conservative.** Each check should fail only when it is genuinely confident the documentation and the code disagree. False positives destroy trust faster than false negatives.
- **Actionable.** Failure messages name the file, the line, the claim, the ground truth, and a suggested resolution. Contributors should not have to debug the audit itself.
- **Small.** Each check is one focused module. There is no central framework. Adding a new check should take an afternoon, not a week.

See the design plan in the conversation history for the longer rationale.
