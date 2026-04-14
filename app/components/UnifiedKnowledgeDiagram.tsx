"use client";

import { useRef, useEffect, useState } from "react";
import { buildUnifiedKnowledgeScene } from "../lib/unifiedKnowledgeScene";
import type { UnifiedKnowledgeResult } from "../lib/unifiedKnowledgeScene";

type AuthorityKey = "chancellor" | "colleges" | "coe" | "edd";

const LOGOS: { key: AuthorityKey; path: string; label: string }[] = [
  { key: "chancellor", path: "/logos/chancellors_rev.png",          label: "Students" },
  { key: "colleges",   path: "/logos/colleges_combined_white.png",  label: "Courses" },
  { key: "coe",        path: "/logos/coe_logo_white.png",           label: "Occupations" },
  { key: "edd",        path: "/logos/edd_logo_white.png",           label: "Employers" },
];

type PosMap = Record<AuthorityKey, { x: number; y: number }>;

const zeroPositions: PosMap = {
  chancellor: { x: 0, y: 0 },
  colleges:   { x: 0, y: 0 },
  coe:        { x: 0, y: 0 },
  edd:        { x: 0, y: 0 },
};

export default function UnifiedKnowledgeDiagram() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const sceneRef = useRef<UnifiedKnowledgeResult | null>(null);
  const [logoPositions, setLogoPositions] = useState<PosMap>(zeroPositions);
  const [formLabelPositions, setFormLabelPositions] = useState<PosMap>(zeroPositions);
  const [cubeLabelPosition, setCubeLabelPosition] = useState<{ x: number; y: number }>({ x: 0, y: 0 });

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const result = buildUnifiedKnowledgeScene(canvas);
    sceneRef.current = result;

    let rafId: number;
    function updatePositions() {
      rafId = requestAnimationFrame(updatePositions);
      if (sceneRef.current) {
        setLogoPositions(sceneRef.current.getLogoPositions());
        setFormLabelPositions(sceneRef.current.getFormLabelPositions());
        setCubeLabelPosition(sceneRef.current.getCubeLabelPosition());
      }
    }
    rafId = requestAnimationFrame(updatePositions);

    return () => {
      cancelAnimationFrame(rafId);
      result.cleanup();
      sceneRef.current = null;
    };
  }, []);

  const labelStyle: React.CSSProperties = {
    fontSize: 12,
    fontWeight: 500,
    textTransform: "uppercase",
    letterSpacing: "0.14em",
    color: "rgba(255,255,255,0.5)",
    fontFamily: "var(--font-days-one)",
    whiteSpace: "nowrap",
    pointerEvents: "none",
  };

  return (
    <div style={{ position: "relative", width: "100%", minHeight: 880 }}>
      <canvas ref={canvasRef} style={{ width: "100%", height: "100%", display: "block", minHeight: 880 }} />

      {/* Cube label */}
      <div
        style={{
          position: "absolute",
          left: `${cubeLabelPosition.x}%`,
          top: `${cubeLabelPosition.y}%`,
          transform: "translate(-50%, -50%)",
          ...labelStyle,
          fontSize: 15,
          color: "rgba(255,255,255,0.75)",
        }}
      >
        College Atlas
      </div>

      {/* Form labels */}
      {LOGOS.map(({ key, label }) => {
        const pos = formLabelPositions[key];
        if (!pos) return null;
        return (
          <div
            key={`label-${key}`}
            style={{
              position: "absolute",
              left: `${pos.x}%`,
              top: `${pos.y}%`,
              transform: "translate(-50%, -50%)",
              ...labelStyle,
            }}
          >
            {label}
          </div>
        );
      })}

      {/* Authority logos */}
      {LOGOS.map(({ key, path }) => {
        const pos = logoPositions[key];
        if (!pos) return null;
        return (
          <div
            key={`logo-${key}`}
            style={{
              position: "absolute",
              left: `${pos.x}%`,
              top: `${pos.y}%`,
              transform: "translate(-50%, -50%)",
              width: 140,
              height: 55,
              pointerEvents: "none",
            }}
          >
            <div
              style={{
                width: "100%",
                height: "100%",
                backgroundColor: "rgba(255,255,255,0.85)",
                WebkitMaskImage: `url(${path})`,
                WebkitMaskSize: "contain",
                WebkitMaskRepeat: "no-repeat",
                WebkitMaskPosition: "center",
                maskImage: `url(${path})`,
                maskSize: "contain",
                maskRepeat: "no-repeat",
                maskPosition: "center",
                filter: "drop-shadow(0 0 4px rgba(255,255,255,0.15))",
              }}
            />
          </div>
        );
      })}
    </div>
  );
}
