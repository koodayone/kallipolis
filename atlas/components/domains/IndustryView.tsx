"use client";

import { useState, useRef, useCallback, useEffect } from "react";
import dynamic from "next/dynamic";
import { AnimatePresence, motion } from "framer-motion";
import { SchoolConfig } from "@/lib/schoolConfig";
import { buildIndustryScene, IndustryNodeKey } from "@/lib/industryScene";
import PartnershipsView from "@/components/industry/PartnershipsView";
import ResearchView from "@/components/industry/ResearchView";
import RisingSun from "@/components/ui/RisingSun";

const IndustryCanvas = dynamic(
  () => import("@/components/industry/IndustryCanvas"),
  { ssr: false }
);

const NODE_NAMES: Record<IndustryNodeKey, string> = {
  partnerships: "Partnerships",
  research: "Research",
};

const CANVAS_HEIGHT = 300;
const CAMERA_Z = 5.5;
const TAN_HALF_FOV = Math.tan((50 / 2) * (Math.PI / 180));
const NODE_WORLD_X: Record<IndustryNodeKey, number> = {
  partnerships: -1.8,
  research: 1.8,
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
    partnerships: 30,
    research: 70,
  });
  const sceneRef = useRef<ReturnType<typeof buildIndustryScene> | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const segment = window.location.hash.replace("#", "").split("/")[1] as IndustryNodeKey;
    if (["partnerships", "research"].includes(segment)) {
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
        research: projectWorldX(NODE_WORLD_X.research, w),
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
                brandColor={parseInt(school.brandColor.replace("#", ""), 16)}
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
              {(["partnerships", "research"] as IndustryNodeKey[]).map((key) => (
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
            animate={{ opacity: industryState === "transitioning-out" ? 0 : 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.35 }}
            style={{ position: "absolute", top: 0, left: 0, right: 0 }}
          >
            {activeNode === "partnerships" && (
              <PartnershipsView school={school} onBack={handleBack} />
            )}
            {activeNode === "research" && (
              <ResearchView school={school} onBack={handleBack} />
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
