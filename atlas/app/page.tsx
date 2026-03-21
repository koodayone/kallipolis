"use client";

import { useState, useRef, useCallback, useEffect } from "react";
import dynamic from "next/dynamic";
import Link from "next/link";
import { AnimatePresence, motion } from "framer-motion";
import { buildAtlasScene, DomainKey } from "@/lib/atlasScene";
import { schoolConfig } from "@/lib/schoolConfig";
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

  // Restore domain from URL hash on mount (e.g. /#government after a refresh)
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
          brandColor={parseInt(schoolConfig.brandColor.replace("#", ""), 16)}
          sceneRef={sceneRef}
        />
      </div>

      {/* State View nav link — top-right, visible on home screen only */}
      <AnimatePresence>
        {showLabels && (
          <motion.div
            key="state-nav"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.35 }}
            style={{ position: "fixed", top: "28px", right: "36px", zIndex: 6 }}
          >
            <Link
              href="/state"
              style={{
                display: "flex",
                alignItems: "center",
                gap: "6px",
                fontFamily: "var(--font-inter), Inter, system-ui, sans-serif",
                fontSize: "11px",
                fontWeight: 500,
                letterSpacing: "0.12em",
                textTransform: "uppercase",
                color: "rgba(255,255,255,0.65)",
                textDecoration: "none",
                transition: "color 0.15s",
              }}
              onMouseEnter={(e) => ((e.currentTarget as HTMLElement).style.color = "#ffffff")}
              onMouseLeave={(e) => ((e.currentTarget as HTMLElement).style.color = "rgba(255,255,255,0.65)")}
            >
              State View
              <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
                <path
                  d="M2.5 6h7M6 2.5l3.5 3.5L6 9.5"
                  stroke="currentColor"
                  strokeWidth="1.3"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>
            </Link>
          </motion.div>
        )}
      </AnimatePresence>

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
              background: "#050e1b",
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
