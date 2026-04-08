"use client";

import { useState, useRef, useCallback, useEffect } from "react";
import dynamic from "next/dynamic";
import { AnimatePresence, motion } from "framer-motion";
import { SchoolConfig } from "@/lib/schoolConfig";
import { buildGovernmentScene, GovReportKey } from "@/lib/governmentScene";
import StrongWorkforceView from "@/components/government/StrongWorkforceView";
import StudentsView from "@/components/college/StudentsView";
import CoursesView from "@/components/college/CoursesView";
import PartnershipsView from "@/components/industry/PartnershipsView";
import OccupationsView from "@/components/industry/OccupationsView";
import EmployersView from "@/components/industry/EmployersView";
import RisingSun from "@/components/ui/RisingSun";

const GovernmentCanvas = dynamic(
  () => import("@/components/government/GovernmentCanvas"),
  { ssr: false }
);

const ALL_KEYS: GovReportKey[] = [
  "students", "partnerships", "employers",
  "courses", "occupations", "strong_workforce",
];

const REPORT_NAMES: Record<GovReportKey, string> = {
  students: "Students",
  courses: "Courses",
  partnerships: "Partnerships",
  occupations: "Occupations",
  employers: "Employers",
  strong_workforce: "Strong Workforce",
};

// Camera at z=7.5, fov=50
const CANVAS_HEIGHT = 500;
const CAMERA_Z = 8.5;
const TAN_HALF_FOV = Math.tan((50 / 2) * (Math.PI / 180));

// World positions matching the scene config
const SOLID_POSITIONS: Record<GovReportKey, { x: number; y: number }> = {
  students:         { x: -4.2, y:  1.5 },
  partnerships:     { x:  0.0, y:  1.5 },
  employers:        { x:  4.2, y:  1.5 },
  courses:          { x: -4.2, y: -2.0 },
  occupations:      { x:  0.0, y: -2.0 },
  strong_workforce: { x:  4.2, y: -2.0 },
};

function projectWorldX(worldX: number, containerWidth: number): number {
  const aspect = containerWidth / CANVAS_HEIGHT;
  const ndcX = worldX / (CAMERA_Z * TAN_HALF_FOV * aspect);
  return ((ndcX + 1) / 2) * 100;
}

const CAMERA_Y = 0.2;

function projectWorldY(worldY: number): number {
  const ndcY = (worldY - CAMERA_Y) / (CAMERA_Z * TAN_HALF_FOV);
  return ((1 - ndcY) / 2) * 100;
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
  const [labelPositions, setLabelPositions] = useState<Record<GovReportKey, number>>(() => {
    const pos: any = {};
    for (const key of ALL_KEYS) pos[key] = 50;
    return pos;
  });
  const sceneRef = useRef<ReturnType<typeof buildGovernmentScene> | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  // Restore report from URL hash on mount
  useEffect(() => {
    const segment = window.location.hash.replace("#", "").split("/")[1] as GovReportKey;
    if (ALL_KEYS.includes(segment)) {
      setActiveReport(segment);
      setGovState("report");
    }
  }, []);

  // Track projected screen positions from the 3D scene
  const [projectedPositions, setProjectedPositions] = useState<Record<string, { x: number; y: number }>>({});

  useEffect(() => {
    let rafId: number;
    const update = () => {
      if (sceneRef.current?.getProjectedPositions) {
        setProjectedPositions(sceneRef.current.getProjectedPositions());
      }
      rafId = requestAnimationFrame(update);
    };
    // Start after a short delay to let the scene initialize
    const timeout = setTimeout(() => { rafId = requestAnimationFrame(update); }, 100);
    return () => { cancelAnimationFrame(rafId); clearTimeout(timeout); };
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
      <AnimatePresence>
        {showHub && (
          <motion.div
            key="identity"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.35 }}
          >
            {/* 3D scene */}
            <div ref={containerRef} style={{ position: "relative", height: "calc(100vh - 180px)", width: "100%", marginTop: "16px" }}>

              {/* Sun + label — absolutely positioned over the canvas */}
              <div
                style={{
                  position: "absolute",
                  top: "-2%",
                  left: "50%",
                  transform: "translateX(-50%)",
                  display: "flex",
                  flexDirection: "column",
                  alignItems: "center",
                  gap: "16px",
                  zIndex: 5,
                  pointerEvents: "none",
                }}
              >
                <div style={{
                  opacity: hoveredReport !== null && govState === "hub" ? 1 : 0,
                  transition: "opacity 0.5s ease-in-out",
                  height: "48px",
                  marginTop: "-14px",
                }}>
                  <RisingSun />
                </div>

                <span
                  style={{
                    fontFamily: "var(--font-inter), Inter, system-ui, sans-serif",
                    fontSize: "15px",
                    fontWeight: 600,
                    letterSpacing: "0.12em",
                    color: hoveredReport ? "#c9a84c" : "rgba(255,255,255,0.85)",
                    textTransform: "uppercase",
                    whiteSpace: "nowrap",
                    transition: "color 0.3s ease-in-out",
                  }}
                >
                  {hoveredReport && govState === "hub" ? REPORT_NAMES[hoveredReport] : "Select a Domain"}
                </span>
              </div>
              <GovernmentCanvas
                onReportClick={handleReportClick}
                onHoverChange={setHoveredReport}
                brandColor={parseInt(school.brandColorNeon.replace("#", ""), 16)}
                canvasOpacity={canvasOpacity}
                sceneRef={sceneRef}
              />

              {/* Per-form labels — positioned using 3D→screen projection */}
              {ALL_KEYS.map((key) => {
                const pos = projectedPositions[key];
                if (!pos) return null;
                return (
                  <span
                    key={key}
                    style={{
                      position: "absolute",
                      top: `${pos.y + 18}%`,
                      left: `${pos.x}%`,
                      transform: "translateX(-50%)",
                      pointerEvents: "none",
                      fontFamily: "var(--font-inter), Inter, system-ui, sans-serif",
                      fontSize: "13px",
                      fontWeight: 600,
                      letterSpacing: "0.13em",
                      textTransform: "uppercase",
                      color: hoveredReport === key ? "#c9a84c" : "rgba(255,255,255,0.35)",
                      whiteSpace: "nowrap",
                      transition: "color 0.3s ease-in-out",
                    }}
                  >
                    {REPORT_NAMES[key]}
                  </span>
                );
              })}
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Solid backdrop */}
      {(govState === "report" || govState === "transitioning-out") && (
        <div style={{ position: "fixed", inset: 0, background: "#060d1f", zIndex: 24 }} />
      )}

      {/* Sub-views */}
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
            {activeReport === "students" && (
              <StudentsView school={school} onBack={handleBack} />
            )}
            {activeReport === "courses" && (
              <CoursesView school={school} onBack={handleBack} />
            )}
            {activeReport === "partnerships" && (
              <PartnershipsView school={school} onBack={handleBack} />
            )}
            {activeReport === "occupations" && (
              <OccupationsView school={school} onBack={handleBack} />
            )}
            {activeReport === "employers" && (
              <EmployersView school={school} onBack={handleBack} />
            )}
            {activeReport === "strong_workforce" && (
              <StrongWorkforceView school={school} onBack={handleBack} />
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
