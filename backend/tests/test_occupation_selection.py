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

from partnerships.generate import _gather_targeted_context, _select_occupation, _gather_aligned_curriculum, _filter_relevant_departments
from ontology.schema import get_driver

COLLEGE = "College of the Sequoias"

# Test cases: (employer, expected_occupation_substring, unacceptable_occupations)
# The expected substring should match the occupation title we'd want selected.
# Unacceptable occupations are generic roles that should NOT be selected.
TEST_CASES = [
    # Trades / Specific
    {
        "employer": "Fresno Plumbing and Heating",
        "expect_contains": "Heating",
        "reject": ["Accountants", "General and Operations", "Administrative"],
        "sector": "Construction",
        "expect_depts": ["Environmental Control|Construction"],
        "reject_depts": ["Sociology", "English", "Psychology", "Fashion"],
    },
    # Agriculture - Poultry Processor
    {
        "employer": "Foster Farms",
        "expect_contains": "Agri|Food",
        "reject": ["Accountants", "General and Operations", "Human Resources"],
        "sector": "Agriculture",
        "expect_depts": ["Agri"],
        "reject_depts": ["Sociology", "English", "Fashion"],
    },
    # Food Manufacturing
    {
        "employer": "Cargill",
        "expect_contains": "Food",
        "reject": ["Accountants", "Marketing", "Human Resources"],
        "sector": "Manufacturing",
        "expect_depts": ["Agri|Food|Work Experience"],
        "reject_depts": ["Sociology", "English", "Fashion"],
    },
    # Healthcare
    {
        "employer": "Adventist Health Hanford",
        "expect_contains": "Nurs",
        "reject": ["Accountants", "Administrative", "Human Resources"],
        "sector": "Healthcare",
        "expect_depts": ["Nurs|Health"],
        "reject_depts": ["Sociology", "English", "Fashion", "Welding"],
    },
    # Healthcare - Hospital
    {
        "employer": "Community Medical Center",
        "expect_contains": "Nurs",
        "reject": ["Accountants", "Administrative", "Human Resources"],
        "sector": "Professional Services",
        "expect_depts": ["Nurs|Health"],
        "reject_depts": ["Sociology", "English", "Fashion", "Welding"],
    },
    # Education
    {
        "employer": "Clovis Adult Education",
        "expect_contains": "Teach|Instruct",
        "reject": ["Accountants", "Administrative", "Human Resources"],
        "sector": "Education",
        "expect_depts": ["Educ|Child"],
        "reject_depts": ["Welding", "Fashion", "Automotive"],
    },
    # Construction
    {
        "employer": "Central California Builders and Development",
        "expect_contains": "Civil|Construction",
        "reject": ["Accountants", "Human Resources", "General and Operations"],
        "sector": "Construction",
        "expect_depts": ["Engineer|Construction|Draft"],
        "reject_depts": ["Sociology", "English", "Fashion"],
    },
    # Government - Prison
    {
        "employer": "California State Prison, Corcoran",
        "expect_contains": "Nurs|Correct|Probation",
        "reject": ["Accountants", "Administrative", "General and Operations"],
        "sector": "Government",
        "expect_depts": ["Nurs|Justice|Health"],
        "reject_depts": ["Fashion", "Welding", "Automotive"],
    },
    # Food Manufacturing - Meat
    {
        "employer": "Central Valley Meat Company",
        "expect_contains": "Food|Safety",
        "reject": ["Accountants", "Human Resources", "General and Operations"],
        "sector": "Manufacturing",
        "expect_depts": ["Food|Agri|Health|Work Experience"],
        "reject_depts": ["Sociology", "English", "Fashion"],
    },
    # Retail - Home Improvement
    {
        "employer": "Home Depot",
        "expect_contains": "Sales|Manager",
        "reject": ["Accountants", "Human Resources"],
        "sector": "Retail",
        "expect_depts": ["Bus|Market"],
        "reject_depts": ["Welding", "Fashion", "Nursing"],
    },
    # Distribution
    {
        "employer": "ULTA Beauty Distribution Center",
        "expect_contains": "Logist",
        "reject": ["Accountants", "Human Resources", "Administrative"],
        "sector": "Professional Services",
        "expect_depts": ["Bus|Supply|Manage|Industrial|Work Experience"],
        "reject_depts": ["Nursing", "Fashion", "Welding"],
    },
    # Agriculture - Farm
    {
        "employer": "Mike Jensen Farms",
        "expect_contains": "Agri",
        "reject": ["Accountants", "General and Operations"],
        "sector": "Agriculture",
        "expect_depts": ["Agri|Plant|Farm"],
        "reject_depts": ["Sociology", "English", "Fashion"],
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

            # Check downstream curriculum alignment (with department filter)
            dept_names = []
            dept_pass = True
            dept_reject_hit = ""
            dept_expect_miss = ""
            if core_skills and skills_exist:
                _, curriculum_evidence = _gather_aligned_curriculum(COLLEGE, core_skills)
                all_dept_names = [d["department"] for d in curriculum_evidence]
                dept_names = _filter_relevant_departments(employer, title, all_dept_names)

                # Check expected departments (at least one match required per pattern)
                for pattern in tc.get("expect_depts", []):
                    found = any(
                        any(term.strip().lower() in dept.lower() for term in pattern.split("|"))
                        for dept in dept_names
                    )
                    if not found:
                        dept_pass = False
                        dept_expect_miss = pattern

                # Check rejected departments
                for dept in dept_names:
                    for reject_dept in tc.get("reject_depts", []):
                        if reject_dept.lower() in dept.lower():
                            dept_pass = False
                            dept_reject_hit = f"{dept} (matches reject '{reject_dept}')"

            passed = expect_pass and not rejected and skills_exist and dept_pass
            status = "PASS" if passed else "FAIL"

            reason = ""
            if not expect_pass:
                reason = f"expected '{tc['expect_contains']}' in title"
            elif rejected:
                reason = f"selected rejected occupation (contains '{rejected_by}')"
            elif not skills_exist:
                reason = f"core skills not in graph: {', '.join(missing_skills)}"
            elif dept_expect_miss:
                reason = f"expected dept matching '{dept_expect_miss}' not found in: {', '.join(dept_names)}"
            elif dept_reject_hit:
                reason = f"rejected dept found: {dept_reject_hit}"

            results.append({
                "employer": employer,
                "sector": tc["sector"],
                "selected": title,
                "soc_code": soc_code,
                "core_skills": core_skills,
                "departments": dept_names,
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
            print(f"  Departments: {', '.join(r.get('departments', []))}")
            print(f"  Reason: {r['reason']}")

    # Detail for all selections
    print(f"\n{'='*80}")
    print("ALL SELECTIONS")
    print(f"{'='*80}")
    for r in results:
        skills = ", ".join(r["core_skills"][:3])
        depts = ", ".join(r.get("departments", [])[:5])
        print(f"  {r['employer']}: {r['selected']}")
        print(f"    Skills: [{skills}]")
        print(f"    Depts:  [{depts}]")


if __name__ == "__main__":
    run_tests()
