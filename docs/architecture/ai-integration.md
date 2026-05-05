# AI Integration

Kallipolis calls two LLM providers, each for a distinct role. Claude handles linguistic operations against existing data — translating natural language questions into Cypher. Gemini handles high-volume structured extraction during the ETL pipeline — reading course catalogs and assigning occupations to employers. The split is deliberate, and the constraints on each call are what make the AI integration safe enough to underpin a product whose value depends on being trustworthy.

## The split

The two models operate at different points in the system and are asked different kinds of questions.

| Model | Where it runs | What it does |
|---|---|---|
| **Claude** (`claude-sonnet-4-6`) | Backend, at request time | Linguistic operations on existing data: NL-to-Cypher, narrative generation |
| **Gemini** (`gemini-2.5-flash`) | Pipeline, during ETL | High-volume structured extraction from documents and descriptions |

Claude is asked to *reason* about institutional context — gaps, alignments, narratives, voice. Gemini is asked to *extract* structured information from unstructured sources at scale. Neither model crosses into the other's role. This is partly a question of cost (Gemini is dramatically cheaper for high-volume extraction work) and partly a question of fit: Claude is better at the kind of careful reasoning the narrative generation requires, and Gemini is better at the kind of disciplined extraction the pipeline requires.

## Where Claude is called

Claude is called in two distinct workflows on the backend.

### Natural language to Cypher

A single shared engine (`backend/llm/query_engine.py`) translates natural language questions into validated Cypher queries. Five domain-specific system prompts cover the five query targets: students, courses, occupations, employers, and partnerships. Each prompt is tailored to the schema of its target — what nodes to traverse, what properties to return, what constraints to apply.

Every translated query is validated before execution. The validator strips markdown fences, rejects any query containing write operations (`CREATE`, `DELETE`, `SET`, `MERGE`, `REMOVE`, `DROP`, `DETACH`, `CALL`, `FOREACH`, `LOAD`), and verifies that the query is college-scoped — every query must reference a `$college` parameter. The validator is the safety boundary that makes it possible to expose natural language querying to users without giving them implicit write access to the graph.

The query engine also handles JSON parsing fallback: Claude is asked to return a JSON object with `cypher` and `interpretation` fields, but the engine tolerates several response shapes (direct JSON, markdown-fenced JSON, or raw Cypher) so that minor formatting variation does not break the query path.

### Partnership opportunity reports (fully deterministic)

The Partnerships flow is occupation-centric and fully deterministic. The orchestrator at `backend/partnerships/opportunity.py` composes the per-(college, SOC) report from the institutional graph: regional demand from COE, TOP-grouped curriculum coverage via `_gather_aligned_curriculum` in `backend/partnerships/gather.py`, student impact via `_gather_student_pipeline` in the same module, and the candidate regional employer set sorted by NAICS-4 industry-share. The five-section narrative is composed by templates in `backend/partnerships/opportunity_narrative.py` (employer-agnostic prose) over the gathered structured evidence.

There is no LLM call at request time in the Partnerships flow today.

## Where Gemini is called

Gemini is called in the ETL pipeline at two points, both of which are high-volume structured extraction or interpretation against an institutional reference set.

### Course extraction from catalogs

`backend/courses/scrape_pdf.py` reads college catalog PDFs and uses Gemini to extract structured course data — code, title, department, units, description, prerequisites, learning outcomes, course objectives. Pages are batched in groups of 25 and passed to the model with a structured output configuration. The output is a `RawCourse` object per course, cached as JSON.

This is high-volume work: hundreds of pages per college catalog, dozens of catalogs across the system. Doing it with Claude would be prohibitively expensive and Gemini's structured extraction is fit for purpose.

### Employer cleanup and occupation mapping

`backend/employers/generate.py` uses Gemini to clean employer names from the raw EDD data, generate descriptive sector classifications, and assign relevant occupations from the regional occupation set. This is the lowest-volume of the Gemini call sites but the most interpretive — the model is being asked to make judgment calls about which occupations a given employer would plausibly hire for, given the employer's name, sector, and the regional occupation set.

The constraint here is institutional reference grounding: the model cannot invent new occupations; it can only select from the set already in the graph for that region, bounded by the BLS OEWS National Industry-Occupation Matrix that links the employer's NAICS-4 to the SOCs that industry actually staffs. This prevents the employer-occupation edges from drifting outside the labor market data the ontology has authoritative grounding for.

The pipeline previously carried two additional Gemini call sites — skill enrichment for courses and skill assignment for occupations. Both have been retired with the move to the institutional TOP-CIP-SOC crosswalk as the bridge between curriculum and labor market.

## What makes the AI calls safe

Across every call site — Claude at request time (NL-to-Cypher per feature, partnership selection, partnership narrative, proposal evaluation, SWP section streaming) and Gemini in the pipeline (course extraction, skill enrichment, occupation-to-skill assignment, employer cleanup) — the same discipline applies. The model is given a constrained context, asked to operate within a bounded vocabulary, and validated either before execution (the Cypher validator) or by being filtered against the existing graph state (the skill and occupation taxonomies).

This is what makes the AI integration *principled and improvable* in the register the product section establishes. The current implementation produces outputs that pass inspection by knowledgeable reviewers. The improvement vectors are concrete: better source data, expert validation of the controlled vocabularies, longitudinal feedback from outcomes, and refinement of the prompts. None of these improvements require redoing the integration. Each is a path along which the existing pattern can become more rigorous without changing its fundamental shape.

The discipline is also what makes the AI integration coherent with the [trust-through-visibility design philosophy](../product/partnerships.md) of the product. The narratives Claude generates are immediately followed by the empirical material that supports each claim, because the model is operating against that material as its context. The skill assignments Gemini produces are inspectable against the courses and occupations they describe, because the controlled vocabulary makes them traceable. The user is not asked to trust the AI; they are asked to trust the data the AI is summarizing or selecting from. The integration is built so that this trust is well-placed.

## How this connects to the product framing

The two-model split is the operational expression of two distinct kinds of work the product does. The unification work — turning disparate institutional data into a single joinable structure — is Gemini's job, and it happens in the pipeline. The intelligence work — turning the unified structure into something a coordinator can act on — is Claude's job, and it happens at request time.

Both kinds of work are bounded by what the [data authorities](../domain/data-authorities.md) have published. Gemini's extraction is grounded in source documents the authorities produce (catalogs, EDD records, COE projections). Claude's generation is grounded in the empirical material those extractions become. Neither model is asked to invent claims the authorities cannot back. This is the data authority principle realized in the AI integration: every output of an AI call traces, eventually, to an institutional source whose job it is to know that kind of thing.

The AI is the help, not the headline. The architecture reflects this by treating the two models as bounded operations on grounded data, not as the source of the data themselves.
