"""Test harness for curriculum co-design primary department selection.

Tests that the LLM selects the department whose identity and mission
most directly align with the occupation — not the department with
the most courses or the broadest skill overlap.

Usage:
    cd backend
    NEO4J_URI=bolt://localhost:7687 NEO4J_USERNAME=neo4j NEO4J_PASSWORD=kallipolis_dev \
    ANTHROPIC_API_KEY=... python tests/test_primary_department.py
"""

from __future__ import annotations
import os
import sys
import time
import logging

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(message)s")

from workflows.partnerships import (
    _gather_targeted_context, _select_occupation,
    _gather_aligned_curriculum, _filter_relevant_departments,
    _select_primary_department_llm,
)

COLLEGE = "College of the Sequoias"

# Test cases: employer, expected primary department pattern, rejected departments
TEST_CASES = [
    {
        "employer": "Fresno Plumbing and Heating",
        "sector": "Construction",
        "expect_dept": "Environmental Control|HVAC|Plumbing|Construction",
        "reject_dept": ["Chemistry", "Biology", "Mathematics", "English"],
    },
    {
        "employer": "Cargill",
        "sector": "Manufacturing",
        "expect_dept": "Agri|Food|Culinary",
        "reject_dept": ["Chemistry", "Biology", "Mathematics", "Physics"],
    },
    {
        "employer": "Adventist Health Hanford",
        "sector": "Healthcare",
        "expect_dept": "Nursing",
        "reject_dept": ["Chemistry", "Biology", "Mathematics"],
    },
    {
        "employer": "Community Medical Center",
        "sector": "Professional Services",
        "expect_dept": "Nursing",
        "reject_dept": ["Chemistry", "Biology", "Mathematics"],
    },
    {
        "employer": "Foster Farms",
        "sector": "Agriculture",
        "expect_dept": "Agri|Animal|Food|Industrial",
        "reject_dept": ["Chemistry", "Biology", "Mathematics", "English"],
    },
    {
        "employer": "Clovis Adult Education",
        "sector": "Education",
        "expect_dept": "Educ|Child",
        "reject_dept": ["Chemistry", "Biology", "Mathematics"],
    },
    {
        "employer": "Central California Builders and Development",
        "sector": "Construction",
        "expect_dept": "Construction|Architect|Draft",
        "reject_dept": ["Chemistry", "Biology", "Mathematics", "English"],
    },
    {
        "employer": "Home Depot",
        "sector": "Retail",
        "expect_dept": "Business|Market",
        "reject_dept": ["Chemistry", "Biology", "Nursing"],
    },
    {
        "employer": "Mike Jensen Farms",
        "sector": "Agriculture",
        "expect_dept": "Agri|Plant|Farm",
        "reject_dept": ["Chemistry", "Biology", "English", "Mathematics"],
    },
    {
        "employer": "ULTA Beauty Distribution Center",
        "sector": "Professional Services",
        "expect_dept": "Industrial|Work Experience|Business",
        "reject_dept": ["Chemistry", "Biology", "Nursing", "English"],
    },
]


def run_tests():
    results = []

    for tc in TEST_CASES:
        employer = tc["employer"]
        print(f"Testing: {employer}...", file=sys.stderr, flush=True)

        t0 = time.time()
        try:
            # Run the pipeline up to department selection
            gathered = _gather_targeted_context(employer, COLLEGE)
            selected_occ = _select_occupation(gathered, "curriculum_codesign")
            occ_title = selected_occ.get("title", "")
            core_skills = selected_occ.get("core_skills", [])

            _, curriculum_evidence = _gather_aligned_curriculum(COLLEGE, core_skills)
            all_dept_names = [d["department"] for d in curriculum_evidence]
            relevant_depts = _filter_relevant_departments(
                gathered.employer_name, occ_title, all_dept_names
            )

            # Select primary department
            primary = _select_primary_department_llm(employer, occ_title, relevant_depts)
            elapsed = round(time.time() - t0, 1)

            # Check expected
            expect_pass = any(
                term.strip().lower() in primary.lower()
                for term in tc["expect_dept"].split("|")
            )

            # Check rejects
            rejected = False
            rejected_by = ""
            for rej in tc["reject_dept"]:
                if rej.lower() in primary.lower():
                    rejected = True
                    rejected_by = rej
                    break

            passed = expect_pass and not rejected
            status = "PASS" if passed else "FAIL"

            reason = ""
            if not expect_pass:
                reason = f"expected dept matching '{tc['expect_dept']}'"
            if rejected:
                reason = f"selected rejected dept (contains '{rejected_by}')"

            results.append({
                "employer": employer,
                "sector": tc["sector"],
                "occupation": occ_title,
                "core_skills": core_skills,
                "filtered_depts": relevant_depts,
                "primary": primary,
                "status": status,
                "reason": reason,
                "elapsed": elapsed,
            })

        except Exception as e:
            results.append({
                "employer": employer,
                "sector": tc["sector"],
                "occupation": "",
                "core_skills": [],
                "filtered_depts": [],
                "primary": "ERROR",
                "status": "ERROR",
                "reason": str(e),
                "elapsed": round(time.time() - t0, 1),
            })

    # Print results
    print(f"\n{'='*90}")
    print("PRIMARY DEPARTMENT SELECTION TEST RESULTS")
    print(f"{'='*90}")
    print(f"{'Employer':<40} {'Occupation':<25} {'Primary Dept':<25} {'Status'}")
    print(f"{'-'*90}")

    pass_count = 0
    for r in results:
        print(f"{r['employer']:<40} {r['occupation'][:23]:<25} {r['primary'][:23]:<25} {r['status']}")
        if r["status"] == "PASS":
            pass_count += 1

    print(f"\n{pass_count}/{len(results)} passed")

    # Failures
    failures = [r for r in results if r["status"] != "PASS"]
    if failures:
        print(f"\n{'='*90}")
        print("FAILURE DETAILS")
        print(f"{'='*90}")
        for r in failures:
            print(f"\n{r['employer']} ({r['sector']}):")
            print(f"  Occupation: {r['occupation']}")
            print(f"  Filtered depts: {', '.join(r['filtered_depts'])}")
            print(f"  Selected: {r['primary']}")
            print(f"  Reason: {r['reason']}")

    # All details
    print(f"\n{'='*90}")
    print("ALL SELECTIONS")
    print(f"{'='*90}")
    for r in results:
        print(f"  {r['employer']}: {r['primary']}")
        print(f"    Occupation: {r['occupation']}")
        print(f"    From: [{', '.join(r['filtered_depts'])}]")


if __name__ == "__main__":
    run_tests()
