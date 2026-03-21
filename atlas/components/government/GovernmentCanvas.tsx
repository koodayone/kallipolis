"use client";

import { useRef, useEffect, useCallback } from "react";
import { buildGovernmentScene, GovReportKey, GovSceneCallbacks } from "@/lib/governmentScene";

type Props = {
  onReportClick: (report: GovReportKey) => void;
  onHoverChange?: (node: GovReportKey | null) => void;
  brandColor: number;
  canvasOpacity: number;
  sceneRef: React.MutableRefObject<ReturnType<typeof buildGovernmentScene> | null>;
};

export default function GovernmentCanvas({
  onReportClick,
  onHoverChange,
  brandColor,
  canvasOpacity,
  sceneRef,
}: Props) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  const stableOnClick = useCallback(onReportClick, []);
  const stableOnHover = useCallback(onHoverChange ?? (() => {}), []);

  useEffect(() => {
    if (!canvasRef.current) return;
    const callbacks: GovSceneCallbacks = {
      onReportClick: stableOnClick,
      onHoverChange: stableOnHover,
      solidColor: brandColor,
    };
    sceneRef.current = buildGovernmentScene(canvasRef.current, callbacks);
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
