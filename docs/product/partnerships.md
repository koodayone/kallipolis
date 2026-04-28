# Partnerships

Partnerships are the form we document that is the unit of action of the ontology. The distinction matters at the most basic level. Students, courses, occupations, and employers are what the ontology represents — the analytical material a coordinator reasons over. Partnerships are what the ontology is for — the action the analytical material directs work toward. Partnerships are also the form the mission sentence names directly: the product exists *for community colleges to forge stronger workforce partnerships with industry*. Partnerships are not one of five forms in a neutral taxonomy. They are the named activity at the center of the product's purpose.

## The essence

In Kallipolis, a partnership is a data-driven opportunity for a community college to engage with an industry employer. A partnership opportunity is formulated from the four units of analysis: it draws on occupations to show the regional labor market context, on courses to show curricular alignment, and on students to show the pipeline of people who would benefit. It is presented to a coordinator as a draft narrative the coordinator can use, with each claim immediately followed by the empirical evidence that grounds it. The shape of the eventual collaboration — advisory board, internship, co-designed curriculum, hiring agreement, or something else — emerges from the conversation the coordinator has with the employer after seeing the opportunity. Kallipolis surfaces the case for engaging; the coordinator's professional judgment determines the form.

The formulation of high-quality partnership opportunities is the core value proposition of Kallipolis, and the entire ontology is dedicated to making this formulation possible.

## What a partnership opportunity contains

A partnership opportunity in Kallipolis has two layers: a narrative that argues for why the partnership is worth pursuing, and the empirical evidence that grounds each section of the narrative. Both layers are present together, not separated. The coordinator reads a claim and immediately sees the data the claim is based on.

### The four sections of the narrative

The narrative is structured around four sections, each carrying a distinct claim.

- **Executive summary.** The institutional case that this employer represents a partnership opportunity for the college. Characterizes what the employer does and integrates the strongest signals of alignment across regional demand, curriculum, and student pipeline in compressed form. The reader finishes this paragraph understanding why this opportunity merits their attention.

- **Occupational demand.** Establishes that the employer's hiring profile represents institutionally significant regional labor market demand. The evidence is the specific occupations the employer hires for, with regional wages, employment levels, growth rates, and annual openings drawn directly from the occupation data.

- **Curriculum alignment.** Establishes that specific departments at the college develop the skills these occupations require. The evidence is the actual departments and courses that develop the relevant skills, with partial alignment named honestly using strengthening-language rather than deficit-language.

- **Student impact.** Asserts the composition and alignment of the student pipeline with this opportunity. The evidence is the population of students at the college whose competency profiles align with the partnership's target occupations.

The four sections map to the executive summary plus three of the four units of analysis: occupations, courses, students. The fourth unit of analysis, employers, is not its own section because it is the *subject* of the narrative — the entity the partnership is being proposed with, not a piece of evidence in the case.

### Strong Workforce evidence

The narrative closes with a tabular Strong Workforce evidence block — the regional supply-demand foundation any subsequent funding justification requires. The block has no narrative; it is data only. Three sub-tables: occupations the employer hires for with their SOC codes and regional annual openings (demand), program completions per TOP6 code projected from Centers of Excellence data (supply), and the gap between them.

This block is what makes the partnership artifact institutionally legible to the Strong Workforce Program without making the artifact itself an SWP application. NOVA submission remains a coordinator-led act; Kallipolis provides the empirical foundation that any submission depends on. The Strong Workforce Program is the institutional context the data is shaped to be legible to; it is not a separate form within the product.

## How partnerships are generated

The methodology behind partnership opportunity generation has three components that work together: occupation selection, evidence assembly, and narrative generation. The pipeline is linear and type-agnostic — every opportunity moves through the same stages.

**Occupation selection.** The first step picks the primary hiring occupation for the employer and a small set of core skills central to the role. The selection is constrained: the model can only choose from the occupations the employer is recorded as hiring for in the regional graph, and it can only choose skills the occupation requires. The skills it picks are biased toward those the college already develops, with at most one skill that represents a genuine curriculum gap.

**Evidence assembly.** With the occupation identified, the system assembles the empirical material that grounds the four sections. Curriculum evidence comes from departments at the college that develop the core skills, narrowed by a department relevance filter to the most directly aligned three. Student pipeline evidence comes from students enrolled in those departments who carry the relevant skill profile. Regional supply-demand evidence comes from the COE-published projected program completions and the regional annual openings already in the graph.

**Narrative generation.** With the evidence assembled, an LLM-mediated step produces the four-section narrative in a single call. The narrative is type-agnostic — it does not name a partnership type or recommend a collaboration shape. Its job is to make the institutional case for why this opportunity merits the coordinator's attention, with each section's claim grounded in the assembled evidence.

The narrative generation operates against a tightly constrained context: only the empirical material assembled in the previous step is available to the model. The model cannot invent evidence, cannot claim things the data does not support, and cannot generalize beyond the specific occupations, courses, and students the assembly produced. The constraint is the same kind of guardrail that governs the unified skills taxonomy — a controlled context that disciplines the interpretive step and prevents the worst LLM failure modes.

### Trust through visibility

The presentation of the partnership opportunity is shaped by a deliberate design philosophy: the narrative is not asked to stand on its own. Each section is followed immediately by the empirical evidence that supports it. The coordinator reads the claim about occupational demand and then sees the actual occupations and their wages and growth rates. They read the claim about curriculum alignment and then see the actual courses that develop the relevant skills. They read the claim about student impact and then see the actual students who carry those skills.

This is a specific commitment about how AI-generated content should be presented in a high-stakes institutional context. The narrative is not persuasive in the marketing sense — it is *grounded* by being immediately followed by the empirical material that supports each claim. The coordinator is not asked to trust the AI. They are asked to trust the data, which the AI is summarizing. The visibility of the empirical foundation is what makes the narrative usable as a draft rather than as a black-box recommendation.

The methodology is principled and improvable. The occupation selection produces defensible primary occupations today; richer signals would refine the choice. The evidence assembly produces empirical material that passes inspection today; richer source data and validation feedback would make it more accurate. The narrative generation produces drafts coordinators can use today; expert input on narrative voice and stakeholder feedback on what makes a draft genuinely usable would refine the output further.

## How the partnership flow will evolve

The partnership generation flow is the surface of Kallipolis where most product engagement with stakeholders is likely to happen. It is the place where coordinators first encounter what the ontology can do for them, and it is the natural site for feedback about what makes a partnership opportunity compelling, what makes a draft genuinely usable, and what the system is missing.

The North Star for the partnerships flow is straightforward: drive partnerships and strengthen the partnership creation process. The current implementation produces opportunities coordinators can use as drafts. Future iterations will refine the narrative quality, sharpen the evidence assembly logic, and incorporate stakeholder feedback into how the system formulates and presents opportunities.

One specific area of possible development is partnership *management* — supporting the work that comes after a partnership has been initiated, including tracking, status updates, ongoing collaboration, and outcome measurement. This would extend Kallipolis beyond opportunity identification into the operational lifecycle of partnerships themselves. Another is productized SWP application generation — turning the regional supply-demand evidence block into a NOVA-shaped submission. Both directions are real architectural possibilities. Neither is in the current scope; both will be informed by what coordinators actually request after working with the discovery artifact.

## The core value proposition

Partnerships unify their angles around a single observation: the formulation of data-driven partnership opportunities is the core value proposition of Kallipolis, and the entire ontology is dedicated to enabling it. Partnerships are not one of five forms in a neutral taxonomy. They are the activity the rest of the ontology exists to enable.

The four units of analysis provide the empirical material. The unified skills taxonomy provides the semantic medium. The Atlas provides the surface where the user encounters all of this. And partnerships are where the analytical work pays off — the moment a coordinator sees a data-driven case for engaging with a specific employer, with the empirical foundation visible right next to the narrative and the regional supply-demand data ready to support any subsequent funding justification.

Everything upstream of the partnership generation flow is preparation. The flow itself is the moment Kallipolis does its job.
