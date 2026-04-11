"use client";

import { useRef, useEffect, useCallback } from "react";
import { buildAtlasScene, FormKey, SceneCallbacks } from "@/lib/atlasScene";

type Props = {
  onFormClick: (form: FormKey) => void;
  onHoverChange?: (form: FormKey | null) => void;
  brandColor: number;
  canvasOpacity: number;
  sceneRef: React.MutableRefObject<ReturnType<typeof buildAtlasScene> | null>;
};

export default function CollegeAtlasCanvas({
  onFormClick,
  onHoverChange,
  brandColor,
  canvasOpacity,
  sceneRef,
}: Props) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  const stableOnClick = useCallback(onFormClick, []);
  const stableOnHover = useCallback(onHoverChange ?? (() => {}), []);

  useEffect(() => {
    if (!canvasRef.current) return;
    const callbacks: SceneCallbacks = {
      onFormClick: stableOnClick,
      onHoverChange: stableOnHover,
      solidColor: brandColor,
    };
    sceneRef.current = buildAtlasScene(canvasRef.current, callbacks);
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
