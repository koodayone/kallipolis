"use client";

import { useState, useRef, useCallback, useEffect } from "react";
import dynamic from "next/dynamic";
import { AnimatePresence, motion } from "framer-motion";
import { SchoolConfig } from "@/lib/schoolConfig";
import { buildGovernmentScene, GovReportKey } from "@/lib/governmentScene";
import StrongWorkforceView from "@/components/government/StrongWorkforceView";
import PerkinsView from "@/components/government/PerkinsView";
import RisingSun from "@/components/ui/RisingSun";

const GovernmentCanvas = dynamic(
  () => import("@/components/government/GovernmentCanvas"),
  { ssr: false }
);

const REPORT_NAMES: Record<GovReportKey, string> = {
  strong_workforce: "Strong Workforce",
  perkins_v: "Perkins V",
};

// Mirror the scene's camera constants to project world-x → screen %.
// Camera: PerspectiveCamera(fov=50, ...) at z=5.5, shapes at z=0.
const CANVAS_HEIGHT = 300;
const CAMERA_Z = 5.5;
const TAN_HALF_FOV = Math.tan((50 / 2) * (Math.PI / 180));
const SOLID_WORLD_X: Record<GovReportKey, number> = {
  strong_workforce: -1.8,
  perkins_v: 1.8,
};

function projectWorldX(worldX: number, containerWidth: number): number {
  const aspect = containerWidth / CANVAS_HEIGHT;
  const ndcX = worldX / (CAMERA_Z * TAN_HALF_FOV * aspect);
  return ((ndcX + 1) / 2) * 100;
}

type GovState = "hub" | "transitioning-in" | "report" | "transitioning-out";

type Props = {
  school: SchoolConfig;
};

export default function GovernmentView({ school }: Props) {
  const [govState, setGovState] = useState<GovState>("hub");
  const [activeReport, setActiveReport] = useState<GovReportKey | null>(null);
  const [hoveredReport, setHoveredReport] = useState<GovReportKey | null>(null);
  const lastHoveredReport = useRef<GovReportKey | null>(null);
  if (hoveredReport !== null) lastHoveredReport.current = hoveredReport;
  const [labelPositions, setLabelPositions] = useState<Record<GovReportKey, number>>({
    strong_workforce: 27,
    perkins_v: 73,
  });
  const sceneRef = useRef<ReturnType<typeof buildGovernmentScene> | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  // Restore report from URL hash on mount (e.g. /#government/strong_workforce)
  useEffect(() => {
    const segment = window.location.hash.replace("#", "").split("/")[1] as GovReportKey;
    if (["strong_workforce", "perkins_v"].includes(segment)) {
      setActiveReport(segment);
      setGovState("report");
    }
  }, []);

  // Recompute label positions whenever the canvas container resizes.
  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    const compute = () => {
      const canvas = el.querySelector("canvas");
      const w = canvas ? canvas.clientWidth : el.clientWidth;
      if (w === 0) return;
      setLabelPositions({
        strong_workforce: projectWorldX(SOLID_WORLD_X.strong_workforce, w),
        perkins_v: projectWorldX(SOLID_WORLD_X.perkins_v, w),
      });
    };
    compute();
    const ro = new ResizeObserver(compute);
    ro.observe(el);
    return () => ro.disconnect();
  }, []);

  const handleReportClick = useCallback((report: GovReportKey) => {
    setActiveReport(report);
    setGovState("transitioning-in");
    window.location.hash = `government/${report}`;
    setTimeout(() => setGovState("report"), 700);
  }, []);

  const handleBack = useCallback(() => {
    setGovState("transitioning-out");
    setTimeout(() => {
      setGovState("hub");
      setActiveReport(null);
      setHoveredReport(null);
      window.location.hash = "government";
      sceneRef.current?.resetScene();
    }, 450);
  }, []);

  const showHub = govState === "hub" || govState === "transitioning-in";
  const showReport = govState === "report" || govState === "transitioning-out";
  const canvasOpacity = govState === "hub" ? 1 : govState === "transitioning-out" ? 1 : 0;

  return (
    <div style={{ minHeight: "calc(100vh - 64px)", position: "relative" }}>
      {/* Institution identity strip — always visible in hub */}
      <AnimatePresence>
        {showHub && (
          <motion.div
            key="identity"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.35 }}
          >
            <div
              style={{
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                justifyContent: "center",
                gap: "14px",
                paddingTop: "48px",
                paddingBottom: "16px",
              }}
            >
              <img
                src={school.logoPath}
                alt={school.name}
                style={{ height: "100px", width: "auto", objectFit: "contain" }}
              />
              <span
                style={{
                  fontFamily: "var(--font-inter), Inter, system-ui, sans-serif",
                  fontSize: "15px",
                  letterSpacing: "0.1em",
                  color: "rgba(255,255,255,0.85)",
                  textTransform: "uppercase",
                  whiteSpace: "nowrap",
                  opacity: hoveredReport !== null && govState === "hub" ? 0 : 1,
                  transition: "opacity 0.5s ease-in-out",
                }}
              >
                Select Government Domain
              </span>
            </div>

            {/* Mini 3D scene */}
            <div ref={containerRef} style={{ position: "relative", height: "300px", width: "100%" }}>
              <GovernmentCanvas
                onReportClick={handleReportClick}
                onHoverChange={setHoveredReport}
                brandColor={parseInt(school.brandColor.replace("#", ""), 16)}
                canvasOpacity={canvasOpacity}
                sceneRef={sceneRef}
              />

              <RisingSun style={{
                position: "absolute",
                top: "10%",
                left: lastHoveredReport.current ? `${labelPositions[lastHoveredReport.current]}%` : "50%",
                transform: "translate(-50%, -50%)",
                opacity: hoveredReport !== null && govState === "hub" ? 1 : 0,
                transition: "opacity 0.5s ease-in-out",
                pointerEvents: "none",
              }} />

              {/* Per-shape labels — projected to match 3D solid positions */}
              {(["strong_workforce", "perkins_v"] as GovReportKey[]).map((key) => (
                <span
                  key={key}
                  style={{
                    position: "absolute",
                    bottom: "40px",
                    left: `${labelPositions[key]}%`,
                    transform: "translateX(-50%)",
                    pointerEvents: "none",
                    fontFamily: "var(--font-inter), Inter, system-ui, sans-serif",
                    fontSize: "13px",
                    fontWeight: 600,
                    letterSpacing: "0.13em",
                    textTransform: "uppercase",
                    color: hoveredReport === key ? "#c9a84c" : "rgba(255,255,255,0.5)",
                    whiteSpace: "nowrap",
                    transition: "color 0.3s ease-in-out",
                  }}
                >
                  {REPORT_NAMES[key]}
                </span>
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Sub-view */}
      <AnimatePresence>
        {showReport && activeReport && (
          <motion.div
            key="report"
            initial={{ opacity: 0 }}
            animate={{ opacity: govState === "transitioning-out" ? 0 : 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.35 }}
            style={{ position: "fixed", inset: 0, background: "#060d1f", overflowY: "auto", overscrollBehavior: "none", zIndex: 25 }}
          >
            {activeReport === "strong_workforce" && (
              <StrongWorkforceView school={school} onBack={handleBack} />
            )}
            {activeReport === "perkins_v" && (
              <PerkinsView school={school} onBack={handleBack} />
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
