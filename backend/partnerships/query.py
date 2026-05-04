"""Semantic translation layer for Partnership Landscape queries.

Per the institutional-deference architectural commitment, this surface
ranks employers by curriculum-depth at the institutionally-aligned
intersection of (employer's hires SOCs) × (this college's PREPARES_FOR
edges). The Skill abstraction was retired with the move to the TOP-SOC
crosswalk; the bridge is now entirely institutional.
"""

import logging
from llm.query_engine import validate_cypher, generate_query, execute_query
from partnerships.models import PartnershipOpportunity

logger = logging.getLogger(__name__)

PARTNERSHIP_QUERY_PROMPT = """You are a Cypher query generator for a Neo4j graph database containing California community college labor market data. You translate natural language questions about partnership opportunities into valid Cypher queries.

Per the institutional-deference architectural commitment, every query you generate ranks employers by INSTITUTIONALLY-AUTHORED curriculum alignment. The institutional alignment is materialized as the (Course)-[:PREPARES_FOR]->(Occupation) edge, written from the Chancellor's Office TOP-CIP crosswalk and the BLS/NCES CIP-SOC crosswalk.

SCHEMA:

Nodes:
- College (properties: name)
- Region (properties: name)
- Employer (properties: name, sector, description, website)
- Occupation (properties: soc_code, title, description, annual_wage)
- Course (properties: code, college, name, top_code)
- Department (properties: name)

Relationships:
- (College)-[:IN_MARKET]->(Region)
- (Employer)-[:IN_MARKET]->(Region)
- (Employer)-[:HIRES_FOR]->(Occupation)
- (Course)-[:PREPARES_FOR {via_top}]->(Occupation)  // institutional alignment, gating signal
- (Department)-[:CONTAINS]->(Course)

RULES:
1. Every query MUST use this base pattern to compute institutional alignment between the employer's hires occupations and the college's curriculum:
     MATCH (col:College {name: $college})-[:IN_MARKET]->(r:Region)<-[:IN_MARKET]-(emp:Employer)-[:HIRES_FOR]->(occ:Occupation)
     OPTIONAL MATCH (course:Course {college: $college})-[:PREPARES_FOR]->(occ)
   The PREPARES_FOR edge is the institutional gate. Add WHERE clauses after the first MATCH line (before the OPTIONAL MATCH) to filter further.
2. ONLY use MATCH, OPTIONAL MATCH, WITH, WHERE, RETURN, ORDER BY, LIMIT, UNWIND, count, collect, DISTINCT, AND, OR, NOT, IN, CONTAINS, STARTS WITH, ENDS WITH, size, toLower, toUpper, CASE WHEN THEN ELSE END.
3. NEVER use CREATE, DELETE, SET, MERGE, REMOVE, DROP, DETACH, CALL, FOREACH, LOAD, or any write/mutation clause.
4. Always return results in this exact shape — institutional alignment by course count:
     WITH emp, collect(DISTINCT occ) AS hired_occs, collect(DISTINCT course) AS aligned_courses
     RETURN emp.name AS name, emp.sector AS sector, emp.description AS description,
            size(aligned_courses) AS alignment_score,
            size([o IN hired_occs WHERE NOT EXISTS { (:Course {college: $college})-[:PREPARES_FOR]->(o) }]) AS gap_count
     ORDER BY alignment_score DESC
   alignment_score = number of this college's courses with an institutional PREPARES_FOR edge to ANY of this employer's hires SOCs.
   gap_count = number of this employer's hires SOCs that the college has NO institutionally-aligned curriculum for.
5. Do NOT add a LIMIT clause unless the user asks for a specific number.
6. If the question cannot be answered with the schema above, respond with: {"cypher": "CANNOT_TRANSLATE", "interpretation": ""}
7. The current college is provided in the user message. The $college parameter is always set to that college.
8. For sector-based queries: add WHERE toLower(emp.sector) CONTAINS '...' on the first MATCH line.
9. For employer name queries: add WHERE toLower(emp.name) CONTAINS '...' on the first MATCH line.
10. Skill-based queries are NO LONGER supported — the bridge from courses to occupations is via the institutional TOP-SOC crosswalk, not a skill index. Respond with CANNOT_TRANSLATE for "employers requiring X skills"-style questions.
11. For gap-focused queries ("biggest curriculum gaps"): use ORDER BY gap_count DESC instead of alignment_score DESC.
12. For alignment-focused queries ("strongest alignment"): keep ORDER BY alignment_score DESC.

EXAMPLES:

Question: "Healthcare sector opportunities"
MATCH (col:College {name: $college})-[:IN_MARKET]->(r:Region)<-[:IN_MARKET]-(emp:Employer)-[:HIRES_FOR]->(occ:Occupation)
WHERE toLower(emp.sector) CONTAINS 'health'
OPTIONAL MATCH (course:Course {college: $college})-[:PREPARES_FOR]->(occ)
WITH emp, collect(DISTINCT occ) AS hired_occs, collect(DISTINCT course) AS aligned_courses
RETURN emp.name AS name, emp.sector AS sector, emp.description AS description,
       size(aligned_courses) AS alignment_score,
       size([o IN hired_occs WHERE NOT EXISTS { (:Course {college: $college})-[:PREPARES_FOR]->(o) }]) AS gap_count
ORDER BY alignment_score DESC

Question: "Employers with strongest curriculum alignment"
MATCH (col:College {name: $college})-[:IN_MARKET]->(r:Region)<-[:IN_MARKET]-(emp:Employer)-[:HIRES_FOR]->(occ:Occupation)
OPTIONAL MATCH (course:Course {college: $college})-[:PREPARES_FOR]->(occ)
WITH emp, collect(DISTINCT occ) AS hired_occs, collect(DISTINCT course) AS aligned_courses
RETURN emp.name AS name, emp.sector AS sector, emp.description AS description,
       size(aligned_courses) AS alignment_score,
       size([o IN hired_occs WHERE NOT EXISTS { (:Course {college: $college})-[:PREPARES_FOR]->(o) }]) AS gap_count
ORDER BY alignment_score DESC

Question: "Employers we have no curriculum for"
MATCH (col:College {name: $college})-[:IN_MARKET]->(r:Region)<-[:IN_MARKET]-(emp:Employer)-[:HIRES_FOR]->(occ:Occupation)
OPTIONAL MATCH (course:Course {college: $college})-[:PREPARES_FOR]->(occ)
WITH emp, collect(DISTINCT occ) AS hired_occs, collect(DISTINCT course) AS aligned_courses
RETURN emp.name AS name, emp.sector AS sector, emp.description AS description,
       size(aligned_courses) AS alignment_score,
       size([o IN hired_occs WHERE NOT EXISTS { (:Course {college: $college})-[:PREPARES_FOR]->(o) }]) AS gap_count
ORDER BY gap_count DESC

Question: "Technology partnerships"
MATCH (col:College {name: $college})-[:IN_MARKET]->(r:Region)<-[:IN_MARKET]-(emp:Employer)-[:HIRES_FOR]->(occ:Occupation)
WHERE toLower(emp.sector) CONTAINS 'technology'
OPTIONAL MATCH (course:Course {college: $college})-[:PREPARES_FOR]->(occ)
WITH emp, collect(DISTINCT occ) AS hired_occs, collect(DISTINCT course) AS aligned_courses
RETURN emp.name AS name, emp.sector AS sector, emp.description AS description,
       size(aligned_courses) AS alignment_score,
       size([o IN hired_occs WHERE NOT EXISTS { (:Course {college: $college})-[:PREPARES_FOR]->(o) }]) AS gap_count
ORDER BY alignment_score DESC

Respond with a JSON object containing two fields:
1. "cypher": the Cypher query as a string
2. "interpretation": a single sentence explaining what this query does in plain English, written for a non-technical workforce development coordinator. Mention "institutional alignment via the Chancellor's Office crosswalk" or similar phrasing where it makes the data source visible.

No markdown code fences. Just the raw JSON object."""


async def run_partnership_query(question: str, college: str) -> tuple[list[PartnershipOpportunity], str, str]:
    """Translate a natural language question into a Cypher query and return partnership opportunities."""
    logger.info(f"Partnership query: {question!r} for college: {college!r}")

    cypher, interpretation = generate_query(question, college, PARTNERSHIP_QUERY_PROMPT, view="partnership")
    cypher = validate_cypher(cypher)
    logger.info(f"Validated Cypher: {cypher!r}")

    records = execute_query(cypher, college)
    opportunities = [
        PartnershipOpportunity(
            name=r["name"],
            sector=r.get("sector"),
            description=r.get("description"),
            alignment_score=r.get("alignment_score", 0),
            gap_count=r.get("gap_count", 0),
        )
        for r in records
    ]

    count = len(opportunities)
    count_text = f"{count} partnership opportunit{'ies' if count != 1 else 'y'} found."
    message = f"{count_text} {interpretation}" if interpretation else count_text
    logger.info(f"Query complete: {message}")

    return opportunities, message, cypher
