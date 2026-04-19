"use client";

import { useRef, useEffect, useState } from "react";
import { buildConvergenceScene, CONVERGENCE_LABELS } from "../lib/convergenceScene";
import type { ConvergenceResult } from "../lib/convergenceScene";

export default function ConvergenceFlowDiagram() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const sceneRef = useRef<ConvergenceResult | null>(null);
  const [labelPositions, setLabelPositions] = useState<Record<string, { x: number; y: number }>>({});
  const [hoveredLabel, setHoveredLabel] = useState<string | null>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const result = buildConvergenceScene(canvas);
    sceneRef.current = result;
    result.onHoverChange(setHoveredLabel);

    let rafId: number;
    function updateLabels() {
      rafId = requestAnimationFrame(updateLabels);
      if (sceneRef.current) {
        setLabelPositions(sceneRef.current.getProjectedPositions());
      }
    }
    rafId = requestAnimationFrame(updateLabels);

    return () => {
      cancelAnimationFrame(rafId);
      result.cleanup();
      sceneRef.current = null;
    };
  }, []);

  return (
    <div style={{ position: "relative", width: "100%", height: 600, overflow: "hidden", animation: "page-fade-in 600ms ease-out" }}>
      <canvas ref={canvasRef} style={{ width: "100%", height: "100%", display: "block" }} />

      {CONVERGENCE_LABELS.map((label) => {
        const pos = labelPositions[label];
        if (!pos) return null;
        const isCenterForm = label === "Partnerships" || label === "Strong Workforce";
        const isHovered = hoveredLabel === label;
        const isDimmed = hoveredLabel !== null && !isHovered;
        return (
          <span
            key={label}
            style={{
              position: "absolute",
              left: `${pos.x}%`,
              top: `${pos.y + (isCenterForm ? 16 : 8)}%`,
              transform: "translate(-50%, 0)",
              fontSize: 10,
              fontWeight: 600,
              letterSpacing: "0.1em",
              textTransform: "uppercase",
              color: isHovered ? "#4fd1fd" : isDimmed ? "rgba(255,255,255,0.15)" : "rgba(255,255,255,0.4)",
              textShadow: isHovered ? "0 0 12px rgba(79,209,253,0.5)" : "none",
              transition: "color 0.2s ease, text-shadow 0.2s ease",
              pointerEvents: "none",
              whiteSpace: "nowrap",
            }}
          >
            {label}
          </span>
        );
      })}
    </div>
  );
}
