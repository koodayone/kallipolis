"""
Raw course dataclass shared by the courses pipeline.

`RawCourse` is the pre-enrichment representation a stage-1 extractor
produces and stage-2 skill derivation consumes. The active extractor is
`courses/scrape_pdf.py`; this module exists to host `RawCourse` so that
`scrape_pdf.py`, `ontology/skills.py`, and `pipeline/run.py` can all
import it from one place.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field


@dataclass
class RawCourse:
    """Raw course data extracted from a college catalog, pre-enrichment."""

    name: str = ""
    code: str = ""
    department: str = ""
    units: str = ""
    description: str = ""
    prerequisites: str = ""
    learning_outcomes: list[str] = field(default_factory=list)
    course_objectives: list[str] = field(default_factory=list)
    transfer_status: str = ""
    ge_area: str = ""
    grading: str = ""
    hours: str = ""
    url: str = ""

    def to_dict(self) -> dict:
        return asdict(self)
