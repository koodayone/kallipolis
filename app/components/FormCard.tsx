"use client";

import { useRef, useEffect, useState } from "react";
import type * as THREE from "three";
import { buildSingleFormScene } from "../lib/singleFormScene";

type Props = {
  factory: (color: number) => THREE.Group;
  label: string;
  source: string;
  description: string;
};

export default function FormCard({ factory, label, source, description }: Props) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const sceneRef = useRef<{ cleanup: () => void } | null>(null);
  const [visible, setVisible] = useState(false);

  // IntersectionObserver — only init WebGL when visible
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

  // Build / tear down scene based on visibility
  useEffect(() => {
    if (visible && canvasRef.current && !sceneRef.current) {
      sceneRef.current = buildSingleFormScene(canvasRef.current, factory);
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

  return (
    <div
      ref={containerRef}
      style={{
        background: "rgba(255,255,255,0.03)",
        border: "1px solid rgba(255,255,255,0.08)",
        borderRadius: 10,
        padding: "24px 20px 20px",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        gap: 12,
      }}
    >
      <canvas
        ref={canvasRef}
        style={{ width: "100%", height: 180, display: "block" }}
      />
      <h3
        style={{
          fontFamily: "var(--font-days-one)",
          fontWeight: 400,
          fontSize: 18,
          color: "rgba(255,255,255,0.9)",
          margin: 0,
          textAlign: "center",
        }}
      >
        {label}
      </h3>
      <span
        style={{
          fontSize: 10,
          fontWeight: 600,
          textTransform: "uppercase",
          letterSpacing: "0.12em",
          color: "#f0425e",
        }}
      >
        {source}
      </span>
      <p
        style={{
          fontSize: 14,
          lineHeight: 1.6,
          color: "rgba(255,255,255,0.55)",
          margin: 0,
          textAlign: "center",
        }}
      >
        {description}
      </p>
    </div>
  );
}
