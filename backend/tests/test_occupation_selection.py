"""Test harness for occupation selection reliability.

Tests that the LLM consistently picks the right primary occupation
and sensible core skills for diverse employers across sectors.

Usage:
    cd backend
    NEO4J_URI=bolt://localhost:7687 NEO4J_USERNAME=neo4j NEO4J_PASSWORD=kallipolis_dev \
    ANTHROPIC_API_KEY=... python tests/test_occupation_selection.py
"""

from __future__ import annotations
import os
import sys
import time
import json
import logging

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(message)s")

from workflows.partnerships import _gather_targeted_context, _select_occupation
from ontology.schema import get_driver

COLLEGE = "College of the Sequoias"

# Test cases: (employer, expected_occupation_substring, unacceptable_occupations)
# The expected substring should match the occupation title we'd want selected.
# Unacceptable occupations are generic roles that should NOT be selected.
TEST_CASES = [
    # Trades / Specific
    {
        "employer": "Fresno Plumbing and Heating",
        "expect_contains": "Heating",  # HVAC Mechanics
        "reject": ["Accountants", "General and Operations", "Administrative"],
        "sector": "Construction",
    },
    # Agriculture - Poultry Processor
    {
        "employer": "Foster Farms",
        "expect_contains": "Agri|Food",  # Agricultural Technicians or Food Scientists
        "reject": ["Accountants", "General and Operations", "Human Resources"],
        "sector": "Agriculture",
    },
    # Food Manufacturing
    {
        "employer": "Cargill",
        "expect_contains": "Food",  # Food Science Technicians or Food Scientists
        "reject": ["Accountants", "Marketing", "Human Resources"],
        "sector": "Manufacturing",
    },
    # Healthcare
    {
        "employer": "Adventist Health Hanford",
        "expect_contains": "Nurs",  # Nursing Assistants, LVNs, or RNs
        "reject": ["Accountants", "Administrative", "Human Resources"],
        "sector": "Healthcare",
    },
    # Healthcare - Hospital
    {
        "employer": "Community Medical Center",
        "expect_contains": "Nurs",  # Nursing
        "reject": ["Accountants", "Administrative", "Human Resources"],
        "sector": "Professional Services",
    },
    # Education
    {
        "employer": "Clovis Adult Education",
        "expect_contains": "Teach|Instruct",  # Teachers or Instructors
        "reject": ["Accountants", "Administrative", "Human Resources"],
        "sector": "Education",
    },
    # Construction
    {
        "employer": "Central California Builders and Development",
        "expect_contains": "Civil|Construction",  # Civil Engineers or Construction Managers
        "reject": ["Accountants", "Human Resources", "General and Operations"],
        "sector": "Construction",
    },
    # Government - Prison (nurses, correctional officers, or probation — all valid)
    {
        "employer": "California State Prison, Corcoran",
        "expect_contains": "Nurs|Correct|Probation",
        "reject": ["Accountants", "Administrative", "General and Operations"],
        "sector": "Government",
    },
    # Food Manufacturing - Meat (safety is central to meat processing)
    {
        "employer": "Central Valley Meat Company",
        "expect_contains": "Food|Safety",  # Food Scientists or Safety Specialists
        "reject": ["Accountants", "Human Resources", "General and Operations"],
        "sector": "Manufacturing",
    },
    # Retail - Home Improvement
    {
        "employer": "Home Depot",
        "expect_contains": "Sales",  # Sales Representatives
        "reject": ["Accountants", "Human Resources"],
        "sector": "Retail",
    },
    # Distribution
    {
        "employer": "ULTA Beauty Distribution Center",
        "expect_contains": "Logist",  # Logisticians
        "reject": ["Accountants", "Human Resources", "Administrative"],
        "sector": "Professional Services",
    },
    # Agriculture - Farm
    {
        "employer": "Mike Jensen Farms",
        "expect_contains": "Agri",  # Agricultural Technicians/Inspectors
        "reject": ["Accountants", "General and Operations"],
        "sector": "Agriculture",
    },
]


def run_tests():
    results = []

    for tc in TEST_CASES:
        employer = tc["employer"]
        print(f"Testing: {employer} ({tc['sector']})...", file=sys.stderr, flush=True)

        t0 = time.time()
        try:
            gathered = _gather_targeted_context(employer, COLLEGE)
            selected = _select_occupation(gathered)
            elapsed = round(time.time() - t0, 1)

            title = selected.get("title", "")
            core_skills = selected.get("core_skills", [])
            soc_code = selected.get("soc_code", "")

            # Check expected (supports | for OR matching)
            expect_pass = any(
                term.strip().lower() in title.lower()
                for term in tc["expect_contains"].split("|")
            )

            # Check rejects
            rejected = False
            rejected_by = ""
            for reject in tc["reject"]:
                if reject.lower() in title.lower():
                    rejected = True
                    rejected_by = reject
                    break

            # Check core skills exist in graph
            skills_exist = True
            missing_skills = []
            if core_skills:
                drv = get_driver()
                with drv.session() as sess:
                    for skill in core_skills:
                        r = sess.run("MATCH (sk:Skill {name: $name}) RETURN sk", name=skill).single()
                        if not r:
                            skills_exist = False
                            missing_skills.append(skill)

            passed = expect_pass and not rejected and skills_exist
            status = "PASS" if passed else "FAIL"

            reason = ""
            if not expect_pass:
                reason = f"expected '{tc['expect_contains']}' in title"
            if rejected:
                reason = f"selected rejected occupation (contains '{rejected_by}')"
            if not skills_exist:
                reason = f"core skills not in graph: {', '.join(missing_skills)}"

            results.append({
                "employer": employer,
                "sector": tc["sector"],
                "selected": title,
                "soc_code": soc_code,
                "core_skills": core_skills,
                "status": status,
                "reason": reason,
                "elapsed": elapsed,
            })

        except Exception as e:
            results.append({
                "employer": employer,
                "sector": tc["sector"],
                "selected": "",
                "soc_code": "",
                "core_skills": [],
                "status": "ERROR",
                "reason": str(e),
                "elapsed": round(time.time() - t0, 1),
            })

    # Print results
    print(f"\n{'='*80}")
    print("OCCUPATION SELECTION TEST RESULTS")
    print(f"{'='*80}")
    print(f"{'Employer':<40} {'Sector':<20} {'Status':<6} {'Time'}")
    print(f"{'-'*80}")

    pass_count = 0
    for r in results:
        print(f"{r['employer']:<40} {r['sector']:<20} {r['status']:<6} {r['elapsed']}s")
        if r["status"] == "PASS":
            pass_count += 1

    print(f"\n{pass_count}/{len(results)} passed")

    # Detail for failures
    failures = [r for r in results if r["status"] != "PASS"]
    if failures:
        print(f"\n{'='*80}")
        print("FAILURE DETAILS")
        print(f"{'='*80}")
        for r in failures:
            print(f"\n{r['employer']} ({r['sector']}):")
            print(f"  Selected: {r['selected']} ({r['soc_code']})")
            print(f"  Core skills: {', '.join(r['core_skills'])}")
            print(f"  Reason: {r['reason']}")

    # Detail for all selections
    print(f"\n{'='*80}")
    print("ALL SELECTIONS")
    print(f"{'='*80}")
    for r in results:
        skills = ", ".join(r["core_skills"][:3])
        print(f"  {r['employer']}: {r['selected']} [{skills}]")


if __name__ == "__main__":
    run_tests()
