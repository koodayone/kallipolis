"""
Employer data loader for a college's labor market region.

Populates Neo4j with regional employers, their sectors, and job roles.
Idempotent via MERGE — safe to re-run.

Usage:
    from pipeline.employers import load_employers
    load_employers(driver, "San Francisco Bay Area")
"""

from __future__ import annotations

import logging
from typing import Dict, List

from neo4j import Driver

logger = logging.getLogger(__name__)

# ── Bay Area employers relevant to Foothill College programs ───────────────────

BAY_AREA_EMPLOYERS: Dict[str, dict] = {
    "Stanford Health Care": {
        "sector": "Healthcare",
        "roles": [
            "Respiratory Therapist",
            "Radiologic Technologist",
            "Dental Hygienist",
            "Medical Laboratory Technician",
            "Patient Care Coordinator",
        ],
    },
    "Kaiser Permanente (Santa Clara)": {
        "sector": "Healthcare",
        "roles": [
            "Pharmacy Technician",
            "Emergency Medical Technician",
            "Health Information Specialist",
            "Medical Assistant",
            "Clinical Lab Scientist",
        ],
    },
    "Apple": {
        "sector": "Technology",
        "roles": [
            "Software Engineer",
            "UX/UI Designer",
            "Data Analyst",
            "Hardware Test Technician",
            "IT Support Specialist",
        ],
    },
    "Google": {
        "sector": "Technology",
        "roles": [
            "Software Developer",
            "Cloud Solutions Architect",
            "Data Scientist",
            "Technical Program Manager",
        ],
    },
    "Lockheed Martin (Sunnyvale)": {
        "sector": "Aerospace & Defense",
        "roles": [
            "Systems Engineer",
            "Cybersecurity Analyst",
            "Manufacturing Technician",
            "Quality Assurance Inspector",
            "Electrical Engineer",
        ],
    },
    "Palo Alto Unified School District": {
        "sector": "K-12 Education",
        "roles": [
            "Early Childhood Education Teacher",
            "Instructional Aide",
            "School Counselor",
            "Special Education Paraprofessional",
        ],
    },
    "El Camino Health": {
        "sector": "Healthcare",
        "roles": [
            "Respiratory Care Practitioner",
            "Diagnostic Medical Sonographer",
            "Radiologic Technologist",
            "Registered Nurse",
        ],
    },
    "Broadcom": {
        "sector": "Technology",
        "roles": [
            "Network Engineer",
            "Software QA Engineer",
            "Systems Administrator",
            "Technical Writer",
        ],
    },
    "Foothill-De Anza Community College District": {
        "sector": "Higher Education",
        "roles": [
            "Instructional Designer",
            "Academic Counselor",
            "Child Development Center Teacher",
            "IT Systems Analyst",
        ],
    },
    "Tesla (Fremont)": {
        "sector": "Manufacturing & Technology",
        "roles": [
            "Production Technician",
            "Automation Engineer",
            "Supply Chain Analyst",
            "Quality Control Inspector",
            "Electrical Systems Technician",
        ],
    },
    "Stanford University": {
        "sector": "Higher Education & Research",
        "roles": [
            "Research Laboratory Technician",
            "Veterinary Technician",
            "Environmental Health & Safety Specialist",
            "IT Support Analyst",
        ],
    },
    "Sutter Health (Palo Alto)": {
        "sector": "Healthcare",
        "roles": [
            "Dental Hygienist",
            "Pharmacy Technician",
            "Health Information Technician",
            "Patient Services Representative",
        ],
    },
}

# Registry of employer sets by region (extensible for other colleges)
EMPLOYER_REGISTRY: Dict[str, Dict[str, dict]] = {
    "San Francisco Bay Area": BAY_AREA_EMPLOYERS,
}


def load_employers(driver: Driver, region: str) -> int:
    """
    Load employers for a labor market region into Neo4j.
    Idempotent via MERGE.

    Returns the number of employers loaded.
    """
    employers = EMPLOYER_REGISTRY.get(region)
    if not employers:
        logger.warning(f"No employer data for region: {region}")
        return 0

    with driver.session() as session:
        # Ensure region exists
        session.run("MERGE (r:LaborMarketRegion {name: $region})", region=region)

        loaded = 0
        for employer_name, data in employers.items():
            session.run(
                """
                MATCH (r:LaborMarketRegion {name: $region})
                MERGE (e:Employer {name: $name})
                ON CREATE SET e.sector = $sector
                ON MATCH SET e.sector = $sector
                MERGE (e)-[:OPERATES_IN]->(r)
                """,
                region=region,
                name=employer_name,
                sector=data["sector"],
            )

            for role_title in data["roles"]:
                session.run(
                    """
                    MATCH (e:Employer {name: $employer})
                    MERGE (j:JobRole {title: $title})
                    MERGE (e)-[:REQUIRES]->(j)
                    """,
                    employer=employer_name,
                    title=role_title,
                )

            loaded += 1

        logger.info(f"Loaded {loaded} employers for {region}")
        return loaded
