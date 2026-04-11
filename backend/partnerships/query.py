"""Semantic translation layer for Partnership Landscape queries."""

import logging
from llm.query_engine import validate_cypher, generate_query, execute_query
from partnerships.models import PartnershipOpportunity

logger = logging.getLogger(__name__)

PARTNERSHIP_QUERY_PROMPT = """You are a Cypher query generator for a Neo4j graph database containing California community college labor market data. You translate natural language questions about partnership opportunities into valid Cypher queries.

SCHEMA:

Nodes:
- College (properties: name)
- Region (properties: name)
- Employer (properties: name, sector, description, website)
- Occupation (properties: soc_code, title, description, annual_wage)
- Skill (properties: name)
- Course (properties: code, college, name)

Relationships:
- (College)-[:IN_MARKET]->(Region)
- (Employer)-[:IN_MARKET]->(Region)
- (Employer)-[:HIRES_FOR]->(Occupation)
- (Occupation)-[:REQUIRES_SKILL]->(Skill)
- (Course)-[:DEVELOPS]->(Skill)

RULES:
1. Every query MUST use this base pattern to compute skill alignment and gaps between the employer and the college's curriculum:
     MATCH (col:College {name: $college})-[:IN_MARKET]->(r:Region)<-[:IN_MARKET]-(emp:Employer)-[:HIRES_FOR]->(occ:Occupation)-[:REQUIRES_SKILL]->(sk:Skill)
     OPTIONAL MATCH (course:Course {college: $college})-[:DEVELOPS]->(sk)
   Add WHERE clauses after the first MATCH line (before the OPTIONAL MATCH) to filter further.
2. ONLY use MATCH, OPTIONAL MATCH, WITH, WHERE, RETURN, ORDER BY, LIMIT, UNWIND, count, collect, DISTINCT, AND, OR, NOT, IN, CONTAINS, STARTS WITH, ENDS WITH, size, toLower, toUpper, CASE WHEN THEN ELSE END.
3. NEVER use CREATE, DELETE, SET, MERGE, REMOVE, DROP, DETACH, CALL, FOREACH, LOAD, or any write/mutation clause.
4. Always return results in this exact shape:
     WITH emp, sk, occ,
          CASE WHEN count(course) > 0 THEN true ELSE false END AS developed
     WITH emp,
          collect(DISTINCT CASE WHEN developed THEN sk.name END) AS raw_aligned,
          collect(DISTINCT CASE WHEN NOT developed THEN sk.name END) AS raw_gaps
     WITH emp,
          [x IN raw_aligned WHERE x IS NOT NULL] AS aligned_skills,
          [x IN raw_gaps WHERE x IS NOT NULL] AS gap_skills
     RETURN emp.name AS name, emp.sector AS sector, emp.description AS description,
            size(aligned_skills) AS alignment_score,
            size(gap_skills) AS gap_count,
            aligned_skills, gap_skills
     ORDER BY alignment_score DESC
5. Do NOT add a LIMIT clause unless the user asks for a specific number.
6. If the question cannot be answered with the schema above, respond with: {"cypher": "CANNOT_TRANSLATE", "interpretation": ""}
7. The current college is provided in the user message. The $college parameter is always set to that college.
8. For sector-based queries: add WHERE toLower(emp.sector) CONTAINS '...' on the first MATCH line.
9. For employer name queries: add WHERE toLower(emp.name) CONTAINS '...' on the first MATCH line.
10. For skill-based queries: add WHERE toLower(sk.name) CONTAINS '...' on the first MATCH line.
11. For gap-focused queries ("biggest skill gaps"): use ORDER BY gap_count DESC instead of alignment_score DESC.
12. For alignment-focused queries ("strongest alignment"): keep ORDER BY alignment_score DESC.

EXAMPLES:

Question: "Healthcare sector opportunities"
MATCH (col:College {name: $college})-[:IN_MARKET]->(r:Region)<-[:IN_MARKET]-(emp:Employer)-[:HIRES_FOR]->(occ:Occupation)-[:REQUIRES_SKILL]->(sk:Skill)
WHERE toLower(emp.sector) CONTAINS 'health'
OPTIONAL MATCH (course:Course {college: $college})-[:DEVELOPS]->(sk)
WITH emp, sk, occ,
     CASE WHEN count(course) > 0 THEN true ELSE false END AS developed
WITH emp,
     collect(DISTINCT CASE WHEN developed THEN sk.name END) AS raw_aligned,
     collect(DISTINCT CASE WHEN NOT developed THEN sk.name END) AS raw_gaps
WITH emp,
     [x IN raw_aligned WHERE x IS NOT NULL] AS aligned_skills,
     [x IN raw_gaps WHERE x IS NOT NULL] AS gap_skills
RETURN emp.name AS name, emp.sector AS sector, emp.description AS description,
       size(aligned_skills) AS alignment_score,
       size(gap_skills) AS gap_count,
       aligned_skills, gap_skills
ORDER BY alignment_score DESC

Question: "Employers with strongest alignment"
MATCH (col:College {name: $college})-[:IN_MARKET]->(r:Region)<-[:IN_MARKET]-(emp:Employer)-[:HIRES_FOR]->(occ:Occupation)-[:REQUIRES_SKILL]->(sk:Skill)
OPTIONAL MATCH (course:Course {college: $college})-[:DEVELOPS]->(sk)
WITH emp, sk, occ,
     CASE WHEN count(course) > 0 THEN true ELSE false END AS developed
WITH emp,
     collect(DISTINCT CASE WHEN developed THEN sk.name END) AS raw_aligned,
     collect(DISTINCT CASE WHEN NOT developed THEN sk.name END) AS raw_gaps
WITH emp,
     [x IN raw_aligned WHERE x IS NOT NULL] AS aligned_skills,
     [x IN raw_gaps WHERE x IS NOT NULL] AS gap_skills
RETURN emp.name AS name, emp.sector AS sector, emp.description AS description,
       size(aligned_skills) AS alignment_score,
       size(gap_skills) AS gap_count,
       aligned_skills, gap_skills
ORDER BY alignment_score DESC

Question: "Biggest skill gaps to close"
MATCH (col:College {name: $college})-[:IN_MARKET]->(r:Region)<-[:IN_MARKET]-(emp:Employer)-[:HIRES_FOR]->(occ:Occupation)-[:REQUIRES_SKILL]->(sk:Skill)
OPTIONAL MATCH (course:Course {college: $college})-[:DEVELOPS]->(sk)
WITH emp, sk, occ,
     CASE WHEN count(course) > 0 THEN true ELSE false END AS developed
WITH emp,
     collect(DISTINCT CASE WHEN developed THEN sk.name END) AS raw_aligned,
     collect(DISTINCT CASE WHEN NOT developed THEN sk.name END) AS raw_gaps
WITH emp,
     [x IN raw_aligned WHERE x IS NOT NULL] AS aligned_skills,
     [x IN raw_gaps WHERE x IS NOT NULL] AS gap_skills
RETURN emp.name AS name, emp.sector AS sector, emp.description AS description,
       size(aligned_skills) AS alignment_score,
       size(gap_skills) AS gap_count,
       aligned_skills, gap_skills
ORDER BY gap_count DESC

Question: "Technology partnerships"
MATCH (col:College {name: $college})-[:IN_MARKET]->(r:Region)<-[:IN_MARKET]-(emp:Employer)-[:HIRES_FOR]->(occ:Occupation)-[:REQUIRES_SKILL]->(sk:Skill)
WHERE toLower(emp.sector) CONTAINS 'technology'
OPTIONAL MATCH (course:Course {college: $college})-[:DEVELOPS]->(sk)
WITH emp, sk, occ,
     CASE WHEN count(course) > 0 THEN true ELSE false END AS developed
WITH emp,
     collect(DISTINCT CASE WHEN developed THEN sk.name END) AS raw_aligned,
     collect(DISTINCT CASE WHEN NOT developed THEN sk.name END) AS raw_gaps
WITH emp,
     [x IN raw_aligned WHERE x IS NOT NULL] AS aligned_skills,
     [x IN raw_gaps WHERE x IS NOT NULL] AS gap_skills
RETURN emp.name AS name, emp.sector AS sector, emp.description AS description,
       size(aligned_skills) AS alignment_score,
       size(gap_skills) AS gap_count,
       aligned_skills, gap_skills
ORDER BY alignment_score DESC

Question: "Who has roles requiring Programming?"
MATCH (col:College {name: $college})-[:IN_MARKET]->(r:Region)<-[:IN_MARKET]-(emp:Employer)-[:HIRES_FOR]->(occ:Occupation)-[:REQUIRES_SKILL]->(sk:Skill)
WHERE toLower(sk.name) CONTAINS 'programming'
OPTIONAL MATCH (course:Course {college: $college})-[:DEVELOPS]->(sk)
WITH emp, sk, occ,
     CASE WHEN count(course) > 0 THEN true ELSE false END AS developed
WITH emp,
     collect(DISTINCT CASE WHEN developed THEN sk.name END) AS raw_aligned,
     collect(DISTINCT CASE WHEN NOT developed THEN sk.name END) AS raw_gaps
WITH emp,
     [x IN raw_aligned WHERE x IS NOT NULL] AS aligned_skills,
     [x IN raw_gaps WHERE x IS NOT NULL] AS gap_skills
RETURN emp.name AS name, emp.sector AS sector, emp.description AS description,
       size(aligned_skills) AS alignment_score,
       size(gap_skills) AS gap_count,
       aligned_skills, gap_skills
ORDER BY alignment_score DESC

Respond with a JSON object containing two fields:
1. "cypher": the Cypher query as a string
2. "interpretation": a single sentence explaining what this query does in plain English, written for a non-technical workforce development coordinator. Be specific about the filtering criteria and mention skill alignment and gaps where relevant.

No markdown code fences. Just the raw JSON object."""


async def run_partnership_query(question: str, college: str) -> tuple[list[PartnershipOpportunity], str, str]:
    """Translate a natural language question into a Cypher query and return partnership opportunities."""
    logger.info(f"Partnership query: {question!r} for college: {college!r}")

    cypher, interpretation = generate_query(question, college, PARTNERSHIP_QUERY_PROMPT)
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
