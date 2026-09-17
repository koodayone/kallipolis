"""The living wage a full-time hourly wage is measured against — MIT's, per California county.

The MIT Living Wage Calculator (livingwage.mit.edu) publishes, for every county, the hourly
wage a full-time worker (2,080 hours a year) must earn to meet a household's basic needs,
by household composition. BACCC names it as its own provenance for living wage, so a
report that measures an occupation's median wage against it agrees with the regional
consortium's materials. The reference figure surfaces use is the calculator's headline:
ONE ADULT, NO CHILDREN, in the college's own county — the county because that is how the
state talks about living wage (the Chancellor's Office metric, the Self-Sufficiency
Standard, Strong Workforce reporting are all county-keyed), and because a college's
service area is drawn within counties.

Authority: MIT owns the threshold; the Centers of Excellence own the wage it is compared
with. The calculator's pages are fetched once by `fetch_bundle` into
`data/mit_living_wage_ca.csv` (one row per county, hourly dollars, with the page's data
year) and never at render time.

    python -m ontology.living_wage          # refresh the bundle from livingwage.mit.edu
"""

from __future__ import annotations

import csv
import html as _html
import re
import time
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

_DATA = Path(__file__).parent / "data" / "mit_living_wage_ca.csv"
_BASE = "https://livingwage.mit.edu"
_STATE_LOCATIONS = f"{_BASE}/states/06/locations"

#: Household columns in the calculator's table, in its order: adults(working) × children.
HOUSEHOLDS = ("1a0c", "1a1c", "1a2c", "1a3c", "2a1w0c", "2a1w1c", "2a1w2c", "2a1w3c",
              "2a2w0c", "2a2w1c", "2a2w2c", "2a2w3c")
HEADLINE = "1a0c"          # one adult, no children — the calculator's headline figure


@dataclass(frozen=True)
class LivingWage:
    fips: str                   # 5-digit county FIPS, e.g. 06085
    county: str                 # "Santa Clara County"
    vintage: str                # the data year the page states
    hourly: dict[str, float]    # household key -> living wage, $/hour
    poverty_1a0c: float
    minimum_wage: float

    @property
    def headline(self) -> float:
        return self.hourly[HEADLINE]

    @property
    def url(self) -> str:
        return f"{_BASE}/counties/{self.fips}"


@lru_cache(maxsize=1)
def _load() -> dict[str, LivingWage]:
    out = {}
    with _DATA.open(newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            out[r["county"]] = LivingWage(r["fips"], r["county"], r["vintage"],
                                          {h: float(r[h]) for h in HOUSEHOLDS},
                                          float(r["poverty_1a0c"]), float(r["minimum_wage"]))
    return out


def living_wage(county: str) -> LivingWage | None:
    """The county's living wage figures; `county` as "Santa Clara County" or "Santa Clara"."""
    c = county if county.endswith(" County") else f"{county} County"
    return _load().get(c)


LIVING_WAGE_VINTAGE = "MIT Living Wage Calculator"


# ── fetch ──────────────────────────────────────────────────────────────────────
def _parse_county(page: str) -> tuple[str, str, dict[str, float], float, float]:
    title = re.search(r"Living Wage Calculation for ([^,<]+), California", page).group(1).strip()
    table = re.search(r"<table.*?</table>", page, re.S).group(0)
    rows = {}
    for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", table, re.S):
        cells = [_html.unescape(re.sub(r"<[^>]+>", "", c)).strip() for c in re.findall(r"<t[hd][^>]*>(.*?)</t[hd]>", tr, re.S)]
        if cells and cells[0] in ("Living Wage", "Poverty Wage", "Minimum Wage"):
            rows[cells[0]] = [float(v.replace("$", "").replace(",", "")) for v in cells[1:] if v.startswith("$")]
    lw = dict(zip(HOUSEHOLDS, rows["Living Wage"]))
    years = re.findall(r"\b(20[2-3]\d)\b", re.sub(r"<[^>]+>", " ", page))   # not 2080, the hours figure
    vintage = max(years) if years else ""
    return title, vintage, lw, rows["Poverty Wage"][0], rows["Minimum Wage"][0]


def fetch_bundle(out: Path = _DATA, *, pause: float = 1.0) -> Path:
    import httpx
    client = httpx.Client(timeout=30, follow_redirects=True, headers={"User-Agent": "Mozilla/5.0 (Kallipolis; living-wage bundle)"})
    index = client.get(_STATE_LOCATIONS).text
    fips = sorted(set(re.findall(r'href="/counties/(06\d{3})"', index)))
    recs = []
    for f in fips:
        page = client.get(f"{_BASE}/counties/{f}").text
        county, vintage, lw, pov, mw = _parse_county(page)
        recs.append({"fips": f, "county": county, "vintage": vintage, **{h: f"{lw[h]:.2f}" for h in HOUSEHOLDS},
                     "poverty_1a0c": f"{pov:.2f}", "minimum_wage": f"{mw:.2f}"})
        time.sleep(pause)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(recs[0]))
        w.writeheader(); w.writerows(recs)
    return out


if __name__ == "__main__":
    p = fetch_bundle()
    print(f"wrote {p} ({sum(1 for _ in open(p)) - 1} counties)")
