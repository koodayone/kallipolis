# Occupations

Of the four units of analysis the ontology grounds itself on, occupations are the only ones that are categories. Students are people. Courses are documents. Employers are organizations. Occupations are abstract classifications — Standard Occupational Classification codes that group many concrete jobs under one label. A registered nurse, in the ontology, is not a person, not a document, not an organization. It is a *kind*, defined in a regulatory and analytical framework, applied to real jobs and real people but not coextensive with any one of them. Occupations are also the most regionally variable foundational, the same category carrying different demand profiles in different parts of California, and the most directly traceable to a single institutional research authority.

## The essence

In Kallipolis, an occupation is a category of regional labor market demand, defined from a particular school's regional perspective by its demand profile, its wage, and the institutional pathway from the college's catalog into the role. Occupations are the demand-side anchor of the supply-demand equation — the structured representation of what the regional labor market needs, presented in a form that lets the curriculum side be aligned against it.

## What an occupation contains

An occupation in the ontology contains several layers, organized around the things a coordinator actually reasons about: the regional demand profile, the wage, and the institutional pathway from the college's catalog into the occupation.

**Identity and description.** Each occupation has a Standard Occupational Classification code, a title, and a summary of the work it consists of. The SOC code is what makes the occupation interoperable with the network of institutional vocabularies that connect curriculum to labor market. The description is what gives the occupation substantive content beyond a label.

**Regional demand profile.** This is the heart of the representation. It includes employment levels, annual openings, growth rate, and the wage attached to the position — all scoped to the region the school serves. The same SOC code carries different metadata in different regions, because labor markets are local. An occupation in the Bay Area is not the same opportunity as the same occupation in the Central Valley. This is what allows a coordinator to ask not just *is this occupation in demand somewhere?* but *is this occupation in demand here?*

**Institutional curriculum alignment.** Each occupation surfaces the courses and departments at the coordinator's college whose TOP code institutionally crosswalks to the SOC through the Chancellor's Office TOP-CIP and BLS/NCES CIP-SOC mappings. This is the demand-side end of the institutional bridge between curriculum and labor market — the inverse of the `PREPARES_FOR` edges materialized at course-load time. Two named external publications jointly authorize every alignment claim, and the alignment view names them as the source.

**Education level.** The credential typically required for entry into the occupation. The field is carried on the occupation node as descriptive metadata — it is no longer used to determine which occupations enter the ontology. Scope is determined by a different authority: the Chancellor's Office Career Technical Education classification, which lists every California CC program in its sector file and is the same authority the Strong Workforce Program rests on. A SOC is represented iff COE tracks regional demand for it *and* a CTE-classified TOP code targets it through the TOP→CIP→SOC crosswalk. This admits the core CTE trades (electricians, welders, plumbers, machinists, carpenters, HVAC mechanics) that BLS codes as entering on a high school diploma but that California community colleges demonstrably serve through CTE certificate programs and apprenticeships. It excludes transfer-academic pathways (pre-engineering, pre-science), which are a different product than workforce-development partnerships.

## Where occupations sit in the supply-demand chain

An occupation in the ontology is a pivot. It is the join point where the demand side meets the institutional bridge to the supply side.

The chain runs: employers hire for occupations; occupations are reachable from courses through the institutional TOP-CIP-SOC crosswalk; students enroll in those courses. Read in the supply direction — from courses through students to alignment with occupations — the chain shows what a college institutionally prepares students for and where they can land in the labor market. Read in the demand direction — from employers through occupations back to courses — the chain shows what the labor market needs and which programs the Chancellor's Office and BLS/NCES jointly recognize as preparing students for it. Both readings traverse the same structure. Occupations are where the demand side meets the institutional bridge that the crosswalk authorizes.

This is the prism through which occupations earn their place in the ontology. They are not interesting in isolation. They are interesting because they are the connection point where regional employer demand becomes a structured signal about which workforce pathways the curriculum already feeds. Without occupations, employers and courses would not be directly comparable, because employer hiring is too noisy to align with the catalog at the course level. Occupations provide the SOC-coded categorical layer that the institutional crosswalk maps the curriculum into, which is what makes the alignment computable.

The school-centric regional perspective matters here too. The ontology represents occupations as they exist in the region a particular school serves, not as abstract national categories. This is what makes the demand-side signal actionable for partnership work: a coordinator looking at the occupations linked to their college is looking at the labor market they could realistically build partnerships into, not the entire national labor market in the abstract.

## How occupations are grounded

The methodology for occupations distinguishes itself from the other foundationals in one important way: the occupation data itself is the most directly traceable to a single authoritative institutional source. The Centers of Excellence for Labor Market Research is the leading source of labor market intelligence for California community colleges, and the occupation node in Kallipolis is largely consistent with what the COE publishes — SOC codes, regional demand profiles, wages, employment levels, growth projections, education levels. The occupation data is not interpreted from scratch; it is sourced from a research arm whose job is to produce exactly this kind of evidence.

This grounding is reinforced by the network of institutional program codes the system uses. SOC codes connect occupations to federal labor market vocabulary. TOP codes connect them to the California community college program classification. CIP codes connect them to the federal instructional program classification. These codes are not invented — they are the formal vocabulary that institutions already use to describe what they teach and what the labor market hires for. The occupation node in Kallipolis sits inside this network of institutionally endorsed vocabularies, which gives it a strong epistemic floor. Among the four foundational entities, occupations come closest to a 1:1 mapping with what an authoritative external research source publishes.

The bridge from occupations back to the curriculum side carries the same institutional grounding. The Chancellor's Office maintains the TOP-CIP crosswalk; the federal NCES and BLS jointly maintain the CIP-SOC crosswalk. Composed end to end, those two publications determine which courses the system represents as institutionally preparing students for each SOC. There is no LLM-mediated interpretive layer between an occupation and the courses it draws on; the chain is fully institutional and fully deterministic.

A previous version of the ontology placed an internally-derived skills index between courses and occupations, with each occupation tagged with skills from a controlled taxonomy. That layer was retired. The institutional TOP-CIP-SOC chain establishes the same bridge with stronger authority and without an LLM interpretive step in a load-bearing position.

## How the methodology will evolve

The future state for occupations is not about privacy (the way it is for students). It is about a specific analytical capability the current methodology can support today but the previous one could not reliably: *curriculum gap identification*.

A curriculum gap is an occupation that the regional labor market demands but no course at a particular college institutionally prepares students for. Identifying gaps accurately lets institutions target areas of curricular improvement and allocate organizational attention to what is missing rather than to what is already covered. This is one of the most actionable analytical questions a coordinator can ask: not just *where do we align?* but *where don't we align, and what should we do about it?*

Gap identification under the institutional bridge is computationally direct: an occupation is a gap iff it is in the employer's hires set and no Course at the college has a `PREPARES_FOR` edge to it. Both terms of that intersection are sourced from named institutional publications, so a flagged gap is a real institutional gap rather than an artifact of internal interpretation. The previous skill-index architecture coupled gap identification to the accuracy of internally-derived skill mappings on both courses and occupations; the institutional bridge removes that coupling.

The remaining methodological evolution paths concentrate around the source data the institutional bridge sits on top of: keeping the Chancellor's Office TOP-CIP and Master Course File data current as the Chancellor's Office updates its publications, and closing coverage gaps where individual CTE courses are not yet TOP-coded.

## What unifies the four angles

The four angles for occupations unify around a particular combination: the strongest epistemic floor among the four foundationals, paired with a fully-institutional bridge to the curriculum side. The robustness comes from the COE grounding on the demand side and from the Chancellor's Office and BLS/NCES crosswalks on the bridge side. There is no LLM-mediated interpretive layer in a load-bearing position; every claim from "occupation X is in regional demand" through "the college institutionally prepares students for X" traces to a named external publication.

Occupations are the most epistemically grounded of the four foundationals. The analytical capability this grounding unlocks — institutional curriculum gap identification — is what lets coordinators target what is missing rather than only describe what is present.
