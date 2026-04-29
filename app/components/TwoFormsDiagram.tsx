"use client";

import { useRef, useEffect } from "react";
import { buildTwoFormsScene } from "../lib/twoFormsScene";
import type { TwoFormsResult } from "../lib/twoFormsScene";

// The chainlink form sits in the PartnershipsSection on the home page.
// No HTML label overlay — the section's eyebrow ("Intelligent
// Partnerships"), its headline, and the "Explore Partnerships" badge
// below all establish that this is the partnerships node.
export default function TwoFormsDiagram() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const sceneRef = useRef<TwoFormsResult | null>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const result = buildTwoFormsScene(canvas);
    sceneRef.current = result;

    return () => {
      result.cleanup();
      sceneRef.current = null;
    };
  }, []);

  return (
    <div className="md:h-[360px] max-md:h-[280px]" style={{ position: "relative", width: "100%", overflow: "hidden" }}>
      <canvas ref={canvasRef} style={{ width: "100%", height: "100%", display: "block" }} />
    </div>
  );
}
