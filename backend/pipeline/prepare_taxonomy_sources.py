"""
Prepare taxonomy source data for the dedicated curation session.

Mines MCFs, enriched files, occupations, and generate_occupations.py
to produce a structured data package that informs taxonomy design.

Usage:
    python -m pipeline.prepare_taxonomy_sources
    # Output: pipeline/cache/taxonomy_sources.json
"""

from __future__ import annotations

import csv
import json
import logging
import re
from collections import Counter, defaultdict
from pathlib import Path

logger = logging.getLogger(__name__)

CACHE_DIR = Path(__file__).parent / "cache"
MCF_DIR = Path("/Users/dayonekoo/Desktop/cc_dataset/mastercoursefiles")
INDUSTRY_DIR = Path(__file__).parent / "industry"


def _extract_top_code_programs() -> dict:
    """Parse all 125 MCFs to extract TOP code program structure."""
    top4_counts: Counter = Counter()
    top2_groups: defaultdict = defaultdict(set)
    colleges_per_top4: defaultdict = defaultdict(set)

    for mcf_path in sorted(MCF_DIR.glob("MasterCourseFile_*.csv")):
        college = mcf_path.stem.replace("MasterCourseFile_", "")
        try:
            with open(mcf_path, newline="") as f:
                reader = csv.reader(f)
                next(reader, None)
                for row in reader:
                    if len(row) < 7:
                        continue
                    top6 = row[3].strip()
                    if len(top6) < 4:
                        continue
                    top4 = top6[:4]
                    top2 = top6[:2]
                    credit = row[4].strip()
                    if credit in ("C", "D"):  # Credit courses only
                        top4_counts[top4] += 1
                        top2_groups[top2].add(top4)
                        colleges_per_top4[top4].add(college)
        except Exception as e:
            logger.warning(f"Error parsing {mcf_path.name}: {e}")

    # Load TOP4 program names from calibration files
    top4_names = {}
    for cal_path in sorted((Path(__file__).parent / "calibrations" / "top4").glob("*.json")):
        try:
            with open(cal_path) as f:
                data = json.load(f)
            for code, info in data.get("top4_codes", {}).items():
                if code not in top4_names:
                    top4_names[code] = info.get("name", "")
        except Exception:
            pass

    # Build structured output
    programs = []
    for top4, count in top4_counts.most_common():
        top2 = top4[:2]
        programs.append({
            "top4": top4,
            "top2": top2,
            "name": top4_names.get(top4, ""),
            "course_count": count,
            "college_count": len(colleges_per_top4[top4]),
        })

    # TOP2 group summary
    top2_summary = {}
    TOP2_NAMES = {
        "01": "Agriculture & Natural Resources",
        "02": "Architecture & Related Technologies",
        "03": "Environmental Sciences & Technologies",
        "04": "Biological Sciences",
        "05": "Business & Management",
        "06": "Media & Communications",
        "07": "Information Technology",
        "08": "Education",
        "09": "Engineering & Industrial Technologies",
        "10": "Fine & Applied Arts",
        "11": "Foreign Language",
        "12": "Health",
        "13": "Family & Consumer Sciences",
        "14": "Law",
        "15": "Humanities (Letters)",
        "16": "Library Science",
        "17": "Mathematics",
        "18": "Military Studies",
        "19": "Physical Sciences",
        "20": "Psychology",
        "21": "Public & Protective Services",
        "22": "Social Sciences",
        "30": "Commercial Services",
        "49": "Interdisciplinary Studies",
    }
    for top2, top4s in sorted(top2_groups.items()):
        total_courses = sum(top4_counts[t] for t in top4s)
        top2_summary[top2] = {
            "name": TOP2_NAMES.get(top2, f"Group {top2}"),
            "top4_count": len(top4s),
            "total_courses": total_courses,
            "programs": [top4_names.get(t, t) for t in sorted(top4s) if top4_names.get(t)],
        }

    return {
        "programs": programs,
        "top2_summary": top2_summary,
        "total_top4_codes": len(top4_counts),
        "total_top2_groups": len(top2_groups),
    }


def _extract_enriched_skills() -> dict:
    """Parse all enriched files to extract skill frequencies."""
    skill_counts: Counter = Counter()
    skill_colleges: defaultdict = defaultdict(set)
    total_courses = 0

    for enriched_path in sorted(CACHE_DIR.glob("*_enriched.json")):
        college = enriched_path.stem.replace("_enriched", "")
        try:
            with open(enriched_path) as f:
                courses = json.load(f)
            total_courses += len(courses)
            for course in courses:
                for skill in course.get("skill_mappings", []):
                    skill_counts[skill] += 1
                    skill_colleges[skill].add(college)
        except Exception as e:
            logger.warning(f"Error parsing {enriched_path.name}: {e}")

    # Filter to skills appearing in 5+ courses
    frequent_skills = []
    for skill, count in skill_counts.most_common():
        if count < 5:
            continue
        frequent_skills.append({
            "name": skill,
            "course_count": count,
            "college_count": len(skill_colleges[skill]),
        })

    return {
        "skills": frequent_skills,
        "total_unique_skills": len(skill_counts),
        "total_courses_analyzed": total_courses,
        "colleges_analyzed": len(list(CACHE_DIR.glob("*_enriched.json"))),
    }


def _extract_occupation_skills() -> dict:
    """Parse occupations.json for industry-side skill vocabulary."""
    occ_path = INDUSTRY_DIR / "occupations.json"
    if not occ_path.exists():
        return {"skills": [], "occupations": 0}

    with open(occ_path) as f:
        occupations = json.load(f)

    skill_counts: Counter = Counter()
    skill_soc_groups: defaultdict = defaultdict(set)
    soc_group_names = defaultdict(set)

    for occ in occupations:
        soc = occ.get("soc_code", "")
        soc2 = soc.split("-")[0] if "-" in soc else soc[:2]
        title = occ.get("title", "")
        soc_group_names[soc2].add(title)
        for skill in occ.get("skills", []):
            skill_counts[skill] += 1
            skill_soc_groups[skill].add(soc2)

    skills = []
    for skill, count in skill_counts.most_common():
        skills.append({
            "name": skill,
            "occupation_count": count,
            "soc_group_count": len(skill_soc_groups[skill]),
            "soc_groups": sorted(skill_soc_groups[skill]),
        })

    # SOC group summary
    SOC_NAMES = {
        "11": "Management", "13": "Business & Financial",
        "15": "Computer & Mathematical", "17": "Architecture & Engineering",
        "19": "Life/Physical/Social Science", "21": "Community & Social Service",
        "23": "Legal", "25": "Education/Training/Library",
        "27": "Arts/Design/Entertainment/Media", "29": "Healthcare Practitioners",
        "31": "Healthcare Support", "33": "Protective Service",
        "35": "Food Preparation & Serving", "37": "Building/Grounds Maintenance",
        "39": "Personal Care & Service", "41": "Sales",
        "43": "Office & Administrative Support", "45": "Farming/Fishing/Forestry",
        "47": "Construction & Extraction", "49": "Installation/Maintenance/Repair",
        "51": "Production", "53": "Transportation & Material Moving",
    }
    soc_summary = {}
    for soc2, titles in sorted(soc_group_names.items()):
        soc_summary[soc2] = {
            "name": SOC_NAMES.get(soc2, f"SOC {soc2}"),
            "occupation_count": len(titles),
            "sample_titles": sorted(titles)[:10],
        }

    return {
        "skills": skills,
        "total_occupations": len(occupations),
        "total_unique_skills": len(skill_counts),
        "soc_summary": soc_summary,
    }


def _extract_generate_occ_vocabulary() -> dict:
    """Parse generate_occupations.py to extract the full embedded vocabulary."""
    gen_path = INDUSTRY_DIR / "generate_occupations.py"
    if not gen_path.exists():
        return {"base_skills": {}, "pattern_skills": []}

    source = gen_path.read_text()

    # Extract GROUP_BASE_SKILLS
    base_skills = {}
    base_match = re.search(r"GROUP_BASE_SKILLS\s*=\s*\{(.+?)\}", source, re.DOTALL)
    if base_match:
        for line in base_match.group(1).split("\n"):
            m = re.match(r'\s*"(\d+)":\s*\[(.+?)\]', line)
            if m:
                soc = m.group(1)
                skills = re.findall(r'"([^"]+)"', m.group(2))
                base_skills[soc] = skills

    # Extract all skill strings from TITLE_SKILL_PATTERNS
    pattern_skills: Counter = Counter()
    for match in re.finditer(r'"([^"]+)"', source):
        term = match.group(1)
        # Filter: must look like a skill (not a regex, not a SOC code)
        if (len(term) > 3 and not term.startswith("r\"") and
                not re.match(r"^\d", term) and
                not any(c in term for c in r".*+?[]()\\|^$") and
                term[0].isupper()):
            pattern_skills[term] += 1

    return {
        "base_skills_by_soc": base_skills,
        "all_vocabulary": sorted(set(
            s for skills in base_skills.values() for s in skills
        ) | set(pattern_skills.keys())),
    }


def _extract_current_taxonomy() -> dict:
    """Load the current SEED + TIER2 taxonomy."""
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from pipeline.skills import UNIFIED_TAXONOMY

    return {
        "unified_taxonomy": sorted(UNIFIED_TAXONOMY),
        "total": len(UNIFIED_TAXONOMY),
    }


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)-7s %(message)s", datefmt="%H:%M:%S")

    logger.info("Extracting taxonomy sources...")

    logger.info("  1/5: TOP code programs from MCFs...")
    top_codes = _extract_top_code_programs()
    logger.info(f"    {top_codes['total_top4_codes']} TOP4 codes, {top_codes['total_top2_groups']} TOP2 groups")

    logger.info("  2/5: Enriched skill frequencies...")
    enriched = _extract_enriched_skills()
    logger.info(f"    {len(enriched['skills'])} skills (freq >= 5) from {enriched['colleges_analyzed']} colleges")

    logger.info("  3/5: Occupation skills...")
    occupations = _extract_occupation_skills()
    logger.info(f"    {occupations['total_unique_skills']} skills across {occupations['total_occupations']} occupations")

    logger.info("  4/5: generate_occupations.py vocabulary...")
    gen_vocab = _extract_generate_occ_vocabulary()
    logger.info(f"    {len(gen_vocab['all_vocabulary'])} unique terms in heuristic patterns")

    logger.info("  5/5: Current taxonomy...")
    current = _extract_current_taxonomy()
    logger.info(f"    {current['total']} terms (SEED + TIER2)")

    # Assemble the package
    package = {
        "description": "Taxonomy source data for the dedicated curation session",
        "education_side": {
            "top_code_structure": top_codes,
            "enriched_skills": enriched,
        },
        "industry_side": {
            "occupation_skills": occupations,
            "heuristic_vocabulary": gen_vocab,
        },
        "current_taxonomy": current,
    }

    output_path = CACHE_DIR / "taxonomy_sources.json"
    with open(output_path, "w") as f:
        json.dump(package, f, indent=2)
    logger.info(f"\nWrote {output_path} ({output_path.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
