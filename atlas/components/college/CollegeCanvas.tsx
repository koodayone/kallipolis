"use client";

import { useRef, useEffect, useCallback } from "react";
import { buildCollegeScene, CollegeNodeKey, CollegeSceneCallbacks } from "@/lib/collegeScene";

type Props = {
  onNodeClick: (node: CollegeNodeKey) => void;
  brandColor: number;
  canvasOpacity: number;
  sceneRef: React.MutableRefObject<ReturnType<typeof buildCollegeScene> | null>;
};

export default function CollegeCanvas({
  onNodeClick,
  brandColor,
  canvasOpacity,
  sceneRef,
}: Props) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  const stableOnClick = useCallback(onNodeClick, []);

  useEffect(() => {
    if (!canvasRef.current) return;
    const callbacks: CollegeSceneCallbacks = {
      onNodeClick: stableOnClick,
      onHoverChange: () => {},
      solidColor: brandColor,
    };
    sceneRef.current = buildCollegeScene(canvasRef.current, callbacks);
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
