/**
 * Renders the two units of action — partnerships (chainlink) and
 * strong workforce (dumbbell) — stacked vertically with ambient rotation.
 */

import * as THREE from "three";

// ── Helpers ───────────────────────────────────────────────────────────────────

function createFormMaterial(color: number): THREE.MeshPhongMaterial {
  return new THREE.MeshPhongMaterial({
    color, emissive: color, emissiveIntensity: 0.45,
    transparent: false, side: THREE.FrontSide, depthWrite: true,
  });
}

function addWithEdges(
  group: THREE.Group, geometry: THREE.BufferGeometry, material: THREE.Material,
  position?: THREE.Vector3, rotation?: THREE.Euler
): void {
  const mesh = new THREE.Mesh(geometry, material);
  if (position) mesh.position.copy(position);
  if (rotation) mesh.rotation.copy(rotation);
  group.add(mesh);
  const edgesGeo = new THREE.EdgesGeometry(geometry, 12);
  const edgeMat = new THREE.LineBasicMaterial({ color: 0xffffff, transparent: true, opacity: 0.7 });
  const edges = new THREE.LineSegments(edgesGeo, edgeMat);
  if (position) edges.position.copy(position);
  if (rotation) edges.rotation.copy(rotation);
  group.add(edges);
}

// ── Chainlink (Partnerships) ──────────────────────────────────────────────────

function createChainlinkForm(color: number): THREE.Group {
  const group = new THREE.Group();
  const mat = createFormMaterial(color);
  const ringRadius = 0.65, tubeRadius = 0.12;

  const ring1 = new THREE.Mesh(new THREE.TorusGeometry(ringRadius, tubeRadius, 32, 64), mat);
  ring1.position.set(0, -ringRadius / 2 - 0.15, 0);
  group.add(ring1);

  const ring2 = new THREE.Mesh(new THREE.TorusGeometry(ringRadius, tubeRadius, 32, 64), mat);
  ring2.position.set(0, ringRadius / 2 - 0.15, 0);
  ring2.rotation.set(0, Math.PI / 2, 0);
  group.add(ring2);

  return group;
}

// ── Dumbbell (Strong Workforce) ───────────────────────────────────────────────

function createDumbbellForm(color: number): THREE.Group {
  const group = new THREE.Group();
  const mat = createFormMaterial(color);

  const barLength = 1.35, barRadius = 0.0825;
  const weightRadius = 0.48, endFaceRadius = 0.39;
  const innerH = 0.15, bodyH = 0.35, outerH = 0.15;
  const totalH = innerH + bodyH + outerH;

  addWithEdges(group, new THREE.CylinderGeometry(barRadius, barRadius, barLength, 8), mat,
    new THREE.Vector3(0, 0, 0), new THREE.Euler(0, 0, Math.PI / 2));

  function addHead(xCenter: number, dir: number) {
    const baseX = xCenter - dir * totalH / 2;
    const rot = new THREE.Euler(0, 0, dir === 1 ? Math.PI / 2 : -Math.PI / 2);
    addWithEdges(group, new THREE.CylinderGeometry(barRadius * 2.5, weightRadius, innerH, 6), mat,
      new THREE.Vector3(baseX + dir * innerH / 2, 0, 0), rot);
    addWithEdges(group, new THREE.CylinderGeometry(weightRadius, weightRadius, bodyH, 6), mat,
      new THREE.Vector3(baseX + dir * (innerH + bodyH / 2), 0, 0), rot);
    addWithEdges(group, new THREE.CylinderGeometry(weightRadius, endFaceRadius, outerH, 6), mat,
      new THREE.Vector3(baseX + dir * (innerH + bodyH + outerH / 2), 0, 0), rot);
  }

  addHead(-barLength / 2, -1);
  addHead(barLength / 2, 1);
  return group;
}

// ── Scene ─────────────────────────────────────────────────────────────────────

const SOLID_COLOR = 0xb0a0ff;
const BG_COLOR = 0x060d1f;
const FORM_SCALE = 1.4;

type FormDef = {
  label: string;
  factory: (color: number) => THREE.Group;
  position: THREE.Vector3;
  rotSpeed: THREE.Vector3;
};

const formDefs: FormDef[] = [
  { label: "Partnerships",     factory: createChainlinkForm, position: new THREE.Vector3(-3.0, 1.6, 0),  rotSpeed: new THREE.Vector3(0.0018, 0.0025, 0.001) },
  { label: "Strong Workforce", factory: createDumbbellForm,  position: new THREE.Vector3(-3.0, -3.4, 0), rotSpeed: new THREE.Vector3(0.0018, 0.0025, 0.001) },
];

export const FORM_LABELS = formDefs.map((f) => f.label);

export type TwoFormsResult = {
  cleanup: () => void;
  getProjectedPositions: () => Record<string, { x: number; y: number }>;
  onHoverChange: (cb: (label: string | null) => void) => void;
};

export function buildTwoFormsScene(canvas: HTMLCanvasElement): TwoFormsResult {
  const rect = canvas.getBoundingClientRect();
  const width = rect.width || canvas.clientWidth || 800;
  const height = rect.height || canvas.clientHeight || 600;

  const renderer = new THREE.WebGLRenderer({ canvas, antialias: true });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.setSize(width, height, false);
  renderer.setClearColor(BG_COLOR, 1);

  const scene = new THREE.Scene();
  scene.fog = new THREE.FogExp2(BG_COLOR, 0.015);

  const camera = new THREE.PerspectiveCamera(50, width / height, 0.1, 100);
  camera.position.set(0, -0.15, 12);

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
    handleHover(hitIndex);
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
  };
}
