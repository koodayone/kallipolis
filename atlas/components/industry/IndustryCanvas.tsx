"use client";

import { useRef, useEffect, useCallback } from "react";
import { buildIndustryScene, IndustryNodeKey, IndustrySceneCallbacks } from "@/lib/industryScene";

type Props = {
  onNodeClick: (node: IndustryNodeKey) => void;
  onHoverChange?: (node: IndustryNodeKey | null) => void;
  brandColor: number;
  canvasOpacity: number;
  sceneRef: React.MutableRefObject<ReturnType<typeof buildIndustryScene> | null>;
};

export default function IndustryCanvas({
  onNodeClick,
  onHoverChange,
  brandColor,
  canvasOpacity,
  sceneRef,
}: Props) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  const stableOnClick = useCallback(onNodeClick, []);
  const stableOnHover = useCallback(onHoverChange ?? (() => {}), []);

  useEffect(() => {
    if (!canvasRef.current) return;
    const callbacks: IndustrySceneCallbacks = {
      onNodeClick: stableOnClick,
      onHoverChange: stableOnHover,
      solidColor: brandColor,
    };
    sceneRef.current = buildIndustryScene(canvasRef.current, callbacks);
    return () => {
      sceneRef.current?.cleanup();
      sceneRef.current = null;
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      style={{
        display: "block",
        width: "100%",
        height: "100%",
        opacity: canvasOpacity,
        transition: "opacity 0.5s ease-out",
        pointerEvents: canvasOpacity > 0.05 ? "auto" : "none",
      }}
    />
  );
}
