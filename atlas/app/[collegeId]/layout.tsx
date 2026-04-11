"use client";

import { useRef, useEffect, useState, useCallback, useMemo, type ReactNode } from "react";
import { useParams, usePathname, useRouter } from "next/navigation";
import dynamic from "next/dynamic";
import { buildAtlasScene, type FormKey, FORM_URL_SLUGS } from "@/college-atlas/scene";
import { getCollegeAtlasConfig } from "@/config/collegeAtlasConfigs";
import { HomeSceneContext, type ProjectedPosition } from "@/college-atlas/homeSceneContext";

const CollegeAtlasCanvas = dynamic(
  () => import("@/college-atlas/CollegeAtlasCanvas"),
  { ssr: false },
);

export default function CollegeAtlasLayout({ children }: { children: ReactNode }) {
  const { collegeId } = useParams<{ collegeId: string }>();
  const pathname = usePathname();
  const router = useRouter();
  const config = getCollegeAtlasConfig(collegeId);

  const sceneRef = useRef<ReturnType<typeof buildAtlasScene> | null>(null);
  const [projectedPositions, setProjectedPositions] = useState<Record<string, ProjectedPosition>>({});
  const [hoveredForm, setHoveredForm] = useState<FormKey | null>(null);

  const homePath = `/${collegeId}`;
  const isHome = pathname === homePath;

  // Redirect if college not found
  useEffect(() => {
    if (!config) router.replace("/");
  }, [config, router]);

  // Pause the scene when focused on a form, unpause when back on the home scene.
  useEffect(() => {
    sceneRef.current?.setPaused(!isHome);
    if (isHome) sceneRef.current?.resetScene();
  }, [isHome]);

  // Forward React-side hover state (from 2D labels) into the scene so that
  // hovering a label brightens the matching 3D form via the scene engine's
  // hoverLight. When the scene's own raycaster sets hover, it flows back
  // through onHoverChange → setHoveredForm → this effect → setExternalHover,
  // which is a no-op because handleHover debounces on key equality.
  useEffect(() => {
    sceneRef.current?.setExternalHover?.(hoveredForm);
  }, [hoveredForm]);

  // Project the canvas's 2D label positions once the scene has built, and
  // again on window resize. The canvas is dynamically imported, so sceneRef
  // may not be populated on the first tick after navigation — keep trying
  // on requestAnimationFrame until we see non-empty positions, then stop.
  // The forms and camera are otherwise fixed, so no ongoing polling is
  // needed once the first projection succeeds.
  useEffect(() => {
    if (!isHome) return;

    let rafId = 0;
    let cancelled = false;

    const pollUntilReady = () => {
      if (cancelled) return;
      const positions = sceneRef.current?.getProjectedPositions?.();
      if (positions && Object.keys(positions).length > 0) {
        setProjectedPositions(positions);
        return; // stop polling; positions are stable from here
      }
      rafId = requestAnimationFrame(pollUntilReady);
    };

    const reproject = () => {
      const positions = sceneRef.current?.getProjectedPositions?.();
      if (positions) setProjectedPositions(positions);
    };

    rafId = requestAnimationFrame(pollUntilReady);
    window.addEventListener("resize", reproject);

    return () => {
      cancelled = true;
      cancelAnimationFrame(rafId);
      window.removeEventListener("resize", reproject);
    };
  }, [isHome]);

  const homeSceneState = useMemo(
    () => ({ projectedPositions, hoveredForm, setHoveredForm }),
    [projectedPositions, hoveredForm],
  );

  // Clicking a 3D form in the canvas navigates to that form's route.
  // This is the canvas's sole interaction pathway; labels on the home
  // page also navigate via Link clicks.
  const handleFormClick = useCallback((form: FormKey) => {
    router.push(`/${collegeId}/${FORM_URL_SLUGS[form]}`);
  }, [router, collegeId]);

  // Canvas hover feeds into the shared HomeSceneContext so the home page
  // can highlight the matching 2D label in gold. The 3D form itself is
  // still brightened by the scene engine's hoverLight independently.
  const handleHoverChange = useCallback(
    (form: FormKey | null) => setHoveredForm(form),
    [],
  );

  if (!config) return null;

  return (
    <div
      style={{
        position: "relative",
        width: "100vw",
        height: "100vh",
        background: "#060d1f",
        overflow: "hidden",
      }}
    >
      {/* Persistent Three.js canvas — fades out when focused on a form,
          stays mounted across child route transitions. */}
      <div style={{ position: "fixed", inset: 0, zIndex: 0 }}>
        <CollegeAtlasCanvas
          onFormClick={handleFormClick}
          onHoverChange={handleHoverChange}
          canvasOpacity={isHome ? 1 : 0}
          brandColor={parseInt(config.brandColorNeon.replace("#", ""), 16)}
          sceneRef={sceneRef}
        />
      </div>

      <HomeSceneContext.Provider value={homeSceneState}>
        {children}
      </HomeSceneContext.Provider>
    </div>
  );
}
