import * as THREE from "three";

export type DomainKey = "government" | "college" | "industry";

export type SceneCallbacks = {
  onDomainClick: (domain: DomainKey) => void;
  onHoverChange: (domain: DomainKey | null) => void;
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

const GOLD = 0xc9a84c;
const BG_COLOR = 0x0a0a0f;
const LERP_SPEED = 0.08;

const DOMAIN_COLOR: Record<string, number> = {
  government: 0xb0c8de, // steel blue-grey
  college:    0x5aaa72, // green
  industry:   0xf04f20, // red-orange
};

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

  // ── Helpers ───────────────────────────────────────────────────────────────
  function makeSolid(
    geometry: THREE.BufferGeometry,
    position: THREE.Vector3,
    rotSpeed: THREE.Vector3,
    domain: DomainKey
  ): SolidEntry {
    // Dark inner fill mesh
    const fillMat = new THREE.MeshPhongMaterial({
      color: 0x0d0d14,
      emissive: 0x0a0a0f,
      transparent: true,
      opacity: 0.85,
      side: THREE.FrontSide,
      depthWrite: true,
    });
    const mesh = new THREE.Mesh(geometry, fillMat);
    mesh.position.copy(position);
    scene.add(mesh);

    // Domain-colored edge wireframe
    const edgesGeo = new THREE.EdgesGeometry(geometry, 12);
    const edgeMat = new THREE.LineBasicMaterial({
      color: DOMAIN_COLOR[domain],
      transparent: true,
      opacity: 0.7,
    });
    const edges = new THREE.LineSegments(edgesGeo, edgeMat);
    edges.position.copy(position);
    scene.add(edges);

    // Per-solid hover point light (domain color)
    const hoverLight = new THREE.PointLight(DOMAIN_COLOR[domain], 0, 4);
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
      targetFillOpacity: 0.85,
      currentFillOpacity: 0.85,
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
      new THREE.Vector3(2.8, 1.3, -0.4),
      new THREE.Vector3(0.003, 0.002, 0.0025),
      "industry"
    ),
    makeSolid(
      new THREE.TetrahedronGeometry(0.95, 0),
      new THREE.Vector3(3.6, 0, 0.2),
      new THREE.Vector3(0.002, 0.003, 0.002),
      "industry"
    ),
    makeSolid(
      new THREE.TetrahedronGeometry(0.85, 0),
      new THREE.Vector3(2.8, -1.3, -0.4),
      new THREE.Vector3(0.0025, 0.002, 0.003),
      "industry"
    ),
  ];

  // Connector lines from cube to each tetrahedron
  const cubePos = new THREE.Vector3(0, 0, 0);
  const connectorMat = new THREE.LineBasicMaterial({
    color: GOLD,
    transparent: true,
    opacity: 0.25,
  });

  const connectorLines: THREE.Line[] = [];

  // Government → College
  const govToCollege = new THREE.Line(
    new THREE.BufferGeometry().setFromPoints([solids[0].basePos, cubePos]),
    connectorMat.clone()
  );
  scene.add(govToCollege);
  connectorLines.push(govToCollege);

  // College → each Industry tetrahedron
  [solids[2], solids[3], solids[4]].forEach((s) => {
    const pts = [cubePos, s.basePos];
    const geo = new THREE.BufferGeometry().setFromPoints(pts);
    const line = new THREE.Line(geo, connectorMat.clone());
    scene.add(line);
    connectorLines.push(line);
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
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
    renderer.setSize(w, h);
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
          if (s.domain === selectedDomain) {
            s.targetEdgeOpacity = 1.0;
            s.targetFillOpacity = 0.95;
            s.targetScale = 1.9;
          } else {
            s.targetEdgeOpacity = 0;
            s.targetFillOpacity = 0;
            s.targetScale = 0.7;
          }
        });
        connectorLines.forEach((l) => {
          (l.material as THREE.LineBasicMaterial).opacity = 0;
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
      s.targetFillOpacity = 0.85;
      // Reset z position to base
      s.mesh.position.z = s.basePos.z;
      s.edges.position.z = s.basePos.z;
      s.hoverLight.intensity = 0;
    });

    connectorLines.forEach((l) => {
      (l.material as THREE.LineBasicMaterial).opacity = 0.25;
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
