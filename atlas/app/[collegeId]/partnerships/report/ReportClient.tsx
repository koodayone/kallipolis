"use client";

// Report surface for the single-college in-place landscape (/[collegeId]/partnerships/report).
// The narrative dual of the dashboard; resolves collegeId → member + the ?sector=
// (or flagship) the same way the dashboard ClientPage does (collegeLandscape), so
// the two surfaces stay in lockstep, then renders LandscapeReport in the same fixed
// full-screen scroll wrapper the /landscape/*/report and pinned reports use.

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { useParams } from "next/navigation";

import LandscapeReport from "@/college-atlas/partnerships/LandscapeReport";
import { getCollegeAtlasConfig } from "@/config/collegeAtlasConfigs";
import { SchoolConfig } from "@/config/schoolConfig";
import { registerGeneratedInstance, type LandscapeInstance } from "@/college-atlas/partnerships/landscapeInstances";
import { fetchLandscapeIndex, collegeLandscape, generatedInstance } from "@/college-atlas/partnerships/landscapeIndex";

const CENTER: React.CSSProperties = {
  position: "fixed", inset: 0, display: "flex", alignItems: "center",
  justifyContent: "center", color: "#5e6a83", fontFamily: "monospace", fontSize: 13, letterSpacing: ".04em",
};

export default function ReportClient() {
  const { collegeId } = useParams<{ collegeId: string }>();
  const [resolved, setResolved] = useState<{ id: string; inst: LandscapeInstance | null } | undefined>(undefined);

  useEffect(() => {
    let alive = true;
    const sector = new URLSearchParams(window.location.search).get("sector");
    fetchLandscapeIndex().then((idx) => {
      if (!alive) return;
      const entry = collegeLandscape(collegeId, idx, sector);
      const inst = entry ? generatedInstance(entry) : null;
      if (inst) registerGeneratedInstance(inst);
      setResolved({ id: entry?.id ?? "", inst });
    });
    return () => { alive = false; };
  }, [collegeId]);

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
