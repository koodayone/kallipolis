# Occupations

Of the four units of analysis the ontology grounds itself on, occupations are the only ones that are categories. Students are people. Courses are documents. Employers are organizations. Occupations are abstract classifications — Standard Occupational Classification codes that group many concrete jobs under one label. A registered nurse, in the ontology, is not a person, not a document, not an organization. It is a *kind*, defined in a regulatory and analytical framework, applied to real jobs and real people but not coextensive with any one of them. Occupations are also the most regionally variable foundational, the same category carrying different demand profiles in different parts of California, and the most directly traceable to a single institutional research authority.

## The essence

In Kallipolis, an occupation is a category of regional labor market demand, defined from a particular school's regional perspective by its demand profile, its wage, and the skills the position requires. Occupations are the demand-side anchor of the supply-demand equation — the structured representation of what the regional labor market needs, presented in a form that lets the curriculum side be aligned against it.

## What an occupation contains

An occupation in the ontology contains several layers, organized around the three things a coordinator actually reasons about: the regional demand profile, the wage, and the skills the position requires.

**Identity and description.** Each occupation has a Standard Occupational Classification code, a title, and a summary of the work it consists of. The SOC code is what makes the occupation interoperable with the network of institutional vocabularies that connect curriculum to labor market. The description is what gives the occupation substantive content beyond a label.

**Regional demand profile.** This is the heart of the representation. It includes employment levels, annual openings, growth rate, and the wage attached to the position — all scoped to the region the school serves. The same SOC code carries different metadata in different regions, because labor markets are local. An occupation in the Bay Area is not the same opportunity as the same occupation in the Central Valley. This is what allows a coordinator to ask not just *is this occupation in demand somewhere?* but *is this occupation in demand here?*

**Required skills.** Each occupation is associated with a set of skills from the unified taxonomy that the position requires. This is the demand-side input to the bridge between teaching and labor market. The skill association is what makes occupations comparable to courses on a shared vocabulary.

**Education level.** The credential typically required for entry into the occupation. The ontology filters to the workforce development band that community colleges actually serve, excluding occupations that require no formal credential, only a high school diploma, a master's, or a doctorate, since these fall outside the cut the product is designed for.

## Where occupations sit in the supply-demand chain

An occupation in the ontology is a pivot. It is the join point where the demand side meets the bridge layer and where the supply side ultimately delivers.

The chain runs: employers hire for occupations; occupations require skills; students develop those skills through courses. Read in the supply direction — from courses through students to alignment with occupations — the chain shows what a college produces and where it can land in the labor market. Read in the demand direction — from employers through occupations to skills back to courses — the chain shows what the labor market needs and where the curriculum could supply it. Both readings traverse the same structure. Occupations are where the demand side meets the bridge that skills carry across.

This is the prism through which occupations earn their place in the ontology. They are not interesting in isolation. They are interesting because they are the connection point where regional employer demand becomes a structured signal about what skills the curriculum needs to produce. Without occupations, employers and skills would not be directly comparable, because employer hiring is too noisy to align with curriculum at the skill level. Occupations provide the categorical layer that makes the alignment computable.

The school-centric regional perspective matters here too. The ontology represents occupations as they exist in the region a particular school serves, not as abstract national categories. This is what makes the demand-side signal actionable for partnership work: a coordinator looking at the occupations linked to their college is looking at the labor market they could realistically build partnerships into, not the entire national labor market in the abstract.

## How occupations are grounded and how skills are associated

The methodology for occupations distinguishes itself from the other foundationals in one important way: the occupation data itself is the most directly traceable to a single authoritative institutional source. The Centers of Excellence for Labor Market Research is the leading source of labor market intelligence for California community colleges, and the occupation node in Kallipolis is largely consistent with what the COE publishes — SOC codes, regional demand profiles, wages, employment levels, growth projections, education levels. The occupation data is not interpreted from scratch; it is sourced from a research arm whose job is to produce exactly this kind of evidence.

This grounding is reinforced by the network of institutional program codes the system uses. SOC codes connect occupations to federal labor market vocabulary. TOP codes connect them to the California community college program classification. CIP codes connect them to the federal instructional program classification. These codes are not invented — they are the formal vocabulary that institutions already use to describe what they teach and what the labor market hires for. The occupation node in Kallipolis sits inside this network of institutionally endorsed vocabularies, which gives it a strong epistemic floor. Among the four foundational entities, occupations come closest to a 1:1 mapping with what an authoritative external research source publishes.

The pressure point is not the occupation data itself. It is the *skills association* layer — how the ontology maps skills from the unified taxonomy onto each occupation. This is the same methodological pressure point we discussed for courses. The pipeline assigns skills to each occupation from the controlled vocabulary, and the assignment is interpretive work that is principled and improvable but not yet expert-validated. The taxonomy acts as a guardrail against invention and drift, and the empirical results pass inspection in the sense that the skills assigned to an occupation are recognizable as what it actually requires. The same refinements that would strengthen the courses methodology — expert review, longitudinal feedback, richer source data — would strengthen the occupations methodology in the same ways.

The core distinction is this: occupations have a stronger epistemic floor than courses because the underlying data traces to an authoritative external research source. Both forms share the same methodological ceiling at the skills layer. Occupations are the most institutionally grounded of the four foundationals, and the place where they can become more rigorous is the same place where courses can — at the layer where the bridge vocabulary is applied.

For the full treatment of the taxonomy itself, see [The Unified Skills Taxonomy](./the-skills-taxonomy.md).

## How the methodology will evolve

The future state for occupations is not about privacy (the way it is for students) or about evolving the taxonomy in collaboration with domain experts in the abstract (though the same kind of expert validation would help here too). It is about a specific analytical capability the current methodology cannot yet support reliably: *skill gap identification*.

A skill gap is a skill that an occupation requires but no course at a particular college develops. Identifying gaps accurately would let institutions target areas of curricular improvement and allocate organizational attention to what is missing rather than to what is already covered. This is one of the most actionable analytical questions a coordinator can ask: not just *where do we align?* but *where don't we align, and what should we do about it?*

Skill gap identification is methodologically downstream of the skills association layer that needs refinement. If the skill mappings on courses and on occupations are accurate enough, gaps become computable as the set difference between what an occupation requires and what the relevant courses develop. If the mappings are not accurate enough, computed gaps will be a mix of real curricular blind spots and artifacts of mapping inconsistency — and the artifacts will be hard to distinguish from the real signals without independent verification. The two improvements are coupled. Refining the skills association is the precondition for accurate gap identification, and accurate gap identification is the value the refinement unlocks.

Beyond gap identification, the same kinds of improvements that would strengthen courses would strengthen occupations: expert input on the unified taxonomy from people who understand both academic curriculum and labor market needs, longitudinal feedback from real outcomes that ties predicted alignments to actual placements, and progressive enrichment of the source data the methodology operates on. The current state is principled, the evolution path is concrete, and the trajectory is toward a methodology that can answer harder questions reliably than it can today.

## What unifies the four angles

The four angles for occupations unify around a particular combination: the strongest epistemic floor among the four foundationals, paired with a methodological pressure point at the skills layer that is shared with courses. The robustness comes from the COE grounding — occupation data traces directly to an authoritative institutional research source. The pressure comes from the skills association — occupations and courses share the same interpretive layer where the unified taxonomy is applied, and that layer is where the methodology has room to evolve.

The architectural improvement vector unique to occupations — skill gap identification — is what makes the pressure point particularly worth addressing. If the skills mappings on both forms become more rigorous, gap identification becomes a computable analytical capability the ontology cannot reliably support today. This is the value the refinement unlocks specifically for occupations, beyond what it unlocks for courses.

Occupations are the most epistemically grounded of the four foundationals. The work to make them more useful is concentrated at the skills layer they share with courses, and the analytical payoff for that work is the gap identification capability that would let institutions target what is missing rather than only describe what is present.
