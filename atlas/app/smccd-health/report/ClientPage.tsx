"use client";

import { motion } from "framer-motion";
import LandscapeReport from "@/college-atlas/partnerships/LandscapeReport";
import { getCollegeAtlasConfig } from "@/config/collegeAtlasConfigs";
import { SchoolConfig } from "@/config/schoolConfig";
import { landscapeInstance } from "@/college-atlas/partnerships/landscapeInstances";

// SMCCD-Health member colleges from the landscape instance registry (College of
// San Mateo, Skyline, Cañada — same members as the AM instance, different
// scope). Each id resolves to a SchoolConfig whose `.name` matches the backend
// college name the /partnerships/smccd-health endpoint returns.
const SMCCD_HEALTH_COLLEGE_IDS = landscapeInstance("smccd-health").collegeIds;

export default function SmccdHealthReportRoute() {
  const colleges = SMCCD_HEALTH_COLLEGE_IDS
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
      <LandscapeReport colleges={colleges} instance="smccd-health" />
    </motion.div>
  );
}
