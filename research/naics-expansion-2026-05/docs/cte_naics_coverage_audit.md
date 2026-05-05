# CTE NAICS Search-Space Audit

Diagnostic: for each CTE-classified SOC in the ontology, BLS OEWS publishes a ranked list of NAICS-4 industries that employ the occupation, weighted by pct_total. The project's employer scrape uses a curated NAICS list (`CTE_NAICS_CODES` in `backend/employers/edd_scrape.py`, documented at `docs/pipeline/swp-sector-naics.md`). This audit asks: are the top-5 NAICS for each CTE SOC in the search list, and are the high-affinity NAICS (≥5.0% pct_total) covered?

## Universe

- CTE-classified Occupation nodes in graph: **506**
- Direct-CTE band (Strong + Moderate entry-level): **343**
  - Strong CTE (postsecondary nondegree / associate's): 98
  - Moderate CTE (HS / some college / no credential): 245
- Direct-CTE SOCs with ≥1 NAICS published by BLS: **343**
- NAICS-4 codes in `CTE_NAICS_CODES`: **140**

## Coverage of top NAICS for direct-CTE SOCs

For each direct-CTE SOC with at least one BLS-published NAICS, what fraction of its top-5 NAICS appear in our search list?

| Coverage of top-N | SOCs |
|---|---:|
| All top-5 in search list | 41 |
| Most (≥60%) in search list | 123 |
| Some (20-60%) in search list | 134 |
| Only one in search list | 0 |
| None in search list | 45 |

**Aggregate top-5 coverage rate: 49.0% (790/1612 top-NAICS pairs in search list)**

**High-affinity (≥5.0%) coverage: 43.1% (149/346 high-affinity NAICS in search list across 137 CTE SOCs that have any high-affinity NAICS)**

---

## Per-SOC: top-5 NAICS for every direct-CTE SOC

For each direct-CTE SOC, lists the top-5 NAICS by pct_total. `✓` = NAICS is in the search list; blank = NAICS is NOT in the search list (potential expansion target).


### `11-3071` Transportation, Storage, and Distribution Managers
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 0/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 2.3% | 4885 |   |  |
| 2.1% | 5321 |   |  |
| 1.6% | 4831 |   |  |
| 1.5% | 4832 |   |  |
| 1.4% | 4883 |   |  |

### `11-9013` Farmers, Ranchers, and Other Agricultural Managers
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 4/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 1.6% | 1152 | ✓ | Agriculture - Animal Support |
| 0.6% | 1151 | ✓ | Agriculture - Crop Support |
| 0.2% | 4245 | ✓ | Wholesale - Farm Products |
| 0.1% | 3111 | ✓ | Manufacturing - Animal Food |
| 0.1% | 8133 |   |  |

### `11-9051` Food Service Managers
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 4/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 2.3% | 7223 | ✓ | Food Service - Special/Caterers |
| 1.7% | 7225 | ✓ | Food Service - Restaurants |
| 1.0% | 7224 | ✓ | Food Service - Bars |
| 0.6% | 7211 | ✓ | Hospitality - Hotels/Motels |
| 0.4% | 4872 |   |  |

### `11-9071` Gambling Managers
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 1/3*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 1.0% | 7132 |   |  |
| 0.1% | 7211 | ✓ | Hospitality - Hotels/Motels |
| 0.1% | 7112 |   |  |

### `11-9081` Lodging Managers
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 2/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 2.2% | 7213 |   |  |
| 2.0% | 7212 | ✓ | Hospitality - RV Parks/Camps |
| 2.0% | 7211 | ✓ | Hospitality - Hotels/Motels |
| 0.3% | 4831 |   |  |
| 0.1% | 5611 |   |  |

### `11-9131` Postmasters and Mail Superintendents
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 0/1*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 2.2% | 4911 |   |  |

### `11-9141` Property, Real Estate, and Community Association Managers
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 0/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 12.7% | 5310 |   |  |
| 4.2% | 2372 |   |  |
| 2.0% | 5259 |   |  |
| 1.2% | 8139 |   |  |
| 1.2% | 7213 |   |  |

### `13-1031` Claims Adjusters, Examiners, and Investigators
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 0/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 9.4% | 5241 |   |  |
| 7.5% | 5242 |   |  |
| 4.3% | 5251 |   |  |
| 2.2% | 9991 |   |  |
| 0.4% | 9992 |   |  |

### `13-2082` Tax Preparers
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 2/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 7.1% | 5412 | ✓ | Professional - Accounting/Tax |
| 0.1% | 5411 |   |  |
| 0.1% | 5132 |   |  |
| 0.1% | 5230 |   |  |
| 0.0% | 5416 | ✓ | Professional - Management/Technical Consulting |

### `15-1232` Computer User Support Specialists
*Moderate CTE · Some college, no degree · top-5 coverage: 3/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 6.2% | 5415 | ✓ | Professional - Computer Systems Design |
| 4.4% | 5132 |   |  |
| 4.4% | 5182 | ✓ | IT - Data Processing/Hosting |
| 3.3% | 4234 | ✓ | Wholesale - Professional Equipment |
| 2.9% | 8112 |   |  |

### `17-3031` Surveying and Mapping Technicians
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 3/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 2.1% | 5413 | ✓ | Professional - Architecture/Engineering |
| 1.0% | 5619 |   |  |
| 0.4% | 2212 | ✓ | Utilities - Natural Gas |
| 0.2% | 2111 | ✓ | Mining - Oil/Gas Extraction |
| 0.1% | 2121 |   |  |

### `19-5012` Occupational Health and Safety Technicians
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 3/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 0.3% | 4931 | ✓ | Transportation - Warehousing/Storage |
| 0.3% | 2121 |   |  |
| 0.3% | 3241 | ✓ | Manufacturing - Petroleum/Coal |
| 0.2% | 3366 | ✓ | Manufacturing - Ship/Boat |
| 0.2% | 2122 |   |  |

### `21-1093` Social and Human Service Assistants
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 3/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 15.7% | 6242 | ✓ | Social Services - Community Emergency Relief |
| 7.3% | 6239 |   |  |
| 7.0% | 8133 |   |  |
| 4.5% | 6232 | ✓ | Healthcare - Residential Care |
| 4.3% | 6243 | ✓ | Social Services - Vocational Rehab |

### `21-1094` Community Health Workers
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 3/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 0.8% | 8132 |   |  |
| 0.8% | 8133 |   |  |
| 0.7% | 6242 | ✓ | Social Services - Community Emergency Relief |
| 0.5% | 6214 | ✓ | Healthcare - Outpatient |
| 0.3% | 6241 | ✓ | Social Services - Individual/Family |

### `23-2093` Title Examiners, Abstractors, and Searchers
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 1/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 1.8% | 5411 |   |  |
| 1.2% | 5241 |   |  |
| 0.5% | 2111 | ✓ | Mining - Oil/Gas Extraction |
| 0.2% | 5259 |   |  |
| 0.2% | 5619 |   |  |

### `27-1012` Craft Artists
*Moderate CTE · No formal educational credential · top-5 coverage: 1/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 2.3% | 7115 |   |  |
| 0.2% | 4591 |   |  |
| 0.1% | 5414 | ✓ | Professional - Graphic/Industrial Design |
| 0.1% | 3399 |   |  |
| 0.1% | 7111 |   |  |

### `27-1019` Artists and Related Workers, All Other
*Moderate CTE · No formal educational credential · top-5 coverage: 2/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 0.5% | 7115 |   |  |
| 0.2% | 5121 | ✓ | Media - Motion Picture/Video |
| 0.1% | 9991 |   |  |
| 0.1% | 8121 | ✓ | Services - Personal Care |
| 0.1% | 4591 |   |  |

### `27-2011` Actors
*Moderate CTE · Some college, no degree · top-5 coverage: 3/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 4.9% | 7111 |   |  |
| 3.9% | 5121 | ✓ | Media - Motion Picture/Video |
| 2.9% | 7131 | ✓ | Arts - Amusement Parks/Arcades |
| 1.6% | 5412 | ✓ | Professional - Accounting/Tax |
| 0.3% | 7121 |   |  |

### `27-2021` Athletes and Sports Competitors
*Moderate CTE · No formal educational credential · top-5 coverage: 1/4*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 8.5% | 7112 |   |  |
| 0.2% | 7113 |   |  |
| 0.1% | 7139 | ✓ | Arts - Other Amusement/Recreation |
| 0.0% | 8139 |   |  |

### `27-2031` Dancers
*Moderate CTE · No formal educational credential · top-5 coverage: 2/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 2.5% | 7111 |   |  |
| 1.0% | 7224 | ✓ | Food Service - Bars |
| 0.3% | 7112 |   |  |
| 0.1% | 7113 |   |  |
| 0.1% | 7139 | ✓ | Arts - Other Amusement/Recreation |

### `27-2032` Choreographers
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 1/2*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 0.9% | 7111 |   |  |
| 0.4% | 6116 | ✓ | Education - Other Schools |

### `27-2042` Musicians and Singers
*Moderate CTE · No formal educational credential · top-5 coverage: 0/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 15.8% | 7111 |   |  |
| 3.3% | 8131 |   |  |
| 1.1% | 7115 |   |  |
| 0.6% | 7113 |   |  |
| 0.3% | 4872 |   |  |

### `27-2091` Disc Jockeys, Except Radio
*Moderate CTE · No formal educational credential · top-5 coverage: 1/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 4.0% | 7115 |   |  |
| 0.5% | 7224 | ✓ | Food Service - Bars |
| 0.2% | 5161 |   |  |
| 0.1% | 7113 |   |  |
| 0.1% | 7112 |   |  |

### `27-2099` Entertainers and Performers, Sports and Related Workers, All Other
*Moderate CTE · No formal educational credential · top-5 coverage: 2/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 2.3% | 7115 |   |  |
| 1.5% | 7111 |   |  |
| 1.1% | 7112 |   |  |
| 1.0% | 7131 | ✓ | Arts - Amusement Parks/Arcades |
| 0.6% | 5121 | ✓ | Media - Motion Picture/Video |

### `27-3099` Media and Communication Workers, All Other
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 2/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 1.6% | 5121 | ✓ | Media - Motion Picture/Video |
| 1.3% | 5161 |   |  |
| 0.5% | 5162 |   |  |
| 0.4% | 7111 |   |  |
| 0.3% | 5418 | ✓ | Professional - Advertising/PR |

### `27-4015` Lighting Technicians
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 2/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 1.9% | 7115 |   |  |
| 0.6% | 7111 |   |  |
| 0.6% | 5121 | ✓ | Media - Motion Picture/Video |
| 0.4% | 7113 |   |  |
| 0.2% | 5414 | ✓ | Professional - Graphic/Industrial Design |

### `27-4021` Photographers
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 0/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 3.1% | 5419 |   |  |
| 1.5% | 5161 |   |  |
| 0.9% | 5162 |   |  |
| 0.5% | 5131 |   |  |
| 0.3% | 4812 |   |  |

### `29-2052` Pharmacy Technicians
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 3/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 21.4% | 4561 |   |  |
| 1.3% | 4550 |   |  |
| 1.2% | 6221 | ✓ | Healthcare - Hospitals (General) |
| 1.1% | 6223 | ✓ | Healthcare - Hospitals (Specialty) |
| 0.7% | 6214 | ✓ | Healthcare - Outpatient |

### `29-2081` Opticians, Dispensing
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 3/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 2.8% | 6213 | ✓ | Healthcare - Other Practitioners |
| 1.7% | 4561 |   |  |
| 0.5% | 4550 |   |  |
| 0.3% | 6211 | ✓ | Healthcare - Physician Offices |
| 0.1% | 6214 | ✓ | Healthcare - Outpatient |

### `31-1133` Psychiatric Aides
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 3/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 5.3% | 6222 | ✓ | Healthcare - Hospitals (Psych/Substance) |
| 0.4% | 6232 | ✓ | Healthcare - Residential Care |
| 0.3% | 9992 |   |  |
| 0.3% | 6239 |   |  |
| 0.2% | 6223 | ✓ | Healthcare - Hospitals (Specialty) |

### `31-2012` Occupational Therapy Aides
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 5/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 0.2% | 6223 | ✓ | Healthcare - Hospitals (Specialty) |
| 0.1% | 6213 | ✓ | Healthcare - Other Practitioners |
| 0.0% | 6231 | ✓ | Healthcare - Nursing Facilities |
| 0.0% | 6211 | ✓ | Healthcare - Physician Offices |
| 0.0% | 6216 | ✓ | Healthcare - Home Health |

### `31-2022` Physical Therapist Aides
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 5/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 2.5% | 6213 | ✓ | Healthcare - Other Practitioners |
| 0.5% | 6223 | ✓ | Healthcare - Hospitals (Specialty) |
| 0.1% | 6211 | ✓ | Healthcare - Physician Offices |
| 0.1% | 6221 | ✓ | Healthcare - Hospitals (General) |
| 0.1% | 6231 | ✓ | Healthcare - Nursing Facilities |

### `31-9093` Medical Equipment Preparers
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 5/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 0.8% | 6221 | ✓ | Healthcare - Hospitals (General) |
| 0.5% | 6212 | ✓ | Healthcare - Dental |
| 0.4% | 6214 | ✓ | Healthcare - Outpatient |
| 0.3% | 6223 | ✓ | Healthcare - Hospitals (Specialty) |
| 0.2% | 6219 | ✓ | Healthcare - Other Ambulatory |

### `31-9096` Veterinary Assistants and Laboratory Animal Caretakers
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 2/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 12.4% | 5419 |   |  |
| 0.6% | 8133 |   |  |
| 0.2% | 8129 |   |  |
| 0.2% | 5417 | ✓ | Professional - Scientific R&D |
| 0.1% | 6113 | ✓ | Education - Colleges/Universities |

### `31-9099` Healthcare Support Workers, All Other
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 4/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 1.4% | 6219 | ✓ | Healthcare - Other Ambulatory |
| 1.1% | 6215 | ✓ | Healthcare - Labs |
| 0.7% | 9991 |   |  |
| 0.6% | 6222 | ✓ | Healthcare - Hospitals (Psych/Substance) |
| 0.6% | 6213 | ✓ | Healthcare - Other Practitioners |

### `33-1011` First-Line Supervisors of Correctional Officers
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 1/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 1.6% | 9992 |   |  |
| 0.8% | 5612 |   |  |
| 0.3% | 9993 |   |  |
| 0.1% | 9991 |   |  |
| 0.0% | 6222 | ✓ | Healthcare - Hospitals (Psych/Substance) |

### `33-1012` First-Line Supervisors of Police and Detectives
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 2/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 2.0% | 9993 |   |  |
| 0.7% | 9992 |   |  |
| 0.3% | 9991 |   |  |
| 0.1% | 6113 | ✓ | Education - Colleges/Universities |
| 0.1% | 6112 | ✓ | Education - Junior Colleges |

### `33-1091` First-Line Supervisors of Security Workers
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 1/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 2.9% | 5616 | ✓ | Admin - Investigation/Security |
| 1.2% | 5211 |   |  |
| 1.1% | 7132 |   |  |
| 0.8% | 7113 |   |  |
| 0.5% | 7121 |   |  |

### `33-1099` First-Line Supervisors of Protective Service Workers, All Other
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 1/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 0.4% | 5619 |   |  |
| 0.2% | 9991 |   |  |
| 0.2% | 7132 |   |  |
| 0.2% | 5211 |   |  |
| 0.1% | 7139 | ✓ | Arts - Other Amusement/Recreation |

### `33-2022` Forest Fire Inspectors and Prevention Specialists
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 0/2*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 0.1% | 9992 |   |  |
| 0.0% | 9993 |   |  |

### `33-3011` Bailiffs
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 0/2*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 0.3% | 9992 |   |  |
| 0.2% | 9993 |   |  |

### `33-3012` Correctional Officers and Jailers
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 1/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 8.6% | 9992 |   |  |
| 7.4% | 5612 |   |  |
| 2.5% | 9993 |   |  |
| 0.6% | 9991 |   |  |
| 0.2% | 6222 | ✓ | Healthcare - Hospitals (Psych/Substance) |

### `33-3021` Detectives and Criminal Investigators
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 1/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 1.9% | 9991 |   |  |
| 1.0% | 9992 |   |  |
| 0.8% | 9993 |   |  |
| 0.1% | 4911 |   |  |
| 0.0% | 6222 | ✓ | Healthcare - Hospitals (Psych/Substance) |

### `33-3051` Police and Sheriff's Patrol Officers
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 2/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 10.0% | 9993 |   |  |
| 2.6% | 9992 |   |  |
| 0.6% | 6112 | ✓ | Education - Junior Colleges |
| 0.6% | 9991 |   |  |
| 0.5% | 6113 | ✓ | Education - Colleges/Universities |

### `33-3052` Transit and Railroad Police
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 0/3*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 0.2% | 4821 |   |  |
| 0.0% | 9993 |   |  |
| 0.0% | 9992 |   |  |

### `33-9021` Private Detectives and Investigators
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 1/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 0.3% | 4550 |   |  |
| 0.1% | 5411 |   |  |
| 0.1% | 4921 | ✓ | Transportation - Couriers/Express Delivery |
| 0.1% | 5511 |   |  |
| 0.1% | 9992 |   |  |

### `33-9031` Gambling Surveillance Officers and Gambling Investigators
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 1/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 2.2% | 7132 |   |  |
| 0.1% | 7112 |   |  |
| 0.1% | 7211 | ✓ | Hospitality - Hotels/Motels |
| 0.0% | 9992 |   |  |
| 0.0% | 9993 |   |  |

### `33-9032` Security Guards
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 2/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 73.7% | 5616 | ✓ | Admin - Investigation/Security |
| 6.6% | 7113 |   |  |
| 5.9% | 7132 |   |  |
| 5.5% | 5211 |   |  |
| 4.4% | 7224 | ✓ | Food Service - Bars |

### `33-9092` Lifeguards, Ski Patrol, and Other Recreational Protective Service Workers
*Moderate CTE · No formal educational credential · top-5 coverage: 3/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 5.0% | 8134 |   |  |
| 3.2% | 7131 | ✓ | Arts - Amusement Parks/Arcades |
| 2.4% | 7139 | ✓ | Arts - Other Amusement/Recreation |
| 0.8% | 9993 |   |  |
| 0.7% | 7212 | ✓ | Hospitality - RV Parks/Camps |

### `35-1011` Chefs and Head Cooks
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 4/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 2.6% | 7223 | ✓ | Food Service - Special/Caterers |
| 1.0% | 7211 | ✓ | Hospitality - Hotels/Motels |
| 0.9% | 7213 |   |  |
| 0.8% | 7225 | ✓ | Food Service - Restaurants |
| 0.7% | 7139 | ✓ | Arts - Other Amusement/Recreation |

### `35-1012` First-Line Supervisors of Food Preparation and Serving Workers
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 5/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 8.3% | 7225 | ✓ | Food Service - Restaurants |
| 6.4% | 7223 | ✓ | Food Service - Special/Caterers |
| 5.8% | 7224 | ✓ | Food Service - Bars |
| 1.6% | 3121 | ✓ | Manufacturing - Beverages |
| 1.4% | 7211 | ✓ | Hospitality - Hotels/Motels |

### `35-2012` Cooks, Institution and Cafeteria
*Moderate CTE · No formal educational credential · top-5 coverage: 4/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 9.3% | 7223 | ✓ | Food Service - Special/Caterers |
| 5.0% | 7213 |   |  |
| 4.9% | 6233 | ✓ | Healthcare - Continuing Care |
| 3.4% | 6231 | ✓ | Healthcare - Nursing Facilities |
| 2.1% | 6244 | ✓ | Social Services - Child Day Care |

### `35-2014` Cooks, Restaurant
*Moderate CTE · No formal educational credential · top-5 coverage: 4/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 11.0% | 7225 | ✓ | Food Service - Restaurants |
| 9.4% | 7224 | ✓ | Food Service - Bars |
| 3.8% | 7211 | ✓ | Hospitality - Hotels/Motels |
| 3.4% | 7132 |   |  |
| 3.1% | 7223 | ✓ | Food Service - Special/Caterers |

### `35-2019` Cooks, All Other
*Moderate CTE · No formal educational credential · top-5 coverage: 2/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 4.5% | 7213 |   |  |
| 0.5% | 7223 | ✓ | Food Service - Special/Caterers |
| 0.2% | 4872 |   |  |
| 0.2% | 3119 | ✓ | Manufacturing - Other Food |
| 0.1% | 3113 |   |  |

### `37-1011` First-Line Supervisors of Housekeeping and Janitorial Workers
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 3/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 2.7% | 5617 | ✓ | Admin - Janitorial/Landscaping |
| 2.1% | 7211 | ✓ | Hospitality - Hotels/Motels |
| 1.8% | 5612 |   |  |
| 1.1% | 7213 |   |  |
| 0.6% | 7212 | ✓ | Hospitality - RV Parks/Camps |

### `37-1012` First-Line Supervisors of Landscaping, Lawn Service, and Groundskeeping Workers
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 3/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 3.8% | 5617 | ✓ | Admin - Janitorial/Landscaping |
| 1.2% | 8122 |   |  |
| 0.8% | 7139 | ✓ | Arts - Other Amusement/Recreation |
| 0.6% | 4442 |   |  |
| 0.5% | 7212 | ✓ | Hospitality - RV Parks/Camps |

### `37-3011` Landscaping and Groundskeeping Workers
*Moderate CTE · No formal educational credential · top-5 coverage: 3/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 25.1% | 5617 | ✓ | Admin - Janitorial/Landscaping |
| 9.2% | 8122 |   |  |
| 6.5% | 7212 | ✓ | Hospitality - RV Parks/Camps |
| 6.5% | 7139 | ✓ | Arts - Other Amusement/Recreation |
| 4.0% | 4442 |   |  |

### `37-3012` Pesticide Handlers, Sprayers, and Applicators, Vegetation
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 4/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 1.1% | 4245 | ✓ | Wholesale - Farm Products |
| 0.6% | 1151 | ✓ | Agriculture - Crop Support |
| 0.6% | 5617 | ✓ | Admin - Janitorial/Landscaping |
| 0.2% | 4442 |   |  |
| 0.0% | 7139 | ✓ | Arts - Other Amusement/Recreation |

### `39-1013` First-Line Supervisors of Gambling Services Workers
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 1/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 4.8% | 7132 |   |  |
| 0.7% | 7211 | ✓ | Hospitality - Hotels/Motels |
| 0.3% | 7112 |   |  |
| 0.0% | 8134 |   |  |
| 0.0% | 8139 |   |  |

### `39-1022` First-Line Supervisors of Personal Service Workers
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 2/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 3.3% | 8121 | ✓ | Services - Personal Care |
| 2.9% | 8129 |   |  |
| 1.3% | 6239 |   |  |
| 1.1% | 6244 | ✓ | Social Services - Child Day Care |
| 0.7% | 8134 |   |  |

### `39-2011` Animal Trainers
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 1/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 6.0% | 1152 | ✓ | Agriculture - Animal Support |
| 2.1% | 8129 |   |  |
| 1.3% | 7112 |   |  |
| 0.7% | 4599 |   |  |
| 0.2% | 7121 |   |  |

### `39-2021` Animal Caretakers
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 1/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 33.4% | 8129 |   |  |
| 19.9% | 1152 | ✓ | Agriculture - Animal Support |
| 8.7% | 4599 |   |  |
| 4.8% | 7112 |   |  |
| 4.7% | 7121 |   |  |

### `39-5093` Shampooers
*Moderate CTE · No formal educational credential · top-5 coverage: 1/1*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 1.0% | 8121 | ✓ | Services - Personal Care |

### `39-6012` Concierges
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 2/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 1.0% | 8129 |   |  |
| 0.7% | 6233 | ✓ | Healthcare - Continuing Care |
| 0.6% | 5310 |   |  |
| 0.4% | 5612 |   |  |
| 0.4% | 7211 | ✓ | Hospitality - Hotels/Motels |

### `39-9011` Childcare Workers
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 2/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 28.6% | 6244 | ✓ | Social Services - Child Day Care |
| 6.4% | 6239 |   |  |
| 6.4% | 8134 |   |  |
| 2.4% | 8131 |   |  |
| 2.0% | 7139 | ✓ | Arts - Other Amusement/Recreation |

### `39-9031` Exercise Trainers and Group Fitness Instructors
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 2/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 13.8% | 7139 | ✓ | Arts - Other Amusement/Recreation |
| 7.3% | 8134 |   |  |
| 2.0% | 8129 |   |  |
| 0.4% | 7112 |   |  |
| 0.3% | 6115 | ✓ | Education - Technical/Trade Schools |

### `41-1011` First-Line Supervisors of Retail Sales Workers
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 0/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 13.2% | 4582 |   |  |
| 12.0% | 4453 |   |  |
| 10.9% | 4571 |   |  |
| 9.7% | 4581 |   |  |
| 9.1% | 4592 |   |  |

### `41-1012` First-Line Supervisors of Non-Retail Sales Workers
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 0/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 3.8% | 4492 |   |  |
| 1.9% | 5615 |   |  |
| 1.8% | 5170 |   |  |
| 1.2% | 4251 |   |  |
| 1.1% | 4238 |   |  |

### `41-2022` Parts Salespersons
*Moderate CTE · No formal educational credential · top-5 coverage: 2/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 20.1% | 4413 |   |  |
| 6.9% | 4412 |   |  |
| 5.9% | 4231 | ✓ | Wholesale - Motor Vehicles/Parts |
| 4.4% | 4411 | ✓ | Retail - Auto Dealers |
| 3.2% | 4238 |   |  |

### `41-3011` Advertising Sales Agents
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 1/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 10.4% | 5161 |   |  |
| 9.8% | 5418 | ✓ | Professional - Advertising/PR |
| 6.7% | 5131 |   |  |
| 3.0% | 5162 |   |  |
| 1.9% | 5192 |   |  |

### `41-3021` Insurance Sales Agents
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 0/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 26.6% | 5242 |   |  |
| 6.5% | 5241 |   |  |
| 3.4% | 5251 |   |  |
| 1.4% | 5615 |   |  |
| 0.1% | 5230 |   |  |

### `41-3041` Travel Agents
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 1/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 25.4% | 5615 |   |  |
| 3.3% | 4831 |   |  |
| 1.5% | 4871 |   |  |
| 0.5% | 4812 |   |  |
| 0.0% | 4811 | ✓ | Transportation - Air |

### `41-3091` Sales Representatives of Services, Except Advertising, Insurance, Financial Services, and Travel
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 0/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 16.3% | 4492 |   |  |
| 12.2% | 5170 |   |  |
| 8.9% | 5331 |   |  |
| 8.2% | 4885 |   |  |
| 6.7% | 5192 |   |  |

### `41-4012` Sales Representatives, Wholesale and Manufacturing, Except Technical and Scientific Products
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 2/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 25.9% | 4251 |   |  |
| 14.8% | 4238 |   |  |
| 11.7% | 4243 |   |  |
| 8.2% | 4231 | ✓ | Wholesale - Motor Vehicles/Parts |
| 6.6% | 4234 | ✓ | Wholesale - Professional Equipment |

### `41-9011` Demonstrators and Product Promoters
*Moderate CTE · No formal educational credential · top-5 coverage: 3/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 3.4% | 3121 | ✓ | Manufacturing - Beverages |
| 2.6% | 5418 | ✓ | Professional - Advertising/PR |
| 0.2% | 4251 |   |  |
| 0.2% | 5416 | ✓ | Professional - Management/Technical Consulting |
| 0.1% | 5613 |   |  |

### `41-9021` Real Estate Brokers
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 1/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 2.6% | 5310 |   |  |
| 0.6% | 5259 |   |  |
| 0.3% | 2372 |   |  |
| 0.1% | 2361 | ✓ | Construction - Residential |
| 0.0% | 5222 |   |  |

### `41-9022` Real Estate Sales Agents
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 3/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 8.9% | 5310 |   |  |
| 3.2% | 2372 |   |  |
| 1.4% | 2111 | ✓ | Mining - Oil/Gas Extraction |
| 1.1% | 2361 | ✓ | Construction - Residential |
| 0.2% | 2212 | ✓ | Utilities - Natural Gas |

### `41-9099` Sales and Related Workers, All Other
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 1/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 1.6% | 5222 |   |  |
| 0.9% | 5619 |   |  |
| 0.8% | 4245 | ✓ | Wholesale - Farm Products |
| 0.7% | 4599 |   |  |
| 0.6% | 7112 |   |  |

### `43-1011` First-Line Supervisors of Office and Administrative Support Workers
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 1/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 4.8% | 4885 |   |  |
| 4.5% | 5614 |   |  |
| 4.2% | 6212 | ✓ | Healthcare - Dental |
| 3.6% | 5222 |   |  |
| 3.5% | 5611 |   |  |

### `43-2099` Communications Equipment Operators, All Other
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 0/2*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 0.0% | 9991 |   |  |
| 0.0% | 9993 |   |  |

### `43-3011` Bill and Account Collectors
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 1/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 6.2% | 5614 |   |  |
| 3.5% | 5222 |   |  |
| 0.8% | 5611 |   |  |
| 0.6% | 5412 | ✓ | Professional - Accounting/Tax |
| 0.5% | 5511 |   |  |

### `43-3031` Bookkeeping, Accounting, and Auditing Clerks
*Moderate CTE · Some college, no degree · top-5 coverage: 2/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 8.9% | 5412 | ✓ | Professional - Accounting/Tax |
| 5.0% | 5611 |   |  |
| 4.1% | 5251 |   |  |
| 3.9% | 5331 |   |  |
| 3.6% | 5122 | ✓ | Media - Sound Recording |

### `43-3041` Gambling Cage Workers
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 1/3*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 3.2% | 7132 |   |  |
| 0.3% | 7112 |   |  |
| 0.3% | 7211 | ✓ | Hospitality - Hotels/Motels |

### `43-3051` Payroll and Timekeeping Clerks
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 1/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 1.6% | 5412 | ✓ | Professional - Accounting/Tax |
| 0.7% | 5611 |   |  |
| 0.5% | 5511 |   |  |
| 0.4% | 4852 |   |  |
| 0.4% | 5331 |   |  |

### `43-3061` Procurement Clerks
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 1/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 1.6% | 4243 |   |  |
| 0.4% | 9991 |   |  |
| 0.2% | 3351 | ✓ | Manufacturing - Electrical Equipment |
| 0.2% | 3152 |   |  |
| 0.1% | 3333 |   |  |

### `43-3071` Tellers
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 2/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 0.6% | 5222 |   |  |
| 0.3% | 5230 |   |  |
| 0.2% | 5616 | ✓ | Admin - Investigation/Security |
| 0.1% | 5511 |   |  |
| 0.0% | 5182 | ✓ | IT - Data Processing/Hosting |

### `43-4011` Brokerage Clerks
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 0/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 3.0% | 5230 |   |  |
| 0.1% | 5222 |   |  |
| 0.1% | 5242 |   |  |
| 0.1% | 4885 |   |  |
| 0.0% | 5511 |   |  |

### `43-4021` Correspondence Clerks
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 2/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 0.0% | 4411 | ✓ | Retail - Auto Dealers |
| 0.0% | 5241 |   |  |
| 0.0% | 5511 |   |  |
| 0.0% | 5611 |   |  |
| 0.0% | 5182 | ✓ | IT - Data Processing/Hosting |

### `43-4041` Credit Authorizers, Checkers, and Clerks
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 0/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 0.4% | 5222 |   |  |
| 0.2% | 4491 |   |  |
| 0.1% | 5614 |   |  |
| 0.1% | 4412 |   |  |
| 0.1% | 5511 |   |  |

### `43-4051` Customer Service Representatives
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 0/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 35.9% | 5614 |   |  |
| 14.6% | 4831 |   |  |
| 11.7% | 5242 |   |  |
| 10.6% | 5241 |   |  |
| 8.4% | 5251 |   |  |

### `43-4071` File Clerks
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 1/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 0.9% | 5411 |   |  |
| 0.4% | 5611 |   |  |
| 0.3% | 5182 | ✓ | IT - Data Processing/Hosting |
| 0.3% | 9993 |   |  |
| 0.2% | 3315 |   |  |

### `43-4131` Loan Interviewers and Clerks
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 0/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 11.6% | 5222 |   |  |
| 0.6% | 5241 |   |  |
| 0.6% | 5259 |   |  |
| 0.5% | 5411 |   |  |
| 0.5% | 5511 |   |  |

### `43-4141` New Accounts Clerks
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 0/4*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 0.1% | 5230 |   |  |
| 0.1% | 5222 |   |  |
| 0.0% | 5511 |   |  |
| 0.0% | 5241 |   |  |

### `43-4151` Order Clerks
*Moderate CTE · Some college, no degree · top-5 coverage: 1/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 1.0% | 4243 |   |  |
| 0.7% | 4592 |   |  |
| 0.5% | 3231 | ✓ | Manufacturing - Printing |
| 0.5% | 4591 |   |  |
| 0.4% | 3379 |   |  |

### `43-4171` Receptionists and Information Clerks
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 4/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 9.7% | 8121 | ✓ | Services - Personal Care |
| 8.2% | 6212 | ✓ | Healthcare - Dental |
| 7.3% | 5419 |   |  |
| 6.1% | 6211 | ✓ | Healthcare - Physician Offices |
| 6.0% | 6213 | ✓ | Healthcare - Other Practitioners |

### `43-5011` Cargo and Freight Agents
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 2/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 22.9% | 4885 |   |  |
| 2.7% | 4881 | ✓ | Transportation - Support Activities (Air) |
| 2.1% | 4831 |   |  |
| 2.0% | 4811 | ✓ | Transportation - Air |
| 1.6% | 4812 |   |  |

### `43-5061` Production, Planning, and Expediting Clerks
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 2/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 1.9% | 3369 |   |  |
| 1.9% | 5121 | ✓ | Media - Motion Picture/Video |
| 1.6% | 3341 | ✓ | Manufacturing - Computers |
| 1.5% | 4861 |   |  |
| 1.5% | 3365 |   |  |

### `43-6011` Executive Secretaries and Executive Administrative Assistants
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 0/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 3.0% | 5230 |   |  |
| 2.5% | 5259 |   |  |
| 2.0% | 8132 |   |  |
| 1.6% | 8139 |   |  |
| 1.4% | 2372 |   |  |

### `43-6012` Legal Secretaries and Administrative Assistants
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 0/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 10.4% | 5411 |   |  |
| 0.3% | 9992 |   |  |
| 0.3% | 5259 |   |  |
| 0.2% | 9993 |   |  |
| 0.1% | 5241 |   |  |

### `43-6013` Medical Secretaries and Administrative Assistants
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 5/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 8.9% | 6212 | ✓ | Healthcare - Dental |
| 8.5% | 6211 | ✓ | Healthcare - Physician Offices |
| 5.0% | 6213 | ✓ | Healthcare - Other Practitioners |
| 4.7% | 6214 | ✓ | Healthcare - Outpatient |
| 3.5% | 6215 | ✓ | Healthcare - Labs |

### `43-6014` Secretaries and Administrative Assistants, Except Legal, Medical, and Executive
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 0/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 12.1% | 7114 |   |  |
| 7.0% | 8131 |   |  |
| 6.0% | 8122 |   |  |
| 5.3% | 8139 |   |  |
| 4.3% | 8132 |   |  |

### `43-9021` Data Entry Keyers
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 3/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 1.7% | 5182 | ✓ | IT - Data Processing/Hosting |
| 0.9% | 4889 |   |  |
| 0.7% | 5412 | ✓ | Professional - Accounting/Tax |
| 0.6% | 6215 | ✓ | Healthcare - Labs |
| 0.6% | 5614 |   |  |

### `43-9022` Word Processors and Typists
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 1/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 0.2% | 9993 |   |  |
| 0.2% | 5614 |   |  |
| 0.1% | 6111 | ✓ | Education - Elementary/Secondary |
| 0.1% | 9992 |   |  |
| 0.1% | 5411 |   |  |

### `43-9041` Insurance Claims and Policy Processing Clerks
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 1/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 7.6% | 5242 |   |  |
| 7.2% | 5241 |   |  |
| 5.2% | 5251 |   |  |
| 0.4% | 6212 | ✓ | Healthcare - Dental |
| 0.3% | 5511 |   |  |

### `43-9061` Office Clerks, General
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 2/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 6.4% | 8122 |   |  |
| 5.4% | 8114 |   |  |
| 5.3% | 4245 | ✓ | Wholesale - Farm Products |
| 5.2% | 2213 | ✓ | Utilities - Water/Sewer |
| 5.2% | 5310 |   |  |

### `45-1011` First-Line Supervisors of Farming, Fishing, and Forestry Workers
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 3/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 5.5% | 1133 |   |  |
| 3.7% | 1152 | ✓ | Agriculture - Animal Support |
| 3.1% | 1151 | ✓ | Agriculture - Crop Support |
| 1.1% | 4245 | ✓ | Wholesale - Farm Products |
| 0.5% | 4442 |   |  |

### `45-2021` Animal Breeders
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 2/3*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 3.1% | 1152 | ✓ | Agriculture - Animal Support |
| 0.0% | 7121 |   |  |
| 0.0% | 3116 | ✓ | Manufacturing - Meat Processing |

### `45-2091` Agricultural Equipment Operators
*Moderate CTE · No formal educational credential · top-5 coverage: 4/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 4.2% | 1151 | ✓ | Agriculture - Crop Support |
| 2.6% | 4245 | ✓ | Wholesale - Farm Products |
| 0.7% | 1152 | ✓ | Agriculture - Animal Support |
| 0.3% | 3111 | ✓ | Manufacturing - Animal Food |
| 0.3% | 4442 |   |  |

### `45-4011` Forest and Conservation Workers
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 0/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 0.2% | 8133 |   |  |
| 0.1% | 9992 |   |  |
| 0.1% | 7121 |   |  |
| 0.0% | 9993 |   |  |
| 0.0% | 8139 |   |  |

### `45-4022` Logging Equipment Operators
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 3/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 40.8% | 1133 |   |  |
| 3.4% | 3211 | ✓ | Manufacturing - Sawmills/Wood |
| 0.2% | 3212 | ✓ | Manufacturing - Veneer/Plywood |
| 0.1% | 3219 | ✓ | Manufacturing - Other Wood Products |
| 0.1% | 4840 |   |  |

### `47-1011` First-Line Supervisors of Construction Trades and Extraction Workers
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 5/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 11.8% | 2362 | ✓ | Construction - Commercial |
| 9.6% | 2373 | ✓ | Construction - Highway/Street |
| 9.5% | 2371 | ✓ | Construction - Utility Systems |
| 8.7% | 2361 | ✓ | Construction - Residential |
| 8.6% | 2379 | ✓ | Construction - Other Heavy |

### `47-2011` Boilermakers
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 4/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 0.4% | 2371 | ✓ | Construction - Utility Systems |
| 0.4% | 8113 |   |  |
| 0.2% | 2362 | ✓ | Construction - Commercial |
| 0.1% | 3366 | ✓ | Manufacturing - Ship/Boat |
| 0.1% | 2382 | ✓ | Construction - HVAC/Plumbing/Electrical |

### `47-2021` Brickmasons and Blockmasons
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 4/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 4.6% | 2381 | ✓ | Construction - Foundation/Structural |
| 0.5% | 2362 | ✓ | Construction - Commercial |
| 0.2% | 3311 |   |  |
| 0.2% | 2389 | ✓ | Construction - Other Specialty |
| 0.2% | 2383 | ✓ | Construction - Finishing |

### `47-2022` Stonemasons
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 4/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 0.5% | 2381 | ✓ | Construction - Foundation/Structural |
| 0.3% | 3270 |   |  |
| 0.1% | 2361 | ✓ | Construction - Residential |
| 0.1% | 2383 | ✓ | Construction - Finishing |
| 0.0% | 2389 | ✓ | Construction - Other Specialty |

### `47-2031` Carpenters
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 5/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 23.6% | 2361 | ✓ | Construction - Residential |
| 14.7% | 2383 | ✓ | Construction - Finishing |
| 13.8% | 2362 | ✓ | Construction - Commercial |
| 9.6% | 2381 | ✓ | Construction - Foundation/Structural |
| 3.9% | 3219 | ✓ | Manufacturing - Other Wood Products |

### `47-2041` Carpet Installers
*Moderate CTE · No formal educational credential · top-5 coverage: 3/4*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 1.2% | 4491 |   |  |
| 1.0% | 2383 | ✓ | Construction - Finishing |
| 0.0% | 2361 | ✓ | Construction - Residential |
| 0.0% | 3219 | ✓ | Manufacturing - Other Wood Products |

### `47-2042` Floor Layers, Except Carpet, Wood, and Hard Tiles
*Moderate CTE · No formal educational credential · top-5 coverage: 4/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 2.2% | 2383 | ✓ | Construction - Finishing |
| 0.5% | 4491 |   |  |
| 0.2% | 3219 | ✓ | Manufacturing - Other Wood Products |
| 0.1% | 2361 | ✓ | Construction - Residential |
| 0.1% | 4441 | ✓ | Retail - Building Materials |

### `47-2043` Floor Sanders and Finishers
*Moderate CTE · No formal educational credential · top-5 coverage: 2/3*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 0.5% | 2383 | ✓ | Construction - Finishing |
| 0.1% | 2381 | ✓ | Construction - Foundation/Structural |
| 0.0% | 4491 |   |  |

### `47-2044` Tile and Stone Setters
*Moderate CTE · No formal educational credential · top-5 coverage: 3/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 3.1% | 2383 | ✓ | Construction - Finishing |
| 1.1% | 3270 |   |  |
| 0.2% | 4491 |   |  |
| 0.1% | 2381 | ✓ | Construction - Foundation/Structural |
| 0.1% | 2389 | ✓ | Construction - Other Specialty |

### `47-2051` Cement Masons and Concrete Finishers
*Moderate CTE · No formal educational credential · top-5 coverage: 5/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 10.6% | 2381 | ✓ | Construction - Foundation/Structural |
| 4.6% | 2389 | ✓ | Construction - Other Specialty |
| 4.4% | 2373 | ✓ | Construction - Highway/Street |
| 1.8% | 2362 | ✓ | Construction - Commercial |
| 1.4% | 2379 | ✓ | Construction - Other Heavy |

### `47-2053` Terrazzo Workers and Finishers
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 1/1*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 0.1% | 2383 | ✓ | Construction - Finishing |

### `47-2071` Paving, Surfacing, and Tamping Equipment Operators
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 4/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 3.8% | 2373 | ✓ | Construction - Highway/Street |
| 2.1% | 2389 | ✓ | Construction - Other Specialty |
| 1.2% | 3241 | ✓ | Manufacturing - Petroleum/Coal |
| 1.0% | 2379 | ✓ | Construction - Other Heavy |
| 0.2% | 4884 |   |  |

### `47-2072` Pile Driver Operators
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 5/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 0.8% | 2379 | ✓ | Construction - Other Heavy |
| 0.1% | 2389 | ✓ | Construction - Other Specialty |
| 0.1% | 2373 | ✓ | Construction - Highway/Street |
| 0.0% | 2371 | ✓ | Construction - Utility Systems |
| 0.0% | 2362 | ✓ | Construction - Commercial |

### `47-2073` Operating Engineers and Other Construction Equipment Operators
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 3/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 15.1% | 2373 | ✓ | Construction - Highway/Street |
| 14.6% | 2389 | ✓ | Construction - Other Specialty |
| 12.1% | 2379 | ✓ | Construction - Other Heavy |
| 12.1% | 2121 |   |  |
| 10.6% | 2123 |   |  |

### `47-2081` Drywall and Ceiling Tile Installers
*Moderate CTE · No formal educational credential · top-5 coverage: 5/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 8.6% | 2383 | ✓ | Construction - Finishing |
| 0.8% | 2361 | ✓ | Construction - Residential |
| 0.7% | 2362 | ✓ | Construction - Commercial |
| 0.4% | 3219 | ✓ | Manufacturing - Other Wood Products |
| 0.3% | 2381 | ✓ | Construction - Foundation/Structural |

### `47-2111` Electricians
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 2/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 21.5% | 2382 | ✓ | Construction - HVAC/Plumbing/Electrical |
| 4.1% | 2121 |   |  |
| 3.1% | 3366 | ✓ | Manufacturing - Ship/Boat |
| 2.9% | 3311 |   |  |
| 2.6% | 2122 |   |  |

### `47-2121` Glaziers
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 5/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 3.8% | 2381 | ✓ | Construction - Foundation/Structural |
| 0.4% | 4441 | ✓ | Retail - Building Materials |
| 0.4% | 2383 | ✓ | Construction - Finishing |
| 0.2% | 2362 | ✓ | Construction - Commercial |
| 0.2% | 8111 | ✓ | Services - Auto Repair/Maintenance |

### `47-2131` Insulation Workers, Floor, Ceiling, and Wall
*Moderate CTE · No formal educational credential · top-5 coverage: 4/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 3.3% | 2383 | ✓ | Construction - Finishing |
| 0.3% | 2362 | ✓ | Construction - Commercial |
| 0.2% | 2382 | ✓ | Construction - HVAC/Plumbing/Electrical |
| 0.1% | 2389 | ✓ | Construction - Other Specialty |
| 0.1% | 5629 |   |  |

### `47-2132` Insulation Workers, Mechanical
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 4/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 0.6% | 2382 | ✓ | Construction - HVAC/Plumbing/Electrical |
| 0.4% | 2383 | ✓ | Construction - Finishing |
| 0.2% | 5629 |   |  |
| 0.2% | 2362 | ✓ | Construction - Commercial |
| 0.1% | 2389 | ✓ | Construction - Other Specialty |

### `47-2141` Painters, Construction and Maintenance
*Moderate CTE · No formal educational credential · top-5 coverage: 5/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 17.4% | 2383 | ✓ | Construction - Finishing |
| 1.5% | 2361 | ✓ | Construction - Residential |
| 0.8% | 3366 | ✓ | Manufacturing - Ship/Boat |
| 0.7% | 2362 | ✓ | Construction - Commercial |
| 0.7% | 2373 | ✓ | Construction - Highway/Street |

### `47-2142` Paperhangers
*Moderate CTE · No formal educational credential · top-5 coverage: 2/3*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 0.2% | 5418 | ✓ | Professional - Advertising/PR |
| 0.1% | 2383 | ✓ | Construction - Finishing |
| 0.0% | 3399 |   |  |

### `47-2152` Plumbers, Pipefitters, and Steamfitters
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 4/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 13.1% | 2382 | ✓ | Construction - HVAC/Plumbing/Electrical |
| 5.4% | 2212 | ✓ | Utilities - Natural Gas |
| 3.4% | 2213 | ✓ | Utilities - Water/Sewer |
| 3.0% | 4862 |   |  |
| 2.7% | 2371 | ✓ | Construction - Utility Systems |

### `47-2181` Roofers
*Moderate CTE · No formal educational credential · top-5 coverage: 5/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 12.7% | 2381 | ✓ | Construction - Foundation/Structural |
| 0.4% | 2361 | ✓ | Construction - Residential |
| 0.3% | 3219 | ✓ | Manufacturing - Other Wood Products |
| 0.2% | 2362 | ✓ | Construction - Commercial |
| 0.1% | 2383 | ✓ | Construction - Finishing |

### `47-2211` Sheet Metal Workers
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 4/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 2.2% | 2382 | ✓ | Construction - HVAC/Plumbing/Electrical |
| 1.5% | 2381 | ✓ | Construction - Foundation/Structural |
| 0.9% | 3366 | ✓ | Manufacturing - Ship/Boat |
| 0.6% | 3362 |   |  |
| 0.6% | 2362 | ✓ | Construction - Commercial |

### `47-2221` Structural Iron and Steel Workers
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 4/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 3.3% | 2381 | ✓ | Construction - Foundation/Structural |
| 1.5% | 2362 | ✓ | Construction - Commercial |
| 0.6% | 3311 |   |  |
| 0.5% | 2373 | ✓ | Construction - Highway/Street |
| 0.4% | 2379 | ✓ | Construction - Other Heavy |

### `47-2231` Solar Photovoltaic Installers
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 4/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 0.6% | 2211 | ✓ | Utilities - Electric Power |
| 0.6% | 2382 | ✓ | Construction - HVAC/Plumbing/Electrical |
| 0.2% | 2371 | ✓ | Construction - Utility Systems |
| 0.1% | 5613 |   |  |
| 0.1% | 2361 | ✓ | Construction - Residential |

### `47-4011` Construction and Building Inspectors
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 3/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 2.5% | 5413 | ✓ | Professional - Architecture/Engineering |
| 0.9% | 2212 | ✓ | Utilities - Natural Gas |
| 0.9% | 9993 |   |  |
| 0.7% | 5419 |   |  |
| 0.5% | 2371 | ✓ | Construction - Utility Systems |

### `47-4021` Elevator and Escalator Installers and Repairers
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 2/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 0.9% | 2382 | ✓ | Construction - HVAC/Plumbing/Electrical |
| 0.4% | 4245 | ✓ | Wholesale - Farm Products |
| 0.1% | 8113 |   |  |
| 0.1% | 3112 |   |  |
| 0.1% | 4238 |   |  |

### `47-4041` Hazardous Materials Removal Workers
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 4/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 17.4% | 5629 |   |  |
| 5.5% | 5622 | ✓ | Waste - Treatment/Disposal |
| 0.7% | 5621 | ✓ | Waste - Collection |
| 0.1% | 2361 | ✓ | Construction - Residential |
| 0.1% | 5416 | ✓ | Professional - Management/Technical Consulting |

### `47-4051` Highway Maintenance Workers
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 2/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 1.9% | 9993 |   |  |
| 1.8% | 9992 |   |  |
| 1.4% | 2373 | ✓ | Construction - Highway/Street |
| 0.1% | 5619 |   |  |
| 0.0% | 2389 | ✓ | Construction - Other Specialty |

### `47-4061` Rail-Track Laying and Maintenance Equipment Operators
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 1/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 5.1% | 4821 |   |  |
| 2.3% | 4882 |   |  |
| 1.0% | 2379 | ✓ | Construction - Other Heavy |
| 0.2% | 2121 |   |  |
| 0.1% | 9993 |   |  |

### `47-4071` Septic Tank Servicers and Sewer Pipe Cleaners
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 3/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 8.7% | 5629 |   |  |
| 0.2% | 2389 | ✓ | Construction - Other Specialty |
| 0.2% | 2213 | ✓ | Utilities - Water/Sewer |
| 0.1% | 9993 |   |  |
| 0.1% | 2371 | ✓ | Construction - Utility Systems |

### `47-5022` Excavating and Loading Machine and Dragline Operators, Surface Mining
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 2/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 14.1% | 2123 |   |  |
| 7.6% | 2121 |   |  |
| 1.2% | 2122 |   |  |
| 0.5% | 2389 | ✓ | Construction - Other Specialty |
| 0.4% | 2373 | ✓ | Construction - Highway/Street |

### `47-5023` Earth Drillers, Except Oil and Gas
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 2/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 1.3% | 2371 | ✓ | Construction - Utility Systems |
| 0.7% | 2122 |   |  |
| 0.7% | 2123 |   |  |
| 0.7% | 2131 |   |  |
| 0.5% | 2379 | ✓ | Construction - Other Heavy |

### `47-5032` Explosives Workers, Ordnance Handling Experts, and Blasters
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 0/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 0.4% | 2122 |   |  |
| 0.3% | 2121 |   |  |
| 0.2% | 2123 |   |  |
| 0.2% | 4882 |   |  |
| 0.1% | 5629 |   |  |

### `47-5041` Continuous Mining Machine Operators
*Moderate CTE · No formal educational credential · top-5 coverage: 0/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 16.4% | 2122 |   |  |
| 7.1% | 2121 |   |  |
| 4.1% | 2123 |   |  |
| 0.3% | 2131 |   |  |
| 0.0% | 3270 |   |  |

### `47-5049` Underground Mining Machine Operators, All Other
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 1/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 3.0% | 2122 |   |  |
| 1.4% | 2121 |   |  |
| 0.4% | 2123 |   |  |
| 0.0% | 2131 |   |  |
| 0.0% | 2371 | ✓ | Construction - Utility Systems |

### `47-5099` Extraction Workers, All Other
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 1/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 2.3% | 2122 |   |  |
| 1.9% | 2121 |   |  |
| 1.9% | 2123 |   |  |
| 0.6% | 2131 |   |  |
| 0.3% | 2111 | ✓ | Mining - Oil/Gas Extraction |

### `49-1011` First-Line Supervisors of Mechanics, Installers, and Repairers
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 3/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 4.7% | 2211 | ✓ | Utilities - Electric Power |
| 4.7% | 4883 |   |  |
| 4.6% | 8111 | ✓ | Services - Auto Repair/Maintenance |
| 3.6% | 8113 |   |  |
| 3.5% | 2212 | ✓ | Utilities - Natural Gas |

### `49-2011` Computer, Automated Teller, and Office Machine Repairers
*Moderate CTE · Some college, no degree · top-5 coverage: 3/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 11.4% | 8112 |   |  |
| 5.6% | 4492 |   |  |
| 2.7% | 4234 | ✓ | Wholesale - Professional Equipment |
| 0.7% | 3341 | ✓ | Manufacturing - Computers |
| 0.3% | 5415 | ✓ | Professional - Computer Systems Design |

### `49-2092` Electric Motor, Power Tool, and Related Repairers
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 0/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 1.1% | 3353 |   |  |
| 1.1% | 8113 |   |  |
| 0.3% | 8112 |   |  |
| 0.2% | 8114 |   |  |
| 0.1% | 4238 |   |  |

### `49-2096` Electronic Equipment Installers and Repairers, Motor Vehicles
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 1/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 0.7% | 8112 |   |  |
| 0.5% | 4492 |   |  |
| 0.3% | 3362 |   |  |
| 0.3% | 4413 |   |  |
| 0.1% | 4231 | ✓ | Wholesale - Motor Vehicles/Parts |

### `49-2098` Security and Fire Alarm Systems Installers
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 2/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 5.3% | 5616 | ✓ | Admin - Investigation/Security |
| 0.8% | 2382 | ✓ | Construction - HVAC/Plumbing/Electrical |
| 0.1% | 4238 |   |  |
| 0.1% | 5612 |   |  |
| 0.0% | 4492 |   |  |

### `49-3021` Automotive Body and Related Repairers
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 4/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 11.1% | 8111 | ✓ | Services - Auto Repair/Maintenance |
| 1.9% | 4411 | ✓ | Retail - Auto Dealers |
| 1.3% | 3361 | ✓ | Manufacturing - Motor Vehicles |
| 0.8% | 5321 |   |  |
| 0.7% | 4231 | ✓ | Wholesale - Motor Vehicles/Parts |

### `49-3022` Automotive Glass Installers and Repairers
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 4/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 1.5% | 8111 | ✓ | Services - Auto Repair/Maintenance |
| 0.1% | 2381 | ✓ | Construction - Foundation/Structural |
| 0.0% | 4413 |   |  |
| 0.0% | 4411 | ✓ | Retail - Auto Dealers |
| 0.0% | 4231 | ✓ | Wholesale - Motor Vehicles/Parts |

### `49-3031` Bus and Truck Mechanics and Diesel Engine Specialists
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 2/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 6.9% | 4231 | ✓ | Wholesale - Motor Vehicles/Parts |
| 6.7% | 5321 |   |  |
| 6.3% | 4851 | ✓ | Transportation - Transit/Ground Passenger |
| 6.1% | 4855 |   |  |
| 5.8% | 4852 |   |  |

### `49-3041` Farm Equipment Mechanics and Service Technicians
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 2/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 3.5% | 4238 |   |  |
| 0.9% | 1151 | ✓ | Agriculture - Crop Support |
| 0.8% | 8113 |   |  |
| 0.6% | 4442 |   |  |
| 0.1% | 1152 | ✓ | Agriculture - Animal Support |

### `49-3042` Mobile Heavy Equipment Mechanics, Except Engines
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 0/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 8.0% | 2122 |   |  |
| 6.0% | 4238 |   |  |
| 5.5% | 4883 |   |  |
| 5.2% | 2121 |   |  |
| 4.0% | 8113 |   |  |

### `49-3043` Rail Car Repairers
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 0/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 16.4% | 4882 |   |  |
| 5.1% | 4821 |   |  |
| 1.5% | 3365 |   |  |
| 0.4% | 4871 |   |  |
| 0.1% | 4883 |   |  |

### `49-3051` Motorboat Mechanics and Service Technicians
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 1/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 6.0% | 8114 |   |  |
| 4.9% | 4412 |   |  |
| 1.4% | 3366 | ✓ | Manufacturing - Ship/Boat |
| 1.0% | 4872 |   |  |
| 1.0% | 4883 |   |  |

### `49-3053` Outdoor Power Equipment and Other Small Engine Mechanics
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 2/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 3.9% | 4442 |   |  |
| 2.8% | 8114 |   |  |
| 1.2% | 4412 |   |  |
| 0.4% | 4441 | ✓ | Retail - Building Materials |
| 0.3% | 7139 | ✓ | Arts - Other Amusement/Recreation |

### `49-3092` Recreational Vehicle Service Technicians
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 1/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 6.9% | 4412 |   |  |
| 0.7% | 5321 |   |  |
| 0.6% | 3362 |   |  |
| 0.2% | 8111 | ✓ | Services - Auto Repair/Maintenance |
| 0.1% | 8114 |   |  |

### `49-9012` Control and Valve Installers and Repairers, Except Mechanical Door
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 3/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 11.6% | 2212 | ✓ | Utilities - Natural Gas |
| 2.7% | 4869 |   |  |
| 2.2% | 2211 | ✓ | Utilities - Electric Power |
| 2.2% | 2213 | ✓ | Utilities - Water/Sewer |
| 1.8% | 4862 |   |  |

### `49-9031` Home Appliance Repairers
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 0/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 14.4% | 8114 |   |  |
| 2.1% | 4492 |   |  |
| 0.3% | 8112 |   |  |
| 0.3% | 4572 |   |  |
| 0.2% | 8113 |   |  |

### `49-9041` Industrial Machinery Mechanics
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 0/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 19.7% | 8113 |   |  |
| 9.1% | 4862 |   |  |
| 9.0% | 3311 |   |  |
| 8.1% | 3221 |   |  |
| 7.7% | 3151 |   |  |

### `49-9043` Maintenance Workers, Machinery
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 0/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 4.4% | 3151 |   |  |
| 1.6% | 2121 |   |  |
| 1.4% | 2122 |   |  |
| 1.2% | 4861 |   |  |
| 0.9% | 3112 |   |  |

### `49-9044` Millwrights
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 2/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 2.6% | 3211 | ✓ | Manufacturing - Sawmills/Wood |
| 1.2% | 3221 |   |  |
| 1.1% | 8113 |   |  |
| 0.7% | 3212 | ✓ | Manufacturing - Veneer/Plywood |
| 0.6% | 3311 |   |  |

### `49-9045` Refractory Materials Repairers, Except Brickmasons
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 1/4*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 0.2% | 3311 |   |  |
| 0.0% | 3315 |   |  |
| 0.0% | 2381 | ✓ | Construction - Foundation/Structural |
| 0.0% | 3270 |   |  |

### `49-9051` Electrical Power-Line Installers and Repairers
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 4/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 14.5% | 2211 | ✓ | Utilities - Electric Power |
| 6.3% | 2371 | ✓ | Construction - Utility Systems |
| 2.4% | 2212 | ✓ | Utilities - Natural Gas |
| 0.3% | 2379 | ✓ | Construction - Other Heavy |
| 0.2% | 9993 |   |  |

### `49-9052` Telecommunications Line Installers and Repairers
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 3/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 9.4% | 5170 |   |  |
| 2.6% | 2371 | ✓ | Construction - Utility Systems |
| 0.6% | 2382 | ✓ | Construction - HVAC/Plumbing/Electrical |
| 0.3% | 2211 | ✓ | Utilities - Electric Power |
| 0.2% | 5162 |   |  |

### `49-9061` Camera and Photographic Equipment Repairers
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 1/2*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 0.0% | 4234 | ✓ | Wholesale - Professional Equipment |
| 0.0% | 8129 |   |  |

### `49-9063` Musical Instrument Repairers and Tuners
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 1/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 1.2% | 8114 |   |  |
| 0.8% | 4591 |   |  |
| 0.1% | 3399 |   |  |
| 0.1% | 7111 |   |  |
| 0.0% | 6113 | ✓ | Education - Colleges/Universities |

### `49-9064` Watch and Clock Repairers
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 0/2*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 0.7% | 4583 |   |  |
| 0.5% | 8114 |   |  |

### `49-9069` Precision Instrument and Equipment Repairers, All Other
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 2/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 2.4% | 8112 |   |  |
| 0.2% | 4234 | ✓ | Wholesale - Professional Equipment |
| 0.1% | 3345 | ✓ | Manufacturing - Instruments |
| 0.1% | 8113 |   |  |
| 0.1% | 9991 |   |  |

### `49-9071` Maintenance and Repair Workers, General
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 2/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 16.7% | 5310 |   |  |
| 14.4% | 7212 | ✓ | Hospitality - RV Parks/Camps |
| 6.8% | 5612 |   |  |
| 6.6% | 7213 |   |  |
| 4.7% | 2213 | ✓ | Utilities - Water/Sewer |

### `49-9094` Locksmiths and Safe Repairers
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 3/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 1.0% | 5616 | ✓ | Admin - Investigation/Security |
| 0.3% | 8114 |   |  |
| 0.1% | 5612 |   |  |
| 0.0% | 6113 | ✓ | Education - Colleges/Universities |
| 0.0% | 6222 | ✓ | Healthcare - Hospitals (Psych/Substance) |

### `49-9095` Manufactured Building and Mobile Home Installers
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 2/3*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 0.3% | 4599 |   |  |
| 0.2% | 3219 | ✓ | Manufacturing - Other Wood Products |
| 0.1% | 2389 | ✓ | Construction - Other Specialty |

### `49-9097` Signal and Track Switch Repairers
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 0/3*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 3.3% | 4821 |   |  |
| 0.3% | 4882 |   |  |
| 0.1% | 9993 |   |  |

### `49-9099` Installation, Maintenance, and Repair Workers, All Other
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 0/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 2.7% | 3399 |   |  |
| 1.7% | 4572 |   |  |
| 1.6% | 3379 |   |  |
| 1.5% | 8114 |   |  |
| 1.3% | 3149 |   |  |

### `51-1011` First-Line Supervisors of Production and Operating Workers
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 1/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 7.6% | 3122 |   |  |
| 6.4% | 3161 |   |  |
| 5.9% | 3328 | ✓ | Manufacturing - Coating/Engraving |
| 5.5% | 3221 |   |  |
| 5.4% | 3312 |   |  |

### `51-2011` Aircraft Structure, Surfaces, Rigging, and Systems Assemblers
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 4/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 5.0% | 3364 | ✓ | Manufacturing - Aerospace |
| 0.7% | 4881 | ✓ | Transportation - Support Activities (Air) |
| 0.1% | 6115 | ✓ | Education - Technical/Trade Schools |
| 0.1% | 5613 |   |  |
| 0.0% | 5413 | ✓ | Professional - Architecture/Engineering |

### `51-2041` Structural Metal Fabricators and Fitters
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 1/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 3.8% | 3366 | ✓ | Manufacturing - Ship/Boat |
| 1.0% | 3362 |   |  |
| 0.6% | 3369 |   |  |
| 0.5% | 3312 |   |  |
| 0.4% | 3399 |   |  |

### `51-2061` Timing Device Assemblers and Adjusters
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 1/1*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 0.1% | 3345 | ✓ | Manufacturing - Instruments |

### `51-3011` Bakers
*Moderate CTE · No formal educational credential · top-5 coverage: 4/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 21.9% | 3118 | ✓ | Manufacturing - Bakeries |
| 0.6% | 7223 | ✓ | Food Service - Special/Caterers |
| 0.5% | 7225 | ✓ | Food Service - Restaurants |
| 0.3% | 3113 |   |  |
| 0.3% | 3119 | ✓ | Manufacturing - Other Food |

### `51-3092` Food Batchmakers
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 4/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 19.8% | 3113 |   |  |
| 15.3% | 3115 | ✓ | Manufacturing - Dairy Products |
| 12.9% | 3114 | ✓ | Manufacturing - Fruit/Vegetable Preserving |
| 11.0% | 3119 | ✓ | Manufacturing - Other Food |
| 8.3% | 3111 | ✓ | Manufacturing - Animal Food |

### `51-4021` Extruding and Drawing Machine Setters, Operators, and Tenders, Metal and Plastic
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 1/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 10.5% | 3314 |   |  |
| 5.7% | 3313 |   |  |
| 4.8% | 3261 | ✓ | Manufacturing - Plastics |
| 4.2% | 3312 |   |  |
| 2.9% | 3359 |   |  |

### `51-4022` Forging Machine Setters, Operators, and Tenders, Metal and Plastic
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 3/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 0.3% | 3311 |   |  |
| 0.2% | 3327 | ✓ | Manufacturing - Machine Shops |
| 0.1% | 3363 | ✓ | Manufacturing - Motor Vehicle Parts |
| 0.1% | 3261 | ✓ | Manufacturing - Plastics |
| 0.1% | 3312 |   |  |

### `51-4023` Rolling Machine Setters, Operators, and Tenders, Metal and Plastic
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 1/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 7.8% | 3311 |   |  |
| 5.1% | 3312 |   |  |
| 3.2% | 3313 |   |  |
| 1.7% | 3314 |   |  |
| 0.3% | 3261 | ✓ | Manufacturing - Plastics |

### `51-4031` Cutting, Punching, and Press Machine Setters, Operators, and Tenders, Metal and Plastic
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 3/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 7.8% | 3312 |   |  |
| 7.2% | 3313 |   |  |
| 5.5% | 3363 | ✓ | Manufacturing - Motor Vehicle Parts |
| 2.2% | 3335 | ✓ | Manufacturing - Metalworking Machinery |
| 2.1% | 3261 | ✓ | Manufacturing - Plastics |

### `51-4032` Drilling and Boring Machine Tool Setters, Operators, and Tenders, Metal and Plastic
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 3/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 0.5% | 3336 |   |  |
| 0.2% | 3327 | ✓ | Manufacturing - Machine Shops |
| 0.2% | 3364 | ✓ | Manufacturing - Aerospace |
| 0.1% | 3335 | ✓ | Manufacturing - Metalworking Machinery |
| 0.1% | 3315 |   |  |

### `51-4033` Grinding, Lapping, Polishing, and Buffing Machine Tool Setters, Operators, and Tenders, Metal and Plastic
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 3/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 8.2% | 3315 |   |  |
| 3.5% | 3328 | ✓ | Manufacturing - Coating/Engraving |
| 3.0% | 3335 | ✓ | Manufacturing - Metalworking Machinery |
| 2.3% | 3327 | ✓ | Manufacturing - Machine Shops |
| 1.4% | 3336 |   |  |

### `51-4034` Lathe and Turning Machine Tool Setters, Operators, and Tenders, Metal and Plastic
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 3/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 1.9% | 3327 | ✓ | Manufacturing - Machine Shops |
| 0.9% | 3336 |   |  |
| 0.6% | 3335 | ✓ | Manufacturing - Metalworking Machinery |
| 0.4% | 3312 |   |  |
| 0.2% | 3364 | ✓ | Manufacturing - Aerospace |

### `51-4035` Milling and Planing Machine Setters, Operators, and Tenders, Metal and Plastic
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 1/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 1.8% | 3313 |   |  |
| 1.3% | 3312 |   |  |
| 1.0% | 2122 |   |  |
| 0.7% | 3327 | ✓ | Manufacturing - Machine Shops |
| 0.5% | 3314 |   |  |

### `51-4041` Machinists
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 3/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 21.9% | 3327 | ✓ | Manufacturing - Machine Shops |
| 12.7% | 3335 | ✓ | Manufacturing - Metalworking Machinery |
| 8.0% | 3336 |   |  |
| 6.4% | 3365 |   |  |
| 3.2% | 3366 | ✓ | Manufacturing - Ship/Boat |

### `51-4061` Model Makers, Metal and Plastic
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 5/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 0.1% | 3335 | ✓ | Manufacturing - Metalworking Machinery |
| 0.1% | 5414 | ✓ | Professional - Graphic/Industrial Design |
| 0.1% | 3261 | ✓ | Manufacturing - Plastics |
| 0.0% | 3327 | ✓ | Manufacturing - Machine Shops |
| 0.0% | 3364 | ✓ | Manufacturing - Aerospace |

### `51-4062` Patternmakers, Metal and Plastic
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 3/4*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 0.7% | 3315 |   |  |
| 0.2% | 3335 | ✓ | Manufacturing - Metalworking Machinery |
| 0.0% | 3261 | ✓ | Manufacturing - Plastics |
| 0.0% | 3364 | ✓ | Manufacturing - Aerospace |

### `51-4071` Foundry Mold and Coremakers
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 1/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 7.5% | 3315 |   |  |
| 0.4% | 3335 | ✓ | Manufacturing - Metalworking Machinery |
| 0.3% | 3314 |   |  |
| 0.2% | 3312 |   |  |
| 0.1% | 3353 |   |  |

### `51-4081` Multiple Machine Tool Setters, Operators, and Tenders, Metal and Plastic
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 2/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 4.6% | 3312 |   |  |
| 4.2% | 3314 |   |  |
| 2.6% | 3261 | ✓ | Manufacturing - Plastics |
| 2.3% | 3363 | ✓ | Manufacturing - Motor Vehicle Parts |
| 2.0% | 3352 |   |  |

### `51-4121` Welders, Cutters, Solderers, and Brazers
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 1/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 14.8% | 3362 |   |  |
| 11.3% | 3365 |   |  |
| 9.7% | 3366 | ✓ | Manufacturing - Ship/Boat |
| 6.8% | 3369 |   |  |
| 6.5% | 8113 |   |  |

### `51-4122` Welding, Soldering, and Brazing Machine Setters, Operators, and Tenders
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 3/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 1.0% | 3369 |   |  |
| 0.9% | 3361 | ✓ | Manufacturing - Motor Vehicles |
| 0.8% | 3363 | ✓ | Manufacturing - Motor Vehicle Parts |
| 0.6% | 3344 | ✓ | Manufacturing - Semiconductors |
| 0.5% | 3312 |   |  |

### `51-4191` Heat Treating Equipment Setters, Operators, and Tenders, Metal and Plastic
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 1/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 3.1% | 3328 | ✓ | Manufacturing - Coating/Engraving |
| 0.7% | 3336 |   |  |
| 0.5% | 3312 |   |  |
| 0.5% | 3315 |   |  |
| 0.5% | 3313 |   |  |

### `51-4192` Layout Workers, Metal and Plastic
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 3/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 2.0% | 3366 | ✓ | Manufacturing - Ship/Boat |
| 0.1% | 3364 | ✓ | Manufacturing - Aerospace |
| 0.1% | 3315 |   |  |
| 0.1% | 9991 |   |  |
| 0.0% | 3328 | ✓ | Manufacturing - Coating/Engraving |

### `51-4194` Tool Grinders, Filers, and Sharpeners
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 3/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 1.5% | 3211 | ✓ | Manufacturing - Sawmills/Wood |
| 0.3% | 3335 | ✓ | Manufacturing - Metalworking Machinery |
| 0.3% | 8113 |   |  |
| 0.3% | 8114 |   |  |
| 0.1% | 3212 | ✓ | Manufacturing - Veneer/Plywood |

### `51-4199` Metal Workers and Plastic Workers, All Other
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 2/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 0.8% | 3314 |   |  |
| 0.7% | 3261 | ✓ | Manufacturing - Plastics |
| 0.4% | 3313 |   |  |
| 0.3% | 3311 |   |  |
| 0.3% | 3328 | ✓ | Manufacturing - Coating/Engraving |

### `51-5112` Printing Press Operators
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 1/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 24.0% | 3231 | ✓ | Manufacturing - Printing |
| 3.8% | 3222 |   |  |
| 3.4% | 3133 |   |  |
| 2.4% | 3149 |   |  |
| 1.9% | 5131 |   |  |

### `51-6092` Fabric and Apparel Patternmakers
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 1/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 1.6% | 3152 |   |  |
| 0.2% | 3149 |   |  |
| 0.0% | 6243 | ✓ | Social Services - Vocational Rehab |
| 0.0% | 4581 |   |  |
| 0.0% | 5511 |   |  |

### `51-6093` Upholsterers
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 1/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 5.5% | 8114 |   |  |
| 1.6% | 3379 |   |  |
| 0.6% | 3366 | ✓ | Manufacturing - Ship/Boat |
| 0.3% | 3141 |   |  |
| 0.3% | 3369 |   |  |

### `51-7011` Cabinetmakers and Bench Carpenters
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 3/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 3.1% | 3219 | ✓ | Manufacturing - Other Wood Products |
| 0.9% | 3362 |   |  |
| 0.7% | 2383 | ✓ | Construction - Finishing |
| 0.3% | 4889 |   |  |
| 0.3% | 3212 | ✓ | Manufacturing - Veneer/Plywood |

### `51-7031` Model Makers, Wood
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 2/3*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 0.0% | 3212 | ✓ | Manufacturing - Veneer/Plywood |
| 0.0% | 3399 |   |  |
| 0.0% | 3219 | ✓ | Manufacturing - Other Wood Products |

### `51-7032` Patternmakers, Wood
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 0/1*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 0.0% | 3270 |   |  |

### `51-7041` Sawing Machine Setters, Operators, and Tenders, Wood
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 3/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 16.6% | 3211 | ✓ | Manufacturing - Sawmills/Wood |
| 6.2% | 3212 | ✓ | Manufacturing - Veneer/Plywood |
| 4.8% | 3219 | ✓ | Manufacturing - Other Wood Products |
| 1.2% | 1133 |   |  |
| 0.1% | 3221 |   |  |

### `51-7042` Woodworking Machine Setters, Operators, and Tenders, Except Sawing
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 3/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 10.8% | 3219 | ✓ | Manufacturing - Other Wood Products |
| 9.4% | 3212 | ✓ | Manufacturing - Veneer/Plywood |
| 6.0% | 3211 | ✓ | Manufacturing - Sawmills/Wood |
| 0.4% | 3399 |   |  |
| 0.2% | 3221 |   |  |

### `51-7099` Woodworkers, All Other
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 3/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 1.4% | 3212 | ✓ | Manufacturing - Veneer/Plywood |
| 1.0% | 3219 | ✓ | Manufacturing - Other Wood Products |
| 0.7% | 3211 | ✓ | Manufacturing - Sawmills/Wood |
| 0.1% | 3399 |   |  |
| 0.0% | 4591 |   |  |

### `51-8011` Nuclear Power Reactor Operators
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 2/3*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 1.1% | 2211 | ✓ | Utilities - Electric Power |
| 0.1% | 5417 | ✓ | Professional - Scientific R&D |
| 0.0% | 9991 |   |  |

### `51-8013` Power Plant Operators
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 4/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 5.6% | 2211 | ✓ | Utilities - Electric Power |
| 0.6% | 5622 | ✓ | Waste - Treatment/Disposal |
| 0.5% | 2212 | ✓ | Utilities - Natural Gas |
| 0.4% | 3221 |   |  |
| 0.3% | 2213 | ✓ | Utilities - Water/Sewer |

### `51-8031` Water and Wastewater Treatment Plant and System Operators
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 2/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 26.5% | 2213 | ✓ | Utilities - Water/Sewer |
| 1.7% | 5622 | ✓ | Waste - Treatment/Disposal |
| 1.6% | 9993 |   |  |
| 0.5% | 3221 |   |  |
| 0.3% | 3314 |   |  |

### `51-8091` Chemical Plant and System Operators
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 5/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 0.9% | 3241 | ✓ | Manufacturing - Petroleum/Coal |
| 0.5% | 3254 | ✓ | Manufacturing - Pharmaceuticals |
| 0.2% | 5622 | ✓ | Waste - Treatment/Disposal |
| 0.0% | 3261 | ✓ | Manufacturing - Plastics |
| 0.0% | 2211 | ✓ | Utilities - Electric Power |

### `51-8092` Gas Plant Operators
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 3/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 12.6% | 4862 |   |  |
| 5.5% | 2212 | ✓ | Utilities - Natural Gas |
| 2.4% | 4861 |   |  |
| 1.3% | 2111 | ✓ | Mining - Oil/Gas Extraction |
| 0.2% | 2211 | ✓ | Utilities - Electric Power |

### `51-9011` Chemical Equipment Operators and Tenders
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 2/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 8.7% | 3254 | ✓ | Manufacturing - Pharmaceuticals |
| 1.7% | 3221 |   |  |
| 1.0% | 3241 | ✓ | Manufacturing - Petroleum/Coal |
| 0.8% | 3314 |   |  |
| 0.3% | 3112 |   |  |

### `51-9012` Separating, Filtering, Clarifying, Precipitating, and Still Machine Setters, Operators, and Tenders
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 3/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 7.4% | 3121 | ✓ | Manufacturing - Beverages |
| 3.7% | 3115 | ✓ | Manufacturing - Dairy Products |
| 1.9% | 3112 |   |  |
| 1.1% | 3254 | ✓ | Manufacturing - Pharmaceuticals |
| 0.7% | 2122 |   |  |

### `51-9061` Inspectors, Testers, Sorters, Samplers, and Weighers
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 1/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 6.4% | 3151 |   |  |
| 6.0% | 3132 |   |  |
| 5.7% | 3315 |   |  |
| 5.2% | 3261 | ✓ | Manufacturing - Plastics |
| 5.1% | 3133 |   |  |

### `51-9071` Jewelers and Precious Stone and Metal Workers
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 1/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 9.1% | 4583 |   |  |
| 2.2% | 3399 |   |  |
| 1.4% | 8114 |   |  |
| 0.2% | 5414 | ✓ | Professional - Graphic/Industrial Design |
| 0.1% | 4599 |   |  |

### `51-9081` Dental Laboratory Technicians
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 3/4*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 8.6% | 3391 | ✓ | Manufacturing - Medical Equipment |
| 0.4% | 6212 | ✓ | Healthcare - Dental |
| 0.0% | 9991 |   |  |
| 0.0% | 6213 | ✓ | Healthcare - Other Practitioners |

### `51-9083` Ophthalmic Laboratory Technicians
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 3/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 2.6% | 3333 |   |  |
| 1.6% | 3391 | ✓ | Manufacturing - Medical Equipment |
| 0.3% | 4561 |   |  |
| 0.2% | 6213 | ✓ | Healthcare - Other Practitioners |
| 0.2% | 4234 | ✓ | Wholesale - Professional Equipment |

### `51-9124` Coating, Painting, and Spraying Machine Setters, Operators, and Tenders
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 1/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 11.8% | 3328 | ✓ | Manufacturing - Coating/Engraving |
| 6.2% | 3133 |   |  |
| 3.6% | 3362 |   |  |
| 3.3% | 3161 |   |  |
| 2.8% | 3369 |   |  |

### `51-9141` Semiconductor Processing Technicians
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 5/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 6.2% | 3344 | ✓ | Manufacturing - Semiconductors |
| 0.4% | 3341 | ✓ | Manufacturing - Computers |
| 0.0% | 3345 | ✓ | Manufacturing - Instruments |
| 0.0% | 3364 | ✓ | Manufacturing - Aerospace |
| 0.0% | 5417 | ✓ | Professional - Scientific R&D |

### `51-9161` Computer Numerically Controlled Tool Operators
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 3/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 11.9% | 3327 | ✓ | Manufacturing - Machine Shops |
| 9.0% | 3335 | ✓ | Manufacturing - Metalworking Machinery |
| 4.7% | 3336 |   |  |
| 3.3% | 3315 |   |  |
| 2.6% | 3364 | ✓ | Manufacturing - Aerospace |

### `53-2012` Commercial Pilots
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 2/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 33.8% | 4812 |   |  |
| 21.5% | 4879 |   |  |
| 3.1% | 6115 | ✓ | Education - Technical/Trade Schools |
| 2.2% | 4881 | ✓ | Transportation - Support Activities (Air) |
| 1.4% | 4832 |   |  |

### `53-2022` Airfield Operations Specialists
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 3/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 2.6% | 4879 |   |  |
| 2.3% | 4812 |   |  |
| 1.8% | 4811 | ✓ | Transportation - Air |
| 0.7% | 4881 | ✓ | Transportation - Support Activities (Air) |
| 0.2% | 6115 | ✓ | Education - Technical/Trade Schools |

### `53-2031` Flight Attendants
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 2/3*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 25.5% | 4811 | ✓ | Transportation - Air |
| 3.0% | 4812 |   |  |
| 0.2% | 4881 | ✓ | Transportation - Support Activities (Air) |

### `53-3033` Light Truck Drivers
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 2/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 59.0% | 4922 |   |  |
| 30.2% | 4921 | ✓ | Transportation - Couriers/Express Delivery |
| 14.0% | 4413 |   |  |
| 11.7% | 4593 |   |  |
| 8.7% | 4231 | ✓ | Wholesale - Motor Vehicles/Parts |

### `53-3051` Bus Drivers, School
*Moderate CTE · No formal educational credential · top-5 coverage: 4/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 65.5% | 4854 | ✓ | Transportation - School Bus |
| 5.4% | 4855 |   |  |
| 4.7% | 4859 | ✓ | Transportation - Other Transit |
| 2.5% | 4851 | ✓ | Transportation - Transit/Ground Passenger |
| 2.2% | 6111 | ✓ | Education - Elementary/Secondary |

### `53-3052` Bus Drivers, Transit and Intercity
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 2/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 55.6% | 4851 | ✓ | Transportation - Transit/Ground Passenger |
| 52.7% | 4855 |   |  |
| 50.1% | 4852 |   |  |
| 21.1% | 4871 |   |  |
| 6.7% | 4859 | ✓ | Transportation - Other Transit |

### `53-3053` Shuttle Drivers and Chauffeurs
*Moderate CTE · No formal educational credential · top-5 coverage: 3/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 52.8% | 4859 | ✓ | Transportation - Other Transit |
| 36.7% | 4853 | ✓ | Transportation - Taxi/Limo |
| 5.9% | 4854 | ✓ | Transportation - School Bus |
| 5.8% | 4852 |   |  |
| 5.1% | 4871 |   |  |

### `53-4011` Locomotive Engineers
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 0/4*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 17.1% | 4821 |   |  |
| 1.1% | 4882 |   |  |
| 0.7% | 4871 |   |  |
| 0.0% | 2123 |   |  |

### `53-4013` Rail Yard Engineers, Dinkey Operators, and Hostlers
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 0/3*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 2.2% | 4882 |   |  |
| 0.6% | 4821 |   |  |
| 0.1% | 2121 |   |  |

### `53-4022` Railroad Brake, Signal, and Switch Operators and Locomotive Firers
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 0/3*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 6.4% | 4821 |   |  |
| 2.9% | 4882 |   |  |
| 0.0% | 9993 |   |  |

### `53-4031` Railroad Conductors and Yardmasters
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 0/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 20.1% | 4821 |   |  |
| 2.4% | 4882 |   |  |
| 1.2% | 4871 |   |  |
| 0.1% | 9993 |   |  |
| 0.0% | 9992 |   |  |

### `53-4041` Subway and Streetcar Operators
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 1/3*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 1.5% | 4851 | ✓ | Transportation - Transit/Ground Passenger |
| 0.2% | 9993 |   |  |
| 0.0% | 9992 |   |  |

### `53-4099` Rail Transportation Workers, All Other
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 1/3*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 2.0% | 4882 |   |  |
| 0.1% | 4821 |   |  |
| 0.1% | 4851 | ✓ | Transportation - Transit/Ground Passenger |

### `53-6041` Traffic Technicians
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 1/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 0.1% | 4831 |   |  |
| 0.1% | 9993 |   |  |
| 0.1% | 9992 |   |  |
| 0.0% | 5619 |   |  |
| 0.0% | 2373 | ✓ | Construction - Highway/Street |

### `53-7021` Crane and Tower Operators
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 2/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 2.7% | 4883 |   |  |
| 2.3% | 3311 |   |  |
| 1.3% | 2389 | ✓ | Construction - Other Specialty |
| 1.1% | 3312 |   |  |
| 0.7% | 2379 | ✓ | Construction - Other Heavy |

### `53-7031` Dredge Operators
*Moderate CTE · High school diploma or equivalent · top-5 coverage: 1/2*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 0.4% | 2123 |   |  |
| 0.2% | 2379 | ✓ | Construction - Other Heavy |

### `53-7041` Hoist and Winch Operators
*Moderate CTE · No formal educational credential · top-5 coverage: 1/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 0.4% | 4831 |   |  |
| 0.3% | 4883 |   |  |
| 0.2% | 3211 | ✓ | Manufacturing - Sawmills/Wood |
| 0.2% | 2121 |   |  |
| 0.1% | 1133 |   |  |

### `53-7199` Material Moving Workers, All Other
*Moderate CTE · No formal educational credential · top-5 coverage: 2/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 1.2% | 4883 |   |  |
| 1.2% | 5321 |   |  |
| 0.6% | 4889 |   |  |
| 0.4% | 4411 | ✓ | Retail - Auto Dealers |
| 0.3% | 3212 | ✓ | Manufacturing - Veneer/Plywood |

### `11-9171` Funeral Home Managers
*Strong CTE · Associate's degree · top-5 coverage: 0/1*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 10.2% | 8122 |   |  |

### `13-1032` Insurance Appraisers, Auto Damage
*Strong CTE · Postsecondary nondegree award · top-5 coverage: 1/3*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 0.4% | 5241 |   |  |
| 0.2% | 5242 |   |  |
| 0.0% | 4411 | ✓ | Retail - Auto Dealers |

### `15-1231` Computer Network Support Specialists
*Strong CTE · Associate's degree · top-5 coverage: 2/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 2.1% | 5170 |   |  |
| 1.3% | 5415 | ✓ | Professional - Computer Systems Design |
| 1.3% | 5182 | ✓ | IT - Data Processing/Hosting |
| 0.8% | 8112 |   |  |
| 0.6% | 5132 |   |  |

### `17-3011` Architectural and Civil Drafters
*Strong CTE · Associate's degree · top-5 coverage: 5/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 4.9% | 5413 | ✓ | Professional - Architecture/Engineering |
| 2.1% | 3212 | ✓ | Manufacturing - Veneer/Plywood |
| 0.7% | 5414 | ✓ | Professional - Graphic/Industrial Design |
| 0.4% | 2361 | ✓ | Construction - Residential |
| 0.4% | 3219 | ✓ | Manufacturing - Other Wood Products |

### `17-3012` Electrical and Electronics Drafters
*Strong CTE · Associate's degree · top-5 coverage: 4/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 0.5% | 2211 | ✓ | Utilities - Electric Power |
| 0.4% | 3353 |   |  |
| 0.4% | 5413 | ✓ | Professional - Architecture/Engineering |
| 0.4% | 3351 | ✓ | Manufacturing - Electrical Equipment |
| 0.3% | 2212 | ✓ | Utilities - Natural Gas |

### `17-3013` Mechanical Drafters
*Strong CTE · Associate's degree · top-5 coverage: 2/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 0.7% | 3333 |   |  |
| 0.6% | 3335 | ✓ | Manufacturing - Metalworking Machinery |
| 0.6% | 5413 | ✓ | Professional - Architecture/Engineering |
| 0.5% | 3365 |   |  |
| 0.4% | 3312 |   |  |

### `17-3019` Drafters, All Other
*Strong CTE · Associate's degree · top-5 coverage: 4/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 0.2% | 3366 | ✓ | Manufacturing - Ship/Boat |
| 0.2% | 5413 | ✓ | Professional - Architecture/Engineering |
| 0.1% | 5414 | ✓ | Professional - Graphic/Industrial Design |
| 0.1% | 3391 | ✓ | Manufacturing - Medical Equipment |
| 0.1% | 3270 |   |  |

### `17-3021` Aerospace Engineering and Operations Technologists and Technicians
*Strong CTE · Associate's degree · top-5 coverage: 4/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 0.9% | 3364 | ✓ | Manufacturing - Aerospace |
| 0.2% | 5413 | ✓ | Professional - Architecture/Engineering |
| 0.2% | 6115 | ✓ | Education - Technical/Trade Schools |
| 0.1% | 3342 |   |  |
| 0.1% | 3345 | ✓ | Manufacturing - Instruments |

### `17-3022` Civil Engineering Technologists and Technicians
*Strong CTE · Associate's degree · top-5 coverage: 2/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 1.9% | 5413 | ✓ | Professional - Architecture/Engineering |
| 0.7% | 9992 |   |  |
| 0.6% | 4861 |   |  |
| 0.2% | 9993 |   |  |
| 0.1% | 2212 | ✓ | Utilities - Natural Gas |

### `17-3023` Electrical and Electronic Engineering Technologists and Technicians
*Strong CTE · Associate's degree · top-5 coverage: 2/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 3.3% | 3344 | ✓ | Manufacturing - Semiconductors |
| 2.2% | 3342 |   |  |
| 1.6% | 3345 | ✓ | Manufacturing - Instruments |
| 1.4% | 3359 |   |  |
| 1.3% | 3353 |   |  |

### `17-3024` Electro-Mechanical and Mechatronics Technologists and Technicians
*Strong CTE · Associate's degree · top-5 coverage: 3/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 0.3% | 3344 | ✓ | Manufacturing - Semiconductors |
| 0.3% | 3345 | ✓ | Manufacturing - Instruments |
| 0.2% | 3342 |   |  |
| 0.2% | 8112 |   |  |
| 0.2% | 2111 | ✓ | Mining - Oil/Gas Extraction |

### `17-3025` Environmental Engineering Technologists and Technicians
*Strong CTE · Associate's degree · top-5 coverage: 2/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 0.6% | 5629 |   |  |
| 0.3% | 5413 | ✓ | Professional - Architecture/Engineering |
| 0.2% | 2122 |   |  |
| 0.1% | 5416 | ✓ | Professional - Management/Technical Consulting |
| 0.1% | 3314 |   |  |

### `17-3026` Industrial Engineering Technologists and Technicians
*Strong CTE · Associate's degree · top-5 coverage: 4/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 2.1% | 3344 | ✓ | Manufacturing - Semiconductors |
| 1.7% | 3336 |   |  |
| 0.9% | 3391 | ✓ | Manufacturing - Medical Equipment |
| 0.8% | 3345 | ✓ | Manufacturing - Instruments |
| 0.8% | 3363 | ✓ | Manufacturing - Motor Vehicle Parts |

### `17-3027` Mechanical Engineering Technologists and Technicians
*Strong CTE · Associate's degree · top-5 coverage: 2/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 0.6% | 3313 |   |  |
| 0.5% | 3365 |   |  |
| 0.5% | 5417 | ✓ | Professional - Scientific R&D |
| 0.5% | 5413 | ✓ | Professional - Architecture/Engineering |
| 0.4% | 3336 |   |  |

### `17-3028` Calibration Technologists and Technicians
*Strong CTE · Associate's degree · top-5 coverage: 1/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 0.9% | 8112 |   |  |
| 0.9% | 4861 |   |  |
| 0.7% | 4869 |   |  |
| 0.6% | 4862 |   |  |
| 0.3% | 3345 | ✓ | Manufacturing - Instruments |

### `17-3029` Engineering Technologists and Technicians, Except Drafters, All Other
*Strong CTE · Associate's degree · top-5 coverage: 3/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 0.7% | 9991 |   |  |
| 0.7% | 5413 | ✓ | Professional - Architecture/Engineering |
| 0.6% | 2111 | ✓ | Mining - Oil/Gas Extraction |
| 0.5% | 3311 |   |  |
| 0.5% | 5417 | ✓ | Professional - Scientific R&D |

### `19-4012` Agricultural Technicians
*Strong CTE · Associate's degree · top-5 coverage: 4/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 2.4% | 1152 | ✓ | Agriculture - Animal Support |
| 0.4% | 4245 | ✓ | Wholesale - Farm Products |
| 0.3% | 5417 | ✓ | Professional - Scientific R&D |
| 0.1% | 3254 | ✓ | Manufacturing - Pharmaceuticals |
| 0.1% | 3112 |   |  |

### `19-4013` Food Science Technicians
*Strong CTE · Associate's degree · top-5 coverage: 4/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 1.2% | 3115 | ✓ | Manufacturing - Dairy Products |
| 1.0% | 3112 |   |  |
| 1.0% | 3114 | ✓ | Manufacturing - Fruit/Vegetable Preserving |
| 0.7% | 3119 | ✓ | Manufacturing - Other Food |
| 0.5% | 3121 | ✓ | Manufacturing - Beverages |

### `19-4031` Chemical Technicians
*Strong CTE · Associate's degree · top-5 coverage: 3/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 2.1% | 3122 |   |  |
| 1.4% | 3254 | ✓ | Manufacturing - Pharmaceuticals |
| 1.3% | 3241 | ✓ | Manufacturing - Petroleum/Coal |
| 0.8% | 2122 |   |  |
| 0.7% | 5413 | ✓ | Professional - Architecture/Engineering |

### `19-4042` Environmental Science and Protection Technicians, Including Health
*Strong CTE · Associate's degree · top-5 coverage: 3/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 0.8% | 5622 | ✓ | Waste - Treatment/Disposal |
| 0.8% | 5629 |   |  |
| 0.4% | 5413 | ✓ | Professional - Architecture/Engineering |
| 0.4% | 5416 | ✓ | Professional - Management/Technical Consulting |
| 0.3% | 8133 |   |  |

### `19-4043` Geological Technicians, Except Hydrologic Technicians
*Strong CTE · Associate's degree · top-5 coverage: 3/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 0.6% | 2111 | ✓ | Mining - Oil/Gas Extraction |
| 0.5% | 2122 |   |  |
| 0.3% | 2131 |   |  |
| 0.3% | 3241 | ✓ | Manufacturing - Petroleum/Coal |
| 0.3% | 5413 | ✓ | Professional - Architecture/Engineering |

### `19-4044` Hydrologic Technicians
*Strong CTE · Associate's degree · top-5 coverage: 3/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 0.1% | 9991 |   |  |
| 0.0% | 2211 | ✓ | Utilities - Electric Power |
| 0.0% | 5413 | ✓ | Professional - Architecture/Engineering |
| 0.0% | 5416 | ✓ | Professional - Management/Technical Consulting |
| 0.0% | 9993 |   |  |

### `19-4051` Nuclear Technicians
*Strong CTE · Associate's degree · top-5 coverage: 5/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 0.8% | 2211 | ✓ | Utilities - Electric Power |
| 0.2% | 3366 | ✓ | Manufacturing - Ship/Boat |
| 0.1% | 5622 | ✓ | Waste - Treatment/Disposal |
| 0.1% | 5417 | ✓ | Professional - Scientific R&D |
| 0.0% | 5413 | ✓ | Professional - Architecture/Engineering |

### `19-4071` Forest and Conservation Technicians
*Strong CTE · Associate's degree · top-5 coverage: 1/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 0.9% | 9991 |   |  |
| 0.2% | 8133 |   |  |
| 0.2% | 9992 |   |  |
| 0.1% | 5417 | ✓ | Professional - Scientific R&D |
| 0.1% | 9993 |   |  |

### `19-4099` Life, Physical, and Social Science Technicians, All Other
*Strong CTE · Associate's degree · top-5 coverage: 4/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 1.5% | 5417 | ✓ | Professional - Scientific R&D |
| 0.8% | 3254 | ✓ | Manufacturing - Pharmaceuticals |
| 0.6% | 6113 | ✓ | Education - Colleges/Universities |
| 0.3% | 9991 |   |  |
| 0.2% | 3345 | ✓ | Manufacturing - Instruments |

### `23-2011` Paralegals and Legal Assistants
*Strong CTE · Associate's degree · top-5 coverage: 0/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 23.0% | 5411 |   |  |
| 1.0% | 5331 |   |  |
| 0.8% | 9991 |   |  |
| 0.7% | 5251 |   |  |
| 0.5% | 5259 |   |  |

### `23-2099` Legal Support Workers, All Other
*Strong CTE · Associate's degree · top-5 coverage: 1/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 1.0% | 5411 |   |  |
| 0.7% | 9991 |   |  |
| 0.3% | 2111 | ✓ | Mining - Oil/Gas Extraction |
| 0.2% | 9992 |   |  |
| 0.2% | 5331 |   |  |

### `25-2011` Preschool Teachers, Except Special Education
*Strong CTE · Associate's degree · top-5 coverage: 2/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 32.0% | 6244 | ✓ | Social Services - Child Day Care |
| 4.1% | 8131 |   |  |
| 1.4% | 8134 |   |  |
| 1.2% | 8133 |   |  |
| 0.9% | 6111 | ✓ | Education - Elementary/Secondary |

### `25-4031` Library Technicians
*Strong CTE · Postsecondary nondegree award · top-5 coverage: 3/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 2.4% | 5192 |   |  |
| 0.8% | 9993 |   |  |
| 0.3% | 6112 | ✓ | Education - Junior Colleges |
| 0.3% | 6113 | ✓ | Education - Colleges/Universities |
| 0.1% | 6111 | ✓ | Education - Elementary/Secondary |

### `27-3092` Court Reporters and Simultaneous Captioners
*Strong CTE · Postsecondary nondegree award · top-5 coverage: 2/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 0.5% | 5614 |   |  |
| 0.2% | 9992 |   |  |
| 0.1% | 9993 |   |  |
| 0.0% | 5121 | ✓ | Media - Motion Picture/Video |
| 0.0% | 6113 | ✓ | Education - Colleges/Universities |

### `27-4011` Audio and Video Technicians
*Strong CTE · Postsecondary nondegree award · top-5 coverage: 2/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 3.3% | 5122 | ✓ | Media - Sound Recording |
| 2.4% | 5121 | ✓ | Media - Motion Picture/Video |
| 2.2% | 7113 |   |  |
| 1.5% | 7111 |   |  |
| 1.4% | 3343 |   |  |

### `27-4012` Broadcast Technicians
*Strong CTE · Associate's degree · top-5 coverage: 2/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 7.7% | 5161 |   |  |
| 2.7% | 5162 |   |  |
| 1.3% | 5121 | ✓ | Media - Motion Picture/Video |
| 0.7% | 5122 | ✓ | Media - Sound Recording |
| 0.5% | 7112 |   |  |

### `27-4014` Sound Engineering Technicians
*Strong CTE · Postsecondary nondegree award · top-5 coverage: 2/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 11.3% | 5122 | ✓ | Media - Sound Recording |
| 1.0% | 5121 | ✓ | Media - Motion Picture/Video |
| 0.5% | 5161 |   |  |
| 0.5% | 7113 |   |  |
| 0.5% | 3346 |   |  |

### `29-1124` Radiation Therapists
*Strong CTE · Associate's degree · top-5 coverage: 5/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 0.3% | 6223 | ✓ | Healthcare - Hospitals (Specialty) |
| 0.2% | 6221 | ✓ | Healthcare - Hospitals (General) |
| 0.1% | 6211 | ✓ | Healthcare - Physician Offices |
| 0.1% | 6215 | ✓ | Healthcare - Labs |
| 0.1% | 6219 | ✓ | Healthcare - Other Ambulatory |

### `29-1126` Respiratory Therapists
*Strong CTE · Associate's degree · top-5 coverage: 5/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 2.6% | 6223 | ✓ | Healthcare - Hospitals (Specialty) |
| 1.7% | 6221 | ✓ | Healthcare - Hospitals (General) |
| 0.3% | 6231 | ✓ | Healthcare - Nursing Facilities |
| 0.3% | 4234 | ✓ | Wholesale - Professional Equipment |
| 0.2% | 6214 | ✓ | Healthcare - Outpatient |

### `29-1292` Dental Hygienists
*Strong CTE · Associate's degree · top-5 coverage: 3/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 19.6% | 6212 | ✓ | Healthcare - Dental |
| 0.2% | 6214 | ✓ | Healthcare - Outpatient |
| 0.1% | 6211 | ✓ | Healthcare - Physician Offices |
| 0.1% | 5613 |   |  |
| 0.0% | 5611 |   |  |

### `29-2031` Cardiovascular Technologists and Technicians
*Strong CTE · Associate's degree · top-5 coverage: 5/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 0.8% | 6221 | ✓ | Healthcare - Hospitals (General) |
| 0.3% | 6223 | ✓ | Healthcare - Hospitals (Specialty) |
| 0.3% | 6215 | ✓ | Healthcare - Labs |
| 0.2% | 6211 | ✓ | Healthcare - Physician Offices |
| 0.2% | 6219 | ✓ | Healthcare - Other Ambulatory |

### `29-2032` Diagnostic Medical Sonographers
*Strong CTE · Associate's degree · top-5 coverage: 5/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 3.0% | 6215 | ✓ | Healthcare - Labs |
| 0.8% | 6221 | ✓ | Healthcare - Hospitals (General) |
| 0.6% | 6211 | ✓ | Healthcare - Physician Offices |
| 0.3% | 6214 | ✓ | Healthcare - Outpatient |
| 0.3% | 6223 | ✓ | Healthcare - Hospitals (Specialty) |

### `29-2033` Nuclear Medicine Technologists
*Strong CTE · Associate's degree · top-5 coverage: 5/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 0.3% | 6215 | ✓ | Healthcare - Labs |
| 0.2% | 6221 | ✓ | Healthcare - Hospitals (General) |
| 0.1% | 6211 | ✓ | Healthcare - Physician Offices |
| 0.1% | 6223 | ✓ | Healthcare - Hospitals (Specialty) |
| 0.1% | 6214 | ✓ | Healthcare - Outpatient |

### `29-2034` Radiologic Technologists and Technicians
*Strong CTE · Associate's degree · top-5 coverage: 5/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 5.2% | 6215 | ✓ | Healthcare - Labs |
| 2.3% | 6221 | ✓ | Healthcare - Hospitals (General) |
| 1.4% | 6211 | ✓ | Healthcare - Physician Offices |
| 1.4% | 6214 | ✓ | Healthcare - Outpatient |
| 0.9% | 6223 | ✓ | Healthcare - Hospitals (Specialty) |

### `29-2035` Magnetic Resonance Imaging Technologists
*Strong CTE · Associate's degree · top-5 coverage: 5/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 2.5% | 6215 | ✓ | Healthcare - Labs |
| 0.4% | 6221 | ✓ | Healthcare - Hospitals (General) |
| 0.2% | 6223 | ✓ | Healthcare - Hospitals (Specialty) |
| 0.2% | 6211 | ✓ | Healthcare - Physician Offices |
| 0.1% | 6214 | ✓ | Healthcare - Outpatient |

### `29-2036` Medical Dosimetrists
*Strong CTE · Postsecondary nondegree award · top-5 coverage: 5/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 0.1% | 6223 | ✓ | Healthcare - Hospitals (Specialty) |
| 0.0% | 6211 | ✓ | Healthcare - Physician Offices |
| 0.0% | 4234 | ✓ | Wholesale - Professional Equipment |
| 0.0% | 6221 | ✓ | Healthcare - Hospitals (General) |
| 0.0% | 6214 | ✓ | Healthcare - Outpatient |

### `29-2042` Emergency Medical Technicians
*Strong CTE · Postsecondary nondegree award · top-5 coverage: 3/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 23.1% | 6219 | ✓ | Healthcare - Other Ambulatory |
| 0.7% | 9993 |   |  |
| 0.6% | 6221 | ✓ | Healthcare - Hospitals (General) |
| 0.3% | 5619 |   |  |
| 0.3% | 6214 | ✓ | Healthcare - Outpatient |

### `29-2043` Paramedics
*Strong CTE · Postsecondary nondegree award · top-5 coverage: 3/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 11.4% | 6219 | ✓ | Healthcare - Other Ambulatory |
| 0.7% | 9993 |   |  |
| 0.3% | 6221 | ✓ | Healthcare - Hospitals (General) |
| 0.2% | 5619 |   |  |
| 0.1% | 7131 | ✓ | Arts - Amusement Parks/Arcades |

### `29-2051` Dietetic Technicians
*Strong CTE · Associate's degree · top-5 coverage: 5/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 0.4% | 6231 | ✓ | Healthcare - Nursing Facilities |
| 0.3% | 6223 | ✓ | Healthcare - Hospitals (Specialty) |
| 0.2% | 6233 | ✓ | Healthcare - Continuing Care |
| 0.2% | 6221 | ✓ | Healthcare - Hospitals (General) |
| 0.1% | 6222 | ✓ | Healthcare - Hospitals (Psych/Substance) |

### `29-2053` Psychiatric Technicians
*Strong CTE · Postsecondary nondegree award · top-5 coverage: 4/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 12.3% | 6222 | ✓ | Healthcare - Hospitals (Psych/Substance) |
| 2.0% | 6232 | ✓ | Healthcare - Residential Care |
| 1.9% | 6213 | ✓ | Healthcare - Other Practitioners |
| 0.9% | 6214 | ✓ | Healthcare - Outpatient |
| 0.7% | 6239 |   |  |

### `29-2055` Surgical Technologists
*Strong CTE · Postsecondary nondegree award · top-5 coverage: 5/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 1.3% | 6221 | ✓ | Healthcare - Hospitals (General) |
| 1.2% | 6214 | ✓ | Healthcare - Outpatient |
| 0.4% | 6211 | ✓ | Healthcare - Physician Offices |
| 0.4% | 6223 | ✓ | Healthcare - Hospitals (Specialty) |
| 0.2% | 6212 | ✓ | Healthcare - Dental |

### `29-2056` Veterinary Technologists and Technicians
*Strong CTE · Associate's degree · top-5 coverage: 1/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 13.1% | 5419 |   |  |
| 0.8% | 8133 |   |  |
| 0.4% | 8129 |   |  |
| 0.1% | 5417 | ✓ | Professional - Scientific R&D |
| 0.1% | 7121 |   |  |

### `29-2057` Ophthalmic Medical Technicians
*Strong CTE · Postsecondary nondegree award · top-5 coverage: 4/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 1.8% | 6213 | ✓ | Healthcare - Other Practitioners |
| 1.6% | 6211 | ✓ | Healthcare - Physician Offices |
| 0.3% | 4561 |   |  |
| 0.1% | 6214 | ✓ | Healthcare - Outpatient |
| 0.1% | 6223 | ✓ | Healthcare - Hospitals (Specialty) |

### `29-2061` Licensed Practical and Licensed Vocational Nurses
*Strong CTE · Postsecondary nondegree award · top-5 coverage: 5/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 12.4% | 6231 | ✓ | Healthcare - Nursing Facilities |
| 4.9% | 6216 | ✓ | Healthcare - Home Health |
| 4.5% | 6233 | ✓ | Healthcare - Continuing Care |
| 3.5% | 6222 | ✓ | Healthcare - Hospitals (Psych/Substance) |
| 3.0% | 6214 | ✓ | Healthcare - Outpatient |

### `29-2072` Medical Records Specialists
*Strong CTE · Postsecondary nondegree award · top-5 coverage: 4/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 1.3% | 6211 | ✓ | Healthcare - Physician Offices |
| 1.1% | 5611 |   |  |
| 0.8% | 6221 | ✓ | Healthcare - Hospitals (General) |
| 0.7% | 6214 | ✓ | Healthcare - Outpatient |
| 0.7% | 6223 | ✓ | Healthcare - Hospitals (Specialty) |

### `29-2099` Health Technologists and Technicians, All Other
*Strong CTE · Postsecondary nondegree award · top-5 coverage: 5/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 4.8% | 6214 | ✓ | Healthcare - Outpatient |
| 1.3% | 6215 | ✓ | Healthcare - Labs |
| 1.0% | 6223 | ✓ | Healthcare - Hospitals (Specialty) |
| 1.0% | 6221 | ✓ | Healthcare - Hospitals (General) |
| 0.9% | 6211 | ✓ | Healthcare - Physician Offices |

### `29-9021` Health Information Technologists and Medical Registrars
*Strong CTE · Postsecondary nondegree award · top-5 coverage: 4/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 0.3% | 6221 | ✓ | Healthcare - Hospitals (General) |
| 0.2% | 6222 | ✓ | Healthcare - Hospitals (Psych/Substance) |
| 0.2% | 6223 | ✓ | Healthcare - Hospitals (Specialty) |
| 0.1% | 5611 |   |  |
| 0.1% | 6211 | ✓ | Healthcare - Physician Offices |

### `29-9093` Surgical Assistants
*Strong CTE · Postsecondary nondegree award · top-5 coverage: 5/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 0.5% | 6212 | ✓ | Healthcare - Dental |
| 0.1% | 6221 | ✓ | Healthcare - Hospitals (General) |
| 0.1% | 6211 | ✓ | Healthcare - Physician Offices |
| 0.1% | 6214 | ✓ | Healthcare - Outpatient |
| 0.1% | 6223 | ✓ | Healthcare - Hospitals (Specialty) |

### `29-9099` Healthcare Practitioners and Technical Workers, All Other
*Strong CTE · Postsecondary nondegree award · top-5 coverage: 4/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 0.5% | 6219 | ✓ | Healthcare - Other Ambulatory |
| 0.2% | 6221 | ✓ | Healthcare - Hospitals (General) |
| 0.2% | 9991 |   |  |
| 0.2% | 6213 | ✓ | Healthcare - Other Practitioners |
| 0.1% | 6223 | ✓ | Healthcare - Hospitals (Specialty) |

### `31-1131` Nursing Assistants
*Strong CTE · Postsecondary nondegree award · top-5 coverage: 5/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 33.2% | 6231 | ✓ | Healthcare - Nursing Facilities |
| 15.8% | 6233 | ✓ | Healthcare - Continuing Care |
| 9.9% | 6223 | ✓ | Healthcare - Hospitals (Specialty) |
| 7.2% | 6221 | ✓ | Healthcare - Hospitals (General) |
| 5.1% | 6216 | ✓ | Healthcare - Home Health |

### `31-2011` Occupational Therapy Assistants
*Strong CTE · Associate's degree · top-5 coverage: 5/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 1.8% | 6213 | ✓ | Healthcare - Other Practitioners |
| 0.8% | 6223 | ✓ | Healthcare - Hospitals (Specialty) |
| 0.5% | 6231 | ✓ | Healthcare - Nursing Facilities |
| 0.3% | 6117 | ✓ | Education - Educational Support Services |
| 0.2% | 6216 | ✓ | Healthcare - Home Health |

### `31-2021` Physical Therapist Assistants
*Strong CTE · Associate's degree · top-5 coverage: 5/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 4.3% | 6213 | ✓ | Healthcare - Other Practitioners |
| 1.2% | 6223 | ✓ | Healthcare - Hospitals (Specialty) |
| 0.7% | 6216 | ✓ | Healthcare - Home Health |
| 0.7% | 6231 | ✓ | Healthcare - Nursing Facilities |
| 0.3% | 6221 | ✓ | Healthcare - Hospitals (General) |

### `31-9011` Massage Therapists
*Strong CTE · Postsecondary nondegree award · top-5 coverage: 5/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 6.4% | 8121 | ✓ | Services - Personal Care |
| 2.4% | 6213 | ✓ | Healthcare - Other Practitioners |
| 0.5% | 7211 | ✓ | Hospitality - Hotels/Motels |
| 0.2% | 6115 | ✓ | Education - Technical/Trade Schools |
| 0.1% | 6211 | ✓ | Healthcare - Physician Offices |

### `31-9091` Dental Assistants
*Strong CTE · Postsecondary nondegree award · top-5 coverage: 3/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 33.2% | 6212 | ✓ | Healthcare - Dental |
| 0.6% | 6214 | ✓ | Healthcare - Outpatient |
| 0.3% | 6211 | ✓ | Healthcare - Physician Offices |
| 0.2% | 9991 |   |  |
| 0.1% | 5611 |   |  |

### `31-9092` Medical Assistants
*Strong CTE · Postsecondary nondegree award · top-5 coverage: 5/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 15.2% | 6211 | ✓ | Healthcare - Physician Offices |
| 6.6% | 6214 | ✓ | Healthcare - Outpatient |
| 5.3% | 6213 | ✓ | Healthcare - Other Practitioners |
| 2.0% | 6221 | ✓ | Healthcare - Hospitals (General) |
| 1.8% | 6219 | ✓ | Healthcare - Other Ambulatory |

### `31-9094` Medical Transcriptionists
*Strong CTE · Postsecondary nondegree award · top-5 coverage: 4/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 2.2% | 5614 |   |  |
| 0.7% | 6211 | ✓ | Healthcare - Physician Offices |
| 0.4% | 6215 | ✓ | Healthcare - Labs |
| 0.2% | 6214 | ✓ | Healthcare - Outpatient |
| 0.2% | 6213 | ✓ | Healthcare - Other Practitioners |

### `31-9097` Phlebotomists
*Strong CTE · Postsecondary nondegree award · top-5 coverage: 5/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 13.7% | 6215 | ✓ | Healthcare - Labs |
| 6.8% | 6219 | ✓ | Healthcare - Other Ambulatory |
| 0.8% | 6221 | ✓ | Healthcare - Hospitals (General) |
| 0.4% | 6242 | ✓ | Social Services - Community Emergency Relief |
| 0.4% | 6211 | ✓ | Healthcare - Physician Offices |

### `33-1021` First-Line Supervisors of Firefighting and Prevention Workers
*Strong CTE · Postsecondary nondegree award · top-5 coverage: 1/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 1.4% | 9993 |   |  |
| 0.9% | 5619 |   |  |
| 0.1% | 9992 |   |  |
| 0.1% | 9991 |   |  |
| 0.0% | 6242 | ✓ | Social Services - Community Emergency Relief |

### `33-2011` Firefighters
*Strong CTE · Postsecondary nondegree award · top-5 coverage: 1/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 5.8% | 5619 |   |  |
| 5.0% | 9993 |   |  |
| 0.5% | 9992 |   |  |
| 0.3% | 9991 |   |  |
| 0.2% | 6219 | ✓ | Healthcare - Other Ambulatory |

### `33-2021` Fire Inspectors and Investigators
*Strong CTE · Postsecondary nondegree award · top-5 coverage: 1/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 0.2% | 9993 |   |  |
| 0.1% | 5616 | ✓ | Admin - Investigation/Security |
| 0.1% | 9992 |   |  |
| 0.0% | 5619 |   |  |
| 0.0% | 5242 |   |  |

### `35-2013` Cooks, Private Household
*Strong CTE · Postsecondary nondegree award · top-5 coverage: 0/1*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 0.1% | 8131 |   |  |

### `39-4011` Embalmers
*Strong CTE · Associate's degree · top-5 coverage: 0/1*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 2.4% | 8122 |   |  |

### `39-4031` Morticians, Undertakers, and Funeral Arrangers
*Strong CTE · Associate's degree · top-5 coverage: 0/2*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 17.4% | 8122 |   |  |
| 0.0% | 9991 |   |  |

### `39-5011` Barbers
*Strong CTE · Postsecondary nondegree award · top-5 coverage: 2/2*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 2.0% | 8121 | ✓ | Services - Personal Care |
| 0.0% | 6115 | ✓ | Education - Technical/Trade Schools |

### `39-5012` Hairdressers, Hairstylists, and Cosmetologists
*Strong CTE · Postsecondary nondegree award · top-5 coverage: 3/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 36.2% | 8121 | ✓ | Services - Personal Care |
| 0.5% | 4550 |   |  |
| 0.4% | 4561 |   |  |
| 0.3% | 6115 | ✓ | Education - Technical/Trade Schools |
| 0.2% | 5121 | ✓ | Media - Motion Picture/Video |

### `39-5091` Makeup Artists, Theatrical and Performance
*Strong CTE · Postsecondary nondegree award · top-5 coverage: 3/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 0.3% | 5121 | ✓ | Media - Motion Picture/Video |
| 0.3% | 8121 | ✓ | Services - Personal Care |
| 0.1% | 7131 | ✓ | Arts - Amusement Parks/Arcades |
| 0.0% | 5161 |   |  |
| 0.0% | 7111 |   |  |

### `39-5092` Manicurists and Pedicurists
*Strong CTE · Postsecondary nondegree award · top-5 coverage: 3/4*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 19.4% | 8121 | ✓ | Services - Personal Care |
| 0.2% | 8129 |   |  |
| 0.1% | 7211 | ✓ | Hospitality - Hotels/Motels |
| 0.0% | 7139 | ✓ | Arts - Other Amusement/Recreation |

### `39-5094` Skincare Specialists
*Strong CTE · Postsecondary nondegree award · top-5 coverage: 4/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 6.7% | 8121 | ✓ | Services - Personal Care |
| 0.2% | 6211 | ✓ | Healthcare - Physician Offices |
| 0.2% | 4561 |   |  |
| 0.2% | 6213 | ✓ | Healthcare - Other Practitioners |
| 0.1% | 7211 | ✓ | Hospitality - Hotels/Motels |

### `43-4161` Human Resources Assistants, Except Payroll and Timekeeping
*Strong CTE · Associate's degree · top-5 coverage: 0/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 0.4% | 9991 |   |  |
| 0.3% | 5511 |   |  |
| 0.3% | 4889 |   |  |
| 0.2% | 5611 |   |  |
| 0.2% | 4852 |   |  |

### `43-9031` Desktop Publishers
*Strong CTE · Associate's degree · top-5 coverage: 3/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 0.6% | 5131 |   |  |
| 0.1% | 3231 | ✓ | Manufacturing - Printing |
| 0.0% | 6114 | ✓ | Education - Business/Management Training |
| 0.0% | 5418 | ✓ | Professional - Advertising/PR |
| 0.0% | 8139 |   |  |

### `49-2021` Radio, Cellular, and Tower Equipment Installers and Repairers
*Strong CTE · Associate's degree · top-5 coverage: 1/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 1.1% | 8112 |   |  |
| 0.5% | 5170 |   |  |
| 0.3% | 3342 |   |  |
| 0.2% | 2371 | ✓ | Construction - Utility Systems |
| 0.1% | 4492 |   |  |

### `49-2022` Telecommunications Equipment Installers and Repairers, Except Line Installers
*Strong CTE · Postsecondary nondegree award · top-5 coverage: 2/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 16.6% | 5170 |   |  |
| 4.6% | 8112 |   |  |
| 0.8% | 2382 | ✓ | Construction - HVAC/Plumbing/Electrical |
| 0.6% | 5162 |   |  |
| 0.2% | 5415 | ✓ | Professional - Computer Systems Design |

### `49-2091` Avionics Technicians
*Strong CTE · Associate's degree · top-5 coverage: 3/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 2.8% | 4881 | ✓ | Transportation - Support Activities (Air) |
| 1.6% | 3364 | ✓ | Manufacturing - Aerospace |
| 0.7% | 4812 |   |  |
| 0.2% | 8112 |   |  |
| 0.2% | 4811 | ✓ | Transportation - Air |

### `49-2093` Electrical and Electronics Installers and Repairers, Transportation Equipment
*Strong CTE · Postsecondary nondegree award · top-5 coverage: 2/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 1.6% | 4821 |   |  |
| 0.4% | 8112 |   |  |
| 0.1% | 3366 | ✓ | Manufacturing - Ship/Boat |
| 0.1% | 4882 |   |  |
| 0.0% | 4231 | ✓ | Wholesale - Motor Vehicles/Parts |

### `49-2094` Electrical and Electronics Repairers, Commercial and Industrial Equipment
*Strong CTE · Postsecondary nondegree award · top-5 coverage: 2/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 2.8% | 8112 |   |  |
| 1.4% | 4862 |   |  |
| 1.2% | 3221 |   |  |
| 0.9% | 2111 | ✓ | Mining - Oil/Gas Extraction |
| 0.8% | 3241 | ✓ | Manufacturing - Petroleum/Coal |

### `49-2095` Electrical and Electronics Repairers, Powerhouse, Substation, and Relay
*Strong CTE · Postsecondary nondegree award · top-5 coverage: 3/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 3.6% | 2211 | ✓ | Utilities - Electric Power |
| 0.4% | 2212 | ✓ | Utilities - Natural Gas |
| 0.3% | 2371 | ✓ | Construction - Utility Systems |
| 0.2% | 4862 |   |  |
| 0.2% | 3353 |   |  |

### `49-2097` Audiovisual Equipment Installers and Repairers
*Strong CTE · Postsecondary nondegree award · top-5 coverage: 1/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 2.4% | 4492 |   |  |
| 1.7% | 8112 |   |  |
| 0.9% | 3343 |   |  |
| 0.2% | 2382 | ✓ | Construction - HVAC/Plumbing/Electrical |
| 0.1% | 7113 |   |  |

### `49-3011` Aircraft Mechanics and Service Technicians
*Strong CTE · Postsecondary nondegree award · top-5 coverage: 3/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 17.4% | 4881 | ✓ | Transportation - Support Activities (Air) |
| 12.0% | 4812 |   |  |
| 6.9% | 4879 |   |  |
| 5.5% | 4811 | ✓ | Transportation - Air |
| 4.6% | 3364 | ✓ | Manufacturing - Aerospace |

### `49-3023` Automotive Service Technicians and Mechanics
*Strong CTE · Postsecondary nondegree award · top-5 coverage: 3/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 23.7% | 8111 | ✓ | Services - Auto Repair/Maintenance |
| 19.8% | 4411 | ✓ | Retail - Auto Dealers |
| 8.8% | 4413 |   |  |
| 3.7% | 4884 |   |  |
| 3.4% | 4231 | ✓ | Wholesale - Motor Vehicles/Parts |

### `49-3052` Motorcycle Mechanics
*Strong CTE · Postsecondary nondegree award · top-5 coverage: 1/4*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 7.0% | 4412 |   |  |
| 1.7% | 8114 |   |  |
| 0.3% | 3369 |   |  |
| 0.0% | 4231 | ✓ | Wholesale - Motor Vehicles/Parts |

### `49-9021` Heating, Air Conditioning, and Refrigeration Mechanics and Installers
*Strong CTE · Postsecondary nondegree award · top-5 coverage: 1/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 13.5% | 4572 |   |  |
| 12.1% | 2382 | ✓ | Construction - HVAC/Plumbing/Electrical |
| 3.2% | 8113 |   |  |
| 1.8% | 5612 |   |  |
| 1.7% | 8114 |   |  |

### `49-9062` Medical Equipment Repairers
*Strong CTE · Associate's degree · top-5 coverage: 3/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 10.0% | 8112 |   |  |
| 3.4% | 4234 | ✓ | Wholesale - Professional Equipment |
| 0.4% | 3391 | ✓ | Manufacturing - Medical Equipment |
| 0.4% | 6214 | ✓ | Healthcare - Outpatient |
| 0.3% | 4561 |   |  |

### `49-9081` Wind Turbine Service Technicians
*Strong CTE · Postsecondary nondegree award · top-5 coverage: 2/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 1.0% | 8113 |   |  |
| 0.9% | 2211 | ✓ | Utilities - Electric Power |
| 0.3% | 3336 |   |  |
| 0.2% | 2371 | ✓ | Construction - Utility Systems |
| 0.1% | 4238 |   |  |

### `49-9092` Commercial Divers
*Strong CTE · Postsecondary nondegree award · top-5 coverage: 1/2*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 0.5% | 2379 | ✓ | Construction - Other Heavy |
| 0.3% | 5619 |   |  |

### `51-4111` Tool and Die Makers
*Strong CTE · Postsecondary nondegree award · top-5 coverage: 3/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 6.3% | 3335 | ✓ | Manufacturing - Metalworking Machinery |
| 2.5% | 3315 |   |  |
| 1.8% | 3363 | ✓ | Manufacturing - Motor Vehicle Parts |
| 1.4% | 3313 |   |  |
| 0.8% | 3327 | ✓ | Manufacturing - Machine Shops |

### `51-5111` Prepress Technicians and Workers
*Strong CTE · Postsecondary nondegree award · top-5 coverage: 3/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 4.0% | 3231 | ✓ | Manufacturing - Printing |
| 0.6% | 3222 |   |  |
| 0.4% | 5131 |   |  |
| 0.3% | 5418 | ✓ | Professional - Advertising/PR |
| 0.1% | 3328 | ✓ | Manufacturing - Coating/Engraving |

### `51-9162` Computer Numerically Controlled Tool Programmers
*Strong CTE · Postsecondary nondegree award · top-5 coverage: 3/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 1.6% | 3327 | ✓ | Manufacturing - Machine Shops |
| 1.6% | 3335 | ✓ | Manufacturing - Metalworking Machinery |
| 0.4% | 3315 |   |  |
| 0.4% | 3364 | ✓ | Manufacturing - Aerospace |
| 0.3% | 3336 |   |  |

### `53-2021` Air Traffic Controllers
*Strong CTE · Associate's degree · top-5 coverage: 3/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 0.9% | 9991 |   |  |
| 0.5% | 4881 | ✓ | Transportation - Support Activities (Air) |
| 0.1% | 6115 | ✓ | Education - Technical/Trade Schools |
| 0.1% | 4812 |   |  |
| 0.1% | 4811 | ✓ | Transportation - Air |

### `53-3032` Heavy and Tractor-Trailer Truck Drivers
*Strong CTE · Postsecondary nondegree award · top-5 coverage: 1/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 58.1% | 4840 |   |  |
| 44.5% | 4884 |   |  |
| 24.9% | 4572 |   |  |
| 23.1% | 5621 | ✓ | Waste - Collection |
| 18.6% | 3270 |   |  |

### `53-5021` Captains, Mates, and Pilots of Water Vessels
*Strong CTE · Postsecondary nondegree award · top-5 coverage: 1/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 28.7% | 4832 |   |  |
| 25.3% | 4872 |   |  |
| 12.4% | 4831 |   |  |
| 9.0% | 4883 |   |  |
| 0.7% | 2379 | ✓ | Construction - Other Heavy |

### `53-5022` Motorboat Operators
*Strong CTE · Postsecondary nondegree award · top-5 coverage: 2/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 2.6% | 4872 |   |  |
| 0.5% | 4832 |   |  |
| 0.3% | 4883 |   |  |
| 0.1% | 2379 | ✓ | Construction - Other Heavy |
| 0.1% | 2213 | ✓ | Utilities - Water/Sewer |

### `53-5031` Ship Engineers
*Strong CTE · Postsecondary nondegree award · top-5 coverage: 1/5*

| pct_total | NAICS-4 | In search list | Label (if listed) |
|---:|---|:---:|---|
| 5.1% | 4832 |   |  |
| 4.9% | 4831 |   |  |
| 2.4% | 4883 |   |  |
| 0.8% | 4872 |   |  |
| 0.1% | 2379 | ✓ | Construction - Other Heavy |

---

## Expansion candidates: top NAICS not in search list

NAICS-4 codes that appear in the top NAICS for direct-CTE SOCs but are NOT in the project's curated search list. Ranked by how many direct-CTE SOCs they're a top-NAICS for, then by aggregate pct_total they bring across those SOCs.

| NAICS-4 | Direct-CTE SOCs it tops | Aggregate pct | Example SOCs |
|---|---:|---:|---|
| `9993` | 36 | 32.0% | `33-3051` (Moderate CTE, 10.0%); `33-2011` (Strong CTE, 5.0%); `33-3012` (Moderate CTE, 2.5%) |
| `9991` | 28 | 12.8% | `13-1031` (Moderate CTE, 2.2%); `33-3021` (Moderate CTE, 1.9%); `53-2021` (Strong CTE, 0.9%) |
| `9992` | 26 | 20.1% | `33-3012` (Moderate CTE, 8.6%); `33-3051` (Moderate CTE, 2.6%); `47-4051` (Moderate CTE, 1.8%) |
| `8112` | 16 | 40.7% | `49-2011` (Moderate CTE, 11.4%); `49-9062` (Strong CTE, 10.0%); `49-2022` (Strong CTE, 4.6%) |
| `8114` | 15 | 43.0% | `49-9031` (Moderate CTE, 14.4%); `49-3051` (Moderate CTE, 6.0%); `51-6093` (Moderate CTE, 5.5%) |
| `2122` | 15 | 39.5% | `47-5041` (Moderate CTE, 16.4%); `49-3042` (Moderate CTE, 8.0%); `47-5049` (Moderate CTE, 3.0%) |
| `2121` | 14 | 42.2% | `47-2073` (Moderate CTE, 12.1%); `47-5022` (Moderate CTE, 7.6%); `47-5041` (Moderate CTE, 7.1%) |
| `8113` | 14 | 42.2% | `49-9041` (Moderate CTE, 19.7%); `51-4121` (Moderate CTE, 6.5%); `49-3042` (Moderate CTE, 4.0%) |
| `3312` | 14 | 32.1% | `51-4031` (Moderate CTE, 7.8%); `51-1011` (Moderate CTE, 5.4%); `51-4023` (Moderate CTE, 5.1%) |
| `7112` | 13 | 18.3% | `27-2021` (Moderate CTE, 8.5%); `39-2021` (Moderate CTE, 4.8%); `39-2011` (Moderate CTE, 1.3%) |
| `3315` | 12 | 29.2% | `51-4033` (Moderate CTE, 8.2%); `51-4071` (Moderate CTE, 7.5%); `51-9061` (Moderate CTE, 5.7%) |
| `5611` | 12 | 12.1% | `43-3031` (Moderate CTE, 5.0%); `43-1011` (Moderate CTE, 3.5%); `29-2072` (Strong CTE, 1.1%) |
| `5619` | 12 | 10.1% | `33-2011` (Strong CTE, 5.8%); `17-3031` (Moderate CTE, 1.0%); `41-9099` (Moderate CTE, 0.9%) |
| `5511` | 12 | 2.5% | `43-3011` (Moderate CTE, 0.5%); `43-4131` (Moderate CTE, 0.5%); `43-3051` (Moderate CTE, 0.5%) |
| `4883` | 11 | 28.5% | `53-5021` (Strong CTE, 9.0%); `49-3042` (Moderate CTE, 5.5%); `49-1011` (Moderate CTE, 4.7%) |
| `7111` | 11 | 28.2% | `27-2042` (Moderate CTE, 15.8%); `27-2011` (Moderate CTE, 4.9%); `27-2031` (Moderate CTE, 2.5%) |
| `3311` | 11 | 24.9% | `49-9041` (Moderate CTE, 9.0%); `51-4023` (Moderate CTE, 7.8%); `47-2111` (Moderate CTE, 2.9%) |
| `4821` | 10 | 59.8% | `53-4031` (Moderate CTE, 20.1%); `53-4011` (Moderate CTE, 17.1%); `53-4022` (Moderate CTE, 6.4%) |
| `5241` | 10 | 36.1% | `43-4051` (Moderate CTE, 10.6%); `13-1031` (Moderate CTE, 9.4%); `43-9041` (Moderate CTE, 7.2%) |
| `4882` | 10 | 30.0% | `49-3043` (Moderate CTE, 16.4%); `53-4022` (Moderate CTE, 2.9%); `53-4031` (Moderate CTE, 2.4%) |
| `3336` | 10 | 18.7% | `51-4041` (Moderate CTE, 8.0%); `51-9161` (Moderate CTE, 4.7%); `17-3026` (Strong CTE, 1.7%) |
| `7113` | 10 | 11.6% | `33-9032` (Moderate CTE, 6.6%); `27-4011` (Strong CTE, 2.2%); `33-1091` (Moderate CTE, 0.8%) |
| `4812` | 9 | 54.4% | `53-2012` (Moderate CTE, 33.8%); `49-3011` (Strong CTE, 12.0%); `53-2031` (Moderate CTE, 3.0%) |
| `8129` | 9 | 42.2% | `39-2021` (Moderate CTE, 33.4%); `39-1022` (Moderate CTE, 2.9%); `39-2011` (Moderate CTE, 2.1%) |
| `4831` | 9 | 39.6% | `43-4051` (Moderate CTE, 14.6%); `53-5021` (Strong CTE, 12.4%); `53-5031` (Strong CTE, 4.9%) |
| `5411` | 9 | 37.9% | `23-2011` (Strong CTE, 23.0%); `43-6012` (Moderate CTE, 10.4%); `23-2093` (Moderate CTE, 1.8%) |
| `2123` | 9 | 32.4% | `47-5022` (Moderate CTE, 14.1%); `47-2073` (Moderate CTE, 10.6%); `47-5041` (Moderate CTE, 4.1%) |
| `4238` | 9 | 28.9% | `41-4012` (Moderate CTE, 14.8%); `49-3042` (Moderate CTE, 6.0%); `49-3041` (Moderate CTE, 3.5%) |
| `5222` | 9 | 21.5% | `43-4131` (Moderate CTE, 11.6%); `43-1011` (Moderate CTE, 3.6%); `43-3011` (Moderate CTE, 3.5%) |
| `3314` | 9 | 19.1% | `51-4021` (Moderate CTE, 10.5%); `51-4081` (Moderate CTE, 4.2%); `51-4023` (Moderate CTE, 1.7%) |
