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
