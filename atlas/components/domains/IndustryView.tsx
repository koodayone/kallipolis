"use client";

import { useState, useRef, useCallback, useEffect } from "react";
import dynamic from "next/dynamic";
import { AnimatePresence, motion } from "framer-motion";
import { SchoolConfig } from "@/lib/schoolConfig";
import { buildIndustryScene, IndustryNodeKey } from "@/lib/industryScene";
import PartnershipsView from "@/components/industry/PartnershipsView";
import OccupationsView from "@/components/industry/OccupationsView";
import EmployersView from "@/components/industry/EmployersView";
import RisingSun from "@/components/ui/RisingSun";

const IndustryCanvas = dynamic(
  () => import("@/components/industry/IndustryCanvas"),
  { ssr: false }
);

const NODE_NAMES: Record<IndustryNodeKey, string> = {
  partnerships: "Partnerships",
  occupations: "Occupations",
  employers: "Employers",
};

const CANVAS_HEIGHT = 300;
const CAMERA_Z = 5.5;
const TAN_HALF_FOV = Math.tan((50 / 2) * (Math.PI / 180));
const NODE_WORLD_X: Record<IndustryNodeKey, number> = {
  partnerships: -3.2,
  occupations: 0,
  employers: 3.2,
};

function projectWorldX(worldX: number, containerWidth: number): number {
  const aspect = containerWidth / CANVAS_HEIGHT;
  const ndcX = worldX / (CAMERA_Z * TAN_HALF_FOV * aspect);
  return ((ndcX + 1) / 2) * 100;
}

type IndustryState = "hub" | "transitioning-in" | "report" | "transitioning-out";

type Props = {
  school: SchoolConfig;
};

export default function IndustryView({ school }: Props) {
  const [industryState, setIndustryState] = useState<IndustryState>("hub");
  const [activeNode, setActiveNode] = useState<IndustryNodeKey | null>(null);
  const [hoveredNode, setHoveredNode] = useState<IndustryNodeKey | null>(null);
  const lastHoveredNode = useRef<IndustryNodeKey | null>(null);
  if (hoveredNode !== null) lastHoveredNode.current = hoveredNode;
  const [labelPositions, setLabelPositions] = useState<Record<IndustryNodeKey, number>>({
    partnerships: 20,
    occupations: 50,
    employers: 80,
  });
  const sceneRef = useRef<ReturnType<typeof buildIndustryScene> | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const segment = window.location.hash.replace("#", "").split("/")[1] as IndustryNodeKey;
    if (["partnerships", "occupations", "employers"].includes(segment)) {
      setActiveNode(segment);
      setIndustryState("report");
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
        partnerships: projectWorldX(NODE_WORLD_X.partnerships, w),
        occupations: projectWorldX(NODE_WORLD_X.occupations, w),
        employers: projectWorldX(NODE_WORLD_X.employers, w),
      });
    };
    compute();
    const ro = new ResizeObserver(compute);
    ro.observe(el);
    return () => ro.disconnect();
  }, []);

  const handleNodeClick = useCallback((node: IndustryNodeKey) => {
    setActiveNode(node);
    setIndustryState("transitioning-in");
    window.location.hash = `industry/${node}`;
    setTimeout(() => setIndustryState("report"), 700);
  }, []);

  const handleBack = useCallback(() => {
    setIndustryState("transitioning-out");
    setTimeout(() => {
      setIndustryState("hub");
      setActiveNode(null);
      setHoveredNode(null);
      window.location.hash = "industry";
      sceneRef.current?.resetScene();
    }, 450);
  }, []);

  const showHub = industryState === "hub" || industryState === "transitioning-in";
  const showReport = industryState === "report" || industryState === "transitioning-out";
  const canvasOpacity = industryState === "hub" ? 1 : industryState === "transitioning-out" ? 1 : 0;

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
                  opacity: hoveredNode !== null && industryState === "hub" ? 0 : 1,
                  transition: "opacity 0.5s ease-in-out",
                }}
              >
                Select Industry Domain
              </span>
            </div>

            {/* Mini 3D scene */}
            <div ref={containerRef} style={{ position: "relative", height: "300px", width: "100%" }}>
              <IndustryCanvas
                onNodeClick={handleNodeClick}
                onHoverChange={setHoveredNode}
                brandColor={parseInt(school.brandColorNeon.replace("#", ""), 16)}
                canvasOpacity={canvasOpacity}
                sceneRef={sceneRef}
              />

              <RisingSun style={{
                position: "absolute",
                top: "10%",
                left: lastHoveredNode.current ? `${labelPositions[lastHoveredNode.current]}%` : "50%",
                transform: "translate(-50%, -50%)",
                opacity: hoveredNode !== null && industryState === "hub" ? 1 : 0,
                transition: "opacity 0.5s ease-in-out",
                pointerEvents: "none",
              }} />

              {/* Per-shape labels */}
              {(["partnerships", "occupations", "employers"] as IndustryNodeKey[]).map((key) => (
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
      {(industryState === "report" || industryState === "transitioning-out") && (
        <div style={{ position: "fixed", inset: 0, background: "#060d1f", zIndex: 24 }} />
      )}

      {/* Sub-view */}
      <AnimatePresence>
        {showReport && activeNode && (
          <motion.div
            key="report"
            initial={{ opacity: 0 }}
            animate={{ opacity: industryState === "transitioning-out" ? 0 : 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.35 }}
            style={{ position: "fixed", inset: 0, background: "#060d1f", overflowY: "auto", overscrollBehavior: "none", zIndex: 25 }}
          >
            {activeNode === "partnerships" && (
              <PartnershipsView school={school} onBack={handleBack} />
            )}
            {activeNode === "occupations" && (
              <OccupationsView school={school} onBack={handleBack} />
            )}
            {activeNode === "employers" && (
              <EmployersView school={school} onBack={handleBack} />
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
