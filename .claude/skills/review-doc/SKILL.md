---
name: review-doc
description: >
  This skill should be used when the user asks to "review a doc", "lint a doc",
  "check this doc against conventions", or names a specific markdown file under
  docs/ with phrasing like "is this doc well-written?", "does this follow the
  conventions?", or "tighten this doc". It reviews a single Kallipolis
  documentation file against docs/conventions.md, surfaces violations the audit
  cannot catch (voice, altitude, spine, structural patterns, forbidden markers),
  and proposes per-finding edits the user approves one at a time before they
  are applied.
---

# Documentation Review (Conventions Compliance)

A focused, conservative reviewer for a single documentation file in `docs/`. The skill is the judgment-based half of conventions enforcement: the audit (`tools/docs-audit/`) covers everything code-grounded and deterministic, and this skill covers what requires reading comprehension — voice, altitude, structural patterns, and the forbidden-markers conventions.

The skill is built on a single principle: **propose, never auto-apply.** Every edit is a discrete, approved act. The skill never homogenizes the user's voice, never mass-edits, and never proceeds past a finding without explicit approval.

## When to use

Run this skill when the user wants to lift a specific narrative documentation file to a higher standard against the conventions. Typical invocations:

- "Review `docs/product/students.md`."
- "Lint this doc for conventions compliance."
- "Tighten `docs/domain/the-ontology.md`."

Do **not** run this skill on:

- Files outside `docs/`
- Code files
- Whole directories — review one file per invocation. Whole-tree review is intentionally not supported because the per-finding approval gate becomes unworkable at scale.

## Argument

A single file path under `docs/`, optionally with a severity threshold:

```
/review-doc docs/product/students.md
/review-doc docs/product/students.md --threshold=blocking
/review-doc docs/product/students.md --threshold=all
```

If no path is given, ask the user which doc to review. Do not guess.

## Severity model

Three levels, each with a clear definition:

- **`blocking`** — Audit failures, and clear-cut structural violations that have a definitive answer (forbidden marker present, narrative doc missing required structural element). No judgment call.
- **`quality`** — Voice, altitude, and spine findings. The skill's core value-add. Each is a judgment call the skill explains with a direct quote and a rationale grounded in `conventions.md`. **This is the default threshold.**
- **`all`** — Adds stylistic suggestions: word choice, sentence length, paragraph length. Off by default because nitpicks drown signal.

The threshold filters which findings are reported; it never affects how the skill reasons about the doc. The skill always evaluates every category internally, and only suppresses output for findings below the threshold.

## Process

The skill runs five phases in strict order. Each phase has a clear purpose and produces concrete state for the next.

### Phase 1 — Read the contract

Before doing anything else, read `docs/conventions.md` in full. This is the source of truth for every judgment the skill makes. Do not rely on memorized rules — `conventions.md` evolves, and the skill must reflect its current state.

If `docs/conventions.md` does not exist or cannot be read, abort and tell the user. The skill cannot operate without its contract.

### Phase 2 — Run the audit

Invoke the deterministic audit on the whole repo:

```bash
python3 tools/docs-audit/audit.py
```

If the audit passes (`PASS: all N checks passed`), continue to Phase 3.

If the audit fails, surface the failures verbatim and ask the user:

> The audit is currently failing on the repo. The failures may or may not be in the file you're reviewing. Do you want to:
> (1) fix the audit failures first, then come back to review,
> (2) proceed with the review of `<path>` anyway, noting that some audit findings may be relevant?

Do not silently ignore an audit failure. The audit is the trust foundation; surfacing its state is part of the skill's job.

### Phase 3 — Read the target file and determine its genre

Read the target file. Look for YAML frontmatter at the very top:

```yaml
---
type: reference
---
```

If `type: reference` is present, the doc is a **reference doc** (e.g., `docs/architecture/graph-model.md`). Reference docs have the structural conventions relaxed because their natural shape is tables, diagrams, and queries, not narrative paragraphs and an essence section. Reference docs still get voice review, but skip the structural pass and skip altitude/spine evaluation.

If no frontmatter is present, the doc is a **narrative doc** by default. Narrative docs get the full review.

### Phase 4 — Structural pass (narrative docs only)

For narrative docs, check the following structural conventions deterministically. Each finding here is `blocking` severity unless explicitly noted.

1. **Opening framing paragraph.** Per `conventions.md`: *"Each document opens with a brief framing paragraph that orients the reader."* Look at the content immediately after the H1 title. If the first non-empty content is anything other than a paragraph (e.g., a heading, a table, a list, a code block), flag it.
2. **`## The essence` section.** Per `conventions.md`: *"Most documents then have an `## The essence` section near the top — a tight statement of what the document is about."* This is a "most documents" rule, not "every document," so flag absence as `quality` rather than `blocking` — some docs legitimately don't need it.
3. **Forbidden markers.** Per `conventions.md`: *"No `*(draft)*` markers in committed content unless something is genuinely a placeholder. No audience tags at the top of files."* Scan for `*(draft)*`, audience-tag patterns (e.g., `**Audience:**`, `**For:**`), and any other markers `conventions.md` lists. Each is `blocking`.
4. **Aspirational claims asserted as present.** Per `conventions.md`: *"No claims about features that do not exist, even aspirationally. Aspirational content should be marked as such within the document, not asserted as present."* This is a judgment call — flag specific sentences that describe behavior the skill suspects may not exist, but mark these as `quality` not `blocking` because the skill cannot reliably verify what does and doesn't exist. The user makes the final call.
5. **File naming.** If reviewing a doc that violates kebab-case or the `the-` prefix convention for structural concepts (per `conventions.md`), flag it as `blocking`. The fix involves a rename, which the skill should propose but not execute (renames cascade to other audit checks).

### Phase 5 — Judgment pass

Read the prose carefully, section by section. Evaluate against the three judgment-based conventions in `conventions.md`:

#### Voice

`conventions.md` specifies: *"Institutional, declarative, direct. Short sentences. The institution is the agent; the product empowers institutional capacity. No hype, no marketing language. Each claim earns its place by saying something specific."*

Look for:

- **First-person plural ("we", "our", "us")** in product/domain prose. The institution is the agent, not "we." Flag and propose a rephrase.
- **Marketing register**: "excited to," "powerful," "seamless," "cutting-edge," "revolutionary," "delight," "empower" used as marketing puff. Flag and propose institutional alternatives.
- **Hedge words** that suggest uncertainty where conventions ask for declarative claims: "may," "might," "could," "should," "perhaps." Flag only if they appear in a section that ought to be declarative.
- **Vague claims** that don't say something specific: "a variety of," "many things," "several aspects." Flag and propose concretion.
- **Long sentences** that bury the point. Conventions ask for short sentences. Flag any sentence longer than ~40 words and propose a split.

Do **not** flag:

- Sentences that are long but legitimately complex (a single dependent clause that earns its length).
- "We" used in conventions.md or in places where the speaker is clearly the audit/skill itself describing its own behavior.
- Hedge words used precisely (e.g., "the audit may be configured to run more often") — these are accurate, not vague.

**Voice is the easiest place for the skill to over-flag and homogenize.** Bias toward under-flagging. When uncertain, do not flag.

#### Altitude

`conventions.md` specifies three altitudes — mission, operational, implementation — and warns: *"Do not collapse altitudes."*

Look for sentences that mix altitudes within a single section:

- A mission-altitude statement ("Kallipolis is a partnership intelligence layer for California community colleges") appearing inside an implementation section discussing how a specific function works.
- An implementation detail ("`partnerships.py` uses brace-depth parsing to stream sections") appearing inside a product or domain section that should stay at operational altitude.
- An operational claim ("the partnerships flow generates a draft narrative") appearing inside a mission overview that should stay at the long-arc framing.

Do **not** flag:

- Brief contextual sentences that legitimately reach across altitudes for orientation (e.g., a product doc briefly mentioning that the feature is implemented via the partnerships flow). One bridging sentence is fine; sustained collapse is not.
- Implementation details in `architecture/` and `pipeline/` docs — those are the right altitude for those sections.

This pass requires real judgment. Bias toward flagging only obvious cases.

#### Spine

`conventions.md` specifies: *"Each section of the documentation has a governing spine — a through-line that makes everything in the section coherent. Spines unify, they do not gatekeep. Their job is to name the principle that ties the section together, not to argue individual features in or out."*

This is the hardest convention to evaluate mechanically. The skill should:

1. Read the doc end to end.
2. State, in one sentence to itself, what it believes the doc's spine is.
3. Walk each section and ask: does this section advance the spine, or is it orthogonal?
4. Flag only sections that feel clearly orthogonal — never individual sentences. Spine findings are about the doc's overall coherence, not its details.

If the skill cannot identify a clear spine for the doc at all, flag this at `quality` — it may indicate the doc itself lacks a through-line, which is one of the few "the doc itself is the problem" findings the skill is allowed to make.

### Phase 6 — Report findings

Output the report in this exact format:

```
Reviewing: <path>
Genre: <narrative|reference>
Audit: <PASS|FAIL>

Findings (<N>):

[<severity>] <category> — <path>:<line>
  "<exact quoted text from the doc>"
  <one-sentence explanation grounded in a specific convention>
  Proposed edit: <minimal, specific revision>
  Apply? [y/n]
```

Each finding must include:

- **Severity tag**: `blocking`, `quality`, or `suggestion`
- **Category**: e.g., `voice drift`, `altitude collapse`, `forbidden marker`, `structural`, `spine`
- **Location**: file path and line number
- **The exact text**, quoted directly from the doc — never a paraphrase
- **A one-sentence rationale** that names the convention being violated
- **A specific proposed edit** that is minimal — change as little as possible to address the finding

Sort findings by severity: `blocking` first, then `quality`, then (if `--threshold=all`) `suggestion`. Within a severity, sort by line number.

If no findings exist at the requested threshold, output:

```
Reviewing: <path>
Genre: <narrative|reference>
Audit: PASS

No findings at threshold <threshold>. The doc is in good shape.
```

### Phase 7 — Apply approved edits

After presenting all findings, wait for the user. The user will respond by approving findings one at a time. For each approval:

1. Re-read the file to confirm the line and the exact quoted text are still present (the doc may have changed between phases).
2. Apply the proposed edit using the Edit tool with the exact quoted text as `old_string` and the proposed edit as `new_string`.
3. Confirm the edit succeeded.
4. Move to the next approved finding.

After all approved edits are applied, run the audit one more time to verify nothing was broken:

```bash
python3 tools/docs-audit/audit.py
```

If the audit now fails when it previously passed, surface this immediately and ask the user how to proceed. Do not silently leave the repo in a broken state.

## Output format

The full skill output for a typical run looks like:

```
Reviewing: docs/product/students.md
Genre: narrative
Audit: PASS

Findings (3):

[blocking] forbidden marker — docs/product/students.md:67
  "This section is *(draft)*."
  Conventions forbid `*(draft)*` markers in committed content.
  Proposed edit: remove "*(draft)*" from this sentence.
  Apply? [y/n]

[quality] voice drift — docs/product/students.md:42
  "We're excited to help colleges partner with employers."
  "We're excited" is marketing voice; conventions specify institutional, declarative, direct.
  Proposed edit: "Kallipolis connects colleges with employers for workforce partnerships."
  Apply? [y/n]

[quality] altitude collapse — docs/product/students.md:89
  "The students flow uses `claude-sonnet-4-6` for narrative generation."
  This is implementation altitude inside an operational section about the students flow.
  Proposed edit: remove this sentence; the implementation detail belongs in architecture/ai-integration.md.
  Apply? [y/n]
```

## Calibration principle

This skill is fundamentally about prose judgment, not deterministic rules. It will sometimes surface findings that feel like noise. When that happens, **the right response is not to accept the noise** — it is to either tighten this `SKILL.md` to suppress that category of finding, or to revise `docs/conventions.md` if the finding reveals that the convention as written produces results the user doesn't actually want.

Bias toward **under-flagging**. A skill that surfaces five real findings and zero false positives is more valuable than one that surfaces ten findings half of which are noise. The user should be able to trust every finding the skill produces.

When in doubt about whether a sentence violates a convention, do not flag it. The cost of a missed finding is small (the convention is broad, the doc is still good); the cost of a false positive is large (the user loses trust in the skill and stops using it).

## Constraints

- **Never auto-apply edits.** Every edit requires explicit user approval. No exceptions.
- **Never modify a doc the user did not name.** The skill operates on exactly one file per invocation.
- **Never modify `docs/conventions.md` itself.** If the skill finds the convention is wrong, surface that to the user — do not silently update the contract.
- **Never homogenize voice.** The user has an authorial voice that conventions describe in outline but do not capture fully. Flag obvious violations; never restyle for stylistic preference.
- **Never run the audit silently if it fails.** Always surface audit state to the user.
- **Never invent a convention.** Every finding must cite a specific rule from `docs/conventions.md`. If the skill wants to flag something not covered by conventions, it must instead suggest that the conventions be extended to cover it.
- **Always quote the exact text.** Findings must include direct quotes from the doc, not paraphrases. The user must be able to verify the skill is reading carefully rather than hallucinating.
- **Always show line numbers.** The user must be able to navigate to the finding immediately.

## Failure modes to avoid

- **Reviewing a code file or a non-doc markdown file.** Refuse politely and ask for a `docs/` path.
- **Mass-flagging based on pattern matching alone.** Voice findings require actual reading; do not regex-grep for "we" and flag every instance.
- **Proposing edits that change meaning.** Edits should preserve the substance and only adjust the form. If the skill cannot propose a meaning-preserving edit, the finding should be reported with `Proposed edit: (manual revision required)` rather than a forced rewrite.
- **Continuing past an audit failure without surfacing it.**
- **Applying multiple edits without per-finding approval.**

## Reference

The contract this skill enforces is `docs/conventions.md`. Read it fresh on every invocation. If `conventions.md` evolves, the skill's behavior evolves with it automatically.

The complementary deterministic verification lives in `tools/docs-audit/`. Together, the audit and this skill cover all of `conventions.md`: the audit covers everything code-grounded, the skill covers everything that requires reading comprehension.
