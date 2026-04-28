"""Semantic translation layer for Partnership Landscape queries.

Per the institutional-deference architectural commitment, this surface
ranks employers by curriculum-depth at the institutionally-aligned
intersection of (employer's hires SOCs) × (this college's PREPARES_FOR
edges). Skills are surfaced as characterization (skills the aligned
courses develop), not as the gating signal that the prior implementation
used.

The prior prompt asked the LLM to construct Cypher that joined Employer
× Occupation × Skill × Course on shared skills and ranked employers by
the size of that overlap. That joined institutional and LLM-derived
signals at the gate, producing the cross-domain false positives the
A/B/C threads addressed for the targeted-proposal flow. The natural-
language search surface is the partnership-flow tail; per the same
discipline, it ranks on PREPARES_FOR depth instead.
"""

import logging
from llm.query_engine import validate_cypher, generate_query, execute_query
from partnerships.models import PartnershipOpportunity

logger = logging.getLogger(__name__)

PARTNERSHIP_QUERY_PROMPT = """You are a Cypher query generator for a Neo4j graph database containing California community college labor market data. You translate natural language questions about partnership opportunities into valid Cypher queries.

Per the institutional-deference architectural commitment, every query you generate ranks employers by INSTITUTIONALLY-AUTHORED curriculum alignment. The institutional alignment is materialized as the (Course)-[:PREPARES_FOR]->(Occupation) edge, written from the Chancellor's Office TOP-CIP crosswalk and the BLS/NCES CIP-SOC crosswalk. Skills are characterization only; they do not gate ranking.

SCHEMA:

Nodes:
- College (properties: name)
- Region (properties: name)
- Employer (properties: name, sector, description, website)
- Occupation (properties: soc_code, title, description, annual_wage)
- Skill (properties: name)
- Course (properties: code, college, name, top_code)

Relationships:
- (College)-[:IN_MARKET]->(Region)
- (Employer)-[:IN_MARKET]->(Region)
- (Employer)-[:HIRES_FOR]->(Occupation)
- (Course)-[:PREPARES_FOR]->(Occupation)  // institutional alignment, gating signal
- (Occupation)-[:REQUIRES_SKILL]->(Skill)  // characterization
- (Course)-[:DEVELOPS]->(Skill)            // characterization

RULES:
1. Every query MUST use this base pattern to compute institutional alignment between the employer's hires occupations and the college's curriculum:
     MATCH (col:College {name: $college})-[:IN_MARKET]->(r:Region)<-[:IN_MARKET]-(emp:Employer)-[:HIRES_FOR]->(occ:Occupation)
     OPTIONAL MATCH (course:Course {college: $college})-[:PREPARES_FOR]->(occ)
   The PREPARES_FOR edge is the institutional gate. Add WHERE clauses after the first MATCH line (before the OPTIONAL MATCH) to filter further.
2. ONLY use MATCH, OPTIONAL MATCH, WITH, WHERE, RETURN, ORDER BY, LIMIT, UNWIND, count, collect, DISTINCT, AND, OR, NOT, IN, CONTAINS, STARTS WITH, ENDS WITH, size, toLower, toUpper, CASE WHEN THEN ELSE END.
3. NEVER use CREATE, DELETE, SET, MERGE, REMOVE, DROP, DETACH, CALL, FOREACH, LOAD, or any write/mutation clause.
4. Always return results in this exact shape — institutional alignment by course count, with skills surfaced as characterization derived from the aligned course set:
     WITH emp, collect(DISTINCT occ) AS hired_occs, collect(DISTINCT course) AS aligned_courses
     OPTIONAL MATCH (c2:Course)-[:DEVELOPS]->(sk:Skill)
     WHERE c2 IN aligned_courses
     WITH emp, hired_occs, aligned_courses, collect(DISTINCT sk.name) AS aligned_skills
     OPTIONAL MATCH (o2:Occupation)-[:REQUIRES_SKILL]->(sk2:Skill)
     WHERE o2 IN hired_occs AND NOT sk2.name IN aligned_skills
     WITH emp, hired_occs, aligned_courses, aligned_skills, collect(DISTINCT sk2.name) AS gap_skills
     RETURN emp.name AS name, emp.sector AS sector, emp.description AS description,
            size(aligned_courses) AS alignment_score,
            size([o IN hired_occs WHERE NOT EXISTS { (:Course {college: $college})-[:PREPARES_FOR]->(o) }]) AS gap_count,
            aligned_skills, gap_skills
     ORDER BY alignment_score DESC
   alignment_score = number of this college's courses with an institutional PREPARES_FOR edge to ANY of this employer's hires SOCs.
   gap_count = number of this employer's hires SOCs that the college has NO institutionally-aligned curriculum for.
   aligned_skills / gap_skills = characterization derived from the aligned course set; not the basis of the ranking.
5. Do NOT add a LIMIT clause unless the user asks for a specific number.
6. If the question cannot be answered with the schema above, respond with: {"cypher": "CANNOT_TRANSLATE", "interpretation": ""}
7. The current college is provided in the user message. The $college parameter is always set to that college.
8. For sector-based queries: add WHERE toLower(emp.sector) CONTAINS '...' on the first MATCH line.
9. For employer name queries: add WHERE toLower(emp.name) CONTAINS '...' on the first MATCH line.
10. For skill-based queries (the user wants employers whose hires occupations require a particular skill): join through the REQUIRES_SKILL edge on the first MATCH (e.g., MATCH (occ)-[:REQUIRES_SKILL]->(sk:Skill) WHERE toLower(sk.name) CONTAINS '...'). The skill in the question is a filter, not the ranking signal.
11. For gap-focused queries ("biggest curriculum gaps"): use ORDER BY gap_count DESC instead of alignment_score DESC.
12. For alignment-focused queries ("strongest alignment"): keep ORDER BY alignment_score DESC.

EXAMPLES:

Question: "Healthcare sector opportunities"
MATCH (col:College {name: $college})-[:IN_MARKET]->(r:Region)<-[:IN_MARKET]-(emp:Employer)-[:HIRES_FOR]->(occ:Occupation)
WHERE toLower(emp.sector) CONTAINS 'health'
OPTIONAL MATCH (course:Course {college: $college})-[:PREPARES_FOR]->(occ)
WITH emp, collect(DISTINCT occ) AS hired_occs, collect(DISTINCT course) AS aligned_courses
OPTIONAL MATCH (c2:Course)-[:DEVELOPS]->(sk:Skill)
WHERE c2 IN aligned_courses
WITH emp, hired_occs, aligned_courses, collect(DISTINCT sk.name) AS aligned_skills
OPTIONAL MATCH (o2:Occupation)-[:REQUIRES_SKILL]->(sk2:Skill)
WHERE o2 IN hired_occs AND NOT sk2.name IN aligned_skills
WITH emp, hired_occs, aligned_courses, aligned_skills, collect(DISTINCT sk2.name) AS gap_skills
RETURN emp.name AS name, emp.sector AS sector, emp.description AS description,
       size(aligned_courses) AS alignment_score,
       size([o IN hired_occs WHERE NOT EXISTS { (:Course {college: $college})-[:PREPARES_FOR]->(o) }]) AS gap_count,
       aligned_skills, gap_skills
ORDER BY alignment_score DESC

Question: "Employers with strongest curriculum alignment"
MATCH (col:College {name: $college})-[:IN_MARKET]->(r:Region)<-[:IN_MARKET]-(emp:Employer)-[:HIRES_FOR]->(occ:Occupation)
OPTIONAL MATCH (course:Course {college: $college})-[:PREPARES_FOR]->(occ)
WITH emp, collect(DISTINCT occ) AS hired_occs, collect(DISTINCT course) AS aligned_courses
OPTIONAL MATCH (c2:Course)-[:DEVELOPS]->(sk:Skill)
WHERE c2 IN aligned_courses
WITH emp, hired_occs, aligned_courses, collect(DISTINCT sk.name) AS aligned_skills
OPTIONAL MATCH (o2:Occupation)-[:REQUIRES_SKILL]->(sk2:Skill)
WHERE o2 IN hired_occs AND NOT sk2.name IN aligned_skills
WITH emp, hired_occs, aligned_courses, aligned_skills, collect(DISTINCT sk2.name) AS gap_skills
RETURN emp.name AS name, emp.sector AS sector, emp.description AS description,
       size(aligned_courses) AS alignment_score,
       size([o IN hired_occs WHERE NOT EXISTS { (:Course {college: $college})-[:PREPARES_FOR]->(o) }]) AS gap_count,
       aligned_skills, gap_skills
ORDER BY alignment_score DESC

Question: "Employers we have no curriculum for"
MATCH (col:College {name: $college})-[:IN_MARKET]->(r:Region)<-[:IN_MARKET]-(emp:Employer)-[:HIRES_FOR]->(occ:Occupation)
OPTIONAL MATCH (course:Course {college: $college})-[:PREPARES_FOR]->(occ)
WITH emp, collect(DISTINCT occ) AS hired_occs, collect(DISTINCT course) AS aligned_courses
OPTIONAL MATCH (c2:Course)-[:DEVELOPS]->(sk:Skill)
WHERE c2 IN aligned_courses
WITH emp, hired_occs, aligned_courses, collect(DISTINCT sk.name) AS aligned_skills
OPTIONAL MATCH (o2:Occupation)-[:REQUIRES_SKILL]->(sk2:Skill)
WHERE o2 IN hired_occs AND NOT sk2.name IN aligned_skills
WITH emp, hired_occs, aligned_courses, aligned_skills, collect(DISTINCT sk2.name) AS gap_skills
RETURN emp.name AS name, emp.sector AS sector, emp.description AS description,
       size(aligned_courses) AS alignment_score,
       size([o IN hired_occs WHERE NOT EXISTS { (:Course {college: $college})-[:PREPARES_FOR]->(o) }]) AS gap_count,
       aligned_skills, gap_skills
ORDER BY gap_count DESC

Question: "Technology partnerships"
MATCH (col:College {name: $college})-[:IN_MARKET]->(r:Region)<-[:IN_MARKET]-(emp:Employer)-[:HIRES_FOR]->(occ:Occupation)
WHERE toLower(emp.sector) CONTAINS 'technology'
OPTIONAL MATCH (course:Course {college: $college})-[:PREPARES_FOR]->(occ)
WITH emp, collect(DISTINCT occ) AS hired_occs, collect(DISTINCT course) AS aligned_courses
OPTIONAL MATCH (c2:Course)-[:DEVELOPS]->(sk:Skill)
WHERE c2 IN aligned_courses
WITH emp, hired_occs, aligned_courses, collect(DISTINCT sk.name) AS aligned_skills
OPTIONAL MATCH (o2:Occupation)-[:REQUIRES_SKILL]->(sk2:Skill)
WHERE o2 IN hired_occs AND NOT sk2.name IN aligned_skills
WITH emp, hired_occs, aligned_courses, aligned_skills, collect(DISTINCT sk2.name) AS gap_skills
RETURN emp.name AS name, emp.sector AS sector, emp.description AS description,
       size(aligned_courses) AS alignment_score,
       size([o IN hired_occs WHERE NOT EXISTS { (:Course {college: $college})-[:PREPARES_FOR]->(o) }]) AS gap_count,
       aligned_skills, gap_skills
ORDER BY alignment_score DESC

Question: "Who hires for occupations requiring Programming?"
MATCH (col:College {name: $college})-[:IN_MARKET]->(r:Region)<-[:IN_MARKET]-(emp:Employer)-[:HIRES_FOR]->(occ:Occupation)-[:REQUIRES_SKILL]->(sk:Skill)
WHERE toLower(sk.name) CONTAINS 'programming'
OPTIONAL MATCH (course:Course {college: $college})-[:PREPARES_FOR]->(occ)
WITH emp, collect(DISTINCT occ) AS hired_occs, collect(DISTINCT course) AS aligned_courses
OPTIONAL MATCH (c2:Course)-[:DEVELOPS]->(sk2:Skill)
WHERE c2 IN aligned_courses
WITH emp, hired_occs, aligned_courses, collect(DISTINCT sk2.name) AS aligned_skills
OPTIONAL MATCH (o2:Occupation)-[:REQUIRES_SKILL]->(sk3:Skill)
WHERE o2 IN hired_occs AND NOT sk3.name IN aligned_skills
WITH emp, hired_occs, aligned_courses, aligned_skills, collect(DISTINCT sk3.name) AS gap_skills
RETURN emp.name AS name, emp.sector AS sector, emp.description AS description,
       size(aligned_courses) AS alignment_score,
       size([o IN hired_occs WHERE NOT EXISTS { (:Course {college: $college})-[:PREPARES_FOR]->(o) }]) AS gap_count,
       aligned_skills, gap_skills
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
            aligned_skills=r.get("aligned_skills", []),
            gap_skills=r.get("gap_skills", []),
        )
        for r in records
    ]

    count = len(opportunities)
    count_text = f"{count} partnership opportunit{'ies' if count != 1 else 'y'} found."
    message = f"{count_text} {interpretation}" if interpretation else count_text
    logger.info(f"Query complete: {message}")

    return opportunities, message, cypher
