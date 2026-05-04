# Courses

Of the four units of analysis the ontology grounds itself on, courses are the only ones that are documents. Students are people. Occupations are categories. Employers are organizations. Courses are written things — declarations of curricular intent that exist as text in a catalog before they exist as anything else. They are the institution's public commitment to teach, made verifiably and at the unit of one course at a time, and this distinguishes them from the other foundationals in a way that shapes both what they contain and what work they do in the larger logic of the ontology.

## The essence

In Kallipolis, a course is the institution's commitment to teach particular content. It is expressed as text in a catalog — description, learning outcomes, course objectives — and tagged with the institutional Taxonomy of Programs (TOP) code that the Chancellor's Office assigns it. The TOP code is what bridges the course to the regional labor market: through the Chancellor's Office TOP-CIP and BLS/NCES CIP-SOC crosswalks, every course's TOP code maps to the set of occupations its program institutionally prepares students for. Courses are the origin point of the supply side: without them, there is nothing for students to enroll in and nothing for the institutional crosswalk to bridge.

## What a course contains

The essential structure of a course in the ontology has two layers: the source content the institution publishes, and the institutional TOP code that positions the course within the workforce-development pathway.

The source content is what the catalog actually says. It includes the course description, the learning outcomes the course is designed to produce, the course objectives the institution commits to addressing, and the substantive material the college will teach. Together, these are the institution's published declaration of what the course delivers.

The institutional TOP code is the Chancellor's Office's authoritative assignment of the course to a Taxonomy of Programs category. It is sourced from the per-college Master Course File and stored on the Course node as `top_code`. The TOP code, composed through the Chancellor's Office TOP-CIP and BLS/NCES CIP-SOC crosswalks, determines the set of occupations the course institutionally prepares students for — materialized as `Course-[:PREPARES_FOR]->Occupation` edges in the graph. Without the TOP code, the source content is descriptive prose; with it, the course participates in the bridge between teaching and labor market demand.

Other course attributes — code, units, prerequisites, transfer status, departmental affiliation — are contextual rather than central. They support the two layers without being them.

## How courses position the college's productive capacity

A course is not isolated. It sits within a department, and the departmental positioning is what allows the course to participate in the larger relational logic of the ontology.

Departments matter because they are the categorical handles the ontology uses to align the curriculum with the regional labor market. The technical mechanism is the Taxonomy of Programs (TOP) code system, used in the California community college system to classify programs and the courses within them. TOP codes do relational work in two distinct directions: course-to-occupation mapping (through the institutional TOP-CIP-SOC crosswalk), which produces the curriculum-to-labor-market alignment, and course-to-student distribution, which shapes the synthetic generation of student enrollments. A course in the Welding department is not just labeled Welding — it is positioned in a way that determines which occupations it can plausibly connect to and which students it can plausibly enroll.

Through learning outcomes, descriptions, and substantive material, courses are the source of the curricular pathway the college offers. They are the origin point of the entire bridge from curriculum to labor market. Everything downstream of a course — students enrolled in it, alignment with occupations, partnerships with employers — traces its empirical grounding back to what the course actually teaches and to the institutional TOP code that situates it.

Without courses, the supply side would be a list of intentions. With courses, it becomes a measurable production system grounded in the Chancellor's Office's institutional record. Students enroll in courses, occupations are reachable from them through the crosswalk, employers hire for those occupations.

## How courses bridge to occupations

The methodology by which courses connect to the regional labor market is grounded in the most consequential institutional artifact the California community college system maintains for workforce alignment: the TOP-CIP-SOC crosswalk chain.

The crosswalk is a deliberate institutional design. The Chancellor's Office publishes the TOP-CIP mapping; the federal NCES and BLS jointly publish the CIP-SOC mapping. Composed end to end, the chain takes a course's six-digit TOP code and yields the set of SOC-coded occupations the course's program institutionally prepares students for. This is the bridge between curriculum and labor market — and it carries institutional authority on every link, sourced from named external publications rather than internally derived.

The Course → Occupation edges in the graph (`PREPARES_FOR`) are materialized directly from this chain at curriculum load time. Each edge stores `via_top` as an audit-trail property — the TOP6 the crosswalk used to mediate that pathway — so any partnership artifact can attribute the claim back to its institutional source.

A previous version of the ontology placed an internally-derived skills index between courses and occupations as the bridge. That layer was retired in favor of the institutional crosswalk. The trade-off was deliberate: the skills index introduced an LLM-mediated step into a load-bearing position where two named external publications already establish the same bridge with stronger authority. The institutional crosswalk does not yield finer-grained "what specifically does this course teach" claims that the skills index attempted, but it grounds the pathway claim in published institutional authority — which is what the rest of the ontology's data-authority commitment requires.

## How the methodology will evolve

The future state for courses is not about privacy, the way it is for students. It is about epistemic improvement.

Two improvements would strengthen the curriculum side without requiring a redesign. The first is better source data — richer and more authoritative course content from channels beyond catalog scraping. Catalogs are the institutional commitment to teach, but the published descriptions are sometimes brief or formulaic. Direct access to syllabi, learning outcome assessments, and faculty-described course content would give a coordinator more material to inspect alongside the structured TOP-coded record.

The second is wider crosswalk coverage. The TOP-CIP-SOC chain is well-established for the CTE catalog, but a small number of CTE courses are not yet mapped to a TOP code in the Master Course File and therefore do not participate in the bridge. Closing those gaps as the Chancellor's Office updates its MCF data is the operational improvement that strengthens the institutional bridge.

## What unifies the four angles

The four angles do not describe four different things about courses. They describe one thing — the source of the bridge between curriculum and labor market — from four different positions. What unifies them is leverage.

Courses are not just one of four foundational entities. They are the form whose institutional positioning determines whether the supply side connects to the demand side at all. Students enroll in them, occupations are reached through them, employers hire for the occupations they prepare students for. The TOP code on each Course node is the load-bearing institutional fact that lets the rest of the ontology compute the bridge.
