"""Unit tests for the schema_constraints check and its helpers."""

from pathlib import Path

from checks.base import Status
from checks.schema_constraints import (
    Constraint,
    SchemaConstraintsCheck,
    extract_actual_constraints,
    extract_documented_constraints,
    parse_doc_constraint,
    parse_schema_property_expr,
)


# ── parse_doc_constraint ──────────────────────────────────────────────


class TestParseDocConstraint:
    def test_single_property_unique(self):
        result = parse_doc_constraint("name UNIQUE")
        assert result == (("name",), "UNIQUE")

    def test_composite_unique(self):
        result = parse_doc_constraint("(code, college) UNIQUE")
        assert result == (("code", "college"), "UNIQUE")

    def test_three_property_composite(self):
        result = parse_doc_constraint("(a, b, c) UNIQUE")
        assert result == (("a", "b", "c"), "UNIQUE")

    def test_not_null(self):
        result = parse_doc_constraint("name NOT NULL")
        assert result == (("name",), "NOT NULL")

    def test_strips_whitespace(self):
        result = parse_doc_constraint("  name UNIQUE  ")
        assert result == (("name",), "UNIQUE")

    def test_invalid_returns_none(self):
        assert parse_doc_constraint("garbage") is None
        assert parse_doc_constraint("") is None
        assert parse_doc_constraint("name") is None  # missing constraint type


# ── parse_schema_property_expr ────────────────────────────────────────


class TestParseSchemaPropertyExpr:
    def test_single_property(self):
        assert parse_schema_property_expr("n.name") == ("name",)

    def test_composite_property(self):
        assert parse_schema_property_expr("(n.code, n.college)") == ("code", "college")

    def test_handles_extra_whitespace(self):
        assert parse_schema_property_expr("n.name ") == ("name",)
        assert parse_schema_property_expr("(n.code,  n.college)") == ("code", "college")


# ── Constraint string representation ─────────────────────────────────


class TestConstraintStr:
    def test_single_property(self):
        c = Constraint(node_type="College", properties=("name",), constraint_type="UNIQUE")
        assert str(c) == "name UNIQUE"

    def test_composite(self):
        c = Constraint(
            node_type="Course",
            properties=("code", "college"),
            constraint_type="UNIQUE",
        )
        assert str(c) == "(code, college) UNIQUE"


# ── extract_documented_constraints ───────────────────────────────────


class TestExtractDocumentedConstraints:
    def test_extracts_simple_table(self, tmp_path):
        doc = tmp_path / "graph-model.md"
        doc.write_text(
            "## Node types\n"
            "\n"
            "| Node | Key properties | Constraint | What it represents |\n"
            "|---|---|---|---|\n"
            "| **College** | name, city | `name UNIQUE` | A college |\n"
            "| **Course** | code, college, name | `(code, college) UNIQUE` | A course |\n"
        )
        constraints = extract_documented_constraints(doc)
        assert len(constraints) == 2
        assert constraints["College"] == Constraint(
            node_type="College", properties=("name",), constraint_type="UNIQUE"
        )
        assert constraints["Course"] == Constraint(
            node_type="Course",
            properties=("code", "college"),
            constraint_type="UNIQUE",
        )

    def test_extracts_from_multiple_tables(self, tmp_path):
        doc = tmp_path / "graph-model.md"
        doc.write_text(
            "## Curriculum side\n"
            "\n"
            "| Node | Key properties | Constraint | What it represents |\n"
            "|---|---|---|---|\n"
            "| **College** | name | `name UNIQUE` | A college |\n"
            "\n"
            "## Industry side\n"
            "\n"
            "| Node | Key properties | Constraint | What it represents |\n"
            "|---|---|---|---|\n"
            "| **Region** | name | `name UNIQUE` | A region |\n"
        )
        constraints = extract_documented_constraints(doc)
        assert "College" in constraints
        assert "Region" in constraints

    def test_skips_rows_in_code_blocks(self, tmp_path):
        doc = tmp_path / "graph-model.md"
        doc.write_text(
            "Real:\n"
            "\n"
            "| Node | Key properties | Constraint | What it represents |\n"
            "|---|---|---|---|\n"
            "| **College** | name | `name UNIQUE` | A college |\n"
            "\n"
            "```markdown\n"
            "| **FakeNode** | x | `x UNIQUE` | not real |\n"
            "```\n"
        )
        constraints = extract_documented_constraints(doc)
        assert "College" in constraints
        assert "FakeNode" not in constraints

    def test_skips_relationship_rows(self, tmp_path):
        # Relationship table rows start with `RELATIONSHIP_NAME` (in code spans),
        # not with **NodeType**, so they should not be parsed as constraints.
        doc = tmp_path / "graph-model.md"
        doc.write_text(
            "## Relationships\n"
            "\n"
            "| Relationship | From | To | What it encodes |\n"
            "|---|---|---|---|\n"
            "| `OFFERS` | College | Department | A college operates a department |\n"
        )
        constraints = extract_documented_constraints(doc)
        assert constraints == {}


# ── extract_actual_constraints ────────────────────────────────────────


class TestExtractActualConstraints:
    def test_extracts_simple_constraint(self, tmp_path):
        schema = tmp_path / "schema.py"
        schema.write_text(
            'session.run("CREATE CONSTRAINT college_name IF NOT EXISTS '
            'FOR (n:College) REQUIRE n.name IS UNIQUE")\n'
        )
        constraints = extract_actual_constraints(schema)
        assert constraints["College"] == Constraint(
            node_type="College", properties=("name",), constraint_type="UNIQUE"
        )

    def test_extracts_composite_constraint(self, tmp_path):
        schema = tmp_path / "schema.py"
        schema.write_text(
            'session.run("CREATE CONSTRAINT course_code_college IF NOT EXISTS '
            'FOR (n:Course) REQUIRE (n.code, n.college) IS UNIQUE")\n'
        )
        constraints = extract_actual_constraints(schema)
        assert constraints["Course"] == Constraint(
            node_type="Course",
            properties=("code", "college"),
            constraint_type="UNIQUE",
        )

    def test_extracts_multiple_constraints(self, tmp_path):
        schema = tmp_path / "schema.py"
        schema.write_text(
            'constraints = [\n'
            '    "CREATE CONSTRAINT college_name IF NOT EXISTS '
            'FOR (n:College) REQUIRE n.name IS UNIQUE",\n'
            '    "CREATE CONSTRAINT department_name IF NOT EXISTS '
            'FOR (n:Department) REQUIRE n.name IS UNIQUE",\n'
            '    "CREATE CONSTRAINT student_uuid IF NOT EXISTS '
            'FOR (n:Student) REQUIRE n.uuid IS UNIQUE",\n'
            ']\n'
        )
        constraints = extract_actual_constraints(schema)
        assert len(constraints) == 3
        assert "College" in constraints
        assert "Department" in constraints
        assert "Student" in constraints


# ── SchemaConstraintsCheck end-to-end ─────────────────────────────────


def _make_minimal_repo(
    tmp_path: Path, doc_text: str, schema_text: str
) -> None:
    """Create a minimal repo with a graph model doc and a schema.py."""
    doc_dir = tmp_path / "docs" / "architecture"
    doc_dir.mkdir(parents=True)
    (doc_dir / "graph-model.md").write_text(doc_text)

    schema_dir = tmp_path / "backend" / "ontology"
    schema_dir.mkdir(parents=True)
    (schema_dir / "schema.py").write_text(schema_text)


class TestSchemaConstraintsCheck:
    def test_passes_when_docs_and_schema_agree(self, tmp_path):
        _make_minimal_repo(
            tmp_path,
            doc_text=(
                "| Node | Key properties | Constraint | What it represents |\n"
                "|---|---|---|---|\n"
                "| **College** | name | `name UNIQUE` | A college |\n"
            ),
            schema_text=(
                'session.run("CREATE CONSTRAINT college_name IF NOT EXISTS '
                'FOR (n:College) REQUIRE n.name IS UNIQUE")\n'
            ),
        )
        result = SchemaConstraintsCheck().run(tmp_path)
        assert result.status == Status.PASS, result.details
        assert result.items_checked == 1

    def test_fails_when_documented_constraint_missing_from_schema(self, tmp_path):
        _make_minimal_repo(
            tmp_path,
            doc_text=(
                "| Node | Key properties | Constraint | What it represents |\n"
                "|---|---|---|---|\n"
                "| **College** | name | `name UNIQUE` | A college |\n"
                "| **Foo** | name | `name UNIQUE` | A foo |\n"
            ),
            schema_text=(
                'session.run("CREATE CONSTRAINT college_name IF NOT EXISTS '
                'FOR (n:College) REQUIRE n.name IS UNIQUE")\n'
            ),
        )
        result = SchemaConstraintsCheck().run(tmp_path)
        assert result.status == Status.FAIL
        assert "Foo" in result.details

    def test_fails_when_schema_has_undocumented_constraint(self, tmp_path):
        _make_minimal_repo(
            tmp_path,
            doc_text=(
                "| Node | Key properties | Constraint | What it represents |\n"
                "|---|---|---|---|\n"
                "| **College** | name | `name UNIQUE` | A college |\n"
            ),
            schema_text=(
                'CREATE CONSTRAINT college_name IF NOT EXISTS '
                'FOR (n:College) REQUIRE n.name IS UNIQUE\n'
                'CREATE CONSTRAINT secret_node IF NOT EXISTS '
                'FOR (n:Secret) REQUIRE n.id IS UNIQUE\n'
            ),
        )
        result = SchemaConstraintsCheck().run(tmp_path)
        assert result.status == Status.FAIL
        assert "Secret" in result.details

    def test_fails_when_property_mismatch(self, tmp_path):
        _make_minimal_repo(
            tmp_path,
            doc_text=(
                "| Node | Key properties | Constraint | What it represents |\n"
                "|---|---|---|---|\n"
                "| **Course** | code | `code UNIQUE` | A course |\n"
            ),
            schema_text=(
                'CREATE CONSTRAINT course_code_college IF NOT EXISTS '
                'FOR (n:Course) REQUIRE (n.code, n.college) IS UNIQUE\n'
            ),
        )
        result = SchemaConstraintsCheck().run(tmp_path)
        assert result.status == Status.FAIL
        assert "Course" in result.details
        assert "mismatch" in result.details.lower()

    def test_skips_when_doc_missing(self, tmp_path):
        schema_dir = tmp_path / "backend" / "ontology"
        schema_dir.mkdir(parents=True)
        (schema_dir / "schema.py").write_text("# empty\n")
        result = SchemaConstraintsCheck().run(tmp_path)
        assert result.status == Status.SKIP

    def test_skips_when_schema_missing(self, tmp_path):
        doc_dir = tmp_path / "docs" / "architecture"
        doc_dir.mkdir(parents=True)
        (doc_dir / "graph-model.md").write_text("# empty\n")
        result = SchemaConstraintsCheck().run(tmp_path)
        assert result.status == Status.SKIP
