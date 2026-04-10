# Kallipolis Documentation

Documentation for Kallipolis, a partnership intelligence layer that unifies academic and labor market data for community colleges to forge stronger workforce partnerships with industry.

This directory holds the canonical documentation for the product, the domain it operates in, and the system that delivers it. It is currently being developed as a working document for building a coherent mental model of Kallipolis, and will evolve into broader-audience documentation as the structure stabilizes.

## Sections

### [Product](./product/)
What Kallipolis is, what it does today, and what it is aiming toward. Operates at two altitudes: the long-arc mission, and the present-day operational reality. No engineering or pipeline detail.

**Foundational elements:**
- [Overview](./product/overview.md) — Mission, what the product does today, the thesis, and the gap it fills
- [The Ontology](./product/the-ontology.md) — The two arenas: four units of analysis grounded in institutional authority, and two units of action formulated from them
- [The Atlas](./product/the-atlas.md) — The navigational layer where the user visualizes and moves through both arenas of the ontology
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
The institutional and policy context that shapes the product. Background needed to make sense of why the product exists and looks the way it does. The spine of this section is pending — the existing draft is heavily SWP-organized and needs to be reconsidered against the new product overview.

- Strong Workforce Program — Policy, funding, regional variation *(needs revision: was framed as the central organizing concept; should become one piece of context among several)*
- Data Authorities — The institutional sources that ground every claim *(draft)*
- California Community College System — Structure, scale, and the consortia model *(draft)*
- Glossary — Domain vocabulary *(draft)*

### [Architecture](./architecture/)
How the system is built. For engineers extending or modifying Kallipolis. The technical choices are downstream of the product framing rather than upstream of it, so most of the existing draft survives — but voice and emphasis should be checked against the new overview.

- [System Overview](./architecture/system-overview.md) — Three apps, one graph, the AI surface *(needs review for voice consistency)*
- Graph Model — The Neo4j schema *(draft)*
- API Reference — All endpoints by router *(draft, candidate for auto-generation)*
- AI Integration — Where Claude and Gemini are called and why *(draft)*
- Streaming — SSE for proposals and SWP sections *(draft)*
- Authentication — JWT, college scoping, middleware *(draft)*

### [Pipeline](./pipeline/)
How institutional data enters the graph. The mechanism by which the ontology comes into being. Operationally the most subtle part of the system.

- Overview — The layers and what "loaded" means *(draft)*
- Course Extraction — PDF scraping, Gemini, the unified skill taxonomy *(draft)*
- Student Generation — Synthetic enrollments and calibration data *(draft)*
- Industry Data — Occupations and regions *(draft)*
- [Employer Generation](./pipeline/employer-generation.md) — EDD scraping, county→metro→COE crosswalk, merge semantics
- Region Reload — Full graph rebuild and verification *(draft)*

### [Operations](./operations/)
Runbooks for setting up and operating Kallipolis.

- Local Setup *(draft)*
- Adding a College *(draft)*
- Adding a Region *(draft)*
- Troubleshooting *(draft)*

## Conventions

- **Voice.** Institutional, declarative, direct. Short sentences. No hype. The institution is the agent; the product empowers institutional capacity.
- **Two altitudes.** Distinguish what the product does today (operational, defensible) from what it is aiming toward (mission, aspirational). Do not collapse one into the other.
- **Spines first, content second.** Each section has a governing principle that determines what belongs in it. Content is written against the spine, not the other way around. When the spine drifts, the content drifts with it.
- **Spines unify; they do not gatekeep.** The job of a spine is to name the through-line that makes everything in the section coherent, not to argue features in or out.
- **Citations.** Where a claim comes from code, cite `path/to/file.py`. Where it comes from external policy or research, cite the source by name.
- **Living, not frozen.** Documentation that describes code should be regenerable from the code. Documentation that describes policy or product strategy is hand-written and revised dialectically.
