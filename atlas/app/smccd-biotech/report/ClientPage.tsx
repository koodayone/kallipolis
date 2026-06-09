"use client";

import { motion } from "framer-motion";
import SvampView from "@/college-atlas/partnerships/SvampView";
import { getCollegeAtlasConfig } from "@/config/collegeAtlasConfigs";
import { SchoolConfig } from "@/config/schoolConfig";
import { landscapeInstance } from "@/college-atlas/partnerships/landscapeInstances";

// SMCCD-Biotech member colleges from the landscape instance registry (College of
// San Mateo, Skyline, Cañada). Each id resolves to a SchoolConfig whose `.name`
// matches the backend college name the /partnerships/smccd-biotech endpoint
// returns.
const SMCCD_BIOTECH_COLLEGE_IDS = landscapeInstance("smccd-biotech").collegeIds;

export default function SmccdBiotechReportRoute() {
  const colleges = SMCCD_BIOTECH_COLLEGE_IDS
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
      <SvampView colleges={colleges} instance="smccd-biotech" />
    </motion.div>
  );
}
