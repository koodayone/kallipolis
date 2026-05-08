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
  // `sector` carries the click-context sector from the partnerships
  // listing. SOCs that belong to multiple PCAH sectors render under
  // whichever sector the user navigated from. Undefined when not
  // supplied (deep-linked or back-navigated reports fall back to the
  // backend's alphabetical default).
  const sector = searchParams.get("sector") ?? undefined;

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
        socCode={socCode}
        sector={sector}
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
