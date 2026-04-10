"use client";

import { useState, useRef, useCallback, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import dynamic from "next/dynamic";
import { AnimatePresence, motion } from "framer-motion";
import { buildAtlasScene, AtlasNodeKey, ALL_NODE_KEYS, NODE_NAMES } from "@/lib/atlasScene";
import { getCollegeAtlasConfig } from "@/lib/collegeAtlasConfigs";
import AtlasMenu from "@/components/auth/AtlasMenu";
import StudentsView from "@/components/college/StudentsView";
import CoursesView from "@/components/college/CoursesView";
import PartnershipsView from "@/components/industry/PartnershipsView";
import OccupationsView from "@/components/industry/OccupationsView";
import EmployersView from "@/components/industry/EmployersView";
import StrongWorkforceView from "@/components/government/StrongWorkforceView";
import KallipolisBrand from "@/components/ui/KallipolisBrand";

const AtlasCanvas = dynamic(() => import("@/components/atlas/AtlasCanvas"), {
  ssr: false,
});

type AppState = "home" | "transitioning-in" | "leaf" | "transitioning-out";

export default function CollegeAtlasPage() {
  const { collegeId } = useParams<{ collegeId: string }>();
  const router = useRouter();
  const config = getCollegeAtlasConfig(collegeId);

  const [appState, setAppState] = useState<AppState>("home");
  const [activeNode, setActiveNode] = useState<AtlasNodeKey | null>(null);
  const [hoveredNode, setHoveredNode] = useState<AtlasNodeKey | null>(null);
  const sceneRef = useRef<ReturnType<typeof buildAtlasScene> | null>(null);

  // Projected label positions from the 3D scene
  const [projectedPositions, setProjectedPositions] = useState<Record<string, { x: number; y: number }>>({});

  // Redirect if college not found
  useEffect(() => {
    if (!config) router.replace("/");
  }, [config, router]);

  // Restore node from URL hash on mount
  useEffect(() => {
    const hash = window.location.hash.replace("#", "") as AtlasNodeKey;
    if (ALL_NODE_KEYS.includes(hash)) {
      setActiveNode(hash);
      setAppState("leaf");
      setTimeout(() => sceneRef.current?.setPaused(true), 200);
    }
  }, []);

  // Track projected positions from 3D scene — only when home
  useEffect(() => {
    let rafId: number;
    const update = () => {
      if (appState === "home" && sceneRef.current?.getProjectedPositions) {
        setProjectedPositions(sceneRef.current.getProjectedPositions());
      }
      rafId = requestAnimationFrame(update);
    };
    const timeout = setTimeout(() => { rafId = requestAnimationFrame(update); }, 100);
    return () => { cancelAnimationFrame(rafId); clearTimeout(timeout); };
  }, [appState]);

  const handleNodeClick = useCallback((node: AtlasNodeKey) => {
    setActiveNode(node);
    setAppState("transitioning-in");
    window.location.hash = node;
    setTimeout(() => {
      setAppState("leaf");
      sceneRef.current?.setPaused(true);
    }, 850);
  }, []);

  const handleBack = useCallback(() => {
    setAppState("transitioning-out");
    setTimeout(() => {
      sceneRef.current?.setPaused(false);
      sceneRef.current?.resetScene();
      setAppState("home");
      setActiveNode(null);
      setHoveredNode(null);
      history.pushState(null, "", window.location.pathname);
    }, 550);
  }, []);

  if (!config) return null;

  const canvasOpacity =
    appState === "home" ? 1 : appState === "transitioning-out" ? 1 : 0;

  const showLabels = appState === "home";
  const showLeaf = appState === "leaf" || appState === "transitioning-out";

  return (
    <div
      style={{
        position: "relative",
        width: "100vw",
        height: "100vh",
        background: "#060d1f",
        overflow: "hidden",
      }}
    >
      {/* Persistent Three.js canvas */}
      <div style={{ position: "fixed", inset: 0, zIndex: 0 }}>
        <AtlasCanvas
          onNodeClick={handleNodeClick}
          onHoverChange={setHoveredNode}
          canvasOpacity={canvasOpacity}
          brandColor={parseInt(config.brandColorNeon.replace("#", ""), 16)}
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
            style={{ position: "fixed", top: "26px", right: "36px", zIndex: 6 }}
          >
            <AtlasMenu navItems={[{ label: "State View", href: "/state", icon: (
              <svg width="12" height="16" viewBox="0 0 16 22" fill="#c9a84c">
                <path d="M0.0,3.6L0.9,5.0L1.1,7.2L2.5,9.1L2.2,8.7L2.2,9.3L3.0,9.7L3.1,9.0L4.6,9.2L3.2,9.3L3.9,10.6L3.1,9.7L2.9,10.4L3.2,11.3L4.2,12.0L3.8,12.6L3.9,13.2L5.9,16.0L5.9,17.3L9.2,18.5L9.3,19.2L10.8,20.2L11.3,22.0L15.4,21.5L15.1,20.0L15.5,18.4L16.0,18.0L15.2,16.3L6.9,7.0L6.9,0.0L0.3,0.0L0.5,1.3L0.3,2.9L0.5,2.7L0.0,3.6Z" />
              </svg>
            ) }]} />
          </motion.div>
        )}
      </AnimatePresence>

      {/* College name — top center */}
      <AnimatePresence>
        {showLabels && (
          <motion.div
            key="college-name"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.35 }}
            style={{
              position: "fixed",
              top: "26px",
              left: "50%",
              transform: "translateX(-50%)",
              zIndex: 6,
              pointerEvents: "none",
            }}
          >
            <span style={{
              fontFamily: "var(--font-days-one), sans-serif",
              fontSize: "18px",
              letterSpacing: "0.08em",
              textTransform: "uppercase",
              color: "rgba(255,255,255,0.85)",
            }}>
              {config.name}
            </span>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Kallipolis logo — top left */}
      <AnimatePresence>
        {showLabels && (
          <motion.div
            key="logo"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.35 }}
            style={{
              position: "fixed",
              top: "20px",
              left: "28px",
              zIndex: 6,
              display: "flex",
              alignItems: "center",
              gap: "7px",
              pointerEvents: "auto",
            }}
          >
            <KallipolisBrand />
          </motion.div>
        )}
      </AnimatePresence>

      {/* Node labels — positioned using 3D projection */}
      <AnimatePresence>
        {showLabels && (
          <motion.div
            key="node-labels"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.35 }}
            style={{ position: "fixed", inset: 0, zIndex: 5, pointerEvents: "none" }}
          >
            {ALL_NODE_KEYS.map((key) => {
              const pos = projectedPositions[key];
              if (!pos) return null;
              return (
                <span
                  key={key}
                  style={{
                    position: "absolute",
                    top: `${pos.y + 14}%`,
                    left: `${pos.x}%`,
                    transform: "translateX(-50%)",
                    pointerEvents: "none",
                    fontFamily: "var(--font-inter), Inter, system-ui, sans-serif",
                    fontSize: "13px",
                    fontWeight: 600,
                    letterSpacing: "0.13em",
                    textTransform: "uppercase",
                    color: hoveredNode === key ? "#c9a84c" : "rgba(255,255,255,0.35)",
                    whiteSpace: "nowrap",
                    transition: "color 0.3s ease-in-out",
                  }}
                >
                  {NODE_NAMES[key]}
                </span>
              );
            })}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Leaf view overlay */}
      <AnimatePresence>
        {showLeaf && activeNode && (
          <motion.div
            key="leaf"
            initial={{ opacity: 0 }}
            animate={{ opacity: appState === "transitioning-out" ? 0 : 1 }}
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
            {activeNode === "students" && (
              <StudentsView school={config} onBack={handleBack} />
            )}
            {activeNode === "courses" && (
              <CoursesView school={config} onBack={handleBack} />
            )}
            {activeNode === "partnerships" && (
              <PartnershipsView school={config} onBack={handleBack} />
            )}
            {activeNode === "occupations" && (
              <OccupationsView school={config} onBack={handleBack} />
            )}
            {activeNode === "employers" && (
              <EmployersView school={config} onBack={handleBack} />
            )}
            {activeNode === "strong_workforce" && (
              <StrongWorkforceView school={config} onBack={handleBack} />
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
