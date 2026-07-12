"""Back-compat shim — the canonical quantity resolvers now live in
``partnerships.quantities``, the single computation layer beneath BOTH the dashboard
builders and the MCP forms (a partnerships module so the builders can reach it without a
``mcp_server`` cycle). This module re-exports that API so existing importers
(``from mcp_server import canonical as CAN``) keep working; new code should import
``partnerships.quantities`` directly.
"""
from partnerships.quantities import (  # noqa: F401  (re-export)
    CollegeCell,
    SUPPLY_SOURCE,
    active_feeders,
    college_roster,
    colleges_actively_awarding,
    colleges_with_program,
    feeders,
    recent_award_years,
    supply,
    supply_over_socs,
    vintage,
)

__all__ = [
    "CollegeCell",
    "SUPPLY_SOURCE",
    "active_feeders",
    "college_roster",
    "colleges_actively_awarding",
    "colleges_with_program",
    "feeders",
    "recent_award_years",
    "supply",
    "supply_over_socs",
    "vintage",
]
