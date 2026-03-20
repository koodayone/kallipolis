"use client";

import { useState, useRef, useCallback } from "react";
import dynamic from "next/dynamic";
import { AnimatePresence, motion } from "framer-motion";
import { buildAtlasScene, DomainKey } from "@/lib/atlasScene";
import AtlasLabels from "@/components/atlas/AtlasLabels";
import DomainView from "@/components/domains/DomainView";

const AtlasCanvas = dynamic(() => import("@/components/atlas/AtlasCanvas"), {
  ssr: false,
});

type AppState = "home" | "transitioning-in" | "domain" | "transitioning-out";

export default function AtlasPage() {
  const [appState, setAppState] = useState<AppState>("home");
  const [activeDomain, setActiveDomain] = useState<DomainKey | null>(null);
  const [hoveredDomain, setHoveredDomain] = useState<DomainKey | null>(null);
  const sceneRef = useRef<ReturnType<typeof buildAtlasScene> | null>(null);

  const handleDomainClick = useCallback((domain: DomainKey) => {
    setActiveDomain(domain);
    setAppState("transitioning-in");
    // Give the Three.js dissolve animation time, then show domain view
    setTimeout(() => setAppState("domain"), 850);
  }, []);

  const handleBack = useCallback(() => {
    setAppState("transitioning-out");
    setTimeout(() => {
      setAppState("home");
      setActiveDomain(null);
      sceneRef.current?.resetScene();
    }, 550);
  }, []);

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
      {/* Persistent Three.js canvas — never unmounted */}
      <div
        style={{
          position: "fixed",
          inset: 0,
          zIndex: 0,
        }}
      >
        <AtlasCanvas
          onDomainClick={handleDomainClick}
          onHoverChange={setHoveredDomain}
          canvasOpacity={canvasOpacity}
          sceneRef={sceneRef}
        />
      </div>

      {/* Atlas domain labels — fade out during transition */}
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
            <AtlasLabels hoveredDomain={hoveredDomain} />
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
              background: "#f8f7f4",
              overflowY: "auto",
            }}
          >
            <DomainView domain={activeDomain} onBack={handleBack} />
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
