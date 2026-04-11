"""Unit tests for the relationship_inventory check and its helpers."""

from pathlib import Path

from checks.base import Status
from checks.relationship_inventory import (
    EdgeTriple,
    RelationshipInventoryCheck,
    extract_actual_edges,
    extract_documented_edges,
    extract_edges_from_cypher,
)


# ── extract_edges_from_cypher ─────────────────────────────────────────


class TestExtractEdgesFromCypher:
    def test_simple_directed_edge(self):
        edges = extract_edges_from_cypher(
            "MATCH (col:College) MATCH (d:Department) "
            "MERGE (col)-[:OFFERS]->(d)"
        )
        assert edges == {EdgeTriple("OFFERS", "College", "Department")}

    def test_edge_with_var_and_props(self):
        edges = extract_edges_from_cypher(
            "MATCH (r:Region) MATCH (o:Occupation) "
            "MERGE (r)-[d:DEMANDS]->(o) SET d.annual_wage = $w"
        )
        assert edges == {EdgeTriple("DEMANDS", "Region", "Occupation")}

    def test_inline_labels_in_path(self):
        edges = extract_edges_from_cypher(
            "MATCH (st:Student)-[e:ENROLLED_IN]->(c:Course)"
        )
        assert edges == {EdgeTriple("ENROLLED_IN", "Student", "Course")}

    def test_chained_path(self):
        edges = extract_edges_from_cypher(
            "MATCH (st:Student)-[e:ENROLLED_IN]->(c:Course)"
            "-[:DEVELOPS]->(s:Skill)"
        )
        assert edges == {
            EdgeTriple("ENROLLED_IN", "Student", "Course"),
            EdgeTriple("DEVELOPS", "Course", "Skill"),
        }

    def test_anonymous_endpoints_dropped(self):
        # Without bound labels we cannot determine direction or shape.
        edges = extract_edges_from_cypher(
            "MATCH (n)-[:REL]->(m)"
        )
        assert edges == set()

    def test_create_pattern(self):
        edges = extract_edges_from_cypher(
            "MERGE (s:Student {uuid: $u}) WITH s "
            "MATCH (c:Course {code: $code}) "
            "CREATE (s)-[:ENROLLED_IN {grade: $g}]->(c)"
        )
        assert edges == {EdgeTriple("ENROLLED_IN", "Student", "Course")}

    def test_label_resolved_from_earlier_binding(self):
        # The MERGE references `col` and `d` by name only; the labels
        # were established by the prior MATCHes.
        edges = extract_edges_from_cypher(
            "MATCH (col:College {name: $inst_name}) "
            "MERGE (d:Department {name: $dept_name}) "
            "MERGE (col)-[:OFFERS]->(d)"
        )
        assert edges == {EdgeTriple("OFFERS", "College", "Department")}


# ── extract_documented_edges ──────────────────────────────────────────


class TestExtractDocumentedEdges:
    def test_extracts_simple_table(self, tmp_path):
        doc = tmp_path / "graph-model.md"
        doc.write_text(
            "| Relationship | From → To | Properties | What it encodes |\n"
            "|---|---|---|---|\n"
            "| `OFFERS` | College → Department | — | a college operates a dept |\n"
            "| `DEMANDS` | Region → Occupation | employment | regional demand |\n"
        )
        edges = extract_documented_edges(doc)
        assert edges == {
            EdgeTriple("OFFERS", "College", "Department"),
            EdgeTriple("DEMANDS", "Region", "Occupation"),
        }

    def test_overloaded_relationship(self, tmp_path):
        doc = tmp_path / "graph-model.md"
        doc.write_text(
            "| Relationship | From → To | Properties | What it encodes |\n"
            "|---|---|---|---|\n"
            "| `IN_MARKET` | College → Region | — | college in market |\n"
            "| `IN_MARKET` | Employer → Region | — | employer in market |\n"
        )
        edges = extract_documented_edges(doc)
        assert edges == {
            EdgeTriple("IN_MARKET", "College", "Region"),
            EdgeTriple("IN_MARKET", "Employer", "Region"),
        }

    def test_skips_rows_in_code_blocks(self, tmp_path):
        doc = tmp_path / "graph-model.md"
        doc.write_text(
            "| Relationship | From → To | Properties | What it encodes |\n"
            "|---|---|---|---|\n"
            "| `OFFERS` | College → Department | — | real |\n"
            "\n"
            "```markdown\n"
            "| `FAKE` | Foo → Bar | — | not real |\n"
            "```\n"
        )
        edges = extract_documented_edges(doc)
        assert EdgeTriple("OFFERS", "College", "Department") in edges
        assert all(e.rel_type != "FAKE" for e in edges)


# ── extract_actual_edges ──────────────────────────────────────────────


class TestExtractActualEdges:
    def test_walks_loader_files(self, tmp_path):
        loader_dir = tmp_path / "backend" / "pipeline"
        loader_dir.mkdir(parents=True)
        (loader_dir / "loader.py").write_text(
            'def load():\n'
            '    session.run(\n'
            '        "MATCH (col:College) MATCH (d:Department) "\n'
            '        "MERGE (col)-[:OFFERS]->(d)"\n'
            '    )\n'
        )
        edges = extract_actual_edges(tmp_path)
        assert EdgeTriple("OFFERS", "College", "Department") in edges


# ── RelationshipInventoryCheck end-to-end ─────────────────────────────


def _make_repo(tmp_path: Path, doc_text: str, loader_text: str) -> None:
    doc_dir = tmp_path / "docs" / "architecture"
    doc_dir.mkdir(parents=True)
    (doc_dir / "graph-model.md").write_text(doc_text)

    loader_dir = tmp_path / "backend" / "pipeline"
    loader_dir.mkdir(parents=True)
    (loader_dir / "loader.py").write_text(loader_text)


class TestRelationshipInventoryCheck:
    def test_passes_when_docs_and_loader_agree(self, tmp_path):
        _make_repo(
            tmp_path,
            doc_text=(
                "| Relationship | From → To | Properties | What it encodes |\n"
                "|---|---|---|---|\n"
                "| `OFFERS` | College → Department | — | yes |\n"
            ),
            loader_text=(
                'def load():\n'
                '    session.run(\n'
                '        "MATCH (col:College) MATCH (d:Department) "\n'
                '        "MERGE (col)-[:OFFERS]->(d)"\n'
                '    )\n'
            ),
        )
        result = RelationshipInventoryCheck().run(tmp_path)
        assert result.status == Status.PASS, result.details

    def test_fails_when_loader_has_extra_edge(self, tmp_path):
        _make_repo(
            tmp_path,
            doc_text=(
                "| Relationship | From → To | Properties | What it encodes |\n"
                "|---|---|---|---|\n"
                "| `OFFERS` | College → Department | — | yes |\n"
            ),
            loader_text=(
                'def load():\n'
                '    session.run(\n'
                '        "MATCH (col:College) MATCH (d:Department) "\n'
                '        "MERGE (col)-[:OFFERS]->(d)"\n'
                '    )\n'
                '    session.run(\n'
                '        "MATCH (e:Employer) MATCH (o:Occupation) "\n'
                '        "MERGE (e)-[:HIRES_FOR]->(o)"\n'
                '    )\n'
            ),
        )
        result = RelationshipInventoryCheck().run(tmp_path)
        assert result.status == Status.FAIL
        assert "HIRES_FOR" in result.details
        assert "no doc row" in result.details

    def test_fails_when_doc_has_extra_edge(self, tmp_path):
        _make_repo(
            tmp_path,
            doc_text=(
                "| Relationship | From → To | Properties | What it encodes |\n"
                "|---|---|---|---|\n"
                "| `OFFERS` | College → Department | — | yes |\n"
                "| `GHOST` | College → Region | — | not in code |\n"
            ),
            loader_text=(
                'def load():\n'
                '    session.run(\n'
                '        "MATCH (col:College) MATCH (d:Department) "\n'
                '        "MERGE (col)-[:OFFERS]->(d)"\n'
                '    )\n'
            ),
        )
        result = RelationshipInventoryCheck().run(tmp_path)
        assert result.status == Status.FAIL
        assert "GHOST" in result.details
        assert "no loader" in result.details

    def test_fails_when_direction_reversed(self, tmp_path):
        _make_repo(
            tmp_path,
            doc_text=(
                "| Relationship | From → To | Properties | What it encodes |\n"
                "|---|---|---|---|\n"
                "| `OFFERS` | Department → College | — | reversed! |\n"
            ),
            loader_text=(
                'def load():\n'
                '    session.run(\n'
                '        "MATCH (col:College) MATCH (d:Department) "\n'
                '        "MERGE (col)-[:OFFERS]->(d)"\n'
                '    )\n'
            ),
        )
        result = RelationshipInventoryCheck().run(tmp_path)
        assert result.status == Status.FAIL
        # Both the doc-only triple and the code-only triple should be reported.
        assert "Department → College" in result.details
        assert "College → Department" in result.details

    def test_skips_when_doc_missing(self, tmp_path):
        loader_dir = tmp_path / "backend" / "pipeline"
        loader_dir.mkdir(parents=True)
        (loader_dir / "loader.py").write_text("# empty\n")
        result = RelationshipInventoryCheck().run(tmp_path)
        assert result.status == Status.SKIP

    def test_skips_when_loaders_missing(self, tmp_path):
        doc_dir = tmp_path / "docs" / "architecture"
        doc_dir.mkdir(parents=True)
        (doc_dir / "graph-model.md").write_text("# empty\n")
        result = RelationshipInventoryCheck().run(tmp_path)
        assert result.status == Status.SKIP
