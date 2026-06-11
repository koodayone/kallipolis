from pydantic import BaseModel


class StudentSummary(BaseModel):
    uuid: str
    primary_focus: str
    courses_completed: int
    gpa: float


class StudentSummaryPage(BaseModel):
    """Response shape for the students-by-college endpoint.

    Retained for the non-PII placeholder endpoint
    (``students.api.get_students``), which always returns an empty page —
    the ontology no longer carries individual Student records. Kept as a
    typed page (rather than a bare list) so the response contract is
    stable if an aggregated, non-PII students surface is added later.
    """
    students: list[StudentSummary]
    total_count: int
    has_more: bool
