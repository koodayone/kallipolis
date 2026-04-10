# The Strong Workforce Program

*Audience: anyone working on Kallipolis who needs to understand the policy environment the product operates in. Read this before working on the SWP builder, the partnership proposal generator, or the labor market intelligence layer.*

The Strong Workforce Program (SWP) is the funding mechanism that makes Kallipolis actionable. Without it, partnership insights are interesting but unfunded. Understanding SWP is understanding why this product exists and what its outputs need to be defensible against.

## What SWP is

SWP was created by AB 1602 in 2016 to reverse 25 years of declining career and technical education enrollment in California community colleges and to address a projected shortfall of one million middle-skill workers. It is a recurring Proposition 98 appropriation, originally set at $290 million per year. Recent years have allocated approximately $230 million as a portion of the funding has been redirected to nursing through 2029.

SWP is **not a competitive grant**. It is a formula-based allocation that flows to every district in the state annually. The policy lever is the formula itself. Weights are assigned to enrollment, unemployment, projected job openings, and program performance. A 17% incentive component is doubled for economically disadvantaged students.

## Funding structure

SWP funds are split three ways:

| Share | Allocation | Mechanism |
|---|---|---|
| 60% | Local share | Distributed by formula directly to 72 districts |
| 40% | Regional share | Distributed through 8 regional consortia |
| 5% | Systemwide | Reserved for Chancellor's Office activities |

Roughly half of SWP spending goes to employee compensation — CTE faculty salaries, career services staff, counselors. The remainder funds equipment, capital expenditures, and program development.

## Why regional variation matters

The eight regional consortia distribute the regional share differently. Five of them make centralized spending decisions through the consortium itself. Three operate as **pass-through** regions where individual colleges apply for regional funds through collaborative proposals called Regional Joint Ventures.

The Bay Area is one of the three pass-through regions. This is the region Kallipolis currently targets, and it shapes the product directly: in a pass-through region, partnership proposals are literally the currency for accessing the 40% regional share. Colleges that build compelling, data-backed cases get funded. Colleges that don't, don't.

The Legislative Analyst's Office (LAO 2025) found that the five centralized consortia produced better student earnings outcomes than the three pass-through regions. The pass-through model puts the burden on individual colleges to make their own cases — which is exactly the burden Kallipolis is designed to lift.

## What SWP applications require

A SWP project application is submitted through NOVA, the state online project planning and reporting system. Each project requires eight narrative sections, all of which need to be defensible under audit:

1. **Project name and description** — concise framing of the project
2. **Rationale** — labor market justification with regional demand and supply data
3. **Sector** — the industry classification the project serves
4. **Employer narrative** — why this employer or partnership is valuable
5. **Metrics narrative** — how the investment translates to measurable outcomes
6. **Workplan activities** — the concrete actions the project will undertake
7. **Workplan outcomes** — the measurable results those activities produce
8. **Risks and mitigation** — what could go wrong and how it will be addressed

Kallipolis generates all eight sections from the partnership proposal and labor market context already assembled in the graph. The output is intended to be a strong first draft, not a finished application — coordinators retain control of the final submission.

## Pain points Kallipolis addresses

1. **Labor market justification is slow.** Coordinators must demonstrate demand using COE data, employer surveys, or regional validation. Kallipolis automates demand-supply gap analysis directly from the graph.
2. **Reporting burden falls on under-resourced staff.** Small colleges often have a single CTE coordinator handling multiple programs. The SWP builder generates evidence-backed narrative sections that would otherwise consume days of writing.
3. **Curriculum development is bottlenecked by justification.** New CTE programs take 18 months or more. Faster data-backed cases shorten the front of that pipeline.
4. **Assessment is duplicated.** The community college system (through the nine COEs) and local workforce boards both conduct labor market research. Kallipolis consolidates the views into one graph so coordinators stop reconciling overlapping reports.

## Key infrastructure SWP runs on

| System | What it does |
|---|---|
| **NOVA** | State online project planning, expenditure tracking, and reporting system. Where SWP applications are submitted. |
| **CTE LaunchBoard** | Statewide data system tracking certificate and degree completion, job placement, median earnings, and living wage attainment |
| **9 Centers of Excellence** | Regional labor market research arms of the community college system. Produce supply-demand gap reports and environmental scans. |
| **8 regional consortia** | Distribute the 40% regional share. Five centralized, three pass-through (Bay Area is pass-through). |

## How this shapes Kallipolis

Three implications for anyone working on the product:

1. **SWP outputs must be NOVA-compatible.** Character limits, section names, and required metadata follow NOVA's schema. Don't introduce sections NOVA does not have.
2. **Narratives must trace to authoritative sources.** Every claim in a generated SWP narrative needs to be defensible. The pipeline grounds claims in COE occupation data, EDD employer data, college DataMart enrollment, and the college's own course catalog.
3. **Bay Area is the design target.** The pass-through model is what makes Kallipolis valuable. In a centralized consortium, the consortium itself does much of this work. In a pass-through region, the colleges do — and that is where the product earns its keep.
