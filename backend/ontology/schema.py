import os
import logging
import uuid
import random
from neo4j import GraphDatabase

logger = logging.getLogger(__name__)

_driver = None


def get_driver():
    global _driver
    if _driver is None:
        _driver = GraphDatabase.driver(
            os.environ["NEO4J_URI"],
            auth=(os.environ["NEO4J_USERNAME"], os.environ["NEO4J_PASSWORD"]),
        )
    return _driver


def close_driver():
    global _driver
    if _driver is not None:
        _driver.close()
        _driver = None


def _migrate_curriculum_to_course(session):
    """Idempotent migration: rename Curriculum→Course, create Department nodes."""
    # Check if any Curriculum nodes exist
    count = session.run("MATCH (n:Curriculum) RETURN count(n) AS cnt").single()["cnt"]
    if count == 0:
        return  # Already migrated or fresh DB

    logger.info(f"Migrating {count} Curriculum nodes to Course nodes...")

    # Drop old constraint if it exists
    try:
        session.run("DROP CONSTRAINT curriculum_name IF EXISTS")
    except Exception:
        pass

    # Rename labels
    session.run("MATCH (c:Curriculum) REMOVE c:Curriculum SET c:Course")

    # Create Department nodes from distinct department values
    session.run("""
        MATCH (c:Course)
        WHERE c.department IS NOT NULL
        WITH DISTINCT c.department AS dept
        MERGE (d:Department {name: dept})
    """)

    # Create Department→Course relationships
    session.run("""
        MATCH (c:Course)
        WHERE c.department IS NOT NULL
        MATCH (d:Department {name: c.department})
        MERGE (d)-[:CONTAINS]->(c)
    """)

    # Verify student enrollments still resolve
    student_count = session.run(
        "MATCH (s:Student)-[:ENROLLED_IN]->(c:Course) RETURN count(c) AS cnt"
    ).single()["cnt"]
    logger.info(f"Migration complete. Student enrollments verified: {student_count}")


def init_schema():
    driver = get_driver()
    with driver.session() as session:
        _migrate_curriculum_to_course(session)
        _create_constraints(session)
        if _is_empty(session):
            logger.info("Seeding Neo4j with Sierra Vista Community College data...")
            _seed(session)
            logger.info("Seed complete.")
        else:
            logger.info("Neo4j already contains data, skipping seed.")


def _create_constraints(session):
    # Drop legacy single-field course name constraint (breaks with multi-college data)
    try:
        session.run("DROP CONSTRAINT course_name IF EXISTS")
    except Exception:
        pass

    constraints = [
        "CREATE CONSTRAINT institution_name IF NOT EXISTS FOR (n:Institution) REQUIRE n.name IS UNIQUE",
        "CREATE CONSTRAINT program_name IF NOT EXISTS FOR (n:Program) REQUIRE n.name IS UNIQUE",
        "CREATE CONSTRAINT course_code_inst IF NOT EXISTS FOR (n:Course) REQUIRE (n.code, n.institution) IS UNIQUE",
        "CREATE CONSTRAINT department_name IF NOT EXISTS FOR (n:Department) REQUIRE n.name IS UNIQUE",
        "CREATE CONSTRAINT employer_name IF NOT EXISTS FOR (n:Employer) REQUIRE n.name IS UNIQUE",
        "CREATE CONSTRAINT region_name IF NOT EXISTS FOR (n:LaborMarketRegion) REQUIRE n.name IS UNIQUE",
        "CREATE CONSTRAINT jobrole_title IF NOT EXISTS FOR (n:JobRole) REQUIRE n.title IS UNIQUE",
        "CREATE CONSTRAINT student_uuid IF NOT EXISTS FOR (n:Student) REQUIRE n.uuid IS UNIQUE",
    ]
    for constraint in constraints:
        session.run(constraint)


def _is_empty(session) -> bool:
    result = session.run("MATCH (n:Institution) RETURN count(n) AS cnt")
    return result.single()["cnt"] == 0


def _seed(session):
    # ── Institution & Region ──────────────────────────────────────────────────
    session.run("""
        MERGE (r:LaborMarketRegion {name: 'Inland Empire / San Bernardino'})
        MERGE (i:Institution {
            name: 'Sierra Vista Community College',
            region: 'Inland Empire / San Bernardino',
            city: 'San Bernardino',
            state: 'California'
        })
        MERGE (i)-[:LOCATED_IN]->(r)
    """)

    # ── Programs & Curricula ──────────────────────────────────────────────────
    programs_curricula = {
        "Healthcare Technology": [
            "Medical Assistant Fundamentals",
            "Electronic Health Records & Coding (ICD-10)",
            "Clinical Phlebotomy & Specimen Processing",
            "Patient Communication & Care Ethics",
            "Health Information Management",
        ],
        "Cybersecurity": [
            "Network Security Fundamentals (CompTIA Network+)",
            "Ethical Hacking & Penetration Testing",
            "Security Operations Center (SOC) Analyst Practice",
            "Cloud Security Essentials (AWS/Azure)",
            "Incident Response & Digital Forensics",
        ],
        "Business Administration": [
            "Principles of Accounting I & II",
            "Supply Chain & Logistics Management",
            "Human Resources Management",
            "Business Law & Compliance",
            "Data Analytics for Business",
        ],
        "Manufacturing Technology": [
            "Computer-Aided Manufacturing (CAM/CNC)",
            "Quality Control & Six Sigma Green Belt Prep",
            "Industrial Automation & Robotics",
            "Blueprint Reading & Technical Drawing",
            "Lean Manufacturing Principles",
        ],
        "Early Childhood Education": [
            "Child Development Theory",
            "Curriculum Planning & Learning Environments",
            "Infant/Toddler Care Specialization",
            "Inclusive Practices & Special Needs",
            "Family & Community Engagement",
        ],
    }

    for program_name, curricula in programs_curricula.items():
        session.run("""
            MATCH (i:Institution {name: 'Sierra Vista Community College'})
            MERGE (p:Program {name: $program_name})
            MERGE (i)-[:OFFERS]->(p)
        """, program_name=program_name)

        for course_name in curricula:
            session.run("""
                MATCH (p:Program {name: $program_name})
                MERGE (c:Course {name: $course_name, program: $program_name})
                MERGE (p)-[:CONTAINS]->(c)
            """, program_name=program_name, course_name=course_name)

    # ── Employers & Job Roles ─────────────────────────────────────────────────
    employers_roles = {
        "Amazon Inland Empire Fulfillment Centers": {
            "sector": "Logistics & E-Commerce",
            "roles": [
                "Fulfillment Operations Manager",
                "Inventory Control Analyst",
                "Robotics Maintenance Technician",
                "Logistics Coordinator",
                "Workplace Safety Specialist",
            ],
        },
        "UPS West Coast Hub (Ontario)": {
            "sector": "Transportation & Logistics",
            "roles": [
                "Package Operations Supervisor",
                "Fleet Maintenance Technician",
                "Supply Chain Analyst",
                "Customs & Compliance Specialist",
            ],
        },
        "Arrowhead Regional Medical Center": {
            "sector": "Healthcare",
            "roles": [
                "Medical Assistant",
                "Health Information Specialist",
                "Clinical Lab Technician",
                "Patient Services Coordinator",
            ],
        },
        "Kaiser Permanente Fontana": {
            "sector": "Healthcare",
            "roles": [
                "Medical Records & Coding Specialist",
                "Phlebotomist",
                "Patient Care Technician",
                "Health IT Support Specialist",
            ],
        },
        "Boeing Defense — Victorville": {
            "sector": "Aerospace & Defense Manufacturing",
            "roles": [
                "CNC Machinist",
                "Quality Assurance Inspector",
                "Manufacturing Engineer (Entry Level)",
                "Supply Chain Coordinator",
                "Aerospace Systems Technician",
            ],
        },
        "Stater Bros. Markets": {
            "sector": "Retail & Grocery",
            "roles": [
                "Retail Business Analyst",
                "HR Generalist",
                "Inventory & Procurement Specialist",
                "Store Operations Manager",
            ],
        },
        "Inland Empire Health Plan (IEHP)": {
            "sector": "Managed Care & Health Insurance",
            "roles": [
                "Healthcare Data Analyst",
                "Claims & Compliance Specialist",
                "Community Health Outreach Coordinator",
            ],
        },
        "San Bernardino City Unified School District": {
            "sector": "K-12 Education",
            "roles": [
                "Early Childhood Education Teacher",
                "Site Supervisor",
                "Instructional Aide (Special Education)",
                "Family Liaison",
            ],
        },
        "Loma Linda University Health": {
            "sector": "Academic Healthcare",
            "roles": [
                "Medical Assistant",
                "Health Information Technician",
                "Cybersecurity Analyst (Health IT)",
                "Clinical Lab Technician",
            ],
        },
        "Esri": {
            "sector": "Geographic Information Systems & Technology",
            "roles": [
                "IT Support Specialist",
                "Cloud Infrastructure Analyst",
                "Data Quality Analyst",
                "Cybersecurity Engineer",
            ],
        },
    }

    for employer_name, data in employers_roles.items():
        session.run("""
            MATCH (r:LaborMarketRegion {name: 'Inland Empire / San Bernardino'})
            MERGE (e:Employer {name: $employer_name, sector: $sector})
            MERGE (e)-[:OPERATES_IN]->(r)
        """, employer_name=employer_name, sector=data["sector"])

        for role_title in data["roles"]:
            session.run("""
                MATCH (e:Employer {name: $employer_name})
                MERGE (j:JobRole {title: $title})
                MERGE (e)-[:REQUIRES]->(j)
            """, employer_name=employer_name, title=role_title)

    # ── Curriculum Properties (course codes, departments, skills) ────────────
    curriculum_details = {
        "Medical Assistant Fundamentals": {
            "code": "HIT 101", "department": "Healthcare Technology",
            "learning_outcomes": ["Perform clinical procedures", "Apply medical terminology", "Document patient encounters"],
            "skill_mappings": ["Clinical Skills", "Communication", "Information Management"],
        },
        "Electronic Health Records & Coding (ICD-10)": {
            "code": "HIT 102", "department": "Healthcare Technology",
            "learning_outcomes": ["Navigate EHR systems", "Apply ICD-10 coding standards", "Ensure HIPAA compliance"],
            "skill_mappings": ["Information Management", "Regulatory Compliance", "Data Analysis"],
        },
        "Clinical Phlebotomy & Specimen Processing": {
            "code": "HIT 103", "department": "Healthcare Technology",
            "learning_outcomes": ["Perform venipuncture", "Process laboratory specimens", "Follow safety protocols"],
            "skill_mappings": ["Clinical Skills", "Quality Assurance", "Safety Compliance"],
        },
        "Patient Communication & Care Ethics": {
            "code": "HIT 104", "department": "Healthcare Technology",
            "learning_outcomes": ["Communicate with diverse patients", "Apply ethical frameworks", "Manage confidentiality"],
            "skill_mappings": ["Communication", "Critical Thinking", "Regulatory Compliance"],
        },
        "Health Information Management": {
            "code": "HIT 105", "department": "Healthcare Technology",
            "learning_outcomes": ["Manage health records systems", "Analyze health data quality", "Implement data governance"],
            "skill_mappings": ["Information Management", "Data Analysis", "Quality Assurance"],
        },
        "Network Security Fundamentals (CompTIA Network+)": {
            "code": "CYB 101", "department": "Cybersecurity",
            "learning_outcomes": ["Configure network security", "Identify vulnerabilities", "Implement access controls"],
            "skill_mappings": ["Technical Security", "Problem Solving", "Critical Thinking"],
        },
        "Ethical Hacking & Penetration Testing": {
            "code": "CYB 102", "department": "Cybersecurity",
            "learning_outcomes": ["Conduct penetration tests", "Document security findings", "Apply ethical frameworks"],
            "skill_mappings": ["Technical Security", "Problem Solving", "Communication"],
        },
        "Security Operations Center (SOC) Analyst Practice": {
            "code": "CYB 103", "department": "Cybersecurity",
            "learning_outcomes": ["Monitor security events", "Analyze threat intelligence", "Respond to incidents"],
            "skill_mappings": ["Technical Security", "Data Analysis", "Critical Thinking"],
        },
        "Cloud Security Essentials (AWS/Azure)": {
            "code": "CYB 104", "department": "Cybersecurity",
            "learning_outcomes": ["Secure cloud infrastructure", "Implement IAM policies", "Audit cloud configurations"],
            "skill_mappings": ["Technical Security", "Information Management", "Problem Solving"],
        },
        "Incident Response & Digital Forensics": {
            "code": "CYB 105", "department": "Cybersecurity",
            "learning_outcomes": ["Investigate security incidents", "Preserve digital evidence", "Write forensic reports"],
            "skill_mappings": ["Technical Security", "Data Analysis", "Communication"],
        },
        "Principles of Accounting I & II": {
            "code": "BUS 101", "department": "Business Administration",
            "learning_outcomes": ["Prepare financial statements", "Apply GAAP principles", "Analyze transactions"],
            "skill_mappings": ["Quantitative Reasoning", "Critical Thinking", "Information Management"],
        },
        "Supply Chain & Logistics Management": {
            "code": "BUS 102", "department": "Business Administration",
            "learning_outcomes": ["Optimize supply chains", "Manage inventory systems", "Analyze logistics data"],
            "skill_mappings": ["Problem Solving", "Data Analysis", "Quantitative Reasoning"],
        },
        "Human Resources Management": {
            "code": "BUS 103", "department": "Business Administration",
            "learning_outcomes": ["Apply employment law", "Manage talent acquisition", "Design training programs"],
            "skill_mappings": ["Communication", "Critical Thinking", "Regulatory Compliance"],
        },
        "Business Law & Compliance": {
            "code": "BUS 104", "department": "Business Administration",
            "learning_outcomes": ["Interpret business regulations", "Assess legal risk", "Ensure organizational compliance"],
            "skill_mappings": ["Critical Thinking", "Regulatory Compliance", "Communication"],
        },
        "Data Analytics for Business": {
            "code": "BUS 105", "department": "Business Administration",
            "learning_outcomes": ["Analyze business datasets", "Create data visualizations", "Derive actionable insights"],
            "skill_mappings": ["Data Analysis", "Quantitative Reasoning", "Problem Solving"],
        },
        "Computer-Aided Manufacturing (CAM/CNC)": {
            "code": "MFG 101", "department": "Manufacturing Technology",
            "learning_outcomes": ["Program CNC machines", "Read technical specifications", "Optimize machining processes"],
            "skill_mappings": ["Technical Manufacturing", "Problem Solving", "Quality Assurance"],
        },
        "Quality Control & Six Sigma Green Belt Prep": {
            "code": "MFG 102", "department": "Manufacturing Technology",
            "learning_outcomes": ["Apply statistical process control", "Conduct quality audits", "Implement DMAIC methodology"],
            "skill_mappings": ["Quality Assurance", "Data Analysis", "Quantitative Reasoning"],
        },
        "Industrial Automation & Robotics": {
            "code": "MFG 103", "department": "Manufacturing Technology",
            "learning_outcomes": ["Program industrial robots", "Design automated systems", "Troubleshoot PLCs"],
            "skill_mappings": ["Technical Manufacturing", "Problem Solving", "Critical Thinking"],
        },
        "Blueprint Reading & Technical Drawing": {
            "code": "MFG 104", "department": "Manufacturing Technology",
            "learning_outcomes": ["Interpret engineering drawings", "Apply GD&T standards", "Create technical sketches"],
            "skill_mappings": ["Technical Manufacturing", "Communication", "Critical Thinking"],
        },
        "Lean Manufacturing Principles": {
            "code": "MFG 105", "department": "Manufacturing Technology",
            "learning_outcomes": ["Apply lean methodologies", "Eliminate waste in processes", "Facilitate continuous improvement"],
            "skill_mappings": ["Problem Solving", "Critical Thinking", "Quality Assurance"],
        },
        "Child Development Theory": {
            "code": "ECE 101", "department": "Early Childhood Education",
            "learning_outcomes": ["Analyze developmental theories", "Observe child behavior", "Apply age-appropriate practices"],
            "skill_mappings": ["Critical Thinking", "Communication", "Clinical Skills"],
        },
        "Curriculum Planning & Learning Environments": {
            "code": "ECE 102", "department": "Early Childhood Education",
            "learning_outcomes": ["Design learning activities", "Create inclusive environments", "Assess learning outcomes"],
            "skill_mappings": ["Communication", "Critical Thinking", "Problem Solving"],
        },
        "Infant/Toddler Care Specialization": {
            "code": "ECE 103", "department": "Early Childhood Education",
            "learning_outcomes": ["Provide responsive caregiving", "Manage health and safety protocols", "Support attachment development"],
            "skill_mappings": ["Clinical Skills", "Safety Compliance", "Communication"],
        },
        "Inclusive Practices & Special Needs": {
            "code": "ECE 104", "department": "Early Childhood Education",
            "learning_outcomes": ["Adapt curricula for diverse learners", "Collaborate with specialists", "Implement IEP objectives"],
            "skill_mappings": ["Communication", "Critical Thinking", "Regulatory Compliance"],
        },
        "Family & Community Engagement": {
            "code": "ECE 105", "department": "Early Childhood Education",
            "learning_outcomes": ["Build family partnerships", "Connect families to resources", "Facilitate community collaboration"],
            "skill_mappings": ["Communication", "Critical Thinking", "Problem Solving"],
        },
    }

    for course_name, details in curriculum_details.items():
        session.run("""
            MATCH (c:Course {name: $name})
            SET c.code = $code,
                c.department = $department,
                c.learning_outcomes = $learning_outcomes,
                c.skill_mappings = $skill_mappings
        """, name=course_name, **details)

    # ── Department nodes ─────────────────────────────────────────────────────
    session.run("""
        MATCH (c:Course)
        WHERE c.department IS NOT NULL
        WITH DISTINCT c.department AS dept
        MERGE (d:Department {name: dept})
    """)
    session.run("""
        MATCH (c:Course)
        WHERE c.department IS NOT NULL
        MATCH (d:Department {name: c.department})
        MERGE (d)-[:CONTAINS]->(c)
    """)

    # ── Anonymous Students with Enrollments ──────────────────────────────────
    terms = ["Fall 2023", "Spring 2024", "Fall 2024", "Spring 2025"]
    grades = ["A", "A", "B", "B", "B", "C", "C", "C", "C", "D", "F", "W"]  # weighted distribution
    all_curricula = list(curriculum_details.keys())

    random.seed(42)  # deterministic for reproducibility

    for _ in range(50):
        student_uuid = str(uuid.uuid4())
        session.run("CREATE (s:Student {uuid: $uuid})", uuid=student_uuid)

        num_courses = random.randint(5, 12)
        selected = random.sample(all_curricula, min(num_courses, len(all_curricula)))

        for course_name in selected:
            term = random.choice(terms)
            grade = random.choice(grades)
            status = "Withdrawn" if grade == "W" else "Completed"

            session.run("""
                MATCH (s:Student {uuid: $uuid})
                MATCH (c:Course {name: $course_name})
                CREATE (s)-[:ENROLLED_IN {grade: $grade, term: $term, status: $status}]->(c)
            """, uuid=student_uuid, course_name=course_name, grade=grade, term=term, status=status)
