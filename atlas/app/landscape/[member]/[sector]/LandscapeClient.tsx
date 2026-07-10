"use client";

// Generated member×sector landscape — the client surface for any college /
// district instance the backend catalog publishes (e.g. /landscape/foothill/adm).
// These routes are SPA-fallback-served (see public/_redirects + landscapeIndex):
// one sentinel shell stands in for every instance, so the identity is resolved
// from the LIVE URL (parseLandscapePath) — not useParams, which would read the
// baked sentinel params. Built from the landscape index (generated instances have
// no landscapeInstances row), and rendered with the same LandscapeDashboard the pinned
// instances use. The 12 pinned instances keep their own flat routes untouched.

import { useEffect, useState } from "react";

import LandscapeDashboard from "@/college-atlas/partnerships/LandscapeDashboard";
import { registerGeneratedInstance, type LandscapeInstance } from "@/college-atlas/partnerships/landscapeInstances";
import { fetchLandscapeIndex, generatedInstance, parseLandscapePath } from "@/college-atlas/partnerships/landscapeIndex";

const FULL_CENTER: React.CSSProperties = {
  position: "fixed",
  inset: 0,
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
  color: "#5e6a83",
  fontFamily: "monospace",
  fontSize: 13,
  letterSpacing: ".04em",
};

export default function LandscapeClient() {
  // SPA fallback: the served HTML is the foothill·AM sentinel regardless of the
  // requested instance, so resolve the identity from the LIVE URL post-mount.
  // The URL only changes via a full navigation (the rail/surface nav
  // hard-navigate), so a one-shot mount read is sufficient.
  // undefined = loading, null = not in the live catalog.
  const [state, setState] = useState<{ id: string; identity: LandscapeInstance | null } | undefined>(undefined);

  useEffect(() => {
    let alive = true;
    const { member, sector } = parseLandscapePath(window.location.pathname);
    const id = `${member}-${sector}`;
    fetchLandscapeIndex().then((idx) => {
      if (!alive) return;
      const entry = idx.find((e) => e.member_id === member && e.sector_id === sector);
      const inst = entry ? generatedInstance(entry) : null;
      if (inst) registerGeneratedInstance(inst);
      setState({ id, identity: inst });
    });
    return () => {
      alive = false;
    };
  }, []);

  if (state === undefined) return <div style={FULL_CENTER}>Loading…</div>;
  if (state.identity === null) return <div style={FULL_CENTER}>This landscape isn’t available.</div>;
  return <LandscapeDashboard instance={state.id} identity={state.identity} />;
}
