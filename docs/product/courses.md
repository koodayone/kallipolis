# Courses

Of the four units of analysis the ontology grounds itself on, courses are the only ones that are documents. Students are people. Occupations are categories. Employers are organizations. Courses are written things — declarations of curricular intent that exist as text in a catalog before they exist as anything else. They are the institution's public commitment to teach, made verifiably and at the unit of one course at a time, and this distinguishes them from the other foundationals in a way that shapes both what they contain and what work they do in the larger logic of the ontology.

## The essence

In Kallipolis, a course is the institution's commitment to teach particular content. It is expressed as text in a catalog — description, learning outcomes, course objectives — and interpreted through a unified taxonomy to produce the skills that bridge what the college teaches to what the regional labor market demands. Courses are the origin point of the supply side: without them, there is nothing for students to acquire and nothing for the bridge to carry.

## What a course contains

The essential structure of a course in the ontology has two layers: the source content the institution publishes, and the skills derived from that content.

The source content is what the catalog actually says. It includes the course description, the learning outcomes the course is designed to produce, the course objectives the institution commits to addressing, and the substantive material the college will teach. Together, these are the institution's published declaration of what the course delivers.

The derived layer is the set of skills the course produces when its content is interpreted against the unified taxonomy. This is the operational output — what the course contributes to the supply side of the workforce development equation. Without the derivation, the source content is descriptive prose. With the derivation, it becomes a computable contribution to the bridge between teaching and labor market demand.

Other course attributes — code, units, prerequisites, transfer status, departmental affiliation — are contextual rather than central. They support the two layers without being them. The two layers are what give the course its operational meaning in the ontology; everything else is metadata that helps situate the course but does not define it.

This is a simpler attributional structure than students. Students have four discrete fields that each measure a different facet of competency. Courses have two layers in sequence — institutional declaration, then derived competency — and the derivation is what turns the declaration into something the ontology can act on.

## How courses position the college's productive capacity

A course is not isolated. It sits within a department, and the departmental positioning is what allows the course to participate in the larger relational logic of the ontology.

Departments matter because they are the categorical handles the ontology uses to align courses with the regional labor market. The technical mechanism is the Taxonomy of Programs (TOP) code system, used in the California community college system to classify programs and the courses within them. TOP codes do relational work in two distinct directions: course-to-occupation mapping, which produces the curriculum-to-labor-market alignment, and course-to-student distribution, which shapes the synthetic generation of student enrollments. A course in the Welding department is not just labeled Welding — it is positioned in a way that determines which occupations it can plausibly connect to and which students it can plausibly enroll.

But the relational angle is not only about structural positioning. It is also about what courses *do* in the ontology's supply-demand logic. Through learning outcomes, descriptions, and substantive material, courses are the source of the competencies the college produces. They are the origin point of the entire bridge from curriculum to labor market. Everything downstream of a course — students with skills, alignment with occupations, partnerships with employers — traces its empirical grounding back to what the course actually teaches.

Without courses, the supply side would be a list of intentions. With courses, it becomes a measurable production system. Students carry the skills, occupations require them, employers hire for them, but courses are where the skills come from. This is the prism through which courses are viewed in the Kallipolis ontology — they are the origin of the productive capacity that the entire ontology represents.

## How skills are derived from courses

The methodology by which courses produce their skill output is the most consequential mechanism in the ontology. It is also one of the most carefully constructed.

The unified skills taxonomy at the center of the methodology is a deliberate design. It was built to give two domains that do not naturally share vocabulary — academic curriculum on one side, industrial labor markets on the other — a common language they can both speak. This is a real engineering and conceptual achievement, not a heuristic. The taxonomy is what enables courses and occupations to be compared at all, which is the precondition for the entire supply-demand logic the ontology rests on. Without the taxonomy, the bridge does not exist.

The derivation step from course content to skills is constrained by the taxonomy. The pipeline reads each course's published content — description, learning outcomes, course objectives — and assigns skills from the controlled vocabulary, not from open-ended generation. This constraint is what protects the methodology from the worst failure modes of LLM-mediated extraction: skill invention, drift across instances, and inconsistency between similar courses. The vocabulary acts as a guardrail. The interpretation happens within a bounded space.

The empirical results pass the inspection that matters. When the skills extracted for a particular course are compared against what a knowledgeable reviewer would say that course actually develops, the classifications are recognizable as accurate. This is the most direct evidence the methodology is doing what it claims to do — producing skill profiles that reflect the course's real content, not interpretive noise. A methodology that produces outputs which can be inspected and recognized as faithful by a domain reviewer is doing its job, even when more formal verification infrastructure is not yet in place.

The current implementation is principled but not yet enriched by the kinds of validation that would make it stronger: expert review of the taxonomy by people who understand both academic curriculum and labor market needs, longitudinal feedback from real outcomes, human-in-the-loop adjudication for edge cases, richer source data. These are paths the methodology can evolve along without changing its fundamental design — principled in its current state, improvable in directions that are concrete rather than speculative.

For the full treatment of the taxonomy itself, see [The Unified Skills Taxonomy](./the-skills-taxonomy.md).

## How the methodology will evolve

The future state for courses is not about privacy, the way it is for students. It is about epistemic improvement.

Three improvements would strengthen the methodology without requiring a redesign. The first is better source data — richer and more authoritative course content from channels beyond catalog scraping. Catalogs are the institutional commitment to teach, but the published descriptions are sometimes brief or formulaic. Direct access to syllabi, learning outcome assessments, and faculty-described course content would give the derivation step more material to interpret. The richer the source content, the more confident the derived skills.

The second is expert input on the taxonomy itself. The unified vocabulary was constructed deliberately, but it was constructed by the team building the product. Bringing in stakeholders who understand both sides of the bridge — community college curriculum specialists on the academic side, workforce development analysts on the industry side — would allow the taxonomy to be validated, refined, and extended by people who can hold it accountable to the domain. The taxonomy is the language of the bridge, and the language becomes stronger when it is shaped by speakers from both sides.

The third is longitudinal feedback from real outcomes. As Kallipolis matures and integrates with institutional partners, the eventual ability to compare predicted skill profiles against actual labor market placements would create a feedback loop the current methodology lacks. The methodology produces skill profiles in a forward-looking way; an outcomes loop would let those profiles be tested against what students actually go on to do.

None of these improvements require throwing away the current methodology. Each is a path along which the methodology can grow into something stronger. The current state is principled, the evolution path is concrete, and the trajectory is toward higher epistemic confidence over time.

## What unifies the four angles

The four angles do not describe four different things about courses. They describe one thing — the source of the bridge between curriculum and labor market — from four different positions. What unifies them is leverage.

Courses are not just one of four foundational entities. They are the form whose fidelity determines whether the supply side connects to the demand side at all. Students carry the skills, occupations require them, employers hire for them, but courses are where the skills come from. Everything downstream of a course inherits whatever the course's skill derivation produces. This is the highest-leverage point in the ontology, and the methodology that operates at this point is correspondingly important to get right.

It is also being gotten right. The methodology is principled, the design choices are defensible, the empirical results pass inspection, and the evolution path is concrete. Courses do their job in the ontology today, and the work to make them do it more rigorously is well-defined. The leverage and the responsibility for honoring it are in the same place.
