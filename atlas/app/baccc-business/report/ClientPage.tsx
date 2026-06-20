"use client";

import { motion } from "framer-motion";
import SvampView from "@/college-atlas/partnerships/SvampView";
import { getCollegeAtlasConfig } from "@/config/collegeAtlasConfigs";
import { SchoolConfig } from "@/config/schoolConfig";
import { landscapeInstance } from "@/college-atlas/partnerships/landscapeInstances";

const COLLEGE_IDS = landscapeInstance("baccc-business").collegeIds;

export default function BacccBusinessReportRoute() {
  const colleges = COLLEGE_IDS
    .map((id) => ({ id, config: getCollegeAtlasConfig(id) }))
    .filter((cc): cc is { id: string; config: SchoolConfig } => cc.config !== null);

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.45 }}
      style={{ position: "fixed", inset: 0, zIndex: 10, background: "#060d1f", overflowY: "auto", overscrollBehavior: "none" }}>
      <SvampView colleges={colleges} instance="baccc-business" />
    </motion.div>
  );
}
