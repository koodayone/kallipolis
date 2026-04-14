"use client";

import { useRef, useEffect, useState } from "react";
import type * as THREE from "three";
import { buildAuthorityRowScene } from "../lib/authorityRowScene";

const ACCENT = "#c9a84c";

type Props = {
  unitName: string;
  authorityName: string;
  logoPath?: string;
  authority: string;
  intelligence: string;
  methodology: string;
  factory: (color: number) => THREE.Group;
  demoScene?: React.ReactNode;
};

export default function AuthorityCard({
  unitName,
  authorityName,
  logoPath,
  authority,
  intelligence,
  methodology,
  factory,
  demoScene,
}: Props) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const sceneRef = useRef<ReturnType<typeof buildAuthorityRowScene> | null>(null);
  const [visible, setVisible] = useState(false);
  const [logoPos, setLogoPos] = useState<{ x: number; y: number } | null>(null);
  const [formPos, setFormPos] = useState<{ x: number; y: number } | null>(null);

  // Intersection observer
  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    const observer = new IntersectionObserver(
      ([entry]) => setVisible(entry.isIntersecting),
      { threshold: 0.1 },
    );
    observer.observe(el);
    return () => observer.disconnect();
  }, []);

  // Build scene
  useEffect(() => {
    if (visible && canvasRef.current && !sceneRef.current) {
      sceneRef.current = buildAuthorityRowScene(canvasRef.current, factory);

      // Update projected positions
      let rafId: number;
      function updatePos() {
        rafId = requestAnimationFrame(updatePos);
        if (sceneRef.current) {
          setLogoPos(sceneRef.current.getEndpointPosition());
          setFormPos(sceneRef.current.getFormPosition());
        }
      }
      rafId = requestAnimationFrame(updatePos);

      return () => cancelAnimationFrame(rafId);
    }
    if (!visible && sceneRef.current) {
      sceneRef.current.cleanup();
      sceneRef.current = null;
    }
    return () => {
      sceneRef.current?.cleanup();
      sceneRef.current = null;
    };
  }, [visible, factory]);

  const logos: Record<string, string> = {
    "/logos/chancellors_logo.png": "/logos/chancellors_rev.png",
    "/logos/coe_logo_clean.png": "/logos/coe_logo_white.png",
    "/logos/edd_logo_clean.png": "/logos/edd_logo_white.png",
  };
  const whiteLogo = logoPath ? logos[logoPath] ?? logoPath : undefined;

  return (
    <div ref={containerRef} style={{ marginBottom: 80 }}>
      {/* Scene row — form → connector → logo, with heading overlaid */}
      <div style={{ position: "relative", width: "100%", height: 340 }}>
        {/* Form name overlaid at top, tracking scene center */}
        {(
          <div style={{ position: "absolute", top: 24, left: "50%", transform: "translateX(-50%)", zIndex: 1, textAlign: "center", pointerEvents: "none" }}>
            <h2
              className="text-[24px] md:text-[30px] leading-[1.12] tracking-[0.1em] text-white"
              style={{ fontFamily: "var(--font-days-one)", fontWeight: 400, margin: 0, fontStyle: "italic", textTransform: "uppercase" }}
            >
              {unitName}
            </h2>
            <div style={{ width: 64, height: 2, background: ACCENT, borderRadius: 1, opacity: 0.9, margin: "12px auto 0" }} />
          </div>
        )}
        <canvas
          ref={canvasRef}
          style={{ width: "100%", height: "100%", display: "block" }}
        />

        {/* Logo overlay at connector endpoint */}
        {whiteLogo && logoPos && (
          <div
            style={{
              position: "absolute",
              left: `${logoPos.x}%`,
              top: `${logoPos.y}%`,
              transform: "translate(0, -50%)",
              pointerEvents: "none",
            }}
          >
            <div
              style={{
                width: 240,
                height: 90,
                backgroundColor: "rgba(255,255,255,0.85)",
                WebkitMaskImage: `url(${whiteLogo})`,
                WebkitMaskSize: "contain",
                WebkitMaskRepeat: "no-repeat",
                WebkitMaskPosition: "center",
                maskImage: `url(${whiteLogo})`,
                maskSize: "contain",
                maskRepeat: "no-repeat",
                maskPosition: "center",
              }}
            />
          </div>
        )}


        {/* Authority name text fallback (unused now that all have logos) */}
        {false && (
          <span
            style={{
              position: "absolute",
              right: "12%",
              top: "50%",
              transform: "translateY(-50%)",
              fontSize: 13,
              fontWeight: 600,
              letterSpacing: "0.06em",
              color: "rgba(255,255,255,0.5)",
              pointerEvents: "none",
              whiteSpace: "nowrap",
              fontFamily: "var(--font-days-one)",
            }}
          >
            {authorityName}
          </span>
        )}
      </div>

      {/* Two-column layout: narrative left, demo right */}
      <div style={{ margin: "24px 0 0", display: "flex", gap: 40 }}>
        {/* Left — authority name + narrative */}
        <div style={{ flex: "0 0 38%", display: "flex", flexDirection: "column", gap: 20 }}>
          <h3 style={{
            fontFamily: "var(--font-days-one)", fontWeight: 400,
            fontSize: 18, color: "rgba(255,255,255,0.9)", margin: 0,
          }}>
            {authorityName}
          </h3>

          <div>
            <span style={{ fontSize: 10, fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.1em", color: ACCENT, display: "block", marginBottom: 4 }}>
              The Authority
            </span>
            <p style={{ fontSize: 14, lineHeight: 1.65, color: "rgba(255,255,255,0.65)", margin: 0 }}>
              {authority}
            </p>
          </div>

          <div>
            <span style={{ fontSize: 10, fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.1em", color: ACCENT, display: "block", marginBottom: 4 }}>
              The Intelligence
            </span>
            <p style={{ fontSize: 14, lineHeight: 1.65, color: "rgba(255,255,255,0.65)", margin: 0 }}>
              {intelligence}
            </p>
          </div>

          <div>
            <span style={{ fontSize: 10, fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.1em", color: ACCENT, display: "block", marginBottom: 4 }}>
              The Methodology
            </span>
            <p style={{ fontSize: 14, lineHeight: 1.65, color: "rgba(255,255,255,0.65)", margin: 0 }}>
              {methodology}
            </p>
          </div>
        </div>

        {/* Right — demo scene */}
        {demoScene && (
          <div style={{
            flex: 1,
            background: "rgba(255,255,255,0.04)",
            border: "1px solid rgba(255,255,255,0.08)",
            borderRadius: 8,
            overflow: "hidden",
            padding: 16,
            alignSelf: "flex-start",
          }}>
            {demoScene}
          </div>
        )}
      </div>
    </div>
  );
}
