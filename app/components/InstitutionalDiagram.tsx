"use client";

import { useRef, useEffect } from "react";
import { buildInstitutionalScene } from "../lib/institutionalScene";

type LegendItem = {
  shape: "pentagon" | "square" | "triangle";
  color: string;
  label: string;
};

const legend: LegendItem[] = [
  { shape: "pentagon", color: "#b0c8de", label: "Government" },
  { shape: "square",   color: "#5aaa72", label: "College" },
  { shape: "triangle", color: "#f04f20", label: "Industry" },
];

function LegendIcon({ shape, color }: { shape: LegendItem["shape"]; color: string }) {
  return (
    <svg width="14" height="14" viewBox="0 0 12 12" style={{ flexShrink: 0 }}>
      {shape === "pentagon" && (
        <polygon points="6,1 11,4.6 9.1,10.5 2.9,10.5 1,4.6" fill={color} />
      )}
      {shape === "square" && (
        <rect x="1" y="1" width="10" height="10" fill={color} />
      )}
      {shape === "triangle" && (
        <polygon points="6,1 11,11 1,11" fill={color} />
      )}
    </svg>
  );
}

export default function InstitutionalDiagram() {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const cleanup = buildInstitutionalScene(canvas);
    return cleanup;
  }, []);

  return (
    <div style={{ position: "relative", width: "100%", height: "100%", minHeight: 300 }}>
      <canvas ref={canvasRef} style={{ width: "100%", height: "100%", display: "block" }} />

      {/* Legend */}
      <div style={{ position: "absolute", top: 16, left: 16, display: "flex", flexDirection: "column", gap: 8 }}>
        {legend.map(({ shape, color, label }) => (
          <div key={label} style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <LegendIcon shape={shape} color={color} />
            <span style={{ fontSize: 14, color: "white", opacity: 0.8 }}>{label}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
