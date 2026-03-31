"use client";

import { useState, useRef, useCallback, useEffect } from "react";
import dynamic from "next/dynamic";
import { AnimatePresence, motion } from "framer-motion";
import { SchoolConfig } from "@/lib/schoolConfig";
import { buildCollegeScene, CollegeNodeKey } from "@/lib/collegeScene";
import StudentsView from "@/components/college/StudentsView";
import CoursesView from "@/components/college/CoursesView";
import RisingSun from "@/components/ui/RisingSun";

const CollegeCanvas = dynamic(
  () => import("@/components/college/CollegeCanvas"),
  { ssr: false }
);

const NODE_NAMES: Record<CollegeNodeKey, string> = {
  students: "Students",
  courses: "Courses",
};

// Mirror the scene's camera constants to project world-x → screen %.
const CANVAS_HEIGHT = 300;
const CAMERA_Z = 5.5;
const TAN_HALF_FOV = Math.tan((50 / 2) * (Math.PI / 180));
const NODE_WORLD_X: Record<CollegeNodeKey, number> = {
  students: -1.8,
  courses: 1.8,
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
  const [hoveredNode, setHoveredNode] = useState<CollegeNodeKey | null>(null);
  const lastHoveredNode = useRef<CollegeNodeKey | null>(null);
  if (hoveredNode !== null) lastHoveredNode.current = hoveredNode;
  const [labelPositions, setLabelPositions] = useState<Record<CollegeNodeKey, number>>({
    students: 30,
    courses: 70,
  });
  const sceneRef = useRef<ReturnType<typeof buildCollegeScene> | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const segment = window.location.hash.replace("#", "").split("/")[1] as CollegeNodeKey;
    if (["students", "courses"].includes(segment)) {
      setActiveNode(segment);
      setCollegeState("report");
    }
  }, []);

  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    const compute = () => {
      const canvas = el.querySelector("canvas");
      const w = canvas ? canvas.clientWidth : el.clientWidth;
      if (w === 0) return;
      setLabelPositions({
        students: projectWorldX(NODE_WORLD_X.students, w),
        courses: projectWorldX(NODE_WORLD_X.courses, w),
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
    window.location.hash = `college/${node}`;
    setTimeout(() => setCollegeState("report"), 700);
  }, []);

  const handleBack = useCallback(() => {
    setCollegeState("transitioning-out");
    setTimeout(() => {
      setCollegeState("hub");
      setActiveNode(null);
      setHoveredNode(null);
      window.location.hash = "college";
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
                flexDirection: "column",
                alignItems: "center",
                justifyContent: "center",
                gap: "14px",
                paddingTop: "64px",
                paddingBottom: "32px",
              }}
            >
              <span
                style={{
                  fontFamily: "var(--font-inter), Inter, system-ui, sans-serif",
                  fontSize: "15px",
                  letterSpacing: "0.1em",
                  color: "rgba(255,255,255,0.85)",
                  textTransform: "uppercase",
                  whiteSpace: "nowrap",
                  opacity: hoveredNode !== null && collegeState === "hub" ? 0 : 1,
                  transition: "opacity 0.5s ease-in-out",
                }}
              >
                Select College Domain
              </span>
            </div>

            {/* Mini 3D scene */}
            <div ref={containerRef} style={{ position: "relative", height: "300px", width: "100%" }}>
              <CollegeCanvas
                onNodeClick={handleNodeClick}
                onHoverChange={setHoveredNode}
                brandColor={parseInt(school.brandColor.replace("#", ""), 16)}
                canvasOpacity={canvasOpacity}
                sceneRef={sceneRef}
              />

              <RisingSun style={{
                position: "absolute",
                top: "10%",
                left: lastHoveredNode.current ? `${labelPositions[lastHoveredNode.current]}%` : "50%",
                transform: "translate(-50%, -50%)",
                opacity: hoveredNode !== null && collegeState === "hub" ? 1 : 0,
                transition: "opacity 0.5s ease-in-out",
                pointerEvents: "none",
              }} />

              {/* Per-shape labels — projected to match 3D solid positions */}
              {(["students", "courses"] as CollegeNodeKey[]).map((key) => (
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
                    color: hoveredNode === key ? "#c9a84c" : "rgba(255,255,255,0.5)",
                    whiteSpace: "nowrap",
                    transition: "color 0.3s ease-in-out",
                  }}
                >
                  {NODE_NAMES[key]}
                </span>
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Solid backdrop — covers hub instantly during transition */}
      {(collegeState === "report" || collegeState === "transitioning-out") && (
        <div style={{ position: "fixed", inset: 0, background: "#060d1f", zIndex: 24 }} />
      )}

      {/* Sub-view */}
      <AnimatePresence>
        {showReport && activeNode && (
          <motion.div
            key="report"
            initial={{ opacity: 0 }}
            animate={{ opacity: collegeState === "transitioning-out" ? 0 : 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.35 }}
            style={{ position: "fixed", inset: 0, background: "#060d1f", overflowY: "auto", overscrollBehavior: "none", zIndex: 25 }}
          >
            {activeNode === "students" && (
              <StudentsView school={school} onBack={handleBack} />
            )}
            {activeNode === "courses" && (
              <CoursesView school={school} onBack={handleBack} />
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
