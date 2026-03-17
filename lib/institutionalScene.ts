import * as THREE from "three";

type SceneNode = {
  id: string;
  geometry: THREE.BufferGeometry;
  color: number;
  position: THREE.Vector3;
  rotationSpeed: number;
};

type Edge = { from: string; to: string };

const GOLD = 0xffcc33;

const nodes: SceneNode[] = [
  {
    id: "gov",
    geometry: new THREE.DodecahedronGeometry(0.85, 0),
    color: 0x8a9bb0,
    position: new THREE.Vector3(0, 3.2, 0),
    rotationSpeed: 0.003,
  },
  {
    id: "college",
    geometry: new THREE.BoxGeometry(1.4, 1.4, 1.4),
    color: 0x4a7c59,
    position: new THREE.Vector3(0, 0.8, 0),
    rotationSpeed: 0.002,
  },
  {
    id: "biz-left",
    geometry: (() => { const g = new THREE.TetrahedronGeometry(0.9, 0); g.rotateX(Math.PI); return g; })(),
    color: 0xc0450a,
    position: new THREE.Vector3(-2.2, -1.8, 0),
    rotationSpeed: 0.004,
  },
  {
    id: "biz-center",
    geometry: (() => { const g = new THREE.TetrahedronGeometry(0.9, 0); g.rotateX(Math.PI); return g; })(),
    color: 0xc0450a,
    position: new THREE.Vector3(0, -2.0, 0),
    rotationSpeed: 0.004,
  },
  {
    id: "biz-right",
    geometry: (() => { const g = new THREE.TetrahedronGeometry(0.9, 0); g.rotateX(Math.PI); return g; })(),
    color: 0xc0450a,
    position: new THREE.Vector3(2.2, -1.8, 0),
    rotationSpeed: 0.004,
  },
];

const edges: Edge[] = [
  { from: "gov", to: "college" },
  { from: "college", to: "biz-left" },
  { from: "college", to: "biz-center" },
  { from: "college", to: "biz-right" },
];

export function buildInstitutionalScene(canvas: HTMLCanvasElement): () => void {
  const width = canvas.clientWidth;
  const height = canvas.clientHeight;

  // Renderer
  const renderer = new THREE.WebGLRenderer({ canvas, antialias: true });
  renderer.setPixelRatio(window.devicePixelRatio);
  renderer.setSize(width, height, false);
  renderer.setClearColor(0x1a1a24);

  // Scene
  const scene = new THREE.Scene();

  // Camera
  const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 100);
  camera.position.set(0, 1, 10);
  camera.lookAt(0, 0.5, 0);

  // Lighting
  scene.add(new THREE.AmbientLight(0xffffff, 0.45));
  const sun = new THREE.DirectionalLight(0xffffff, 1.1);
  sun.position.set(5, 8, 5);
  scene.add(sun);
  const fill = new THREE.DirectionalLight(0x4466aa, 0.3);
  fill.position.set(-5, -3, -5);
  scene.add(fill);

  // Build node meshes
  const meshByID = new Map<string, THREE.Mesh>();
  for (const node of nodes) {
    const geo = node.geometry.toNonIndexed();
    const mat = new THREE.MeshPhongMaterial({ color: node.color, flatShading: true, shininess: 30 });
    const mesh = new THREE.Mesh(geo, mat);
    mesh.position.copy(node.position);
    scene.add(mesh);
    meshByID.set(node.id, mesh);
  }

  // Build edges + joint dots
  const lineMat = new THREE.LineBasicMaterial({ color: GOLD });
  const dotMat = new THREE.MeshBasicMaterial({ color: GOLD });
  const dotGeo = new THREE.SphereGeometry(0.06, 8, 8);

  for (const edge of edges) {
    const fromPos = nodes.find(n => n.id === edge.from)!.position;
    const toPos = nodes.find(n => n.id === edge.to)!.position;

    const points = [fromPos.clone(), toPos.clone()];
    const lineGeo = new THREE.BufferGeometry().setFromPoints(points);
    scene.add(new THREE.Line(lineGeo, lineMat));

    const dotA = new THREE.Mesh(dotGeo, dotMat);
    dotA.position.copy(fromPos);
    scene.add(dotA);

    const dotB = new THREE.Mesh(dotGeo, dotMat);
    dotB.position.copy(toPos);
    scene.add(dotB);
  }

  // Resize handler
  const resizeObserver = new ResizeObserver(() => {
    const w = canvas.clientWidth;
    const h = canvas.clientHeight;
    renderer.setSize(w, h, false);
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
  });
  if (canvas.parentElement) resizeObserver.observe(canvas.parentElement);

  // Animation loop
  let rafId: number;
  const nodeEntries = nodes.map(n => ({ mesh: meshByID.get(n.id)!, speed: n.rotationSpeed }));

  function animate() {
    rafId = requestAnimationFrame(animate);
    for (const { mesh, speed } of nodeEntries) {
      mesh.rotation.y += speed;
    }
    renderer.render(scene, camera);
  }
  animate();

  // Cleanup
  return () => {
    cancelAnimationFrame(rafId);
    resizeObserver.disconnect();
    renderer.dispose();
  };
}
