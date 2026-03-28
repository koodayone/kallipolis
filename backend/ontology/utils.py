from collections import Counter

GRADE_POINTS = {"A": 4.0, "B": 3.0, "C": 2.0, "D": 1.0, "F": 0.0}


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
