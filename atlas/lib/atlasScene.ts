import * as THREE from "three";
import { Line2 } from "three/examples/jsm/lines/Line2.js";
import { LineGeometry } from "three/examples/jsm/lines/LineGeometry.js";
import { LineMaterial } from "three/examples/jsm/lines/LineMaterial.js";

export type DomainKey = "government" | "college" | "industry";

export type SceneCallbacks = {
  onDomainClick: (domain: DomainKey) => void;
  onHoverChange: (domain: DomainKey | null) => void;
  solidColor: number;
};

type SolidEntry = {
  domain: DomainKey;
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
  | { phase: "pulse"; elapsed: number; domain: DomainKey }
  | { phase: "dissolve"; elapsed: number; domain: DomainKey };

type ConnectorEntry = {
  line: Line2;
  triggerDomain: DomainKey;
  targetOpacity: number;
  currentOpacity: number;
};

const GOLD = 0xc9a84c;
const BG_COLOR = 0x041e54;
const LERP_SPEED = 0.08;

export function buildAtlasScene(
  canvas: HTMLCanvasElement,
  callbacks: SceneCallbacks
): {
  cleanup: () => void;
  resetScene: () => void;
} {
  // ── Renderer ──────────────────────────────────────────────────────────────
  const renderer = new THREE.WebGLRenderer({
    canvas,
    antialias: true,
    alpha: false,
  });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  // Use getBoundingClientRect to get true layout dimensions after CSS is applied
  const initRect = canvas.getBoundingClientRect();
  const initW = initRect.width || window.innerWidth;
  const initH = initRect.height || window.innerHeight;
  renderer.setSize(initW, initH);
  renderer.setClearColor(BG_COLOR, 1);

  // ── Scene & Camera ────────────────────────────────────────────────────────
  const scene = new THREE.Scene();
  scene.fog = new THREE.FogExp2(BG_COLOR, 0.03);

  const camera = new THREE.PerspectiveCamera(
    50,
    initW / initH,
    0.1,
    100
  );
  camera.position.set(0, 0.4, 9);

  // ── Lighting ──────────────────────────────────────────────────────────────
  const ambient = new THREE.AmbientLight(0xffffff, 0.08);
  scene.add(ambient);

  const keyLight = new THREE.DirectionalLight(0xc9a84c, 0.5);
  keyLight.position.set(5, 8, 4);
  scene.add(keyLight);

  const rimLight = new THREE.DirectionalLight(0x2244aa, 0.25);
  rimLight.position.set(-4, -2, -6);
  scene.add(rimLight);

  const fillLight = new THREE.DirectionalLight(0xffffff, 0.12);
  fillLight.position.set(0, 5, 8);
  scene.add(fillLight);

  const solidColor = callbacks.solidColor;

  // ── Helpers ───────────────────────────────────────────────────────────────
  function makeSolid(
    geometry: THREE.BufferGeometry,
    position: THREE.Vector3,
    rotSpeed: THREE.Vector3,
    domain: DomainKey
  ): SolidEntry {
    const fillMat = new THREE.MeshPhongMaterial({
      color: solidColor,
      emissive: solidColor,
      emissiveIntensity: 0.45,
      transparent: false,
      side: THREE.FrontSide,
      depthWrite: true,
    });
    const mesh = new THREE.Mesh(geometry, fillMat);
    mesh.position.copy(position);
    scene.add(mesh);

    const edgesGeo = new THREE.EdgesGeometry(geometry, 12);
    const edgeMat = new THREE.LineBasicMaterial({
      color: 0xffffff,
      transparent: true,
      opacity: 0.7,
    });
    const edges = new THREE.LineSegments(edgesGeo, edgeMat);
    edges.position.copy(position);
    scene.add(edges);

    const hoverLight = new THREE.PointLight(solidColor, 0, 4);
    hoverLight.position.copy(position);
    scene.add(hoverLight);

    return {
      domain,
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
    // Government — Dodecahedron (left)
    makeSolid(
      new THREE.DodecahedronGeometry(1.05, 0),
      new THREE.Vector3(-3.6, 0, 0),
      new THREE.Vector3(0.0018, 0.0025, 0.001),
      "government"
    ),
    // College — Cube (center)
    makeSolid(
      new THREE.BoxGeometry(1.5, 1.5, 1.5),
      new THREE.Vector3(0, 0, 0),
      new THREE.Vector3(0.001, 0.004, 0.002),
      "college"
    ),
    // Industry — Tetrahedra × 3 (fan to the right of cube)
    makeSolid(
      new THREE.TetrahedronGeometry(0.85, 0),
      new THREE.Vector3(3.6, 1.3, -0.4),
      new THREE.Vector3(0.003, 0.002, 0.0025),
      "industry"
    ),
    makeSolid(
      new THREE.TetrahedronGeometry(0.95, 0),
      new THREE.Vector3(4.4, 0, 0.2),
      new THREE.Vector3(0.002, 0.003, 0.002),
      "industry"
    ),
    makeSolid(
      new THREE.TetrahedronGeometry(0.85, 0),
      new THREE.Vector3(3.6, -1.3, -0.4),
      new THREE.Vector3(0.0025, 0.002, 0.003),
      "industry"
    ),
  ];

  // Connector lines — hidden by default, revealed on hover
  const cubePos = new THREE.Vector3(0, 0, 0);

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

  const connectors: ConnectorEntry[] = [];

  // Government → College (revealed on government hover)
  connectors.push({
    line: makeConnector(solids[0].basePos, cubePos),
    triggerDomain: "government",
    targetOpacity: 0,
    currentOpacity: 0,
  });

  // College → each Industry tetrahedron (revealed on industry hover)
  [solids[2], solids[3], solids[4]].forEach((s) => {
    connectors.push({
      line: makeConnector(cubePos, s.basePos),
      triggerDomain: "industry",
      targetOpacity: 0,
      currentOpacity: 0,
    });
  });

  // ── Interaction State ─────────────────────────────────────────────────────
  let hoveredDomain: DomainKey | null = null;
  let clickState: ClickState = { phase: "idle" };
  let selectedDomain: DomainKey | null = null;
  let isLocked = false; // prevent interaction during transition

  const mouse = new THREE.Vector2(-999, -999);
  const raycaster = new THREE.Raycaster();
  raycaster.params.Line = { threshold: 0.1 };

  const allMeshes = solids.map((s) => s.mesh);

  function getSolidsByDomain(domain: DomainKey) {
    return solids.filter((s) => s.domain === domain);
  }

  function handleHover(domain: DomainKey | null) {
    if (hoveredDomain === domain) return;
    hoveredDomain = domain;
    callbacks.onHoverChange(domain);

    solids.forEach((s) => {
      const isHovered = domain !== null && s.domain === domain;
      s.targetEdgeOpacity = isHovered ? 1.0 : domain !== null ? 0.45 : 0.7;
      s.hoverLight.intensity = isHovered ? 0.6 : 0;
      s.targetScale = isHovered ? 1.06 : 1.0;
    });

    connectors.forEach((c) => {
      c.targetOpacity = domain !== null && c.triggerDomain === domain ? 0.75 : 0;
    });
  }

  function handleClick(domain: DomainKey) {
    if (isLocked) return;
    isLocked = true;
    selectedDomain = domain;
    clickState = { phase: "pulse", elapsed: 0, domain };
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
      if (solid) handleClick(solid.domain);
    }
  }

  // ResizeObserver fires immediately after first paint with correct dimensions
  // and on every subsequent resize — more reliable than window.resize
  const resizeObserver = new ResizeObserver((entries) => {
    const entry = entries[0];
    const w = entry.contentRect.width;
    const h = entry.contentRect.height;
    if (w === 0 || h === 0) return;
    const aspect = w / h;
    camera.aspect = aspect;
    // Pull camera back on narrow viewports so the full scene stays visible.
    // sceneHalfWidth = ~5.5 units (rightmost solid edge); FOV = 50°.
    const sceneHalfWidth = 5.5;
    const requiredZ = sceneHalfWidth / (Math.tan((50 / 2) * Math.PI / 180) * aspect);
    camera.position.z = Math.max(9, Math.min(22, requiredZ));
    camera.updateProjectionMatrix();
    renderer.setSize(w, h);
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

  function lerp(a: number, b: number, t: number) {
    return a + (b - a) * t;
  }

  function tick() {
    rafId = requestAnimationFrame(tick);
    const now = performance.now();
    const delta = Math.min((now - lastTime) / 1000, 0.05); // cap at 50ms
    lastTime = now;

    // ── Raycasting for hover ──
    if (!isLocked) {
      raycaster.setFromCamera(mouse, camera);
      const hits = raycaster.intersectObjects(allMeshes);
      const hitSolid = hits.length > 0
        ? solids.find((s) => s.mesh === hits[0].object) ?? null
        : null;
      handleHover(hitSolid ? hitSolid.domain : null);

      // cursor
      canvas.style.cursor = hitSolid ? "pointer" : "default";
    }

    // ── Click state machine ──
    if (clickState.phase === "pulse") {
      clickState.elapsed += delta;
      const t = clickState.elapsed / 0.22;
      // Pulse: scale up then snap back
      const pulsed = Math.sin(Math.PI * Math.min(t, 1)) * 0.18 + 1;
      getSolidsByDomain(clickState.domain).forEach((s) => {
        s.currentScale = pulsed;
        s.mesh.scale.setScalar(pulsed);
        s.edges.scale.setScalar(pulsed);
      });

      if (clickState.elapsed >= 0.22) {
        // Move to dissolve phase
        clickState = { phase: "dissolve", elapsed: 0, domain: clickState.domain };
        // Set targets: fade others, scale selected
        solids.forEach((s) => {
          // Enable transparency on fill so opacity lerp takes effect during dissolve
          (s.mesh.material as THREE.MeshPhongMaterial).transparent = true;
          if (s.domain === selectedDomain) {
            s.targetEdgeOpacity = 1.0;
            s.targetFillOpacity = 1.0;
            s.targetScale = 1.9;
          } else {
            s.targetEdgeOpacity = 0;
            s.targetFillOpacity = 0;
            s.targetScale = 0.7;
          }
        });
        connectors.forEach((c) => {
          c.targetOpacity = 0;
        });
      }
    } else if (clickState.phase === "dissolve") {
      clickState.elapsed += delta;

      // Move selected solid toward camera
      getSolidsByDomain(clickState.domain).forEach((s) => {
        s.mesh.position.z = lerp(s.mesh.position.z, s.basePos.z + 1.8, 0.05);
        s.edges.position.z = s.mesh.position.z;
      });

      if (clickState.elapsed >= 0.7) {
        // Signal domain selection — canvas CSS opacity handled in React
        callbacks.onDomainClick(clickState.domain);
        clickState = { phase: "idle" };
      }
    }

    // ── Ambient rotation & lerp ──
    solids.forEach((s) => {
      // Rotation
      s.mesh.rotation.x += s.rotSpeed.x;
      s.mesh.rotation.y += s.rotSpeed.y;
      s.mesh.rotation.z += s.rotSpeed.z;
      s.edges.rotation.copy(s.mesh.rotation);

      // Scale lerp
      if (clickState.phase !== "pulse" || !solids.filter(x => x.domain === (clickState as {domain: DomainKey}).domain).includes(s)) {
        s.currentScale = lerp(s.currentScale, s.targetScale, LERP_SPEED);
        s.mesh.scale.setScalar(s.currentScale);
        s.edges.scale.setScalar(s.currentScale);
      }

      // Edge opacity lerp
      s.currentEdgeOpacity = lerp(s.currentEdgeOpacity, s.targetEdgeOpacity, LERP_SPEED);
      (s.edges.material as THREE.LineBasicMaterial).opacity = s.currentEdgeOpacity;

      // Fill opacity lerp
      s.currentFillOpacity = lerp(s.currentFillOpacity, s.targetFillOpacity, LERP_SPEED);
      (s.mesh.material as THREE.MeshPhongMaterial).opacity = s.currentFillOpacity;
    });

    // ── Connector opacity lerp + holographic shimmer ──
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

  // ── Reset (reverse transition) ────────────────────────────────────────────
  function resetScene() {
    isLocked = false;
    selectedDomain = null;
    hoveredDomain = null;
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
      // Reset z position to base
      s.mesh.position.z = s.basePos.z;
      s.edges.position.z = s.basePos.z;
      s.hoverLight.intensity = 0;
    });

    connectors.forEach((c) => {
      c.targetOpacity = 0;
      c.currentOpacity = 0;
      (c.line.material as LineMaterial).opacity = 0;
    });
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
