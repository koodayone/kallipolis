"use client";

// Report surface for a generated member×sector landscape — the narrative dual of
// the dashboard, mirroring the pinned reports (e.g. /smccd-adm/report). Reads the
// route params, resolves the instance identity from the landscape index, registers
// it (so LandscapeReport's landscapeInstance() call sites resolve instead of falling back
// to SVAMP), and renders LandscapeReport in the same fixed full-screen scroll wrapper the
// pinned reports use.

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import LandscapeReport from "@/college-atlas/partnerships/LandscapeReport";
import { getCollegeAtlasConfig } from "@/config/collegeAtlasConfigs";
import { SchoolConfig } from "@/config/schoolConfig";
import { registerGeneratedInstance, type LandscapeInstance } from "@/college-atlas/partnerships/landscapeInstances";
import { fetchLandscapeIndex, generatedInstance, parseLandscapePath } from "@/college-atlas/partnerships/landscapeIndex";

const CENTER: React.CSSProperties = {
  position: "fixed", inset: 0, display: "flex", alignItems: "center",
  justifyContent: "center", color: "#5e6a83", fontFamily: "monospace", fontSize: 13, letterSpacing: ".04em",
};

export default function ReportClient() {
  // SPA fallback: identity resolved from the LIVE URL (parseLandscapePath), not
  // useParams — the served HTML is the foothill·AM sentinel shell. See
  // LandscapeClient for the full rationale.
  const [resolved, setResolved] = useState<{ id: string; inst: LandscapeInstance | null } | undefined>(undefined);

  useEffect(() => {
    let alive = true;
    const { member, sector } = parseLandscapePath(window.location.pathname);
    const id = `${member}-${sector}`;
    fetchLandscapeIndex().then((idx) => {
      if (!alive) return;
      const entry = idx.find((e) => e.member_id === member && e.sector_id === sector);
      const inst = entry ? generatedInstance(entry) : null;
      if (inst) registerGeneratedInstance(inst);
      setResolved({ id, inst });
    });
    return () => { alive = false; };
  }, []);

  if (resolved === undefined) return <div style={CENTER}>Loading…</div>;
  if (resolved.inst === null) return <div style={CENTER}>This report isn’t available.</div>;

  const colleges = resolved.inst.collegeIds
    .map((cid) => ({ id: cid, config: getCollegeAtlasConfig(cid) }))
    .filter((cc): cc is { id: string; config: SchoolConfig } => cc.config !== null);

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.45 }}
      style={{ position: "fixed", inset: 0, zIndex: 10, background: "#060d1f", overflowY: "auto", overscrollBehavior: "none" }}
    >
      <LandscapeReport colleges={colleges} instance={resolved.id} />
    </motion.div>
  );
}
