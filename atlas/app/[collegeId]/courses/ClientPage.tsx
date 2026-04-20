"use client";

import { useParams, useRouter } from "next/navigation";
import { motion } from "framer-motion";
import CoursesView from "@/college-atlas/courses/CoursesView";
import { getCollegeAtlasConfig } from "@/config/collegeAtlasConfigs";

export default function CoursesRoute() {
  const { collegeId } = useParams<{ collegeId: string }>();
  const router = useRouter();
  const config = getCollegeAtlasConfig(collegeId);

  if (!config) return null;

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
      <CoursesView school={config} onBack={() => router.push(`/${collegeId}`)} />
    </motion.div>
  );
}
