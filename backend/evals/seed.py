"""Load the committed eval seed (``seed.json``) into the Neo4j at NEO4J_URI.

Used by CI (after the Neo4j service container starts, before pytest) and locally against a
throwaway Neo4j. Idempotent: nodes/edges are MERGEd on their natural keys. Regenerate the
fixture with ``evals.extract_seed`` against a full graph.
"""
import gzip
import json
from pathlib import Path

from ontology.schema import get_driver, init_schema

SEED = Path(__file__).parent / "seed.json.gz"

# natural-key property name(s) per label (schema constraints, ontology/schema.py)
NODE_KEYS = {
    "Program": ("college", "top6"), "Course": ("code", "college"), "Occupation": ("soc_code",),
    "AcademicYear": ("year",), "Term": ("term",), "Region": ("name",), "Employer": ("name",),
}
# edge type -> (from_label, {node_prop: seed_field}, to_label, {node_prop: seed_field})
EDGE_SPEC = {
    "AWARDED":  ("Program",  {"college": "f_college", "top6": "f_top6"}, "AcademicYear", {"year": "t_year"}),
    "ENROLLED": ("Program",  {"college": "f_college", "top6": "f_top6"}, "Term",         {"term": "t_term"}),
    "DEMANDS":  ("Region",   {"name": "f_region"},                      "Occupation",   {"soc_code": "t_soc"}),
    "HIRES_FOR":("Employer", {"name": "f_emp"},                         "Occupation",   {"soc_code": "t_soc"}),
    "IN_MARKET":("Employer", {"name": "f_emp"},                         "Region",       {"name": "t_region"}),
}


def load(*, ensure_schema: bool = True) -> None:
    if ensure_schema:
        init_schema()
    data = json.loads(gzip.decompress(SEED.read_bytes()))
    with get_driver().session() as s:
        for label, recs in data["nodes"].items():
            key = ", ".join(f"{k}: r.{k}" for k in NODE_KEYS[label])
            s.run(f"UNWIND $recs AS r MERGE (n:{label} {{{key}}}) SET n += r", recs=recs)
        for etype, recs in data["edges"].items():
            fl, fk, tl, tk = EDGE_SPEC[etype]
            fm = ", ".join(f"{p}: r.{fld}" for p, fld in fk.items())
            tm = ", ".join(f"{p}: r.{fld}" for p, fld in tk.items())
            s.run(f"UNWIND $recs AS r MATCH (a:{fl} {{{fm}}}), (b:{tl} {{{tm}}}) "
                  f"MERGE (a)-[e:{etype}]->(b) SET e += r.props", recs=recs)
    n = sum(len(v) for v in data["nodes"].values())
    e = sum(len(v) for v in data["edges"].values())
    print(f"loaded eval seed: {n} nodes, {e} edges")


if __name__ == "__main__":
    load()
