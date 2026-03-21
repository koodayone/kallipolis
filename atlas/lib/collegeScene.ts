import * as THREE from "three";

export type CollegeNodeKey = "students" | "curricula" | "programs";

export type CollegeSceneCallbacks = {
  onNodeClick: (node: CollegeNodeKey) => void;
  onHoverChange: (node: CollegeNodeKey | null) => void;
  solidColor: number; // THREE hex int, e.g. 0x7b2d3e
};

type SolidEntry = {
  node: CollegeNodeKey;
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
  | { phase: "pulse"; elapsed: number; node: CollegeNodeKey }
  | { phase: "dissolve"; elapsed: number; node: CollegeNodeKey };

const LERP_SPEED = 0.08;

export function buildCollegeScene(
  canvas: HTMLCanvasElement,
  callbacks: CollegeSceneCallbacks
): {
  cleanup: () => void;
  resetScene: () => void;
} {
  const initW = canvas.clientWidth || 800;
  const initH = canvas.clientHeight || 360;

  // ── Renderer ──────────────────────────────────────────────────────────────
  const renderer = new THREE.WebGLRenderer({
    canvas,
    antialias: true,
    alpha: true,
  });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.setSize(initW, initH, false);
  renderer.setClearColor(0x000000, 0);

  // ── Scene & Camera ────────────────────────────────────────────────────────
  const scene = new THREE.Scene();

  const camera = new THREE.PerspectiveCamera(50, initW / initH, 0.1, 100);
  camera.position.set(0, 0, 5.5);

  // ── Lighting ──────────────────────────────────────────────────────────────
  scene.add(new THREE.AmbientLight(0xffffff, 0.5));

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
    node: CollegeNodeKey
  ): SolidEntry {
    const color = solidColor;

    const fillMat = new THREE.MeshPhongMaterial({
      color,
      emissive: color,
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

    const hoverLight = new THREE.PointLight(color, 0, 4);
    hoverLight.position.copy(position);
    scene.add(hoverLight);

    return {
      node,
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
    // Students — Tetrahedron (left)
    makeSolid(
      new THREE.TetrahedronGeometry(1.1, 0),
      new THREE.Vector3(-3.0, 0, 0),
      new THREE.Vector3(0.002, 0.0028, 0.0012),
      "students"
    ),
    // Curricula — Icosahedron (center)
    makeSolid(
      new THREE.IcosahedronGeometry(0.95, 0),
      new THREE.Vector3(0, 0, 0),
      new THREE.Vector3(0.0015, 0.002, 0.001),
      "curricula"
    ),
    // Programs — Dodecahedron (right)
    makeSolid(
      new THREE.DodecahedronGeometry(0.95, 0),
      new THREE.Vector3(3.0, 0, 0),
      new THREE.Vector3(0.0018, 0.0022, 0.0008),
      "programs"
    ),
  ];

  // ── Interaction State ─────────────────────────────────────────────────────
  let hoveredNode: CollegeNodeKey | null = null;
  let clickState: ClickState = { phase: "idle" };
  let selectedNode: CollegeNodeKey | null = null;
  let isLocked = false;

  const mouse = new THREE.Vector2(-999, -999);
  const raycaster = new THREE.Raycaster();
  const allMeshes = solids.map((s) => s.mesh);

  function handleHover(node: CollegeNodeKey | null) {
    if (hoveredNode === node) return;
    hoveredNode = node;
    callbacks.onHoverChange(node);

    solids.forEach((s) => {
      const isHovered = node !== null && s.node === node;
      s.targetEdgeOpacity = isHovered ? 1.0 : node !== null ? 0.45 : 0.7;
      s.hoverLight.intensity = isHovered ? 0.6 : 0;
      s.targetScale = isHovered ? 1.06 : 1.0;
    });
  }

  function handleClick(node: CollegeNodeKey) {
    if (isLocked) return;
    isLocked = true;
    selectedNode = node;
    clickState = { phase: "pulse", elapsed: 0, node };
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
      if (solid) handleClick(solid.node);
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
    renderer.setSize(w, h, false);
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
      handleHover(hitSolid ? hitSolid.node : null);
      canvas.style.cursor = hitSolid ? "pointer" : "default";
    }

    // Click state machine
    if (clickState.phase === "pulse") {
      clickState.elapsed += delta;
      const t = clickState.elapsed / 0.22;
      const pulsed = Math.sin(Math.PI * Math.min(t, 1)) * 0.18 + 1;
      const pulsingSolid = solids.find((s) => s.node === (clickState as { node: CollegeNodeKey }).node);
      if (pulsingSolid) {
        pulsingSolid.currentScale = pulsed;
        pulsingSolid.mesh.scale.setScalar(pulsed);
        pulsingSolid.edges.scale.setScalar(pulsed);
      }

      if (clickState.elapsed >= 0.22) {
        clickState = { phase: "dissolve", elapsed: 0, node: clickState.node };
        solids.forEach((s) => {
          (s.mesh.material as THREE.MeshPhongMaterial).transparent = true;
          if (s.node === selectedNode) {
            s.targetEdgeOpacity = 1.0;
            s.targetFillOpacity = 1.0;
            s.targetScale = 1.9;
          } else {
            s.targetEdgeOpacity = 0;
            s.targetFillOpacity = 0;
            s.targetScale = 0.7;
          }
        });
      }
    } else if (clickState.phase === "dissolve") {
      clickState.elapsed += delta;

      const selectedSolid = solids.find((s) => s.node === (clickState as { node: CollegeNodeKey }).node);
      if (selectedSolid) {
        selectedSolid.mesh.position.z = lerp(selectedSolid.mesh.position.z, selectedSolid.basePos.z + 1.8, 0.05);
        selectedSolid.edges.position.z = selectedSolid.mesh.position.z;
      }

      if (clickState.elapsed >= 0.7) {
        callbacks.onNodeClick((clickState as { node: CollegeNodeKey }).node);
        clickState = { phase: "idle" };
      }
    }

    // Ambient rotation & lerp
    solids.forEach((s) => {
      s.mesh.rotation.x += s.rotSpeed.x;
      s.mesh.rotation.y += s.rotSpeed.y;
      s.mesh.rotation.z += s.rotSpeed.z;
      s.edges.rotation.copy(s.mesh.rotation);

      if (clickState.phase !== "pulse" || (clickState as { node: CollegeNodeKey }).node !== s.node) {
        s.currentScale = lerp(s.currentScale, s.targetScale, LERP_SPEED);
        s.mesh.scale.setScalar(s.currentScale);
        s.edges.scale.setScalar(s.currentScale);
      }

      s.currentEdgeOpacity = lerp(s.currentEdgeOpacity, s.targetEdgeOpacity, LERP_SPEED);
      (s.edges.material as THREE.LineBasicMaterial).opacity = s.currentEdgeOpacity;

      s.currentFillOpacity = lerp(s.currentFillOpacity, s.targetFillOpacity, LERP_SPEED);
      (s.mesh.material as THREE.MeshPhongMaterial).opacity = s.currentFillOpacity;
    });

    renderer.render(scene, camera);
  }

  tick();

  // ── Reset ─────────────────────────────────────────────────────────────────
  function resetScene() {
    isLocked = false;
    selectedNode = null;
    hoveredNode = null;
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
