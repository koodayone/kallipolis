# Kallipolis Documentation

Documentation for Kallipolis, a partnership intelligence layer that unifies academic and labor market data for community colleges to forge stronger workforce partnerships with industry.

This directory holds the canonical documentation for the product, the domain it operates in, and the system that delivers it. The product section is at a coherent first-draft state; the other sections (domain, architecture, pipeline, operations) remain in development. As the structure stabilizes, the documentation will evolve into broader-audience material.

## Sections

### [Product](./product/)
What Kallipolis is, what it does today, and what it is aiming toward. Operates at two altitudes: the long-arc mission, and the present-day operational reality. No engineering or pipeline detail.

**Foundational elements:**
- [Overview](./product/overview.md) — Mission, what the product does today, the thesis, and the gap it fills
- [The Ontology](./product/the-ontology.md) — The two arenas: four units of analysis grounded in institutional authority, and two units of action formulated from them
- [The Atlas](./product/the-atlas.md) — The navigational layer at two scales: the College Atlas surfaces a single institution through six iconic entry points, the State Atlas surfaces the entire California community college system for cross-institution navigation
- [The Unified Skills Taxonomy](./product/the-skills-taxonomy.md) — The controlled vocabulary through which the ontology semantically reasons about relationships between the four foundational forms; the semantic center of the ontology's analytical capability

Each form in the ontology receives its own dedicated treatment, describing the product experience in relation to that form.

**Units of analysis:**
- [Students](./product/students.md) — Represented people whose competency portrait makes the supply side of workforce development empirical
- [Courses](./product/courses.md) — The institution's commitment to teach, interpreted through a unified taxonomy to produce the skills that bridge curriculum to labor market
- [Occupations](./product/occupations.md) — Categories of regional labor market demand, grounded in Centers of Excellence research, with skill gap identification as the unique improvement vector
- [Employers](./product/employers.md) — Real organizations grounded in EDD records, restrictively scoped to actors the workforce development ecosystem can coordinate with, the operational target the other three foundationals direct work toward

**Units of action:**
- [Partnerships](./product/partnerships.md) — Data-driven partnership opportunities formulated from the four units of analysis, presented as drafts a coordinator can use; the discovery stage of the partnership lifecycle and the core value proposition of Kallipolis
- [Strong Workforce](./product/strong-workforce.md) — The justification stage of the partnership lifecycle, where a discovered partnership is translated into a NOVA-compatible SWP project application; the form through which Kallipolis becomes institutionally legible at state scale

### [Domain](./domain/)
Documents how the workforce development worldview manifests in the context of California Community Colleges, and the components of that manifestation that most directly shape Kallipolis. Same audience as the product section: written for mental model first, with the option of becoming broader-audience material later.

- [Overview](./domain/overview.md) — The worldview, how it manifests in California Community Colleges, and how the four domain areas relate to the realization of the Kallipolis vision
- [Strong Workforce Program](./domain/strong-workforce-program.md) — The funding and compliance structure through which the worldview is operationalized at scale, grounded in California Education Code Part 54.5 (sections 88820–88833)
- [Data Authorities](./domain/data-authorities.md) — The four institutional sources that ground every claim Kallipolis makes: DataMart for students, college catalogs for courses, the Centers of Excellence for occupations, and the EDD Labor Market Information Division for employers
- [California Community College System](./domain/california-community-college-system.md) — The 116-college, 2.2-million-student system whose state-level coordination and explicit workforce mandate give Kallipolis the architectural shape it has
- [Glossary](./domain/glossary.md) — The vocabulary the worldview speaks in: institutional names, classification systems, and policy concepts that appear throughout the documentation

### [Architecture](./architecture/)
How the system is built. The technical choices are downstream of the product framing rather than upstream of it. Same audience as the product and domain sections: written for mental model first, with the option of becoming engineering-onboarding material later.

- [System Overview](./architecture/system-overview.md) — Three apps, one graph, the AI surface, the streaming and authentication patterns
- [Graph Model](./architecture/graph-model.md) — The Neo4j schema: eight node types, eleven relationships, and the bridge logic that connects curriculum to labor market through skills
- [AI Integration](./architecture/ai-integration.md) — Where Claude and Gemini are called, what each model is asked to do, and the constraints that make the integration principled and improvable

### [Pipeline](./pipeline/)
How institutional data enters the graph. The mechanism by which the ontology comes into being. Same audience as the architecture section: written for mental model first.

- [Overview](./pipeline/overview.md) — The five stages, what each stage produces, and how the curriculum-side and industry-side pipelines converge in the same graph
- [Student Generation](./pipeline/student-generation.md) — The synthetic methodology, the DataMart calibration, and what the generated population is and is not
- [Employer Generation](./pipeline/employer-generation.md) — EDD scraping, county→metro→COE crosswalk, merge semantics

## Conventions

- **Voice.** Institutional, declarative, direct. Short sentences. No hype. The institution is the agent; the product empowers institutional capacity.
- **Two altitudes.** Distinguish what the product does today (operational, defensible) from what it is aiming toward (mission, aspirational). Do not collapse one into the other.
- **Spines first, content second.** Each section has a governing principle that determines what belongs in it. Content is written against the spine, not the other way around. When the spine drifts, the content drifts with it.
- **Spines unify; they do not gatekeep.** The job of a spine is to name the through-line that makes everything in the section coherent, not to argue features in or out.
- **Citations.** Where a claim comes from code, cite `path/to/file.py`. Where it comes from external policy or research, cite the source by name.
- **Living, not frozen.** Documentation that describes code should be regenerable from the code. Documentation that describes policy or product strategy is hand-written and revised dialectically.
