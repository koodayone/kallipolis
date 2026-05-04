"""Eval suite for the 12 proposed example queries across all colleges.

Runs each example question against every college in the graph and checks:
  1. Cypher generation succeeds (no CANNOT_TRANSLATE, no crash)
  2. Cypher passes validation (read-only, college-scoped)
  3. Semantic correctness — generated Cypher contains required patterns
     (WHERE clauses, ORDER BY, base traversal) specific to each question
  4. Execution returns at least one result
  5. Response interpretation is non-empty

Usage:
    # Run full eval (all colleges × all questions):
    python -m tests.integration.test_example_queries

    # Run for a single college:
    python -m tests.integration.test_example_queries --college "Foothill College"

    # Run a single question category:
    python -m tests.integration.test_example_queries --category employers

    # Dry run (generate + validate + pattern check, no execution):
    python -m tests.integration.test_example_queries --dry-run

    # Run N trials per question to test consistency:
    python -m tests.integration.test_example_queries --college "Foothill College" --trials 3

Results are written to tests/integration/eval_results.json with per-cell
pass/fail, generated Cypher, and pattern match details for debugging.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import re
import sys
import time
from dataclasses import dataclass, asdict, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from llm.query_engine import generate_query, validate_cypher, execute_query
from ontology.schema import get_driver
from students.query import STUDENT_QUERY_PROMPT
from courses.query import COURSE_QUERY_PROMPT
from employers.query import EMPLOYER_QUERY_PROMPT
from occupations.query import OCCUPATION_QUERY_PROMPT

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)


# ── Cypher pattern assertions ────────────────────────────────────────
#
# Each question has a list of (label, pattern) tuples. The pattern is
# checked case-insensitively against the generated Cypher. Every pattern
# must match for the question to pass semantic correctness.
#
# Patterns verify:
#   - Base traversal is present (correct relationship chain)
#   - Correct WHERE clause for the question's intent
#   - Correct ORDER BY when the question implies a sort
#   - Required return columns are present

def _patterns(
    base: list[tuple[str, str]],
    extra: list[tuple[str, str]] | None = None,
) -> list[tuple[str, str]]:
    return base + (extra or [])


# ── Base traversals (the non-negotiable MATCH chain per feature) ─────

EMPLOYER_BASE = [
    ("employer base traversal",
     r"college.*in_market.*region.*in_market.*employer.*hires_for.*occupation.*prepares_for.*course"),
    ("returns emp.name", r"emp\.name\s+as\s+name"),
    ("returns aligned_course_count", r"aligned_course_count"),
    ("college scoped", r"\$college"),
]

OCCUPATION_BASE = [
    ("occupation base traversal",
     r"college.*in_market.*region.*demands.*occupation.*prepares_for.*course"),
    ("returns soc_code", r"soc_code"),
    ("returns annual_wage", r"annual_wage"),
    ("college scoped", r"\$college"),
]

COURSE_BASE = [
    ("course college scope", r"course\s*\{.*college:\s*\$college"),
    ("returns c.name", r"c\.name\s+as\s+name"),
    ("returns c.code", r"c\.code\s+as\s+code"),
    ("college scoped", r"\$college"),
]

STUDENT_BASE = [
    # Anchor accepts either parameterized ($college) or literal ('Foothill College')
    # college scoping in the ENROLLED_IN base.
    ("student anchor pattern",
     r"student.*enrolled_in.*course.*(\$college|college:\s*')"),
    ("returns uuid", r"s\.uuid\s+as\s+uuid"),
    ("returns gpa", r"s\.gpa\s+as\s+gpa"),
    ("college scoped", r"(\$college|college:\s*')"),
]


# ── Per-question pattern definitions ─────────────────────────────────

QUERY_SPECS: dict[str, tuple[str, list[tuple[str, str]]]] = {
    # ── Employers ──
    "Employers with the strongest curriculum alignment": (
        EMPLOYER_QUERY_PROMPT,
        _patterns(EMPLOYER_BASE, [
            ("sorts by aligned_course_count",
             r"order\s+by\s+aligned_course_count\s+desc"),
        ]),
    ),
    "Employers in regional priority sectors": (
        EMPLOYER_QUERY_PROMPT,
        _patterns(EMPLOYER_BASE, [
            ("filters on priority_sectors via swp_sectors intersection",
             r"swp_sectors.*priority_sectors|priority_sectors.*swp_sectors"),
        ]),
    ),

    # ── Occupations ──
    "Occupations with the highest wages": (
        OCCUPATION_QUERY_PROMPT,
        _patterns(OCCUPATION_BASE, [
            ("sorts by annual_wage",
             r"order\s+by\s+d\.annual_wage\s+desc"),
        ]),
    ),
    "Occupations with the most yearly openings": (
        OCCUPATION_QUERY_PROMPT,
        _patterns(OCCUPATION_BASE, [
            ("sorts by annual_openings",
             r"order\s+by\s+d\.annual_openings\s+desc"),
        ]),
    ),
    "Occupations growing fastest in our region": (
        OCCUPATION_QUERY_PROMPT,
        _patterns(OCCUPATION_BASE, [
            ("sorts by growth_rate",
             r"order\s+by\s+d\.growth_rate\s+desc"),
        ]),
    ),

    # ── Courses ──
    "Courses that prepare for nursing occupations": (
        COURSE_QUERY_PROMPT,
        _patterns(COURSE_BASE, [
            ("traverses PREPARES_FOR->Occupation",
             r"prepares_for.*occupation"),
            ("filters on nursing occupation title",
             r"tolower\(occ\.title\)\s+contains\s+'nurs"),
        ]),
    ),
    "Courses relevant to career and technical education": (
        COURSE_QUERY_PROMPT,
        _patterns(COURSE_BASE, [
            ("filters on is_cte = true",
             r"c\.is_cte\s*=\s*true"),
        ]),
    ),
    "Manufacturing department courses with no prerequisites": (
        COURSE_QUERY_PROMPT,
        _patterns(COURSE_BASE, [
            ("filters on manufacturing department",
             r"tolower\(c\.department\)\s+contains\s+'manufactur"),
            ("filters on no prerequisites",
             r"prerequisites\s+is\s+null|prerequisites\s*=\s*''"),
        ]),
    ),

    # ── Students ──
    "Students specializing in 'construction technology'": (
        STUDENT_QUERY_PROMPT,
        _patterns(STUDENT_BASE, [
            # Pattern accepts any primary_focus filter — the rendered
            # question is per-college-overridden (PER_COLLEGE_OVERRIDES)
            # to ensure each school has a concrete program with student
            # population.
            ("filters on primary_focus",
             r"tolower\(s\.primary_focus\).*contains"),
        ]),
    ),
    "Honor-roll Engineering students who took Calculus": (
        STUDENT_QUERY_PROMPT,
        _patterns(STUDENT_BASE, [
            ("filters on engineering primary_focus",
             r"tolower\(s\.primary_focus\)\s+contains\s+'engineer"),
            ("GPA threshold >= 3.5",
             r"s\.gpa\s*>=\s*3\.5"),
            ("filters on calculus by name or code",
             r"calculus|math 1"),
        ]),
    ),
    "Students prepared for healthcare occupations": (
        STUDENT_QUERY_PROMPT,
        _patterns(STUDENT_BASE, [
            ("uses health filter (occupation title or focus)",
             r"(tolower\(occ\.title\).*contains\s+'(health|medical|nurs)|tolower\(s\.primary_focus\).*contains\s+'health)"),
        ]),
    ),
}


@dataclass
class PatternResult:
    label: str
    pattern: str
    matched: bool


@dataclass
class EvalResult:
    college: str
    category: str
    question: str
    trial: int
    cypher_generated: bool
    cypher_valid: bool
    patterns_passed: int
    patterns_total: int
    pattern_details: list[dict] = field(default_factory=list)
    execution_success: bool = False
    result_count: int = 0
    has_interpretation: bool = False
    cypher: str = ""
    interpretation: str = ""
    error: str = ""
    latency_ms: int = 0

    @property
    def semantically_correct(self) -> bool:
        return self.patterns_passed == self.patterns_total


CATEGORIES = {
    "employers": [
        "Employers with the strongest curriculum alignment",
        "Employers in regional priority sectors",
    ],
    "occupations": [
        "Occupations with the highest wages",
        "Occupations with the most yearly openings",
        "Occupations growing fastest in our region",
    ],
    "courses": [
        "Courses that prepare for nursing occupations",
        "Courses relevant to career and technical education",
        "Manufacturing department courses with no prerequisites",
    ],
    "students": [
        "Students specializing in 'construction technology'",
        "Honor-roll Engineering students who took Calculus",
        "Students prepared for healthcare occupations",
    ],
}


PROMPT_TO_VIEW = {
    id(EMPLOYER_QUERY_PROMPT): "employer",
    id(OCCUPATION_QUERY_PROMPT): "occupation",
    id(COURSE_QUERY_PROMPT): "course",
    id(STUDENT_QUERY_PROMPT): "student",
}


# Per-college rendering for parameterized example questions. The eval keys
# results by the canonical question (so per-question reporting aggregates
# correctly), but the LLM is asked the school-appropriate variant.
#
# For "Students specializing in X", X is each school's most-populous CTE-
# flavored primary_focus among students who took at least one CTE course.
# Values curated from a one-time graph query; they should be re-curated
# whenever the synthetic-student generation methodology changes the
# primary_focus distribution.
PER_COLLEGE_OVERRIDES: dict[tuple[str, str], str] = {
    ("Students specializing in 'construction technology'", "Shasta College"):
        "Students specializing in 'early childhood education'",
    ("Students specializing in 'construction technology'", "Foothill College"):
        "Students specializing in 'accounting'",
    ("Students specializing in 'construction technology'", "College of the Sequoias"):
        "Students specializing in 'child development'",
    ("Students specializing in 'construction technology'", "Oxnard College"):
        "Students specializing in 'fire technology'",
    ("Students specializing in 'construction technology'", "Compton College"):
        "Students specializing in 'nursing'",
    ("Students specializing in 'construction technology'", "Irvine Valley College"):
        "Students specializing in 'accounting'",
    ("Students specializing in 'construction technology'", "College of the Desert"):
        "Students specializing in 'health sciences'",
    ("Students specializing in 'construction technology'", "San Diego City College"):
        "Students specializing in 'cybersecurity and data analytics'",
}


def render_question(question: str, college: str) -> str:
    """Apply per-college override if one is registered, else return as-is."""
    return PER_COLLEGE_OVERRIDES.get((question, college), question)


def get_all_colleges() -> list[str]:
    driver = get_driver()
    with driver.session() as session:
        records = session.run(
            "MATCH (c:College) RETURN c.name AS name ORDER BY name"
        ).data()
    return [r["name"] for r in records]


def check_patterns(cypher: str, patterns: list[tuple[str, str]]) -> list[PatternResult]:
    lower = cypher.lower()
    normalized = re.sub(r"\s+", " ", lower)
    results = []
    for label, pattern in patterns:
        matched = bool(re.search(pattern, normalized, re.IGNORECASE))
        results.append(PatternResult(label=label, pattern=pattern, matched=matched))
    return results


def run_single_eval(
    question: str, college: str, category: str, trial: int, dry_run: bool = False
) -> EvalResult:
    prompt, patterns = QUERY_SPECS[question]

    result = EvalResult(
        college=college,
        category=category,
        question=question,
        trial=trial,
        cypher_generated=False,
        cypher_valid=False,
        patterns_passed=0,
        patterns_total=len(patterns),
    )

    t0 = time.time()

    try:
        view = PROMPT_TO_VIEW.get(id(prompt), "")
        rendered = render_question(question, college)
        cypher, interpretation = generate_query(rendered, college, prompt, view=view)
        result.cypher = cypher
        result.interpretation = interpretation
        result.cypher_generated = True
        result.has_interpretation = bool(interpretation and interpretation.strip())
    except Exception as e:
        result.error = f"generation: {e}"
        result.latency_ms = int((time.time() - t0) * 1000)
        return result

    try:
        validated = validate_cypher(cypher)
        result.cypher = validated
        result.cypher_valid = True
    except ValueError as e:
        result.error = f"validation: {e}"
        result.latency_ms = int((time.time() - t0) * 1000)
        return result

    pattern_results = check_patterns(validated, patterns)
    result.patterns_passed = sum(1 for p in pattern_results if p.matched)
    result.pattern_details = [asdict(p) for p in pattern_results]

    if not result.semantically_correct:
        failed = [p for p in pattern_results if not p.matched]
        result.error = f"pattern: {', '.join(p.label for p in failed)}"

    if dry_run:
        result.latency_ms = int((time.time() - t0) * 1000)
        return result

    try:
        records = execute_query(validated, college)
        result.execution_success = True
        result.result_count = len(records)
    except Exception as e:
        if not result.error:
            result.error = f"execution: {e}"

    result.latency_ms = int((time.time() - t0) * 1000)
    return result


def print_summary(results: list[EvalResult], dry_run: bool = False) -> None:
    total = len(results)
    generated = sum(1 for r in results if r.cypher_generated)
    valid = sum(1 for r in results if r.cypher_valid)
    semantic = sum(1 for r in results if r.semantically_correct)
    executed = sum(1 for r in results if r.execution_success)
    has_results = sum(1 for r in results if r.result_count > 0)
    has_interp = sum(1 for r in results if r.has_interpretation)

    print(f"\n{'=' * 72}")
    print(f"EVAL SUMMARY — {total} evaluations")
    print(f"{'=' * 72}")
    print(f"  Cypher generated:      {generated:>4}/{total} ({generated/total*100:.0f}%)")
    print(f"  Cypher valid:          {valid:>4}/{total} ({valid/total*100:.0f}%)")
    print(f"  Semantically correct:  {semantic:>4}/{total} ({semantic/total*100:.0f}%)")
    if not dry_run:
        print(f"  Execution success:     {executed:>4}/{total} ({executed/total*100:.0f}%)")
        print(f"  Returned results:      {has_results:>4}/{total} ({has_results/total*100:.0f}%)")
    print(f"  Has interpretation:    {has_interp:>4}/{total} ({has_interp/total*100:.0f}%)")

    # Per-question breakdown
    questions = list(dict.fromkeys(r.question for r in results))
    print(f"\n{'─' * 72}")
    print("PER-QUESTION BREAKDOWN")
    print(f"{'─' * 72}")
    for q in questions:
        q_results = [r for r in results if r.question == q]
        q_total = len(q_results)
        q_semantic = sum(1 for r in q_results if r.semantically_correct)
        q_results_ok = sum(1 for r in q_results if r.result_count > 0)
        q_fail = sum(1 for r in q_results if r.error)
        q_empty = sum(1 for r in q_results if r.execution_success and r.result_count == 0)

        if q_semantic == q_total and (dry_run or q_results_ok == q_total):
            status = "PASS"
        elif q_semantic > 0:
            status = "WARN"
        else:
            status = "FAIL"

        print(f"  [{status}] {q}")
        sem_pct = q_semantic / q_total * 100
        if dry_run:
            print(f"         semantic: {q_semantic}/{q_total} ({sem_pct:.0f}%)")
        else:
            print(f"         semantic: {q_semantic}/{q_total} ({sem_pct:.0f}%), "
                  f"results: {q_results_ok}/{q_total}, empty: {q_empty}, errors: {q_fail}")

    # Pattern failures
    pattern_failures = [r for r in results if r.cypher_valid and not r.semantically_correct]
    if pattern_failures:
        print(f"\n{'─' * 72}")
        print(f"PATTERN FAILURES ({len(pattern_failures)})")
        print(f"{'─' * 72}")
        for r in pattern_failures:
            failed = [p for p in r.pattern_details if not p["matched"]]
            print(f"  {r.college} | {r.question}")
            for p in failed:
                print(f"    MISSING: {p['label']}")
            print(f"    Cypher: {r.cypher[:150]}")
            print()

    # Hard failures (generation or validation errors)
    hard_failures = [r for r in results if not r.cypher_valid]
    if hard_failures:
        print(f"\n{'─' * 72}")
        print(f"HARD FAILURES ({len(hard_failures)})")
        print(f"{'─' * 72}")
        for r in hard_failures:
            print(f"  {r.college} | {r.question}")
            print(f"    Error: {r.error}")
            print()

    # Empty results
    if not dry_run:
        empties = [r for r in results if r.execution_success and r.result_count == 0]
        if empties:
            print(f"\n{'─' * 72}")
            print(f"EMPTY RESULTS ({len(empties)})")
            print(f"{'─' * 72}")
            for r in empties:
                print(f"  {r.college} | {r.question}")


def main():
    parser = argparse.ArgumentParser(description="Eval suite for example NL queries")
    parser.add_argument("--college", help="Run for a single college only")
    parser.add_argument("--category", choices=CATEGORIES.keys(), help="Run a single category")
    parser.add_argument("--dry-run", action="store_true", help="Generate + validate + pattern check, skip execution")
    parser.add_argument("--trials", type=int, default=1, help="Number of trials per question (tests consistency)")
    args = parser.parse_args()

    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("ERROR: ANTHROPIC_API_KEY not set")
        sys.exit(1)

    if args.college:
        colleges = [args.college]
    else:
        colleges = get_all_colleges()

    categories = [args.category] if args.category else list(CATEGORIES.keys())
    questions = [q for cat in categories for q in CATEGORIES[cat]]

    total_evals = len(questions) * len(colleges) * args.trials
    print(f"Running {total_evals} evals "
          f"({len(colleges)} colleges × {len(questions)} questions"
          f"{f' × {args.trials} trials' if args.trials > 1 else ''})")
    if args.dry_run:
        print("(dry run — no execution)")
    print()

    results: list[EvalResult] = []
    completed = 0

    for question in questions:
        cat = next(c for c, qs in CATEGORIES.items() if question in qs)
        for college in colleges:
            for trial in range(args.trials):
                completed += 1
                tag = f"[{completed}/{total_evals}]"
                trial_str = f" t{trial+1}" if args.trials > 1 else ""
                print(f"  {tag} {cat}: {college}{trial_str} — {question[:45]}...",
                      end="", flush=True)

                r = run_single_eval(question, college, cat, trial + 1, dry_run=args.dry_run)
                results.append(r)

                if not r.cypher_valid:
                    print(f" FAIL ({r.error[:40]})")
                elif not r.semantically_correct:
                    print(f" PATTERN ({r.error[:40]})")
                elif r.result_count == 0 and not args.dry_run:
                    print(f" EMPTY ({r.latency_ms}ms)")
                else:
                    extra = f"{r.result_count} results, " if not args.dry_run else ""
                    pct = r.patterns_passed / r.patterns_total * 100
                    print(f" OK ({extra}{pct:.0f}% patterns, {r.latency_ms}ms)")

    print_summary(results, dry_run=args.dry_run)

    out_path = Path(__file__).parent / "eval_results.json"
    with open(out_path, "w") as f:
        json.dump([asdict(r) for r in results], f, indent=2)
    print(f"\nDetailed results written to {out_path}")


if __name__ == "__main__":
    main()
