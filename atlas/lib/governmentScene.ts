import * as THREE from "three";
import { Line2 } from "three/examples/jsm/lines/Line2.js";
import { LineGeometry } from "three/examples/jsm/lines/LineGeometry.js";
import { LineMaterial } from "three/examples/jsm/lines/LineMaterial.js";

export type GovReportKey = "strong_workforce" | "perkins_v";

export type GovSceneCallbacks = {
  onReportClick: (report: GovReportKey) => void;
  onHoverChange: (report: GovReportKey | null) => void;
};

type SolidEntry = {
  report: GovReportKey;
  mesh: THREE.Mesh;
  edges: THREE.LineSegments;
  hoverLight: THREE.PointLight;
  rotSpeed: THREE.Vector3;
  basePos: THREE.Vector3;
  targetScale: number;
  currentScale: number;
  targetEdgeOpacity: number;
  currentEdgeOpacity: number;
  targetFillOpacity: number;
  currentFillOpacity: number;
};

type ClickState =
  | { phase: "idle" }
  | { phase: "pulse"; elapsed: number; report: GovReportKey }
  | { phase: "dissolve"; elapsed: number; report: GovReportKey };

const GOLD = 0xc9a84c;
const LERP_SPEED = 0.08;

const REPORT_COLOR: Record<GovReportKey, number> = {
  strong_workforce: 0xc47a8a, // warm rose — Foothill maroon family
  perkins_v:        0x7a9ab8, // steel blue — federal, cool
};

export function buildGovernmentScene(
  canvas: HTMLCanvasElement,
  callbacks: GovSceneCallbacks
): {
  cleanup: () => void;
  resetScene: () => void;
} {
  const initRect = canvas.getBoundingClientRect();
  const initW = initRect.width || 800;
  const initH = initRect.height || 360;

  // ── Renderer ──────────────────────────────────────────────────────────────
  const renderer = new THREE.WebGLRenderer({
    canvas,
    antialias: true,
    alpha: true, // transparent — page bg shows through
  });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.setSize(initW, initH);
  renderer.setClearColor(0x000000, 0);

  // ── Scene & Camera ────────────────────────────────────────────────────────
  const scene = new THREE.Scene();

  const camera = new THREE.PerspectiveCamera(50, initW / initH, 0.1, 100);
  camera.position.set(0, 0, 5.5);

  // ── Lighting ──────────────────────────────────────────────────────────────
  scene.add(new THREE.AmbientLight(0xffffff, 0.08));

  const keyLight = new THREE.DirectionalLight(0xc9a84c, 0.5);
  keyLight.position.set(5, 8, 4);
  scene.add(keyLight);

  const rimLight = new THREE.DirectionalLight(0x2244aa, 0.25);
  rimLight.position.set(-4, -2, -6);
  scene.add(rimLight);

  scene.add(new THREE.DirectionalLight(0xffffff, 0.12)).position.set(0, 5, 8);

  // ── Helpers ───────────────────────────────────────────────────────────────
  function makeSolid(
    geometry: THREE.BufferGeometry,
    position: THREE.Vector3,
    rotSpeed: THREE.Vector3,
    report: GovReportKey
  ): SolidEntry {
    const color = REPORT_COLOR[report];

    const fillMat = new THREE.MeshPhongMaterial({
      color,
      emissive: color,
      emissiveIntensity: 0.15,
      transparent: false,
      side: THREE.FrontSide,
      depthWrite: true,
    });
    const mesh = new THREE.Mesh(geometry, fillMat);
    mesh.position.copy(position);
    scene.add(mesh);

    const edgesGeo = new THREE.EdgesGeometry(geometry, 12);
    const edgeMat = new THREE.LineBasicMaterial({
      color,
      transparent: true,
      opacity: 0.7,
    });
    const edges = new THREE.LineSegments(edgesGeo, edgeMat);
    edges.position.copy(position);
    scene.add(edges);

    const hoverLight = new THREE.PointLight(color, 0, 4);
    hoverLight.position.copy(position);
    scene.add(hoverLight);

    return {
      report,
      mesh,
      edges,
      hoverLight,
      rotSpeed,
      basePos: position.clone(),
      targetScale: 1,
      currentScale: 1,
      targetEdgeOpacity: 0.7,
      currentEdgeOpacity: 0.7,
      targetFillOpacity: 1.0,
      currentFillOpacity: 1.0,
    };
  }

  // ── Solids ────────────────────────────────────────────────────────────────
  const solids: SolidEntry[] = [
    // Strong Workforce — Icosahedron (left)
    makeSolid(
      new THREE.IcosahedronGeometry(0.85, 0),
      new THREE.Vector3(-1.8, 0, 0),
      new THREE.Vector3(0.0018, 0.0025, 0.001),
      "strong_workforce"
    ),
    // Perkins V — Octahedron (right)
    makeSolid(
      new THREE.OctahedronGeometry(0.9, 0),
      new THREE.Vector3(1.8, 0, 0),
      new THREE.Vector3(0.001, 0.003, 0.002),
      "perkins_v"
    ),
  ];

  // ── Connector ─────────────────────────────────────────────────────────────
  const connectorGeo = new LineGeometry();
  connectorGeo.setPositions([
    solids[0].basePos.x, solids[0].basePos.y, solids[0].basePos.z,
    solids[1].basePos.x, solids[1].basePos.y, solids[1].basePos.z,
  ]);
  const connectorMat = new LineMaterial({
    color: GOLD,
    linewidth: 2,
    transparent: true,
    opacity: 0,
    resolution: new THREE.Vector2(initW, initH),
  });
  const connector = new Line2(connectorGeo, connectorMat);
  connector.computeLineDistances();
  scene.add(connector);

  let connectorTargetOpacity = 0;
  let connectorCurrentOpacity = 0;

  // ── Interaction State ─────────────────────────────────────────────────────
  let hoveredReport: GovReportKey | null = null;
  let clickState: ClickState = { phase: "idle" };
  let selectedReport: GovReportKey | null = null;
  let isLocked = false;

  const mouse = new THREE.Vector2(-999, -999);
  const raycaster = new THREE.Raycaster();
  const allMeshes = solids.map((s) => s.mesh);

  function handleHover(report: GovReportKey | null) {
    if (hoveredReport === report) return;
    hoveredReport = report;
    callbacks.onHoverChange(report);

    solids.forEach((s) => {
      const isHovered = report !== null && s.report === report;
      s.targetEdgeOpacity = isHovered ? 1.0 : report !== null ? 0.45 : 0.7;
      s.hoverLight.intensity = isHovered ? 0.6 : 0;
      s.targetScale = isHovered ? 1.06 : 1.0;
    });

    connectorTargetOpacity = report !== null ? 0.75 : 0;
  }

  function handleClick(report: GovReportKey) {
    if (isLocked) return;
    isLocked = true;
    selectedReport = report;
    clickState = { phase: "pulse", elapsed: 0, report };
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
    const hits = raycaster.intersectObjects(allMeshes);
    if (hits.length > 0) {
      const solid = solids.find((s) => s.mesh === hits[0].object);
      if (solid) handleClick(solid.report);
    }
  }

  // ── ResizeObserver ────────────────────────────────────────────────────────
  const resizeObserver = new ResizeObserver((entries) => {
    const entry = entries[0];
    const w = entry.contentRect.width;
    const h = entry.contentRect.height;
    if (w === 0 || h === 0) return;
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
    renderer.setSize(w, h);
    connectorMat.resolution.set(w, h);
  });
  resizeObserver.observe(canvas);

  canvas.addEventListener("mousemove", onMouseMove);
  canvas.addEventListener("click", onMouseClick);

  // ── Animation Loop ────────────────────────────────────────────────────────
  let rafId = 0;
  let lastTime = performance.now();

  function lerp(a: number, b: number, t: number) {
    return a + (b - a) * t;
  }

  function tick() {
    rafId = requestAnimationFrame(tick);
    const now = performance.now();
    const delta = Math.min((now - lastTime) / 1000, 0.05);
    lastTime = now;

    // Hover raycasting
    if (!isLocked) {
      raycaster.setFromCamera(mouse, camera);
      const hits = raycaster.intersectObjects(allMeshes);
      const hitSolid = hits.length > 0
        ? solids.find((s) => s.mesh === hits[0].object) ?? null
        : null;
      handleHover(hitSolid ? hitSolid.report : null);
      canvas.style.cursor = hitSolid ? "pointer" : "default";
    }

    // Click state machine
    if (clickState.phase === "pulse") {
      clickState.elapsed += delta;
      const t = clickState.elapsed / 0.22;
      const pulsed = Math.sin(Math.PI * Math.min(t, 1)) * 0.18 + 1;
      const pulsingSolid = solids.find((s) => s.report === (clickState as { report: GovReportKey }).report);
      if (pulsingSolid) {
        pulsingSolid.currentScale = pulsed;
        pulsingSolid.mesh.scale.setScalar(pulsed);
        pulsingSolid.edges.scale.setScalar(pulsed);
      }

      if (clickState.elapsed >= 0.22) {
        clickState = { phase: "dissolve", elapsed: 0, report: clickState.report };
        solids.forEach((s) => {
          (s.mesh.material as THREE.MeshPhongMaterial).transparent = true;
          if (s.report === selectedReport) {
            s.targetEdgeOpacity = 1.0;
            s.targetFillOpacity = 1.0;
            s.targetScale = 1.9;
          } else {
            s.targetEdgeOpacity = 0;
            s.targetFillOpacity = 0;
            s.targetScale = 0.7;
          }
        });
        connectorTargetOpacity = 0;
      }
    } else if (clickState.phase === "dissolve") {
      clickState.elapsed += delta;

      const selectedSolid = solids.find((s) => s.report === (clickState as { report: GovReportKey }).report);
      if (selectedSolid) {
        selectedSolid.mesh.position.z = lerp(selectedSolid.mesh.position.z, selectedSolid.basePos.z + 1.8, 0.05);
        selectedSolid.edges.position.z = selectedSolid.mesh.position.z;
      }

      if (clickState.elapsed >= 0.7) {
        callbacks.onReportClick((clickState as { report: GovReportKey }).report);
        clickState = { phase: "idle" };
      }
    }

    // Ambient rotation & lerp
    solids.forEach((s) => {
      s.mesh.rotation.x += s.rotSpeed.x;
      s.mesh.rotation.y += s.rotSpeed.y;
      s.mesh.rotation.z += s.rotSpeed.z;
      s.edges.rotation.copy(s.mesh.rotation);

      if (clickState.phase !== "pulse" || (clickState as { report: GovReportKey }).report !== s.report) {
        s.currentScale = lerp(s.currentScale, s.targetScale, LERP_SPEED);
        s.mesh.scale.setScalar(s.currentScale);
        s.edges.scale.setScalar(s.currentScale);
      }

      s.currentEdgeOpacity = lerp(s.currentEdgeOpacity, s.targetEdgeOpacity, LERP_SPEED);
      (s.edges.material as THREE.LineBasicMaterial).opacity = s.currentEdgeOpacity;

      s.currentFillOpacity = lerp(s.currentFillOpacity, s.targetFillOpacity, LERP_SPEED);
      (s.mesh.material as THREE.MeshPhongMaterial).opacity = s.currentFillOpacity;
    });

    // Connector shimmer
    connectorCurrentOpacity = lerp(connectorCurrentOpacity, connectorTargetOpacity, LERP_SPEED);
    const shimmer = connectorCurrentOpacity > 0.01
      ? 0.7 + 0.3 * Math.sin((now / 1000) * (2 * Math.PI / 3))
      : 1;
    connectorMat.opacity = connectorCurrentOpacity * shimmer;

    renderer.render(scene, camera);
  }

  tick();

  // ── Reset ─────────────────────────────────────────────────────────────────
  function resetScene() {
    isLocked = false;
    selectedReport = null;
    hoveredReport = null;
    clickState = { phase: "idle" };
    canvas.style.cursor = "default";

    solids.forEach((s) => {
      s.targetScale = 1;
      s.targetEdgeOpacity = 0.7;
      s.targetFillOpacity = 1.0;
      s.currentFillOpacity = 1.0;
      const mat = s.mesh.material as THREE.MeshPhongMaterial;
      mat.opacity = 1.0;
      mat.transparent = false;
      s.mesh.position.z = s.basePos.z;
      s.edges.position.z = s.basePos.z;
      s.hoverLight.intensity = 0;
    });

    connectorTargetOpacity = 0;
    connectorCurrentOpacity = 0;
    connectorMat.opacity = 0;
  }

  // ── Cleanup ───────────────────────────────────────────────────────────────
  function cleanup() {
    cancelAnimationFrame(rafId);
    canvas.removeEventListener("mousemove", onMouseMove);
    canvas.removeEventListener("click", onMouseClick);
    resizeObserver.disconnect();
    renderer.dispose();
  }

  return { cleanup, resetScene };
}
