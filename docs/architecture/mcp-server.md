# The MCP Server

The MCP server is the conversational surface of the Kallipolis intelligence layer. It exposes the ontology to a frontier model through the Model Context Protocol, so that a practitioner can reach the same supply-and-demand analysis the dashboard shows by asking for it in plain language. It is read-only, stateless, and public, mounted in-process at `/mcp` (`backend/main.py`). The code lives in `backend/mcp_server/`.

This document is the single account of how that surface works: the principle it is built on, the analytical construct it exposes, the catalog of forms and the descent that walks them, the response envelope that keeps every figure defensible, and the tools as shipped. It draws on two companions for the parts that are not specific to the conversational surface — the analytical substrate in [the supply–demand construct](../../research/mcp-server/supply-demand-construct.md), and the surface-agnostic reading doctrine in [the epistemic contract](../domain/epistemic-contract.md) — and summarizes each here rather than restating it.

## The essence

The consumer of every tool response is the model, not the user. Each payload becomes part of the model's context and shapes how it reasons for the rest of the conversation. So the server does not return bare data — it returns data framed the way an ideal workforce-development practitioner would frame it. Bare data produces a model that narrates numbers; framed data produces a model that reasons about programs, occupations, employers, and gaps, and stays inside the evidence. The server is an opinionated experience over the ontology, not a database adapter.

Two levels of provenance carry the framing. In-payload authority tags and epistemic markers steer the model; a deep link to the corroborating dashboard view lets the practitioner verify the figure with their own eyes. The model's case is compelling because it is rigorous — a claim lands because it is backed by a provenance-tagged number and a view the practitioner can inspect.

## The construct it exposes

Every analysis the server performs is one view of a single relation: institutional **supply** (what colleges produce) against labor-market **demand** (what the region hires), projected across the TOP→CIP→SOC crosswalk, bounded by a sector. The two sides do not meet directly. Demand is a property of occupations, grounded in Centers of Excellence research, and is regional by construction. Supply is a property of programs, grounded in CCCCO DataMart completions, and is institutional by construction. The crosswalk is what joins them: it carries a program's *addressable demand* (the openings across the occupations it prepares graduates for) and an occupation's *supply* (the completions of every program that feeds it).

The crosswalk is many-to-many, and that is by design — a program genuinely prepares graduates for several occupations, and an occupation is genuinely served by several programs. Because these projections are pools, not exclusive assignments, they are summed at full value and carry no epistemic penalty. Summing across is also the authority's own method: it is how the Centers of Excellence compute projected supply, so matching it is what keeps the numbers corroborated rather than divergent. A sector bounds the projection to authority-backed edges, which is what makes it defensible — across sectors the crosswalk is noise, within a sector it is a coherent mapping.

This construct is the substrate of the whole intelligence layer, not the MCP server alone. It is realized in `backend/partnerships/quantities.py`, the single computation layer beneath both the dashboard builders and the MCP forms. The conversational surface is one consumer of it. The full formalism — the crosswalk operator, the two computation regimes, the qualifier and comparison operators — is [the supply–demand construct](../../research/mcp-server/supply-demand-construct.md).

## The catalog: forms and coordinates

An analysis separates into a **form** and a **coordinate**. A form is the shape of an analytical move — designed, curated, and epistemically guarded. A coordinate is the scope it runs at — an institution and, where the form needs one, a sector. The model picks a form and a coordinate; it does not invent a form. This makes the catalog's boundary a testable property rather than a judgment call: a question the catalog can answer is a form the model selects, and a question it cannot is a form that would have to be composed from primitives.

The forms are not a hand-picked list. They are a bounded grid of `{anchor × operation}`, and both axes are finite. The anchors are the ontology's spine — **member → sector → program → occupation → employer** — and the operations are a small set: overview, drill, greenfield, and compare. The catalog fills that grid; it does not sprawl. The forms and their static identity — the practitioner question, the domain meaning, the load-bearing guardrail — live in `backend/mcp_server/catalog.py`.

| Anchor | Built form | Answers |
|---|---|---|
| member | `member_portfolio` | The whole institution across every sector it runs, against regional demand, in one call. |
| sector | `sector_overview` | One sector's portfolio, program-forward: the member's programs and the demand each addresses. |
| program | `program_pathways` (program mode) | What a program prepares students for. |
| occupation | `supply_demand_gaps`, `occupation_profile`, `program_pathways` (occupation mode) | The gap for an occupation; its whole regional picture; the programs that feed it. |
| employer | `regional_employers` | Which regional employers hire for an occupation. |
| greenfield entry | `unmet_demand` | In-demand occupations the member graduates no one into. |
| compare | `compare` | A member's programs ranked against each other on a chosen measure. |

The catalog is a graph, not a list. Each form carries adjacency edges — the ideal practitioner's sense of what to ask next — wired in `catalog.py` and emitted as the `next_moves` of every response. The server owns the edge set; the model phrases it. An edge is a typed pointer to a form and a coordinate, never free text, and its target is always a callable tool.

## The descent

The catalog graph, walked, is the descent — the conversation's principled shape. It follows the ontology's spine in the practitioner's own order:

> orient → **member_portfolio** (all sectors) → **sector_overview** (the member's programs and the demand they address) → a **program** → a single **occupation** → the **employers** behind it, with **unmet_demand** as the greenfield off-ramp.

The descent is soft, not scripted. The `next_moves` are guide rails: each node answers one question at one scope, the practitioner walks it turn by turn, and the model may leave the rail when a question jumps grain. There is never a blank prompt to face, and the conversation is never an open graph traversal.

It is program-first by design. The program is the practitioner's lever — colleges run, fund, and start programs, and the Strong Workforce Program funds programs — and the occupation is its justification. So `sector_overview` is program-forward: its rows are the member's programs, each carrying its completions and its addressable demand, and occupations are drilled from a program rather than listed alongside it. The greenfield case has no program yet, so it enters occupation-first through `unmet_demand`. Entry is conditional on intent: program-first for what exists, occupation-first for what is missing.

The descent is also how the practitioner learns the ontology. A sector view composes programs and occupations through the visible crosswalk, so the practitioner learns the shape of the model — the program-occupation relation, projected-versus-actual supply, regional-versus-institutional demand — by being oriented. Pedagogy is a property of where the conversation starts, not a separate mode.

One rule keeps the descent efficient: a form's scope matches its question's scope, so the model routes rather than loops. A whole-institution question is a single `member_portfolio` call across all sectors, not a loop of `sector_overview`. Aggregation lives in the cached canonical layer, so adding a college or a sector is data, not code.

## The response envelope

Every analytical response is a fixed-arity envelope (`backend/mcp_server/envelope.py`). Its shape is the behavioral spec, because the shape is what the model reads. Three obligations are structural rather than advisory:

- **Bind.** Every figure is a qualified value carrying its source, its granularity, and its vintage. No field on the envelope holds a bare number; to state a figure the model must carry its qualifiers, because the figure does not exist in the payload without them.
- **Gate.** When a defensible figure cannot be produced — a granularity mismatch, an absent or suppressed value, an out-of-scope request — the envelope returns an explicit marker (`unavailable`, `unknown`, or `out-of-scope`) with the value forced to null. Absence is represented, never a zero the model could read past, never a silent omission.
- **Distinguish.** Quantities that are easy to conflate are separate, named keys — projected supply is never merged with actual awards, regional demand never with institutional supply. Non-conflation is enforced by naming.

The envelope's other slots frame without interpreting. A **framing** slot carries the static domain meaning of the form and computed salience flags (a wide crosswalk fan-out, small counts, a stale vintage) but never a reading of the specific numbers. A **licensing** slot states what the result does and does not license the model to claim. **Next moves** carry the catalog edges. A **view link** carries the dashboard deep link, or an `unavailable` marker when the form has no corresponding view. Provenance is carried once at response scope so it survives truncation — under context pressure, data rows drop before qualifiers do. Responses are summary-first: an aggregate, the most salient rows, and a pointer to call again for the rest, which keeps a wide crosswalk from flooding the model's context.

The division of labor is firm. The server supplies meaning and salience; the model supplies interpretation. The model may make a case, but every claim must trace to a qualified figure the tools returned. The surface-agnostic statement of these obligations — the one every Kallipolis surface honors, not the MCP server alone — is [the epistemic contract](../domain/epistemic-contract.md).

## The reading contract

The reading contract reaches the model through the one channel every MCP client injects: the tool description. `backend/mcp_server/worldview.py` holds a condensed `DOCTRINE` — the voice, the reading rules, and the navigation offer — and `backend/mcp_server/server.py` prepends it to every tool's description, so the contract arrives on every call. A fuller `WORLDVIEW` preamble rides the server's advisory instructions field, but it load-bears nothing the descriptions do not already carry. Each form's field-specific guardrail — the projected-versus-actual reminder, the regional-gap reminder, the statewide-wage reminder — lives on that form in the catalog, written once.

The prose posture is intent-gated. The model is told to speak plainly — programs, occupations, employers, awards, demand, gaps — and to add a qualifier only when it changes how a figure should be read: a wage pooled statewide at the program grain rather than one college's graduates, a supply that is a multi-year projection rather than a single year, a value that is absent and so unknown rather than zero. Fuller provenance comes when the practitioner asks where a figure comes from, not on every number. The payload still binds every value structurally; the model is primed to sound like a practitioner rather than a citation.

## Orientation and scope

Analysis is scoped to an institution, and orientation is how that scope is established (`backend/mcp_server/scope.py`). There is no server-side fuzzy matcher, because the consumer is a frontier model: `list_institutions` exposes the universe of institutions and their live sectors, the model maps the practitioner's college to a canonical identifier, and `institution_overview` confirms the match and grounds the model in what is knowable at that scope — the live sectors, the region, and the honest limits.

Scope-first is emergent, not a separate checkpoint. A form needs a coordinate; orientation is how a coordinate is obtained; a form called without a resolvable coordinate returns a gate marker that routes back to orientation. There is no server session: scope is a parameter on every call and is echoed on every response, so the qualifier triple is itself the conversation's scope memory, and a long conversation does not drift.

Orientation is also where the limits are stated plainly. Wage outcomes are pooled statewide at the program grain for a single cohort, never a specific college's graduates. Spend-against-gap and eligibility overlays are unavailable — no allocation or clock-hour data exists in the ontology. DataMart suppression is not preserved, so a blank is unknown, not zero. The architecture degrades honestly rather than promising evidence it cannot produce.

## The surface as shipped

Eleven tools are live at `https://api.kallipolis.us/mcp`, without authentication, over stateless HTTP, in a frozen order. The public names are practitioner questions; the internal form identifiers differ and are mapped to public names in `catalog.py`.

| Tool | Coordinate | Answers |
|---|---|---|
| `list_institutions` | filter (optional) | The institutions the system knows and the sectors each is live in, for identity resolution. |
| `institution_overview` | member | The member, its region, its per-sector program counts, its honest limits, and suggested questions. |
| `member_portfolio` | member | One row per sector — regional demand against regional projected completions, the member's supply and share, the gap — plus an institution-wide total, in one call. |
| `sector_overview` | member, sector | The sector aggregate, with rows for the member's programs ranked by the demand each addresses. |
| `compare` | member, unit type, criterion, sector (optional) | A member's programs ranked against each other on a chosen measure. |
| `supply_demand_gaps` | member, sector, occupation (optional) | Regional annual openings minus total regional projected completions, per occupation. |
| `program_coverage` | member, sector | Covered, Partial, or Gap for each college-and-program, by whether a feeding program both enrolls and awards. |
| `program_pathways` | member, sector, program or occupation | The crosswalk in either direction, with the fan-out surfaced rather than collapsed. |
| `regional_employers` | member, sector, occupation (optional) | Regional employers ranked by how prominently their industry staffs the target occupations. |
| `occupation_profile` | member, occupation | The whole regional picture of one occupation — demand, feeders, regional supply and gap, employers, and its sector. No sector required; the region is derived from the member. |
| `unmet_demand` | member | Occupations the region demands but the member graduates no one into, filtered to community-college-servable education, a living-wage floor, and a meaningful-openings floor, ranked by opportunity. |

A guided-onboarding prompt, `start-here`, accompanies the tools. An OAuth-protected twin of the same set is banked in `server.py` for a future private-data phase but is dormant.

### The gap figure

The supply–demand gap is regional annual openings minus the **total** regional projected completions — every college in the member's Centers-of-Excellence region. A member's own completions are its **share** of that regional supply, never the gap itself. Supply is the Centers-of-Excellence Annual Projected Supply method — a trailing three-year average of DataMart completions, reconstructed on current DataMart data — read as a projection rather than one year's raw count. This is the figure most easily misread, and the guardrail against reading the gap as one college's shortfall is stated on the form itself.

### Comparison

`compare` ranks a member's programs by a chosen criterion, turning a measure into a decision — which program is largest, fastest-growing, most under-supplied, or highest-earning. The criteria menu is generated from the registry in `backend/mcp_server/compare.py`, so the surface updates the moment a criterion or a unit type is added — data, not code. Every criterion is a plain sum-across pool, a ratio computed at the program grain, or a directly measured graduate outcome. None is a weighted composite: a program wage blended from its occupations' wages would be such a composite, and is excluded by construction.

## What it is not

The server is a framing layer, not a reimplementation. The forms wrap the existing deterministic engine — the builders in `backend/partnerships/landscape_build.py`, `backend/partnerships/landscape_programs.py`, and `backend/partnerships/landscape_employers.py` — and the canonical resolvers in `backend/partnerships/quantities.py`, and add the envelope. Because every form composes the same canonical functions that the dashboard builders compose, a program's numbers cannot drift between the two surfaces; corroboration is a property of the shared computation layer, not a reconciliation step.

The tools are task-shaped, not graph primitives: there is no raw query surface. Form outputs are reproducible given a coordinate. The server never mutates the graph or triggers a pipeline. It does not generate documents — the board-ready report is a separate surface. It does not replace the dashboard or the Atlas; it materializes from them and points back at them.

## The road not yet built

The catalog is deliberately incomplete, and the missing cells of the grid are the roadmap. The largest are the sector-anchor aggregate as a standalone orientation form and the comparison operators that set a member against a reference set — market share, supply concentration, and competitive overlap. These are not new primitives; they are the same relation evaluated across a set of colleges rather than a single anchor, and they are the first forms to promote when the server takes on open composition. A new form is earned by evidence that the catalog cannot answer a real question, not by enumeration in advance.
