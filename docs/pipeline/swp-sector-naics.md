# SWP Sector NAICS Composition

The employer scrape restricts itself to NAICS industries that represent at least one Strong Workforce Program priority sector. This document is the authority for which NAICS 4-digit codes are included, which are excluded, and why.

## The essence

The Strong Workforce Program sector taxonomy is defined by the California Community Colleges Chancellor's Office in the Program and Course Approval Handbook (PCAH). The canonical sector list — twelve sectors plus an administrative "Unassigned" bucket — is published in the `TOP Codes to Sectors.xlsx` file, which Kallipolis ships in-repo at `backend/ontology/data/TOP Codes to Sectors.xlsx` and loads at import time from both sides of the ontology. Every NAICS 4-digit code in `CTE_NAICS_CODES` (`backend/employers/edd_scrape.py`) maps to at least one of the twelve sectors; codes that represent no SWP sector are excluded. The sector string list is loaded from the xlsx by the `_load_pcah_cte_top6` helper in `backend/ontology/crosswalks.py`, so a change to the published PCAH taxonomy flows into the graph on the next import without code edits beyond adding or adjusting the per-NAICS mappings.

## Authority

The canonical file is the Chancellor's Office PCAH crosswalk [TOP Codes to Sectors](https://www.calpassplus.org/launchboard/). The same file is loaded by the occupation side of the graph via `_load_pcah_cte_top6` in `backend/ontology/crosswalks.py`, so the two sides of the ontology speak the same sector vocabulary by construction. The employer-side loader `_load_swp_sectors` is in `backend/employers/edd_scrape.py`.

The twelve sectors, verbatim from the xlsx:

1. Advanced Manufacturing
2. Advanced Transportation and Logistics
3. Agriculture, Water and Environmental Technologies
4. Business and Entrepreneurship
5. Education and Human Development
6. Energy, Construction and Utilities
7. Global Trade
8. Health
9. Information and Communication Technologies - Digital Media
10. Life Sciences - Biotechnology
11. Public Safety
12. Retail, Hospitality and Tourism

The "Unassigned" bucket — an administrative category for TOP codes not yet classified — is filtered out by the loader and never appears on the employer side.

## Sector composition

The following tables enumerate every NAICS 4-digit code currently in the scrape list, grouped by primary SWP sector. Additional sectors after the primary reflect legitimate cross-sector representation — a semiconductor manufacturer is both Advanced Manufacturing and ICT; a hospital is Health; a medical-device manufacturer is Health and Life Sciences and Advanced Manufacturing.

### Agriculture, Water and Environmental Technologies

| NAICS | Label | Additional sectors |
|---|---|---|
| 1111 | Agriculture - Oilseed/Grain | — |
| 1112 | Agriculture - Vegetables/Melons | — |
| 1113 | Agriculture - Fruit/Tree Nuts | — |
| 1114 | Agriculture - Greenhouse/Nursery | — |
| 1119 | Agriculture - Other Crops | — |
| 1121 | Agriculture - Cattle | — |
| 1122 | Agriculture - Hogs/Pigs | — |
| 1123 | Agriculture - Poultry/Eggs | — |
| 1124 | Agriculture - Sheep/Goats | — |
| 1125 | Agriculture - Aquaculture | — |
| 1129 | Agriculture - Other Animals | — |
| 1151 | Agriculture - Crop Support | — |
| 1152 | Agriculture - Animal Support | — |
| 2213 | Utilities - Water/Sewer | Energy, Construction and Utilities |
| 3111 | Manufacturing - Animal Food | — |
| 3114 | Manufacturing - Fruit/Vegetable Preserving | — |
| 3115 | Manufacturing - Dairy Products | — |
| 3116 | Manufacturing - Meat Processing | — |
| 3117 | Manufacturing - Seafood Processing | — |
| 3118 | Manufacturing - Bakeries | Business and Entrepreneurship |
| 3119 | Manufacturing - Other Food | — |
| 3121 | Manufacturing - Beverages | — |
| 4245 | Wholesale - Farm Products | Global Trade |
| 5621 | Waste - Collection | — |
| 5622 | Waste - Treatment/Disposal | — |
| 9241 | Environmental Quality - Government | — |

### Advanced Manufacturing

| NAICS | Label | Additional sectors |
|---|---|---|
| 3211 | Manufacturing - Sawmills/Wood | — |
| 3212 | Manufacturing - Veneer/Plywood | — |
| 3219 | Manufacturing - Other Wood Products | — |
| 3231 | Manufacturing - Printing | — |
| 3261 | Manufacturing - Plastics | — |
| 3273 | Manufacturing - Cement/Concrete | — |
| 3323 | Manufacturing - Architectural Metals | — |
| 3327 | Manufacturing - Machine Shops | — |
| 3328 | Manufacturing - Coating/Engraving | — |
| 3329 | Manufacturing - Other Fabricated Metals | — |
| 3331 | Manufacturing - Ag/Construction Machinery | Agriculture, Water and Environmental Technologies |
| 3332 | Manufacturing - Industrial Machinery | — |
| 3335 | Manufacturing - Metalworking Machinery | — |

### Advanced Transportation and Logistics

| NAICS | Label | Additional sectors |
|---|---|---|
| 3361 | Manufacturing - Motor Vehicles | Advanced Manufacturing |
| 3363 | Manufacturing - Motor Vehicle Parts | Advanced Manufacturing |
| 3364 | Manufacturing - Aerospace | Advanced Manufacturing |
| 3366 | Manufacturing - Ship/Boat | Advanced Manufacturing |
| 4231 | Wholesale - Motor Vehicles/Parts | Global Trade |
| 4811 | Transportation - Air | Global Trade |
| 4841 | Transportation - Trucking (General) | Global Trade |
| 4842 | Transportation - Trucking (Specialized) | Global Trade |
| 4851 | Transportation - Transit/Ground Passenger | — |
| 4853 | Transportation - Taxi/Limo | — |
| 4854 | Transportation - School Bus | — |
| 4859 | Transportation - Other Transit | — |
| 4881 | Transportation - Support Activities (Air) | Global Trade |
| 4921 | Transportation - Couriers/Express Delivery | Global Trade |
| 4931 | Transportation - Warehousing/Storage | Global Trade |
| 8111 | Services - Auto Repair/Maintenance | — |

### Business and Entrepreneurship

| NAICS | Label | Additional sectors |
|---|---|---|
| 5412 | Professional - Accounting/Tax | — |
| 5413 | Professional - Architecture/Engineering | Advanced Manufacturing |
| 5414 | Professional - Graphic/Industrial Design | — |
| 5416 | Professional - Management/Technical Consulting | — |
| 5418 | Professional - Advertising/PR | — |
| 5617 | Admin - Janitorial/Landscaping | Agriculture, Water and Environmental Technologies |
| 8121 | Services - Personal Care | — |

### Education and Human Development

| NAICS | Label | Additional sectors |
|---|---|---|
| 6111 | Education - Elementary/Secondary | — |
| 6112 | Education - Junior Colleges | — |
| 6113 | Education - Colleges/Universities | — |
| 6114 | Education - Business/Management Training | Business and Entrepreneurship |
| 6115 | Education - Technical/Trade Schools | — |
| 6116 | Education - Other Schools | — |
| 6117 | Education - Educational Support Services | — |
| 6241 | Social Services - Individual/Family | — |
| 6242 | Social Services - Community Emergency Relief | — |
| 6243 | Social Services - Vocational Rehab | — |
| 6244 | Social Services - Child Day Care | Business and Entrepreneurship |

### Energy, Construction and Utilities

| NAICS | Label | Additional sectors |
|---|---|---|
| 2111 | Mining - Oil/Gas Extraction | — |
| 2211 | Utilities - Electric Power | — |
| 2212 | Utilities - Natural Gas | — |
| 2361 | Construction - Residential | — |
| 2362 | Construction - Commercial | — |
| 2371 | Construction - Utility Systems | — |
| 2373 | Construction - Highway/Street | Advanced Transportation and Logistics |
| 2379 | Construction - Other Heavy | — |
| 2381 | Construction - Foundation/Structural | Advanced Manufacturing |
| 2382 | Construction - HVAC/Plumbing/Electrical | — |
| 2383 | Construction - Finishing | — |
| 2389 | Construction - Other Specialty | — |
| 3241 | Manufacturing - Petroleum/Coal | Advanced Manufacturing |
| 3334 | Manufacturing - HVAC Equipment | Advanced Manufacturing |
| 3351 | Manufacturing - Electrical Equipment | Advanced Manufacturing |

### Global Trade

| NAICS | Label | Additional sectors |
|---|---|---|
| 4234 | Wholesale - Professional Equipment | — |
| 4241 | Wholesale - Paper/Packaging | — |
| 4244 | Wholesale - Grocery/Related | Agriculture, Water and Environmental Technologies |
| 4247 | Wholesale - Petroleum | Energy, Construction and Utilities |
| 4249 | Wholesale - Miscellaneous Nondurable | — |

### Health

| NAICS | Label | Additional sectors |
|---|---|---|
| 3391 | Manufacturing - Medical Equipment | Life Sciences, Advanced Manufacturing |
| 6211 | Healthcare - Physician Offices | — |
| 6212 | Healthcare - Dental | — |
| 6213 | Healthcare - Other Practitioners | — |
| 6214 | Healthcare - Outpatient | — |
| 6215 | Healthcare - Labs | Life Sciences - Biotechnology |
| 6216 | Healthcare - Home Health | — |
| 6219 | Healthcare - Other Ambulatory | — |
| 6221 | Healthcare - Hospitals (General) | — |
| 6222 | Healthcare - Hospitals (Psych/Substance) | — |
| 6223 | Healthcare - Hospitals (Specialty) | — |
| 6231 | Healthcare - Nursing Facilities | — |
| 6232 | Healthcare - Residential Care | — |
| 6233 | Healthcare - Continuing Care | — |

### Information and Communication Technologies - Digital Media

| NAICS | Label | Additional sectors |
|---|---|---|
| 3341 | Manufacturing - Computers | Advanced Manufacturing |
| 3344 | Manufacturing - Semiconductors | Advanced Manufacturing |
| 5112 | IT - Software Publishing | — |
| 5121 | Media - Motion Picture/Video | — |
| 5122 | Media - Sound Recording | — |
| 5151 | Media - Radio/TV Broadcasting | — |
| 5171 | IT - Telecommunications (Wired) | — |
| 5172 | IT - Telecommunications (Wireless) | — |
| 5182 | IT - Data Processing/Hosting | — |
| 5191 | IT - Other Information Services/Web Portals | — |
| 5415 | Professional - Computer Systems Design | — |

### Life Sciences - Biotechnology

| NAICS | Label | Additional sectors |
|---|---|---|
| 3254 | Manufacturing - Pharmaceuticals | Advanced Manufacturing |
| 3345 | Manufacturing - Instruments | Advanced Manufacturing |
| 5417 | Professional - Scientific R&D | — |

### Public Safety

| NAICS | Label | Additional sectors |
|---|---|---|
| 5616 | Admin - Investigation/Security | — |
| 9221 | Government - Justice/Public Order/Safety | — |
| 9222 | Government - Fire Protection | — |

NAICS 2017+ rolls police, courts, corrections, and fire into a single 4-digit code (9221). Some EDD data additionally returns 9222 as a distinct Fire Protection subdivision — the pipeline preserves both mappings because the upstream source uses both.

### Retail, Hospitality and Tourism

| NAICS | Label | Additional sectors |
|---|---|---|
| 4248 | Wholesale - Beer/Wine/Spirits | Agriculture, Water and Environmental Technologies |
| 4411 | Retail - Auto Dealers | — |
| 4441 | Retail - Building Materials | — |
| 4451 | Retail - Grocery Stores | — |
| 4452 | Retail - Specialty Food | — |
| 4461 | Retail - Health/Personal Care | — |
| 4511 | Retail - Sporting Goods/Hobby | — |
| 4521 | Retail - Department Stores | — |
| 4529 | Retail - General Merchandise | — |
| 7131 | Arts - Amusement Parks/Arcades | — |
| 7139 | Arts - Other Amusement/Recreation | — |
| 7211 | Hospitality - Hotels/Motels | — |
| 7212 | Hospitality - RV Parks/Camps | — |
| 7223 | Food Service - Special/Caterers | Business and Entrepreneurship |
| 7224 | Food Service - Bars | — |
| 7225 | Food Service - Restaurants | — |

## What is deliberately excluded

The following NAICS 2-digit sectors have no 4-digit codes in the scrape list. Each exclusion is tied to the absence of a mapping to any SWP sector.

**Finance (NAICS 52)** — Banks, nondepository credit, securities, insurance carriers, insurance agencies. PCAH has no Finance sector; Banking and Finance TOP codes carry no SWP classification. Accounting and business administration are represented on the industry side via `5412` under Business and Entrepreneurship.

**Real Estate (NAICS 53)** — Lessors, agents, property management. Not a PCAH sector. Agents and brokers train via standalone licensing pathways outside the community college CTE system.

**Legal Services (NAICS 5411)** — Paralegal TOP codes carry no SWP sector. Law practice is not a community-college-trained profession at the scale that produces SWP partnerships.

**General Government Administration (NAICS 9211, 9223, 9231)** — Executive and legislative support, human resource administration, economic program administration. Public Administration TOP codes carry no SWP sector. The only government codes retained are `9221` (Justice, Public Order, and Safety — Public Safety) and `9241` (Environmental Quality — Agriculture, Water and Environmental Technologies) because both explicitly map to canonical PCAH sectors.

**Religious and Civic Organizations (NAICS 8131, 8134)** — Not PCAH-classifiable; not employment targets in the CTE sense.

**Arts non-recreation (NAICS 7111, 7121)** — Performing arts companies, museums. Technical Theater and Commercial Dance TOP codes carry no SWP sector, and museums have no TOP code representation at all.

**Employment and Business Support Services (NAICS 5613, 5614)** — Staffing agencies and call centers. Excluded structurally because their members place workers at other employers rather than hire onto their own payroll.

## How to update this mapping

The sector list is loaded dynamically from `backend/ontology/data/TOP Codes to Sectors.xlsx`. To pick up a new Chancellor's Office edition:

1. Replace the xlsx file in `backend/ontology/data/`.
2. Run `python3 -m pytest backend/employers/test_edd_scrape.py backend/ontology/test_regions.py` — the invariant tests will flag any sector-string drift between the xlsx, `CTE_NAICS_CODES`, and `COE_REGION_PRIORITY_SECTORS`.
3. If a new sector is introduced, add representative NAICS codes to `CTE_NAICS_CODES` (the invariant test requires every sector to have at least one primary NAICS). If a sector is removed, reassign the NAICS codes that pointed at it.
4. Update this document.

The NAICS 4-digit dict in `backend/employers/edd_scrape.py` is editorial — the judgment about which NAICS industries represent which SWP sector is employer-domain knowledge not carried in the xlsx. The xlsx provides the TOP-program-to-sector mapping; the NAICS-to-sector mapping derives from "which industries employ the workers produced by those programs," which is a human call.

## Related

- [Employer Generation](./employer-generation.md) — the pipeline stage that consumes this NAICS list.
- [Occupation Generation](./occupation-generation.md) — the occupation side of the PCAH crosswalk; uses the same `TOP Codes to Sectors.xlsx` to scope the CTE SOC universe.
- [AI Integration](../architecture/ai-integration.md) — the Gemini cleanup step that assigns per-employer SOC codes on top of the regional occupation list.
