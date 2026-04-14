"use client";

import { useRef, useEffect, useState } from "react";
import { buildAtlasPreviewScene, FORM_LABELS } from "../lib/atlasPreviewScene";
import type { AtlasPreviewResult } from "../lib/atlasPreviewScene";
import { ROTATION_COLLEGES, FADE_DURATION } from "../lib/collegeRotation";

type Props = {
  activeIndex: number;
  opacity: number;
};

function AtlasScene({ activeIndex, opacity }: Props) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const sceneRef = useRef<AtlasPreviewResult | null>(null);
  const [labelPositions, setLabelPositions] = useState<Record<string, { x: number; y: number }>>({});
  const [hoveredLabel, setHoveredLabel] = useState<string | null>(null);

  const college = ROTATION_COLLEGES[activeIndex];

  // Update scene color when active college changes
  useEffect(() => {
    sceneRef.current?.setColor(college.neonColor);
  }, [college.neonColor]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const result = buildAtlasPreviewScene(canvas);
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
    <div style={{ borderRadius: 10, overflow: "hidden", background: "#060d1f", border: "1px solid rgba(255,255,255,0.2)" }}>
      {/* College title bar */}
      <div
        style={{
          padding: "28px 0 0",
          textAlign: "center",
          borderBottom: "1px solid rgba(255, 255, 255, 0.15)",
        }}
      >
        <h3
          style={{
            fontFamily: "var(--font-days-one)",
            fontSize: 18,
            fontWeight: 400,
            letterSpacing: "0.14em",
            textTransform: "uppercase",
            color: "rgba(255,255,255,0.9)",
            margin: "0 0 28px",
            opacity,
            transition: `opacity ${FADE_DURATION}ms ease`,
          }}
        >
          {college.name}
        </h3>
      </div>

      {/* Scene */}
      <div
        style={{
          position: "relative",
          width: "100%",
          aspectRatio: "16 / 10",
          opacity,
          transition: `opacity ${FADE_DURATION}ms ease`,
        }}
      >
        <canvas
          ref={canvasRef}
          style={{ display: "block", width: "100%", height: "100%" }}
        />

        {/* Projected labels */}
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
                top: `${pos.y + 18}%`,
                transform: "translate(-50%, 0)",
                fontSize: 11,
                fontWeight: 600,
                letterSpacing: "0.12em",
                textTransform: "uppercase",
                color: isHovered ? college.neonHex : isDimmed ? "rgba(255,255,255,0.2)" : "rgba(255,255,255,0.35)",
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
    </div>
  );
}

export default function AtlasPreview({ activeIndex, opacity }: Props) {
  const college = ROTATION_COLLEGES[activeIndex];

  return (
    <section style={{ background: "#060d1f", padding: "64px 64px" }}>
      {/* Section header */}
      <div style={{ textAlign: "center", marginBottom: 48 }}>
        <p style={{ fontSize: 13, fontWeight: 500, textTransform: "uppercase", letterSpacing: "0.15em", color: "rgba(255,255,255,0.45)", marginBottom: 16 }}>
          The College Atlas
        </p>
        <div style={{ width: 64, height: 2, background: college.neonHex, borderRadius: 1, opacity, transition: `opacity ${FADE_DURATION}ms ease`, margin: "0 auto 24px" }} />
        <h2 style={{ fontFamily: "var(--font-days-one)", fontSize: 36, fontWeight: 400, lineHeight: 1.15, letterSpacing: "-0.02em", color: "white", margin: "0 auto", maxWidth: 750 }}>
          Kallipolis unifies a workforce development model for California Community Colleges.
        </h2>
      </div>

      {/* Scene panel */}
      <div style={{ maxWidth: 720, margin: "0 auto" }}>
        <AtlasScene activeIndex={activeIndex} opacity={opacity} />
      </div>
    </section>
  );
}
