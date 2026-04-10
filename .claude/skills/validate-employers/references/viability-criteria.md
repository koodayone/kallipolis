# Workforce Development Partnership Viability Criteria

Each criterion below must be satisfied for an employer to be retained. The criteria
are ordered from cheapest to evaluate (web search) to most nuanced (judgment call),
enabling early exit on obvious failures.

---

## Criterion 1: Institutional Web Presence

**Rule**: The organization must have an official website that represents it as an
institution — not merely a listing on a third-party directory.

**Passes**:
- Dedicated domain (e.g., `kaweahhealth.org`, `clarkbrosinc.com`)
- Subpage on a parent organization's domain (e.g., a clinic listed on
  `clinicasierravista.org/locations/elm-community-health-center/`)
- Government `.gov` page for the specific entity
- Education `.edu` page for the specific institution

**Fails**:
- Only appears on Yelp, BBB, Yellow Pages, Manta, or LinkedIn
- Only appears in EDD/labor market databases
- Has a Facebook page but no website
- Domain exists but is parked, under construction, or unrelated
- Domain appears in search results but actual page content is ad-network scripts,
  tracking iframes, or placeholder text (common with expired/lapsed domains —
  **always fetch and verify page content before accepting a URL**)

**Why this matters**: A community college partnership requires a counterpart that can
receive a formal proposal, designate a point of contact, and execute an agreement.
Organizations without web presence almost universally lack this capacity. The website
is a proxy for institutional formality.

**Examples from analysis**:
- PASS: Lion Raisins → lionraisins.com (Wix site, but functional)
- PASS: Elm Community Health Center → clinicasierravista.org (parent site)
- FAIL: Latino Farm Labor Services → only BBB/Yellow Pages listings
- FAIL: R & N Packing → only directory listings, 10 employees

---

## Criterion 2: Currently Operating

**Rule**: The organization must be actively operating. Not closed, sold, acquired and
dissolved, or pending shutdown.

**Passes**:
- Active business with current web presence
- Acquired but still operating under same name at same location
- Seasonal operations (e.g., ski resorts, harvest-dependent ag)

**Fails**:
- Facility closed (e.g., Del Monte Foods Hanford — closed March 2025)
- Business sold and name retired (e.g., Lo Bue Brothers — sold 2017)
- Pending closure announced in news

**Verification**: Search for `"{employer name}" closed OR shutdown OR sold OR acquired`
to check for recent closures. News results from the past 2 years are most relevant.

**Examples from analysis**:
- FAIL: Del Monte Foods (Hanford) — plant closed March 2025, 378 workers laid off
- FAIL: Lo Bue Brothers — sold packing house in 2017 after 83 years
- PASS: China Peak Mountain Resort — seasonal but actively operating

---

## Criterion 3: Distinct Entity

**Rule**: The employer must be a standalone organizational entity, not a sub-unit,
internal venue, or alias of another employer already in the list.

**Passes**:
- Independent organization with its own leadership/management
- Subsidiary with distinct operations (e.g., Adventist Health Tulare is a distinct
  hospital even though part of Adventist Health system)
- Government agency with distinct workforce (e.g., Fresno Police Department)

**Fails**:
- Coffee shop or restaurant inside a casino (partner with the casino instead)
- Internal department of a city government listed as separate employer
  (e.g., "Visalia Public Works Administration" — partner with City of Visalia)
- Generic/ambiguous name that cannot be resolved to a specific organization
  (e.g., "Solid Waste Collection", "Blackstone")
- Sub-entity of a parent already in the list with no distinct workforce

**Deduplication**: When a parent and child both appear, keep both only if the child
has a meaningfully distinct workforce and partnership surface. Example:
- KEEP BOTH: Community Medical Centers + Fresno Heart & Surgical Hospital
  (different specialties, different hiring needs)
- REMOVE CHILD: Yokuts Coffee House (a restaurant inside Eagle Mountain Casino —
  partnership would be with the casino)

**Examples from analysis**:
- FAIL: Yokuts Coffee House — venue inside Eagle Mountain Casino
- FAIL: Solid Waste Collection — generic name, not an identifiable org
- FAIL: Blackstone — ambiguous (auto dealership? investment firm? neighborhood?)
- FAIL: United States Cotton Classing Office — tiny USDA satellite, not partnership-scale
- PASS: Fresno County Sheriff's Office — distinct workforce, distinct CTE pipeline

---

## Criterion 4: CTE-Relevant Workforce

**Rule**: The employer must hire for roles that community college CTE programs
prepare students for. The occupations should align with certificate or associate
degree pathways.

**Passes**:
- Healthcare employers (nursing, allied health, medical coding)
- Manufacturing (machinists, technicians, quality control)
- Construction and trades (electricians, plumbers, HVAC)
- IT and technology (network admin, web development, cybersecurity)
- Business services (accounting, HR, office administration)
- Public safety (law enforcement, fire, corrections)
- Hospitality and culinary (hotel management, food service)
- Agriculture technology (precision ag, equipment operation)
- Automotive (service technicians, parts management)

**Fails**:
- Farm labor contracting (seasonal manual labor, no CTE pathway)
- Sole-proprietor retail with no career ladder
- Organizations where all roles require graduate degrees only

**Edge case — large ag operations**: Large farming operations (500+ employees) may
have CTE-relevant roles (equipment maintenance, logistics, food safety, accounting)
even if the core operation is agricultural. Assess based on occupational diversity,
not just sector.

**Examples from analysis**:
- FAIL: Zepeda's Farm Labor Services — farm labor contracting only
- FAIL: MGM Labor Contracting — small labor contractor
- PASS: Woolf Farming Company — 900+ employees, diverse operations including
  processing, logistics, and technology roles
- PASS: Sun-Maid Growers — manufacturing, quality control, logistics

---

## Criterion 5: Partnership Capacity

**Rule**: The organization must have the institutional infrastructure to sustain a
workforce development partnership. This means some combination of: HR department,
training programs, management hierarchy, and organizational stability.

**Size thresholds by sector** (guidelines, not hard cutoffs):
- Healthcare: 25+ employees (even small clinics partner for clinical rotations)
- Manufacturing: 100+ employees (need scale for internship programs)
- Construction/Trades: 50+ employees (apprenticeship programs need supervision)
- Government: Any size (institutional capacity is inherent)
- Education: Any size (natural partnership infrastructure)
- Retail/Hospitality: 100+ employees or multi-location (single small shops lack capacity)
- Agriculture: 200+ employees (need operational complexity beyond field labor)
- Professional Services: 50+ employees

**Passes**:
- Has a careers page or employment section on website
- Has an HR department or designated hiring manager
- Is part of a larger organizational system (health system, school district, county)
- Has training programs, apprenticeships, or internship history
- Is employee-owned (ESOP) — indicates organizational maturity

**Fails**:
- Sole proprietor or family operation with <10 employees
- No evidence of HR infrastructure or hiring process
- Business is a single retail location with only entry-level, high-turnover roles

**Examples from analysis**:
- PASS: Geil Enterprises — 500+ employee ESOP, security/janitorial, careers page
- PASS: Warmerdam Packing — ~180 employees, dedicated HR email, employment page
- FAIL: Circle K Ranch — small retail gift shop, no careers infrastructure
- FAIL: Wiebe Farms — olive oil tasting room, family operation

---

## Decision Matrix

When criteria conflict or an employer is borderline:

| Situation | Decision |
|-----------|----------|
| Large employer (500+), no website | Flag for manual review, retain with `website: null` |
| Small employer (<50), strong website + careers page | Retain — web presence signals capacity |
| Government sub-department | Remove if parent entity is already listed |
| Seasonal employer (resort, ag processing) | Retain if institution persists year-round |
| Recently acquired, operating under new name | Retain with updated name and website |
| Parent org in list + child org in list | Keep both if distinct workforce/CTE pathways |
