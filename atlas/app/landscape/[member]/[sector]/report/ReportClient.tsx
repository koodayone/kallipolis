"use client";

// Report surface for a generated member×sector landscape — the narrative dual of
// the dashboard, mirroring the pinned reports (e.g. /smccd-adm/report). Reads the
// route params, resolves the instance identity from the landscape index, registers
// it (so SvampView's landscapeInstance() call sites resolve instead of falling back
// to SVAMP), and renders SvampView in the same fixed full-screen scroll wrapper the
// pinned reports use.

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { motion } from "framer-motion";
import SvampView from "@/college-atlas/partnerships/SvampView";
import { getCollegeAtlasConfig } from "@/config/collegeAtlasConfigs";
import { SchoolConfig } from "@/config/schoolConfig";
import { registerGeneratedInstance, type LandscapeInstance } from "@/college-atlas/partnerships/landscapeInstances";
import { fetchLandscapeIndex, generatedInstance } from "@/college-atlas/partnerships/landscapeIndex";

const CENTER: React.CSSProperties = {
  position: "fixed", inset: 0, display: "flex", alignItems: "center",
  justifyContent: "center", color: "#5e6a83", fontFamily: "monospace", fontSize: 13, letterSpacing: ".04em",
};

export default function ReportClient() {
  const params = useParams<{ member: string; sector: string }>();
  const member = (params?.member as string) ?? "";
  const sector = (params?.sector as string) ?? "";
  const id = `${member}-${sector}`;
  const [ready, setReady] = useState<LandscapeInstance | null | undefined>(undefined);

  useEffect(() => {
    let alive = true;
    fetchLandscapeIndex().then((idx) => {
      if (!alive) return;
      const entry = idx.find((e) => e.member_id === member && e.sector_id === sector);
      const inst = entry ? generatedInstance(entry) : null;
      if (inst) registerGeneratedInstance(inst);
      setReady(inst);
    });
    return () => { alive = false; };
  }, [member, sector]);

  if (ready === undefined) return <div style={CENTER}>Loading…</div>;
  if (ready === null) return <div style={CENTER}>This report isn’t available.</div>;

  const colleges = ready.collegeIds
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
      <SvampView colleges={colleges} instance={id} />
    </motion.div>
  );
}
