# LLM Picks vs Top-NAICS Picks: Side-by-Side

For each sample SOC, compares the LLM-curated employer set (from graph HIRES_FOR edges in SD/I + LA) against the top employers under the new methodology (sorted by pct_total of the NAICS each employer sits in). The pct_total column shows what BLS publishes for the (NAICS, SOC) pair — same for every employer in the same NAICS.

**Key question:** When the LLM picks an employer, does that employer sit in the top-pct NAICS for the SOC (LLM is redundant with NAICS) or in a lower-pct NAICS (LLM adds signal NAICS-sort misses)?


## `49-9021` HVAC Mechanics — Strong CTE specialty

**Top NAICS for this SOC**: `4572` at 13.5% pct_total

**LLM-curated picks (SD/I + LA)**: 8 employers

LLM picks grouped by NAICS (with that NAICS's pct_total for this SOC):

| NAICS | NAICS pct_total for SOC | n employers | Sample names |
|---|---:|---:|---|
| `2382` (89% of top) | 12.1% | 8 | Servi-Tek; Pacific Rim Mechanical; Bill Howe Plumbing Heating & Air; AO Reed; Semper Solaris |

Top 10 employers under new method (sort by pct_total desc):

| pct_total | NAICS | Region | Employer | Also picked by LLM? |
|---:|---|:---:|---|:---:|
| 13.5% | 4572 | LA | Jankovich Co |   |
| 12.1% | 2382 | SD | A-AAA Drain Patrol |   |
| 12.1% | 2382 | SD | AO Reed & Co |   |
| 12.1% | 2382 | SD | Apex Mechanical Systems Inc |   |
| 12.1% | 2382 | SD | Ars/Rescue Rooter | ✓ |
| 12.1% | 2382 | SD | Baker Electric Inc |   |
| 12.1% | 2382 | SD | Bay Air Systems |   |
| 12.1% | 2382 | SD | Bergelectric Corp |   |
| 12.1% | 2382 | SD | Bill Howe Plbg Htg-Air |   |
| 12.1% | 2382 | SD | Bradshaw Engineering Corp |   |

**Diagnosis**: Only 0/8 LLM picks (0%) sit in the top-pct NAICS — LLM picks are spread across different NAICS than the top one. **LLM may be adding signal** the NAICS-sort misses.

## `47-2111` Electricians — Strong-CTE-aligned trade

**Top NAICS for this SOC**: `2382` at 21.5% pct_total

**LLM-curated picks (SD/I + LA)**: 11 employers

LLM picks grouped by NAICS (with that NAICS's pct_total for this SOC):

| NAICS | NAICS pct_total for SOC | n employers | Sample names |
|---|---:|---:|---|
| `2382` **TOP** | 21.5% | 7 | Servi-Tek; Bergelectric Corporation; Baker Electric; Semper Solaris; Ars/Rescue Rooter |
| `3366` (14% of top) | 3.1% | 1 | Continental Maritime of San Diego |
| `2371` (9% of top) | 1.9% | 1 | Itron Networked Solutions |
| `3345` (1% of top) | 0.2% | 1 | Honeywell |
| `3332` (0% of top) | 0.0% | 1 | Thyssenkrupp Elevator |

Top 10 employers under new method (sort by pct_total desc):

| pct_total | NAICS | Region | Employer | Also picked by LLM? |
|---:|---|:---:|---|:---:|
| 21.5% | 2382 | SD | A-AAA Drain Patrol |   |
| 21.5% | 2382 | SD | AO Reed & Co |   |
| 21.5% | 2382 | SD | Apex Mechanical Systems Inc |   |
| 21.5% | 2382 | SD | Ars/Rescue Rooter | ✓ |
| 21.5% | 2382 | SD | Baker Electric Inc |   |
| 21.5% | 2382 | SD | Bay Air Systems |   |
| 21.5% | 2382 | SD | Bergelectric Corp |   |
| 21.5% | 2382 | SD | Bill Howe Plbg Htg-Air |   |
| 21.5% | 2382 | SD | Bradshaw Engineering Corp |   |
| 21.5% | 2382 | SD | Carini Home Svc |   |

**Diagnosis**: 7/11 LLM picks (64%) sit in the top-pct NAICS — LLM and NAICS partially overlap; LLM also picks in lower-pct NAICS.

## `23-2011` Paralegals — Strong CTE legal specialty

**Top NAICS for this SOC**: `5411` at 23.0% pct_total

**LLM-curated picks (SD/I + LA)**: 5 employers

LLM picks grouped by NAICS (with that NAICS's pct_total for this SOC):

| NAICS | NAICS pct_total for SOC | n employers | Sample names |
|---|---:|---:|---|
| `5416` (0% of top) | 0.1% | 2 | Pettit Kohn Ingrassia & Lutz PC; Edata Services US |
| `6113` (0% of top) | 0.0% | 1 | California Western School of Law |
| `9221` (0% of top) | 0.0% | 2 | Los Angeles County Superior Court; Court of Appeal |

Top 10 employers under new method (sort by pct_total desc):

| pct_total | NAICS | Region | Employer | Also picked by LLM? |
|---:|---|:---:|---|:---:|
| 23.0% | 5411 | SD | Artiano Shinoff |   |
| 23.0% | 5411 | SD | Bremer Whyte Brown-O'meara LLP |   |
| 23.0% | 5411 | SD | Chicago Title Insurance Co |   |
| 23.0% | 5411 | SD | Clark Hill Plc |   |
| 23.0% | 5411 | SD | Cooley LLP |   |
| 23.0% | 5411 | SD | Daniel Pascucci |   |
| 23.0% | 5411 | SD | Dentons |   |
| 23.0% | 5411 | SD | Dentons US LLP |   |
| 23.0% | 5411 | SD | District Attorney |   |
| 23.0% | 5411 | SD | DLA Piper LLP |   |

**Diagnosis**: Only 0/5 LLM picks (0%) sit in the top-pct NAICS — LLM picks are spread across different NAICS than the top one. **LLM may be adding signal** the NAICS-sort misses.

## `49-3023` Automotive Service Techs — very distinctive

**Top NAICS for this SOC**: `8111` at 23.7% pct_total

**LLM-curated picks (SD/I + LA)**: 35 employers

LLM picks grouped by NAICS (with that NAICS's pct_total for this SOC):

| NAICS | NAICS pct_total for SOC | n employers | Sample names |
|---|---:|---:|---|
| `4411` (84% of top) | 19.8% | 33 | Symbolic Motors; Lexus El Cajon; Lexus Carlsbad; Kearny Mesa Toyota; Kearny Mesa Subaru |
| `4231` (14% of top) | 3.4% | 1 | Manheim San Diego |
| `2389` (0% of top) | 0.0% | 1 | Auto Glass Now |

Top 10 employers under new method (sort by pct_total desc):

| pct_total | NAICS | Region | Employer | Also picked by LLM? |
|---:|---|:---:|---|:---:|
| 23.7% | 8111 | SD | Aj-Usa Inc |   |
| 23.7% | 8111 | SD | Auto Glass Now | ✓ |
| 23.7% | 8111 | SD | Escondido Auto Tint |   |
| 23.7% | 8111 | SD | Mitchell Repair Info Co LLC |   |
| 23.7% | 8111 | SD | Philip Thearle's Autowerks |   |
| 23.7% | 8111 | SD | Renty Collision Ctr |   |
| 23.7% | 8111 | SD | St-Gobain Solar Gard |   |
| 23.7% | 8111 | SD | Symbolic Motors | ✓ |
| 23.7% | 8111 | SD | Toyota Carlsbad Collision Ctr |   |
| 23.7% | 8111 | LA | Agoura Hills Car Wash |   |

**Diagnosis**: Only 0/35 LLM picks (0%) sit in the top-pct NAICS — LLM picks are spread across different NAICS than the top one. **LLM may be adding signal** the NAICS-sort misses.

## `31-9091` Dental Assistants — distinctive medical

**Top NAICS for this SOC**: `6212` at 33.2% pct_total

**LLM-curated picks (SD/I + LA)**: 0 employers

LLM picks grouped by NAICS (with that NAICS's pct_total for this SOC):

| NAICS | NAICS pct_total for SOC | n employers | Sample names |
|---|---:|---:|---|

Top 10 employers under new method (sort by pct_total desc):

| pct_total | NAICS | Region | Employer | Also picked by LLM? |
|---:|---|:---:|---|:---:|
| 33.2% | 6212 | SD | Denticenter |   |
| 33.2% | 6212 | SD | EEA Dental Support Svc |   |
| 33.2% | 6212 | SD | Vista Family Dental |   |
| 33.2% | 6212 | LA | Bellflower Dental Group |   |
| 33.2% | 6212 | LA | Burbank Dental Lab |   |
| 33.2% | 6212 | LA | Burton D Schnierow DDS Inc |   |
| 33.2% | 6212 | LA | CDG Orthodontic Ctr |   |
| 33.2% | 6212 | LA | Children's Dental Building |   |
| 33.2% | 6212 | LA | Children's Dental Group |   |
| 33.2% | 6212 | LA | Dental Health Svc |   |

**Diagnosis**: LLM made no picks for this SOC — new method provides full coverage where LLM had none.

## `29-2061` LVNs — distinctive nursing

**Top NAICS for this SOC**: `6231` at 12.4% pct_total

**LLM-curated picks (SD/I + LA)**: 62 employers

LLM picks grouped by NAICS (with that NAICS's pct_total for this SOC):

| NAICS | NAICS pct_total for SOC | n employers | Sample names |
|---|---:|---:|---|
| `6231` **TOP** | 12.4% | 12 | Covenant Care California; Western Convalescent Hospital; Inland Valley Care and Rehabilitation Cente |
| `6216` (39% of top) | 4.9% | 5 | Elizabeth Hospice; St. Paul's PACE El Cajon; Sharp Home Health and Medical Care; Accent Care; Visiti |
| `6233` (36% of top) | 4.5% | 17 | Silverado Senior Living; Remington Club; Pacifica Senior Living Vista; Lantern Crest Senior Living;  |
| `6214` (24% of top) | 3.0% | 16 | Planned Parenthood; Truecare; Sharp Rees-Stealy Medical Group; Scripps Clinic Urgent Care; Vista Com |
| `6223` (22% of top) | 2.7% | 8 | UCSD Cancer Prevention Center; Select Specialty Hospital San Diego; Kindred Hospital San Diego; USC  |
| `6211` (21% of top) | 2.6% | 3 | Sharp Rees-Stealy Chula Vista; Graybill Medical Group; High Desert Medical Group |
| `6221` (12% of top) | 1.5% | 1 | Prospect Medical Holdings |

Top 10 employers under new method (sort by pct_total desc):

| pct_total | NAICS | Region | Employer | Also picked by LLM? |
|---:|---|:---:|---|:---:|
| 12.4% | 6231 | SD | Accentcare Hospice |   |
| 12.4% | 6231 | SD | Amaya Springs Health Care Ctr |   |
| 12.4% | 6231 | SD | Arbor Hills Nursing Ctr |   |
| 12.4% | 6231 | SD | Arroyo Vista Nursing Ctr |   |
| 12.4% | 6231 | SD | Bonitaview Sharp Hospicecare |   |
| 12.4% | 6231 | SD | Bradley Court |   |
| 12.4% | 6231 | SD | Brighton Place San Diego |   |
| 12.4% | 6231 | SD | Brighton Place Spring Valley |   |
| 12.4% | 6231 | SD | California Hospice Network |   |
| 12.4% | 6231 | SD | Canyon Villas Retirement |   |

**Diagnosis**: Only 12/62 LLM picks (19%) sit in the top-pct NAICS — LLM picks are spread across different NAICS than the top one. **LLM may be adding signal** the NAICS-sort misses.

## `29-2042` EMTs — distinctive emergency

**Top NAICS for this SOC**: `6219` at 23.1% pct_total

**LLM-curated picks (SD/I + LA)**: 3 employers

LLM picks grouped by NAICS (with that NAICS's pct_total for this SOC):

| NAICS | NAICS pct_total for SOC | n employers | Sample names |
|---|---:|---:|---|
| `6219` **TOP** | 23.1% | 1 | American Medical Response |
| `7131` (1% of top) | 0.3% | 1 | Raging Waters Los Angeles |
| `9222` (0% of top) | 0.0% | 1 | Los Angeles County Fire Department |

Top 10 employers under new method (sort by pct_total desc):

| pct_total | NAICS | Region | Employer | Also picked by LLM? |
|---:|---|:---:|---|:---:|
| 23.1% | 6219 | SD | 9AM Health Inc |   |
| 23.1% | 6219 | SD | Aero Medevac |   |
| 23.1% | 6219 | SD | Alliance Health Clinic |   |
| 23.1% | 6219 | SD | American Medical Response | ✓ |
| 23.1% | 6219 | SD | American Red Cross Blood Svc |   |
| 23.1% | 6219 | SD | Arthrosi Therapeutics Inc |   |
| 23.1% | 6219 | SD | Ashcare Virtual Health Inc |   |
| 23.1% | 6219 | SD | Astiva Health |   |
| 23.1% | 6219 | SD | Blue Wave Health Supply LLC |   |
| 23.1% | 6219 | SD | Callison Health Inc |   |

**Diagnosis**: 1/3 LLM picks (33%) sit in the top-pct NAICS — LLM and NAICS partially overlap; LLM also picks in lower-pct NAICS.

## `33-3051` Police — distinctive public safety

**Top NAICS for this SOC**: `9993` at 10.0% pct_total

**LLM-curated picks (SD/I + LA)**: 5 employers

LLM picks grouped by NAICS (with that NAICS's pct_total for this SOC):

| NAICS | NAICS pct_total for SOC | n employers | Sample names |
|---|---:|---:|---|
| `9221` (0% of top) | 0.0% | 5 | Monterey Park Police Department; Long Beach Police Department; Lancaster Sheriff's Office; Los Angel |

Top 10 employers under new method (sort by pct_total desc):

| pct_total | NAICS | Region | Employer | Also picked by LLM? |
|---:|---|:---:|---|:---:|
| 6.3% | 9221 | SD | California Department-Forestry |   |
| 6.3% | 9221 | SD | Campo Fire & Rescue |   |
| 6.3% | 9221 | SD | Carlsbad Police Dept |   |
| 6.3% | 9221 | SD | Chula Vista Fire Dept Sta 1 |   |
| 6.3% | 9221 | SD | Chula Vista Fire Dept Sta 2 |   |
| 6.3% | 9221 | SD | Chula Vista Police Dept |   |
| 6.3% | 9221 | SD | Chula Vista Police Dept-Crimes |   |
| 6.3% | 9221 | SD | City-Sn Diego Fire-Rescue Dept |   |
| 6.3% | 9221 | SD | Coronado Fire Dept |   |
| 6.3% | 9221 | SD | Coronado Police Dept |   |

**Diagnosis**: Only 0/5 LLM picks (0%) sit in the top-pct NAICS — LLM picks are spread across different NAICS than the top one. **LLM may be adding signal** the NAICS-sort misses.

## `15-1232` Computer User Support — moderate

**Top NAICS for this SOC**: `5415` at 6.2% pct_total

**LLM-curated picks (SD/I + LA)**: 0 employers

LLM picks grouped by NAICS (with that NAICS's pct_total for this SOC):

| NAICS | NAICS pct_total for SOC | n employers | Sample names |
|---|---:|---:|---|

Top 10 employers under new method (sort by pct_total desc):

| pct_total | NAICS | Region | Employer | Also picked by LLM? |
|---:|---|:---:|---|:---:|
| 6.2% | 5415 | SD | 101DOMAIN Inc |   |
| 6.2% | 5415 | SD | Boldbuild-Construction Mgmt |   |
| 6.2% | 5415 | SD | CACI Inc |   |
| 6.2% | 5415 | SD | CHC Consulting LLC |   |
| 6.2% | 5415 | SD | Cirrascale Corp |   |
| 6.2% | 5415 | SD | Corporate Technologies LLC |   |
| 6.2% | 5415 | SD | Data 911 |   |
| 6.2% | 5415 | SD | Epsilon Systems Solutions Inc |   |
| 6.2% | 5415 | SD | EVOTEK Inc |   |
| 6.2% | 5415 | SD | Fair Isaac Corp |   |

**Diagnosis**: LLM made no picks for this SOC — new method provides full coverage where LLM had none.

## `13-2011` Accountants — cross-cutting bachelor's

**Top NAICS for this SOC**: `5412` at 31.7% pct_total

**LLM-curated picks (SD/I + LA)**: 9 employers

LLM picks grouped by NAICS (with that NAICS's pct_total for this SOC):

| NAICS | NAICS pct_total for SOC | n employers | Sample names |
|---|---:|---:|---|
| `5412` **TOP** | 31.7% | 8 | KPMG; Paychex; Deloitte Tax LLP; EY; KPMG |
| `5416` (7% of top) | 2.3% | 1 | Pettit Kohn Ingrassia & Lutz PC |

Top 10 employers under new method (sort by pct_total desc):

| pct_total | NAICS | Region | Employer | Also picked by LLM? |
|---:|---|:---:|---|:---:|
| 31.7% | 5412 | SD | 99TEN Business Solutions |   |
| 31.7% | 5412 | SD | Abeo Management Corp |   |
| 31.7% | 5412 | SD | Considine & Considine |   |
| 31.7% | 5412 | SD | CSC Tci |   |
| 31.7% | 5412 | SD | Deloitte Tax LLP | ✓ |
| 31.7% | 5412 | SD | Eisneramper |   |
| 31.7% | 5412 | SD | EY | ✓ |
| 31.7% | 5412 | SD | KPMG | ✓ |
| 31.7% | 5412 | SD | Lavine Lofgren Morris |   |
| 31.7% | 5412 | SD | Moss Adams LLP |   |

**Diagnosis**: 8/9 LLM picks (89%) sit in the top-pct NAICS — LLM is **largely redundant** with NAICS-based selection.
