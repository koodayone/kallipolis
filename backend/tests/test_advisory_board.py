"""Test harness for advisory board proposal quality.

Tests structural requirements (department count, occupation count, field presence)
and narrative quality standards (natural prose, non-prescriptive posture,
foundational department scope, agenda topic grounding).

Usage:
    cd backend
    NEO4J_URI=bolt://localhost:7687 NEO4J_USERNAME=neo4j NEO4J_PASSWORD=kallipolis_dev \
    ANTHROPIC_API_KEY=... python tests/test_advisory_board.py
"""

from __future__ import annotations
import os
import sys
import re
import time
import json
import logging

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(message)s")

from workflows.partnerships import (
    _gather_targeted_context, _run_pipeline,
)

COLLEGE = "College of the Sequoias"

# Prescriptive language patterns to flag
PRESCRIPTIVE_PATTERNS = [
    r"\bshould address\b",
    r"\bshould open with\b",
    r"\bmust implement\b",
    r"\bneed to\b",
    r"\bshould focus on\b",
    r"\bshould align\b",
    r"\bshould embed\b",
    r"\bshould incorporate\b",
]

# Skill names that should NOT be capitalized (unless start of sentence)
SKILL_LABEL_PATTERNS = [
    r"(?<!^)(?<!\. )Food Safety",
    r"(?<!^)(?<!\. )Quality Control",
    r"(?<!^)(?<!\. )Operations Management",
    r"(?<!^)(?<!\. )Regulatory Compliance",
    r"(?<!^)(?<!\. )Laboratory Techniques",
    r"(?<!^)(?<!\. )Patient Assessment",
    r"(?<!^)(?<!\. )Clinical Documentation",
    r"(?<!^)(?<!\. )Nursing Process",
]

# Legitimate acronyms that SHOULD be capitalized
ACRONYMS = ["HVAC", "HACCP", "EPA", "OSHA", "EHR", "BLS", "USDA", "FDA"]

# Foundational departments — flag if narrative assertively recommends changes to these
FOUNDATIONAL_DEPTS = ["biology", "chemistry", "mathematics", "physics", "statistics"]

# Generic occupations that should not dominate selection
GENERIC_OCCUPATIONS = [
    "General and Operations Managers",
    "Office Clerks",
    "Administrative Services Managers",
    "Receptionists",
    "Secretaries",
]

TEST_CASES = [
    {
        "employer": "Cargill",
        "sector": "Manufacturing",
        "expect_occ_contains": ["Food|Agri|Industrial"],
        "expect_dept_contains": ["Agri|Culinary|Industrial"],
    },
    {
        "employer": "Adventist Health Hanford",
        "sector": "Healthcare",
        "expect_occ_contains": ["Nurs|Pharm|Radiol|Health"],
        "expect_dept_contains": ["Nurs|Pharm|Emergency|Health"],
    },
    {
        "employer": "Fresno Plumbing and Heating",
        "sector": "Construction",
        "expect_occ_contains": ["Heat|Plumb|Construct"],
        "expect_dept_contains": ["Environmental|Construction|Electric"],
    },
    {
        "employer": "Foster Farms",
        "sector": "Agriculture",
        "expect_occ_contains": ["Food|Agri|Industrial"],
        "expect_dept_contains": ["Agri|Animal|Industrial"],
    },
    {
        "employer": "Home Depot",
        "sector": "Retail",
        "expect_occ_contains": ["Sales|Retail|Manager|Logist"],
        "expect_dept_contains": ["Bus|Work Experience"],
    },
]


def _check_prescriptive(text: str) -> list[str]:
    """Find prescriptive language patterns in text."""
    violations = []
    for pattern in PRESCRIPTIVE_PATTERNS:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            violations.append(f"prescriptive: '{matches[0]}'")
    return violations


def _check_capitalized_skills(text: str) -> list[str]:
    """Find skill names used as capitalized labels (not natural prose)."""
    violations = []
    for pattern in SKILL_LABEL_PATTERNS:
        matches = re.findall(pattern, text)
        if matches:
            violations.append(f"capitalized skill label: '{matches[0]}'")
    return violations


def _check_acronyms_lowercase(text: str) -> list[str]:
    """Find legitimate acronyms that were incorrectly lowercased."""
    violations = []
    for acr in ACRONYMS:
        lower = acr.lower()
        # Look for the lowercase version that isn't part of a larger word
        if re.search(rf"\b{lower}\b", text):
            violations.append(f"lowercase acronym: '{lower}' should be '{acr}'")
    return violations


def _check_foundational_assertive(text: str) -> list[str]:
    """Flag assertive recommendations about foundational departments."""
    violations = []
    assertive_patterns = [
        r"(should|must|need to).{0,40}(biology|chemistry|mathematics|physics)",
        r"(align|update|change|modify).{0,30}(biology|chemistry|mathematics|physics).{0,20}(lab|course|curriculum)",
    ]
    for pattern in assertive_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            violations.append(f"assertive foundational dept recommendation: {matches[0]}")
    return violations


def _check_skill_as_curriculum(text: str) -> list[str]:
    """Flag skill names used as standalone curricula."""
    violations = []
    patterns = [
        r"Operations Management.{0,10}curriculum",
        r"Quality Control.{0,10}curriculum",
        r"Food Safety.{0,10}curriculum",
        r"Regulatory Compliance.{0,10}curriculum",
    ]
    for pattern in patterns:
        if re.search(pattern, text, re.IGNORECASE):
            violations.append(f"skill-as-curriculum: matched '{pattern}'")
    return violations


def run_tests():
    results = []

    for tc in TEST_CASES:
        employer = tc["employer"]
        print(f"Testing: {employer} ({tc['sector']})...", file=sys.stderr, flush=True)

        t0 = time.time()
        try:
            gathered = _gather_targeted_context(employer, COLLEGE, "advisory_board")
            proposal = _run_pipeline(employer, COLLEGE, "advisory_board", gathered)
            elapsed = round(time.time() - t0, 1)

            checks = []
            violations = []

            # ── Structural checks ──

            # 2-4 selected occupations
            occ_count = len(proposal.selected_occupations)
            if 2 <= occ_count <= 4:
                checks.append(("occ_count", "PASS", f"{occ_count} occupations"))
            else:
                checks.append(("occ_count", "FAIL", f"{occ_count} occupations (expected 2-4)"))

            # No generic occupations dominating
            generic_selected = [o for o in proposal.selected_occupations if o in GENERIC_OCCUPATIONS]
            if len(generic_selected) <= 1:
                checks.append(("occ_identity", "PASS", f"{len(generic_selected)} generic"))
            else:
                checks.append(("occ_identity", "FAIL", f"too many generic: {generic_selected}"))

            # Expected occupations present
            for pattern in tc.get("expect_occ_contains", []):
                found = any(
                    any(t.strip().lower() in o.lower() for t in pattern.split("|"))
                    for o in proposal.selected_occupations
                )
                if found:
                    checks.append(("occ_expected", "PASS", f"found '{pattern}'"))
                else:
                    checks.append(("occ_expected", "FAIL", f"missing '{pattern}' in {proposal.selected_occupations}"))

            # Thesis non-empty
            if proposal.advisory_thesis:
                checks.append(("thesis", "PASS", f"{len(proposal.advisory_thesis)} chars"))
            else:
                checks.append(("thesis", "FAIL", "empty thesis"))

            # 2-3 agenda topics
            topic_count = len(proposal.agenda_topics)
            if 2 <= topic_count <= 3:
                checks.append(("agenda_count", "PASS", f"{topic_count} topics"))
            else:
                checks.append(("agenda_count", "FAIL", f"{topic_count} topics (expected 2-3)"))

            # Department count <= 7
            dept_count = len(proposal.justification.curriculum_evidence)
            if dept_count <= 7:
                checks.append(("dept_count", "PASS", f"{dept_count} departments"))
            else:
                checks.append(("dept_count", "FAIL", f"{dept_count} departments (max 7)"))

            # Expected departments present
            dept_names = [d.department for d in proposal.justification.curriculum_evidence]
            for pattern in tc.get("expect_dept_contains", []):
                found = any(
                    any(t.strip().lower() in d.lower() for t in pattern.split("|"))
                    for d in dept_names
                )
                if found:
                    checks.append(("dept_expected", "PASS", f"found '{pattern}'"))
                else:
                    checks.append(("dept_expected", "FAIL", f"missing '{pattern}' in {dept_names}"))

            # ── Narrative quality checks ──

            narrative_text = (
                f"{proposal.opportunity} "
                f"{proposal.justification.curriculum_composition} "
                f"{proposal.justification.student_composition} "
                f"{proposal.roadmap}"
            )

            # Prescriptive language
            prescriptive = _check_prescriptive(narrative_text)
            if not prescriptive:
                checks.append(("prescriptive", "PASS", "no prescriptive language"))
            else:
                checks.append(("prescriptive", "WARN", "; ".join(prescriptive)))

            # Capitalized skill labels
            cap_skills = _check_capitalized_skills(narrative_text)
            if not cap_skills:
                checks.append(("natural_prose", "PASS", "skills woven naturally"))
            else:
                checks.append(("natural_prose", "WARN", "; ".join(cap_skills[:3])))

            # Acronym capitalization
            acr_issues = _check_acronyms_lowercase(narrative_text)
            if not acr_issues:
                checks.append(("acronyms", "PASS", "acronyms properly capitalized"))
            else:
                checks.append(("acronyms", "WARN", "; ".join(acr_issues)))

            # Foundational department assertiveness
            foundational = _check_foundational_assertive(narrative_text)
            if not foundational:
                checks.append(("foundational_scope", "PASS", "no assertive gen-ed recommendations"))
            else:
                checks.append(("foundational_scope", "WARN", "; ".join(foundational)))

            # Agenda topic rationale grounding
            agenda_text = " ".join(t.rationale for t in proposal.agenda_topics)
            skill_as_curr = _check_skill_as_curriculum(agenda_text)
            if not skill_as_curr:
                checks.append(("agenda_grounding", "PASS", "rationales reference programs"))
            else:
                checks.append(("agenda_grounding", "WARN", "; ".join(skill_as_curr)))

            # Agenda topic prescriptive check
            agenda_topic_text = " ".join(f"{t.topic} {t.rationale}" for t in proposal.agenda_topics)
            agenda_prescriptive = _check_prescriptive(agenda_topic_text)
            foundational_agenda = _check_foundational_assertive(agenda_topic_text)
            if not agenda_prescriptive and not foundational_agenda:
                checks.append(("agenda_tone", "PASS", "agenda tone appropriate"))
            else:
                issues = agenda_prescriptive + foundational_agenda
                checks.append(("agenda_tone", "WARN", "; ".join(issues[:3])))

            results.append({
                "employer": employer,
                "sector": tc["sector"],
                "checks": checks,
                "occupations": proposal.selected_occupations,
                "thesis": proposal.advisory_thesis,
                "departments": dept_names,
                "topics": [t.topic for t in proposal.agenda_topics],
                "elapsed": elapsed,
            })

        except Exception as e:
            import traceback
            traceback.print_exc(file=sys.stderr)
            results.append({
                "employer": employer,
                "sector": tc["sector"],
                "checks": [("pipeline", "ERROR", str(e))],
                "occupations": [],
                "thesis": "",
                "departments": [],
                "topics": [],
                "elapsed": round(time.time() - t0, 1),
            })

    # ── Print results ──

    print(f"\n{'='*90}")
    print("ADVISORY BOARD PROPOSAL TEST RESULTS")
    print(f"{'='*90}")

    total_pass = 0
    total_warn = 0
    total_fail = 0
    total_error = 0

    for r in results:
        print(f"\n  {r['employer']} ({r['sector']}) — {r['elapsed']}s")
        print(f"  Occupations: {r['occupations']}")
        print(f"  Departments: {r['departments']}")
        if r["thesis"]:
            thesis_preview = r["thesis"][:120] + "..." if len(r["thesis"]) > 120 else r["thesis"]
            print(f"  Thesis: {thesis_preview}")
        for topic in r["topics"]:
            topic_preview = topic[:100] + "..." if len(topic) > 100 else topic
            print(f"  Agenda: {topic_preview}")
        print()

        for check_name, status, detail in r["checks"]:
            icon = {"PASS": "✓", "FAIL": "✗", "WARN": "⚠", "ERROR": "✗"}.get(status, "?")
            print(f"    {icon} {check_name:<22} {status:<5} {detail}")
            if status == "PASS":
                total_pass += 1
            elif status == "WARN":
                total_warn += 1
            elif status == "FAIL":
                total_fail += 1
            else:
                total_error += 1

    print(f"\n{'='*90}")
    print(f"SUMMARY: {total_pass} passed, {total_warn} warnings, {total_fail} failed, {total_error} errors")
    print(f"{'='*90}")


if __name__ == "__main__":
    run_tests()
