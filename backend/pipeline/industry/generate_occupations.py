"""
Generate occupation descriptions and skill mappings for OEWS occupations.

Maps each occupation to 5-8 skills from the existing skill vocabulary
derived from community college course catalogs. Skills are matched by
occupation title and SOC group using keyword-based heuristics validated
against the actual skill list.

Usage:
    python -m pipeline.industry.generate_occupations
"""

import json
import logging
import re
from pathlib import Path

logger = logging.getLogger(__name__)

# SOC major group → base skills that most occupations in the group share
GROUP_BASE_SKILLS = {
    "11": ["Administration & Management", "Strategic Planning", "Organizational Leadership", "Budgeting", "Decision Making"],
    "13": ["Economics & Accounting", "Financial Analysis", "Data Analysis & Visualization", "Regulatory Compliance"],
    "15": ["Programming", "Computers & Electronics", "Software Development", "Data Analysis & Visualization"],
    "17": ["Engineering & Technology", "Mathematics", "Design", "Technical Drawing"],
    "19": ["Science", "Research", "Data Analysis & Visualization", "Laboratory Techniques"],
    "21": ["Social Perceptiveness", "Active Listening", "Counseling", "Community Engagement"],
    "23": ["Law & Government", "Legal Research", "Regulatory Compliance", "Writing"],
    "25": ["Education & Training", "Instructing", "Curriculum Development", "Assessment"],
    "27": ["Design", "Creative Thinking", "Multimedia Production", "Communications & Media"],
    "29": ["Clinical Skills", "Patient Care", "Medical Terminology", "Anatomy & Physiology"],
    "31": ["Patient Care", "Personal Care", "Basic Life Support", "Communication Skills"],
    "33": ["Law & Government", "Safety Protocols", "Physical Fitness", "Emergency Response"],
    "35": ["Food Safety", "Cooking Techniques", "Food Service Operations", "Sanitation"],
    "37": ["Equipment Operation & Maintenance", "Safety Protocols", "Chemical Handling"],
    "39": ["Customer Service", "Communication Skills", "Personal Care"],
    "41": ["Sales & Marketing", "Customer Service", "Product Knowledge", "Communication Skills"],
    "43": ["Data Entry", "Office Administration", "Communication Skills", "Filing Systems"],
    "45": ["Equipment Operation & Maintenance", "Safety Protocols", "Agriculture"],
    "47": ["Safety Protocols", "Equipment Operation & Maintenance", "Construction", "Blueprint Reading"],
    "49": ["Troubleshooting", "Equipment Operation & Maintenance", "Mechanical", "Electrical Systems"],
    "51": ["Quality Control Analysis", "Manufacturing", "Equipment Operation & Maintenance", "Safety Protocols"],
    "53": ["Transportation", "Safety Protocols", "Equipment Operation & Maintenance"],
}

# Keyword patterns in occupation titles → additional skills
TITLE_SKILL_PATTERNS = [
    # Healthcare
    (r"nurs", ["Nursing Process", "Patient Assessment", "Medication Administration", "Clinical Patient Care"]),
    (r"dental", ["Dental Hygiene", "Dental Assisting", "Infection Control"]),
    (r"pharmac", ["Pharmacology", "Medication Administration", "Chemistry"]),
    (r"therap", ["Therapeutic Techniques", "Patient Assessment", "Rehabilitation"]),
    (r"surgeon|surgical", ["Surgical Procedures", "Anatomy & Physiology", "Patient Care"]),
    (r"physician|doctor", ["Clinical Patient Care", "Patient Assessment", "Diagnosis"]),
    (r"radiol|imaging|sonograph", ["Medical Imaging", "Anatomy & Physiology", "Patient Care"]),
    (r"respiratory", ["Respiratory Therapy", "Patient Care", "Medical Equipment"]),
    (r"medical assist", ["Medical Assisting", "Patient Care", "Medical Terminology"]),
    (r"veterinar", ["Animal Science", "Veterinary Medicine", "Clinical Skills"]),
    (r"health info|medical record", ["Health Information Systems", "Medical Terminology", "Regulatory Compliance"]),
    (r"mental health|psycholog|psychiatr", ["Psychology", "Counseling", "Mental Health"]),
    (r"social work", ["Social Work", "Case Management", "Community Resources"]),
    (r"dietiti|nutritio", ["Nutrition", "Food Science", "Patient Care"]),
    (r"optometr|optic", ["Optics", "Patient Care", "Clinical Skills"]),
    (r"audiolog", ["Audiology", "Patient Assessment", "Clinical Skills"]),
    (r"occupational therap", ["Occupational Therapy", "Rehabilitation", "Patient Assessment"]),
    (r"physical therap", ["Physical Therapy", "Rehabilitation", "Anatomy & Physiology"]),
    (r"emerg|paramed|emt", ["Emergency Response", "Basic Life Support", "Patient Assessment"]),

    # Technology
    (r"software", ["Software Development", "Programming", "Software Testing", "Algorithm Design"]),
    (r"web develop|web design", ["Web Development", "HTML/CSS", "Programming"]),
    (r"database", ["Database Management", "Data Management", "SQL"]),
    (r"network|system.?admin", ["Network Configuration", "Computer Systems", "Information Technology"]),
    (r"cybersecur|information secur", ["Network & Cybersecurity", "Information Security", "Computers & Electronics"]),
    (r"data scien|data analy|statistic", ["Data Analysis & Visualization", "Statistics", "Programming"]),
    (r"artificial intelligence|machine learn", ["Machine Learning", "Data Analysis & Visualization", "Programming"]),
    (r"computer support|help desk|it support", ["Technical Support", "Troubleshooting", "Computer Systems"]),

    # Engineering
    (r"civil engineer", ["Civil Engineering", "Structural Analysis", "Construction"]),
    (r"mechanical engineer", ["Mechanical", "Engineering & Technology", "CAD"]),
    (r"electrical engineer", ["Electrical Systems", "Electronics", "Circuit Design"]),
    (r"industrial engineer", ["Industrial Engineering", "Process Improvement", "Quality Control Analysis"]),
    (r"environmental engineer", ["Environmental Science", "Regulatory Compliance", "Chemistry"]),
    (r"chemical engineer", ["Chemistry", "Process Engineering", "Laboratory Techniques"]),
    (r"aerospace", ["Aerospace Engineering", "Physics", "Mathematics"]),
    (r"architect", ["Architecture", "Design", "CAD", "Construction"]),
    (r"survey|cartograph|geograph", ["Geography", "Geographic Information Systems", "Surveying"]),
    (r"drafter|drafting|cad", ["Technical Drawing", "CAD", "Design"]),

    # Trades/Construction
    (r"electrician|electrical install", ["Electrical Systems", "Blueprint Reading", "Electrical Wiring"]),
    (r"plumb", ["Plumbing", "Blueprint Reading", "Pipe Trades"]),
    (r"hvac|heating|air condition|refriger", ["HVAC", "Refrigeration", "Mechanical", "Troubleshooting"]),
    (r"weld", ["Welding & Fabrication", "Metal Working", "Blueprint Reading"]),
    (r"carpenter", ["Carpentry", "Construction", "Blueprint Reading"]),
    (r"mason|concrete|brick", ["Construction", "Masonry", "Blueprint Reading"]),
    (r"paint|coat", ["Painting", "Surface Preparation", "Safety Protocols"]),
    (r"roofer", ["Construction", "Safety Protocols", "Roofing"]),
    (r"pipefitt|steamfitt", ["Pipe Trades", "Blueprint Reading", "Welding & Fabrication"]),
    (r"sheet metal", ["Sheet Metal Work", "Blueprint Reading", "Welding & Fabrication"]),
    (r"iron.?work", ["Structural Steel", "Welding & Fabrication", "Construction"]),
    (r"machin", ["Machining", "CNC Programming", "Manufacturing", "Blueprint Reading"]),
    (r"auto|vehicle|mechanic", ["Automotive Repair", "Troubleshooting", "Mechanical", "Diagnostics"]),

    # Business/Finance
    (r"account", ["Accounting", "Financial Statements", "Bookkeeping", "Tax Preparation"]),
    (r"financ|invest|secur.?anal", ["Financial Analysis", "Investment", "Economics & Accounting"]),
    (r"insur", ["Insurance", "Risk Management", "Customer Service"]),
    (r"real estate", ["Real Estate", "Sales & Marketing", "Negotiation"]),
    (r"human resource|hr ", ["Human Resources", "Personnel & Human Resources", "Recruitment"]),
    (r"market", ["Marketing", "Market Analysis", "Sales & Marketing", "Digital Marketing"]),
    (r"logist|supply chain", ["Supply Chain Management", "Logistics", "Inventory Management"]),
    (r"purchas|procurement|buyer", ["Procurement", "Supply Chain Management", "Negotiation"]),

    # Education
    (r"teacher|instructor|professor|faculty", ["Teaching", "Curriculum Development", "Assessment", "Classroom Management"]),
    (r"librar", ["Library Science", "Research", "Information Literacy"]),
    (r"child|preschool|kindergarten", ["Child Development & Pedagogy", "Early Childhood Education", "Classroom Management"]),
    (r"special education", ["Special Education", "Individualized Instruction", "Assessment"]),
    (r"tutor|teaching assist", ["Tutoring", "Teaching", "Communication Skills"]),

    # Arts/Media
    (r"graphic design", ["Graphic Design", "Digital Design", "Typography"]),
    (r"photograph", ["Photography", "Digital Photography", "Image Editing"]),
    (r"film|video|broadcast|camera", ["Video Production", "Broadcasting", "Film Production"]),
    (r"audio|sound", ["Audio Production", "Sound Design", "Audio Engineering"]),
    (r"music", ["Music", "Music Theory", "Performance"]),
    (r"writ|author|editor|report", ["Writing", "Editing", "Journalism"]),
    (r"translat|interpret", ["Translation", "Language Skills", "Cultural Competence"]),
    (r"animat", ["Animation", "3D Animation", "2D Animation", "Digital Design"]),
    (r"interior design", ["Interior Design", "Design", "Space Planning"]),

    # Food Service
    (r"chef|cook", ["Cooking Techniques", "Food Safety", "Menu Planning", "Kitchen Management"]),
    (r"bak", ["Baking", "Food Safety", "Cooking Techniques"]),
    (r"bartend", ["Bartending", "Customer Service", "Food Safety"]),
    (r"waiter|waitress|food server", ["Food Service Operations", "Customer Service"]),

    # Legal
    (r"lawyer|attorney", ["Legal Research", "Law & Government", "Litigation"]),
    (r"paralegal|legal assist", ["Paralegal Studies", "Legal Research", "Legal Writing"]),
    (r"judge|magistrate", ["Law & Government", "Legal Research", "Judgment & Decision Making"]),

    # Protective Services
    (r"firefight", ["Fire Science", "Emergency Response", "Safety Protocols", "Physical Fitness"]),
    (r"police|detective|sheriff|law enforcement", ["Criminal Justice", "Law Enforcement", "Investigation"]),
    (r"correct", ["Corrections", "Law & Government", "Safety Protocols"]),
    (r"security guard|security officer", ["Security", "Safety Protocols", "Surveillance"]),

    # Personal Care
    (r"barber|hairdress|cosmetolog|hair styl", ["Cosmetology", "Hair Styling", "Customer Service"]),
    (r"skin care|esthetic|facial", ["Skin Care", "Cosmetology", "Customer Service"]),
    (r"manicur|nail", ["Nail Technology", "Cosmetology", "Customer Service"]),
    (r"fitness|exercise|personal train", ["Physical Fitness", "Exercise Physiology", "Anatomy & Physiology"]),
    (r"recreation|amusement", ["Recreation", "Customer Service", "Program Management"]),
    (r"funeral|mortician|embalm", ["Funeral Services", "Customer Service", "Regulatory Compliance"]),
    (r"childcare|nann", ["Childcare", "Child Development & Pedagogy", "First Aid"]),

    # Agriculture
    (r"farm|agricult|crop|ranch", ["Agriculture", "Horticulture", "Equipment Operation & Maintenance"]),
    (r"landscap|groundskeep", ["Horticulture", "Landscaping", "Equipment Operation & Maintenance"]),
    (r"forest|logging", ["Forestry", "Environmental Science", "Equipment Operation & Maintenance"]),
    (r"fish|aquaculture", ["Aquaculture", "Marine Biology", "Equipment Operation & Maintenance"]),
    (r"pest control", ["Pest Management", "Chemical Handling", "Safety Protocols"]),
    (r"tree trimm|arborist", ["Arboriculture", "Safety Protocols", "Equipment Operation & Maintenance"]),
    (r"viticult|wine|vineyard", ["Viticulture", "Wine Production", "Agriculture"]),
    (r"horticult|flor", ["Horticulture", "Plant Science", "Design"]),

    # Transportation
    (r"truck|bus|driv", ["Driving", "Transportation", "Safety Protocols"]),
    (r"pilot|aviat", ["Aviation", "Navigation", "Safety Protocols"]),
    (r"sailor|marine|seaman|boat", ["Seamanship", "Navigation", "Safety Protocols"]),
    (r"locomotive|railroad|rail", ["Railroad Operations", "Safety Protocols", "Equipment Operation & Maintenance"]),
    (r"dispatc", ["Dispatching", "Communication Skills", "Emergency Response"]),

    # Production/Manufacturing
    (r"assembl", ["Assembly", "Manufacturing", "Quality Control Analysis"]),
    (r"inspector|quality", ["Quality Control Analysis", "Inspection", "Regulatory Compliance"]),
    (r"printing|press oper", ["Printing Technology", "Equipment Operation & Maintenance"]),
    (r"textile|sewing|tailor", ["Textiles", "Sewing", "Pattern Making"]),
    (r"woodwork|cabinet|furniture", ["Woodworking", "Carpentry", "Design"]),
    (r"jewel", ["Jewelry Making", "Design", "Metalworking"]),
    (r"electronic.?assembl|semiconductor", ["Electronics", "Assembly", "Quality Control Analysis"]),
    (r"water|wastewat", ["Water Treatment", "Environmental Science", "Chemistry"]),
    (r"power plant|stationary engineer", ["Power Generation", "Mechanical", "Safety Protocols"]),
]


def generate_description(title: str) -> str:
    """Generate a concise 1-2 sentence description for an occupation."""
    # Use title directly — most SOC titles are already descriptive
    # Add a standard framing
    t = title.lower()

    if "all other" in t:
        base = title.replace(", All Other", "").replace(", all other", "")
        return f"Performs specialized tasks in the {base.lower()} field not classified in more specific occupation categories."

    if "managers" in t or "director" in t or "chief" in t:
        return f"Plans, directs, and coordinates activities related to {title.lower().replace(' managers', '').replace(' manager', '')}."

    if "supervisors" in t or "supervisor" in t:
        return f"Directly supervises and coordinates activities of workers in {title.lower().replace('first-line supervisors of ', '').replace('first-line supervisor of ', '')}."

    if "technicians" in t or "technician" in t:
        field = title.lower().replace(" technicians", "").replace(" technician", "")
        return f"Operates equipment, conducts tests, and assists professionals in {field}."

    if "engineers" in t or "engineer" in t:
        field = title.lower().replace(" engineers", "").replace(" engineer", "")
        return f"Applies engineering principles to design, develop, test, and evaluate systems and processes in {field}."

    if "teachers" in t or "instructor" in t or "professor" in t:
        return f"Teaches courses and develops curriculum for students in {title.lower().replace(' teachers, postsecondary', '').replace(' instructor', '').replace(' professor', '')}."

    if "clerks" in t or "clerk" in t:
        return f"Performs clerical and administrative duties related to {title.lower().replace(' clerks', '').replace(' clerk', '')}."

    if "helpers" in t:
        return f"Assists skilled workers by performing support tasks in {title.lower().replace('helpers--', '').replace('helpers-', '')}."

    if "assemblers" in t or "fabricators" in t:
        return f"Assembles, fabricates, and finishes manufactured products related to {title.lower().replace(' assemblers and fabricators', '').replace(' assemblers', '')}."

    if "operators" in t or "operator" in t:
        return f"Operates and monitors equipment and machinery for {title.lower().replace(' operators', '').replace(' operator', '')}."

    if "inspectors" in t or "inspector" in t:
        return f"Examines and inspects products, materials, or processes to ensure quality and compliance in {title.lower().replace(' inspectors', '').replace(' inspector', '')}."

    if "installers" in t or "installer" in t or "repairers" in t:
        return f"Installs, maintains, and repairs equipment and systems related to {title.lower().replace(' installers and repairers', '').replace(' installer', '').replace(' repairer', '')}."

    if "analyst" in t:
        return f"Analyzes data, trends, and systems to support decision-making in {title.lower().replace(' analysts', '').replace(' analyst', '')}."

    if "specialist" in t:
        return f"Provides specialized expertise and support in {title.lower().replace(' specialists', '').replace(' specialist', '')}."

    if "worker" in t:
        return f"Performs tasks and duties related to {title.lower().replace(' workers', '').replace(' worker', '')}."

    if "assistant" in t or "aide" in t:
        return f"Provides support and assistance in {title.lower().replace(' assistants', '').replace(' assistant', '').replace(' aides', '').replace(' aide', '')}."

    return f"Performs professional duties and tasks as a {title.lower()}."


def map_skills(soc_code: str, title: str, valid_skills: set) -> list[str]:
    """Map an occupation to 5-8 skills from the valid skill set."""
    major = soc_code.split("-")[0]

    # Start with group base skills
    candidates = list(GROUP_BASE_SKILLS.get(major, []))

    # Add title-matched skills
    title_lower = title.lower()
    for pattern, skills in TITLE_SKILL_PATTERNS:
        if re.search(pattern, title_lower):
            candidates.extend(skills)

    # Filter to only valid skills
    matched = []
    seen = set()
    for skill in candidates:
        if skill in valid_skills and skill not in seen:
            matched.append(skill)
            seen.add(skill)

    # If too few matches, add generic skills from the group
    generic_fallbacks = [
        "Critical Thinking", "Complex Problem Solving", "Communication Skills",
        "Active Learning", "Time Management", "Teamwork",
        "Problem Solving", "Project Management", "Data Analysis & Visualization",
    ]
    for skill in generic_fallbacks:
        if len(matched) >= 5:
            break
        if skill in valid_skills and skill not in seen:
            matched.append(skill)
            seen.add(skill)

    return matched[:8]


def generate_all():
    """Generate descriptions and skill mappings for all OEWS occupations."""
    # Load data
    base_dir = Path(__file__).parent
    with open(base_dir / "oews_parsed.json") as f:
        oews = json.load(f)
    with open("/tmp/all_skills.json") as f:
        valid_skills = set(json.load(f))

    logger.info(f"Processing {len(oews['occupations'])} occupations against {len(valid_skills)} skills")

    occupations = []
    skill_hit_counts = []

    for occ in oews["occupations"]:
        soc = occ["soc_code"]
        title = occ["title"]

        description = generate_description(title)
        skills = map_skills(soc, title, valid_skills)

        occupations.append({
            "soc_code": soc,
            "title": title,
            "description": description,
            "annual_wage": occ["annual_wage"],
            "skills": skills,
            "regions": occ["regions"],
        })
        skill_hit_counts.append(len(skills))

    # Stats
    avg_skills = sum(skill_hit_counts) / len(skill_hit_counts)
    min_skills = min(skill_hit_counts)
    low_skill = [(o["title"], len(o["skills"])) for o in occupations if len(o["skills"]) < 5]

    logger.info(f"Generated {len(occupations)} occupations")
    logger.info(f"Avg skills/occupation: {avg_skills:.1f}")
    logger.info(f"Min skills: {min_skills}")
    if low_skill:
        logger.info(f"Occupations with <5 skills ({len(low_skill)}):")
        for title, count in low_skill[:10]:
            logger.info(f"  {count} skills: {title}")

    # Unique skills used
    all_used = set()
    for o in occupations:
        all_used.update(o["skills"])
    logger.info(f"Unique skills referenced: {len(all_used)}")

    # Write output
    out_path = base_dir / "occupations.json"
    with open(out_path, "w") as f:
        json.dump(occupations, f, indent=2)
    logger.info(f"Wrote to {out_path}")

    return occupations


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    generate_all()
