# The Ontology

The Kallipolis ontology is the foundation of everything the product does. Without it, the atlas has nothing to navigate, the AI has nothing to reason about, and the partnership artifacts have nothing to be grounded in. This document describes what the ontology is, what it commits to, and what it makes possible.

## The essence

The Kallipolis ontology is a digital representation of the community college from a workforce development perspective. It is grounded on four foundational entities — students, courses, occupations, and employers — and on the relationships between them. The proposition the ontology stands on is that these four entities and their relationships are central to the formation of data-driven partnerships between community colleges and industry.

## Two arenas

The ontology is organized around two arenas: a layer of analysis and a layer of action. Both are native to the ontology. They are distinguished by the role each plays, not by their membership.

The first arena holds the **units of analysis** — the four foundational entities that ground the ontology in institutional authority. These are the things the coordinator studies and measures. They represent ground truths about the college and the region: who is enrolled, what is taught, what jobs are in demand, who is hiring. Each unit of analysis is backed by a single institutional source responsible for the truth of that kind of evidence.

The second arena holds the **units of action** — partnerships and strong workforce. These are not facts to be known but things to be done. They are formulated from the units of analysis to drive the work of partnership formation forward. A partnership becomes a unit of action when the conditions for pursuing it become computable from the foundationals. A strong workforce project becomes a unit of action when the partnership has enough empirical grounding to support a fundable case. Both depend on the units of analysis to be coherent, and both give the units of analysis their purpose.

The two arenas exist in the same ontology because the product exists to support both knowing and doing. A purely descriptive ontology would represent the four foundationals but would have no organizing principle for what to do with them. A purely action-oriented ontology would name partnerships and funding pathways but would have no grounding for why any particular one matters. Kallipolis needs both, and it holds both within the same coherent structure.

## The units of analysis

The four units of analysis are foundational because each is backed by a single institutional authority responsible for the truth of that kind of evidence.

**Students.** The people enrolled at a college, with their program affiliation, course history, and the skills they have developed. The institutional authority is the Chancellor's Office Management Information System Data Mart, the system of record for community college enrollment and outcomes. Students appear in the ontology as entities, not as rows. What is represented is the person and what they know how to do, not the database record.

**Courses.** The courses a college actually teaches, with their content, learning outcomes, course objectives, and the skills they develop. The institutional authority is the college's own course catalog — the curricular definition the institution stands behind. Courses are organized by department within a college and are the substrate on which student learning is built.

**Occupations.** The jobs in regional demand, with employment levels, wage data, growth projections, and the skills they require. The institutional authority is the Centers of Excellence, the community college system's labor market research arm, which produces regional supply-demand reports and environmental scans. Occupations are scoped to a region. The same occupation can have different demand profiles in different parts of California.

**Employers.** The organizations hiring in the region, with their sector, scale, and the occupations they hire for. The institutional authority is the California Employment Development Department, the state's authoritative source for employer establishment data. Employers are real organizations with real workforces, not aggregated statistics.

The mapping is one-to-one. Four units of analysis, four authorities. Every claim the ontology makes about the analytical layer traces back to one of these four institutional sources.

## How the units of analysis connect

The four foundationals relate to each other through a small set of relationships that encode the supply-demand logic of workforce development.

On the supply side, students enroll in courses, and courses develop skills. A student who completes a course inherits the skills that course is designed to develop. The student therefore carries an empirical skill profile that traces back to the curriculum the institution actually delivered.

On the demand side, occupations require skills, and employers hire for occupations. A regional employer hiring for a particular occupation is hiring for the skills that occupation requires. The employer therefore generates a derived skill demand that traces back to the labor market the region actually has.

The two sides meet on skills. A skill that is developed by a course on the supply side and also required by an occupation on the demand side is a bridge. Bridge skills are how the supply and demand sides become joinable. Without them, the four foundationals would be two disconnected pairs. With them, the analytical layer becomes a single graph in which a coordinator can traverse from a course to a regional employer through the skill that connects them.

## Skills as emergent

Skills appear in the ontology as the mechanism by which courses connect to occupations, but they are not foundational in the same way the units of analysis are. Skills do not have their own institutional authority. They are derived from analysis of what courses develop and what occupations require, produced by the pipeline as it interprets curriculum descriptions and occupational specifications against a unified skill taxonomy that gives both sides a common vocabulary.

Skills are real and they carry the relational logic of the entire analytical layer. But they are emergent from the foundationals, not authored alongside them. Treating skills as the bridge rather than as a foundation is what allows the four-entity grounding to remain clean.

## The units of action

Alongside the four units of analysis, the ontology contains two units of action: partnerships and strong workforce. They are entities the ontology makes available for the user to act on, formulated from the foundationals to drive the work forward.

**Partnerships.** A partnership is a relationship between a college and an industry employer organized around workforce development. Partnerships are not stored as static records in the ontology; they are formulated from the relational structure of the four units of analysis. A partnership becomes meaningful when there is alignment between what a college's courses develop, what its students know, what occupations a regional employer hires for, and what skills those occupations require. The ontology makes the alignment computable. It does not predetermine which partnerships exist; it surfaces the conditions under which a partnership becomes worth pursuing.

**Strong workforce.** Strong workforce is the funding pathway through which California community colleges convert partnership intelligence into institutional action. As a unit of action in the ontology, it represents the targets and constraints of strong workforce program work — the demand-supply gaps that justify funding requests, the labor market intelligence that grounds project rationale, the curriculum alignment that supports proposal narratives. Like partnerships, strong workforce is formulated from the foundationals.

Both units of action depend on the units of analysis to be coherent. A partnership without students, courses, occupations, and employers is not a partnership; it is a wish. A strong workforce project without an empirical foundation is a story; it is not a fundable proposal. The units of analysis are what give the units of action their grounding. The units of action are what give the units of analysis their purpose. The two arenas are what they are because of each other.

## Why it is called an ontology

A database stores records. An ontology represents entities and the relationships between them in a form that asserts those entities are real and those relationships are meaningful. Kallipolis is built on an ontology rather than a database because the things it represents — students, courses, occupations, employers, partnerships, strong workforce — are not rows. They are people, curriculum, jobs, organizations, institutional relationships, and funding pathways. The institutional authorities supply records that describe the units of analysis; the units of action are formulated from those records but represent something different — the work to be done. The ontology represents both arenas in a single coherent structure.

The ontology is also propositional. It is not a neutral aggregation of data but a theory of what matters for partnership formation in the workforce development domain. Other ontologies of the same domain are possible — credential-centric, industry-centric, geographic-centric — and they would represent the same reality through a different cut. Kallipolis has committed to a particular cut: four units of analysis grounded in institutional authority, two units of action formulated from them, connected through skills and regions. The commitment is what gives the ontology coherence. A neutral data model cannot do what an opinionated ontology can do, because partnership work requires a stance on what counts as evidence and what counts as worth doing.

## What is in scope and what is not

The ontology represents the community college from a workforce development perspective. This is a deliberately partial representation. A community college is a complex institution with athletics, governance, financial aid, food services, alumni networks, real estate, research, student services, and dozens of other domains. None of these are in the ontology. They are not modeled because they are not relevant to the formation of partnerships between colleges and industry, which is what the ontology exists to support.

The partiality is the point. By refusing to model everything, the ontology can model the workforce development cut precisely. A more comprehensive representation would dilute the focus and force the ontology to take positions on questions outside its expertise. The two-arena grounding is what keeps the scope tight and the claims defensible.

## What the ontology makes possible

Because the ontology exists, certain questions become answerable that were not answerable before. A coordinator can ask which regional employers hire for the skills a particular program teaches and get an answer grounded in actual courses and actual labor market demand. A dean can ask how strong the alignment is between the college's curriculum and the regional industries the college serves. A program director can ask which skills are required by occupations in regional demand but are not yet developed by any course at the college, and use that gap to inform curriculum planning.

These questions were always askable. They were not always answerable, because answering them used to require assembling fragmented data from disconnected institutional sources by hand, in a process that took days or weeks for each individual question. The ontology compresses that process because the joining has already been done.

Beyond what becomes answerable, the ontology also makes things actionable that were not actionable before. The two units of action — partnerships and strong workforce — are computable in the ontology, which means a coordinator can move from identifying a partnership opportunity, to drafting a proposal, to building a strong workforce application without leaving the same coherent representation. The unification is what makes the work continuous. Without the ontology, each step would require its own data assembly, its own justification, its own translation. With the ontology, the steps share a common foundation, and the work flows through the arenas as one connected effort.

This is the contribution the ontology makes to the rest of the product. Everything else in Kallipolis — the atlas, the AI workflows, the artifacts — depends on the ontology being a thing that exists. The atlas navigates the ontology. The AI reasons against it. The artifacts cite it. None of them work without the foundation.
