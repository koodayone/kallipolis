"use client";

import { useState, useRef, useCallback, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import dynamic from "next/dynamic";
import { AnimatePresence, motion } from "framer-motion";
import { buildAtlasScene, DomainKey } from "@/lib/atlasScene";
import { getCollegeAtlasConfig } from "@/lib/collegeAtlasConfigs";
import AtlasLabels from "@/components/atlas/AtlasLabels";
import DomainView from "@/components/domains/DomainView";
import AtlasMenu from "@/components/auth/AtlasMenu";

const AtlasCanvas = dynamic(() => import("@/components/atlas/AtlasCanvas"), {
  ssr: false,
});

type AppState = "home" | "transitioning-in" | "domain" | "transitioning-out";

export default function CollegeAtlasPage() {
  const { collegeId } = useParams<{ collegeId: string }>();
  const router = useRouter();
  const config = getCollegeAtlasConfig(collegeId);

  const [appState, setAppState] = useState<AppState>("home");
  const [activeDomain, setActiveDomain] = useState<DomainKey | null>(null);
  const [hoveredDomain, setHoveredDomain] = useState<DomainKey | null>(null);
  const sceneRef = useRef<ReturnType<typeof buildAtlasScene> | null>(null);

  // Redirect if college not found
  useEffect(() => {
    if (!config) router.replace("/");
  }, [config, router]);

  // Restore domain from URL hash on mount
  useEffect(() => {
    const hash = window.location.hash.replace("#", "").split("/")[0] as DomainKey;
    if (["government", "college", "industry"].includes(hash)) {
      setActiveDomain(hash);
      setAppState("domain");
    }
  }, []);

  const handleDomainClick = useCallback((domain: DomainKey) => {
    setActiveDomain(domain);
    setAppState("transitioning-in");
    window.location.hash = domain;
    setTimeout(() => setAppState("domain"), 850);
  }, []);

  const handleBack = useCallback(() => {
    setAppState("transitioning-out");
    setTimeout(() => {
      setAppState("home");
      setActiveDomain(null);
      history.pushState(null, "", window.location.pathname);
      sceneRef.current?.resetScene();
    }, 550);
  }, []);

  if (!config) return null;

  const canvasOpacity =
    appState === "home" ? 1 : appState === "transitioning-out" ? 1 : 0;

  const showLabels = appState === "home";
  const showDomain = appState === "domain" || appState === "transitioning-out";

  return (
    <div
      style={{
        position: "relative",
        width: "100vw",
        height: "100vh",
        background: "#0a0a0f",
        overflow: "hidden",
      }}
    >
      {/* Persistent Three.js canvas */}
      <div style={{ position: "fixed", inset: 0, zIndex: 0 }}>
        <AtlasCanvas
          onDomainClick={handleDomainClick}
          onHoverChange={setHoveredDomain}
          canvasOpacity={canvasOpacity}
          brandColor={parseInt(config.brandColor.replace("#", ""), 16)}
          sceneRef={sceneRef}
        />
      </div>

      {/* Menu — top-right, visible on home screen only */}
      <AnimatePresence>
        {showLabels && (
          <motion.div
            key="atlas-menu"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.35 }}
            style={{ position: "fixed", top: "28px", right: "36px", zIndex: 6 }}
          >
            <AtlasMenu navItems={[{ label: "State View", href: "/state", icon: (
              <svg width="12" height="16" viewBox="0 0 16 22" fill="#c9a84c">
                <path d="M0.0,3.6L0.9,5.0L1.1,7.2L2.5,9.1L2.2,8.7L2.2,9.3L3.0,9.7L3.1,9.0L4.6,9.2L3.2,9.3L3.9,10.6L3.1,9.7L2.9,10.4L3.2,11.3L4.2,12.0L3.8,12.6L3.9,13.2L5.9,16.0L5.9,17.3L9.2,18.5L9.3,19.2L10.8,20.2L11.3,22.0L15.4,21.5L15.1,20.0L15.5,18.4L16.0,18.0L15.2,16.3L6.9,7.0L6.9,0.0L0.3,0.0L0.5,1.3L0.3,2.9L0.5,2.7L0.0,3.6Z" />
              </svg>
            ) }]} />
          </motion.div>
        )}
      </AnimatePresence>

      {/* Atlas domain labels */}
      <AnimatePresence>
        {showLabels && (
          <motion.div
            key="labels"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.35 }}
            style={{ position: "fixed", inset: 0, zIndex: 5, pointerEvents: "none" }}
          >
            <AtlasLabels hoveredDomain={hoveredDomain} school={config} />
          </motion.div>
        )}
      </AnimatePresence>

      {/* Domain overlay */}
      <AnimatePresence>
        {showDomain && activeDomain && (
          <motion.div
            key="domain"
            initial={{ opacity: 0 }}
            animate={{ opacity: appState === "transitioning-out" ? 0 : 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.45 }}
            style={{
              position: "fixed",
              inset: 0,
              zIndex: 10,
              background: "#041e54",
              overflowY: "auto",
            }}
          >
            <DomainView domain={activeDomain} onBack={handleBack} school={config} />
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
