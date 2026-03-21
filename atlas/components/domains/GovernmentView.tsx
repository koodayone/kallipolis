"use client";

import { useState, useRef, useCallback, useEffect } from "react";
import dynamic from "next/dynamic";
import { AnimatePresence, motion } from "framer-motion";
import { SchoolConfig } from "@/lib/schoolConfig";
import { buildGovernmentScene, GovReportKey } from "@/lib/governmentScene";
import StrongWorkforceView from "@/components/government/StrongWorkforceView";
import PerkinsView from "@/components/government/PerkinsView";

const GovernmentCanvas = dynamic(
  () => import("@/components/government/GovernmentCanvas"),
  { ssr: false }
);

const REPORT_NAMES: Record<GovReportKey, string> = {
  strong_workforce: "Strong Workforce Program",
  perkins_v: "Perkins V",
};

// Mirror the scene's camera constants to project world-x → screen %.
// Camera: PerspectiveCamera(fov=50, ...) at z=5.5, shapes at z=0.
const CANVAS_HEIGHT = 360;
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
  const [labelPositions, setLabelPositions] = useState<Record<GovReportKey, number>>({
    strong_workforce: 27,
    perkins_v: 73,
  });
  const sceneRef = useRef<ReturnType<typeof buildGovernmentScene> | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  // Recompute label positions whenever the canvas container resizes.
  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    const compute = () => {
      const w = el.clientWidth;
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
    setTimeout(() => setGovState("report"), 700);
  }, []);

  const handleBack = useCallback(() => {
    setGovState("transitioning-out");
    setTimeout(() => {
      setGovState("hub");
      setActiveReport(null);
      sceneRef.current?.resetScene();
    }, 450);
  }, []);

  const showHub = govState === "hub" || govState === "transitioning-in";
  const showReport = govState === "report" || govState === "transitioning-out";
  const canvasOpacity = govState === "hub" ? 1 : govState === "transitioning-out" ? 1 : 0;

  return (
    <div style={{ minHeight: "calc(100vh - 64px)" }}>
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
                alignItems: "center",
                justifyContent: "center",
                paddingTop: "36px",
                paddingBottom: "36px",
                borderBottom: "1px solid rgba(255,255,255,0.1)",
              }}
            >
              <img
                src={school.logoPathWide ?? school.logoPath}
                alt={school.name}
                style={{ height: "60px", width: "auto", objectFit: "contain" }}
              />
            </div>

            {/* Mini 3D scene */}
            <div ref={containerRef} style={{ position: "relative", height: "360px", width: "100%" }}>
              <GovernmentCanvas
                onReportClick={handleReportClick}
                brandColor={parseInt(school.brandColor.replace("#", ""), 16)}
                canvasOpacity={canvasOpacity}
                sceneRef={sceneRef}
              />

              {/* Per-shape labels — projected to match 3D solid positions */}
              {(["strong_workforce", "perkins_v"] as GovReportKey[]).map((key) => (
                <span
                  key={key}
                  style={{
                    position: "absolute",
                    bottom: "28px",
                    left: `${labelPositions[key]}%`,
                    transform: "translateX(-50%)",
                    pointerEvents: "none",
                    fontFamily: "var(--font-inter), Inter, system-ui, sans-serif",
                    fontSize: "11px",
                    fontWeight: 600,
                    letterSpacing: "0.13em",
                    textTransform: "uppercase",
                    color: "rgba(255,255,255,0.55)",
                    whiteSpace: "nowrap",
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
