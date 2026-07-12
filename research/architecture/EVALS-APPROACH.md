# The evals-centric approach

Companion to `ARCHITECTURE-FINDINGS.md` (the evidence) and `PLAN-PROMPT.md` (the plan).
This is the *why* — the conceptual frame the phased refactor is executing against.

## Interpretation

An evals-centric architecture treats **executable statements of what the system must mean**
as the primary, durable artifact, and the implementation as fungible material shaped to keep
them green. You don't test code you happened to write; you write the truths down first and let
the code be whatever satisfies them.

Our system is almost entirely deterministic — a graph plus resolvers — so the LLM sense of
"eval" (grade fuzzy output) doesn't transfer directly. Here an eval is **a truth-condition over
observable behavior that must hold no matter how the internals are arranged.** That last clause
is load-bearing: an eval phrased over the *interface* survives a rewrite of the *guts*, which is
exactly what lets us tear out the duplicated computation without fear.

## Why this system needs it

The bug series — gap values disagreeing across tools (#99), then `colleges_offering` (#103) —
was one *shape* of bug, not three bugs: the same quantity (supply, gap, feeders, roster)
computed in several places over several stores, drifting. Fix one surface, the next surfaces,
because "correct" lives in the developer's head, not the repo. Supply alone is computed three
ways over two stores, asserted-equal in a comment (`canonical.py:9`) and never tested-equal.
Evals-centric converts "correct" from *a property of attention* into *a property of the system*.

## Three tiers (descending durability)

1. **Invariants — relational truths.** "The same coordinate yields the same supply on every
   surface." "A college in a roster must own a Program node." "gap = demand − supply over the
   *same* college-set." They encode *meaning*, not values — invariant under data refresh, each
   killing a whole *class* of bug. The dashboard⇄MCP corroboration invariant is the crown jewel:
   once green, the #99/#103 class cannot recur without turning CI red.
2. **Characterization goldens — behavioral snapshots.** Today's numbers, committed, so any change
   is a reviewable *diff*. They don't claim the numbers are right; they claim *you changed them,
   on purpose*. Freeze today's behavior (incl. today's divergence), move the machinery beneath,
   read exactly what moved. (Feathers' characterization tests.)
3. **Judgments — semantic quality.** For genuinely fuzzy surfaces (does the prose read well).
   LLM-judged, only behind a deterministic pre-gate. Smallest role here — the system is mostly
   deterministic, and we don't reach for LLM judgment where a deterministic check will do.

## The ratchet

Every bug becomes a new invariant (regression → permanent eval). Every refactor is guarded by
goldens. Every new capability must satisfy the standing invariants or *deliberately* re-baseline
them with sign-off. Meaning only accretes; it never silently erodes. This is also what makes
*agentic* evolution tractable: point an agent at "simplify the computation layer" or "add equity
data," and the eval harness is the fitness function — the change is accepted only if the
invariants stay green. Evals are how correctness is delegated safely.

## How this harness realizes it

The abstraction is only as good as its enforcement. Each piece maps to one requirement:

- **Seed graph = a reproducible specimen of reality.** The invariants existed but *skipped* (no
  live DB) — same as not existing. The seed makes the world small, deterministic, committed, and
  (natural-key-keyed, script-regenerated) faithful as the schema evolves. Enabling move:
  aspirational invariants become enforced. Fidelity matters — e.g. seeding `deanza/retail` from
  the *unresolved* full-SOC spec so a live-but-empty coordinate reproduces.
- **CI = the enforcement point.** An eval that isn't a merge gate is a convention, and
  conventions rot. The graph invariants now run on every PR (the docs-audit mechanism's
  computational twin).
- **Goldens from *both* paths = refactor legibility.** Capturing builder AND canonical numbers
  makes the migration diff show precisely what the unification changed, and where the
  stale-CSV-vs-fresh-graph divergence gets corrected we see each correction and sign off.
- **The corroboration invariant = the bug class sealed.** Asserts the relational truth the whole
  series violated. Can't pass until Phase 2's unification — so it is Phase 2's acceptance test,
  not a Phase-1 gate.
- **One `make evals` gate = a single meaning of "still correct."** Not "ran tests / checked
  snapshots / eyeballed numbers," but one composite answer to "does the system still mean what it
  meant."

## The payoff

We get to do the risky thing — collapse the duplicated computation into one authoritative layer —
*without holding the whole system in our heads*, because the invariants hold the meaning while we
move the machinery. Evals-first is both the method (lock, then refactor beneath) and the goal (a
standing spec that lets the ontology keep evolving, by humans or agents, without regressing what
it already gets right).
