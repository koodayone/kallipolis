# The Ontology

The Kallipolis ontology is the foundation of everything the product does. Without it, the atlas has nothing to navigate, the AI has nothing to reason about, and the partnership artifacts have nothing to be grounded in. This document describes what the ontology is, what it commits to, and what it makes possible.

## The essence

The Kallipolis ontology is a digital representation of the community college from a workforce development perspective. It is grounded on four foundational entities — students, courses, occupations, and employers — and on the relationships between them. The proposition the ontology stands on is that these four entities and their relationships are central to the formation of data-driven partnerships between community colleges and industry.

## Two arenas, one action

The ontology is organized around two arenas: a layer of analysis and a layer of action. Both are native to the ontology. They are distinguished by the role each plays, not by their membership.

The first arena holds the **units of analysis** — the four foundational entities that ground the ontology in institutional authority. These are the things the coordinator studies and measures. They represent ground truths about the college and the region: who is enrolled, what is taught, what jobs are in demand, who is hiring. Each unit of analysis is backed by a single institutional source responsible for the truth of that kind of evidence.

The second arena holds the **unit of action** — partnerships. This is not a fact to be known but a thing to be done. It is formulated from the units of analysis to drive the work of partnership formation forward. A partnership becomes a unit of action when the conditions for pursuing it become computable from the foundationals. The unit of action depends on the units of analysis to be coherent, and it gives the units of analysis their purpose.

The two arenas exist in the same ontology because the product exists to support both knowing and doing. A purely descriptive ontology would represent the four foundationals but would have no organizing principle for what to do with them. A purely action-oriented ontology would name partnerships but would have no grounding for why any particular one matters. Kallipolis needs both, and it holds both within the same coherent structure.

## The units of analysis

The four units of analysis are foundational because each is backed by a single institutional authority responsible for the truth of that kind of evidence.

**Students.** The people enrolled at a college, with their program affiliation, course history, GPA, and the workforce pathways their completed coursework institutionally feeds. The institutional authority is the Chancellor's Office Management Information System Data Mart, the system of record for community college enrollment and outcomes. Students appear in the ontology as entities, not as rows. What is represented is the person and the curricular pathway they are on.

**Courses.** The courses a college actually teaches, with their content, learning outcomes, course objectives, and the institutional Taxonomy of Programs (TOP) code that connects them to the workforce-development pathway. The institutional authority is the college's own course catalog — the curricular definition the institution stands behind — combined with the Chancellor's Office Master Course File that assigns each course its TOP code. Courses are organized by department within a college and are the substrate on which student learning is built.

**Occupations.** The jobs in regional demand, with employment levels, wage data, growth projections, and the entry-level education they typically require. The institutional authority is the Centers of Excellence, the community college system's labor market research arm, which produces regional supply-demand reports and environmental scans. Occupations are scoped to a region. The same occupation can have different demand profiles in different parts of California.

**Employers.** The organizations hiring in the region, with their sector, scale, and the occupations they hire for. The institutional authority is the California Employment Development Department, the state's authoritative source for employer establishment data. Employers are real organizations with real workforces, not aggregated statistics.

The mapping is one-to-one. Four units of analysis, four authorities. Every claim the ontology makes about the analytical layer traces back to one of these four institutional sources.

## How the units of analysis connect

The four foundationals relate to each other through a small set of relationships that encode the supply-demand logic of workforce development.

On the supply side, students enroll in courses. A student who completes courses inherits the workforce-pathway preparation those courses institutionally feed, traceable back to the curriculum the institution actually delivered.

On the demand side, regions demand occupations and employers hire for them. A regional employer hiring for a particular occupation is generating regional demand for that occupation, traceable back to the labor market the region actually has.

The two sides meet at occupations through the institutional TOP-CIP-SOC crosswalk. The Chancellor's Office publishes the TOP-CIP mapping; the federal NCES and BLS jointly publish the CIP-SOC mapping. Composed end to end, the chain takes a course's six-digit TOP code and yields the set of SOC-coded occupations the course's program institutionally prepares students for. A `Course-[:PREPARES_FOR]->Occupation` edge in the graph is therefore an institutional claim authorized by two named external publications, not an internally-derived inference. Without the institutional bridge, the four foundationals would be two disconnected pairs. With it, the analytical layer becomes a single graph in which a coordinator can traverse from a course to a regional employer through the occupation that connects them.

## The bridge is institutional, not derived

The bridge between curriculum and labor market lives entirely in named external publications. There is no internally-derived skill index between courses and occupations; both sides connect through the SOC-coded occupation node, with the Course→Occupation edge materialized directly from the Chancellor's Office and BLS/NCES crosswalks. This is what keeps the four-entity grounding clean — every connection between foundationals traces back to an institutional source, including the bridge that joins the two sides.

## The unit of action

Alongside the four units of analysis, the ontology contains one unit of action: partnerships. It is the entity the ontology makes available for the user to act on, formulated from the foundationals to drive the work forward.

**Partnerships.** A partnership is a relationship between a college and an industry employer organized around workforce development. Partnerships are not stored as static records in the ontology; they are formulated from the relational structure of the four units of analysis. A partnership becomes meaningful when there is alignment between what occupations a regional employer hires for and which courses at the college institutionally prepare students for those occupations through the TOP-CIP-SOC crosswalk. The ontology makes the alignment computable. It does not predetermine which partnerships exist; it surfaces the conditions under which a partnership becomes worth pursuing.

The partnership artifact closes with a tabular regional supply-demand evidence block — TOP codes, SOC codes, and the gap between projected program completions and regional annual openings. This block is the empirical foundation that any subsequent funding justification (including Strong Workforce Program applications submitted through NOVA) requires. The artifact does not produce the funding application itself; it produces the evidence the application depends on. Strong Workforce as an institutional program shapes what evidence is institutionally legible at state scale, but the program is not its own peer form in the ontology — its presence is felt through the regional data the partnership artifact draws on.

The unit of action depends on the units of analysis to be coherent. A partnership without students, courses, occupations, and employers is not a partnership; it is a wish. The units of analysis are what give the unit of action its grounding. The unit of action is what gives the units of analysis their purpose. The two arenas are what they are because of each other.

## Why it is called an ontology

A database stores records. An ontology represents entities and the relationships between them in a form that asserts those entities are real and those relationships are meaningful. Kallipolis is built on an ontology rather than a database because the things it represents — students, courses, occupations, employers, partnerships — are not rows. They are people, curriculum, jobs, organizations, and institutional relationships. The institutional authorities supply records that describe the units of analysis; the unit of action is formulated from those records but represents something different — the work to be done. The ontology represents both arenas in a single coherent structure.

The ontology is also propositional. It is not a neutral aggregation of data but a theory of what matters for partnership formation in the workforce development domain. Other ontologies of the same domain are possible — credential-centric, industry-centric, geographic-centric — and they would represent the same reality through a different cut. Kallipolis has committed to a particular cut: four units of analysis grounded in institutional authority, one unit of action formulated from them, bridged by the institutional TOP-CIP-SOC crosswalk and scoped by region. The commitment is what gives the ontology coherence. A neutral data model cannot do what an opinionated ontology can do, because partnership work requires a stance on what counts as evidence and what counts as worth doing.

## What is in scope and what is not

The ontology represents the community college from a workforce development perspective. This is a deliberately partial representation. A community college is a complex institution with athletics, governance, financial aid, food services, alumni networks, real estate, research, student services, and dozens of other domains. None of these are in the ontology. They are not modeled because they are not relevant to the formation of partnerships between colleges and industry, which is what the ontology exists to support.

The partiality is the point. By refusing to model everything, the ontology can model the workforce development cut precisely. A more comprehensive representation would dilute the focus and force the ontology to take positions on questions outside its expertise. The two-arena grounding — four units of analysis, one unit of action — is what keeps the scope tight and the claims defensible.

## What the ontology makes possible

Because the ontology exists, certain questions become answerable that were not answerable before. A coordinator can ask which regional employers hire for occupations the college's TOP codes institutionally prepare students for, and get an answer grounded in actual courses and actual labor market demand. A dean can ask how strong the alignment is between the college's curriculum and the regional industries the college serves. A program director can ask which occupations are in regional demand but the college has no aligned program for, and use that gap to inform curriculum planning.

These questions were always askable. They were not always answerable, because answering them used to require assembling fragmented data from disconnected institutional sources by hand, in a process that took days or weeks for each individual question. The ontology compresses that process because the joining has already been done.

Beyond what becomes answerable, the ontology also makes things actionable that were not actionable before. The unit of action — partnerships — is computable in the ontology, which means a coordinator can move from identifying an opportunity to a draft artifact in seconds rather than days. The artifact carries both the narrative case and the empirical evidence — including the regional supply-demand data any subsequent funding justification requires — without leaving the same coherent representation. Without the ontology, each step would require its own data assembly, its own justification, its own translation. With the ontology, the steps share a common foundation, and the work flows as one connected effort.

This is the contribution the ontology makes to the rest of the product. Everything else in Kallipolis — the atlas, the AI workflows, the artifacts — depends on the ontology being a thing that exists. The atlas navigates the ontology. The AI reasons against it. The artifacts cite it. None of them work without the foundation.
