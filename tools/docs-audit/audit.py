"""Kallipolis documentation audit — entry point.

Runs all registered checks against the repository and reports results.
Exit code is 0 if all checks pass, 1 if any check fails, 2 if the
invocation was invalid (unknown check name, etc.).

Run from the repository root:

    python tools/docs-audit/audit.py            # all checks
    python tools/docs-audit/audit.py --check file_paths    # one check
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Allow direct execution: add this script's directory to sys.path so the
# `checks` and `lib` packages can be imported as top-level modules.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from checks.base import Check, Status  # noqa: E402
from checks.file_paths import FilePathsCheck  # noqa: E402
from checks.markdown_links import MarkdownLinksCheck  # noqa: E402
from checks.api_endpoints import APIEndpointsCheck  # noqa: E402
from checks.model_names import ModelNamesCheck  # noqa: E402
from lib.reporter import HumanReporter  # noqa: E402


# Registry of all checks. Add new checks here as they are built.
ALL_CHECKS: list[Check] = [
    FilePathsCheck(),
    MarkdownLinksCheck(),
    APIEndpointsCheck(),
    ModelNamesCheck(),
]


def find_repo_root() -> Path:
    """Find the repository root by walking up from this script's location."""
    current = Path(__file__).resolve().parent
    while current != current.parent:
        if (current / ".git").exists():
            return current
        current = current.parent
    raise RuntimeError(
        "Could not find repository root (no .git directory found in any parent)"
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Kallipolis documentation audit",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--check",
        type=str,
        default=None,
        help="Run only a specific check by name",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List available checks and exit",
    )
    args = parser.parse_args()

    if args.list:
        print("Available checks:")
        for check in ALL_CHECKS:
            print(f"  {check.name}: {check.description}")
        return 0

    repo_root = find_repo_root()

    # Filter to a single check if requested
    checks_to_run: list[Check] = list(ALL_CHECKS)
    if args.check:
        checks_to_run = [c for c in ALL_CHECKS if c.name == args.check]
        if not checks_to_run:
            available = ", ".join(c.name for c in ALL_CHECKS)
            print(f"Unknown check: {args.check}", file=sys.stderr)
            print(f"Available: {available}", file=sys.stderr)
            return 2

    # Run all checks
    results = []
    for check in checks_to_run:
        result = check.run(repo_root)
        results.append(result)

    # Report
    reporter = HumanReporter()
    reporter.report(results)

    # Exit code reflects the worst outcome
    if any(r.status == Status.FAIL for r in results):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
