import os
import logging
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


def init_schema():
    driver = get_driver()
    with driver.session() as session:
        _create_constraints(session)
        if _is_empty(session):
            logger.info("Seeding Neo4j with Sierra Vista Community College data...")
            _seed(session)
            logger.info("Seed complete.")
        else:
            logger.info("Neo4j already contains data, skipping seed.")


def _create_constraints(session):
    constraints = [
        "CREATE CONSTRAINT institution_name IF NOT EXISTS FOR (n:Institution) REQUIRE n.name IS UNIQUE",
        "CREATE CONSTRAINT program_name IF NOT EXISTS FOR (n:Program) REQUIRE n.name IS UNIQUE",
        "CREATE CONSTRAINT curriculum_name IF NOT EXISTS FOR (n:Curriculum) REQUIRE n.name IS UNIQUE",
        "CREATE CONSTRAINT employer_name IF NOT EXISTS FOR (n:Employer) REQUIRE n.name IS UNIQUE",
        "CREATE CONSTRAINT region_name IF NOT EXISTS FOR (n:LaborMarketRegion) REQUIRE n.name IS UNIQUE",
        "CREATE CONSTRAINT jobrole_title IF NOT EXISTS FOR (n:JobRole) REQUIRE n.title IS UNIQUE",
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

        for curriculum_name in curricula:
            session.run("""
                MATCH (p:Program {name: $program_name})
                MERGE (c:Curriculum {name: $curriculum_name, program: $program_name})
                MERGE (p)-[:CONTAINS]->(c)
            """, program_name=program_name, curriculum_name=curriculum_name)

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
