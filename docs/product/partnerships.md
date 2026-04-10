# Partnerships

Partnerships are the first form we document that is a unit of action rather than a unit of analysis. The distinction matters at the most basic level. Students, courses, occupations, and employers are what the ontology represents — the analytical material a coordinator reasons over. Partnerships are what the ontology is for — the action the analytical material directs work toward. Partnerships are also the form the mission sentence names directly: the product exists *for community colleges to forge stronger workforce partnerships with industry*. Partnerships are not one of six forms in a neutral taxonomy. They are the named activity at the center of the product's purpose.

## The essence

In Kallipolis, a partnership is a data-driven opportunity for a community college to engage with an industry employer in one of three structured forms — advisory board, internship pipeline, or curriculum co-design. A partnership opportunity is formulated from the four units of analysis: it draws on occupations to show the regional labor market context, on courses to show curricular alignment, and on students to show the pipeline of people who would benefit. It is presented to a coordinator as a draft narrative the coordinator can use, with each claim immediately followed by the empirical evidence that grounds it. The formulation of high-quality partnership opportunities is the core value proposition of Kallipolis, and the entire ontology is dedicated to making this formulation possible.

## What a partnership opportunity contains

A partnership opportunity in Kallipolis has two layers: a narrative that argues for why the partnership is worth pursuing, and the empirical evidence that grounds each section of the narrative. Both layers are present together, not separated. The coordinator reads a claim and immediately sees the data the claim is based on.

### The three sections of the narrative

The narrative is structured around three sections, each answering a distinct question.

- **Occupational demand.** This section establishes that the occupations the employer hires for are attractive in the region's labor market. The evidence is regional demand profiles, wages, employment levels, and growth rates drawn directly from the occupation data.

- **Curriculum alignment.** This section establishes that the college's curriculum is well-positioned for collaboration with this employer. The evidence is the actual departments and courses at the college that develop the skills the employer's occupations require.

- **Student pipeline.** This section establishes that there are students who would benefit from the partnership. The evidence is the population of students at the college whose competency profiles align with the partnership's target occupations.

The three sections map to three of the four units of analysis: occupations, courses, students. The fourth unit of analysis, employers, is not a section because it is the *subject* of the narrative — the entity the partnership is being proposed with, not a piece of evidence in the case. The architecture of the narrative reflects the architecture of the ontology precisely.

### The three partnership types

The partnership generation flow supports three types of opportunity, each with its own narrative and its own data assembly logic.

- **Advisory board.** A structured engagement where industry representatives provide ongoing input into the college's curriculum and career pathways for a sector or program area.

- **Internship pipeline.** A relationship in which the college's students gain workplace experience with the employer, typically tied to a specific program or set of courses.

- **Curriculum co-design.** A deeper engagement where the college and the employer work together to design or revise curriculum that produces graduates aligned with the employer's hiring needs.

The constraint to three types is a deliberate scoping choice. Each type can be supported with the rigor the data assembly requires, which a more comprehensive system would compromise. This is the same partial-by-design principle that governs the ontology as a whole, applied at the level of what kinds of partnerships the system can currently produce.

## Where partnerships sit in the partnership lifecycle

Partnerships and Strong Workforce are the two units of action in the ontology, and they correspond to two distinct stages of a coordinator's actual workflow. Partnerships sit at the *discovery stage* — the moment a coordinator is deciding whether a particular relationship with an employer is worth pursuing. Strong Workforce sits at the *justification stage* — the moment after the decision to pursue has been made, when the partnership needs to be translated into a fundable proposal that complies with state mandates.

The two stages answer different questions. The discovery stage answers *should I pursue this?* The justification stage answers *now that I am pursuing it, how do I get it funded under state requirements?* The partnership generation flow is built around the first question. The strong workforce flow, documented in the next file, is built around the second.

This sequential framing matters because it explains why the two units of action need their own treatment despite being related. They are not parallel artifacts. They are sequential stages in the same lifecycle, with different audiences (the coordinator's own decision vs. state compliance), different data assembly logic, and different narrative purposes. A single document covering both would conflate two distinct kinds of work.

## How partnerships are generated

The methodology behind partnership opportunity generation has three components that work together: semantic classification, data assembly, and narrative generation. The partnership type is the organizing variable that shapes all three.

**Semantic classification.** The first step is determining what kind of partnership opportunity is being formulated. The three types — advisory board, internship pipeline, curriculum co-design — are not interchangeable. Each one has a different relationship structure, requires different evidence to be compelling, and produces a different narrative. The semantic classification step identifies which type the opportunity belongs to and routes the assembly logic accordingly.

**Data assembly.** With the type identified, the system assembles the empirical material needed to make the case. The assembly is type-specific. An advisory board opportunity emphasizes sector-level alignment and the industry expertise the college could draw on. An internship pipeline emphasizes specific occupations and the students positioned to fill them. A curriculum co-design opportunity emphasizes skill gaps and the courses that could be revised to close them. The same four foundationals provide the raw material in every case, but the questions asked of them differ by type, and the evidence selected reflects those questions.

**Narrative generation.** With the type-specific evidence assembled, an LLM-mediated step produces the narrative. The narrative is shaped by the partnership type — its tone, its structure, the order in which it presents the three sections, and the emphasis it places on each kind of evidence. The narrative is not a generic template filled with values. It is a document whose voice and architecture are tailored to the specific kind of partnership the opportunity represents.

The narrative generation operates against a tightly constrained context: only the empirical material assembled in the previous step is available to the model. The model cannot invent evidence, cannot claim things the data does not support, and cannot generalize beyond the specific occupations, courses, and students the assembly produced. The constraint is the same kind of guardrail we discussed for the unified skills taxonomy — a controlled context that disciplines the interpretive step and prevents the worst LLM failure modes.

### Trust through visibility

The presentation of the partnership opportunity is shaped by a deliberate design philosophy: the narrative is not asked to stand on its own. Each section is followed immediately by the empirical evidence that supports it. The coordinator reads the claim about occupational demand and then sees the actual occupations and their wages and growth rates. They read the claim about curriculum alignment and then see the actual courses that develop the relevant skills. They read the claim about student pipeline and then see the actual students who carry those skills.

This is a specific commitment about how AI-generated content should be presented in a high-stakes institutional context. The narrative is not persuasive in the marketing sense — it is *grounded* by being immediately followed by the empirical material that supports each claim. The coordinator is not asked to trust the AI. They are asked to trust the data, which the AI is summarizing. The visibility of the empirical foundation is what makes the narrative usable as a draft rather than as a black-box recommendation.

The methodology is principled and improvable, in the same register that applies to the methodological work in the form documents. The semantic classification produces type-correct routing today; richer typology might support more partnership forms in the future. The data assembly produces empirical evidence that passes inspection today; richer source data and validation feedback would make it more accurate. The narrative generation produces drafts coordinators can use today; expert input on narrative voice and stakeholder feedback on what makes a draft genuinely usable would refine the output further.

## How the partnership flow will evolve

The partnership generation flow is the surface of Kallipolis where most product engagement with stakeholders is likely to happen. It is the place where coordinators first encounter what the ontology can do for them, and it is the natural site for feedback about what makes a partnership opportunity compelling, what makes a draft genuinely usable, and what the system is missing.

The North Star for the partnerships flow is straightforward: drive partnerships and strengthen the partnership creation process. The current implementation produces opportunities coordinators can use as drafts. Future iterations will refine the narrative quality, sharpen the data assembly logic, and incorporate stakeholder feedback into how the system formulates and presents opportunities.

One specific area of possible development is partnership *management* — supporting the work that comes after a partnership has been initiated, including tracking, status updates, ongoing collaboration, and outcome measurement. This would extend Kallipolis beyond the discovery stage into the operational lifecycle of partnerships themselves. It is a real direction the architecture could move toward, but it is premature for deeper deliberation at this stage. The current focus is on doing the discovery stage well, and the partnership generation flow is where that work will be refined first.

## The core value proposition

Partnerships unify their angles around a single observation: the formulation of data-driven partnership opportunities is the core value proposition of Kallipolis, and the entire ontology is dedicated to enabling it. Partnerships are not one of six forms in a neutral taxonomy. They are the activity the rest of the ontology exists to enable.

The four units of analysis provide the empirical material. The unified skills taxonomy provides the semantic medium. The Atlas provides the surface where the user encounters all of this. And partnerships are where the analytical work pays off — the moment a coordinator sees a data-driven case for engaging with a specific employer in a specific way, with the empirical foundation visible right next to the narrative.

Everything upstream of the partnership generation flow is preparation. The flow itself is the moment Kallipolis does its job.
