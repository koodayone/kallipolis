"""Format audit results for output."""

from typing import List

from checks.base import CheckResult, Status


class HumanReporter:
    """Format audit results for terminal display.

    Produces a human-readable report with one block per check, followed
    by a summary line indicating overall pass/fail status.
    """

    PASS_GLYPH = "✓"
    FAIL_GLYPH = "✗"
    SKIP_GLYPH = "⊘"

    def report(self, results: List[CheckResult]) -> None:
        passed = [r for r in results if r.status == Status.PASS]
        failed = [r for r in results if r.status == Status.FAIL]
        skipped = [r for r in results if r.status == Status.SKIP]

        print()
        print("=" * 70)
        print("Kallipolis Documentation Audit")
        print("=" * 70)
        print()

        for result in results:
            self._print_result(result)
            print()

        # Summary
        print("=" * 70)
        if failed:
            print(
                f"FAIL: {len(passed)} passed, "
                f"{len(failed)} failed, "
                f"{len(skipped)} skipped"
            )
        else:
            total = len(passed) + len(skipped)
            if skipped:
                print(
                    f"PASS: {len(passed)} of {total} checks passed "
                    f"({len(skipped)} skipped)"
                )
            else:
                print(f"PASS: all {len(passed)} checks passed")
        print("=" * 70)
        print()

    def _print_result(self, result: CheckResult) -> None:
        if result.status == Status.PASS:
            count_suffix = (
                f" ({result.items_checked} items checked)"
                if result.items_checked
                else ""
            )
            print(f"{self.PASS_GLYPH} {result.check}{count_suffix}")
            return

        if result.status == Status.SKIP:
            print(f"{self.SKIP_GLYPH} {result.check} (skipped)")
            if result.details:
                for line in result.details.split("\n"):
                    print(f"  {line}")
            return

        # FAIL
        print(f"{self.FAIL_GLYPH} {result.check}")
        if result.details:
            for line in result.details.split("\n"):
                print(f"  {line}")
        if result.resolution:
            print()
            print(f"  Resolution: {result.resolution}")
