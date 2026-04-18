"use client";

import { useRef, useEffect, useState } from "react";
import { buildConvergenceScene, CONVERGENCE_LABELS } from "../lib/convergenceScene";
import type { ConvergenceResult } from "../lib/convergenceScene";

export default function ConvergenceFlowDiagram() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const sceneRef = useRef<ConvergenceResult | null>(null);
  const [labelPositions, setLabelPositions] = useState<Record<string, { x: number; y: number }>>({});

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const result = buildConvergenceScene(canvas);
    sceneRef.current = result;

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
    <div style={{ position: "relative", width: "100%", height: 600, overflow: "hidden" }}>
      <canvas ref={canvasRef} style={{ width: "100%", height: "100%", display: "block" }} />

      {CONVERGENCE_LABELS.map((label) => {
        const pos = labelPositions[label];
        if (!pos) return null;
        const isCenterForm = label === "Partnerships" || label === "Strong Workforce";
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
              color: "rgba(255,255,255,0.4)",
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
