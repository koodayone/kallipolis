"use client";

// Member-root landing: /landscape/<member> (no sector) opens the member's view
// on its flagship sector, where the industry rail takes over for switching —
// mirroring how /smccd redirects to /smccd-adm. The default sector is the first
// one the member is actually live in, in priority order (the CTE-core /
// tech-forward industries first), resolved from the landscape index. Falls back
// to the State Atlas for an unknown member.

import { useEffect } from "react";
import { fetchLandscapeIndex, parseLandscapePath } from "@/college-atlas/partnerships/landscapeIndex";

// Flagship-first: land on Advanced Manufacturing where present, then the other
// priority sectors, before the broader-access industries.
const DEFAULT_SECTOR_PRIORITY = [
  "adm", "biotech", "ecu", "atl", "ict", "health", "business", "public_safety", "edhd", "agwet", "retail",
];

export default function MemberRedirect() {
  useEffect(() => {
    // SPA fallback: read the member from the LIVE URL (the served HTML is the
    // foothill sentinel). Hard-navigate to the flagship sector — the per-instance
    // sector route isn't pre-rendered, so a client router.replace would 404 its
    // RSC payload; window.location.replace re-enters through the _redirects shell.
    const { member } = parseLandscapePath(window.location.pathname);
    if (!member) { window.location.replace("/"); return; }
    let alive = true;
    fetchLandscapeIndex().then((idx) => {
      if (!alive) return;
      const live = new Set(idx.filter((e) => e.member_id === member).map((e) => e.sector_id));
      const target = DEFAULT_SECTOR_PRIORITY.find((s) => live.has(s)) ?? [...live][0];
      window.location.replace(target ? `/landscape/${member}/${target}${window.location.search}` : "/");
    });
    return () => { alive = false; };
  }, []);

  return (
    <div style={{ position: "fixed", inset: 0, display: "flex", alignItems: "center", justifyContent: "center", color: "#5e6a83", fontFamily: "monospace", fontSize: 13, letterSpacing: ".04em" }}>
      Loading…
    </div>
  );
}
