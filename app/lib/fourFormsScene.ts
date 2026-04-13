/**
 * Renders the four units of analysis — students, courses, occupations,
 * employers — as platonic forms in a 2x2 grid with ambient rotation.
 * Reuses the form factories from atlasPreviewScene.
 */

import * as THREE from "three";

// ── Shared helpers ────────────────────────────────────────────────────────────

function createFormMaterial(color: number): THREE.MeshPhongMaterial {
  return new THREE.MeshPhongMaterial({
    color,
    emissive: color,
    emissiveIntensity: 0.45,
    transparent: false,
    side: THREE.FrontSide,
    depthWrite: true,
  });
}

function addWithEdges(
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
  const edgeMat = new THREE.LineBasicMaterial({ color: 0xffffff, transparent: true, opacity: 0.7 });
  const edges = new THREE.LineSegments(edgesGeo, edgeMat);
  if (position) edges.position.copy(position);
  if (rotation) edges.rotation.copy(rotation);
  group.add(edges);
}

// ── Form factories ────────────────────────────────────────────────────────────

function createMortarboardForm(color: number): THREE.Group {
  const group = new THREE.Group();
  const mat = createFormMaterial(color);
  const boardGeo = new THREE.BoxGeometry(1.53, 0.077, 1.53);
  addWithEdges(group, boardGeo, mat, new THREE.Vector3(0, 0.281, 0));
  const capGeo = new THREE.CylinderGeometry(0.523, 0.612, 0.255, 6);
  addWithEdges(group, capGeo, mat, new THREE.Vector3(0, 0.102, 0));
  const buttonGeo = new THREE.SphereGeometry(0.089, 8, 6);
  addWithEdges(group, buttonGeo, mat, new THREE.Vector3(0, 0.37, 0));
  const cordGeo = new THREE.CylinderGeometry(0.026, 0.026, 0.765, 4);
  addWithEdges(group, cordGeo, mat, new THREE.Vector3(0.765 / 2, 0.344, 0), new THREE.Euler(0, 0, Math.PI / 2));
  const tasselGeo = new THREE.CylinderGeometry(0.026, 0.026, 0.638, 4);
  addWithEdges(group, tasselGeo, mat, new THREE.Vector3(0.765, 0.344 - 0.638 / 2, 0));
  const tasselEndGeo = new THREE.SphereGeometry(0.089, 6, 4);
  addWithEdges(group, tasselEndGeo, mat, new THREE.Vector3(0.765, 0.344 - 0.638, 0));
  group.position.y = -0.128;
  return group;
}

function createBookForm(color: number): THREE.Group {
  const group = new THREE.Group();
  const mat = createFormMaterial(color);
  const cw = 1.05, ch = 1.35, ct = 0.06, oa = 0.25;
  addWithEdges(group, new THREE.BoxGeometry(cw, ch, ct), mat,
    new THREE.Vector3(-cw / 2 * Math.cos(oa), 0, -cw / 2 * Math.sin(oa)), new THREE.Euler(0, oa, 0));
  addWithEdges(group, new THREE.BoxGeometry(cw, ch, ct), mat,
    new THREE.Vector3(cw / 2 * Math.cos(oa), 0, -cw / 2 * Math.sin(oa)), new THREE.Euler(0, -oa, 0));
  const pw = cw * 0.88, ph = ch * 0.92, pd = 0.225;
  addWithEdges(group, new THREE.BoxGeometry(0.03, ch, pd), mat, new THREE.Vector3(0, 0, -cw * Math.sin(oa) * 0.65));
  addWithEdges(group, new THREE.BoxGeometry(pw, ph, pd), mat,
    new THREE.Vector3(-pw / 2 * Math.cos(oa), 0, -pw / 2 * Math.sin(oa)), new THREE.Euler(0, oa, 0));
  addWithEdges(group, new THREE.BoxGeometry(pw, ph, pd), mat,
    new THREE.Vector3(pw / 2 * Math.cos(oa), 0, -pw / 2 * Math.sin(oa)), new THREE.Euler(0, -oa, 0));
  return group;
}

function createHardhatForm(color: number): THREE.Group {
  const group = new THREE.Group();
  const mat = createFormMaterial(color);
  const domeGeo = new THREE.SphereGeometry(0.75, 32, 20, 0, Math.PI * 2, 0, Math.PI / 2);
  const dome = new THREE.Mesh(domeGeo, mat);
  dome.scale.set(0.9, 1.1, 1.15);
  group.add(dome);
  const brimGeo = new THREE.TorusGeometry(0.80, 0.10, 12, 48);
  const brim = new THREE.Mesh(brimGeo, mat);
  brim.rotation.x = Math.PI / 2;
  brim.scale.set(0.9, 1.15, 1.0);
  group.add(brim);
  const ridgeMat = new THREE.MeshBasicMaterial({ color: 0xffffff, transparent: true, opacity: 1.0 });
  const centerRidge = new THREE.Mesh(new THREE.TorusGeometry(0.75, 0.012, 4, 32, Math.PI), ridgeMat);
  centerRidge.rotation.set(0, Math.PI / 2, 0);
  centerRidge.scale.set(1.15, 1.1, 0.9);
  group.add(centerRidge);
  for (const x of [-0.22, 0.22]) {
    const r = new THREE.Mesh(new THREE.TorusGeometry(0.75, 0.012, 4, 32, Math.PI), ridgeMat);
    r.rotation.set(0, Math.PI / 2, 0);
    r.position.x = x;
    r.scale.set(1.1, 1.05, 0.8);
    group.add(r);
  }
  group.position.y = -0.15;
  return group;
}

function createSkyscraperForm(color: number): THREE.Group {
  const group = new THREE.Group();
  const mat = createFormMaterial(color);
  mat.side = THREE.DoubleSide;
  const bW = 0.3, tW = 0.2, bY = -1, mY = 0, tY = 1, mS = 0.85;
  const v = [
    -bW, bY, -bW, bW, bY, -bW, bW, bY, bW, -bW, bY, bW,
    -bW * mS, mY, -bW * mS, 0, mY, -tW * Math.SQRT2 * 1.1, bW * mS, mY, -bW * mS, tW * Math.SQRT2 * 1.1, mY, 0,
    bW * mS, mY, bW * mS, 0, mY, tW * Math.SQRT2 * 1.1, -bW * mS, mY, bW * mS, -tW * Math.SQRT2 * 1.1, mY, 0,
    0, tY, -tW * Math.SQRT2, tW * Math.SQRT2, tY, 0, 0, tY, tW * Math.SQRT2, -tW * Math.SQRT2, tY, 0,
  ];
  const f = [0,2,1,0,3,2,0,5,4,0,1,5,1,6,5,1,7,6,1,2,7,2,8,7,2,9,8,2,3,9,3,10,9,3,11,10,3,0,11,0,4,11,
    4,5,12,5,6,12,6,13,12,6,7,13,7,8,13,8,14,13,8,9,14,9,10,14,10,15,14,10,11,15,11,4,15,4,12,15,12,13,14,12,14,15];
  const geo = new THREE.BufferGeometry();
  geo.setAttribute("position", new THREE.Float32BufferAttribute(v, 3));
  geo.setIndex(f);
  geo.computeVertexNormals();
  group.add(new THREE.Mesh(geo, mat));
  const eGeo = new THREE.EdgesGeometry(geo, 5);
  group.add(new THREE.LineSegments(eGeo, new THREE.LineBasicMaterial({ color: 0xffffff, transparent: true, opacity: 0.7 })));
  const spire = new THREE.Mesh(new THREE.CylinderGeometry(0.005, 0.025, 0.35, 6), mat);
  spire.position.y = tY + 0.175;
  group.add(spire);
  return group;
}

// ── Scene ─────────────────────────────────────────────────────────────────────

const SOLID_COLOR = 0xc9a84c;
const BG_COLOR = 0x060d1f;
const FORM_SCALE = 1.6;

type FormDef = {
  label: string;
  factory: (color: number) => THREE.Group;
  position: THREE.Vector3;
  rotSpeed: THREE.Vector3;
};

const formDefs: FormDef[] = [
  { label: "Students",    factory: createMortarboardForm, position: new THREE.Vector3(-2.8, 3.0, 0),  rotSpeed: new THREE.Vector3(0.0018, 0.0025, 0.001) },
  { label: "Courses",     factory: createBookForm,        position: new THREE.Vector3(2.8, 3.0, 0),   rotSpeed: new THREE.Vector3(0.0015, 0.002, 0.001) },
  { label: "Occupations", factory: createHardhatForm,     position: new THREE.Vector3(-2.8, -3.2, 0), rotSpeed: new THREE.Vector3(0.002, 0.0028, 0.0012) },
  { label: "Employers",   factory: createSkyscraperForm,  position: new THREE.Vector3(2.8, -3.2, 0),  rotSpeed: new THREE.Vector3(0.0015, 0.002, 0.0018) },
];

export const FORM_LABELS = formDefs.map((f) => f.label);

export type FourFormsResult = {
  cleanup: () => void;
  getProjectedPositions: () => Record<string, { x: number; y: number }>;
  onHoverChange: (cb: (label: string | null) => void) => void;
  setColor: (color: number) => void;
};

export function buildFourFormsScene(canvas: HTMLCanvasElement): FourFormsResult {
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
  camera.position.set(0, -0.15, 14);

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

  const entries = formDefs.map((f, i) => {
    const group = f.factory(SOLID_COLOR);
    group.position.copy(f.position);
    group.scale.setScalar(FORM_SCALE);
    scene.add(group);
    group.traverse((child) => {
      if (child instanceof THREE.Mesh) child.userData.formIndex = i;
    });
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
    setColor: (newColor: number) => {
      const threeColor = new THREE.Color(newColor);
      keyLight.color.copy(threeColor);
      for (const e of entries) {
        e.hoverLight.color.copy(threeColor);
        e.group.traverse((child) => {
          if (child instanceof THREE.Mesh) {
            const m = child.material;
            if (m instanceof THREE.MeshPhongMaterial && m.depthWrite) {
              m.color.copy(threeColor);
              m.emissive.copy(threeColor);
            }
          }
        });
      }
    },
  };
}
