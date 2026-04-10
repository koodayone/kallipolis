# Students

Of the four units of analysis the ontology grounds itself on, students are the only ones who are people. Courses are documents, occupations are categories, employers are organizations. Students are human beings — and this distinguishes them from the other foundationals in a way that has consequences for how the product represents them, how it generates them today, and how it intends to handle them in the future. This document describes what a student is in the Kallipolis ontology, what the ontology surfaces about each one, what work those contents do, and how the representation is expected to evolve.

## The essence

In Kallipolis, a student is a represented person whose competency portrait — primary focus, course history, GPA, and skill profile — makes the supply side of workforce development empirical. Each field answers a facet of one question: is this student equipped to enter the workforce in this area, and at what level? Together, the fields turn courses into a measurable production system and turn the labor market into a destination for the competencies that system produces.

## What a student contains

The ontology surfaces four fields about each student. The selection is deliberate: it does not surface demographics, socioeconomic status, geographic origin, learning preferences, financial aid status, or any of the dozens of other things the institutional source could supply. It surfaces these four because each one answers a different facet of one question — *is this student equipped to enter the workforce in this area, and at what level?*

- **Primary focus** says what the student is preparing for. This is intent — the program or career path the student has declared as their orientation. It is what the student is becoming.
- **Course history** says what the student has been exposed to. This is curricular reality — the actual list of courses the student has completed. It is the record of what teaching they received.
- **GPA** says how well the student has absorbed what they were taught. This is the academic signal — a quality indicator that distinguishes a student who is ready from one who is on the way.
- **Skill profile** says what the student can actually do. This is derived competency — the set of skills the student has acquired, computed from the courses they have completed against the skill taxonomy that gives the ontology its common vocabulary.

Together, these four fields form a competency portrait. Each is a different measurement of the same underlying question. None could be removed without the portrait losing a dimension. The selection is the same epistemic move that governs the ontology as a whole — represent the entity from a workforce development perspective and refuse to model anything that is not in service of that perspective, even when the source data could supply it.

## How those contents position the student

The four fields are not just descriptive. They are what makes the supply side of workforce development empirical rather than abstract.

The supply side of workforce development is colleges producing graduates with skills. Without students, this is rhetoric — an institutional claim that the curriculum produces capable workers. With students, the claim becomes measurable. The student is the literal carrier of skill from the supply side, and the four fields are what make the carrying observable. *Course history* shows what teaching the student received; *skill profile* shows what teaching translated into competency; *GPA* shows how confidently; *primary focus* shows where the student is taking those competencies.

This is what gives the relational layer of the ontology its empirical character. Courses develop skills; students acquire skills; occupations require skills; employers hire for occupations. The chain is meaningful only because students populate the middle of it. They are the entity that turns "this college teaches X" into "this many students at this college have actually learned X to a level the labor market can recognize." Without students, the supply side would be a list of courses and intentions. With students, it becomes a measurable production system.

A coordinator looking at the relational graph is almost always asking a student-mediated question: how many students at my college have the skills required by this occupation, how many of them are in programs aligned with this employer, which ones have a primary focus that suggests they would be interested in this partnership opportunity. The four fields are what make those questions answerable.

## How students are generated today

The student records currently in the Kallipolis ontology are synthetic. They are produced by a sophisticated but imperfect methodology that takes a college's actual courses and skill taxonomy and synthesizes a population of students whose enrollments, completions, and skill profiles approximate the institutional reality of that college. The methodology is not a placeholder. It is a deliberate choice that the documentation has an obligation to be legible about.

Two things justify the synthetic approach.

The first is privacy. Real student data is sensitive enough that handling it carries legal, ethical, and operational burdens that a product at this stage is not yet equipped to take on. By synthesizing students from validated curricular data, Kallipolis can demonstrate the analytical power of the ontology without becoming a custodian of records that come with FERPA obligations and institutional access agreements. The synthesis is a way of doing the analytical work before the trust infrastructure exists to handle the real records.

The second is what the synthetic data lets the system show. Synthetic students are not inferior to real students for the purpose of demonstrating what the ontology makes possible. They illustrate the *art of the possible* — what the system can do when it has student-level evidence to reason about. A coordinator looking at a Kallipolis instance with synthetic students is looking at a structurally faithful approximation of what they would see with their college's real student records, and the analytical capability is the same in both cases.

The legibility obligation is the price of the approach. A user who does not understand that the students are synthetic could overinterpret the insights, mistaking the population for a literal headcount of their actual students. A user who does understand can read the analysis in the right register: as a structurally accurate model of what the institution looks like, populated by representative figures rather than identified individuals. The documentation has to make this distinction clear, because the distinction is what allows the synthetic approach to be honest rather than evasive.

## How students will be represented in the future

The architecture commits to a future state in which students are anonymized to Kallipolis but identifiable to community college stakeholders.

The current synthetic approach is appropriate for the present, but it does not exhaust what the product can become. The aspirational architecture extends the system's value to the individual level — matching real people to real employment opportunities, tailoring student pathways through programs, supporting the kind of advising work that requires knowing who a student actually is. None of this is possible with synthetic data. All of it requires real records.

The way to do this without making Kallipolis a custodian of sensitive data is to invert the relationship. The system stores enough about each student to do the analytical work but never stores anything that identifies them. The institution holds the identification key. When a college user looks at a student through Kallipolis, they see a real person — but they see them through their college's identity layer, not through anything Kallipolis itself surfaces. Kallipolis sees a competency profile and a set of relationships. The college sees a name, an advising history, a relationship to the program.

This is a privacy stance and an architectural commitment at the same time. It says that institutional knowledge stays with the institution. Kallipolis provides the analytical foundation; the college applies it to the individuals it has obligations toward. The product becomes more valuable as it integrates with real data, but it never becomes a system of record for the people that data describes. The boundary is deliberate.

This future state is not implemented today. It is a direction the architecture is building toward. Marking it in the documentation matters because it shapes the way the current synthetic approach should be read — not as a permanent compromise, but as the present-day form of a longer commitment to do this work without compromising student privacy.

## What unifies the four angles

The four angles — what a student contains, how those contents position them, how they are generated, how they will be represented — are not four competing definitions of a student. They are four layers of one definition.

The first layer says what is *in* a student record. The second layer says what those contents *do* in the larger logic of the ontology. The third layer says how the contents are *currently produced*. The fourth layer says how the contents will be *produced in the future*. All four are needed because the student form is the only one of the four units of analysis where the gap between the current implementation and the future ambition is large enough to require explicit acknowledgment.

Courses, occupations, and employers all use real institutional data today. Students use synthesized data today and real data tomorrow. The form's documentation has to honor both states — the present and the trajectory — without collapsing either one into the other. Students are unique among the foundationals in this way, and the unique treatment is what the four angles are for.
