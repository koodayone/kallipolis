"use client";

import { useRef, useEffect } from "react";
import type * as THREE from "three";
import { buildSingleFormScene } from "../lib/singleFormScene";

type Props = {
  factory: (color: number) => THREE.Group;
  label: string;
  color: number;
  active: boolean;
};

export default function MiniFormCell({ factory, label, color, active }: Props) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const sceneRef = useRef<{ cleanup: () => void } | null>(null);

  useEffect(() => {
    if (active && canvasRef.current && !sceneRef.current) {
      sceneRef.current = buildSingleFormScene(canvasRef.current, factory, color);
    }
    return () => {
      sceneRef.current?.cleanup();
      sceneRef.current = null;
    };
  }, [active, factory, color]);

  return (
    <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 8 }}>
      <canvas
        ref={canvasRef}
        style={{ width: "100%", height: 140, display: "block" }}
      />
      <span style={{
        fontSize: 10,
        fontWeight: 600,
        letterSpacing: "0.12em",
        textTransform: "uppercase",
        color: "rgba(255,255,255,0.4)",
      }}>
        {label}
      </span>
    </div>
  );
}
