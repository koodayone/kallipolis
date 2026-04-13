/**
 * Simplified rendering of the six College Atlas forms for the landing page.
 *
 * Renders the same platonic geometries used in the atlas — mortarboard,
 * book, chainlink, hardhat, skyscraper, dumbbell — in a 2x3 grid with
 * ambient rotation. No interactivity, no raycasting, no click handling.
 * Pure display.
 */

import * as THREE from "three";
import {
  createMortarboardForm,
  createBookForm,
  createChainlinkForm,
  createHardhatForm,
  createSkyscraperForm,
  createDumbbellForm,
} from "./formFactories";

// ── Scene configuration ───────────────────────────────────────────────────────

const SOLID_COLOR = 0xf0425e;
const BG_COLOR = 0x060d1f;

type FormDef = {
  label: string;
  factory: (color: number) => THREE.Group;
  position: THREE.Vector3;
  rotSpeed: THREE.Vector3;
};

const FORM_SCALE = 2.1;

const formDefs: FormDef[] = [
  // Top row
  { label: "Students",         factory: createMortarboardForm, position: new THREE.Vector3(-9.0, 4.2, 0),  rotSpeed: new THREE.Vector3(0.0018, 0.0025, 0.001) },
  { label: "Partnerships",     factory: createChainlinkForm,   position: new THREE.Vector3(0, 4.2, 0),     rotSpeed: new THREE.Vector3(0.0018, 0.0025, 0.001) },
  { label: "Employers",        factory: createSkyscraperForm,  position: new THREE.Vector3(9.0, 4.2, 0),   rotSpeed: new THREE.Vector3(0.0015, 0.002, 0.0018) },
  // Bottom row
  { label: "Courses",          factory: createBookForm,        position: new THREE.Vector3(-9.0, -3.4, 0), rotSpeed: new THREE.Vector3(0.0015, 0.002, 0.001) },
  { label: "Strong Workforce", factory: createDumbbellForm,    position: new THREE.Vector3(0, -3.4, 0),    rotSpeed: new THREE.Vector3(0.0018, 0.0025, 0.001) },
  { label: "Occupations",      factory: createHardhatForm,     position: new THREE.Vector3(9.0, -3.4, 0),  rotSpeed: new THREE.Vector3(0.002, 0.0028, 0.0012) },
];

// ── Build scene ───────────────────────────────────────────────────────────────

export type AtlasPreviewResult = {
  cleanup: () => void;
  getProjectedPositions: () => Record<string, { x: number; y: number }>;
  onHoverChange: (cb: (label: string | null) => void) => void;
  setColor: (color: number) => void;
};

export const FORM_LABELS = formDefs.map((f) => f.label);

export function buildAtlasPreviewScene(canvas: HTMLCanvasElement): AtlasPreviewResult {
  const rect = canvas.getBoundingClientRect();
  const width = rect.width || canvas.clientWidth || 800;
  const height = rect.height || canvas.clientHeight || 600;

  const renderer = new THREE.WebGLRenderer({ canvas, antialias: true });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.setSize(width, height, false);
  renderer.setClearColor(BG_COLOR, 1);

  const scene = new THREE.Scene();
  scene.fog = new THREE.FogExp2(BG_COLOR, 0.015);

  const fov = 50;
  const camera = new THREE.PerspectiveCamera(fov, width / height, 0.1, 100);
  camera.position.set(0, -0.15, 21);

  // Lighting — matches atlas
  scene.add(new THREE.AmbientLight(0xffffff, 0.08));
  const keyLight = new THREE.DirectionalLight(SOLID_COLOR, 0.5);
  keyLight.position.set(5, 8, 4);
  scene.add(keyLight);
  const rimLight = new THREE.DirectionalLight(0x2244aa, 0.25);
  rimLight.position.set(-4, -2, -6);
  scene.add(rimLight);
  const fillLight = new THREE.DirectionalLight(0xffffff, 0.12);
  fillLight.position.set(0, 5, 8);
  scene.add(fillLight);

  // Build forms
  const entries = formDefs.map((f, i) => {
    const group = f.factory(SOLID_COLOR);
    group.position.copy(f.position);
    group.scale.setScalar(FORM_SCALE);
    scene.add(group);

    // Tag meshes for raycasting
    group.traverse((child) => {
      if (child instanceof THREE.Mesh) {
        child.userData.formIndex = i;
      }
    });

    // Hover point light
    const hoverLight = new THREE.PointLight(SOLID_COLOR, 0, 6);
    hoverLight.position.copy(f.position);
    scene.add(hoverLight);

    return {
      group,
      rotSpeed: f.rotSpeed,
      basePos: f.position.clone(),
      hoverLight,
      targetScale: FORM_SCALE,
      currentScale: FORM_SCALE,
      targetEdgeOpacity: 0.7,
      currentEdgeOpacity: 0.7,
    };
  });

  // Raycasting
  const mouse = new THREE.Vector2(-999, -999);
  const raycaster = new THREE.Raycaster();
  let hoveredIndex: number | null = null;
  let hoverCallback: ((label: string | null) => void) | null = null;

  function getAllMeshes(): THREE.Mesh[] {
    const meshes: THREE.Mesh[] = [];
    for (const e of entries) {
      e.group.traverse((child) => {
        if (child instanceof THREE.Mesh) meshes.push(child);
      });
    }
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

  function onMouseMove(e: MouseEvent) {
    const rect = canvas.getBoundingClientRect();
    mouse.x = ((e.clientX - rect.left) / rect.width) * 2 - 1;
    mouse.y = -((e.clientY - rect.top) / rect.height) * 2 + 1;
  }

  function onMouseLeave() {
    mouse.set(-999, -999);
    handleHover(null);
  }

  canvas.addEventListener("mousemove", onMouseMove);
  canvas.addEventListener("mouseleave", onMouseLeave);

  // Resize
  const resizeObserver = new ResizeObserver((obs) => {
    const entry = obs[0];
    const w = entry.contentRect.width;
    const h = entry.contentRect.height;
    if (w === 0 || h === 0) return;
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
    renderer.setSize(w, h, false);
  });
  resizeObserver.observe(canvas);

  // Animation
  let rafId = 0;
  const LERP = 0.08;

  function tick() {
    rafId = requestAnimationFrame(tick);

    // Hover raycasting
    raycaster.setFromCamera(mouse, camera);
    const hits = raycaster.intersectObjects(getAllMeshes());
    const hitIndex = hits.length > 0 ? (hits[0].object.userData.formIndex as number) ?? null : null;
    handleHover(hitIndex);
    canvas.style.cursor = hitIndex !== null ? "pointer" : "default";

    for (const e of entries) {
      // Rotation
      e.group.rotation.x += e.rotSpeed.x;
      e.group.rotation.y += e.rotSpeed.y;
      e.group.rotation.z += e.rotSpeed.z;

      // Scale lerp
      e.currentScale += (e.targetScale - e.currentScale) * LERP;
      e.group.scale.setScalar(e.currentScale);

      // Edge opacity lerp
      e.currentEdgeOpacity += (e.targetEdgeOpacity - e.currentEdgeOpacity) * LERP;
      e.group.traverse((child) => {
        if (child instanceof THREE.LineSegments) {
          (child.material as THREE.LineBasicMaterial).opacity = e.currentEdgeOpacity;
        }
      });
    }

    renderer.render(scene, camera);
  }
  tick();

  function getProjectedPositions(): Record<string, { x: number; y: number }> {
    const positions: Record<string, { x: number; y: number }> = {};
    for (let i = 0; i < entries.length; i++) {
      const pos = entries[i].basePos.clone();
      pos.project(camera);
      positions[formDefs[i].label] = {
        x: ((pos.x + 1) / 2) * 100,
        y: ((1 - pos.y) / 2) * 100,
      };
    }
    return positions;
  }

  function setColor(newColor: number) {
    const threeColor = new THREE.Color(newColor);
    keyLight.color.copy(threeColor);
    for (const e of entries) {
      e.hoverLight.color.copy(threeColor);
      e.group.traverse((child) => {
        if (child instanceof THREE.Mesh) {
          const mat = child.material;
          if (mat instanceof THREE.MeshPhongMaterial && mat.depthWrite) {
            mat.color.copy(threeColor);
            mat.emissive.copy(threeColor);
          }
        }
      });
    }
  }

  return {
    cleanup: () => {
      cancelAnimationFrame(rafId);
      canvas.removeEventListener("mousemove", onMouseMove);
      canvas.removeEventListener("mouseleave", onMouseLeave);
      resizeObserver.disconnect();
      renderer.dispose();
    },
    getProjectedPositions,
    onHoverChange: (cb: (label: string | null) => void) => { hoverCallback = cb; },
    setColor,
  };
}
