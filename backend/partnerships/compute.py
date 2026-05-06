"""
Materialize derived analytical edges for the partnerships surface.

Three edge types live here:
  - PARTNERSHIP_ALIGNMENT (College→Employer, per-college batched)
  - OCCUPATION_PIPELINE (College→Occupation, per-college batched)
  - HAS_COMPETENCY (Student→Occupation, per-student batched, cross-college)

Each is a precomputed summarization of an expensive request-time
traversal. Running them at pipeline-reload time shifts the work to
ingestion and lets endpoints become bounded edge reads.

The /employers/ endpoint ranks employers in a college's region by
curriculum alignment via the institutional TOP-SOC crosswalk: for each
employer, count the courses (and departments) at this college whose
PREPARES_FOR set intersects the employer's HIRES_FOR set.

Computed at request time, that traversal does ~40M DbHits per college
(College → Region → Employer × HIRES_FOR × PREPARES_FOR × CONTAINS),
materializing a multi-million-row cartesian before aggregating. On the
prod e2-medium VM that's 26s for Foothill (Bay region, 311 employers)
and timeouts (>300s) for LA/OC/SD-region colleges (350+ employers).

This module materializes the same alignment as a precomputed edge,
shifting the work to ingestion time. At request time the endpoint is
O(employers in region) — sub-100ms regardless of region size.

Edge properties:
  roles_count             count of distinct occupations the employer
                          hires for in this college's region — the full
                          BLS OEWS NAICS-4 occupation set. Reported for
                          completeness; not currently rendered.
  aligned_roles_count     count of those occupations the college
                          institutionally connects to via the TOP-CIP-SOC
                          crosswalk (i.e. the college has at least one
                          course that PREPARES_FOR the occupation). This
                          is what the "Roles" column in EmployersView
                          renders so it stays consistent with the
                          "Employer Occupations (N)" header in the
                          expanded panel, which already filters by
                          aligned_course_count > 0.
  aligned_course_count    number of distinct courses at this college
                          that PREPARES_FOR any of the employer's
                          hire occupations. The institutional alignment
                          depth — 0 means no curricular pathway exists
                          at this college; higher means deeper coverage.

Stored fields are deliberately minimal. `aligned_department_count` was
in the legacy shape but never rendered. The full `occupations: string[]`
list (collect of titles) was previously sent on every list-page load but
~1.7 MB of titles per request was streamed only to compute a single
`.length` integer in the UI — replaced here with the precomputed count.
Materializing unrendered or one-step-derivable fields buys no user value
and adds compute + storage cost. Re-add either if a surface starts using
the underlying data.

Idempotent: re-running drops this college's existing
PARTNERSHIP_ALIGNMENT edges and rebuilds from current state, so changes
in PREPARES_FOR or employer set propagate cleanly. The legacy skill-
based properties (aligned_skills, gap_skills, alignment_score, etc.)
on edges from the old skill-overlap model are dropped along with the
edges and not re-created — Skill nodes were retired with the TOP-SOC
refactor and those properties are no longer meaningful.
"""

from __future__ import annotations

import argparse
import logging

from neo4j import Driver

logger = logging.getLogger(__name__)


def materialize_partnership_alignment(driver: Driver, college: str) -> dict:
    """Drop and rebuild PARTNERSHIP_ALIGNMENT edges out of one college.

    Reads College → Region → Employer → Occupation HIRES_FOR plus
    Course PREPARES_FOR Occupation and Department CONTAINS Course,
    aggregates per (college, employer), writes one edge per employer
    in the college's region. Returns counts for verification.

    Pre-conditions:
      - College, Region, Employer nodes exist (load_industry_data)
      - HIRES_FOR edges exist (load_employers)
      - Course nodes exist with college property (load_courses)
      - PREPARES_FOR edges exist (materialize_prepares_for, called
        from courses/load.py)

    Without those upstream steps the compute writes zero edges (or
    edges with aligned_course_count=0 for employers in region but
    with no curricular alignment). Both are valid outcomes.

    Returns: {edges_dropped, edges_created, employers_with_alignment}

    `employers_with_alignment` counts edges with aligned_course_count>0
    — i.e. employers where the institutional crosswalk establishes at
    least one curricular pathway. Edges are written for every employer
    in the region regardless, so the list view shows them all; the
    count is for diagnostic visibility (a region with very low ratio
    suggests the crosswalk is sparse for that college's TOP set).
    """
    stats = {
        "edges_dropped": 0,
        "edges_created": 0,
        "employers_with_alignment": 0,
    }

    with driver.session() as session:
        # Step 1: drop existing PARTNERSHIP_ALIGNMENT edges out of this
        # college. Idempotency: a re-run gets a clean rebuild from
        # current graph state. Also clears any legacy skill-based
        # properties from the pre-refactor edges.
        result = session.run(
            """
            MATCH (c:College {name: $college})-[pa:PARTNERSHIP_ALIGNMENT]->()
            DELETE pa
            RETURN count(pa) AS n
            """,
            college=college,
        ).single()
        stats["edges_dropped"] = result["n"] if result else 0

        # Step 2: rebuild. Single query per college — Neo4j can keep
        # the (employers in region) working set hot through the
        # aggregation. Using CREATE rather than MERGE because we just
        # deleted; CREATE skips the existence check and avoids the
        # composite-index scan MERGE would do.
        result = session.run(
            """
            MATCH (c:College {name: $college})-[:IN_MARKET]->(r:Region)
                  <-[:IN_MARKET]-(emp:Employer)-[:HIRES_FOR]->(occ:Occupation)
            WITH c, emp, collect(DISTINCT occ) AS occs
            // aligned_roles_count: of the employer's HIRES_FOR roles, how many
            // does this college institutionally connect to via the TOP-CIP-SOC
            // crosswalk? This is the count the EmployersView ROLES column
            // displays — same filter the expanded panel header uses. Without
            // it, the column shows the full HIRES_FOR count (which post-C13
            // is the BLS OEWS NAICS-4 occupation set, often 100+ entries) and
            // is inconsistent with the panel header that filters by
            // aligned_course_count > 0.
            WITH c, emp, occs,
                 size([o IN occs WHERE EXISTS { (course:Course {college: c.name})-[:PREPARES_FOR]->(o) }]) AS aligned_roles_count
            OPTIONAL MATCH (course:Course {college: c.name})-[:PREPARES_FOR]->(o:Occupation)
            WHERE o IN occs
            WITH c, emp, occs, aligned_roles_count,
                 count(DISTINCT course) AS aligned_course_count
            CREATE (c)-[pa:PARTNERSHIP_ALIGNMENT {
                roles_count: size(occs),
                aligned_roles_count: aligned_roles_count,
                aligned_course_count: aligned_course_count
            }]->(emp)
            RETURN count(pa) AS n,
                   sum(CASE WHEN aligned_course_count > 0 THEN 1 ELSE 0 END) AS with_alignment
            """,
            college=college,
        ).single()
        if result:
            stats["edges_created"] = result["n"]
            stats["employers_with_alignment"] = result["with_alignment"]

    logger.info(
        f"materialize_partnership_alignment({college}): "
        f"{stats['edges_created']} edges written "
        f"({stats['employers_with_alignment']} with curricular alignment, "
        f"{stats['edges_dropped']} stale edges cleared)"
    )
    return stats


def materialize_occupation_pipeline(driver: Driver, college: str) -> dict:
    """Drop and rebuild OCCUPATION_PIPELINE edges out of one college.

    For each occupation the college's region demands AND the college has
    institutionally connected curriculum to (at least one Course
    PREPARES_FOR), write one (College)-[:OCCUPATION_PIPELINE]->(Occupation)
    edge with the per-(college, soc) aggregates the partnerships
    SectorIndex needs:

      course_count    distinct courses at this college that PREPARES_FOR
                      this occupation. The institutional curricular
                      depth.
      employer_count  distinct employers in the college's region that
                      HIRES_FOR this occupation (and the region also
                      DEMANDS the occupation, mirroring the existing
                      build_sector_index filter).
      student_count   distinct students at this college enrolled in any
                      course in any department that contains a
                      PREPARES_FOR-aligned course for this occupation.
                      The same aggregation `_gather_student_pipeline`
                      reports as `total_in_aligned_departments`.
      top_codes       distinct TOP6 codes the aligned courses are
                      MCF-tagged with. Used downstream by
                      build_sector_index's supply-side calc to look up
                      COE program-completion estimates per SOC. Stored
                      as a list to avoid the second course-side query.

    Edges are written only where course_count > 0 — i.e. the SOC has at
    least one institutional curricular pathway at this college. The
    SectorIndex filter excluded SOCs without alignment anyway, so
    skipping them at compute time is consistent and saves storage.

    Three queries (course/top_codes, employer count, student count) run
    sequentially and Python aggregates the rows; bulk write via UNWIND.
    Splitting into three reads keeps each query's cartesian bounded —
    fusing them into one mega-MATCH made the planner choose worse
    plans on the e2-medium VM in dry runs.

    Idempotent: re-running drops this college's existing
    OCCUPATION_PIPELINE edges and rebuilds. Safe to call ad-hoc.

    Pre-conditions: same as materialize_partnership_alignment —
    PREPARES_FOR materialized, employers loaded, students generated.

    Returns: {edges_dropped, edges_created, socs_with_employers, socs_with_students}
    """
    stats = {
        "edges_dropped": 0,
        "edges_created": 0,
        "socs_with_employers": 0,
        "socs_with_students": 0,
    }

    with driver.session() as session:
        # Step 1: drop stale edges out of this college.
        result = session.run(
            """
            MATCH (c:College {name: $college})-[op:OCCUPATION_PIPELINE]->()
            DELETE op
            RETURN count(op) AS n
            """,
            college=college,
        ).single()
        stats["edges_dropped"] = result["n"] if result else 0

        # Step 2: per-(college, soc) course count + the TOP6 set of those
        # courses. The WHERE course_count > 0 filter restricts the
        # downstream edge set to SOCs with at least one institutional
        # pathway, matching build_sector_index's gating.
        course_rows = session.run(
            """
            MATCH (c:College {name: $college})-[:IN_MARKET]->(r:Region)
                  -[:DEMANDS]->(occ:Occupation)
            OPTIONAL MATCH (course:Course {college: $college})-[:PREPARES_FOR]->(occ)
            WITH occ,
                 count(DISTINCT course) AS course_count,
                 collect(DISTINCT course.top_code) AS raw_top_codes
            WHERE course_count > 0
            RETURN occ.soc_code AS soc,
                   course_count,
                   [t IN raw_top_codes WHERE t IS NOT NULL AND t <> ''] AS top_codes
            """,
            college=college,
        ).data()

        if not course_rows:
            logger.info(
                f"materialize_occupation_pipeline({college}): no aligned "
                f"SOCs (no PREPARES_FOR edges yet?); zero edges written"
            )
            return stats

        # Step 3: employer counts. WHERE (r)-[:DEMANDS]->(occ) mirrors
        # build_sector_index's exact filter — only count employers for
        # SOCs the region also demands, so a Bay-region employer hiring
        # a SOC that's only demanded in LA doesn't count toward Foothill.
        emp_rows = session.run(
            """
            MATCH (col:College {name: $college})-[:IN_MARKET]->(r:Region)
                  <-[:IN_MARKET]-(emp:Employer)-[:HIRES_FOR]->(occ:Occupation)
            WHERE (r)-[:DEMANDS]->(occ)
            RETURN occ.soc_code AS soc,
                   count(DISTINCT emp) AS employer_count
            """,
            college=college,
        ).data()
        emp_by_soc = {r["soc"]: r["employer_count"] for r in emp_rows}

        # Step 4: student counts. The previously-slowest query in
        # build_sector_index (1.3s p50, 11s p95). Same shape preserved
        # so the precomputed value matches what live computation would
        # have produced — students at this college enrolled in any
        # course in any department that contains a PREPARES_FOR-aligned
        # course for the SOC.
        student_rows = session.run(
            """
            MATCH (col:College {name: $college})-[:IN_MARKET]->(r:Region)
                  -[:DEMANDS]->(occ:Occupation)
            OPTIONAL MATCH (dept:Department)-[:CONTAINS]->(:Course {college: $college})-[:PREPARES_FOR]->(occ)
            WITH occ, collect(DISTINCT dept) AS aligned_depts
            OPTIONAL MATCH (d2:Department)-[:CONTAINS]->(:Course {college: $college})<-[:ENROLLED_IN]-(s:Student)
            WHERE d2 IN aligned_depts
            RETURN occ.soc_code AS soc,
                   count(DISTINCT s) AS student_count
            """,
            college=college,
        ).data()
        student_by_soc = {r["soc"]: r["student_count"] for r in student_rows}

        # `total_in_program` (primary-focus-gated student count) was
        # attempted as a 4th precomputed property but the natural
        # compute query — OPTIONAL MATCH (Student) WHERE primary_focus
        # IN aligned_dept_names per (college, soc) — OOM'd Neo4j on
        # the e2-medium VM because the planner can't use the
        # student_primary_focus index when the IN-list varies per row.
        # gather.py keeps that count live for now (uses the index
        # because $departments is bound). See gather.py:
        # `_gather_student_pipeline` for the deferred precompute
        # design notes.

        # Step 5: assemble UNWIND rows from course_rows (the gating set —
        # only SOCs with course_count > 0). Other counts default to 0
        # if the joins above didn't reach them.
        rows = [
            {
                "soc": r["soc"],
                "course_count": r["course_count"],
                "employer_count": emp_by_soc.get(r["soc"], 0),
                "student_count": student_by_soc.get(r["soc"], 0),
                "top_codes": r["top_codes"],
            }
            for r in course_rows
        ]
        stats["socs_with_employers"] = sum(1 for r in rows if r["employer_count"] > 0)
        stats["socs_with_students"] = sum(1 for r in rows if r["student_count"] > 0)

        # Step 6: bulk-create edges via UNWIND. One round-trip for the
        # write phase regardless of edge count. Idempotency relies on
        # the DELETE in step 1 — using CREATE rather than MERGE here
        # so duplicate edges become a loud failure if step 1 was
        # somehow skipped.
        result = session.run(
            """
            UNWIND $rows AS row
            MATCH (col:College {name: $college})
            MATCH (occ:Occupation {soc_code: row.soc})
            CREATE (col)-[op:OCCUPATION_PIPELINE {
                course_count: row.course_count,
                employer_count: row.employer_count,
                student_count: row.student_count,
                top_codes: row.top_codes
            }]->(occ)
            RETURN count(op) AS n
            """,
            college=college,
            rows=rows,
        ).single()
        stats["edges_created"] = result["n"] if result else 0

    logger.info(
        f"materialize_occupation_pipeline({college}): "
        f"{stats['edges_created']} edges written "
        f"({stats['socs_with_employers']} with employers, "
        f"{stats['socs_with_students']} with student pipelines, "
        f"{stats['edges_dropped']} stale edges cleared)"
    )
    return stats


# Chained-WITH cypher with no UNWIND. The earlier collect/UNWIND
# pattern produced a cartesian explosion (rows × students = N²) that
# hung Neo4j; the planner couldn't tell that students was the same list
# across the inner UNWIND. Plain chained WITH preserves row-per-student
# cardinality through the pipeline.
_HAS_COMPETENCY_BATCH_CREATE = """
MATCH (s:Student)
WITH s ORDER BY s.uuid SKIP $offset LIMIT $batch_size
OPTIONAL MATCH (s)-[:ENROLLED_IN]->(c:Course)-[pf:PREPARES_FOR]->(occ:Occupation)
WITH s, occ,
     count(DISTINCT c) AS competency_depth,
     [t IN collect(DISTINCT pf.via_top) WHERE t IS NOT NULL] AS via_tops
WHERE occ IS NOT NULL
CREATE (s)-[:HAS_COMPETENCY {
    competency_depth: competency_depth,
    via_tops: via_tops
}]->(occ)
RETURN count(*) AS edges_created
"""

# Drop existing edges in chunks so a global wipe doesn't hold a single
# multi-million-edge transaction in heap. 50K-edge batches keep each
# DELETE transaction well within the 2 GB heap on e2-standard-2.
_HAS_COMPETENCY_DELETE_CHUNK = """
MATCH ()-[hc:HAS_COMPETENCY]->()
WITH hc LIMIT $chunk_size
DELETE hc
RETURN count(hc) AS n
"""


def materialize_has_competency(driver: Driver, batch_size: int = 2_500) -> dict:
    """Drop and rebuild HAS_COMPETENCY edges across all students.

    Materializes (Student)-[:HAS_COMPETENCY {competency_depth, via_tops}]->(Occupation)
    edges, one per (student, soc) pair where the student has at least one
    ENROLLED_IN edge to a Course that PREPARES_FOR the Occupation.

    Properties:
      competency_depth  count of distinct PREPARES_FOR-tagged courses the
                        student is enrolled in for this occupation.
                        The "spectrum" measure: 1 = beginning to develop,
                        N = substantial coursework completed.
      via_tops          distinct TOP6 codes of the courses that route the
                        student-occupation pathway. Mirrors the audit
                        pattern on PREPARES_FOR.via_top; enables grouped
                        rendering of competency by program area without
                        re-traversing.

    Cross-college by design: the edge aggregates over a student's full
    enrollment history regardless of which colleges contributed which
    courses. A student enrolled at Foothill and De Anza for the same SOC
    gets one edge with combined depth.

    Two-phase batching:

      Phase 1 — drop existing HAS_COMPETENCY edges in chunks of 50K.
      A single global DELETE of millions of edges would hold a giant
      transaction in heap; chunking caps each DELETE transaction.

      Phase 2 — per-batch CREATE. Iterate students by UUID order in
      batches of `batch_size` (default 2500); each batch's transaction
      walks ENROLLED_IN+PREPARES_FOR for those students, aggregates per
      (student, occ) pair, and writes the edges. ~75K edges per CREATE
      transaction at the default batch size.

    Trade-off: phase 1 leaves a window where no HAS_COMPETENCY edges
    exist before phase 2 starts. During that window any /partnerships/
    opportunity request returns empty top_students. Acceptable for
    pipeline reload (planned downtime); not acceptable for live ops.
    Mitigation if needed: keep batches per-student-atomic by doing
    drop+rebuild within each batch transaction instead of phasing —
    but that requires care around the cartesian-explosion trap that
    hung the first attempt. For now, planned-window is fine; the
    materialize is a reload-time operation, not a live-ops one.

    Pre-conditions: PREPARES_FOR materialized, students generated,
    ENROLLED_IN edges present. Missing pre-conditions yield zero
    edges; not an error.

    Returns: {students_total, edges_dropped, batches, edges_created}
    """
    with driver.session() as session:
        total_students = session.run(
            "MATCH (s:Student) RETURN count(s) AS n"
        ).single()["n"]

    if total_students == 0:
        logger.warning("materialize_has_competency: no Student nodes; zero edges written")
        return {"students_total": 0, "edges_dropped": 0, "batches": 0, "edges_created": 0}

    edges_dropped = 0
    chunk_size = 50_000
    logger.info("materialize_has_competency: phase 1 — drop existing HAS_COMPETENCY edges")
    with driver.session() as session:
        while True:
            def delete_chunk(tx, chunk_size=chunk_size):
                return tx.run(_HAS_COMPETENCY_DELETE_CHUNK, chunk_size=chunk_size).single()

            result = session.execute_write(delete_chunk)
            n = result["n"] if result else 0
            edges_dropped += n
            if n < chunk_size:
                break
            logger.info(f"  dropped {edges_dropped} so far …")
    logger.info(f"  phase 1 complete: {edges_dropped} edges dropped")

    batches = (total_students + batch_size - 1) // batch_size
    total_edges = 0
    logger.info(
        f"materialize_has_competency: phase 2 — {total_students} students "
        f"→ {batches} batches of {batch_size}"
    )

    with driver.session() as session:
        for batch_idx in range(batches):
            offset = batch_idx * batch_size

            def run_batch(tx, offset=offset, batch_size=batch_size):
                return tx.run(
                    _HAS_COMPETENCY_BATCH_CREATE,
                    offset=offset,
                    batch_size=batch_size,
                ).single()

            result = session.execute_write(run_batch)
            edges = result["edges_created"] if result else 0
            total_edges += edges
            logger.info(
                f"  batch {batch_idx + 1}/{batches} "
                f"(students {offset}–{offset + batch_size}): "
                f"edges_created={edges}"
            )

    logger.info(
        f"materialize_has_competency: complete — "
        f"{total_edges} edges across {batches} batches "
        f"({edges_dropped} stale edges cleared)"
    )
    return {
        "students_total": total_students,
        "edges_dropped": edges_dropped,
        "batches": batches,
        "edges_created": total_edges,
    }


def _all_colleges(driver: Driver) -> list[str]:
    with driver.session() as s:
        rows = s.run("MATCH (c:College) RETURN c.name AS name ORDER BY c.name").data()
    return [r["name"] for r in rows]


def main():
    """CLI entrypoint for ad-hoc materialization (e.g., on prod after a
    code change that requires fresh edges without a full reload).

    Three edge sets:
      - PARTNERSHIP_ALIGNMENT (per College→Employer, per-college batched)
      - OCCUPATION_PIPELINE (per College→Occupation, per-college batched)
      - HAS_COMPETENCY (per Student→Occupation, per-student batched —
        cross-college by nature, so not gated by --college)

    All three run by default. The first two are gated by --college (or
    --all); HAS_COMPETENCY is global and runs once regardless of the
    --college flag. Use --only=<edge> to run just one.
    """
    parser = argparse.ArgumentParser(
        description="Materialize partnership precomputed edges.",
    )
    parser.add_argument("--college", help="College name (for per-college edges). Omit to process all.")
    parser.add_argument("--all", action="store_true", help="Process every College in graph.")
    parser.add_argument(
        "--only",
        choices=("partnership_alignment", "occupation_pipeline", "has_competency"),
        help="Only materialize one edge set (default: all three).",
    )
    parser.add_argument(
        "--has-competency-batch-size",
        type=int,
        default=10_000,
        help="Students per HAS_COMPETENCY batch transaction (default: 10000).",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)-7s %(message)s",
        datefmt="%H:%M:%S",
    )

    from ontology.schema import get_driver, close_driver

    driver = get_driver()
    try:
        # Per-college edges
        run_pa = args.only in (None, "partnership_alignment")
        run_op = args.only in (None, "occupation_pipeline")
        if run_pa or run_op:
            if args.all or not args.college:
                colleges = _all_colleges(driver)
                logger.info(f"Processing {len(colleges)} colleges")
                for c in colleges:
                    if run_pa:
                        materialize_partnership_alignment(driver, c)
                    if run_op:
                        materialize_occupation_pipeline(driver, c)
            else:
                if run_pa:
                    materialize_partnership_alignment(driver, args.college)
                if run_op:
                    materialize_occupation_pipeline(driver, args.college)

        # Cross-college edges (run once globally, not gated by --college)
        if args.only in (None, "has_competency"):
            materialize_has_competency(
                driver, batch_size=args.has_competency_batch_size
            )
    finally:
        close_driver()


if __name__ == "__main__":
    main()
