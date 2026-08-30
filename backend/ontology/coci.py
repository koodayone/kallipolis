"""COCI — the CCCCO Curriculum Inventory: which awards a college is APPROVED to offer.

The complement to DataMart. DataMart records what a college *conferred*; COCI records
what it is approved to *offer*. A credential can be live in COCI and absent from DataMart
— Foothill's Respiratory Care B.S. was approved 2024-05-30 and its first cohort has not
graduated inside our award window — and that gap is exactly what a program evaluation
needs to show.

WHAT THIS MODULE IS AUTHORITATIVE FOR, and what it is not:

  * which awards exist under a (college, TOP6)      -> COCI, here
  * the award TYPE and its unit BAND                -> COCI, here
  * STATUS (Active / Teachout / Inactive / ...)     -> COCI, here
  * APPROVED DATE                                   -> COCI, here
  * the EXACT current unit requirement              -> the college CATALOG, not here
  * conferrals                                      -> DataMart, not here

That fifth line is the load-bearing one. `CERT UNITS` / `MAJOR UNITS` are the figures as
of APPROVAL, and programs are revised without re-approval so long as they stay inside
their approved band. Of 20,592 Active records, 43% carry no approval date at all and 19%
predate 2015 (earliest: 1946). Checked against Foothill's own catalog: the Veterinary
Assisting certificate (approved 2020) matches exactly at 12.5, while the Veterinary
Technology A.S. (approved 1975-01-01) reads 98.50 against a catalog that says 93.

Worse, those numbers are CALENDAR-NATIVE while DataMart's labels are semester-normalized.
Foothill is a quarter college (its catalog states the 90-unit associate minimum; semester
colleges require 60). Rendering a raw COCI unit count would put quarter units beside
semester units in one document and publish a number contradicting the college's own page.

So callers should render `award_band()`, never the raw unit fields. Every certificate
AWARD string carries DUAL semester/quarter notation ("8S/12Q to fewer than 16S/24Q"),
which is calendar-safe and stays current — moving outside the band forces re-approval.
"""
from __future__ import annotations

import csv
import gzip
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from ontology.programs import AWARD_TIERS

_DATA = Path(__file__).parent / "data" / "coci_programs.csv.gz"

# Snapshot date of the bundled export, stated like ontology.supply.COE_DEMAND_VINTAGE so a
# surface can cite its currency rather than implying the file is live.
COCI_VINTAGE = "CCCCO Curriculum Inventory (COCI) program export, as of 2026-08-27"

# COCI's own status vocabulary, kept whole. Collapsing to a boolean would throw away
# "Active - Teachout Only" — closed to new students, still teaching out the enrolled —
# which is the single most useful signal COCI carries for a program review.
STATUS_ACTIVE = "Active"
STATUS_TEACHOUT = "Active - Teachout Only"
#: Statuses a student can still act on. Everything else (Inactive, Draft, Review,
#: Revision, Submitted, Approved-but-not-yet-active) is not an offer.
OFFERED_STATUSES = (STATUS_ACTIVE, STATUS_TEACHOUT)

# Graph college name -> COCI college code. EXPLICIT, never fuzzy: there are 121 COCI codes
# against our 115 colleges and the irregulars do not pattern-match — "City College of San
# Francisco" is SAN FRANCISCO CITY, and the nine Los Angeles colleges abbreviate to "L.A. X".
# A prefix matcher reached only 93/115 during the audit that motivated this module.
_COLLEGE_CODE: dict[str, str] = {
    'Allan Hancock College': 'ALLAN HANCOCK',
    'American River College': 'AMERICAN RIVER',
    'Antelope Valley College': 'ANTELOPE VALLEY',
    'Bakersfield College': 'BAKERSFIELD',
    'Barstow Community College': 'BARSTOW',
    'Berkeley City College': 'BERKELEY CITY',
    'Butte College': 'BUTTE',
    'Cabrillo College': 'CABRILLO',
    'Cañada College': 'CANADA',
    'Cerritos College': 'CERRITOS',
    'Cerro Coso Community College': 'CERRO COSO',
    'Chabot College': 'CHABOT',
    'Chaffey College': 'CHAFFEY',
    'Citrus College': 'CITRUS',
    'City College of San Francisco': 'SAN FRANCISCO CITY',
    'Clovis Community College': 'CLOVIS',
    'Coastline College': 'COASTLINE',
    'College of Alameda': 'ALAMEDA',
    'College of Marin': 'MARIN',
    'College of San Mateo': 'SAN MATEO',
    'College of the Canyons': 'CANYONS',
    'College of the Desert': 'DESERT',
    'College of the Redwoods': 'REDWOODS',
    'College of the Sequoias': 'SEQUOIAS',
    'College of the Siskiyous': 'SISKIYOUS',
    'Columbia College': 'COLUMBIA',
    'Compton College': 'COMPTON',
    'Contra Costa College': 'CONTRA COSTA',
    'Copper Mountain College': 'COPPER MOUNTAIN',
    'Cosumnes River College': 'COSUMNES RIVER',
    'Crafton Hills College': 'CRAFTON HILLS',
    'Cuesta College': 'CUESTA',
    'Cuyamaca College': 'CUYAMACA',
    'Cypress College': 'CYPRESS',
    'De Anza College': 'DE ANZA',
    'Diablo Valley College': 'DIABLO VALLEY',
    'East Los Angeles College': 'EAST L.A.',
    'El Camino College': 'EL CAMINO',
    'Evergreen Valley College': 'EVERGREEN VALLEY',
    'Feather River College': 'FEATHER RIVER',
    'Folsom Lake College': 'FOLSOM LAKE',
    'Foothill College': 'FOOTHILL',
    'Fresno City College': 'FRESNO CITY',
    'Fullerton College': 'FULLERTON',
    'Gavilan College': 'GAVILAN',
    'Glendale Community College': 'GLENDALE',
    'Golden West College': 'GOLDEN WEST',
    'Grossmont College': 'GROSSMONT',
    'Hartnell College': 'HARTNELL',
    'Imperial Valley College': 'IMPERIAL VALLEY',
    'Irvine Valley College': 'IRVINE VALLEY',
    'Lake Tahoe Community College': 'LAKE TAHOE',
    'Laney College': 'LANEY',
    'Las Positas College': 'LAS POSITAS',
    'Lassen College': 'LASSEN',
    'Long Beach City College': 'LONG BEACH CITY',
    'Los Angeles City College': 'L.A. CITY',
    'Los Angeles Harbor College': 'L.A. HARBOR',
    'Los Angeles Mission College': 'MISSION',
    'Los Angeles Pierce College': 'L.A. PIERCE',
    'Los Angeles Southwest College': 'L.A. SOUTHWEST',
    'Los Angeles Trade-Technical College': 'L.A. TRADE-TECH',
    'Los Angeles Valley College': 'L.A. VALLEY',
    'Los Medanos College': 'LOS MEDANOS',
    'Madera Community College': 'Madera',
    'Mendocino College': 'MENDOCINO',
    'Merced College': 'MERCED',
    'Merritt College': 'MERRITT',
    'MiraCosta College': 'MIRA COSTA',
    'Mission College': 'MISSION',
    'Modesto Junior College': 'MODESTO',
    'Monterey Peninsula College': 'MONTEREY PENINSULA',
    'Moorpark College': 'MOORPARK',
    'Moreno Valley College': 'MORENO VALLEY',
    'Mt. San Antonio College': 'MT. SAN ANTONIO',
    'Mt. San Jacinto College': 'MT. SAN JACINTO',
    'Napa Valley College': 'NAPA VALLEY',
    'Norco College': 'NORCO',
    'Ohlone College': 'OHLONE',
    'Orange Coast College': 'ORANGE COAST',
    'Oxnard College': 'OXNARD',
    'Palo Verde College': 'PALO VERDE',
    'Palomar College': 'PALOMAR',
    'Pasadena City College': 'PASADENA CITY',
    'Porterville College': 'PORTERVILLE',
    'Reedley College': 'REEDLEY',
    'Rio Hondo College': 'RIO HONDO',
    'Riverside City College': 'RIVERSIDE CITY',
    'Sacramento City College': 'SACRAMENTO CITY',
    'Saddleback College': 'SADDLEBACK',
    'San Bernardino Valley College': 'SAN BERNARDINO',
    'San Diego City College': 'SAN DIEGO CITY',
    'San Diego Mesa College': 'SAN DIEGO MESA',
    'San Diego Miramar College': 'SAN DIEGO MIRAMAR',
    'San Joaquin Delta College': 'SAN JOAQUIN DELTA',
    'San Jose City College': 'SAN JOSE CITY',
    'Santa Ana College': 'SANTA ANA',
    'Santa Barbara City College': 'SANTA BARBARA CITY',
    'Santa Monica College': 'SANTA MONICA',
    'Santa Rosa Junior College': 'SANTA ROSA',
    'Santiago Canyon College': 'SANTIAGO CANYON',
    'Shasta College': 'SHASTA',
    'Sierra College': 'SIERRA',
    'Skyline College': 'SKYLINE',
    'Solano Community College': 'SOLANO',
    'Southwestern College': 'SOUTHWESTERN',
    'Taft College': 'TAFT',
    'Ventura College': 'VENTURA',
    'Victor Valley College': 'VICTOR VALLEY',
    'West Hills College Coalinga': 'COALINGA COLLEGE',
    'West Hills College Lemoore': 'LEMOORE COLLEGE',
    'West Los Angeles College': 'WEST L.A.',
    'West Valley College': 'WEST VALLEY',
    'Woodland Community College': 'WOODLAND',
    'Yuba College': 'YUBA',
}


@dataclass(frozen=True)
class CociAward:
    """One approved award: a (title, award type) a college may confer under a TOP code."""
    college: str
    top6: str
    title: str
    award: str          # COCI's raw AWARD string — carries the dual S/Q band
    status: str
    approved: str       # ISO date, or "" — 43% of Active records carry none
    goal: str
    control_number: str

    @property
    def tier(self) -> str:
        return coci_award_tier(self.award)

    @property
    def band(self) -> str:
        return award_band(self.award)

    @property
    def is_teachout(self) -> bool:
        return self.status == STATUS_TEACHOUT


def coci_award_tier(award: str) -> str:
    """Map a COCI AWARD string onto the shared `AWARD_TIERS` vocabulary.

    Deliberately SEPARATE from `ontology.programs.award_tier` rather than an extension of
    it. That function feeds `award_type_sort_key`, which the dashboard's programs panel
    uses for ordering, so widening it to a second dialect puts a shipped surface at risk
    for no gain. The two share the VOCABULARY (`AWARD_TIERS`); `test_coci.py` pins the
    correspondence so they cannot drift apart.

    COCI's dialect has a trap DataMart's lacks: it writes BOTH "A.A- T Degree" (hyphen)
    and "A.S. T Degree" (space). A first-cut regex matching only the hyphen mis-filed
    1,548 transfer degrees as associate degrees.
    """
    a = (award or "").strip()
    if not a:
        return ""
    if "Baccalaureate" in a:
        return "baccalaureate"
    if re.search(r"[-.]\s*T\s+Degree", a) or "Transfer" in a:
        return "transfer degree"
    if "Degree" in a:
        return "associate degree"
    if "Noncredit" in a:
        return "noncredit award"
    if "Certificate" in a:
        return "certificate"
    return "other credit award"


def award_band(award: str) -> str:
    """The unit band a COCI award type guarantees, as "8-16 semester / 12-24 quarter units".

    This — not `CERT UNITS`/`MAJOR UNITS` — is what a surface should print. It is
    calendar-explicit and it stays current, because a program that moves outside its band
    must be re-approved into a different award type. Degrees carry no band and return "".
    """
    a = (award or "")
    m = re.search(r"(\d+)S/(\d+)Q\s+to\s+fewer than\s+(\d+)S/(\d+)Q", a)
    if m:
        return f"{m.group(1)}\u2013{m.group(3)} semester / {m.group(2)}\u2013{m.group(4)} quarter units"
    m = re.search(r"(\d+)\+S/(\d+)\+Q", a)
    if m:
        return f"{m.group(1)}+ semester / {m.group(2)}+ quarter units"
    # the "18 or greater semester(or 27 or greater quarter)" shape
    m = re.search(r"(\d+)\s+or greater semester\(or\s+(\d+)\s+or greater", a, re.I)
    if m:
        return f"{m.group(1)}+ semester / {m.group(2)}+ quarter units"
    m = re.search(r"(\d+)\s+to fewer than\s+(\d+)\s+semester\(or\s+(\d+)\s+to fewer than\s+(\d+)", a, re.I)
    if m:
        return f"{m.group(1)}\u2013{m.group(2)} semester / {m.group(3)}\u2013{m.group(4)} quarter units"
    return ""


def _top6(top_code: str) -> str:
    """COCI's TOP CODE is a combined label — "1210.00* Respiratory Care/Therapy"."""
    m = re.match(r"\s*(\d{4})\.(\d{2})", top_code or "")
    return (m.group(1) + m.group(2)) if m else ""


@lru_cache(maxsize=1)
def _load() -> dict[tuple[str, str], tuple[CociAward, ...]]:
    out: dict[tuple[str, str], list[CociAward]] = {}
    with gzip.open(_DATA, "rt", encoding="utf-8-sig", newline="") as fh:
        for r in csv.DictReader(fh):
            t = _top6(r.get("TOP CODE", ""))
            if not t:
                continue
            code = (r.get("COLLEGE") or "").strip()
            out.setdefault((code, t), []).append(CociAward(
                college=code, top6=t, title=(r.get("TITLE") or "").strip(),
                award=(r.get("AWARD") or "").strip(), status=(r.get("STATUS") or "").strip(),
                approved=(r.get("APPROVED DATE") or "").strip(),
                goal=(r.get("GOAL") or "").strip(),
                control_number=(r.get("CONTROL NUMBER") or "").strip()))
    return {k: tuple(v) for k, v in out.items()}


def coci_code(college: str) -> str | None:
    """The COCI code for a graph college name, or None when unmapped."""
    return _COLLEGE_CODE.get(college)


def awards_for(college: str, top6: str, *, offered_only: bool = True) -> list[CociAward]:
    """Approved awards for a (graph college name, TOP6), highest credential first.

    `offered_only` keeps Active and Teachout — what a student can still act on — and drops
    Inactive and the not-yet-live statuses. Ordering matches the report's credential weight
    so this section and the conferrals table read in the same sequence.
    """
    code = coci_code(college)
    if not code:
        return []
    rows = _load().get((code, top6), ())
    if offered_only:
        rows = tuple(r for r in rows if r.status in OFFERED_STATUSES)
    return sorted(rows, key=lambda r: (AWARD_TIERS.index(r.tier) if r.tier in AWARD_TIERS
                                       else len(AWARD_TIERS), r.title))
