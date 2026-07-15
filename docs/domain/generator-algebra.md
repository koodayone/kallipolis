# The generator algebra

Every question a practitioner asks Kallipolis is a walk over a small, typed graph: from an institution
to its programs, from a program to the occupations it prepares students for, from an occupation to
regional demand and the employers behind it. The tools that answer those questions are the graph's
*generators* — a handful of operations that compose into walks. This document names that algebra: its
objects, its operations, and the *laws* a correct walk must preserve. It is the specification the
semantic evaluation (Tier C) grades the analyst against, and the reference the dashboard/MCP
unification builds toward. The algebra itself lives in code; this document narrates and cites it, and does not
restate it — the single writer is [`backend/mcp_server/catalog.py`](../../backend/mcp_server/catalog.py).

## The essence

A practitioner's question is a request to evaluate a **measure at a coordinate**, sometimes over a
**comparison class**. Answering it is a walk over typed objects via typed operations. The measure is
correct only if the walk reached the right coordinate — the right grain, the right direction, the
right comparison class. Two surfaces answer these questions, the MCP analyst and the dashboard, and
the algebra's laws are what keep their answers one and the same.

## Objects, coordinates, and operations

- **Objects** are the typed nodes: an Institution at a grain (college, district, consortium, region),
  a Program (TOP6), an Occupation (SOC), a Sector, an Employer, joined through the TOP→CIP→SOC
  crosswalk. The coordinate of any figure — its member, sector, region, occupation, or program — is
  carried on the wire by the `Coordinate` model in
  [`backend/mcp_server/envelope.py`](../../backend/mcp_server/envelope.py).
- **Operations** are the eleven tools, each a form with a natural-language `question`, a domain
  `meaning`, and a load-bearing `guardrail`, declared in
  [`backend/mcp_server/catalog.py`](../../backend/mcp_server/catalog.py). The legal adjacency between
  them — the "what to ask next" a walk may follow — is the `EDGES` table in the same file. Comparison
  is its own operation, whose unit types and criteria are registered in
  [`backend/mcp_server/compare.py`](../../backend/mcp_server/compare.py).
- **Measures** at a coordinate — openings, wage, growth, projected supply, latest-year supply, gap,
  share, addressable demand — are read under the source·granularity·vintage qualifier triple of
  [the epistemic contract](./epistemic-contract.md).

## The laws

A correct walk preserves these invariants. They are the machine-readable `LAWS` manifest in
[`backend/evals/conversational/semantic_checks.py`](../../backend/evals/conversational/semantic_checks.py),
each with a relation and a check; the probes that exercise them live in
[`backend/evals/conversational/semantic_pathways.py`](../../backend/evals/conversational/semantic_pathways.py).

| Law | Relation | What it forbids | Probe seam · check |
|---|---|---|---|
| Coordinate identity | `=` | a measure at a coordinate reading differently depending on which tool reached it | `coordinate_identity` · `run_group` (coordinate-aware) |
| Regional invariance | `=` | an occupation's regional gap changing with which member anchors the query | `grain_transitions` · `run_group` |
| Grain nesting | `≤` | a college's own supply exceeding its district's; a member's share outside [0,1] | `grain_transitions` · `run_group` |
| Part ≤ whole | `≤` | served-occupation demand exceeding full-sector demand; addressable pools summed | `two_demand`, `non_summable` · `surfaced_both_demands` + judge |
| Forward/reverse consistency | `⊇` | an occupation's feeder set omitting a program declared to prepare for it (membership, never magnitude — the crosswalk is many-to-many and lossy) | `forward_reverse` · `forward_reverse_membership` + judge looseness-flag |
| Absence ≠ zero | language | a gated or blank field read as `0`; a structural zero (no program) read as unknown | `absence_zero` · `absence_not_zero_language` |
| Establish before analyze | ordering | a scoped measure computed before the institution coordinate is established | S7 onboarding · `establish_order` |

The `=` laws run as **metamorphic groups** (a relation across a paired A/B set of transcripts); the
rest run **per-transcript**. Coordinate identity's group is the **two-window** invariant: the same
coordinate reached two ways must read one value — the specification the dashboard/MCP unification is
built toward, with the dashboard offered via `view_link` as the second window.

The `=` laws need no blessed answer — they assert a relation across a probe *group*, which is why
they are the trust backbone: a misroute that reports a member's own share instead of the regional gap
makes two anchors of the same occupation disagree, and the equality fails. The many-to-many laws are
inexact **by construction** — forward/reverse is set membership plus a required looseness flag, never
magnitude equality — and the `LAWS` tolerance column encodes that so no later change tightens it into
a false invariant.

## The seams

The laws break, when they break, at the *joins* — where one natural-language question maps to two
correctly-scoped readings. These are the coverage targets the probe matrix weights toward:

- **Two-demand.** "Demand for my sector" is the full-sector market (`sector_overview`) or the demand
  for the occupations already served (`supply_demand_gaps`) — two correct numbers; the analyst must
  name which. This is the feeder-resolution seam logged in
  [`backend/evals/conversational/SUBSTRATE-QUEUE.md`](../../backend/evals/conversational/SUBSTRATE-QUEUE.md).
- **Forward/reverse.** A program's occupations versus an occupation's programs — asymmetric under the
  lossy crosswalk.
- **Grain transitions.** College ↔ district ↔ consortium ↔ region — the regional gap is invariant
  while the member's own supply and share change.
- **Comparison classes.** Comparing the wrong unit type, or on an unstated axis.
- **Absence versus zero**, and **non-summable pools**.

## How it is verified

The algebra is enforced at two levels. At the **server**, the referential-integrity tests in
[`backend/mcp_server/test_compare.py`](../../backend/mcp_server/test_compare.py) prove the *computation*
honors coordinate identity and grain nesting — the right form is called by construction. In
**conversation**, Tier C proves the *analyst's walk* honors the same laws: the metamorphic runner and
the per-transcript checks in
[`backend/evals/conversational/semantic_checks.py`](../../backend/evals/conversational/semantic_checks.py),
graded on classification and defensibility against Article VI of
[the conversational constitution](../../backend/evals/conversational/constitution.md). The coverage of
this document against the enforced manifest is itself a test (`test_semantic.py`), so every law named
here maps to a check, and every check to a law.
