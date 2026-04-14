"use client";

import { useRef, useEffect, useState } from "react";
import { buildTwoFormsScene, FORM_LABELS } from "../lib/twoFormsScene";
import type { TwoFormsResult } from "../lib/twoFormsScene";

export default function TwoFormsDiagram() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const sceneRef = useRef<TwoFormsResult | null>(null);
  const [labelPositions, setLabelPositions] = useState<Record<string, { x: number; y: number }>>({});
  const [hoveredLabel, setHoveredLabel] = useState<string | null>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const result = buildTwoFormsScene(canvas);
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
    <div style={{ position: "relative", width: "100%", height: 500, overflow: "hidden" }}>
      <canvas ref={canvasRef} style={{ width: "100%", height: "100%", display: "block" }} />

      {FORM_LABELS.map((label) => {
        const pos = labelPositions[label];
        if (!pos) return null;
        const isHovered = hoveredLabel === label;
        const isDimmed = hoveredLabel !== null && !isHovered;
        return (
          <span
            key={label}
            onMouseEnter={() => {
              setHoveredLabel(label);
              sceneRef.current?.setExternalHover(label);
            }}
            onMouseLeave={() => {
              setHoveredLabel(null);
              sceneRef.current?.setExternalHover(null);
            }}
            style={{
              position: "absolute",
              left: `${pos.x + 22}%`,
              top: `${pos.y}%`,
              transform: "translate(0, -50%)",
              fontSize: 15,
              fontWeight: 700,
              letterSpacing: "0.12em",
              textTransform: "uppercase",
              color: isHovered ? "#a8e4fe" : isDimmed ? "rgba(255,255,255,0.2)" : "rgba(255,255,255,0.35)",
              textShadow: isHovered ? "0 0 12px rgba(79,209,253,0.5)" : "none",
              transition: "color 0.2s ease, text-shadow 0.2s ease",
              cursor: "pointer",
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
