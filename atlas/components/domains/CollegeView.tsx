"use client";

import { useState, useRef, useCallback, useEffect } from "react";
import dynamic from "next/dynamic";
import { AnimatePresence, motion } from "framer-motion";
import { SchoolConfig } from "@/lib/schoolConfig";
import { buildCollegeScene, CollegeNodeKey } from "@/lib/collegeScene";
import StudentsView from "@/components/college/StudentsView";
import CurriculaView from "@/components/college/CurriculaView";
import ProgramsView from "@/components/college/ProgramsView";

const CollegeCanvas = dynamic(
  () => import("@/components/college/CollegeCanvas"),
  { ssr: false }
);

const NODE_NAMES: Record<CollegeNodeKey, string> = {
  students: "Students",
  curricula: "Curricula",
  programs: "Programs",
};

// Mirror the scene's camera constants to project world-x → screen %.
const CANVAS_HEIGHT = 360;
const CAMERA_Z = 5.5;
const TAN_HALF_FOV = Math.tan((50 / 2) * (Math.PI / 180));
const NODE_WORLD_X: Record<CollegeNodeKey, number> = {
  students: -2.2,
  curricula: 0,
  programs: 2.2,
};

function projectWorldX(worldX: number, containerWidth: number): number {
  const aspect = containerWidth / CANVAS_HEIGHT;
  const ndcX = worldX / (CAMERA_Z * TAN_HALF_FOV * aspect);
  return ((ndcX + 1) / 2) * 100;
}

type CollegeState = "hub" | "transitioning-in" | "report" | "transitioning-out";

type Props = {
  school: SchoolConfig;
};

export default function CollegeView({ school }: Props) {
  const [collegeState, setCollegeState] = useState<CollegeState>("hub");
  const [activeNode, setActiveNode] = useState<CollegeNodeKey | null>(null);
  const [labelPositions, setLabelPositions] = useState<Record<CollegeNodeKey, number>>({
    students: 20,
    curricula: 50,
    programs: 80,
  });
  const sceneRef = useRef<ReturnType<typeof buildCollegeScene> | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    const compute = () => {
      const w = el.clientWidth;
      if (w === 0) return;
      setLabelPositions({
        students: projectWorldX(NODE_WORLD_X.students, w),
        curricula: projectWorldX(NODE_WORLD_X.curricula, w),
        programs: projectWorldX(NODE_WORLD_X.programs, w),
      });
    };
    compute();
    const ro = new ResizeObserver(compute);
    ro.observe(el);
    return () => ro.disconnect();
  }, []);

  const handleNodeClick = useCallback((node: CollegeNodeKey) => {
    setActiveNode(node);
    setCollegeState("transitioning-in");
    setTimeout(() => setCollegeState("report"), 700);
  }, []);

  const handleBack = useCallback(() => {
    setCollegeState("transitioning-out");
    setTimeout(() => {
      setCollegeState("hub");
      setActiveNode(null);
      sceneRef.current?.resetScene();
    }, 450);
  }, []);

  const showHub = collegeState === "hub" || collegeState === "transitioning-in";
  const showReport = collegeState === "report" || collegeState === "transitioning-out";
  const canvasOpacity = collegeState === "hub" ? 1 : collegeState === "transitioning-out" ? 1 : 0;

  return (
    <div style={{ minHeight: "calc(100vh - 64px)", position: "relative" }}>
      <AnimatePresence>
        {showHub && (
          <motion.div
            key="hub"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.35 }}
          >
            {/* Institution identity strip */}
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
              <CollegeCanvas
                onNodeClick={handleNodeClick}
                brandColor={parseInt(school.brandColor.replace("#", ""), 16)}
                canvasOpacity={canvasOpacity}
                sceneRef={sceneRef}
              />

              {/* Per-shape labels — projected to match 3D solid positions */}
              {(["students", "curricula", "programs"] as CollegeNodeKey[]).map((key) => (
                <span
                  key={key}
                  style={{
                    position: "absolute",
                    bottom: "48px",
                    left: `${labelPositions[key]}%`,
                    transform: "translateX(-50%)",
                    pointerEvents: "none",
                    fontFamily: "var(--font-inter), Inter, system-ui, sans-serif",
                    fontSize: "13px",
                    fontWeight: 600,
                    letterSpacing: "0.13em",
                    textTransform: "uppercase",
                    color: "#ffffff",
                    whiteSpace: "nowrap",
                  }}
                >
                  {NODE_NAMES[key]}
                </span>
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Sub-view */}
      <AnimatePresence>
        {showReport && activeNode && (
          <motion.div
            key="report"
            initial={{ opacity: 0 }}
            animate={{ opacity: collegeState === "transitioning-out" ? 0 : 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.35 }}
            style={{ position: "absolute", top: 0, left: 0, right: 0 }}
          >
            {activeNode === "students" && (
              <StudentsView school={school} onBack={handleBack} />
            )}
            {activeNode === "curricula" && (
              <CurriculaView school={school} onBack={handleBack} />
            )}
            {activeNode === "programs" && (
              <ProgramsView school={school} onBack={handleBack} />
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
