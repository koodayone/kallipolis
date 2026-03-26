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

## Data Pipeline

| Stage | Script | Input | Output |
|-------|--------|-------|--------|
| Catalog scraping | `pipeline/scraper_pdf.py` | College PDF catalogs | Raw courses |
| Skill enrichment | `pipeline/skills.py` | Raw courses | Enriched courses with skill mappings |
| Curriculum loading | `pipeline/loader.py` | Enriched courses | College, Department, Course, Skill nodes |
| Student generation | `pipeline/students.py` | Enriched courses + calibrations | Student, ENROLLED_IN, HAS_SKILL |
| Occupation loading | `pipeline/industry/loader.py` | OEWS parsed data + occupations.json | Region, Occupation, DEMANDS, REQUIRES_SKILL |
| Employer loading | `pipeline/industry/employers.py` | employers.json | Employer, IN_MARKET, HIRES_FOR |

Calibration configs per college: `pipeline/calibrations/{college}.json` — empirical grade distributions and enrollment data from DataMart.
