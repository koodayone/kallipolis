"""Base classes and result types for audit checks."""

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Optional


class Status(Enum):
    """Outcome of a single check."""

    PASS = "pass"
    FAIL = "fail"
    SKIP = "skip"


@dataclass
class CheckResult:
    """Structured result of running a check.

    A passing check has status=PASS and may report `items_checked` to give
    a sense of how much work was done. A failing check has status=FAIL,
    a `details` block describing the discrepancy, and a `resolution`
    explaining how to fix it. A skipped check has status=SKIP, used when
    the check cannot run (e.g., a required directory is missing).
    """

    check: str
    status: Status
    details: Optional[str] = None
    resolution: Optional[str] = None
    items_checked: int = 0


class Check:
    """Base class for audit checks.

    Each check is a small focused module that targets one class of
    documentation claim. Subclasses set `name` and `description` and
    implement `run(repo_root)`.
    """

    name: str = ""
    description: str = ""

    def run(self, repo_root: Path) -> CheckResult:
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement run(repo_root)"
        )
