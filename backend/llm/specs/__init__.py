"""Per-feature query specs for the spec engine.

Each module under this package represents one analytical view's query
surface. They share a uniform shape (SpecClass / EXTRACTOR_PROMPT /
SPEC_SCHEMA / render_cypher / interpret_spec) so the spec engine can
dispatch by view name.
"""
from . import courses, employers, occupations

# Map view-name strings used elsewhere in the codebase (in the existing
# `query_engine.resolve_vocabulary` view parameter) to the per-feature
# spec module. Adding a new feature is a one-line addition here.
VIEW_TO_MODULE = {
    "occupation": occupations,
    "course": courses,
    "employer": employers,
}

# View → SpecClass for callers that want to validate a spec dict
# externally (used by the spec_engine extractor).
VIEW_TO_SPEC_CLASS = {
    "occupation": occupations.OccupationSpec,
    "course": courses.CourseSpec,
    "employer": employers.EmployerSpec,
}

__all__ = [
    "courses", "employers", "occupations",
    "VIEW_TO_MODULE", "VIEW_TO_SPEC_CLASS",
]
