# Kallipolis Documentation

Documentation for Kallipolis, a partnership intelligence layer that unifies academic and labor market data for community colleges to forge stronger workforce partnerships with industry.

This directory holds the canonical documentation for the product, the domain it operates in, and the system that delivers it. The product section is at a coherent first-draft state; the other sections (domain, architecture, pipeline, operations) remain in development. As the structure stabilizes, the documentation will evolve into broader-audience material.

## Sections

### [Product](./product/)
What Kallipolis is, what it does today, and what it is aiming toward. Operates at two altitudes: the long-arc mission, and the present-day operational reality. No engineering or pipeline detail.

**Foundational elements:**
- [Overview](./product/overview.md) — Mission, what the product does today, the thesis, and the gap it fills
- [The Ontology](./product/the-ontology.md) — The two arenas: four units of analysis grounded in institutional authority, and one unit of action formulated from them
- [The Atlas](./product/the-atlas.md) — The navigational layer at two scales: the College Atlas surfaces a single institution through six iconic entry points, the State Atlas surfaces the entire California community college system for cross-institution navigation

The ontology bridges curriculum to labor market through the institutional TOP-CIP-SOC crosswalk maintained by the California Community Colleges Chancellor's Office and BLS/NCES — a single externally-authored mapping, not an internally-derived skills index. Each form in the ontology receives its own dedicated treatment, describing the product experience in relation to that form.

**Units of analysis:**
- [Students](./product/students.md) — Retained as a navigational unit; individual records removed under the non-PII posture, with supply-side signal carried by program-level aggregates
- [Courses](./product/courses.md) — The institution's commitment to teach, tagged with the institutional TOP code that bridges each course to the occupations its program prepares students for
- [Occupations](./product/occupations.md) — Categories of regional labor market demand, grounded in Centers of Excellence research, with curriculum gap identification as the unique improvement vector
- [Employers](./product/employers.md) — Real organizations grounded in EDD records, restrictively scoped to actors the workforce development ecosystem can coordinate with, the operational target the other three foundationals direct work toward

**Unit of action:**
- [Partnerships](./product/partnerships.md) — Data-driven partnership opportunities formulated from the units of analysis, presented as drafts a coordinator can use; the core value proposition of Kallipolis

### [Domain](./domain/)
Documents how the workforce development worldview manifests in the context of California Community Colleges, and the components of that manifestation that most directly shape Kallipolis. Same audience as the product section: written for mental model first, with the option of becoming broader-audience material later.

- [Overview](./domain/overview.md) — The worldview, how it manifests in California Community Colleges, and how the four domain areas relate to the realization of the Kallipolis vision
- [Strong Workforce Program](./domain/strong-workforce-program.md) — The funding and compliance structure through which the worldview is operationalized at scale, grounded in California Education Code Part 54.5 (sections 88820–88833)
- [Data Authorities](./domain/data-authorities.md) — The institutional sources that ground every claim Kallipolis makes: DataMart for program awards and enrollment, college catalogs for courses, the Centers of Excellence for occupations, and the EDD Labor Market Information Division for employers
- [The Epistemic Contract](./domain/epistemic-contract.md) — How to read the figures the authorities ground without overstating them: the source·granularity·vintage qualifier triple and the Bind / Gate / Distinguish obligations every Kallipolis surface honors
- [California Community College System](./domain/california-community-college-system.md) — The 116-college, 2.2-million-student system whose state-level coordination and explicit workforce mandate give Kallipolis the architectural shape it has
- [Glossary](./domain/glossary.md) — The vocabulary the worldview speaks in: institutional names, classification systems, and policy concepts that appear throughout the documentation

### [Architecture](./architecture/)
How the system is built. The technical choices are downstream of the product framing rather than upstream of it. Same audience as the product and domain sections: written for mental model first, with the option of becoming engineering-onboarding material later.

- [System Overview](./architecture/system-overview.md) — Three apps, one graph, the AI surface, the streaming and authentication patterns
- [Graph Model](./architecture/graph-model.md) — The Neo4j schema: seven node types, nine relationships, and the institutional `PREPARES_FOR` edge that bridges curriculum to labor market through the TOP-CIP-SOC crosswalk
- [Institutional Deference Evolution](./architecture/institutional-deference-evolution.md) — The architectural commitment to ground every analytical claim in a named institutional source, and the C-series of commits that progressively realized it
- [AI Integration](./architecture/ai-integration.md) — Where Claude and Gemini are called, what each model is asked to do, and the constraints that make the integration principled and improvable
- [The MCP Server](./architecture/mcp-server.md) — The conversational surface: a frontier model reasoning over the ontology through a bounded `{anchor × operation}` catalog of supply-and-demand forms, walked as a program-first descent and kept defensible by the response envelope
- [Deployment](./architecture/deployment.md) — The preview deployment shape: static atlas on Cloudflare Pages, backend + Neo4j on a GCP VM behind Caddy, secrets in Secret Manager, nightly backups to Cloud Storage

### [Pipeline](./pipeline/)
How institutional data enters the graph. The mechanism by which the ontology comes into being. Same audience as the architecture section: written for mental model first.

- [Overview](./pipeline/overview.md) — The four stages, what each stage produces, and how the curriculum-side and industry-side pipelines converge in the same graph
- [Employer Generation](./pipeline/employer-generation.md) — EDD scraping at the COE region unit, sector scoping, Gemini cleanup, merge semantics
- [SWP Sector NAICS Composition](./pipeline/swp-sector-naics.md) — The authoritative mapping from NAICS 4-digit codes to Strong Workforce priority sectors, with the full inclusion/exclusion trail
- [Occupation Generation](./pipeline/occupation-generation.md) — COE demand feed, institutional CTE scope filter (PCAH TOP→CIP→SOC), and the `education_level`-on-node design choice

## Conventions

The patterns this documentation follows are codified in [conventions.md](./conventions.md), which serves as the contract that the audit infrastructure (`tools/docs-audit/`) and any skill that writes documentation both reference. In brief:

- **Voice.** Institutional, declarative, direct. The institution is the agent; the product empowers institutional capacity.
- **Two altitudes.** Distinguish what the product does today (operational, defensible) from what it is aiming toward (mission, aspirational).
- **Spines first, content second.** Each section has a governing principle that determines what belongs in it. Spines unify; they do not gatekeep.
- **Code-grounded claims have structured forms.** Claims that need to be auto-verified live in tables, code spans, or markdown links — not in unstructured prose. See [conventions.md](./conventions.md) for the specific patterns.
- **Living, not frozen.** Documentation that describes code is verified against the code by the audit and revised when either side changes.
