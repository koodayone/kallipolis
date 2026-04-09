/**
 * Unified scene engine for the Kallipolis atlas.
 *
 * Replaces the four duplicated scene builders (atlas, college, industry, government)
 * with a single configuration-driven engine that supports platonic forms (THREE.Group)
 * as first-class citizens alongside legacy single-geometry primitives.
 */

import * as THREE from "three";
import { Line2 } from "three/examples/jsm/lines/Line2.js";
import { LineGeometry } from "three/examples/jsm/lines/LineGeometry.js";
import { LineMaterial } from "three/examples/jsm/lines/LineMaterial.js";

// ── Types ──────────────────────────────────────────────────────────────────────

export type FormFactory = (color: number) => THREE.Group;

export type FormConfig<K extends string> = {
  key: K;
  id?: string; // unique identifier for connector resolution (defaults to key)
  factory: FormFactory;
  position: THREE.Vector3;
  rotSpeed: THREE.Vector3;
  oscillate?: { axis: "x" | "y" | "z"; center: number; amplitude: number; speed: number }; // gentle back-and-forth instead of continuous rotation
};

export type ConnectorConfig<K extends string> = {
  fromId: string; // matches FormConfig.id (or FormConfig.key if no id)
  toId: string;
  triggerKey: K; // which key's hover reveals this connector
};

export type SceneConfig<K extends string> = {
  forms: FormConfig<K>[];
  connectors?: ConnectorConfig<K>[];
  camera: { position: THREE.Vector3; fov: number };
  ambientIntensity: number;
  clearAlpha?: number; // 0 for transparent (hub scenes), 1 for opaque (main atlas)
  fog?: { density: number };
  sceneHalfWidth?: number; // for responsive camera Z on main atlas
};

export type SceneCallbacks<K extends string> = {
  onClick: (key: K) => void;
  onHoverChange: (key: K | null) => void;
  solidColor: number;
};

type FormEntry<K extends string> = {
  key: K;
  id: string;
  group: THREE.Group;
  meshes: THREE.Mesh[];
  edgeSegments: THREE.LineSegments[];
  hoverLight: THREE.PointLight;
  rotSpeed: THREE.Vector3;
  basePos: THREE.Vector3;
  targetScale: number;
  currentScale: number;
  targetEdgeOpacity: number;
  currentEdgeOpacity: number;
  targetFillOpacity: number;
  currentFillOpacity: number;
  oscillate?: { axis: "x" | "y" | "z"; center: number; amplitude: number; speed: number };
};

type ConnectorEntry<K extends string> = {
  line: Line2;
  triggerKey: K;
  targetOpacity: number;
  currentOpacity: number;
};

type ClickState<K extends string> =
  | { phase: "idle" }
  | { phase: "pulse"; elapsed: number; key: K }
  | { phase: "dissolve"; elapsed: number; key: K };

// ── Constants ──────────────────────────────────────────────────────────────────

const GOLD = 0xc9a84c;
const BG_COLOR = 0x060d1f;
const LERP_SPEED = 0.08;
const PULSE_DURATION = 0.22;
const DISSOLVE_DURATION = 0.7;
const PULSE_AMPLITUDE = 0.18;
const DISSOLVE_Z_OFFSET = 1.8;
const DISSOLVE_Z_SPEED = 0.05;

// ── Helpers ────────────────────────────────────────────────────────────────────

function lerp(a: number, b: number, t: number): number {
  return a + (b - a) * t;
}

/**
 * Add a mesh and its edge wireframe overlay to a group.
 * Exported for use by platonic form factories.
 */
export function addWithEdges(
  group: THREE.Group,
  geometry: THREE.BufferGeometry,
  material: THREE.Material,
  position?: THREE.Vector3,
  rotation?: THREE.Euler
): void {
  const mesh = new THREE.Mesh(geometry, material);
  if (position) mesh.position.copy(position);
  if (rotation) mesh.rotation.copy(rotation);
  group.add(mesh);

  const edgesGeo = new THREE.EdgesGeometry(geometry, 12);
  const edgeMat = new THREE.LineBasicMaterial({
    color: 0xffffff,
    transparent: true,
    opacity: 0.7,
  });
  const edges = new THREE.LineSegments(edgesGeo, edgeMat);
  if (position) edges.position.copy(position);
  if (rotation) edges.rotation.copy(rotation);
  group.add(edges);
}

/**
 * Create a standard MeshPhongMaterial matching the atlas design system.
 * Exported for use by platonic form factories.
 */
export function createFormMaterial(color: number): THREE.MeshPhongMaterial {
  return new THREE.MeshPhongMaterial({
    color,
    emissive: color,
    emissiveIntensity: 0.45,
    transparent: false,
    side: THREE.FrontSide,
    depthWrite: true,
  });
}

/**
 * Wrap a single BufferGeometry as a platonic form group.
 * Use for legacy primitives that haven't been replaced with platonic forms yet.
 */
export function createPrimitiveForm(geometry: THREE.BufferGeometry, color: number): THREE.Group {
  const group = new THREE.Group();
  group.name = "platonic-primitive";
  addWithEdges(group, geometry, createFormMaterial(color));
  return group;
}

// ── Engine ─────────────────────────────────────────────────────────────────────

/**
 * Build an interactive 3D scene from a configuration.
 * Handles rendering, animation, raycasting, click/hover, and connectors.
 */
export function buildScene<K extends string>(
  canvas: HTMLCanvasElement,
  config: SceneConfig<K>,
  callbacks: SceneCallbacks<K>
): {
  cleanup: () => void;
  resetScene: () => void;
  getProjectedPositions: () => Record<string, { x: number; y: number }>;
} {
  const initRect = canvas.getBoundingClientRect();
  const initW = initRect.width || canvas.clientWidth || 800;
  const initH = initRect.height || canvas.clientHeight || 600;
  const clearAlpha = config.clearAlpha ?? 0;

  // ── Renderer ──────────────────────────────────────────────────────────────
  const renderer = new THREE.WebGLRenderer({
    canvas,
    antialias: true,
    alpha: clearAlpha === 0,
  });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.setSize(initW, initH, clearAlpha === 0 ? false : undefined);
  renderer.setClearColor(clearAlpha === 0 ? 0x000000 : BG_COLOR, clearAlpha);

  // ── Scene & Camera ────────────────────────────────────────────────────────
  const scene = new THREE.Scene();
  if (config.fog) {
    scene.fog = new THREE.FogExp2(BG_COLOR, config.fog.density);
  }

  const camera = new THREE.PerspectiveCamera(
    config.camera.fov,
    initW / initH,
    0.1,
    100
  );
  camera.position.copy(config.camera.position);

  // ── Lighting ──────────────────────────────────────────────────────────────
  scene.add(new THREE.AmbientLight(0xffffff, config.ambientIntensity));

  const keyLight = new THREE.DirectionalLight(GOLD, 0.5);
  keyLight.position.set(5, 8, 4);
  scene.add(keyLight);

  const rimLight = new THREE.DirectionalLight(0x2244aa, 0.25);
  rimLight.position.set(-4, -2, -6);
  scene.add(rimLight);

  const fillLight = new THREE.DirectionalLight(0xffffff, 0.12);
  fillLight.position.set(0, 5, 8);
  scene.add(fillLight);

  const solidColor = callbacks.solidColor;

  // ── Build Forms ───────────────────────────────────────────────────────────

  function extractChildren(group: THREE.Group): { meshes: THREE.Mesh[]; edges: THREE.LineSegments[] } {
    const meshes: THREE.Mesh[] = [];
    const edges: THREE.LineSegments[] = [];
    group.traverse((child) => {
      if (child instanceof THREE.Mesh) meshes.push(child);
      else if (child instanceof THREE.LineSegments) edges.push(child);
    });
    return { meshes, edges };
  }

  const forms: FormEntry<K>[] = config.forms.map((fc) => {
    const group = fc.factory(solidColor);
    group.position.copy(fc.position);
    scene.add(group);

    const { meshes, edges } = extractChildren(group);

    // Tag all meshes for raycasting resolution
    meshes.forEach((m) => { m.userData.formKey = fc.key; });

    // Hover light at the form's position
    const hoverLight = new THREE.PointLight(solidColor, 0, 4);
    hoverLight.position.copy(fc.position);
    scene.add(hoverLight);

    return {
      key: fc.key,
      id: fc.id ?? fc.key,
      group,
      meshes,
      edgeSegments: edges,
      hoverLight,
      rotSpeed: fc.rotSpeed.clone(),
      oscillate: fc.oscillate,
      basePos: fc.position.clone(),
      targetScale: 1,
      currentScale: 1,
      targetEdgeOpacity: 0.7,
      currentEdgeOpacity: 0.7,
      targetFillOpacity: 1.0,
      currentFillOpacity: 1.0,
    };
  });

  // Dynamic mesh collection for raycasting — supports async-loaded GLB models
  function getAllMeshes(): THREE.Mesh[] {
    const meshes: THREE.Mesh[] = [];
    for (const f of forms) {
      f.group.updateMatrixWorld(true);
      f.group.traverse((child) => {
        if (child instanceof THREE.Mesh) {
          if (!child.userData.formKey) child.userData.formKey = f.key;
          meshes.push(child);
        }
      });
    }
    return meshes;
  }

  function getFormsByKey(key: K): FormEntry<K>[] {
    return forms.filter((f) => f.key === key);
  }

  // ── Connectors (optional) ─────────────────────────────────────────────────

  function makeConnector(a: THREE.Vector3, b: THREE.Vector3): Line2 {
    const geo = new LineGeometry();
    geo.setPositions([a.x, a.y, a.z, b.x, b.y, b.z]);
    const mat = new LineMaterial({
      color: GOLD,
      linewidth: 3,
      transparent: true,
      opacity: 0,
      resolution: new THREE.Vector2(initW, initH),
    });
    const line = new Line2(geo, mat);
    line.computeLineDistances();
    scene.add(line);
    return line;
  }

  const connectors: ConnectorEntry<K>[] = [];
  if (config.connectors) {
    for (const cc of config.connectors) {
      const fromForm = forms.find((f) => f.id === cc.fromId);
      const toForm = forms.find((f) => f.id === cc.toId);
      if (fromForm && toForm) {
        connectors.push({
          line: makeConnector(fromForm.basePos, toForm.basePos),
          triggerKey: cc.triggerKey,
          targetOpacity: 0.3,
          currentOpacity: 0.3,
        });
      }
    }
  }

  // ── Interaction State ─────────────────────────────────────────────────────

  let hoveredKey: K | null = null;
  let clickState: ClickState<K> = { phase: "idle" };
  let selectedKey: K | null = null;
  let isLocked = false;

  const mouse = new THREE.Vector2(-999, -999);
  const raycaster = new THREE.Raycaster();
  if (connectors.length > 0) {
    raycaster.params.Line = { threshold: 0.1 };
  }

  function handleHover(key: K | null) {
    if (hoveredKey === key) return;
    hoveredKey = key;
    callbacks.onHoverChange(key);

    forms.forEach((f) => {
      const isHovered = key !== null && f.key === key;
      f.targetEdgeOpacity = isHovered ? 1.0 : key !== null ? 0.45 : 0.7;
      f.hoverLight.intensity = isHovered ? 0.6 : 0;
      f.targetScale = isHovered ? 1.06 : 1.0;
    });

    connectors.forEach((c) => {
      c.targetOpacity = key !== null && c.triggerKey === key ? 1.0 : 0.3;
    });
  }

  function handleClick(key: K) {
    if (isLocked) return;
    isLocked = true;
    selectedKey = key;
    clickState = { phase: "pulse", elapsed: 0, key };
  }

  // ── Mouse Events ──────────────────────────────────────────────────────────

  function onMouseMove(e: MouseEvent) {
    const rect = canvas.getBoundingClientRect();
    mouse.x = ((e.clientX - rect.left) / rect.width) * 2 - 1;
    mouse.y = -((e.clientY - rect.top) / rect.height) * 2 + 1;
  }

  function onMouseClick(e: MouseEvent) {
    if (isLocked) return;
    const rect = canvas.getBoundingClientRect();
    const clickMouse = new THREE.Vector2(
      ((e.clientX - rect.left) / rect.width) * 2 - 1,
      -((e.clientY - rect.top) / rect.height) * 2 + 1
    );
    raycaster.setFromCamera(clickMouse, camera);
    const hits = raycaster.intersectObjects(getAllMeshes());
    if (hits.length > 0) {
      const formKey = (hits[0].object as THREE.Mesh).userData.formKey as K;
      if (formKey) handleClick(formKey);
    }
  }

  // ── Resize ────────────────────────────────────────────────────────────────

  const resizeObserver = new ResizeObserver((entries) => {
    const entry = entries[0];
    const w = entry.contentRect.width;
    const h = entry.contentRect.height;
    if (w === 0 || h === 0) return;
    camera.aspect = w / h;

    if (config.sceneHalfWidth) {
      const requiredZ = config.sceneHalfWidth / (Math.tan((config.camera.fov / 2) * Math.PI / 180) * (w / h));
      camera.position.z = Math.max(config.camera.position.z, Math.min(22, requiredZ));
    }

    camera.updateProjectionMatrix();
    renderer.setSize(w, h, clearAlpha === 0 ? false : undefined);

    connectors.forEach((c) => {
      (c.line.material as LineMaterial).resolution.set(w, h);
    });
  });
  resizeObserver.observe(canvas);

  canvas.addEventListener("mousemove", onMouseMove);
  canvas.addEventListener("click", onMouseClick);

  // ── Animation Loop ────────────────────────────────────────────────────────

  let rafId = 0;
  let lastTime = performance.now();
  const startTime = performance.now();
  let paused = false;

  function tick() {
    rafId = requestAnimationFrame(tick);
    if (paused) return;
    const now = performance.now();
    const delta = Math.min((now - lastTime) / 1000, 0.05);
    lastTime = now;

    // ── Hover raycasting ──
    if (!isLocked) {
      raycaster.setFromCamera(mouse, camera);
      const hits = raycaster.intersectObjects(getAllMeshes());
      const hitKey = hits.length > 0
        ? ((hits[0].object as THREE.Mesh).userData.formKey as K) ?? null
        : null;
      handleHover(hitKey);
      canvas.style.cursor = hitKey ? "pointer" : "default";
    }

    // ── Click state machine ──
    if (clickState.phase === "pulse") {
      clickState.elapsed += delta;
      const t = clickState.elapsed / PULSE_DURATION;
      const pulsed = Math.sin(Math.PI * Math.min(t, 1)) * PULSE_AMPLITUDE + 1;

      getFormsByKey(clickState.key).forEach((f) => {
        f.currentScale = pulsed;
        f.group.scale.setScalar(pulsed);
      });

      if (clickState.elapsed >= PULSE_DURATION) {
        clickState = { phase: "dissolve", elapsed: 0, key: clickState.key };

        forms.forEach((f) => {
          // Enable transparency for dissolve
          f.group.traverse((child) => {
            if (child instanceof THREE.Mesh) {
              (child.material as THREE.MeshPhongMaterial).transparent = true;
            }
          });

          if (f.key === selectedKey) {
            f.targetEdgeOpacity = 1.0;
            f.targetFillOpacity = 1.0;
            f.targetScale = 1.9;
          } else {
            f.targetEdgeOpacity = 0;
            f.targetFillOpacity = 0;
            f.targetScale = 0.7;
          }
        });

        connectors.forEach((c) => { c.targetOpacity = 0; });
      }
    } else if (clickState.phase === "dissolve") {
      clickState.elapsed += delta;

      getFormsByKey(clickState.key).forEach((f) => {
        f.group.position.z = lerp(f.group.position.z, f.basePos.z + DISSOLVE_Z_OFFSET, DISSOLVE_Z_SPEED);
      });

      if (clickState.elapsed >= DISSOLVE_DURATION) {
        callbacks.onClick(clickState.key);
        clickState = { phase: "idle" };
      }
    }

    // ── Ambient rotation & lerp ──
    forms.forEach((f) => {
      // Rotation (applied to group — all children inherit)
      if (f.oscillate) {
        const elapsed = (now - startTime) / 1000 * f.oscillate.speed;
        f.group.rotation[f.oscillate.axis] = f.oscillate.center + Math.sin(elapsed) * f.oscillate.amplitude;
      } else {
        f.group.rotation.x += f.rotSpeed.x;
        f.group.rotation.y += f.rotSpeed.y;
        f.group.rotation.z += f.rotSpeed.z;
      }

      // Scale lerp (skip if currently pulsing this form)
      const isPulsing = clickState.phase === "pulse" && clickState.key === f.key;
      if (!isPulsing) {
        f.currentScale = lerp(f.currentScale, f.targetScale, LERP_SPEED);
        f.group.scale.setScalar(f.currentScale);
      }

      // Edge opacity lerp — traverse group for dynamic mesh support
      f.currentEdgeOpacity = lerp(f.currentEdgeOpacity, f.targetEdgeOpacity, LERP_SPEED);
      f.group.traverse((child) => {
        if (child instanceof THREE.LineSegments) {
          (child.material as THREE.LineBasicMaterial).opacity = f.currentEdgeOpacity;
        }
      });

      // Fill opacity lerp — traverse group for dynamic mesh support
      f.currentFillOpacity = lerp(f.currentFillOpacity, f.targetFillOpacity, LERP_SPEED);
      f.group.traverse((child) => {
        if (child instanceof THREE.Mesh) {
          (child.material as THREE.MeshPhongMaterial).opacity = f.currentFillOpacity;
        }
      });
    });

    // ── Connector opacity lerp + shimmer ──
    connectors.forEach((c, i) => {
      c.currentOpacity = lerp(c.currentOpacity, c.targetOpacity, LERP_SPEED);
      const shimmer = c.currentOpacity > 0.01
        ? 0.7 + 0.3 * Math.sin((now / 1000) * (2 * Math.PI / 3) + i * 0.9)
        : 1;
      (c.line.material as LineMaterial).opacity = c.currentOpacity * shimmer;
    });

    renderer.render(scene, camera);
  }

  tick();

  // ── Reset ─────────────────────────────────────────────────────────────────

  function resetScene() {
    isLocked = false;
    selectedKey = null;
    hoveredKey = null;
    clickState = { phase: "idle" };
    canvas.style.cursor = "default";

    forms.forEach((f) => {
      f.targetScale = 1;
      f.targetEdgeOpacity = 0.7;
      f.targetFillOpacity = 1.0;
      f.currentFillOpacity = 1.0;

      f.group.traverse((child) => {
        if (child instanceof THREE.Mesh) {
          const m = child.material as THREE.MeshPhongMaterial;
          m.opacity = 1.0;
          m.transparent = false;
        }
      });

      f.group.position.z = f.basePos.z;
      f.hoverLight.intensity = 0;
    });

    connectors.forEach((c) => {
      c.targetOpacity = 0.3;
      c.currentOpacity = 0.3;
      (c.line.material as LineMaterial).opacity = 0.3;
    });
  }

  function setPaused(p: boolean) {
    paused = p;
    if (!p) {
      lastTime = performance.now();
    }
  }

  // ── Cleanup ───────────────────────────────────────────────────────────────

  function cleanup() {
    cancelAnimationFrame(rafId);
    canvas.removeEventListener("mousemove", onMouseMove);
    canvas.removeEventListener("click", onMouseClick);
    resizeObserver.disconnect();
    renderer.dispose();
  }

  function getProjectedPositions(): Record<string, { x: number; y: number }> {
    const positions: Record<string, { x: number; y: number }> = {};
    const canvasRect = canvas.getBoundingClientRect();
    for (const f of forms) {
      const pos = f.group.position.clone();
      pos.project(camera);
      // Convert NDC (-1 to 1) to percentage (0 to 100)
      positions[f.key] = {
        x: ((pos.x + 1) / 2) * 100,
        y: ((1 - pos.y) / 2) * 100,
      };
    }
    return positions;
  }

  return { cleanup, resetScene, getProjectedPositions, setPaused };
}
