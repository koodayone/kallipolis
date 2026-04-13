"use client";

import { useRef, useEffect, useState } from "react";
import { buildEpistemologyScene, ROW_DATA } from "../lib/epistemologyScene";
import type { EpistemologyResult } from "../lib/epistemologyScene";
import { FADE_DURATION } from "../lib/collegeRotation";

type Props = {
  activeIndex?: number;
  opacity?: number;
};

export default function EpistemologyGraph({ activeIndex = 0, opacity = 1 }: Props) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const sceneRef = useRef<EpistemologyResult | null>(null);
  const [positions, setPositions] = useState<{
    forms: Record<string, { x: number; y: number }>;
    ends: Record<string, { x: number; y: number }>;
  }>({ forms: {}, ends: {} });
  const [hoveredLabel, setHoveredLabel] = useState<string | null>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const result = buildEpistemologyScene(canvas);
    sceneRef.current = result;
    result.onHoverChange(setHoveredLabel);

    let rafId: number;
    function update() {
      rafId = requestAnimationFrame(update);
      if (sceneRef.current) {
        setPositions(sceneRef.current.getProjectedPositions());
      }
    }
    rafId = requestAnimationFrame(update);

    return () => {
      cancelAnimationFrame(rafId);
      result.cleanup();
      sceneRef.current = null;
    };
  }, []);

  return (
    <div
      style={{
        position: "relative",
        width: "100%",
        height: "100%",
        minHeight: 700,
      }}
    >
      <canvas ref={canvasRef} style={{ width: "100%", height: "100%", display: "block" }} />

      {/* Form labels (left side, below each form) */}
      {ROW_DATA.map((row) => {
        const pos = positions.forms[row.label];
        if (!pos) return null;
        const isHovered = hoveredLabel === row.label;
        const isDimmed = hoveredLabel !== null && !isHovered;
        return (
          <span
            key={`form-${row.label}`}
            style={{
              position: "absolute",
              left: `${pos.x}%`,
              top: `${pos.y + 9}%`,
              transform: "translate(-50%, 0)",
              fontSize: 10,
              fontWeight: 600,
              letterSpacing: "0.1em",
              textTransform: "uppercase",
              color: isHovered ? "#FFCC33" : isDimmed ? "rgba(255,255,255,0.15)" : "rgba(255,255,255,0.35)",
              transition: "color 0.2s ease",
              pointerEvents: "none",
              whiteSpace: "nowrap",
            }}
          >
            {row.label}
          </span>
        );
      })}

      {/* Authority logos (right side, at connector endpoints) */}
      {ROW_DATA.map((row) => {
        const pos = positions.ends[row.label];
        if (!pos) return null;
        const logos: Record<string, string> = {
          "Chancellor's Office": "/logos/chancellors_rev.png",
          "Colleges": "/logos/colleges_combined_white.png",
          "COE": "/logos/coe_logo_white.png",
          "EDD": "/logos/edd_logo_white.png",
        };
        const logo = logos[row.authority];
        if (!logo) return null;
        const isHovered = hoveredLabel === row.label;
        const isDimmed = hoveredLabel !== null && !isHovered;
        return (
          <div
            key={`auth-${row.label}`}
            style={{
              position: "absolute",
              left: `${pos.x}%`,
              top: `${pos.y}%`,
              transform: "translate(0, -50%)",
              pointerEvents: "none",
              opacity: isDimmed ? 0.3 : 1,
              transition: "opacity 0.2s ease",
            }}
          >
            <div
              style={{
                width: 200,
                height: 90,
                backgroundColor: isHovered ? "#ffffff" : "rgba(255,255,255,0.85)",
                WebkitMaskImage: `url(${logo})`,
                WebkitMaskSize: "contain",
                WebkitMaskRepeat: "no-repeat",
                WebkitMaskPosition: "center",
                maskImage: `url(${logo})`,
                maskSize: "contain",
                maskRepeat: "no-repeat",
                maskPosition: "center",
                transition: `background-color 0.2s ease`,
                filter: isHovered ? "drop-shadow(0 0 8px rgba(255,255,255,0.3))" : "drop-shadow(0 0 4px rgba(255,255,255,0.15))",
              }}
            />
          </div>
        );
      })}
    </div>
  );
}
