"""Students API — non-PII placeholder.

The ontology no longer carries individual Student nodes or enrollment
edges (removed in the non-PII migration). The ``students`` feature unit
is retained as a navigational surface — the atlas Students node and the
``/students`` route still resolve — but there is no per-student data to
serve. Program-level enrollment is exposed as aggregates per TOP6 via
the Partnerships surface.

The list endpoint returns an empty page (rather than 404) so the atlas
Students page renders its placeholder without an error state.
"""

from fastapi import APIRouter, Query

from students.models import StudentSummaryPage

router = APIRouter()


@router.get("/", response_model=StudentSummaryPage)
def get_students(
    college: str,
    limit: int = Query(100, ge=1, le=5000),
    offset: int = Query(0, ge=0),
):
    """No per-student data in the non-PII ontology; returns an empty page.

    Kept (rather than removed) so the atlas Students surface and any
    cached clients resolve to an empty result instead of a 404.
    """
    return StudentSummaryPage(students=[], total_count=0, has_more=False)
