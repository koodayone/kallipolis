# Kallipolis Ontology

8 node types · 9 edge types · ~274K nodes · ~8.5M edges

## Nodes

### Curriculum Side

| Node | Properties | Constraint | Source |
|------|-----------|------------|--------|
| **College** | name, city, state, region | name IS UNIQUE | Pipeline config |
| **Department** | name | name IS UNIQUE | College catalog PDFs |
| **Course** | code, college, name, department, units, description, prerequisites, learning_outcomes, course_objectives, skill_mappings, transfer_status, url | (code, college) IS UNIQUE | College catalog PDFs |
| **Skill** | name | name IS UNIQUE | AI-derived from course learning outcomes |
| **Student** | uuid | uuid IS UNIQUE | Synthetic, calibrated to DataMart |

### Industry Side

| Node | Properties | Constraint | Source |
|------|-----------|------------|--------|
| **Region** | name | name IS UNIQUE | EDD OEWS metro area definitions |
| **Occupation** | soc_code, title, description, annual_wage | soc_code IS UNIQUE | EDD OEWS 2025 |
| **Employer** | name, sector | name IS UNIQUE | EDD HWOL + web research |

## Relationships

| Relationship | From → To | Properties | Count |
|-------------|-----------|------------|-------|
| **OFFERS** | College → Department | — | 1,916 |
| **CONTAINS** | Department → Course | — | 26,654 |
| **DEVELOPS** | Course → Skill | — | 149,919 |
| **ENROLLED_IN** | Student → Course | grade, term, status | 2,031,208 |
| **HAS_SKILL** | Student → Skill | — | 6,266,833 |
| **IN_MARKET** | College → Region | — | 26 |
| **IN_MARKET** | Employer → Region | — | 95 |
| **DEMANDS** | Region → Occupation | employment | 3,525 |
| **REQUIRES_SKILL** | Occupation → Skill | — | 4,216 |
| **HIRES_FOR** | Employer → Occupation | — | 176 |

## Graph Diagram

```
College ──OFFERS──▶ Department ──CONTAINS──▶ Course ──DEVELOPS──▶ Skill
   │                                            ▲                   ▲ │
   │                                 ENROLLED_IN│          HAS_SKILL│ │
   │                                            │                   │ │
   │                                         Student ───────────────┘ │
   │                                                                  │
   ├──IN_MARKET──▶ Region ◀──IN_MARKET── Employer                    │
                     │                      │                         │
                     │DEMANDS               │HIRES_FOR                │
                     ▼                      ▼                         │
                  Occupation ──REQUIRES_SKILL──────────────────────────┘
```

Skill is the bridge node connecting curriculum to industry.

## Key Traversals

**Workforce alignment** — what occupations match our curriculum:
```cypher
MATCH (c:College {name: $college})-[:IN_MARKET]->(r:Region)-[:DEMANDS]->(occ:Occupation)
      -[:REQUIRES_SKILL]->(sk:Skill)<-[:DEVELOPS]-(course:Course {college: $college})
RETURN occ.title, count(DISTINCT sk) AS skills_aligned
ORDER BY skills_aligned DESC
```

**Employer matching** — which employers need skills we produce:
```cypher
MATCH (c:College {name: $college})-[:IN_MARKET]->(r:Region)<-[:IN_MARKET]-(emp:Employer)
      -[:HIRES_FOR]->(occ:Occupation)-[:REQUIRES_SKILL]->(sk:Skill)
      <-[:DEVELOPS]-(course:Course {college: $college})
RETURN emp.name, emp.sector, count(DISTINCT sk) AS skills_aligned
ORDER BY skills_aligned DESC
```

**Skill gap** — what the market needs that we don't teach:
```cypher
MATCH (emp:Employer {name: $employer})-[:HIRES_FOR]->(occ:Occupation)
      -[:REQUIRES_SKILL]->(sk:Skill)
WHERE NOT EXISTS { MATCH (course:Course {college: $college})-[:DEVELOPS]->(sk) }
RETURN sk.name, collect(DISTINCT occ.title) AS needed_for
```

**Student qualification** — which students have skills an employer needs:
```cypher
MATCH (emp:Employer {name: $employer})-[:HIRES_FOR]->(occ:Occupation)
      -[:REQUIRES_SKILL]->(sk:Skill)<-[:HAS_SKILL]-(st:Student)
WHERE EXISTS { MATCH (st)-[:ENROLLED_IN]->(c:Course {college: $college}) }
RETURN sk.name, count(DISTINCT st) AS students
ORDER BY students DESC
```

## Scale (26 Bay Area colleges)

| Entity | Count |
|--------|-------|
| Colleges | 26 |
| Departments | 744 |
| Courses | 26,204 |
| Skills | 4,951 |
| Students | 241,778 |
| Regions | 8 |
| Occupations | 724 |
| Employers | 74 |
| Total nodes | ~274,500 |
| Total edges | ~8,483,000 |

## Data Generation Methodology

### Stage 1: Course Catalog Extraction

**Source:** Official college catalog PDFs published under California Title 5 requirements. Each of the 116 California community colleges publishes a catalog annually containing every approved course — its code, title, department, units, description, prerequisites, learning outcomes, course objectives, transfer status, and grading policy.

**Process:** `pipeline/scraper_pdf.py` downloads the catalog PDF for each college and uses Gemini Flash to extract structured course data from the pages. A regex-based course code detector (e.g., "BUS 101", "CS 1A") identifies course pages, which are batched in groups of 25 and sent to the LLM for extraction. The output is a `RawCourse` object per course, cached as `{college}_raw.json`.

**Scale:** 26 Bay Area colleges processed, yielding 26,204 courses across 744 departments.

### Stage 2: Skill Enrichment

**Source:** The extracted course data from Stage 1, combined with a 108-skill seed taxonomy derived from O*NET (the US Department of Labor's occupational information network).

**Process:** `pipeline/skills.py` sends batches of courses to Gemini Flash with instructions to extract 3-6 workforce-relevant skills per course. The LLM is constrained to prefer skill names from the seed taxonomy (e.g., "Programming", "Clinical Patient Care", "Regulatory Compliance") and may introduce novel skill names only when the course teaches something genuinely not covered by the taxonomy. The output is an enriched course with a `skill_mappings` array, cached as `{college}_enriched.json`.

**Result:** 4,951 unique skills across all 26 colleges, with 149,919 Course → DEVELOPS → Skill edges.

### Stage 3: Synthetic Student Generation

**Source:** Per-college calibration data derived from two California public data systems:

- **DataMart** (datamart.cccco.edu) — the California Community Colleges Chancellor's Office Management Information System. Provides the Grade Distribution Summary report, which gives actual grade distributions (A/B/C/D/F/W/P percentages) broken out by 2-digit TOP code (Taxonomy of Programs) group per college. This is the empirical basis for how synthetic students perform in different disciplines.

- **College institutional data** — published enrollment headcounts, full-time/part-time ratios, and fall-to-winter retention rates from each college's own fact sheets and institutional metrics pages.

**Process:** `pipeline/students.py` generates synthetic students for each college using a calibration config at `pipeline/calibrations/{college}.json`. Each config contains:
- `enrollment` — verified headcount from the college's published data
- `success_rate` — college-wide course success rate from DataMart
- `retention_rate` — fall-to-winter retention from college institutional metrics
- `ft_ratio` — full-time student percentage from college fact sheets
- `grade_distribution` — college-wide grade percentages from DataMart
- `top_group_enrollment_share` — enrollment distribution across 2-digit TOP code disciplines from DataMart
- `top_group_success_rate` — per-discipline success rates from DataMart (e.g., 97% in Engineering vs 72% in Mathematics at Foothill)
- `top_group_grades` — per-discipline grade distributions from DataMart
- `dept_to_top_group` — mapping of college-specific department names to DataMart TOP code groups

The generator uses a success-rate-gated grading model: for each enrollment, the student's probability of passing depends on the discipline-specific success rate, and the grade distribution within pass/fail follows the discipline-specific distribution from DataMart. Students are assigned a primary department (weighted by enrollment share), persist across terms based on the retention rate (geometric decay), and take courses from their department cluster (65% affinity) and GE pool (35%). Only completed enrollments (A/B/C/P grades) produce HAS_SKILL edges.

**Validation:** After generation, the synthetic population's aggregate success rate is compared against the DataMart target. Typical deviation is <1%.

**Privacy:** No education records are accessed. All calibration data comes from publicly published aggregates. Synthetic students are generated entities, not de-identified real students. There is zero FERPA exposure.

**Scale:** 241,778 students, 2,031,208 enrollments, 6,266,833 HAS_SKILL edges across 26 colleges.

### Stage 4: Regional Occupation Data

**Source:** California Employment Development Department (EDD) Occupational Employment and Wage Statistics (OEWS) survey results, published June 2025 with May 2024 employment data and Q1 2025 wages. Downloaded as XLSX files from `labormarketinfo.edd.ca.gov`, one file per metropolitan statistical area (MSA) or metropolitan division (MD).

**Process:** `pipeline/industry/oews_parser.py` reads the 8 Bay Area metro XLSX files. Each file's "OEWS Data" sheet contains rows with SOC (Standard Occupational Classification) code, occupation title, employment count, and mean annual wage. Broad category rows (SOC codes ending in -0000) are filtered out, leaving only detailed occupation codes. Occupations are deduplicated across metros, with wages averaged across regions where data exists.

Occupation descriptions and skill mappings are generated by `pipeline/industry/generate_occupations.py`, which maps each occupation title to 5-8 skills from the existing 4,951-skill vocabulary using SOC group-based base skills and title keyword pattern matching. All skill names are validated against the graph — zero invented skills are permitted.

**Metros covered:**
- San Jose-Sunnyvale-Santa Clara MSA
- Oakland-Fremont-Berkeley MD
- San Francisco-San Mateo-Redwood City MD
- Santa Rosa-Petaluma MSA
- Napa MSA
- Vallejo MSA
- Santa Cruz-Watsonville MSA
- San Rafael MD

**Scale:** 8 regions, 724 detailed occupations, 3,525 DEMANDS edges (with employment counts), 4,216 REQUIRES_SKILL edges.

### Stage 5: Employer Data

**Source:** Two complementary data streams:

- **EDD Help Wanted OnLine (HWOL)** — a monthly publication from the EDD Labor Market Information Division that aggregates online job postings data from Burning Glass Technologies (now Lightcast). The XLSX download includes the top 10 employers by job ad volume per metro area, providing the anchor employers (large-scale hirers like Apple, Kaiser Permanente, Stanford Health Care).

- **Web research** — targeted job market searches scoped to each college's city and distinctive skill profile. Each college's top skill clusters (derived from HAS_SKILL aggregation in the graph) define search queries like "HVAC technician jobs Livermore CA" or "video production companies Fremont CA." This surfaces the long-tail employers — local contractors, clinics, manufacturers, and specialized firms — that HWOL's top-10 lists miss but that are often the most relevant CTE partnership candidates.

**Process:** `pipeline/industry/employers.py` loads employer data from `employers.json`. Each employer is mapped to one or more regions (via IN_MARKET) and to the occupations they hire for (via HIRES_FOR, matched by SOC code). The HIRES_FOR → REQUIRES_SKILL chain connects each employer to the skills they need, completing the traversal from curriculum to specific companies.

**Scale:** 74 employers across 8 regions, 95 IN_MARKET edges, 176 HIRES_FOR edges.

## Data Pipeline Summary

| Stage | Script | Input | Output |
|-------|--------|-------|--------|
| Catalog scraping | `pipeline/scraper_pdf.py` | College PDF catalogs | Raw courses |
| Skill enrichment | `pipeline/skills.py` | Raw courses + O*NET seed taxonomy | Enriched courses with skill mappings |
| Curriculum loading | `pipeline/loader.py` | Enriched courses | College, Department, Course, Skill nodes |
| Student generation | `pipeline/students.py` | Enriched courses + DataMart calibrations | Student, ENROLLED_IN, HAS_SKILL |
| Occupation loading | `pipeline/industry/loader.py` | EDD OEWS XLSX files + occupations.json | Region, Occupation, DEMANDS, REQUIRES_SKILL |
| Employer loading | `pipeline/industry/employers.py` | EDD HWOL + web research → employers.json | Employer, IN_MARKET, HIRES_FOR |
