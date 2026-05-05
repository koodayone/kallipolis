"""Translate DataMart CSV college display names to backend college keys.

DataMart CSVs (StudentHeadcount, UnitLoadSumm, CourseRetSuccessSumm,
top6_grades) use Chancellor's Office display names ("Santa Barbara",
"Mt. San Jacinto", "LA Trade"). The pipeline keys colleges by backend
keys ("sbcc", "mtsanjacinto", "lattc") that flow from
`backend/pipeline/catalog_sources.json`.

The translation is derived from `mcf_key_map._PDF_TO_MCF`, which already
maintains the canonical backend-key ↔ MCF-key mapping. The MCF key
convention is snake_case display names with periods stripped, so a CSV
name normalized the same way matches MCF keys for ~96% of colleges.
The remaining cases (CSV display names with subdivision qualifiers like
"Chabot Hayward") get explicit handling here.

Usage:
    from pipeline.datamart_keys import csv_name_to_backend_key
    key = csv_name_to_backend_key("Santa Barbara")  # -> "sbcc"
    key = csv_name_to_backend_key("Foothill")       # -> "foothill"
    key = csv_name_to_backend_key("Madera")         # -> None (not in catalog)
"""
from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Optional

from pipeline.mcf_key_map import _PDF_TO_MCF


# CSV display names that need cleanup before snake-casing because the
# CSV uses subdivision qualifiers that don't appear in the backend key
# or MCF key. Apply before normalization.
_CSV_NAME_FIXUPS = {
    "Chabot Hayward": "Chabot",
}


# Explicit mappings for CSV names where snake-case, MCF inverse, concat
# form, and suffix-drop all fail. Genuinely irregular name pairs only.
_EXPLICIT_BACKEND_KEYS = {
    "san_francisco": "ccsf",
}


def _normalize(name: str) -> str:
    """Lowercase, strip periods, collapse whitespace to underscores,
    drop other non-alphanumerics."""
    name = _CSV_NAME_FIXUPS.get(name.strip(), name.strip())
    name = name.replace(".", "")
    s = re.sub(r"\s+", "_", name.lower())
    return re.sub(r"[^a-z0-9_]", "", s)


@lru_cache(maxsize=1)
def _mcf_to_backend() -> dict[str, str]:
    """Inverse of _PDF_TO_MCF: MCF key → backend key."""
    return {mcf: pdf for pdf, mcf in _PDF_TO_MCF.items()}


@lru_cache(maxsize=1)
def _catalog_keys() -> set[str]:
    """Backend keys present in catalog_sources.json."""
    path = Path(__file__).parent / "catalog_sources.json"
    with open(path) as f:
        return set(json.load(f)["colleges"].keys())


def csv_name_to_backend_key(name: str) -> Optional[str]:
    """Translate a DataMart CSV college display name to its backend key.

    Returns None when the college does not appear in catalog_sources.json
    (CalBright, Madera, San Diego College of Continuing Ed, etc. — colleges
    DataMart reports on but Kallipolis doesn't ingest).
    """
    if not name:
        return None
    normalized = _normalize(name)
    catalog = _catalog_keys()

    # 1. Direct match: snake_case form is already the backend key.
    if normalized in catalog:
        return normalized

    # 2. Inverse-MCF match: snake_case form is the MCF key, find backend key.
    backend = _mcf_to_backend().get(normalized)
    if backend and backend in catalog:
        return backend

    # 3. Concat form: backend key drops the underscores ("palo_verde" -> "paloverde").
    concat = normalized.replace("_", "")
    if concat in catalog:
        return concat

    # 4. Drop trailing "_college" suffix ("norco_college" -> "norco").
    if normalized.endswith("_college"):
        stripped = normalized[: -len("_college")]
        if stripped in catalog:
            return stripped
        if stripped.replace("_", "") in catalog:
            return stripped.replace("_", "")

    # 5. Explicit override for genuinely irregular pairs (San Francisco -> ccsf).
    explicit = _EXPLICIT_BACKEND_KEYS.get(normalized)
    if explicit and explicit in catalog:
        return explicit

    return None
