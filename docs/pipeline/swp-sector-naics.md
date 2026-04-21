# SWP Sector NAICS Composition

The employer scrape restricts itself to NAICS industries that represent at least one Strong Workforce Program priority sector. This document is the authority for which NAICS 4-digit codes are included, which are excluded, and why.

## The essence

The Strong Workforce Program's "Doing What Matters for Jobs and the Economy" framework defines ten priority sectors. Every NAICS 4-digit code in `CTE_NAICS_CODES` (`backend/employers/edd_scrape.py`) maps to at least one of these sectors; codes that represent no SWP sector are excluded. The sector framework is the methodology authority, and each code's sector tags are the trail that lets a reader see why it was included.

## Authority

The canonical sector list is published by the California Community Colleges Chancellor's Office on the LaunchBoard platform. The [Program Code by Sector PDF](https://www.calpassplus.org/medialibrary/calpassplus/launchboard/documents/program_code_by_sector.pdf) maps every CTE TOP6 program code to its SWP priority sector(s). That document is a TOP-code-to-sector crosswalk (program-side); no published crosswalk maps NAICS codes (industry-side) to sectors. This repository's NAICS assignments are derived from the TOP-code assignments by matching industries to the programs they employ.

The ten sectors, verbatim from the LaunchBoard PDF:

1. Advanced Manufacturing and Advanced Technology
2. Advanced Transportation & Renewable Energy
3. Agriculture, Water & Environmental Technologies
4. Energy (Efficiency) & Utilities
5. Global Trade & Logistics
6. Health
7. Information & Communication Technologies (ICT) / Digital Media
8. Life Sciences / Biotechnology
9. Retail/Hospitality/Tourism
10. Small Business

Small Business is a cross-cutting sector — many TOP codes carry it as a secondary tag alongside their industry-primary sector. A handful of industries are classified under Small Business as primary because they employ the professions trained under small-business-anchored TOP codes (accounting, consulting, advertising, personal care, custodial services, childcare).

## Sector composition

The following tables enumerate every NAICS 4-digit code currently in the scrape list, grouped by primary SWP sector. Additional sectors (after the primary) reflect legitimate cross-sector representation — a semiconductor manufacturer is both Advanced Manufacturing and ICT; a hospital is Health; a medical-device manufacturer is Health and Life Sciences and Advanced Manufacturing.

### Agriculture, Water & Environmental Technologies

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
| 2213 | Utilities - Water/Sewer | Energy (Efficiency) & Utilities |
| 3111 | Manufacturing - Animal Food | — |
| 3114 | Manufacturing - Fruit/Vegetable Preserving | — |
| 3115 | Manufacturing - Dairy Products | — |
| 3116 | Manufacturing - Meat Processing | — |
| 3117 | Manufacturing - Seafood Processing | — |
| 3118 | Manufacturing - Bakeries | Small Business |
| 3119 | Manufacturing - Other Food | — |
| 3121 | Manufacturing - Beverages | — |
| 4245 | Wholesale - Farm Products | Global Trade & Logistics |
| 5621 | Waste - Collection | — |
| 5622 | Waste - Treatment/Disposal | — |
| 9241 | Environmental Quality - Government | — |

### Advanced Manufacturing and Advanced Technology

| NAICS | Label | Additional sectors |
|---|---|---|
| 2361 | Construction - Residential | — |
| 2362 | Construction - Commercial | — |
| 2371 | Construction - Utility Systems | Energy (Efficiency) & Utilities |
| 2373 | Construction - Highway/Street | Advanced Transportation & Renewable Energy |
| 2379 | Construction - Other Heavy | — |
| 2381 | Construction - Foundation/Structural | — |
| 2382 | Construction - HVAC/Plumbing/Electrical | Energy (Efficiency) & Utilities |
| 2383 | Construction - Finishing | — |
| 2389 | Construction - Other Specialty | — |
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
| 3331 | Manufacturing - Ag/Construction Machinery | Agriculture, Water & Environmental Technologies |
| 3332 | Manufacturing - Industrial Machinery | — |
| 3335 | Manufacturing - Metalworking Machinery | — |

### Advanced Transportation & Renewable Energy

| NAICS | Label | Additional sectors |
|---|---|---|
| 3361 | Manufacturing - Motor Vehicles | Advanced Manufacturing |
| 3363 | Manufacturing - Motor Vehicle Parts | Advanced Manufacturing |
| 3364 | Manufacturing - Aerospace | Advanced Manufacturing |
| 3366 | Manufacturing - Ship/Boat | Advanced Manufacturing |
| 4231 | Wholesale - Motor Vehicles/Parts | Global Trade & Logistics |
| 4811 | Transportation - Air | Global Trade & Logistics |
| 4841 | Transportation - Trucking (General) | Global Trade & Logistics |
| 4842 | Transportation - Trucking (Specialized) | Global Trade & Logistics |
| 4851 | Transportation - Transit/Ground Passenger | — |
| 4853 | Transportation - Taxi/Limo | — |
| 4854 | Transportation - School Bus | — |
| 4859 | Transportation - Other Transit | — |
| 4881 | Transportation - Support Activities (Air) | Global Trade & Logistics |
| 4921 | Transportation - Couriers/Express Delivery | Global Trade & Logistics |
| 8111 | Services - Auto Repair/Maintenance | — |

### Energy (Efficiency) & Utilities

| NAICS | Label | Additional sectors |
|---|---|---|
| 2111 | Mining - Oil/Gas Extraction | — |
| 2211 | Utilities - Electric Power | — |
| 2212 | Utilities - Natural Gas | — |
| 3241 | Manufacturing - Petroleum/Coal | Advanced Manufacturing |
| 3334 | Manufacturing - HVAC Equipment | Advanced Manufacturing |
| 3351 | Manufacturing - Electrical Equipment | Advanced Manufacturing |

### Global Trade & Logistics

| NAICS | Label | Additional sectors |
|---|---|---|
| 4234 | Wholesale - Professional Equipment | — |
| 4241 | Wholesale - Paper/Packaging | — |
| 4244 | Wholesale - Grocery/Related | Agriculture, Water & Environmental Technologies |
| 4247 | Wholesale - Petroleum | Energy (Efficiency) & Utilities |
| 4249 | Wholesale - Miscellaneous Nondurable | — |
| 4931 | Transportation - Warehousing/Storage | Advanced Transportation & Renewable Energy |

### Health

| NAICS | Label | Additional sectors |
|---|---|---|
| 3391 | Manufacturing - Medical Equipment | Life Sciences, Advanced Manufacturing |
| 6211 | Healthcare - Physician Offices | — |
| 6212 | Healthcare - Dental | — |
| 6213 | Healthcare - Other Practitioners | — |
| 6214 | Healthcare - Outpatient | — |
| 6215 | Healthcare - Labs | Life Sciences / Biotechnology |
| 6216 | Healthcare - Home Health | — |
| 6219 | Healthcare - Other Ambulatory | — |
| 6221 | Healthcare - Hospitals (General) | — |
| 6222 | Healthcare - Hospitals (Psych/Substance) | — |
| 6223 | Healthcare - Hospitals (Specialty) | — |
| 6231 | Healthcare - Nursing Facilities | — |
| 6232 | Healthcare - Residential Care | — |
| 6233 | Healthcare - Continuing Care | — |

### Information & Communication Technologies (ICT) / Digital Media

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

### Life Sciences / Biotechnology

| NAICS | Label | Additional sectors |
|---|---|---|
| 3254 | Manufacturing - Pharmaceuticals | Advanced Manufacturing |
| 3345 | Manufacturing - Instruments | Advanced Manufacturing |
| 5417 | Professional - Scientific R&D | — |

### Retail/Hospitality/Tourism

| NAICS | Label | Additional sectors |
|---|---|---|
| 4248 | Wholesale - Beer/Wine/Spirits | Agriculture, Water & Environmental Technologies |
| 4411 | Retail - Auto Dealers | — |
| 4441 | Retail - Building Materials | — |
| 4451 | Retail - Grocery Stores | — |
| 4452 | Retail - Specialty Food | — |
| 4461 | Retail - Health/Personal Care | — |
| 4511 | Retail - Sporting Goods/Hobby | — |
| 4521 | Retail - Department Stores | — |
| 4529 | Retail - General Merchandise | — |
| 5616 | Admin - Investigation/Security | — |
| 7131 | Arts - Amusement Parks/Arcades | — |
| 7139 | Arts - Other Amusement/Recreation | — |
| 7211 | Hospitality - Hotels/Motels | — |
| 7212 | Hospitality - RV Parks/Camps | — |
| 7223 | Food Service - Special/Caterers | Small Business |
| 7224 | Food Service - Bars | — |
| 7225 | Food Service - Restaurants | — |

### Small Business

| NAICS | Label | Additional sectors |
|---|---|---|
| 5412 | Professional - Accounting/Tax | — |
| 5413 | Professional - Architecture/Engineering | Advanced Manufacturing |
| 5414 | Professional - Graphic/Industrial Design | — |
| 5416 | Professional - Management/Technical Consulting | — |
| 5418 | Professional - Advertising/PR | — |
| 5617 | Admin - Janitorial/Landscaping | Agriculture, Water & Environmental Technologies |
| 6244 | Social Services - Child Day Care | — |
| 8121 | Services - Personal Care | — |

## What is deliberately excluded

The following NAICS 2-digit sectors have no 4-digit codes in the scrape list. Each exclusion is tied to the absence of an SWP sector that would justify inclusion.

**Finance (NAICS 52)** — Banks, nondepository credit, securities, insurance carriers, insurance agencies. No Doing What Matters sector claims them; Banking and Finance (TOP 050400) carries no sector tag in the LaunchBoard document. Community college CTE programs in finance exist (Business Administration, Accounting) but roll up under Small Business rather than a finance-specific sector; those programs are represented on the industry side via `5412` Accounting.

**Real Estate (NAICS 53)** — Lessors, agents, property management. Real Estate (TOP 051100) carries no SWP sector. Agents and brokers train via standalone licensing pathways outside the community college CTE system.

**Legal Services (NAICS 5411)** — Paralegal (TOP 140200) carries no SWP sector. Law practice is not a community-college-trained profession at the scale that produces SWP partnerships.

**Education (NAICS 61)** — Elementary, secondary, junior colleges, universities, technical schools, other schools. No DWM sector claims the education industry. Educational Aide (TOP 080200) and Special Education (TOP 080900) carry no sector tag. K-12 districts are CTE *teaching* employers, not CTE *hiring* targets in the SWP partnership sense; and private postsecondary institutions are methodologically murky.

**Social Services (partial exclusion, NAICS 6241-6243)** — Individual/family services, emergency relief, vocational rehab. Human Services (TOP 210400) and Disability Services (TOP 210450) carry no SWP sector. `6244` Child Day Care is retained under Small Business because Child Development (TOP 130500) is explicitly tagged Small Business.

**Arts non-recreation (NAICS 7111, 7121)** — Performing arts companies, museums, historical sites. Technical Theater (TOP 100600) and Commercial Dance (TOP 100810) carry no SWP sector, and museums have no TOP code representation at all.

**Religious and Civic Organizations (NAICS 8131, 8134)** — No TOP codes map to these industries; they are not employment targets in the CTE sense.

**General Government Administration (NAICS 9211, 9221, 9222, 9223, 9231)** — Executive/legislative, justice/public order, fire protection, human resource administration, economic program administration. Administration of Justice (TOP 210500), Fire Technology (TOP 213300), Police Academy (TOP 210550) all carry no SWP sector tag. Public Safety is a priority sector in some COE regional plans (`COE_REGION_PRIORITY_SECTORS` in `backend/ontology/regions.py`) but is not a Doing What Matters sector; the methodology in this document anchors to DWM. If Public Safety is added as an eleventh sector in the future, `9221`, `9222`, and the police/fire-adjacent manufacturing codes (armored vehicles, safety equipment) would be reinstated. The only government code retained is `9241` Environmental Quality, which TOP 030300 Environmental Technology explicitly maps to Agriculture, Water & Environmental Technologies.

**Employment and Business Support Services (NAICS 5613, 5614)** — Staffing agencies and call centers. These were excluded in the earlier version of the list and remain excluded: their members place workers at other employers rather than hire onto their own payroll, so they are structurally not partnership targets regardless of sector.

## How to update this mapping

The NAICS dict lives in `backend/employers/edd_scrape.py` as `CTE_NAICS_CODES`. Each entry is `(naicsect, label, [sectors])` where `sectors` is a list of SWP sector names drawn from `SWP_SECTORS` in the same file. The first sector is the primary classification.

To add a NAICS code, add an entry to the dict in the section of the appropriate primary sector, and update the corresponding table above. To remove a code, delete the entry and remove its row from the table.

When a new SWP sector is added to the Doing What Matters framework (for example, a canonical Public Safety sector), add it to `SWP_SECTORS`, add a section to this document, and move or add NAICS codes accordingly. The sector list and the NAICS dict are the two places where sector identity lives; everything else derives from them.

## Related

- [Employer Generation](./employer-generation.md) — the pipeline stage that consumes this NAICS list.
- [AI Integration](../architecture/ai-integration.md) — the Gemini cleanup step that assigns per-employer SOC codes on top of the regional occupation list.
