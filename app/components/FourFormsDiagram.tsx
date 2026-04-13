"use client";

import { useRef, useEffect, useState } from "react";
import { buildFourFormsScene, FORM_LABELS } from "../lib/fourFormsScene";
import type { FourFormsResult } from "../lib/fourFormsScene";
import { ROTATION_COLLEGES, FADE_DURATION } from "../lib/collegeRotation";

type Props = {
  activeIndex?: number;
  opacity?: number;
};

export default function FourFormsDiagram({ activeIndex = 0, opacity = 1 }: Props) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const sceneRef = useRef<FourFormsResult | null>(null);
  const [labelPositions, setLabelPositions] = useState<Record<string, { x: number; y: number }>>({});
  const [hoveredLabel, setHoveredLabel] = useState<string | null>(null);

  const college = ROTATION_COLLEGES[activeIndex];

  useEffect(() => {
    sceneRef.current?.setColor(college.neonColor);
  }, [college.neonColor]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const result = buildFourFormsScene(canvas);
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
    <div
      style={{
        position: "relative",
        width: "100%",
        height: "100%",
        minHeight: 500,
        opacity,
        transition: `opacity ${FADE_DURATION}ms ease`,
      }}
    >
      <canvas ref={canvasRef} style={{ width: "100%", height: "100%", display: "block" }} />

      {FORM_LABELS.map((label) => {
        const pos = labelPositions[label];
        if (!pos) return null;
        const isHovered = hoveredLabel === label;
        const isDimmed = hoveredLabel !== null && !isHovered;
        return (
          <span
            key={label}
            style={{
              position: "absolute",
              left: `${pos.x}%`,
              top: `${pos.y + 20}%`,
              transform: "translate(-50%, 0)",
              fontSize: 11,
              fontWeight: 600,
              letterSpacing: "0.12em",
              textTransform: "uppercase",
              color: isHovered ? "#FFCC33" : isDimmed ? "rgba(255,255,255,0.2)" : "rgba(255,255,255,0.35)",
              transition: "color 0.2s ease",
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
