# Documentation Conventions

This document codifies the patterns the Kallipolis documentation follows. It is the source of truth for what *correct documentation* means in this repository, and it is the document both the audit infrastructure (`tools/docs-audit/`) and the skill instructions reference when they need to know how documentation should be written.

Two audiences consult it. **Contributors** (human or agent) writing documentation read this to know how to write content that passes the audit and matches the established voice. **Tooling** (the audit, the skills) reads this as the contract that defines what it should verify or enforce.

---

## Voice and altitude

### Voice

Institutional, declarative, direct. Short sentences. The institution is the agent; the product empowers institutional capacity. No hype, no marketing language. Each claim earns its place by saying something specific.

### Altitude

Documentation operates at multiple altitudes. Make sure each statement is at the right one:

- **Mission altitude.** The long-arc framing of what the product is for. Present in overview documents.
- **Operational altitude.** What the product does today. Present in product, domain, architecture, and pipeline documents.
- **Implementation altitude.** How specific code does what it does. Present in architecture and pipeline documents only.

Do not collapse altitudes. A mission claim ("Kallipolis is a partnership intelligence layer") is different from an operational claim ("the partnerships flow generates a draft narrative"), which is different from an implementation detail ("`partnerships.py` uses brace-depth parsing to stream sections"). Each altitude has a place; mixing them produces unclear writing.

### Spines and unification

Each section of the documentation has a governing spine — a through-line that makes everything in the section coherent. Spines unify, they do not gatekeep. Their job is to name the principle that ties the section together, not to argue individual features in or out. Content is written against the spine; when the spine drifts, the content drifts with it.

---

## Structural conventions

### File and directory layout

```
docs/
├── README.md            # Top-level index
├── conventions.md       # This document
├── product/             # What Kallipolis is and does
├── domain/              # The institutional context
├── architecture/        # How the system is built
└── pipeline/            # How data enters the graph
```

Each section has an overview document as its entry point (`overview.md` for sections that follow that pattern, `system-overview.md` for architecture). File names use kebab-case. Files that document a structural concept use the `the-` prefix (`the-ontology.md`, `the-atlas.md`, `the-skills-taxonomy.md`). Files that document a form or entity use the name directly (`students.md`, `courses.md`).

### Document structure

Each document opens with a brief framing paragraph that orients the reader. Most documents then have an `## The essence` section near the top — a tight statement of what the document is about. Substantive sections follow. Unifying observations or conclusions go at the end.

### What not to include

- **No audience tags** at the top of files. The audience is consistent across the documentation; restating it is noise.
- **No `*(draft)*` markers** in committed content unless something is genuinely a placeholder.
- **No claims about features that do not exist**, even aspirationally. Aspirational content should be marked as such within the document, not asserted as present.

---

## Code-grounded claim conventions

These are the conventions the audit relies on. Any claim that needs to be auto-verified must be in one of these forms. Claims written in prose without these structures are still allowed, but they are not covered by the audit and are the contributor's responsibility to keep accurate.

### File path references

Inline code spans or markdown links: `` `backend/partnerships/api.py` `` or `[the loader](../backend/courses/load.py)`. The audit verifies that the referenced file exists.

### API endpoints

In markdown tables with `Method` and `Path` columns, or inline as `` `POST /partnerships/targeted/stream` ``. The audit prefers tables for systematic listings because they are more reliably parsed than prose.

### Schema — node types, properties, constraints

The node-type table in `architecture/graph-model.md` is the canonical schema reference. Each row has columns for `Node`, `Key properties`, `Constraint`, and `What it represents`. The audit reads this table directly and verifies it against `backend/ontology/schema.py` and the loaders.

### Relationships — edge types and properties

The relationship table in `architecture/graph-model.md` is the canonical reference. Each row has columns for `Relationship`, `From → To`, `Properties`, and `What it encodes`. The audit reads this table directly and verifies it against the `MERGE` and `SET` statements in the loaders.

### Model names

The verbatim model identifier in inline code: `` `claude-sonnet-4-6` ``, `` `gemini-2.5-flash` ``. The audit greps the codebase for the actual model strings and compares.

### Numerical constants

The verbatim Python identifier in inline code: `` `PRIMARY_STICKINESS = 0.60` ``, `` `DEPT_CAP = 6` ``, `` `BATCH_SIZE = 30` ``. The audit cross-references these against the actual constants in the corresponding Python files.

### Cross-references

Always relative markdown links: `[The Atlas](./product/the-atlas.md)`. Never absolute URLs for internal documentation. Anchor links should match section headers exactly.

---

## Feature-primary layout and vocabulary alignment

The backend and the atlas are organized around **ontology units**, not around engineering layers. Each unit (students, courses, occupations, employers, partnerships, strong-workforce) owns a directory containing all of its code, and the name of that unit is the same across every layer of conversation about it — product doc, backend directory, URL prefix, atlas directory. This is what keeps product language and engineering language in sync, and what keeps multi-agent work composable: two agents working on two features touch non-overlapping files.

This section is the contract. Two audit checks — `backend_layout` and `vocabulary_alignment` — enforce it mechanically on every push.

### The principle

One concept, one canonical name, mechanical transformations to every other surface form, bidirectional verification. The canonical source is the product doc filename stem under `docs/product/`. Every other surface form derives from it via a well-defined rule, not via a handwritten mapping that could drift independently.

### Surface forms and transformations

Each ontology unit currently has four load-bearing surface forms, enforced by the audit:

| Surface | Location | Derivation from canonical |
|---|---|---|
| Product doc | *docs/product/CANONICAL.md* | Canonical (identity) |
| Backend package | *backend/CANONICAL_WITH_UNDERSCORES/* | Replace `-` with `_` |
| Atlas feature | *atlas/college-atlas/CANONICAL/* | Canonical (identity) |
| URL prefix | */CANONICAL* in `backend/main.py` | Prepend `/` |

For example, `strong-workforce` (the canonical form, matching `docs/product/strong-workforce.md`) derives `backend/strong_workforce/`, `atlas/college-atlas/strong-workforce/`, and `/strong-workforce` respectively. The hyphen-to-underscore transform exists because Python packages cannot contain hyphens; the other three surfaces preserve the canonical form.

Three further surface forms exist but are **not yet enforced** by the audit: Neo4j node labels (`Student`, `Course`, etc.), Pydantic model prefixes (`StudentSummary`, `EmployerMatch`), and test file names (`test_student_helpers.py`). These involve PascalCase and singular/plural rules that need more design before mechanical enforcement.

### Rules enforced by `backend_layout`

The `backend_layout` check (in `tools/docs-audit/checks/backend_layout.py`) enforces three structural invariants about `backend/`:

1. Only known directories live at the top of `backend/`. The six feature directories plus the shared-infrastructure directories (`backend/ontology/`, `backend/llm/`, `backend/pipeline/`, `backend/tests/`, `backend/scripts/`, `backend/docs/`) are allowed. A new top-level directory under `backend/` — for example, a catchment named *shared/* or *utils/* — fails the check. New features go in their own feature directory; new shared code goes in `backend/ontology/` or `backend/llm/`.

2. Each feature directory contains at least `__init__.py`, `api.py`, and `models.py`. A feature missing one of those is either half-built or structurally broken.

3. No stray Python files at `backend/` top level except `main.py`. Every `.py` file belongs in a feature directory or a shared-infrastructure directory.

### Rules enforced by `vocabulary_alignment`

The `vocabulary_alignment` check (in `tools/docs-audit/checks/vocabulary_alignment.py`) enforces bidirectional correspondence across the four current surface forms. It walks:

1. **Forward:** for each non-meta product doc under `docs/product/`, verify that the derived backend directory, atlas directory, and URL prefix all exist.

2. **Reverse:** for each backend feature directory and each atlas feature directory, verify that a corresponding product doc exists.

Both directions are necessary. Forward catches aspiration without implementation (a product doc for a unit that wasn't built). Reverse catches implementation without documentation (a feature built without being described in product language).

### How to add a new ontology unit

The sequence is: write the product doc first, then derive the other surface forms. The product doc is the source of truth, and everything else is bound to it.

1. Create the new product document under `docs/product/` — its filename stem (e.g., `regional-workforce-boards` for `regional-workforce-boards.md`) is the canonical form.
2. Create the new backend feature directory under `backend/`, applying the hyphen-to-underscore transform to the canonical form. Include at minimum `__init__.py`, `api.py`, and `models.py`.
3. Create the new atlas feature directory under `atlas/college-atlas/`, preserving the canonical form's hyphens.
4. Add the router to `backend/main.py` with an `app.include_router` call whose `prefix` argument is `/` followed by the canonical form.
5. Run `python3 tools/docs-audit/audit.py` and confirm both `backend_layout` and `vocabulary_alignment` still pass.

Any deviation from this sequence — a product doc without code, code without a doc, a URL prefix that doesn't match the feature directory — will fail the audit at step 5.

### How to add a meta doc under `docs/product/`

Meta documents that describe the ontology framing rather than naming a unit (for example, `the-ontology.md`, `the-atlas.md`, `the-skills-taxonomy.md`) must be registered explicitly in the audit, or the vocabulary alignment check will treat them as units and demand matching code.

Add the filename stem to the `_META_DOC_STEMS` set in `tools/docs-audit/checks/vocabulary_alignment.py`. This is a deliberate friction — it forces the contributor to answer "is this a unit or meta?" every time a new product-section document is added.

### How to add an exemption

If a unit legitimately skips one of the four surface forms — for example, an action unit whose atlas experience is nested inside a consuming analysis unit rather than standing alone — the exemption lives in the `UNIT_EXEMPTIONS` dict at the top of `tools/docs-audit/checks/vocabulary_alignment.py`. The entry must document *why* the exemption exists so future readers can judge whether it still applies. The dict is currently empty; all six units currently have all four surface forms.

### Why this is the convention

Feature-primary layout and vocabulary alignment are the substrate for two properties the project depends on: **agentic parallelization** (two agents working on two features touch non-overlapping files, so their work composes by merging directories rather than by merging within files), and **product-engineering vocabulary alignment** (the name a coordinator reads in the product doc is the same name a developer reads in the code directory and the same name an agent uses when asked to "improve the Students feature"). Without mechanical enforcement, both properties decay on natural timescales as new code is added, features are renamed, and shortcuts are taken under deadline. The two audit checks listed above are what keeps the substrate load-bearing instead of aspirational.

---

## What this enables

### The audit (`tools/docs-audit/`)

The audit reads documentation according to the conventions above. Each check targets a specific class of claim and verifies it against the actual code. When a check fails, the audit reports the discrepancy with enough context for a contributor to resolve it.

The audit can only verify claims that follow the conventions. A claim written in unstructured prose is allowed but is not auto-verified.

### Skills

Skills that write or update documentation reference this document in their SKILL.md instructions. A skill that adds an API endpoint to the documentation knows to add it as a table row, not as a prose mention, because that is what this document specifies.

Skills that load documentation as runtime context (`load-domain-context`, etc.) can rely on the documentation being structured according to these conventions, which means they can extract the information they need without each skill having to re-derive the parsing logic.

The conventions are the contract that connects the audit, the skills, and the documentation itself. All three depend on the conventions being well-defined and respected.

---

## How conventions evolve

The conventions document is a living artifact. It grows when the audit or the skill ecosystem grows.

**When a new convention is added:**

1. Update this document with the new convention
2. Update the corresponding audit check, or add a new one if needed
3. Update SKILL.md files for any skills that write documentation in the affected area

**When an existing convention is changed:**

1. Update this document
2. Update the audit checks that depend on the convention
3. Update affected documentation to match the new convention
4. Re-run the audit to verify everything is consistent

The conventions document is the source of truth. If the audit and the conventions disagree, the conventions are correct and the audit needs to be updated. If the documentation and the conventions disagree, the documentation needs to be updated.
