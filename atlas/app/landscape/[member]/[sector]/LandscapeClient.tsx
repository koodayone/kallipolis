"use client";

// Generated member×sector landscape — the client surface for any college /
// district instance the backend catalog publishes (e.g. /landscape/foothill/adm).
// Reads the route params (the atlas convention: server page does
// generateStaticParams, the client reads the param), builds the instance
// identity from the landscape index (generated instances have no
// landscapeInstances row), and renders the same SvampDashboard the pinned
// instances use. The 12 pinned instances keep their own flat routes untouched.

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";

import SvampDashboard from "@/college-atlas/partnerships/SvampDashboard";
import { registerGeneratedInstance, type LandscapeInstance } from "@/college-atlas/partnerships/landscapeInstances";
import { fetchLandscapeIndex, generatedInstance } from "@/college-atlas/partnerships/landscapeIndex";

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
  const params = useParams<{ member: string; sector: string }>();
  const member = (params?.member as string) ?? "";
  const sector = (params?.sector as string) ?? "";
  const id = `${member}-${sector}`;
  // undefined = loading, null = not in the live catalog.
  const [identity, setIdentity] = useState<LandscapeInstance | null | undefined>(undefined);

  useEffect(() => {
    let alive = true;
    fetchLandscapeIndex().then((idx) => {
      if (!alive) return;
      const entry = idx.find((e) => e.member_id === member && e.sector_id === sector);
      const inst = entry ? generatedInstance(entry) : null;
      if (inst) registerGeneratedInstance(inst);
      setIdentity(inst);
    });
    return () => {
      alive = false;
    };
  }, [member, sector]);

  if (identity === undefined) return <div style={FULL_CENTER}>Loading…</div>;
  if (identity === null) return <div style={FULL_CENTER}>This landscape isn’t available.</div>;
  return <SvampDashboard instance={id} identity={identity} />;
}
