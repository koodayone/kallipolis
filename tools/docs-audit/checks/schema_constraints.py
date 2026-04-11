"""schema_constraints check: documented schema constraints match schema.py.

This check verifies that the constraint claims in the node-type table of
docs/architecture/graph-model.md match the actual `CREATE CONSTRAINT`
statements in backend/ontology/schema.py. It is the most consequential
check in the audit because the schema is the structural contract of the
ontology, and drift between the documented schema and the actual schema
is what bit us in the manual audit that prompted the audit infrastructure.

Conventions this check relies on (see docs/conventions.md):
- The graph model document has a node-type table with columns
  Node, Key properties, Constraint, What it represents
- The Node cell uses bold formatting: `**College**`
- The Constraint cell uses inline code: `` `name UNIQUE` `` or
  `` `(code, college) UNIQUE` ``
- backend/ontology/schema.py uses statements of the form
  CREATE CONSTRAINT <name> IF NOT EXISTS FOR (n:<NodeType>)
  REQUIRE <expr> IS <UNIQUE|NOT NULL>

The check compares both directions:
- Every documented constraint must exist in schema.py
- Every constraint in schema.py must be documented
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from extractors.markdown import iter_markdown_lines

from .base import Check, CheckResult, Status


# ── Patterns ──────────────────────────────────────────────────────────

# Documented row in graph-model.md table:
# | **NodeType** | properties | `constraint` | description |
DOC_ROW_RE = re.compile(
    r"^\s*\|\s*\*\*(\w+)\*\*\s*\|"   # Node name in bold (captured)
    r"[^|]*\|"                          # Properties cell (skipped)
    r"\s*`([^`]+)`\s*\|"                # Constraint in inline code (captured)
)

# Schema constraint in schema.py:
# CREATE CONSTRAINT <name> IF NOT EXISTS FOR (n:<NodeType>) REQUIRE <expr> IS <TYPE>
SCHEMA_CONSTRAINT_RE = re.compile(
    r"CREATE CONSTRAINT \w+ IF NOT EXISTS\s+"
    r"FOR\s*\(n:(\w+)\)\s+"
    r"REQUIRE\s+(.+?)\s+IS\s+(UNIQUE|NOT NULL)"
)

# Property reference in a constraint expression: n.<prop>
PROP_REF_RE = re.compile(r"n\.(\w+)")

# Documented constraint format: "name UNIQUE" or "(code, college) UNIQUE"
DOC_CONSTRAINT_RE = re.compile(r"^(.+?)\s+(UNIQUE|NOT NULL)$")


# ── Data types ────────────────────────────────────────────────────────


@dataclass(frozen=True)
class Constraint:
    """A schema constraint on a node type.

    Frozen so it can be used as a dictionary key and compared by value.
    Properties are stored as a tuple to preserve order (composite
    constraints depend on the order of property names).
    """

    node_type: str
    properties: Tuple[str, ...]
    constraint_type: str  # "UNIQUE" or "NOT NULL"

    def __str__(self) -> str:
        if len(self.properties) == 1:
            return f"{self.properties[0]} {self.constraint_type}"
        return f"({', '.join(self.properties)}) {self.constraint_type}"


# ── Parsers ───────────────────────────────────────────────────────────


def parse_doc_constraint(s: str) -> Optional[Tuple[Tuple[str, ...], str]]:
    """Parse a documented constraint string.

    Examples:
        'name UNIQUE'              -> (('name',), 'UNIQUE')
        '(code, college) UNIQUE'   -> (('code', 'college'), 'UNIQUE')
        'uuid NOT NULL'            -> (('uuid',), 'NOT NULL')

    Returns None if the string does not match the expected format.
    """
    match = DOC_CONSTRAINT_RE.match(s.strip())
    if not match:
        return None

    prop_expr = match.group(1).strip()
    constraint_type = match.group(2)

    if prop_expr.startswith("(") and prop_expr.endswith(")"):
        inner = prop_expr[1:-1]
        properties = tuple(p.strip() for p in inner.split(","))
    else:
        properties = (prop_expr,)

    return (properties, constraint_type)


def parse_schema_property_expr(expr: str) -> Tuple[str, ...]:
    """Extract property names from a Cypher constraint expression.

    Examples:
        'n.name'                   -> ('name',)
        '(n.code, n.college)'      -> ('code', 'college')
    """
    return tuple(PROP_REF_RE.findall(expr))


# ── Extractors ────────────────────────────────────────────────────────


def extract_documented_constraints(doc_file: Path) -> Dict[str, Constraint]:
    """Extract documented schema constraints from the graph model document.

    Walks the document looking for table rows in the form
    `| **NodeType** | ... | \`constraint\` | ... |`
    and parses each constraint cell into a Constraint object.

    Returns a dict mapping node type name to Constraint.
    """
    constraints: Dict[str, Constraint] = {}

    for _lineno, line in iter_markdown_lines(doc_file):
        match = DOC_ROW_RE.match(line)
        if not match:
            continue

        node_type = match.group(1)
        constraint_str = match.group(2)

        parsed = parse_doc_constraint(constraint_str)
        if not parsed:
            continue

        properties, constraint_type = parsed
        constraints[node_type] = Constraint(
            node_type=node_type,
            properties=properties,
            constraint_type=constraint_type,
        )

    return constraints


def extract_actual_constraints(schema_file: Path) -> Dict[str, Constraint]:
    """Extract actual schema constraints from schema.py.

    Walks the schema file looking for `CREATE CONSTRAINT ...` statements
    and parses each one into a Constraint object.

    Returns a dict mapping node type name to Constraint.
    """
    constraints: Dict[str, Constraint] = {}
    content = schema_file.read_text()

    for match in SCHEMA_CONSTRAINT_RE.finditer(content):
        node_type = match.group(1)
        expr = match.group(2)
        constraint_type = match.group(3)

        properties = parse_schema_property_expr(expr)
        if not properties:
            continue

        constraints[node_type] = Constraint(
            node_type=node_type,
            properties=properties,
            constraint_type=constraint_type,
        )

    return constraints


# ── The check ─────────────────────────────────────────────────────────


class SchemaConstraintsCheck(Check):
    name = "schema_constraints"
    description = (
        "Schema constraints in graph-model.md match backend/ontology/schema.py"
    )

    def run(self, repo_root: Path) -> CheckResult:
        doc_file = repo_root / "docs" / "architecture" / "graph-model.md"
        schema_file = repo_root / "backend" / "ontology" / "schema.py"

        if not doc_file.exists():
            return CheckResult(
                check=self.name,
                status=Status.SKIP,
                details=f"Graph model document not found at {doc_file}",
            )
        if not schema_file.exists():
            return CheckResult(
                check=self.name,
                status=Status.SKIP,
                details=f"Schema file not found at {schema_file}",
            )

        documented = extract_documented_constraints(doc_file)
        actual = extract_actual_constraints(schema_file)

        all_node_types = set(documented.keys()) | set(actual.keys())
        items_checked = len(all_node_types)

        problems: List[str] = []

        # Direction 1: every documented constraint must exist in schema
        for node_type in sorted(documented.keys()):
            doc_constraint = documented[node_type]
            if node_type not in actual:
                problems.append(
                    f"  {node_type}: documented as `{doc_constraint}`, "
                    f"but no constraint found in schema.py for this node type"
                )
                continue
            actual_constraint = actual[node_type]
            if doc_constraint != actual_constraint:
                problems.append(
                    f"  {node_type}: mismatch\n"
                    f"      docs say:  `{doc_constraint}`\n"
                    f"      schema.py: `{actual_constraint}`"
                )

        # Direction 2: every schema constraint must be documented
        for node_type in sorted(actual.keys()):
            if node_type not in documented:
                actual_constraint = actual[node_type]
                problems.append(
                    f"  {node_type}: schema.py has `{actual_constraint}`, "
                    f"but no constraint is documented for this node type "
                    f"in graph-model.md"
                )

        if not problems:
            return CheckResult(
                check=self.name,
                status=Status.PASS,
                items_checked=items_checked,
            )

        details_lines = [
            f"Found {len(problems)} schema constraint discrepancies "
            f"across {items_checked} node types:"
        ]
        details_lines.extend(problems)

        return CheckResult(
            check=self.name,
            status=Status.FAIL,
            details="\n".join(details_lines),
            items_checked=items_checked,
            resolution=(
                "For each discrepancy, either update docs/architecture/graph-model.md "
                "to match the schema, or update backend/ontology/schema.py to match "
                "the documented constraint. The two files must agree on the "
                "constraint shape (properties and constraint type)."
            ),
        )
