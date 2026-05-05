"use client";

import { Suspense } from "react";
import { useParams, useRouter, useSearchParams } from "next/navigation";
import { motion } from "framer-motion";
import OpportunityReport from "@/college-atlas/partnerships/OpportunityReport";
import { getCollegeAtlasConfig } from "@/config/collegeAtlasConfigs";

function OpportunityRouteInner() {
  const { collegeId } = useParams<{ collegeId: string }>();
  const searchParams = useSearchParams();
  const router = useRouter();
  const config = getCollegeAtlasConfig(collegeId);
  const socCode = searchParams.get("soc") ?? "";

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
      <OpportunityReport
        school={config}
        collegeId={collegeId}
        socCode={socCode}
        onBack={() => router.push(`/${collegeId}/partnerships`)}
      />
    </motion.div>
  );
}

export default function OpportunityRoute() {
  // Suspense boundary required because useSearchParams suspends during
  // static prerender.
  return (
    <Suspense fallback={null}>
      <OpportunityRouteInner />
    </Suspense>
  );
}
