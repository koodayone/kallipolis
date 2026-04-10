# Graph Model

The Kallipolis ontology is implemented as a Neo4j property graph with eight node types and roughly eleven relationship types. This document describes the schema — what each node type represents, what each relationship encodes, and how the supply-demand chain is realized in actual graph structure.

## The eight node types

Five node types live on the curriculum side, three on the industry side. Each one corresponds to a concept in the product section.

### Curriculum side

| Node | Key properties | Constraint | What it represents |
|---|---|---|---|
| **College** | name, city, state, region | `name UNIQUE` | A California community college |
| **Department** | name | `name UNIQUE` | A department within a college (e.g., Welding, Nursing) |
| **Course** | code, college, name, department, units, description, learning_outcomes, course_objectives, skill_mappings, transfer_status, url | `(code, college) UNIQUE` | A course actually taught at a college |
| **Skill** | name | `name UNIQUE` | A workforce-relevant competency from the unified taxonomy |
| **Student** | uuid | `uuid UNIQUE` | A student enrolled at a college (synthetic) |

### Industry side

| Node | Key properties | Constraint | What it represents |
|---|---|---|---|
| **Region** | name | `name UNIQUE` | A regional labor market |
| **Occupation** | soc_code, title, description, annual_wage | `soc_code UNIQUE` | A SOC-coded occupation in regional demand |
| **Employer** | name, sector | `name UNIQUE` | A real organization that hires in California |

The eight node types map cleanly to the conceptual structure documented in the product section. The four units of analysis — students, courses, occupations, employers — each have a node type. The two structural elements — colleges and departments on the curriculum side, regions on the industry side — are containers and intermediaries. The skill node is the emergent bridge that connects supply to demand.

## The eleven relationship types

Relationships encode the supply-demand logic of workforce development. Each one is directional and most carry no properties.

| Relationship | From → To | Properties | What it encodes |
|---|---|---|---|
| `OFFERS` | College → Department | — | A college operates a department |
| `CONTAINS` | Department → Course | — | A department offers a course |
| `DEVELOPS` | Course → Skill | — | A course develops a skill (derived from the taxonomy) |
| `ENROLLED_IN` | Student → Course | grade, term, status | A student is or was enrolled in a course |
| `HAS_SKILL` | Student → Skill | — | A student has acquired a skill (derived from completed enrollments) |
| `IN_MARKET` | College → Region | — | A college operates within a regional labor market |
| `IN_MARKET` | Employer → Region | — | An employer operates within a regional labor market |
| `DEMANDS` | Region → Occupation | employment | A region has demand for an occupation, with regional employment data |
| `REQUIRES_SKILL` | Occupation → Skill | — | An occupation requires a skill (derived from the taxonomy) |
| `HIRES_FOR` | Employer → Occupation | — | An employer hires for an occupation |

The `IN_MARKET` relationship is overloaded: the same edge type connects both colleges and employers to their regional labor markets. This works because the semantics are the same in both cases — the entity operates within the region — even though the entities being connected are different node types.

## Schema diagram

```
College ──OFFERS──▶ Department ──CONTAINS──▶ Course ──DEVELOPS──▶ Skill
   │                                            ▲                   ▲ │
   │                                 ENROLLED_IN│          HAS_SKILL│ │
   │                                            │                   │ │
   │                                         Student ───────────────┘ │
   │                                                                  │
   ├──IN_MARKET──▶ Region ◀──IN_MARKET── Employer                     │
                     │                      │                         │
                     │DEMANDS               │HIRES_FOR                 │
                     ▼                      ▼                         │
                  Occupation ──REQUIRES_SKILL─────────────────────────┘
```

The diagram shows the two halves of the graph meeting at `Skill`. Read left to right, the diagram traces the supply chain: a college offers departments, departments contain courses, courses develop skills, students enroll in courses and acquire those skills. Read right to left from the skill layer, it traces the demand chain: occupations require skills, regions demand occupations, employers hire for occupations. The two chains meet at the skill node, which is what makes the supply-demand alignment computable.

## The bridge logic

The point of the graph schema is to make a specific question answerable: *which regional employers hire for skills that this college teaches?* The answer is computed by traversing the bridge that the schema constructs between the curriculum and industry sides.

A skill is a bridge skill when it appears on both sides — it is `DEVELOPS`-related to at least one course at a college and `REQUIRES_SKILL`-related to at least one occupation in the college's region. Without bridge skills, the graph would be two disconnected pairs (college-students-courses on one side, region-employers-occupations on the other). With them, the graph becomes a single connected structure in which a coordinator can traverse from a course to a regional employer through the skill that connects them.

This is why the unified skills taxonomy is so consequential. The taxonomy is what guarantees that a course's skill claims and an occupation's skill requirements are expressed in the same vocabulary. Without it, the `DEVELOPS` and `REQUIRES_SKILL` relationships would point at different skill nodes even when they represent the same competency, and the bridge would not exist.

## Two illustrative traversals

**Workforce alignment** — what occupations match a college's curriculum:

```cypher
MATCH (c:College {name: $college})-[:IN_MARKET]->(r:Region)-[:DEMANDS]->(occ:Occupation)
      -[:REQUIRES_SKILL]->(sk:Skill)<-[:DEVELOPS]-(course:Course {college: $college})
RETURN occ.title, count(DISTINCT sk) AS skills_aligned
ORDER BY skills_aligned DESC
```

This is the supply-demand chain traversed end to end. It starts at a college, follows `IN_MARKET` to the region, follows `DEMANDS` to occupations the region needs, follows `REQUIRES_SKILL` to the skills those occupations require, and joins on courses at the same college that develop those skills. The count of aligned skills is a measure of how well the college's curriculum matches each occupation in the region.

**Skill gap** — what occupations need that this college does not teach:

```cypher
MATCH (emp:Employer {name: $employer})-[:HIRES_FOR]->(occ:Occupation)
      -[:REQUIRES_SKILL]->(sk:Skill)
WHERE NOT EXISTS { MATCH (c:Course {college: $college})-[:DEVELOPS]->(sk) }
RETURN sk.name, collect(DISTINCT occ.title) AS needed_for
```

This is the gap identification capability the [occupations product document](../product/occupations.md) names as the unique improvement vector for the occupation form. The traversal starts at an employer, follows `HIRES_FOR` to its occupations, follows `REQUIRES_SKILL` to the skills those occupations need, and filters to skills that no course at the target college develops. The result is the set of curricular gaps that the partnership work could address.

## How the schema embodies the product framing

The graph schema is the operational expression of the conceptual structure documented in the product section.

- The **four units of analysis** correspond to the four foundational node types: `Student`, `Course`, `Occupation`, `Employer`. Each one is uniquely constrained, has its own institutional authority, and serves as a substantive entity rather than a structural one.
- **`College`, `Department`, and `Region`** are containers — they organize the foundationals into groupings that the user navigates through but does not act on directly.
- **`Skill`** is the emergent bridge. It is real and load-bearing in the graph, but it has no institutional authority of its own. It is derived from analysis of what courses develop and what occupations require.
- The **two units of action** — partnerships and strong workforce — are not stored as node types. They are computed from traversals over the eight node types. A partnership opportunity is the result of a query that joins curriculum to labor market through skills; an SWP application is the same evidentiary substrate reshaped for a specific institutional consumer. The graph is what makes both computable, even though neither has its own table.
