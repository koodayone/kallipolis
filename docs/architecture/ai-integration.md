# AI Integration

Kallipolis calls two LLM providers, each for a distinct role. Claude handles linguistic operations against existing data — translating natural language questions into Cypher and generating partnership and strong workforce narratives. Gemini handles high-volume structured extraction during the ETL pipeline — reading course catalogs, deriving skill mappings, assigning occupations to employers. The split is deliberate, and the constraints on each call are what make the AI integration safe enough to underpin a product whose value depends on being trustworthy.

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

A single shared engine (`backend/workflows/query_engine.py`) translates natural language questions into validated Cypher queries. Five domain-specific system prompts cover the five query targets: students, courses, occupations, employers, and partnerships. Each prompt is tailored to the schema of its target — what nodes to traverse, what properties to return, what constraints to apply.

Every translated query is validated before execution. The validator strips markdown fences, rejects any query containing write operations (`CREATE`, `DELETE`, `SET`, `MERGE`, `REMOVE`, `DROP`, `DETACH`, `CALL`, `FOREACH`, `LOAD`), and verifies that the query is college-scoped — every query must reference a `$college` parameter. The validator is the safety boundary that makes it possible to expose natural language querying to users without giving them implicit write access to the graph.

The query engine also handles JSON parsing fallback: Claude is asked to return a JSON object with `cypher` and `interpretation` fields, but the engine tolerates several response shapes (direct JSON, markdown-fenced JSON, or raw Cypher) so that minor formatting variation does not break the query path.

### Narrative generation

The partnership opportunity flow (`backend/workflows/partnerships.py`) and the strong workforce project flow (`backend/workflows/swp.py`) both use Claude to produce the narratives that get presented to the coordinator. The partnership flow makes multiple Claude calls per opportunity — semantic classification of the partnership type, data assembly logic, narrative section generation — and the SWP flow makes additional calls to produce each NOVA-shaped section.

Both flows are constrained the same way: Claude operates against a tightly bounded context window that contains only the empirical material assembled in the previous step. The model cannot invent evidence, cannot generalize beyond the specific occupations, courses, students, and employers in the assembled context, and cannot reach outside the prompt for additional information. The narrative is grounded by construction, not by post-hoc validation.

The SWP flow also uses Claude's streaming API (`client.messages.stream`) to produce sections progressively. The implementation does brace-depth JSON parsing on the stream so that each section becomes available as soon as Claude finishes generating it, rather than waiting for the entire response to complete. This is what makes the streaming experience in the [strong workforce form](../product/strong-workforce.md) feel responsive rather than batched.

## Where Gemini is called

Gemini is called in the ETL pipeline at four points, all of which are high-volume structured extraction.

### Course extraction from catalogs

`backend/pipeline/scraper_pdf.py` reads college catalog PDFs and uses Gemini to extract structured course data — code, title, department, units, description, prerequisites, learning outcomes, course objectives. Pages are batched in groups of 25 and passed to the model with a structured output configuration. The output is a `RawCourse` object per course, cached as JSON.

This is high-volume work: hundreds of pages per college catalog, dozens of catalogs across the system. Doing it with Claude would be prohibitively expensive and Gemini's structured extraction is fit for purpose.

### Skill enrichment

`backend/pipeline/skills.py` takes the extracted course data and enriches each course with 3-6 workforce-relevant skills drawn from the unified taxonomy. Gemini is constrained to prefer skill names from the seed taxonomy and may introduce novel skill names only when the course teaches something genuinely not covered by existing terms. The output is the `skill_mappings` field on each course, which becomes the `Course → DEVELOPS → Skill` edges in the graph.

This is the methodological pressure point we discussed in [the skills taxonomy product document](../product/the-skills-taxonomy.md): the controlled vocabulary acts as a guardrail against the worst LLM failure modes (skill invention, drift across instances, inconsistency between similar courses). The model is selecting from a fixed set, not generating freely.

### Occupation-to-skill assignment

`backend/pipeline/industry/assign_occupation_skills.py` performs the same kind of constrained selection for occupations: each SOC-coded occupation is assigned 5-8 skills from the existing skill vocabulary. The constraint is the same — only existing taxonomy terms are valid — and the result is the `Occupation → REQUIRES_SKILL → Skill` edges that complete the demand side of the bridge.

Together, the skill enrichment for courses and the skill assignment for occupations are what make the bridge between curriculum and labor market computable. Both sides of the bridge use the same vocabulary because both are produced by Gemini calls constrained to the same controlled set.

### Employer cleanup and occupation mapping

`backend/pipeline/industry/generate_employers.py` uses Gemini to clean employer names from the raw EDD data, generate descriptive sector classifications, and assign relevant occupations from the regional occupation set. This is the lowest-volume of the four Gemini call sites but the most interpretive — the model is being asked to make judgment calls about which occupations a given employer would plausibly hire for, given the employer's name, sector, and the regional occupation set.

The constraint here is the same controlled-set discipline: the model cannot invent new occupations; it can only select from the set already in the graph for that region. This prevents the employer-occupation edges from drifting outside the labor market data the ontology has authoritative grounding for.

## What makes the AI calls safe

Across all six call sites — two for Claude, four for Gemini — the same discipline applies. The model is given a constrained context, asked to operate within a bounded vocabulary, and validated either before execution (the Cypher validator) or by being filtered against the existing graph state (the skill and occupation taxonomies).

This is what makes the AI integration *principled and improvable* in the register the product section establishes. The current implementation produces outputs that pass inspection by knowledgeable reviewers. The improvement vectors are concrete: better source data, expert validation of the controlled vocabularies, longitudinal feedback from outcomes, and refinement of the prompts. None of these improvements require redoing the integration. Each is a path along which the existing pattern can become more rigorous without changing its fundamental shape.

The discipline is also what makes the AI integration coherent with the [trust-through-visibility design philosophy](../product/partnerships.md) of the product. The narratives Claude generates are immediately followed by the empirical material that supports each claim, because the model is operating against that material as its context. The skill assignments Gemini produces are inspectable against the courses and occupations they describe, because the controlled vocabulary makes them traceable. The user is not asked to trust the AI; they are asked to trust the data the AI is summarizing or selecting from. The integration is built so that this trust is well-placed.

## How this connects to the product framing

The two-model split is the operational expression of two distinct kinds of work the product does. The unification work — turning disparate institutional data into a single joinable structure — is Gemini's job, and it happens in the pipeline. The intelligence work — turning the unified structure into something a coordinator can act on — is Claude's job, and it happens at request time.

Both kinds of work are bounded by what the [data authorities](../domain/data-authorities.md) have published. Gemini's extraction is grounded in source documents the authorities produce (catalogs, EDD records, COE projections). Claude's generation is grounded in the empirical material those extractions become. Neither model is asked to invent claims the authorities cannot back. This is the data authority principle realized in the AI integration: every output of an AI call traces, eventually, to an institutional source whose job it is to know that kind of thing.

The AI is the help, not the headline. The architecture reflects this by treating the two models as bounded operations on grounded data, not as the source of the data themselves.
