"""Shared test setup. Adds the audit's root directory to sys.path so tests
can import `checks.*` and `lib.*` directly.
"""

import sys
from pathlib import Path

# tools/docs-audit/tests/conftest.py → tools/docs-audit/
AUDIT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(AUDIT_ROOT))
