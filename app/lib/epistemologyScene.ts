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

// ── Form factories ────────────────────────────────────────────────────────────

function createMortarboardForm(color: number): THREE.Group {
  const group = new THREE.Group();
  const mat = createFormMaterial(color);
  addWithEdges(group, new THREE.BoxGeometry(1.53, 0.077, 1.53), mat, new THREE.Vector3(0, 0.281, 0));
  addWithEdges(group, new THREE.CylinderGeometry(0.523, 0.612, 0.255, 6), mat, new THREE.Vector3(0, 0.102, 0));
  addWithEdges(group, new THREE.SphereGeometry(0.089, 8, 6), mat, new THREE.Vector3(0, 0.37, 0));
  addWithEdges(group, new THREE.CylinderGeometry(0.026, 0.026, 0.765, 4), mat, new THREE.Vector3(0.765 / 2, 0.344, 0), new THREE.Euler(0, 0, Math.PI / 2));
  addWithEdges(group, new THREE.CylinderGeometry(0.026, 0.026, 0.638, 4), mat, new THREE.Vector3(0.765, 0.344 - 0.638 / 2, 0));
  addWithEdges(group, new THREE.SphereGeometry(0.089, 6, 4), mat, new THREE.Vector3(0.765, 0.344 - 0.638, 0));
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
  const dome = new THREE.Mesh(new THREE.SphereGeometry(0.75, 32, 20, 0, Math.PI * 2, 0, Math.PI / 2), mat);
  dome.scale.set(0.9, 1.1, 1.15); group.add(dome);
  const brim = new THREE.Mesh(new THREE.TorusGeometry(0.80, 0.10, 12, 48), mat);
  brim.rotation.x = Math.PI / 2; brim.scale.set(0.9, 1.15, 1.0); group.add(brim);
  const ridgeMat = new THREE.MeshBasicMaterial({ color: 0xffffff, transparent: true, opacity: 1.0 });
  const cr = new THREE.Mesh(new THREE.TorusGeometry(0.75, 0.012, 4, 32, Math.PI), ridgeMat);
  cr.rotation.set(0, Math.PI / 2, 0); cr.scale.set(1.15, 1.1, 0.9); group.add(cr);
  for (const x of [-0.22, 0.22]) {
    const r = new THREE.Mesh(new THREE.TorusGeometry(0.75, 0.012, 4, 32, Math.PI), ridgeMat);
    r.rotation.set(0, Math.PI / 2, 0); r.position.x = x; r.scale.set(1.1, 1.05, 0.8); group.add(r);
  }
  group.position.y = -0.15;
  return group;
}

function createSkyscraperForm(color: number): THREE.Group {
  const group = new THREE.Group();
  const mat = createFormMaterial(color); mat.side = THREE.DoubleSide;
  const bW = 0.3, tW = 0.2, bY = -1, mY = 0, tY = 1, mS = 0.85;
  const v = [
    -bW,bY,-bW, bW,bY,-bW, bW,bY,bW, -bW,bY,bW,
    -bW*mS,mY,-bW*mS, 0,mY,-tW*Math.SQRT2*1.1, bW*mS,mY,-bW*mS, tW*Math.SQRT2*1.1,mY,0,
    bW*mS,mY,bW*mS, 0,mY,tW*Math.SQRT2*1.1, -bW*mS,mY,bW*mS, -tW*Math.SQRT2*1.1,mY,0,
    0,tY,-tW*Math.SQRT2, tW*Math.SQRT2,tY,0, 0,tY,tW*Math.SQRT2, -tW*Math.SQRT2,tY,0,
  ];
  const f = [0,2,1,0,3,2,0,5,4,0,1,5,1,6,5,1,7,6,1,2,7,2,8,7,2,9,8,2,3,9,3,10,9,3,11,10,3,0,11,0,4,11,
    4,5,12,5,6,12,6,13,12,6,7,13,7,8,13,8,14,13,8,9,14,9,10,14,10,15,14,10,11,15,11,4,15,4,12,15,12,13,14,12,14,15];
  const geo = new THREE.BufferGeometry();
  geo.setAttribute("position", new THREE.Float32BufferAttribute(v, 3));
  geo.setIndex(f); geo.computeVertexNormals();
  group.add(new THREE.Mesh(geo, mat));
  group.add(new THREE.LineSegments(new THREE.EdgesGeometry(geo, 5), new THREE.LineBasicMaterial({ color: 0xffffff, transparent: true, opacity: 0.7 })));
  const spire = new THREE.Mesh(new THREE.CylinderGeometry(0.005, 0.025, 0.35, 6), mat);
  spire.position.y = tY + 0.175; group.add(spire);
  return group;
}

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
  camera.position.set(0, -0.8, 9);

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

  const formGroups: { group: THREE.Group; rotSpeed: THREE.Vector3 }[] = [];
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
    formGroups.push({ group, rotSpeed: new THREE.Vector3(0.0018, 0.0025, 0.001) });

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
  function tick() {
    rafId = requestAnimationFrame(tick);
    const elapsed = (performance.now() - startTime) / 1000;

    for (const fg of formGroups) {
      fg.group.rotation.x += fg.rotSpeed.x;
      fg.group.rotation.y += fg.rotSpeed.y;
      fg.group.rotation.z += fg.rotSpeed.z;
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
  };
}
