"""Test harness for curriculum co-design gap skill identification.

Tests that the dedicated gap identification prompt produces genuinely
absent skills across diverse employers — not taxonomy artifacts or
synonyms of existing skills.

Usage:
    cd backend
    NEO4J_URI=bolt://localhost:7687 NEO4J_USERNAME=neo4j NEO4J_PASSWORD=kallipolis_dev \
    ANTHROPIC_API_KEY=... python tests/test_gap_identification.py
"""

from __future__ import annotations
import os
import sys
import time
import logging

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(message)s")

from partnerships.generate import (
    _gather_targeted_context, _select_occupation,
    _get_developed_skills, _identify_gap_skill,
)

COLLEGE = "College of the Sequoias"

# Same 12 employers from the occupation selection test harness
TEST_CASES = [
    {"employer": "Fresno Plumbing and Heating", "sector": "Construction"},
    {"employer": "Foster Farms", "sector": "Agriculture"},
    {"employer": "Cargill", "sector": "Manufacturing"},
    {"employer": "Adventist Health Hanford", "sector": "Healthcare"},
    {"employer": "Community Medical Center", "sector": "Professional Services"},
    {"employer": "Clovis Adult Education", "sector": "Education"},
    {"employer": "Central California Builders and Development", "sector": "Construction"},
    {"employer": "California State Prison, Corcoran", "sector": "Government"},
    {"employer": "Central Valley Meat Company", "sector": "Manufacturing"},
    {"employer": "Home Depot", "sector": "Retail"},
    {"employer": "ULTA Beauty Distribution Center", "sector": "Professional Services"},
    {"employer": "Mike Jensen Farms", "sector": "Agriculture"},
]


def run_tests():
    results = []

    for tc in TEST_CASES:
        employer = tc["employer"]
        print(f"Testing: {employer}...", file=sys.stderr, flush=True)

        t0 = time.time()
        try:
            # Step 1: Get context and select occupation (using co-design flow)
            gathered = _gather_targeted_context(employer, COLLEGE)
            selected_occ = _select_occupation(gathered, "curriculum_codesign")
            occ_title = selected_occ.get("title", "")

            # Step 2: Get developed skills
            college_skills = _get_developed_skills(COLLEGE, occ_title)

            # Step 3: Identify gap
            gap_result = _identify_gap_skill(
                gathered.employer_name, gathered.sector, occ_title, college_skills
            )
            elapsed = round(time.time() - t0, 1)

            gap_skill = gap_result.get("gap_skill", "")
            rationale = gap_result.get("rationale", "")

            # Check: is the gap skill a substring of any developed skill (basic synonym check)?
            potential_overlap = []
            gap_lower = gap_skill.lower()
            for s in college_skills:
                s_lower = s.lower()
                if gap_lower in s_lower or s_lower in gap_lower:
                    potential_overlap.append(s)

            results.append({
                "employer": employer,
                "sector": tc["sector"],
                "occupation": occ_title,
                "core_skills": selected_occ.get("core_skills", []),
                "developed_skills": college_skills,
                "gap_skill": gap_skill,
                "rationale": rationale,
                "potential_overlap": potential_overlap,
                "elapsed": elapsed,
            })

        except Exception as e:
            results.append({
                "employer": employer,
                "sector": tc["sector"],
                "occupation": "",
                "core_skills": [],
                "developed_skills": [],
                "gap_skill": "ERROR",
                "rationale": str(e),
                "potential_overlap": [],
                "elapsed": round(time.time() - t0, 1),
            })

    # Print results
    print(f"\n{'='*90}")
    print("GAP SKILL IDENTIFICATION TEST RESULTS")
    print(f"{'='*90}")
    print(f"{'Employer':<40} {'Occupation':<30} {'Gap Skill':<25} {'Time'}")
    print(f"{'-'*90}")

    for r in results:
        flag = " ⚠" if r["potential_overlap"] else ""
        print(f"{r['employer']:<40} {r['occupation'][:28]:<30} {r['gap_skill'][:23]:<25} {r['elapsed']}s{flag}")

    # Detailed output
    print(f"\n{'='*90}")
    print("DETAILED RESULTS")
    print(f"{'='*90}")
    for r in results:
        print(f"\n{r['employer']} ({r['sector']}):")
        print(f"  Occupation: {r['occupation']}")
        print(f"  Core skills: {', '.join(r['core_skills'])}")
        print(f"  Gap skill: {r['gap_skill']}")
        print(f"  Rationale: {r['rationale']}")
        if r["potential_overlap"]:
            print(f"  ⚠ POTENTIAL OVERLAP with: {', '.join(r['potential_overlap'])}")
        print(f"  Developed skills ({len(r['developed_skills'])}): {', '.join(r['developed_skills'])}")


if __name__ == "__main__":
    run_tests()
