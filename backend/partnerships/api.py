"""Partnership endpoints — sector index and per-occupation opportunity reports.

The Partnerships surface is occupation-centric: SOCs are organized under
the 12 PCAH-classified Strong Workforce sectors and each report frames
the regional employer set as candidate partners for a multi-employer
engagement around the occupational pathway.
"""

from fastapi import APIRouter, HTTPException
from partnerships.models import OpportunityReport, SectorIndex
from partnerships.opportunity import build_opportunity_report, build_sector_index

router = APIRouter()


@router.get("/sectors", response_model=SectorIndex)
def get_partnership_sectors(college: str):
    """Returns the Strong Workforce sector accordion for a college:
    every PCAH-classified sector with at least one CTE-reachable,
    regionally-demanded occupation, alphabetically ordered.

    Per the institutional-deference principle: the sector→occupation
    mapping comes from the Chancellor's Office Program and Course
    Approval Handbook (PCAH) walked through the TOP-CIP-SOC chain.
    A SOC may appear under multiple sectors — institutional reality,
    not a partition.
    """
    try:
        return build_sector_index(college)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/opportunity/{soc_code}", response_model=OpportunityReport)
def get_partnership_opportunity(
    soc_code: str,
    college: str,
    sector: str | None = None,
):
    """Returns the per-(college, occupation) partnership opportunity
    report. Composed deterministically from the institutional graph:
    regional demand (COE), TOP-grouped curriculum coverage, student
    impact, regional employer set sorted by NAICS industry share, and
    employer-agnostic narrative pointing to the multi-employer
    engagement opportunity the data identifies.

    The optional `sector` query parameter preserves the user's click
    context: SOCs that belong to multiple PCAH sectors render with
    whichever sector they were navigated from, rather than being
    re-resolved alphabetically. Invalid sectors (not actually one of
    the SOC's PCAH sectors) are ignored — the report falls back to
    the alphabetical default.
    """
    try:
        return build_opportunity_report(college, soc_code, sector_hint=sector)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
