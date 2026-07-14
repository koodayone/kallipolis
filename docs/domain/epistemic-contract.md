# The Epistemic Contract

The [data authorities](./data-authorities.md) establish who stands behind each figure Kallipolis surfaces. The epistemic contract is the companion discipline: how to *read* those figures without overstating them. It is the set of obligations every Kallipolis surface honors when it puts a number in front of a practitioner — the conversational layer, the reports, the dashboard. Where the authority principle makes a claim traceable, the epistemic contract keeps the reading of that claim honest.

## The essence

Every figure Kallipolis surfaces carries three qualifiers — its **source**, its **granularity**, and its **vintage** — and means less than it appears to without them. The contract is three obligations. **Bind** every figure to its qualifiers, so a number never travels without the context that makes it mean what it means. **Gate** an absent figure as unknown, never as zero, so a suppressed or missing value is read as missing evidence rather than a measured absence. **Distinguish** quantities that look alike but are not — a multi-year supply projection from a single year's count, regional demand from an institution's own share of it. A surface that honors these three can be trusted at scale, because a practitioner can trace any claim it makes back to a figure an institutional authority is responsible for.

## The qualifier triple

A figure is not a bare number. It is a number plus three things:

- **Source** — the institutional authority responsible for that kind of evidence: demand and wage from the Centers of Excellence, program supply and enrollment from DataMart, employer relevance from federal staffing patterns. The [data authorities](./data-authorities.md) document names them.
- **Granularity** — the scope the figure describes. A wage pooled statewide at the program-type grain is a different fact from one college's own graduates' earnings; a regional openings count is a different fact from one institution's hiring.
- **Vintage** — the period the figure is as of. A projection built on a trailing window is a different fact from the most recent single year.

The triple travels with the figure. To state the number is to carry its qualifiers.

## The three obligations

**Bind.** Every figure arrives bound to its source, granularity, and vintage, and is stated with whatever part of that binding changes how it should be read. A number offered without its binding invites the reader to assume a precision or a scope the evidence does not support.

**Gate.** An absent value — suppressed at the source, unknown, or outside the scope of what the data holds — is represented as absent, never coerced to zero. DataMart suppresses small cells rather than reporting them; a suppressed cell is unknown, not empty. Reading absence as zero manufactures a fact the authority never asserted.

**Distinguish.** Quantities that are easy to conflate are kept as separate, named facts. The system never merges a projection with an actual, or a regional total with an institutional share, into one convenient number.

## The reading rules

The distinctions the contract most often has to protect:

- **Projected supply is not a single year's count.** The supply figure behind a gap is a projection — a trailing three-year average of DataMart program completions, the same method the Centers of Excellence use for annual projected supply, reconstructed on current DataMart data. It smooths year-to-year noise. The most recent single year is a separate figure that can run above or below the projection. Both are DataMart completions; the distinction is the window, not the source. Never say "supply" without saying which.
- **The gap is regional.** A supply–demand gap measures regional openings against the whole region's projected completions. An institution's own completions are its share of that regional supply, not the gap itself.
- **Wages are statewide and coarse.** Wage figures are pooled statewide at the program-type grain for a single cohort. They describe a program type across California, never a specific college's own graduates.
- **The crosswalk is many-to-many.** The program-to-occupation bridge is the external TOP→CIP→SOC crosswalk, not an internal skills index. A program can prepare students for many occupations and an occupation can be fed by many programs; the fan-out is surfaced, never collapsed into a single per-program number.
- **Absent is not zero.** When a value is unavailable, unknown, or out of scope, the honest statement is that the evidence is missing — not that the quantity is nil.

## Rigor without recitation

The contract governs what is *true* about a figure; it does not demand that every qualifier be recited every time a figure is named. A surface honors it by stating figures plainly and attaching a qualifier when it changes how the number should be read — a statewide wage, a projected rather than single-year supply, an absent value that is unknown rather than zero. The fuller provenance of a figure — whose method, whose data, as of when — is offered when a practitioner asks where a number comes from or whether to trust it, not on every number. What is never optional is that each claim trace to a figure the data returned, and that a corroborating view be offered so the practitioner can verify with their own eyes. The persuasion comes from the rigor, never from going past the evidence.

## How this manifests

The epistemic contract is surface-agnostic doctrine. The conversational layer renders it as the reading posture that primes the model and as the per-figure guardrails on each analysis it returns. The reports render it as the discipline of following every generated narrative immediately with the data that grounds it. The dashboard renders it as the source and scope labels attached to each figure a practitioner sees. Each surface enforces the same obligations through its own mechanism; the contract is the shared canon they all answer to, so that a figure read in a conversation, a report, and a dashboard says the same true thing about itself in all three.
