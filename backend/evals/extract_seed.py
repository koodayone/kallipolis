"""Extract the eval seed — a small, reproducible slice of the graph covering the golden
coordinates. Run against a FULL graph (dev, with NEO4J_URI set) to regenerate the committed
fixture ``seed.json`` whenever the golden coordinates or the schema change:

    NEO4J_URI=bolt://localhost:7699 NEO4J_USERNAME=neo4j NEO4J_PASSWORD=… \\
        python3.11 -m evals.extract_seed

Scope = the SEED_INSTANCES' colleges × their sectors' feeder TOPs, with FULL supply/demand
data (AWARDED/ENROLLED/Course/DEMANDS — small) and a TOP-N-per-SOC employer subset (HIRES_FOR
is the only large relation). Nodes/edges are keyed on their natural keys (schema constraints),
never Neo4j internal ids, so the fixture is stable across reloads. The huge unused relation
PREPARES_FOR (crosswalk-from-files, not queried by the tools) is excluded.
"""
import gzip
import json
from pathlib import Path

from ontology.schema import get_driver
from ontology.crosswalks import top6_to_soc
from mcp_server.scope import scope_for

SEED_INSTANCES = [("svamp", "adm"), ("smccd", "adm"), ("baccc", "health"),
                  ("ccsf", "adm"), ("deanza", "retail")]
EMPLOYERS_PER_SOC = 15
OUT = Path(__file__).parent / "seed.json.gz"   # gzipped: machine-generated, ~8:1


def _scope():
    colleges, tops, socs = set(), set(), set()
    for member, sector in SEED_INSTANCES:
        r = scope_for(member, sector)
        if not r:
            continue
        spec = r[0]   # UNRESOLVED spec: full sector SOCs. resolve() NARROWS .socs to the
                      # effective set, but liveness (registry.has_supply / relevant_tops) is
                      # computed on the full set, so the seed must carry the full-set feeders
                      # + their awards — else a live-but-empty coordinate (deanza/retail) reads
                      # as out-of-scope. Also captures the awards gate's on-the-books-but-dormant
                      # feeders that relevant_tops would otherwise drop.
        colleges |= set(spec.colleges)
        socs |= set(spec.socs)
        in_scope = spec.in_scope_tops()
        soc_map = top6_to_soc(in_scope)
        targets = set(spec.socs)
        tops |= {t for t in in_scope if soc_map.get(t, set()) & targets}
    return sorted(colleges), sorted(tops), sorted(socs)


def main():
    colleges, tops, socs = _scope()
    with get_driver().session() as s:
        def rows(q, **p):
            return s.run(q, **p).data()

        # ── nodes (natural-key props captured generically) ──
        nodes = {
            "Program": [r["props"] for r in rows(
                "MATCH (p:Program) WHERE p.college IN $c AND p.top6 IN $t RETURN properties(p) AS props",
                c=colleges, t=tops)],
            # Course: keep only the fields the tools query (coverage needs presence via top_code);
            # drop the heavy description/learning_outcomes text that dominates the fixture size.
            "Course": [r["props"] for r in rows(
                "MATCH (c:Course) WHERE c.college IN $c AND c.top_code IN $t "
                "RETURN {code: c.code, college: c.college, top_code: c.top_code, name: c.name} AS props",
                c=colleges, t=tops)],
            "Occupation": [r["props"] for r in rows(
                "MATCH (o:Occupation) WHERE o.soc_code IN $s RETURN properties(o) AS props", s=socs)],
            "AcademicYear": [r["props"] for r in rows("MATCH (n:AcademicYear) RETURN properties(n) AS props")],
            "Term": [r["props"] for r in rows("MATCH (n:Term) RETURN properties(n) AS props")],
            "Region": [r["props"] for r in rows("MATCH (n:Region) RETURN properties(n) AS props")],
            # Statewide pooled graduate-wage cohorts for the scope's TOP6s (all recipient
            # types). Keyed by top6 only, so ONE set per TOP6 regardless of colleges.
            "ProgramWageOutcome": [r["props"] for r in rows(
                "MATCH (w:ProgramWageOutcome) WHERE w.top6 IN $t RETURN properties(w) AS props "
                "ORDER BY w.top6, w.recipient_type", t=tops)],
        }
        # employer subset: top-N per SOC by HIRES_FOR relevance
        emp_names = {r["name"] for r in rows(
            "MATCH (e:Employer)-[h:HIRES_FOR]->(o:Occupation) WHERE o.soc_code IN $s "
            "WITH o.soc_code AS soc, e, h.pct_total AS pct ORDER BY pct DESC "
            "WITH soc, collect(e.name)[0..$n] AS top WHERE size(top) > 0 "
            "UNWIND top AS name RETURN DISTINCT name", s=socs, n=EMPLOYERS_PER_SOC)}
        nodes["Employer"] = [r["props"] for r in rows(
            "MATCH (e:Employer) WHERE e.name IN $e RETURN properties(e) AS props", e=list(emp_names))]

        # ── edges (endpoints by natural key) ──
        edges = {
            # SUM over the award_type / credit_type edge-key so the seed carries ONE edge per
            # (program, year|term) with the total — the graph keys AWARDED by award_type and
            # ENROLLED by credit_type (multiple edges each), but the seed loader MERGEs on the
            # endpoints alone, which would otherwise collapse to a single arbitrary edge and
            # undercount. Every supply/coverage query already sums count, so the total is faithful.
            "AWARDED": rows(
                "MATCH (p:Program)-[r:AWARDED]->(ay:AcademicYear) WHERE p.college IN $c AND p.top6 IN $t "
                "WITH p.college AS f_college, p.top6 AS f_top6, ay.year AS t_year, "
                "toInteger(sum(coalesce(r.count,0))) AS cnt "
                "RETURN f_college, f_top6, t_year, {count: cnt} AS props",
                c=colleges, t=tops),
            "ENROLLED": rows(
                "MATCH (p:Program)-[r:ENROLLED]->(tm:Term) WHERE p.college IN $c AND p.top6 IN $t "
                "WITH p.college AS f_college, p.top6 AS f_top6, tm.term AS t_term, "
                "toInteger(sum(coalesce(r.count,0))) AS cnt "
                "RETURN f_college, f_top6, t_term, {count: cnt} AS props",
                c=colleges, t=tops),
            "DEMANDS": rows(
                "MATCH (rg:Region)-[r:DEMANDS]->(o:Occupation) WHERE o.soc_code IN $s "
                "RETURN rg.name AS f_region, o.soc_code AS t_soc, properties(r) AS props", s=socs),
            "HIRES_FOR": rows(
                "MATCH (e:Employer)-[r:HIRES_FOR]->(o:Occupation) WHERE e.name IN $e AND o.soc_code IN $s "
                "RETURN e.name AS f_emp, o.soc_code AS t_soc, properties(r) AS props",
                e=list(emp_names), s=socs),
            "IN_MARKET": rows(
                "MATCH (e:Employer)-[r:IN_MARKET]->(rg:Region) WHERE e.name IN $e "
                "RETURN e.name AS f_emp, rg.name AS t_region, properties(r) AS props", e=list(emp_names)),
            "HAS_WAGE_OUTCOME": rows(
                "MATCH (p:Program)-[:HAS_WAGE_OUTCOME]->(w:ProgramWageOutcome) "
                "WHERE p.college IN $c AND p.top6 IN $t "
                "RETURN p.college AS f_college, p.top6 AS f_top6, w.top6 AS t_top6, "
                "w.recipient_type AS t_recipient_type, {} AS props "
                "ORDER BY f_college, f_top6, t_recipient_type", c=colleges, t=tops),
        }

    payload = json.dumps({"nodes": nodes, "edges": edges}, sort_keys=True).encode()
    OUT.write_bytes(gzip.compress(payload, mtime=0))   # mtime=0 → byte-stable across runs
    counts = {k: len(v) for k, v in nodes.items()} | {f":{k}": len(v) for k, v in edges.items()}
    print(f"seed scope: {len(colleges)} colleges, {len(tops)} TOPs, {len(socs)} SOCs")
    print("wrote", OUT, "-", counts, "-", OUT.stat().st_size // 1024, "KB")


if __name__ == "__main__":
    main()
