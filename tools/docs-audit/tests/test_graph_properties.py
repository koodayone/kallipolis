"""Unit tests for the graph_properties check and its helpers."""

from pathlib import Path

from checks.base import Status
from checks.graph_properties import (
    GraphPropertiesCheck,
    extract_actual_properties,
    extract_documented_edge_properties,
    extract_documented_node_properties,
    extract_properties_from_cypher,
    iter_cypher_strings,
    parse_doc_property_list,
)


# ── parse_doc_property_list ───────────────────────────────────────────


class TestParseDocPropertyList:
    def test_single_property(self):
        assert parse_doc_property_list("name") == {"name"}

    def test_comma_separated(self):
        assert parse_doc_property_list("name, city, state") == {"name", "city", "state"}

    def test_em_dash_means_no_props(self):
        assert parse_doc_property_list("—") == set()

    def test_hyphen_means_no_props(self):
        assert parse_doc_property_list("-") == set()

    def test_empty_string(self):
        assert parse_doc_property_list("") == set()
        assert parse_doc_property_list("   ") == set()

    def test_strips_whitespace(self):
        assert parse_doc_property_list(" name , city ") == {"name", "city"}


# ── extract_documented_node_properties ────────────────────────────────


class TestExtractDocumentedNodeProperties:
    def test_extracts_simple_node_table(self, tmp_path):
        doc = tmp_path / "graph-model.md"
        doc.write_text(
            "## Curriculum side\n"
            "\n"
            "| Node | Key properties | Constraint | What it represents |\n"
            "|---|---|---|---|\n"
            "| **College** | name, city, state | `name UNIQUE` | A college |\n"
            "| **Department** | name | `name UNIQUE` | A department |\n"
        )
        result = extract_documented_node_properties(doc)
        assert result["College"] == {"name", "city", "state"}
        assert result["Department"] == {"name"}

    def test_skips_rows_in_code_blocks(self, tmp_path):
        doc = tmp_path / "graph-model.md"
        doc.write_text(
            "| Node | Key properties | Constraint | What it represents |\n"
            "|---|---|---|---|\n"
            "| **College** | name | `name UNIQUE` | A college |\n"
            "\n"
            "```markdown\n"
            "| **FakeNode** | x | `x UNIQUE` | not real |\n"
            "```\n"
        )
        result = extract_documented_node_properties(doc)
        assert "College" in result
        assert "FakeNode" not in result


# ── extract_documented_edge_properties ────────────────────────────────


class TestExtractDocumentedEdgeProperties:
    def test_extracts_edge_with_props(self, tmp_path):
        doc = tmp_path / "graph-model.md"
        doc.write_text(
            "| Relationship | From → To | Properties | What it encodes |\n"
            "|---|---|---|---|\n"
            "| `DEMANDS` | Region → Occupation | employment, annual_wage | demand |\n"
            "| `OFFERS` | College → Department | — | a college operates a dept |\n"
        )
        result = extract_documented_edge_properties(doc)
        assert result["DEMANDS"] == {"employment", "annual_wage"}
        assert result["OFFERS"] == set()

    def test_unions_overloaded_relationship(self, tmp_path):
        # IN_MARKET appears twice with the same (empty) props.
        doc = tmp_path / "graph-model.md"
        doc.write_text(
            "| Relationship | From → To | Properties | What it encodes |\n"
            "|---|---|---|---|\n"
            "| `IN_MARKET` | College → Region | — | college in market |\n"
            "| `IN_MARKET` | Employer → Region | — | employer in market |\n"
        )
        result = extract_documented_edge_properties(doc)
        assert result["IN_MARKET"] == set()


# ── iter_cypher_strings ───────────────────────────────────────────────


class TestIterCypherStrings:
    def test_finds_cypher_in_string_constants(self, tmp_path):
        py = tmp_path / "loader.py"
        py.write_text(
            'def f():\n'
            '    session.run("MERGE (c:College {name: $name})")\n'
            '    print("not cypher")\n'
        )
        strings = list(iter_cypher_strings(py))
        assert any("MERGE" in s for s in strings)
        assert not any("not cypher" in s for s in strings)

    def test_finds_triple_quoted_cypher(self, tmp_path):
        py = tmp_path / "loader.py"
        py.write_text(
            'def f():\n'
            '    session.run("""\n'
            '        MATCH (c:Course)\n'
            '        SET c.name = $name\n'
            '    """)\n'
        )
        strings = list(iter_cypher_strings(py))
        assert len(strings) == 1
        assert "MATCH" in strings[0]


# ── extract_properties_from_cypher ────────────────────────────────────


class TestExtractPropertiesFromCypher:
    def test_inline_props_from_merge(self):
        nodes, edges = extract_properties_from_cypher(
            "MERGE (c:College {name: $name, city: $city})"
        )
        assert nodes == {"College": {"name", "city"}}
        assert edges == {}

    def test_set_clause_props(self):
        nodes, edges = extract_properties_from_cypher(
            "MERGE (c:College {name: $name}) "
            "ON CREATE SET c.city = $city, c.state = $state"
        )
        assert nodes["College"] == {"name", "city", "state"}

    def test_composite_key(self):
        nodes, _ = extract_properties_from_cypher(
            "MERGE (c:Course {code: $code, college: $college})"
        )
        assert nodes["Course"] == {"code", "college"}

    def test_edge_inline_props(self):
        _, edges = extract_properties_from_cypher(
            "CREATE (s)-[:ENROLLED_IN {grade: $g, term: $t, status: $st}]->(c)"
        )
        assert edges["ENROLLED_IN"] == {"grade", "term", "status"}

    def test_edge_set_props(self):
        _, edges = extract_properties_from_cypher(
            "MERGE (r)-[d:DEMANDS]->(o) "
            "SET d.employment = $e, d.annual_wage = $w"
        )
        assert edges["DEMANDS"] == {"employment", "annual_wage"}

    def test_ignores_unbound_var_refs(self):
        # `row.foo` is an UNWIND row reference, not a node property.
        nodes, _ = extract_properties_from_cypher(
            "UNWIND $batch AS row "
            "MERGE (e:Employer {name: row.name}) "
            "SET e.sector = row.sector"
        )
        assert nodes["Employer"] == {"name", "sector"}

    def test_per_string_scoping(self):
        # Same var bound to different labels in different fragments — only
        # one fragment should produce one binding.
        nodes_a, _ = extract_properties_from_cypher(
            "MATCH (c:Course) RETURN c.name"
        )
        nodes_b, _ = extract_properties_from_cypher(
            "MATCH (c:College) RETURN c.city"
        )
        assert nodes_a == {"Course": {"name"}}
        assert nodes_b == {"College": {"city"}}


# ── extract_actual_properties ─────────────────────────────────────────


class TestExtractActualProperties:
    def test_walks_loader_files(self, tmp_path):
        loader_dir = tmp_path / "backend" / "courses"
        loader_dir.mkdir(parents=True)
        (loader_dir / "load.py").write_text(
            'def load():\n'
            '    session.run(\n'
            '        "MERGE (c:College {name: $name}) '
            'ON CREATE SET c.city = $city"\n'
            '    )\n'
        )
        nodes, edges = extract_actual_properties(tmp_path)
        assert nodes["College"] == {"name", "city"}
        assert edges == {}


# ── GraphPropertiesCheck end-to-end ───────────────────────────────────


def _make_repo(tmp_path: Path, doc_text: str, loader_text: str) -> None:
    doc_dir = tmp_path / "docs" / "architecture"
    doc_dir.mkdir(parents=True)
    (doc_dir / "graph-model.md").write_text(doc_text)

    loader_dir = tmp_path / "backend" / "courses"
    loader_dir.mkdir(parents=True)
    (loader_dir / "load.py").write_text(loader_text)


class TestGraphPropertiesCheck:
    def test_passes_when_docs_and_loaders_agree(self, tmp_path):
        _make_repo(
            tmp_path,
            doc_text=(
                "| Node | Key properties | Constraint | What it represents |\n"
                "|---|---|---|---|\n"
                "| **College** | name, city | `name UNIQUE` | A college |\n"
            ),
            loader_text=(
                'def load():\n'
                '    session.run(\n'
                '        "MERGE (c:College {name: $name}) '
                'ON CREATE SET c.city = $city"\n'
                '    )\n'
            ),
        )
        result = GraphPropertiesCheck().run(tmp_path)
        assert result.status == Status.PASS, result.details

    def test_fails_when_loader_has_extra_property(self, tmp_path):
        _make_repo(
            tmp_path,
            doc_text=(
                "| Node | Key properties | Constraint | What it represents |\n"
                "|---|---|---|---|\n"
                "| **College** | name | `name UNIQUE` | A college |\n"
            ),
            loader_text=(
                'def load():\n'
                '    session.run(\n'
                '        "MERGE (c:College {name: $name}) '
                'ON CREATE SET c.secret = $secret"\n'
                '    )\n'
            ),
        )
        result = GraphPropertiesCheck().run(tmp_path)
        assert result.status == Status.FAIL
        assert "College" in result.details
        assert "secret" in result.details

    def test_fails_when_docs_have_extra_property(self, tmp_path):
        _make_repo(
            tmp_path,
            doc_text=(
                "| Node | Key properties | Constraint | What it represents |\n"
                "|---|---|---|---|\n"
                "| **College** | name, ghost | `name UNIQUE` | A college |\n"
            ),
            loader_text=(
                'def load():\n'
                '    session.run("MERGE (c:College {name: $name})")\n'
            ),
        )
        result = GraphPropertiesCheck().run(tmp_path)
        assert result.status == Status.FAIL
        assert "ghost" in result.details

    def test_fails_when_edge_property_undocumented(self, tmp_path):
        _make_repo(
            tmp_path,
            doc_text=(
                "| Node | Key properties | Constraint | What it represents |\n"
                "|---|---|---|---|\n"
                "| **Region** | name | `name UNIQUE` | A region |\n"
                "| **Occupation** | soc_code | `soc_code UNIQUE` | An occupation |\n"
                "\n"
                "| Relationship | From → To | Properties | What it encodes |\n"
                "|---|---|---|---|\n"
                "| `DEMANDS` | Region → Occupation | — | regional demand |\n"
            ),
            loader_text=(
                'def load():\n'
                '    session.run(\n'
                '        "MERGE (r:Region {name: $r}) "\n'
                '        "MERGE (o:Occupation {soc_code: $s}) "\n'
                '        "MERGE (r)-[d:DEMANDS]->(o) SET d.annual_wage = $w"\n'
                '    )\n'
            ),
        )
        result = GraphPropertiesCheck().run(tmp_path)
        assert result.status == Status.FAIL
        assert "DEMANDS" in result.details
        assert "annual_wage" in result.details

    def test_skips_when_doc_missing(self, tmp_path):
        loader_dir = tmp_path / "backend" / "courses"
        loader_dir.mkdir(parents=True)
        (loader_dir / "load.py").write_text("# empty\n")
        result = GraphPropertiesCheck().run(tmp_path)
        assert result.status == Status.SKIP

    def test_skips_when_loaders_missing(self, tmp_path):
        doc_dir = tmp_path / "docs" / "architecture"
        doc_dir.mkdir(parents=True)
        (doc_dir / "graph-model.md").write_text("# empty\n")
        result = GraphPropertiesCheck().run(tmp_path)
        assert result.status == Status.SKIP
