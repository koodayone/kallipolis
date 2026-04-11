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

  // Project the canvas's 2D label positions once on mount (after the scene
  // has built) and again on window resize (which changes the camera aspect).
  // The forms' world positions and the camera are otherwise fixed, so there
  // is no reason to re-project every frame — that would cause a re-render
  // storm in the home page's label list.
  useEffect(() => {
    if (!isHome) return;

    let cancelled = false;
    const project = () => {
      if (cancelled) return;
      const positions = sceneRef.current?.getProjectedPositions?.();
      if (positions) setProjectedPositions(positions);
    };

    // Wait briefly for the scene to initialize after mount/navigation.
    const timeout = setTimeout(project, 150);
    window.addEventListener("resize", project);
    return () => {
      cancelled = true;
      clearTimeout(timeout);
      window.removeEventListener("resize", project);
    };
  }, [isHome]);

  const homeSceneState = useMemo(() => ({ projectedPositions }), [projectedPositions]);

  // Clicking a 3D form in the canvas navigates to that form's route.
  // This is the canvas's sole interaction pathway; labels on the home
  // page also navigate via Link clicks.
  const handleFormClick = useCallback((form: FormKey) => {
    router.push(`/${collegeId}/${FORM_URL_SLUGS[form]}`);
  }, [router, collegeId]);

  // Hover feedback on the 3D form itself (brightening via hoverLight) is
  // handled inside the scene engine without needing a React callback.
  // The gold label highlight from the pre-routing design is dropped here;
  // it can be restored later via a small context if the UX gap matters.
  const noopHoverChange = useCallback((_form: FormKey | null) => {}, []);

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
          onHoverChange={noopHoverChange}
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
