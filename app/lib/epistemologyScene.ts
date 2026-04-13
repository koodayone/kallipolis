/**
 * Epistemology graph: 4 horizontal rows, each with a platonic form
 * connected by a gold cylinder to a data authority endpoint.
 *
 * Row layout (top to bottom):
 *   Students (mortarboard) ——— Chancellor's Office
 *   Courses (book) ——— Chancellor's Office
 *   Occupations (hardhat) ——— COE + EDD
 *   Employers (skyscraper) ——— EDD
 */

import * as THREE from "three";
import {
  createMortarboardForm,
  createBookForm,
  createHardhatForm,
  createSkyscraperForm,
} from "./formFactories";

// ── Scene config ──────────────────────────────────────────────────────────────

const GOLD = 0xc9a84c;
const BG_COLOR = 0x060d1f;
const FORM_SCALE = 0.55;

type RowDef = {
  label: string;
  authority: string;
  factory: (color: number) => THREE.Group;
  formX: number;
  endX: number;
  y: number;
};

// Visible area at Z=9, FOV=50: X ≈ ±2.3, Y ≈ ±4.2
// Forms at -1.5 (with ~0.5 unit geometry radius at scale 0.55 → edge at ~-2.0, safe)
// Endpoints at 1.5 (logo overlay sits outside canvas to the right via HTML)
// Rows evenly spaced across ±2.7 vertical
const rows: RowDef[] = [
  { label: "Students",    authority: "Chancellor's Office", factory: createMortarboardForm, formX: -1.5, endX: 1.5, y: 2.7 },
  { label: "Courses",     authority: "Colleges",             factory: createBookForm,        formX: -1.5, endX: 1.5, y: 0.9 },
  { label: "Occupations", authority: "COE",                  factory: createHardhatForm,     formX: -1.5, endX: 1.5, y: -0.9 },
  { label: "Employers",   authority: "EDD",                 factory: createSkyscraperForm,  formX: -1.5, endX: 1.5, y: -2.7 },
];

export type EpistemologyResult = {
  cleanup: () => void;
  getProjectedPositions: () => { forms: Record<string, { x: number; y: number }>; ends: Record<string, { x: number; y: number }> };
  setColor: (color: number) => void;
  onHoverChange: (cb: (label: string | null) => void) => void;
};

export const ROW_DATA = rows.map((r) => ({ label: r.label, authority: r.authority }));

export function buildEpistemologyScene(canvas: HTMLCanvasElement): EpistemologyResult {
  const rect = canvas.getBoundingClientRect();
  const width = rect.width || canvas.clientWidth || 800;
  const height = rect.height || canvas.clientHeight || 600;

  const renderer = new THREE.WebGLRenderer({ canvas, antialias: true });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.setSize(width, height, false);
  renderer.setClearColor(BG_COLOR, 1);

  const scene = new THREE.Scene();
  scene.fog = new THREE.FogExp2(BG_COLOR, 0.012);

  const camera = new THREE.PerspectiveCamera(50, width / height, 0.1, 100);
  camera.position.set(0, -0.4, 9);

  scene.add(new THREE.AmbientLight(0xffffff, 0.08));
  const keyLight = new THREE.DirectionalLight(GOLD, 0.5);
  keyLight.position.set(5, 8, 4); scene.add(keyLight);
  const rimLight = new THREE.DirectionalLight(0x2244aa, 0.25);
  rimLight.position.set(-4, -2, -6); scene.add(rimLight);
  const fillLight = new THREE.DirectionalLight(0xffffff, 0.12);
  fillLight.position.set(0, 5, 8); scene.add(fillLight);

  // Build rows
  // Core connector — bright, thin
  const connectorMat = new THREE.MeshPhongMaterial({
    color: GOLD, emissive: GOLD, emissiveIntensity: 0.8,
    transparent: true, opacity: 0.7,
  });
  // Outer glow halo — wider, softer
  const glowMat = new THREE.MeshPhongMaterial({
    color: GOLD, emissive: GOLD, emissiveIntensity: 0.4,
    transparent: true, opacity: 0.12,
  });
  // Junction spheres
  const junctionMat = new THREE.MeshPhongMaterial({
    color: GOLD, emissive: GOLD, emissiveIntensity: 1.0,
    transparent: true, opacity: 0.85,
  });
  const junctionGeo = new THREE.SphereGeometry(0.04, 8, 8);

  const formGroups: { group: THREE.Group; rotSpeed: THREE.Vector3; hoverLight: THREE.PointLight; targetScale: number; currentScale: number; targetEdgeOpacity: number; currentEdgeOpacity: number }[] = [];
  const connectorMeshes: THREE.Mesh[] = [];
  const glowMeshes: THREE.Mesh[] = [];
  const formPositions: THREE.Vector3[] = [];
  const endPositions: THREE.Vector3[] = [];

  for (const row of rows) {
    const formPos = new THREE.Vector3(row.formX, row.y, 0);
    const endPos = new THREE.Vector3(row.endX, row.y, 0);
    formPositions.push(formPos);
    endPositions.push(endPos);

    // Form
    const group = row.factory(GOLD);
    group.position.copy(formPos);
    group.scale.setScalar(FORM_SCALE);
    scene.add(group);
    group.traverse((child) => { if (child instanceof THREE.Mesh) child.userData.formIndex = formGroups.length; });
    const hoverLight = new THREE.PointLight(GOLD, 0, 4);
    hoverLight.position.copy(formPos);
    scene.add(hoverLight);
    formGroups.push({ group, rotSpeed: new THREE.Vector3(0.0018, 0.0025, 0.001), hoverLight, targetScale: FORM_SCALE, currentScale: FORM_SCALE, targetEdgeOpacity: 0.7, currentEdgeOpacity: 0.7 });

    const startX = row.formX + 0.9;
    const endX = row.endX - 0.3;
    const length = endX - startX;
    const midX = startX + length / 2;

    // Core cylinder
    const cylGeo = new THREE.CylinderGeometry(0.018, 0.018, length, 8);
    const cyl = new THREE.Mesh(cylGeo, connectorMat);
    cyl.position.set(midX, row.y, 0);
    cyl.rotation.z = Math.PI / 2;
    scene.add(cyl);
    connectorMeshes.push(cyl);

    // Outer glow cylinder
    const glowGeo = new THREE.CylinderGeometry(0.06, 0.06, length, 8);
    const glowCyl = new THREE.Mesh(glowGeo, glowMat);
    glowCyl.position.set(midX, row.y, 0);
    glowCyl.rotation.z = Math.PI / 2;
    scene.add(glowCyl);
    glowMeshes.push(glowCyl);

    // Junction spheres at both ends
    const jStart = new THREE.Mesh(junctionGeo, junctionMat);
    jStart.position.set(startX, row.y, 0);
    scene.add(jStart);
    const jEnd = new THREE.Mesh(junctionGeo, junctionMat);
    jEnd.position.set(endX, row.y, 0);
    scene.add(jEnd);

    // Point lights — brighter, two per connector
    const glow1 = new THREE.PointLight(GOLD, 0.3, 3);
    glow1.position.set(midX - length * 0.25, row.y, 0.6);
    scene.add(glow1);
    const glow2 = new THREE.PointLight(GOLD, 0.3, 3);
    glow2.position.set(midX + length * 0.25, row.y, 0.6);
    scene.add(glow2);
  }

  // Hover raycasting
  const mouse = new THREE.Vector2(-999, -999);
  const raycaster = new THREE.Raycaster();
  let hoveredIndex: number | null = null;
  let hoverCallback: ((label: string | null) => void) | null = null;

  function getAllMeshes(): THREE.Mesh[] {
    const meshes: THREE.Mesh[] = [];
    for (const fg of formGroups) fg.group.traverse((c) => { if (c instanceof THREE.Mesh) meshes.push(c); });
    return meshes;
  }

  function handleHover(index: number | null) {
    if (hoveredIndex === index) return;
    hoveredIndex = index;
    hoverCallback?.(index !== null ? rows[index].label : null);
    formGroups.forEach((fg, i) => {
      const isHovered = index !== null && i === index;
      fg.targetEdgeOpacity = isHovered ? 1.0 : index !== null ? 0.35 : 0.7;
      fg.hoverLight.intensity = isHovered ? 0.8 : 0;
      fg.targetScale = isHovered ? FORM_SCALE * 1.12 : FORM_SCALE;
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

  // Resize
  const resizeObserver = new ResizeObserver((obs) => {
    const e = obs[0]; const w = e.contentRect.width; const h = e.contentRect.height;
    if (w === 0 || h === 0) return;
    camera.aspect = w / h; camera.updateProjectionMatrix(); renderer.setSize(w, h, false);
  });
  resizeObserver.observe(canvas);

  // Animation
  let rafId = 0;
  const startTime = performance.now();
  const LERP = 0.08;
  function tick() {
    rafId = requestAnimationFrame(tick);
    const elapsed = (performance.now() - startTime) / 1000;

    // Hover raycasting
    raycaster.setFromCamera(mouse, camera);
    const hits = raycaster.intersectObjects(getAllMeshes());
    const hitIndex = hits.length > 0 ? (hits[0].object.userData.formIndex as number) ?? null : null;
    handleHover(hitIndex);
    canvas.style.cursor = hitIndex !== null ? "pointer" : "default";

    for (const fg of formGroups) {
      fg.group.rotation.x += fg.rotSpeed.x;
      fg.group.rotation.y += fg.rotSpeed.y;
      fg.group.rotation.z += fg.rotSpeed.z;

      // Scale lerp
      fg.currentScale += (fg.targetScale - fg.currentScale) * LERP;
      fg.group.scale.setScalar(fg.currentScale);

      // Edge opacity lerp
      fg.currentEdgeOpacity += (fg.targetEdgeOpacity - fg.currentEdgeOpacity) * LERP;
      fg.group.traverse((child) => {
        if (child instanceof THREE.LineSegments)
          (child.material as THREE.LineBasicMaterial).opacity = fg.currentEdgeOpacity;
      });
    }

    // Gentle shimmer on glow halos — each row offset for a wave effect
    glowMeshes.forEach((mesh, i) => {
      const shimmer = 0.08 + 0.06 * Math.sin(elapsed * 1.5 + i * 1.2);
      (mesh.material as THREE.MeshPhongMaterial).opacity = shimmer;
    });

    // Pulse the core connector brightness subtly
    const corePulse = 0.6 + 0.15 * Math.sin(elapsed * 2.0);
    connectorMat.opacity = corePulse;

    renderer.render(scene, camera);
  }
  tick();

  return {
    cleanup: () => {
      cancelAnimationFrame(rafId);
      canvas.removeEventListener("mousemove", onMouseMove);
      canvas.removeEventListener("mouseleave", onMouseLeave);
      resizeObserver.disconnect();
      renderer.dispose();
    },
    getProjectedPositions: () => {
      const forms: Record<string, { x: number; y: number }> = {};
      const ends: Record<string, { x: number; y: number }> = {};
      for (let i = 0; i < rows.length; i++) {
        const fp = formPositions[i].clone(); fp.project(camera);
        forms[rows[i].label] = { x: ((fp.x + 1) / 2) * 100, y: ((1 - fp.y) / 2) * 100 };
        const ep = endPositions[i].clone(); ep.project(camera);
        ends[rows[i].label] = { x: ((ep.x + 1) / 2) * 100, y: ((1 - ep.y) / 2) * 100 };
      }
      return { forms, ends };
    },
    setColor: (newColor: number) => {
      const c = new THREE.Color(newColor);
      keyLight.color.copy(c);
      connectorMat.color.copy(c);
      connectorMat.emissive.copy(c);
      for (const fg of formGroups) {
        fg.group.traverse((child) => {
          if (child instanceof THREE.Mesh) {
            const m = child.material;
            if (m instanceof THREE.MeshPhongMaterial && m.depthWrite) {
              m.color.copy(c); m.emissive.copy(c);
            }
          }
        });
      }
    },
    onHoverChange: (cb: (label: string | null) => void) => { hoverCallback = cb; },
  };
}
