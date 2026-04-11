# Student Generation

The student generation stage produces a synthetic student population for each college, calibrated against real institutional data. The output is a `Student` node per generated person, with `ENROLLED_IN` edges to the courses they have taken and `HAS_SKILL` edges to the skills they have acquired through completed enrollments. This document describes what the generation does, what data it is calibrated against, and what the output represents.

## Why the data is synthetic

The product currently uses synthetic student data, not real student records. The reasons are documented in detail in the [students product document](../product/students.md), but the short version is twofold. First, real student data is sensitive enough that handling it carries legal, ethical, and operational burdens (FERPA, institutional access agreements, data protection infrastructure) that the product is not yet equipped to take on. Second, the synthetic approach lets the system demonstrate the analytical power of the ontology — the *art of the possible* — without requiring access to records the product does not yet need to function.

The architectural commitment in the product section is that students will eventually be real but anonymized to Kallipolis (with the college holding the identification key). The synthetic methodology described here is the present-day form of that commitment, not a permanent compromise.

## What the methodology calibrates against

The synthetic generation is anchored in three sources of public, aggregated, institutionally validated data.

**DataMart 4-digit TOP code grade distributions.** The Chancellor's Office MIS Data Mart publishes per-college grade distributions broken out by 4-digit TOP code (Taxonomy of Programs). For each TOP code at each college, DataMart provides the percentage of grades that were A, B, C, D, F, W, P, etc. These distributions are the empirical anchor for both *which areas of study* the college's students concentrate in and *how well* they perform across those areas. A college might have 49–114 distinct 4-digit codes, each representing a substantive program area (Accounting, Computer Software Development, Dental Occupations, and so on).

**DataMart Master Course Files.** Each college submits course-level TOP code assignments to the Chancellor's Office as part of its MIS submission. Parsing these gives a mapping from course prefix (e.g., `CS`, `ACTG`, `BIOL`) to 4-digit TOP code, which is what allows individual courses in the catalog to be assigned to the correct program area. The mapping covers about 97% of courses across the colleges in the system.

**College institutional data.** Each college publishes its own enrollment headcount, full-time-to-part-time ratio, and fall-to-winter retention rate. These are operational facts the college is responsible for and that drive the parameters of the generation: how many students to generate, how many courses per term they take, and how persistence drops off across terms.

All three sources are publicly available, aggregated, and institutionally validated. No student records are accessed and no de-identification is performed. The synthetic students are generated entities, not de-identified real students.

## How the methodology works

The generation runs in six conceptual steps for each college.

**1. Course pooling.** Each enriched course in the college catalog is assigned a 4-digit TOP code via its prefix, using the prefix-to-TOP4 mapping. Courses are grouped into pools by TOP code so that the generation can draw enrollments from a specific program area when it needs to.

**2. Primary assignment.** Each student is given a primary 4-digit TOP code, weighted by the DataMart enrollment share for that code. This is the student's area of concentration. A college whose DataMart data shows 12% of grades coming from Accounting will have roughly 12% of its synthetic students concentrating in Accounting.

**3. Enrollment generation.** For each enrollment a student takes, the generator draws a course with 60% stickiness (`PRIMARY_STICKINESS = 0.60`) to the student's primary TOP code pool and 40% chance of drawing from the full TOP code distribution (also weighted by enrollment share). This produces realistic course-taking patterns where students concentrate in one area while also taking general education and elective courses across other areas.

**4. Department cap.** A maximum of 6 courses per department per student (`DEPT_CAP = 6`) prevents unrealistic concentration. When a student hits the cap, the generator redirects subsequent enrollments in that department to other parts of the distribution. This is a structural guardrail against pathological generation patterns.

**5. Grade assignment.** Each enrollment receives a grade sampled directly from the 4-digit TOP code's grade distribution as published by DataMart. A course in Accounting uses Accounting's grade distribution; a course in Mathematics uses Mathematics'. There is no college-wide averaging — every course's grade is sampled from the empirical distribution for that course's TOP code. This is what makes the aggregate success rates of the synthetic population match the college's actual aggregate success rates.

**6. Skill materialization.** Only completed enrollments (grades A, B, C, P) produce `HAS_SKILL` edges. The skills come from the `Course → DEVELOPS → Skill` edges of the completed course. A student who completes a welding course inherits the skills the welding course is designed to develop. This is what makes students the empirical carriers of skill from the supply side, in the language of the [students product document](../product/students.md).

## What the parameters control

A small number of per-college parameters drive the operational shape of the generation.

| Parameter | What it controls | Source |
|---|---|---|
| `enrollment` | Total number of students generated | College's published headcount |
| `ft_ratio` | Full-time student percentage (drives course load: FT 4–6 courses/term, PT 1–3) | College's published FT/PT split |
| `retention_rate` | Fall-to-winter retention (geometric decay determines persistence across terms) | College's published retention metric |

Within these parameters, the algorithm is deterministic for a given seed. The same seed produces the same population, which makes the generation reproducible across runs and comparable across changes to the methodology.

## Validation

After generation, the synthetic population's aggregate success rate is compared against the DataMart target and the difference is logged. The mechanism is in `backend/pipeline/students.py` and runs after every generation. In practice, observed deviations have been small — typically within a percentage point or so — though the algorithm does not enforce a hard threshold and the exact magnitude depends on the calibration data for the specific college.

The validation matters because it is what gives the synthetic population its claim to structural fidelity. The students are not real, but the population behaves the way the real population does at the aggregate level. A coordinator analyzing the synthetic population will see the same patterns of concentration, completion, and skill acquisition that the real population would produce.

## What the output represents

The output of this stage is `Student` nodes connected to courses (via `ENROLLED_IN` with grade, term, and status properties) and to skills (via `HAS_SKILL`, materialized only from completed enrollments).

Each generated student is an empirically faithful representative figure, not a de-identified real student. The structural patterns of the population — concentration, performance, skill acquisition — match the patterns the real population produces, which is what allows the analytical work the [partnership generation flow](../product/partnerships.md) does to surface meaningful student-pipeline evidence. A coordinator looking at the student layer of the [graph](../architecture/graph-model.md) is looking at a structurally accurate model populated by representative figures, not at an extracted view of identified individuals.

The honesty of the approach depends on the methodology being legible. A user who does not understand that the students are synthetic could overinterpret the population as a literal headcount; a user who does understand can read the analysis in the right register. This document, alongside the [students product document](../product/students.md), is part of what makes the methodology legible.
