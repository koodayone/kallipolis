/**
 * Renders the partnership chainlink — the unit of action that integrates
 * the four foundational forms — as a single ambient-rotating object on
 * the home page's PartnershipsSection.
 *
 * Previously rendered both partnerships and "strong workforce" stacked
 * vertically; the latter was removed when the ontology dropped Strong
 * Workforce as a node. Strong Workforce remains the policy program the
 * partnership unit of action serves, but it is no longer a separate form.
 */

import * as THREE from "three";
import { createChainlinkForm } from "./formFactories";

// ── Scene ─────────────────────────────────────────────────────────────────────

const SOLID_COLOR = 0x4fd1fd;
const BG_COLOR = 0x060d1f;
const FORM_SCALE = 1.8;

type FormDef = {
  label: string;
  factory: (color: number) => THREE.Group;
  position: THREE.Vector3;
  rotSpeed: THREE.Vector3;
};

// Single chainlink centered in the scene. Desktop and mobile both center
// horizontally; mobile shifts the form slightly to leave room for the
// label below (HTML overlay positioning is branched in TwoFormsDiagram).
const desktopFormDefs: FormDef[] = [
  { label: "Partnerships", factory: createChainlinkForm, position: new THREE.Vector3(-2.4, -0.6, 0), rotSpeed: new THREE.Vector3(0.0018, 0.0025, 0.001) },
];

const mobileFormDefs: FormDef[] = [
  { label: "Partnerships", factory: createChainlinkForm, position: new THREE.Vector3(0, -0.4, 0), rotSpeed: new THREE.Vector3(0.0018, 0.0025, 0.001) },
];

export const FORM_LABELS = desktopFormDefs.map((f) => f.label);

const MOBILE_BREAKPOINT_PX = 768;

export type TwoFormsResult = {
  cleanup: () => void;
  getProjectedPositions: () => Record<string, { x: number; y: number }>;
  onHoverChange: (cb: (label: string | null) => void) => void;
  setExternalHover: (label: string | null) => void;
  layoutMode: "mobile" | "desktop";
};

export function buildTwoFormsScene(canvas: HTMLCanvasElement): TwoFormsResult {
  const rect = canvas.getBoundingClientRect();
  const width = rect.width || canvas.clientWidth || 800;
  const height = rect.height || canvas.clientHeight || 600;
  // Use viewport width (not canvas width) so a max-w-* container can't
  // false-trigger mobile mode on desktop.
  const layoutMode: "mobile" | "desktop" = typeof window !== "undefined" && window.innerWidth < MOBILE_BREAKPOINT_PX ? "mobile" : "desktop";
  const formDefs = layoutMode === "mobile" ? mobileFormDefs : desktopFormDefs;

  const renderer = new THREE.WebGLRenderer({ canvas, antialias: true });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.setSize(width, height, false);
  renderer.setClearColor(BG_COLOR, 1);

  const scene = new THREE.Scene();
  scene.fog = new THREE.FogExp2(BG_COLOR, 0.015);

  const camera = new THREE.PerspectiveCamera(50, width / height, 0.1, 100);
  camera.position.set(0, -1.8, 12);

  scene.add(new THREE.AmbientLight(0xffffff, 0.08));
  const keyLight = new THREE.DirectionalLight(SOLID_COLOR, 0.5);
  keyLight.position.set(5, 8, 4); scene.add(keyLight);
  scene.add(new THREE.DirectionalLight(0x2244aa, 0.25).translateX(-4).translateY(-2).translateZ(-6));
  scene.add(new THREE.DirectionalLight(0xffffff, 0.12).translateY(5).translateZ(8));

  const entries = formDefs.map((f, i) => {
    const group = f.factory(SOLID_COLOR);
    group.position.copy(f.position);
    group.scale.setScalar(FORM_SCALE);
    scene.add(group);
    group.traverse((child) => { if (child instanceof THREE.Mesh) child.userData.formIndex = i; });
    const hoverLight = new THREE.PointLight(SOLID_COLOR, 0, 6);
    hoverLight.position.copy(f.position);
    scene.add(hoverLight);
    return {
      group, rotSpeed: f.rotSpeed, basePos: f.position.clone(), hoverLight,
      targetScale: FORM_SCALE, currentScale: FORM_SCALE,
      targetEdgeOpacity: 0.7, currentEdgeOpacity: 0.7,
    };
  });

  const mouse = new THREE.Vector2(-999, -999);
  const raycaster = new THREE.Raycaster();
  let hoveredIndex: number | null = null;
  let externalHover: number | null = null;
  let hoverCallback: ((label: string | null) => void) | null = null;

  function getAllMeshes(): THREE.Mesh[] {
    const meshes: THREE.Mesh[] = [];
    for (const e of entries) e.group.traverse((c) => { if (c instanceof THREE.Mesh) meshes.push(c); });
    return meshes;
  }

  function handleHover(index: number | null) {
    if (hoveredIndex === index) return;
    hoveredIndex = index;
    hoverCallback?.(index !== null ? formDefs[index].label : null);
    entries.forEach((e, i) => {
      const isHovered = index !== null && i === index;
      e.targetEdgeOpacity = isHovered ? 1.0 : index !== null ? 0.35 : 0.7;
      e.hoverLight.intensity = isHovered ? 0.8 : 0;
      e.targetScale = isHovered ? FORM_SCALE * 1.08 : FORM_SCALE;
    });
  }

  function onMouseMove(ev: MouseEvent) {
    const r = canvas.getBoundingClientRect();
    mouse.x = ((ev.clientX - r.left) / r.width) * 2 - 1;
    mouse.y = -((ev.clientY - r.top) / r.height) * 2 + 1;
  }
  function onMouseLeave() { mouse.set(-999, -999); handleHover(null); }
  canvas.addEventListener("mousemove", onMouseMove);
  canvas.addEventListener("mouseleave", onMouseLeave);

  const resizeObserver = new ResizeObserver((obs) => {
    const e = obs[0]; const w = e.contentRect.width; const h = e.contentRect.height;
    if (w === 0 || h === 0) return;
    camera.aspect = w / h; camera.updateProjectionMatrix(); renderer.setSize(w, h, false);
  });
  resizeObserver.observe(canvas);

  let rafId = 0;
  const LERP = 0.08;

  function tick() {
    rafId = requestAnimationFrame(tick);
    raycaster.setFromCamera(mouse, camera);
    const hits = raycaster.intersectObjects(getAllMeshes());
    const hitIndex = hits.length > 0 ? (hits[0].object.userData.formIndex as number) ?? null : null;
    handleHover(externalHover ?? hitIndex);
    canvas.style.cursor = hitIndex !== null ? "pointer" : "default";

    for (const e of entries) {
      e.group.rotation.x += e.rotSpeed.x;
      e.group.rotation.y += e.rotSpeed.y;
      e.group.rotation.z += e.rotSpeed.z;
      e.currentScale += (e.targetScale - e.currentScale) * LERP;
      e.group.scale.setScalar(e.currentScale);
      e.currentEdgeOpacity += (e.targetEdgeOpacity - e.currentEdgeOpacity) * LERP;
      e.group.traverse((child) => {
        if (child instanceof THREE.LineSegments)
          (child.material as THREE.LineBasicMaterial).opacity = e.currentEdgeOpacity;
      });
    }
    renderer.render(scene, camera);
  }
  tick();

  return {
    cleanup: () => {
      cancelAnimationFrame(rafId);
      canvas.removeEventListener("mousemove", onMouseMove);
      canvas.removeEventListener("mouseleave", onMouseLeave);
      resizeObserver.disconnect(); renderer.dispose();
    },
    getProjectedPositions: () => {
      const positions: Record<string, { x: number; y: number }> = {};
      for (let i = 0; i < entries.length; i++) {
        const pos = entries[i].basePos.clone(); pos.project(camera);
        positions[formDefs[i].label] = { x: ((pos.x + 1) / 2) * 100, y: ((1 - pos.y) / 2) * 100 };
      }
      return positions;
    },
    onHoverChange: (cb: (label: string | null) => void) => { hoverCallback = cb; },
    setExternalHover: (label: string | null) => {
      externalHover = label !== null ? formDefs.findIndex((f) => f.label === label) : null;
      if (externalHover === -1) externalHover = null;
    },
    layoutMode,
  };
}
