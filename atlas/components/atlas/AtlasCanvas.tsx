"use client";

import { useRef, useEffect, useCallback } from "react";
import { buildAtlasScene, DomainKey, SceneCallbacks } from "@/lib/atlasScene";

type Props = {
  onDomainClick: (domain: DomainKey) => void;
  onHoverChange?: (domain: DomainKey | null) => void;
  canvasOpacity: number;
  sceneRef: React.MutableRefObject<ReturnType<typeof buildAtlasScene> | null>;
};

export default function AtlasCanvas({
  onDomainClick,
  onHoverChange,
  canvasOpacity,
  sceneRef,
}: Props) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  const stableOnClick = useCallback(onDomainClick, []);
  const stableOnHover = useCallback(onHoverChange ?? (() => {}), []);

  useEffect(() => {
    if (!canvasRef.current) return;
    const callbacks: SceneCallbacks = {
      onDomainClick: stableOnClick,
      onHoverChange: stableOnHover,
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
