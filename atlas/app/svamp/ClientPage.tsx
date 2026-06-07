"use client";

import { motion } from "framer-motion";
import SvampView from "@/college-atlas/partnerships/SvampView";
import { getCollegeAtlasConfig } from "@/config/collegeAtlasConfigs";
import { SchoolConfig } from "@/config/schoolConfig";

// The five Silicon Valley Advanced Manufacturing member colleges, in display
// order. Each id resolves to a SchoolConfig whose `.name` matches the backend
// college name the landscape endpoint returns.
const SVAMP_COLLEGE_IDS = ["deanza", "evergreen", "foothill", "mission", "ohlone"];

export default function SvampRoute() {
  const colleges = SVAMP_COLLEGE_IDS
    .map((id) => ({ id, config: getCollegeAtlasConfig(id) }))
    .filter((c): c is { id: string; config: SchoolConfig } => c.config !== null);

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.45 }}
      style={{
        position: "fixed",
        inset: 0,
        zIndex: 10,
        background: "#060d1f",
        overflowY: "auto",
        overscrollBehavior: "none",
      }}
    >
      {/* No onBack — the report's header now carries the dashboard's unified
          nav grammar (brand · title · surface forms), with no atlas chevron. */}
      <SvampView colleges={colleges} />
    </motion.div>
  );
}
