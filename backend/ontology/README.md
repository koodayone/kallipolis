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
| Students | 241,850 |
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

**Source:** Per-college calibration data derived from three California public data systems:

- **DataMart 4-digit TOP code Grade Distribution** (datamart.cccco.edu) — the California Community Colleges Chancellor's Office Management Information System. Provides grade distributions (A/B/C/D/F/W/P percentages) broken out by 4-digit TOP code (Taxonomy of Programs) per college. Each college has 49-114 distinct 4-digit codes (e.g., 0502 Accounting, 0707 Computer Software Development, 1240 Dental Occupations). This is the empirical basis for both enrollment distribution and grade outcomes across disciplines. Parsed by `pipeline/calibrations/parse_top4.py` into per-college JSON files at `pipeline/calibrations/top4/{college}.json`.

- **DataMart Master Course Files** — the authoritative course-level TOP code assignments from each college's MIS submission. Each course prefix (e.g., "CS", "ACTG", "BIOL") maps to a 4-digit TOP code. Downloaded for all 26 colleges, parsed into a global mapping at `pipeline/calibrations/prefix_to_top4.json` with 1,939 entries covering 97% of courses.

- **College institutional data** — published enrollment headcounts, full-time/part-time ratios, and fall-to-winter retention rates from each college's own fact sheets and institutional metrics pages. Stored in `pipeline/calibrations/{college}.json`.

**Process:** `pipeline/students.py` generates synthetic students for each college using the 4-digit TOP code calibration. The algorithm:

1. **Course pooling**: Each enriched course is assigned a 4-digit TOP code via its prefix (using `prefix_to_top4.json`). Courses are grouped into pools by TOP code.

2. **Primary assignment**: Each student is assigned a primary 4-digit TOP code, weighted by the DataMart enrollment share for that code. This determines the student's area of concentration.

3. **Enrollment generation**: For each enrollment, there is a 60% chance of drawing from the student's primary TOP code pool and a 40% chance of drawing from the full TOP code distribution (weighted by enrollment share). This produces realistic course-taking patterns where students concentrate in one area while also taking GE/elective courses across other areas.

4. **Department cap**: A maximum of 6 courses per department per student prevents unrealistic concentration. When a student hits the cap, their enrollment redirects to another TOP code from the full distribution.

5. **Grade assignment**: Each enrollment receives a grade sampled directly from the 4-digit TOP code's grade distribution in the DataMart data. A course in Accounting (0502) uses Accounting's grade distribution; a course in Mathematics (1701) uses Mathematics'. No college-wide averaging.

6. **Skill materialization**: Only completed enrollments (grades A, B, C, P) produce Student → HAS_SKILL → Skill edges, derived from the Course → DEVELOPS → Skill edges of the completed course.

**Key parameters** (from `pipeline/calibrations/{college}.json`):
- `enrollment` — verified headcount from the college's published data
- `ft_ratio` — full-time student percentage (determines course load: FT 4-6 courses/term, PT 1-3)
- `retention_rate` — fall-to-winter retention (geometric decay determines persistence across terms)

**Validation:** After generation, the synthetic population's aggregate success rate is compared against the DataMart target. Typical deviation is <1%. Per-department enrollment shares track the 4-digit TOP code distribution within ~1 percentage point. Primary focus distributions (the department where each student has the most completions) closely mirror the enrollment shares due to the 4-digit granularity — each TOP code maps roughly 1-to-1 with a department, eliminating the dilution that occurs with coarser groupings.

**Privacy:** No education records are accessed. All calibration data comes from publicly published aggregates. Synthetic students are generated entities, not de-identified real students. There is zero FERPA exposure.

**Scale:** 241,850 students, 2,067,687 enrollments across 26 colleges.

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
| TOP4 calibration parsing | `pipeline/calibrations/parse_top4.py` | DataMart 4-digit grade distribution CSV | Per-college TOP4 calibration JSON |
| Student generation | `pipeline/students.py` | Enriched courses + TOP4 calibrations + prefix mapping | Student, ENROLLED_IN, HAS_SKILL |
| Occupation loading | `pipeline/industry/loader.py` | EDD OEWS XLSX files + occupations.json | Region, Occupation, DEMANDS, REQUIRES_SKILL |
| Employer loading | `pipeline/industry/employers.py` | EDD HWOL + web research → employers.json | Employer, IN_MARKET, HIRES_FOR |
