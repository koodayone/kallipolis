# Kallipolis Documentation

Institutional intelligence for California community college workforce partnerships.

This directory holds the canonical documentation for Kallipolis — what it is, how it works, and how to operate it. It is organized by audience and intent.

## Sections

### [Product](./product/)
What Kallipolis does and who it's for. Written for college CTE coordinators, deans, and partners. No implementation details.

- [Overview](./product/overview.md) — Mission, problem, and audience
- Discover → Propose → Fund — The core product flow *(draft)*
- The Atlas — What users see and do *(draft)*
- Partnership Proposals — Generation flow from a user's perspective *(draft)*
- SWP Builder — Strong Workforce Program project applications *(draft)*
- Natural Language Queries — Asking the graph in plain English *(draft)*

### [Domain](./domain/)
The institutional and policy context that shapes the product. Read this before working on anything substantive.

- [Strong Workforce Program](./domain/strong-workforce-program.md) — Policy, funding, regional variation, college pain points
- Data Authorities — The four institutional sources that ground every claim *(draft)*
- California CC System — 116 colleges, 73 districts, COE regions, consortia *(draft)*
- Glossary — SWP, NOVA, COE, SOC, NAICS, OEWS, TOP, DataMart, LaunchBoard *(draft)*

### [Architecture](./architecture/)
How the system is built. For engineers extending or modifying Kallipolis.

- [System Overview](./architecture/system-overview.md) — Three apps, one graph, the AI surface
- Graph Model — Neo4j schema, constraints, the skill bridge *(draft)*
- API Reference — All endpoints by router *(draft, candidate for auto-generation)*
- AI Integration — Where Claude and Gemini are called and why *(draft)*
- Streaming — SSE for proposals and SWP sections *(draft)*
- Authentication — JWT, college scoping, middleware *(draft)*

### [Pipeline](./pipeline/)
How institutional data enters the graph. The most operationally complex part of the system.

- Overview — The four layers and what "loaded" means *(draft)*
- Course Extraction — PDF scraping, Gemini, the unified skill taxonomy *(draft)*
- Student Generation — Synthetic enrollments and calibration data *(draft)*
- Industry Data — COE occupations, OEWS wages, region loading *(draft)*
- [Employer Generation](./pipeline/employer-generation.md) — EDD scraping, county→metro→COE crosswalk, merge semantics
- Region Reload — Full graph rebuild and verification *(draft)*

### [Operations](./operations/)
Runbooks for setting up and operating Kallipolis.

- Local Setup — Docker Compose, environment variables, first run *(draft)*
- Adding a College — End-to-end onboarding *(draft)*
- Adding a Region — Expanding beyond the Bay Area *(draft)*
- Troubleshooting — Common issues and verification queries *(draft)*

## Conventions

- **Voice.** Institutional, clear, declarative. Short sentences. No hype. No em dashes in body prose. Claims trace to a source.
- **Citations.** Where a claim comes from code, cite `path/to/file.py:line`. Where it comes from external policy, cite the source by name (LAO 2025, AB 1602, NOVA, COE).
- **Audience first.** Each document declares its audience in the first paragraph. Product docs assume no engineering knowledge. Architecture docs assume engineering fluency.
- **Living, not frozen.** Documents that describe code should be regenerable from the code via skills. Documents that describe policy or product strategy are hand-written and reviewed.
