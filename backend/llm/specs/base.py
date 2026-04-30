"""Shared types for per-feature query specs.

The spec engine (`llm/spec_engine.py`) replaces free-form Cypher
generation with a constrained NL → spec → templated Cypher pipeline.
Each ontology view (occupations, courses, employers, students) has
its own spec module under `llm/specs/` exporting:
  - SpecClass         (Pydantic) — the structured intent
  - EXTRACTOR_PROMPT  (str)      — Flash extraction system prompt
  - SPEC_SCHEMA       (dict)     — Gemini structured-output schema
  - render_cypher(spec) -> (cypher, params)
  - interpret_spec(spec) -> str  — deterministic NL of the spec

This base module defines the cross-feature primitives used by all
spec modules.
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

NumericOp = Literal[">", ">=", "<", "<=", "=", "!="]


class NumericFilter(BaseModel):
    """A numeric comparison filter used in Cypher WHERE clauses."""
    op: NumericOp
    value: float


# JSON-schema fragment for NumericFilter, reused in each feature's
# SPEC_SCHEMA definition. Gemini's response_schema needs OBJECT shape
# with `properties` and `required` arrays.
NUMERIC_FILTER_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "op": {"type": "STRING", "enum": [">", ">=", "<", "<=", "=", "!="]},
        "value": {"type": "NUMBER"},
    },
    "required": ["op", "value"],
}


def render_op_label(op: NumericOp) -> str:
    """Plain-English rendering of a numeric op for interpret_spec output."""
    return {
        ">": "above", ">=": "at least",
        "<": "below", "<=": "at most",
        "=": "equal to", "!=": "not equal to",
    }[op]
