"""graph_properties check: documented node and edge properties match the loaders.

Verifies that the property lists in the node and relationship tables of
docs/architecture/graph-model.md match the properties actually set by
the Cypher MERGE/CREATE/SET statements in the loader files. The check
runs in both directions:

- every documented property must be set by a loader
- every property set by a loader must be documented

This is the second-most consequential check in the audit (after
schema_constraints). Property drift is the class of error that hid
Employer.description and Employer.website from the docs in the manual
audit that prompted the audit infrastructure.

How extraction works:

The loader files contain Cypher embedded in Python string literals. We
walk every string literal via the Python AST, filter to those that
contain Cypher keywords, and parse each one as a single scope. Within
that scope:

1. Every `(var:Label {prop: ..., ...})` pattern binds `var` to `Label`
   and contributes the brace keys as properties of `Label`.
2. Every `[var:RelType {prop: ..., ...}]` pattern does the same for
   relationships, with `var` optional.
3. Every `var.prop` reference (in SET / WHERE / RETURN / WITH clauses)
   is attributed to the bound label or relationship type.

Variable scope is per Cypher string, so the same short name (`c`, `r`,
`s`) bound to different labels in different `session.run` calls does
not collide.
"""

from __future__ import annotations

import ast
import re
from collections import defaultdict
from pathlib import Path
from typing import Dict, Iterator, List, Set, Tuple

from extractors.markdown import iter_markdown_lines

from .base import Check, CheckResult, Status


# ── Loader files to scan ──────────────────────────────────────────────

LOADER_FILES = [
    "backend/courses/load.py",
    "backend/students/generate.py",
    "backend/pipeline/load_skills.py",
    "backend/occupations/load.py",
    "backend/employers/load.py",
]


# ── Patterns ──────────────────────────────────────────────────────────

# Documented node row in graph-model.md:
# | **NodeType** | prop1, prop2, ... | `constraint` | description |
DOC_NODE_ROW_RE = re.compile(
    r"^\s*\|\s*\*\*(\w+)\*\*\s*\|"   # Node name in bold (captured)
    r"\s*([^|]+?)\s*\|"                # Properties cell (captured)
    r"\s*`[^`]+`\s*\|"                 # Constraint cell (skipped)
)

# Documented edge row in graph-model.md:
# | `REL_NAME` | From → To | props or — | description |
DOC_EDGE_ROW_RE = re.compile(
    r"^\s*\|\s*`(\w+)`\s*\|"           # Relationship name in code (captured)
    r"\s*[^|]+?\s*\|"                   # From → To cell (skipped)
    r"\s*([^|]+?)\s*\|"                 # Properties cell (captured)
)

# Cypher node pattern: (var:Label) or (var:Label {prop: val, ...})
NODE_PATTERN_RE = re.compile(
    r"\(\s*(\w+)\s*:\s*(\w+)\s*(\{[^}]*\})?\s*\)"
)

# Cypher edge pattern: [:RelType] or [var:RelType] or [var:RelType {props}]
EDGE_PATTERN_RE = re.compile(
    r"\[\s*(\w+)?\s*:\s*(\w+)\s*(\{[^}]*\})?\s*\]"
)

# Property keys inside a `{...}` map literal: word followed by colon
INLINE_PROP_RE = re.compile(r"(\w+)\s*:")

# Property reference: var.prop
PROP_REF_RE = re.compile(r"\b(\w+)\.(\w+)\b")

# Strings that look like Cypher must contain at least one of these.
CYPHER_KEYWORDS = ("MERGE", "CREATE", "MATCH", "SET")


# ── Doc extractors ────────────────────────────────────────────────────


def parse_doc_property_list(cell: str) -> Set[str]:
    """Parse a comma-separated property list from a doc table cell.

    An em-dash, a hyphen, or an empty cell mean "no properties".
    """
    s = cell.strip()
    if not s or s in ("—", "-"):
        return set()
    return {p.strip() for p in s.split(",") if p.strip()}


def extract_documented_node_properties(doc_file: Path) -> Dict[str, Set[str]]:
    """Extract documented node properties from the graph model document."""
    result: Dict[str, Set[str]] = {}
    for _, line in iter_markdown_lines(doc_file):
        match = DOC_NODE_ROW_RE.match(line)
        if not match:
            continue
        node_type = match.group(1)
        result[node_type] = parse_doc_property_list(match.group(2))
    return result


def extract_documented_edge_properties(doc_file: Path) -> Dict[str, Set[str]]:
    """Extract documented edge properties from the graph model document.

    If the same relationship type appears in multiple rows (e.g., the
    overloaded `IN_MARKET` row for College→Region and Employer→Region),
    the property sets are unioned.
    """
    result: Dict[str, Set[str]] = defaultdict(set)
    for _, line in iter_markdown_lines(doc_file):
        match = DOC_EDGE_ROW_RE.match(line)
        if not match:
            continue
        rel_type = match.group(1)
        result[rel_type] |= parse_doc_property_list(match.group(2))
    return dict(result)


# ── Loader extractors ─────────────────────────────────────────────────


def iter_cypher_strings(source_file: Path) -> Iterator[str]:
    """Yield string literals from a Python source file that look like Cypher.

    Uses the AST so f-strings and concatenations are handled correctly:
    a plain string constant is yielded as-is; an f-string is currently
    skipped (no Cypher in this codebase relies on f-string interpolation).
    """
    try:
        tree = ast.parse(source_file.read_text())
    except SyntaxError:
        return
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            s = node.value
            if any(kw in s for kw in CYPHER_KEYWORDS):
                yield s


def extract_properties_from_cypher(
    cypher: str,
) -> Tuple[Dict[str, Set[str]], Dict[str, Set[str]]]:
    """Extract node and edge properties from a single Cypher fragment.

    Returns `(node_props, edge_props)`. Each maps a label or relationship
    type to the set of property names referenced for it inside the
    fragment, as either inline `{...}` keys or `var.prop` references
    where `var` was bound by a pattern in the same fragment.
    """
    node_bindings: Dict[str, str] = {}
    edge_bindings: Dict[str, str] = {}
    node_props: Dict[str, Set[str]] = defaultdict(set)
    edge_props: Dict[str, Set[str]] = defaultdict(set)

    # Pass 1: collect bindings and inline brace properties.
    for match in NODE_PATTERN_RE.finditer(cypher):
        var, label, brace = match.group(1), match.group(2), match.group(3)
        node_bindings[var] = label
        if brace:
            for prop in INLINE_PROP_RE.findall(brace):
                node_props[label].add(prop)

    for match in EDGE_PATTERN_RE.finditer(cypher):
        var, rel, brace = match.group(1), match.group(2), match.group(3)
        if var:
            edge_bindings[var] = rel
        if brace:
            for prop in INLINE_PROP_RE.findall(brace):
                edge_props[rel].add(prop)

    # Pass 2: var.prop references — SET, WHERE, RETURN, WITH, ORDER BY.
    for match in PROP_REF_RE.finditer(cypher):
        var, prop = match.group(1), match.group(2)
        if var in node_bindings:
            node_props[node_bindings[var]].add(prop)
        elif var in edge_bindings:
            edge_props[edge_bindings[var]].add(prop)

    return dict(node_props), dict(edge_props)


def extract_actual_properties(
    repo_root: Path,
) -> Tuple[Dict[str, Set[str]], Dict[str, Set[str]]]:
    """Walk all loader files and aggregate node and edge properties."""
    all_node_props: Dict[str, Set[str]] = defaultdict(set)
    all_edge_props: Dict[str, Set[str]] = defaultdict(set)

    for rel_path in LOADER_FILES:
        path = repo_root / rel_path
        if not path.exists():
            continue
        for cypher in iter_cypher_strings(path):
            node_props, edge_props = extract_properties_from_cypher(cypher)
            for label, props in node_props.items():
                all_node_props[label] |= props
            for rel, props in edge_props.items():
                all_edge_props[rel] |= props

    return dict(all_node_props), dict(all_edge_props)


# ── The check ─────────────────────────────────────────────────────────


class GraphPropertiesCheck(Check):
    name = "graph_properties"
    description = (
        "Node and edge properties in graph-model.md match backend loaders"
    )

    def run(self, repo_root: Path) -> CheckResult:
        doc_file = repo_root / "docs" / "architecture" / "graph-model.md"

        if not doc_file.exists():
            return CheckResult(
                check=self.name,
                status=Status.SKIP,
                details=f"Graph model document not found at {doc_file}",
            )

        loader_paths = [repo_root / p for p in LOADER_FILES]
        if not any(p.exists() for p in loader_paths):
            return CheckResult(
                check=self.name,
                status=Status.SKIP,
                details="No loader files found",
            )

        doc_node_props = extract_documented_node_properties(doc_file)
        doc_edge_props = extract_documented_edge_properties(doc_file)
        actual_node_props, actual_edge_props = extract_actual_properties(repo_root)

        problems: List[str] = []

        # ── Compare node properties ───────────────────────────────────
        all_nodes = set(doc_node_props) | set(actual_node_props)
        for node in sorted(all_nodes):
            doc_props = doc_node_props.get(node, set())
            actual = actual_node_props.get(node, set())

            if node not in doc_node_props:
                problems.append(
                    f"  Node {node}: loaders set {sorted(actual)} "
                    f"but no row in graph-model.md"
                )
                continue
            if node not in actual_node_props:
                problems.append(
                    f"  Node {node}: documented as {sorted(doc_props)} "
                    f"but no loader sets these"
                )
                continue

            missing_in_code = doc_props - actual
            extra_in_code = actual - doc_props
            if missing_in_code or extra_in_code:
                lines = [f"  Node {node}: property mismatch"]
                if missing_in_code:
                    lines.append(
                        f"      docs have but loaders don't set: "
                        f"{sorted(missing_in_code)}"
                    )
                if extra_in_code:
                    lines.append(
                        f"      loaders set but docs don't list: "
                        f"{sorted(extra_in_code)}"
                    )
                problems.append("\n".join(lines))

        # ── Compare edge properties ───────────────────────────────────
        all_edges = set(doc_edge_props) | set(actual_edge_props)
        for edge in sorted(all_edges):
            doc_props = doc_edge_props.get(edge, set())
            actual = actual_edge_props.get(edge, set())

            if edge not in doc_edge_props:
                problems.append(
                    f"  Edge {edge}: loaders set {sorted(actual)} "
                    f"but no row in graph-model.md"
                )
                continue
            if edge not in actual_edge_props and doc_props:
                problems.append(
                    f"  Edge {edge}: documented as {sorted(doc_props)} "
                    f"but no loader sets these"
                )
                continue

            missing_in_code = doc_props - actual
            extra_in_code = actual - doc_props
            if missing_in_code or extra_in_code:
                lines = [f"  Edge {edge}: property mismatch"]
                if missing_in_code:
                    lines.append(
                        f"      docs have but loaders don't set: "
                        f"{sorted(missing_in_code)}"
                    )
                if extra_in_code:
                    lines.append(
                        f"      loaders set but docs don't list: "
                        f"{sorted(extra_in_code)}"
                    )
                problems.append("\n".join(lines))

        items_checked = len(all_nodes) + len(all_edges)

        if not problems:
            return CheckResult(
                check=self.name,
                status=Status.PASS,
                items_checked=items_checked,
            )

        details_lines = [
            f"Found {len(problems)} property discrepancies "
            f"across {len(all_nodes)} node types and "
            f"{len(all_edges)} relationship types:"
        ]
        details_lines.extend(problems)

        return CheckResult(
            check=self.name,
            status=Status.FAIL,
            details="\n".join(details_lines),
            items_checked=items_checked,
            resolution=(
                "For each discrepancy, either update "
                "docs/architecture/graph-model.md to match the loaders or "
                "update the loader to match the docs. The two sources must "
                "agree on the set of properties for every node and "
                "relationship type."
            ),
        )
