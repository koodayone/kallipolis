"""Deterministic (form, coordinate, selection) → dashboard deep-link.

Maps a Tier 1 form onto the frozen ``landscapeUrl.ts`` grammar (lens/soc/top/
college/emp/panel). The route base distinguishes pinned instances (``/<id>``,
e.g. ``/svamp``) from generated ones (``/landscape/<member>/<sector>``),
mirroring the atlas routing. The mapping is deliberately not total (§3):
aggregate lenses force a default selection client-side, disclosed in the note
rather than hidden.
"""
from __future__ import annotations

import os
from typing import Optional
from urllib.parse import urlencode

from partnerships.landscape import REGISTRY

from mcp_server.envelope import ViewLink

# The dashboard host (distinct from the API host). Env-overridable for local dev.
_ATLAS_BASE = os.environ.get(
    "KALLIPOLIS_ATLAS_URL", "https://preview.kallipolis.us").rstrip("/")

# form → (lens, dashboard-only panel). Selection keys are added from the coordinate.
_FORM_LENS: dict[str, tuple[str, Optional[str]]] = {
    "sector_overview": ("occupations", None),
    "gap": ("occupations", None),
    "occupation_profile": ("occupations", None),
    "coverage": ("programs", "programs.coverage"),
    "pathway_program": ("programs", None),
    "pathway_occupation": ("occupations", None),
    "regional_employers": ("employers", None),
}


def _route_base(instance_id: str, member_id: str, sector_id: str) -> str:
    if instance_id in REGISTRY:
        return f"/{instance_id}"                       # pinned: /svamp, /smccd-adm
    return f"/landscape/{member_id}/{sector_id}"        # generated: /landscape/foothill/adm


def view_link(form: str, *, instance_id: str, member_id: str, sector_id: str,
              soc: Optional[str] = None, top6: Optional[str] = None,
              college_key: Optional[str] = None,
              employer: Optional[str] = None) -> ViewLink:
    """Build the corroborating dashboard deep-link for a form at a coordinate."""
    key = form
    if form == "pathway":
        key = "pathway_program" if top6 else "pathway_occupation"
    if key not in _FORM_LENS:
        return ViewLink(url=None, status="unavailable",
                        note=f"No dashboard view for form '{form}'.")
    lens, panel = _FORM_LENS[key]

    params: list[tuple[str, str]] = [("lens", lens)]
    if soc and lens == "occupations":
        params.append(("soc", soc))
    if top6 and lens == "programs":
        params.append(("top", top6))
    if employer and lens == "employers":
        params.append(("emp", employer))
    if college_key:
        params.append(("college", college_key))
    if panel:
        params.append(("panel", panel))

    base = _route_base(instance_id, member_id, sector_id)
    url = f"{_ATLAS_BASE}{base}?{urlencode(params)}"

    note = ""
    if not (soc or top6 or employer):
        note = ("Opens on the lens with a default selection (view state applies "
                "client-side); select the row above to corroborate the figure.")
    return ViewLink(url=url, status="ok", note=note)
