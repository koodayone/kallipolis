"""Pytest bootstrap — fail fast, with an actionable message, on unsupported Python.

The backend uses PEP-604 unions (``int | None``) as runtime annotations (e.g.
``ontology/timing.py``), which raise a cryptic ``TypeError: unsupported operand``
at import/collection on Python < 3.10. Guard here so a developer on the system
``python3`` (often 3.9) sees a clear instruction instead of that traceback.

CI pins Python 3.11 (uv, ``.github/workflows/unit-tests.yml``); run locally with
``make test`` or ``python3.11 -m pytest``.
"""
import sys

if sys.version_info < (3, 10):
    raise SystemExit(
        f"\nKallipolis backend requires Python >= 3.10 (it uses PEP-604 `int | None` "
        f"annotations).\nYou are on Python {sys.version.split()[0]}. "
        f"Run `make test` (repo root) or `python3.11 -m pytest`.\n"
    )
