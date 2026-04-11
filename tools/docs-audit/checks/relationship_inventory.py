"""relationship_inventory check: documented edges match the loader patterns.

Verifies that the relationship table in `docs/architecture/graph-model.md`
agrees with the actual `MERGE` / `CREATE` / `MATCH` patterns in the
backend loaders, treating each row as a `(rel_type, from_label,
to_label)` triple. The comparison is bidirectional:

- every documented edge triple must appear in at least one loader
- every edge triple appearing in a loader must be documented

This catches the class of drift behind the manual-audit mistakes around
relationship counts and direction (the "eleven vs ten" miss, missing
edges, reversed arrows). Composite cases like `IN_MARKET` — which is
overloaded for both `College → Region` and `Employer → Region` — are
naturally handled because each row contributes its own triple.

Extraction:

- For each Cypher fragment in a loader file, we first build a
  `var → Label` binding map by walking every `(var:Label ...)` node
  pattern.
- Then we walk every directed path fragment of the form
  `(...)-[edge]->(...)`, take the immediate left and right nodes, and
  resolve their labels from the binding map.
- Each resolved triple is added to the actual edge inventory.
"""

from __future__ import annotations

import ast
import re
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterator, List, Optional, Set, Tuple

from extractors.markdown import iter_markdown_lines

from .base import Check, CheckResult, Status


# ── Files to scan ─────────────────────────────────────────────────────

LOADER_FILES = [
    "backend/pipeline/loader.py",
    "backend/pipeline/students.py",
    "backend/pipeline/load_skills.py",
    "backend/pipeline/industry/loader.py",
    "backend/pipeline/industry/employers.py",
]


# ── Patterns ──────────────────────────────────────────────────────────

# Documented edge row in graph-model.md:
# | `REL_NAME` | FromLabel → ToLabel | props | description |
DOC_EDGE_ROW_RE = re.compile(
    r"^\s*\|\s*`(\w+)`\s*\|"               # rel type (captured)
    r"\s*(\w+)\s*(?:→|->)\s*(\w+)\s*\|"    # from → to (captured)
)

# A `(var:Label ...)` node pattern. The label is optional so the same
# regex can be used to walk path expressions where the label may have
# been declared earlier.
NODE_PATTERN_RE = re.compile(
    r"\(\s*(\w+)\s*(?::\s*(\w+))?\s*(\{[^}]*\})?\s*\)"
)

# A directed edge fragment: `(left)-[edge]->(right)`. We use a lookahead
# for the right-hand node so chains like `(a)-[:R1]->(b)-[:R2]->(c)`
# are walked end-to-end without consuming the shared node.
DIRECTED_EDGE_RE = re.compile(
    r"\(([^)]*)\)\s*-\s*\[([^\]]*)\]\s*->\s*(?=\(([^)]*)\))"
)

# Inside a node-paren content string, the leading word is the var name
# and an optional `:Label` follows.
NODE_CONTENT_RE = re.compile(r"^\s*(\w+)(?:\s*:\s*(\w+))?")

# Inside an edge-bracket content string, the rel type follows a colon.
EDGE_CONTENT_RE = re.compile(r":\s*(\w+)")

CYPHER_KEYWORDS = ("MERGE", "CREATE", "MATCH")


# ── Data types ────────────────────────────────────────────────────────


@dataclass(frozen=True)
class EdgeTriple:
    """A directed edge in the graph schema, identified by rel type and
    the labels of its endpoints. Frozen so it can live in a set."""

    rel_type: str
    from_label: str
    to_label: str

    def __str__(self) -> str:
        return f"{self.rel_type} ({self.from_label} → {self.to_label})"


# ── Doc extractor ─────────────────────────────────────────────────────


def extract_documented_edges(doc_file: Path) -> Set[EdgeTriple]:
    """Extract documented edge triples from the relationship table."""
    edges: Set[EdgeTriple] = set()
    for _, line in iter_markdown_lines(doc_file):
        match = DOC_EDGE_ROW_RE.match(line)
        if not match:
            continue
        edges.add(
            EdgeTriple(
                rel_type=match.group(1),
                from_label=match.group(2),
                to_label=match.group(3),
            )
        )
    return edges


# ── Loader extractor ──────────────────────────────────────────────────


def iter_cypher_strings(source_file: Path) -> Iterator[str]:
    """Yield string literals from a Python source file that look like Cypher."""
    try:
        tree = ast.parse(source_file.read_text())
    except SyntaxError:
        return
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            s = node.value
            if any(kw in s for kw in CYPHER_KEYWORDS):
                yield s


def _build_node_bindings(cypher: str) -> Dict[str, str]:
    """Walk every `(var:Label ...)` in a Cypher fragment and return a
    var → label map. Anonymous or label-less nodes are ignored."""
    bindings: Dict[str, str] = {}
    for match in NODE_PATTERN_RE.finditer(cypher):
        var, label = match.group(1), match.group(2)
        if var and label:
            bindings[var] = label
    return bindings


def _node_var(paren_content: str) -> Optional[str]:
    """Pull the variable name out of the inside of a node parenthesis."""
    match = NODE_CONTENT_RE.match(paren_content)
    return match.group(1) if match and match.group(1) else None


def _edge_rel(bracket_content: str) -> Optional[str]:
    """Pull the relationship type out of the inside of an edge bracket."""
    match = EDGE_CONTENT_RE.search(bracket_content)
    return match.group(1) if match else None


def extract_edges_from_cypher(cypher: str) -> Set[EdgeTriple]:
    """Extract directed edge triples from a single Cypher fragment.

    Returns a set of `(rel_type, from_label, to_label)`. Edges where
    either endpoint cannot be resolved to a label (anonymous or
    unbound) are silently dropped — we only verify what we can prove.
    """
    bindings = _build_node_bindings(cypher)
    edges: Set[EdgeTriple] = set()

    for match in DIRECTED_EDGE_RE.finditer(cypher):
        src_content, edge_content, dst_content = (
            match.group(1),
            match.group(2),
            match.group(3),
        )
        src_var = _node_var(src_content)
        dst_var = _node_var(dst_content)
        rel = _edge_rel(edge_content)
        if not (src_var and dst_var and rel):
            continue
        from_label = bindings.get(src_var)
        to_label = bindings.get(dst_var)
        if not (from_label and to_label):
            continue
        edges.add(
            EdgeTriple(
                rel_type=rel,
                from_label=from_label,
                to_label=to_label,
            )
        )
    return edges


def extract_actual_edges(repo_root: Path) -> Set[EdgeTriple]:
    """Walk every loader file and aggregate edge triples."""
    all_edges: Set[EdgeTriple] = set()
    for rel_path in LOADER_FILES:
        path = repo_root / rel_path
        if not path.exists():
            continue
        for cypher in iter_cypher_strings(path):
            all_edges |= extract_edges_from_cypher(cypher)
    return all_edges


# ── The check ─────────────────────────────────────────────────────────


class RelationshipInventoryCheck(Check):
    name = "relationship_inventory"
    description = (
        "Relationship table in graph-model.md matches loader MERGE patterns"
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

        documented = extract_documented_edges(doc_file)
        actual = extract_actual_edges(repo_root)

        problems: List[str] = []

        missing_in_code = documented - actual
        for edge in sorted(missing_in_code, key=str):
            problems.append(
                f"  documented but no loader has it: {edge}"
            )

        extra_in_code = actual - documented
        for edge in sorted(extra_in_code, key=str):
            problems.append(
                f"  loader has it but no doc row: {edge}"
            )

        items_checked = len(documented | actual)

        if not problems:
            return CheckResult(
                check=self.name,
                status=Status.PASS,
                items_checked=items_checked,
            )

        details_lines = [
            f"Found {len(problems)} relationship inventory discrepancies "
            f"across {items_checked} unique edge triples:"
        ]
        details_lines.extend(problems)

        return CheckResult(
            check=self.name,
            status=Status.FAIL,
            details="\n".join(details_lines),
            items_checked=items_checked,
            resolution=(
                "For each discrepancy, either add the missing relationship "
                "to docs/architecture/graph-model.md or add the missing "
                "MERGE/CREATE pattern to the corresponding loader. "
                "Documentation and code must agree on the full set of "
                "(rel_type, from_label, to_label) triples — including "
                "direction."
            ),
        )
