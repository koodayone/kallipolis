"use client";

import { useRef, useEffect } from "react";
import { buildInstitutionalScene } from "@/lib/institutionalScene";

const legend = [
  { color: "#8a9bb0", label: "State Government" },
  { color: "#4a7c59", label: "College" },
  { color: "#c0450a", label: "Business" },
];

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
        {legend.map(({ color, label }) => (
          <div key={label} style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <div style={{ width: 10, height: 10, borderRadius: "50%", background: color, flexShrink: 0 }} />
            <span style={{ fontSize: 12, color: "white", opacity: 0.8 }}>{label}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
