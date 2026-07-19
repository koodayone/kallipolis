"use client";

// /[collegeId]/partnerships renders the college's single-college LANDSCAPE
// IN PLACE — no bounce to /landscape/<member>/<sector>. The dashboard's own
// vocabulary lives under /partnerships: the industry rail switches sector via
// ?sector= on this same URL, and the Dashboard⇄Report toggle stays under
// /[collegeId]/partnerships(/report). Resolve collegeId → member by NAME (the
// frontend id and backend member_id diverge; memberIdForCollege joins on
// SchoolConfig.name == member_label), pick the sector from ?sector= (validated)
// or the member's flagship, and render the same LandscapeDashboard the pinned
// and /landscape/* routes use — identical instance identity via generatedInstance.
// (This route is statically pre-rendered per featured college, so ?sector= is a
// plain query on a real page — no SPA-fallback sentinel needed.)

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";

import LandscapeDashboard from "@/college-atlas/partnerships/LandscapeDashboard";
import { registerGeneratedInstance, type LandscapeInstance } from "@/college-atlas/partnerships/landscapeInstances";
import { fetchLandscapeIndex, collegeLandscape, generatedInstance } from "@/college-atlas/partnerships/landscapeIndex";

const FULL_CENTER: React.CSSProperties = {
  position: "fixed",
  inset: 0,
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
  background: "#060d1f",
  color: "#5e6a83",
  fontFamily: "monospace",
  fontSize: 13,
  letterSpacing: ".04em",
};

export default function PartnershipsRoute() {
  const { collegeId } = useParams<{ collegeId: string }>();
  // undefined = loading, identity null = no landscape for this college.
  const [state, setState] = useState<{ id: string; identity: LandscapeInstance | null } | undefined>(undefined);

  useEffect(() => {
    let alive = true;
    const sector = new URLSearchParams(window.location.search).get("sector");
    fetchLandscapeIndex().then((idx) => {
      if (!alive) return;
      const entry = collegeLandscape(collegeId, idx, sector);
      const inst = entry ? generatedInstance(entry) : null;
      if (inst) registerGeneratedInstance(inst);
      setState({ id: entry?.id ?? "", identity: inst });
    });
    return () => {
      alive = false;
    };
  }, [collegeId]);

  if (state === undefined) return <div style={FULL_CENTER}>Loading…</div>;
  if (state.identity === null) return <div style={FULL_CENTER}>This landscape isn’t available.</div>;
  return <LandscapeDashboard instance={state.id} identity={state.identity} />;
}
