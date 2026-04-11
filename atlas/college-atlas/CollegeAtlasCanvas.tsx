"use client";

import { useRef, useEffect, useCallback } from "react";
import { buildAtlasScene, FormKey, SceneCallbacks } from "@/college-atlas/scene";

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

  // Capture the callbacks at mount time so the scene is built with stable
  // references. Rebuilding the Three.js scene on every parent re-render
  // would tear down and re-initialize GPU state, lose camera position,
  // and flash the canvas — all undesirable. We deliberately ignore later
  // callback identity changes; if the parent needs fresher handlers it
  // should use a ref-based pattern, which the layout already does for
  // hover state via setExternalHover.
  // eslint-disable-next-line react-hooks/exhaustive-deps
  const stableOnClick = useCallback(onFormClick, []);
  // eslint-disable-next-line react-hooks/exhaustive-deps
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
    // Scene init runs exactly once on mount. brandColor and the callbacks
    // are captured at mount time; we do not want a scene rebuild if the
    // parent re-renders with a new brand color or a new callback identity.
    // eslint-disable-next-line react-hooks/exhaustive-deps
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
