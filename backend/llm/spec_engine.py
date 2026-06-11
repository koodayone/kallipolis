"""Spec engine — Flash-driven NL → spec → templated Cypher pipeline.

Replaces the free-form Cypher generation in `llm/query_engine.py` with
a constrained classifier-and-templater architecture. The user's
question is classified into a per-feature structured spec by Gemini
Flash; the spec is rendered into Cypher by a deterministic per-feature
template; the rendered Cypher is parametrized so filter values never
appear inline.

Compared to the Sonnet path, this approach:
  - removes a multi-second LLM call (Flash on a small structured-output
    task takes ~1 s vs Sonnet's 3-7 s on full Cypher generation);
  - guarantees structural correctness (read-only, college-scoped,
    schema-conformant Cypher) by template construction rather than
    post-validation regex;
  - produces deterministic output (same question → same spec → same
    Cypher) and exposes the spec back as plain English via
    `interpret_spec`, so users see what was understood and can
    audit the interpretation.

Per-feature configuration (Spec class, Flash prompt, response schema,
template, NL renderer) lives under `llm/specs/`. The engine is the
thin glue that picks the right module by view name and runs Flash.
"""
from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass

from google import genai
from google.genai import types

from llm.specs import VIEW_TO_MODULE, VIEW_TO_SPEC_CLASS

logger = logging.getLogger(__name__)


@dataclass
class SpecResult:
    """Outcome of a spec-engine run.

    `unsupported=True` means Flash explicitly classified the question as
    out-of-grammar; the API caller should surface `unsupported_reason`
    plus the canonical example queries so the user can rephrase.

    `cypher=None` together with `unsupported=False` is reserved for an
    upstream error (Flash returned malformed JSON); callers handle it
    the same as a generic 500.
    """
    view: str
    cypher: str | None
    params: dict
    interpretation: str | None
    unsupported: bool = False
    unsupported_reason: str | None = None
    spec_dict: dict | None = None  # for debugging / audit


_RETRY_ATTEMPTS = 4


def _client() -> genai.Client:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY required for spec engine")
    return genai.Client(api_key=api_key)


def _extract(question: str, view: str) -> tuple[dict, bool, str | None]:
    """Run Flash to extract the spec dict for one question."""
    if view not in VIEW_TO_MODULE:
        raise ValueError(f"Unknown view: {view!r}")
    module = VIEW_TO_MODULE[view]
    client = _client()

    last_err: Exception | None = None
    for attempt in range(_RETRY_ATTEMPTS):
        try:
            response = client.models.generate_content(
                model=os.environ.get("GEMINI_MODEL", "gemini-2.5-flash"),
                contents=f"{module.EXTRACTOR_PROMPT}\n\nQuestion: {question}",
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=module.SPEC_SCHEMA,
                    temperature=0.0,
                ),
            )
            raw = json.loads(response.text)
            return (
                raw,
                bool(raw.get("unsupported")),
                raw.get("unsupported_reason") if raw.get("unsupported") else None,
            )
        except Exception as e:
            last_err = e
            msg = str(e).lower()
            if "503" in msg or "unavailable" in msg or "resource_exhausted" in msg:
                # Transient model-availability error — exponential backoff.
                # Don't return a malformed spec; let the next attempt try.
                import time
                time.sleep(2 ** attempt)
                continue
            raise
    if last_err:
        raise last_err
    raise RuntimeError("spec extraction failed without error")


def run_spec(question: str, college: str, view: str) -> SpecResult:
    """Translate a natural-language question into a templated Cypher query.

    Returns a SpecResult. On success, `cypher` is the rendered Cypher
    and `params` includes `college` plus any filter values. On
    explicit out-of-grammar classification, `unsupported=True` and the
    caller should surface `unsupported_reason` plus example-query
    suggestions to the user.
    """
    if view not in VIEW_TO_MODULE:
        raise ValueError(f"Unknown view: {view!r}")
    module = VIEW_TO_MODULE[view]
    spec_class = VIEW_TO_SPEC_CLASS[view]

    raw, unsupported, reason = _extract(question, view)
    if unsupported:
        return SpecResult(
            view=view,
            cypher=None,
            params={},
            interpretation=None,
            unsupported=True,
            unsupported_reason=reason,
            spec_dict=raw,
        )

    # Filter the dict to only fields defined on the SpecClass — Flash
    # may include scratch fields (e.g., the `unsupported`/`unsupported_reason`
    # signals or any extras the schema accidentally allowed) that the
    # Pydantic constructor would reject.
    spec_data = {k: raw.get(k) for k in spec_class.model_fields if raw.get(k) is not None}
    spec = spec_class(**spec_data)

    cypher, filter_params = module.render_cypher(spec)
    return SpecResult(
        view=view,
        cypher=cypher,
        params={"college": college, **filter_params},
        interpretation=module.interpret_spec(spec),
        unsupported=False,
        spec_dict=spec.model_dump(),
    )


def execute_spec(result: SpecResult) -> list[dict]:
    """Execute the rendered Cypher with the spec's parameters."""
    if result.cypher is None:
        raise RuntimeError("Cannot execute an unsupported or malformed spec result")
    from ontology.schema import get_driver
    driver = get_driver()
    with driver.session() as session:
        records = session.execute_read(
            lambda tx, q=result.cypher, p=result.params: tx.run(q, **p).data()
        )
    return records


def is_enabled_for(view: str) -> bool:
    """Feature-flag check.

    Defaults: occupation + employer always on; course off
    until further validation. Override via env vars
    SPEC_ENGINE_<VIEW>=1|0 (uppercased).
    """
    defaults = {
        "occupation": "1",
        "employer": "1",
        "course": "0",
    }
    env_key = f"SPEC_ENGINE_{view.upper()}"
    return os.environ.get(env_key, defaults.get(view, "0")) == "1"
