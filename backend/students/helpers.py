import re
from collections import Counter

GRADE_POINTS = {"A": 4.0, "B": 3.0, "C": 2.0, "D": 1.0, "F": 0.0}

_COURSE_NUMBER_RE = re.compile(r"(\d+)([A-Z]*)")


def course_order_key(code: str) -> tuple[int, str]:
    """Extract (number, letter_suffix) from a course code for ordering
    same-prefix courses within a student's enrollment history.

    The first digit run is the number; any immediately following capital
    letters are the suffix. Tuples compare lexicographically, so within a
    shared numeric class the suffix determines order (17A < 17B < 17C).

    Examples:
        "HIST 17B"     -> (17, "B")
        "C S 77B"      -> (77, "B")
        "ENGL C1001"   -> (1001, "")
        "PSYC C1000H"  -> (1000, "H")
        "CHEM 12AL"    -> (12, "AL")
        "ENGL 1CH"     -> (1, "CH")
        "PSYC 72R"     -> (72, "R")
        "UNKNOWN"      -> (0, "")
    """
    match = _COURSE_NUMBER_RE.search(code)
    if not match:
        return (0, "")
    return (int(match.group(1)), match.group(2))


def compute_gpa(grades: list[str]) -> float:
    graded = [GRADE_POINTS[g] for g in grades if g in GRADE_POINTS]
    if not graded:
        return 0.0
    return round(sum(graded) / len(graded), 2)


def compute_primary_focus(enrollments: list[dict]) -> str:
    completed = [e["department"] for e in enrollments if e["status"] == "Completed" and e.get("department")]
    if not completed:
        return "Undeclared"
    return Counter(completed).most_common(1)[0][0]
