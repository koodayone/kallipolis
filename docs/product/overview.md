# Kallipolis: Overview

*Audience: CTE coordinators, deans, workforce partners, prospective stakeholders. No engineering knowledge assumed.*

Kallipolis is an institutional intelligence platform for California community college workforce program coordinators. It helps colleges identify industry partnerships grounded in their actual curriculum, demonstrate labor market demand from authoritative sources, and turn that evidence into fundable Strong Workforce Program project applications.

## The problem

California community colleges are the largest workforce development system in the country. Every year, coordinators are asked to justify new programs, expand existing ones, and apply for Strong Workforce Program funds that flow through regional consortia. The work is bottlenecked by four recurring frictions:

1. **Labor market justification.** Demonstrating demand requires assembling Centers of Excellence reports, OEWS wage data, employer surveys, and regional projections from disconnected sources.
2. **Reporting burden.** NOVA, the state planning system, requires GL-reconciled expenditure tracking and quarterly forecasting. Small colleges with one CTE coordinator wearing multiple hats struggle to keep up.
3. **Curriculum development latency.** A new CTE program typically takes 18 months or more to move through approval. Faster, data-backed justification accelerates the pipeline.
4. **Duplicated assessment.** Both the community college system and local workforce boards conduct overlapping labor market research. Coordinators reconcile the same questions across multiple sources.

Kallipolis addresses these frictions by consolidating curriculum, student, occupation, and employer data into a single graph and applying AI to the operational tasks that consume the most time.

## What it does

Kallipolis is organized around three actions: **discover**, **propose**, and **fund**.

### Discover
The atlas surfaces partnership opportunities by traversing the skill graph from a college's actual courses and students to occupations in regional demand and employers hiring for those occupations. Coordinators can query the graph in plain English ("which manufacturing employers hire for the skills our welding program teaches?") and get answers grounded in their own curriculum and authoritative regional data.

### Propose
Once an opportunity is identified, Kallipolis generates a partnership proposal narrative. Three engagement types are supported: internships, curriculum co-design, and advisory boards. The narrative names specific occupations, draws on the college's actual courses and student composition, and identifies skill gaps where curriculum could be extended. Proposals are written in a voice intended to be sent — direct, evidence-grounded, and respectful of existing programs.

### Fund
The Strong Workforce Program builder takes a partnership proposal and produces the eight narrative sections required for a NOVA-compatible SWP project application. Each section is anchored in labor market intelligence drawn from the graph: regional demand, college supply estimates, demand-supply gaps, and the curriculum alignment evidence assembled during the proposal stage.

## Who it's for

**Primary users.** California community college CTE coordinators, deans of workforce education, and program directors who write SWP applications and broker industry partnerships.

**Secondary audiences.** Centers of Excellence analysts who supply the labor market intelligence; regional consortium leads who evaluate SWP proposals; workforce development board staff coordinating with colleges.

**Not the audience.** Students looking for jobs, employers looking to hire, or faculty looking for curriculum design tools. Kallipolis is operational infrastructure for the institutional layer.

## What grounds the work

Every analytical node in Kallipolis traces to a single institutional authority. This is a deliberate epistemic choice — no source is asked to answer a question outside its expertise.

| Node | Authority | What it answers |
|---|---|---|
| Students | DataMart | Who is enrolled, in what programs, with what outcomes |
| Courses | Course catalogs | What the college actually teaches |
| Occupations | Centers of Excellence | What jobs are in demand in the region |
| Employers | Employment Development Department | Who hires in the region and at what scale |

When a dean asks where a number comes from, the answer is one line: it comes from the institution whose job it is to know. No blending across sources. No averaging across methodologies. No provenance ambiguity.

## What it does not do

Kallipolis does not replace NOVA, COE research, or institutional research offices. It is not a system of record. It does not store student PII. It does not generate curriculum, manage course approval, or handle expenditure reporting. It is an analytical and drafting layer that sits above the systems of record and accelerates the work of building defensible cases for partnership and funding.

## Where to go next

- [Strong Workforce Program](../domain/strong-workforce-program.md) — The funding mechanism that makes Kallipolis actionable
- Discover → Propose → Fund — The end-to-end product flow *(draft)*
- The Atlas — What the interactive interface does *(draft)*
