import * as THREE from "three";

type SceneNode = {
  id: string;
  geometry: THREE.BufferGeometry;
  color: number;
  position: THREE.Vector3;
  rotationSpeed: number;
  initialRotation?: THREE.Euler;
};

type Edge = { from: string; to: string; reverseParticle?: boolean };

const GOLD = 0xffcc33;

const nodes: SceneNode[] = [
  {
    id: "gov",
    geometry: (() => { const g = new THREE.DodecahedronGeometry(0.85, 0); g.rotateX(0.46); return g; })(),
    color: 0xb0c8de,
    position: new THREE.Vector3(0, 3.2, 0),
    rotationSpeed: 0.0015,
  },
  {
    id: "college",
    geometry: new THREE.BoxGeometry(1.4, 1.4, 1.4),
    color: 0x5aaa72,
    position: new THREE.Vector3(0, 0.8, 0),
    rotationSpeed: 0.001,
    initialRotation: new THREE.Euler(0.35, 0.6, 0),
  },
  {
    id: "biz-left",
    geometry: new THREE.ConeGeometry(0.8, 0.8 * Math.sqrt(2), 3),
    color: 0xf04f20,
    position: new THREE.Vector3(-2.2, -1.8, 0),
    initialRotation: new THREE.Euler(0.3, 0, 0),
    rotationSpeed: 0.002,
  },
  {
    id: "biz-center",
    geometry: new THREE.ConeGeometry(0.8, 0.8 * Math.sqrt(2), 3),
    color: 0xf04f20,
    position: new THREE.Vector3(0, -2.0, 0),
    initialRotation: new THREE.Euler(0.3, 0, 0),
    rotationSpeed: 0.002,
  },
  {
    id: "biz-right",
    geometry: new THREE.ConeGeometry(0.8, 0.8 * Math.sqrt(2), 3),
    color: 0xf04f20,
    position: new THREE.Vector3(2.2, -1.8, 0),
    initialRotation: new THREE.Euler(0.3, 0, 0),
    rotationSpeed: 0.002,
  },
];

const edges: Edge[] = [
  { from: "gov", to: "college", reverseParticle: true },
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
  renderer.outputColorSpace = THREE.SRGBColorSpace;

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
    if (node.initialRotation) mesh.rotation.copy(node.initialRotation);
    scene.add(mesh);
    meshByID.set(node.id, mesh);
  }

  // Build edges + joint dots
  // TubeGeometry is used instead of Line because WebGL ignores LineBasicMaterial.linewidth
  const tubeMat = new THREE.MeshBasicMaterial({ color: GOLD });
  const dotMat = new THREE.MeshBasicMaterial({ color: GOLD });
  const dotGeo = new THREE.SphereGeometry(0.08, 8, 8);

  // Flowing particles per edge
  type Particle = { curve: THREE.LineCurve3; mesh: THREE.Mesh; t: number; speed: number };
  const particles: Particle[] = [];
  const particleMat = new THREE.MeshBasicMaterial({ color: 0xffe580 });
  const particleGeo = new THREE.SphereGeometry(0.07, 6, 6);

  for (const edge of edges) {
    const fromPos = nodes.find(n => n.id === edge.from)!.position;
    const toPos = nodes.find(n => n.id === edge.to)!.position;

    const curve = new THREE.LineCurve3(fromPos.clone(), toPos.clone());
    const tubeGeo = new THREE.TubeGeometry(curve, 1, 0.025, 6, false);
    scene.add(new THREE.Mesh(tubeGeo, tubeMat));

    const dotA = new THREE.Mesh(dotGeo, dotMat);
    dotA.position.copy(fromPos);
    scene.add(dotA);

    const dotB = new THREE.Mesh(dotGeo, dotMat);
    dotB.position.copy(toPos);
    scene.add(dotB);

    // Two particles per edge, staggered by 0.5
    const particleStart = edge.reverseParticle ? toPos.clone() : fromPos.clone();
    const particleEnd = edge.reverseParticle ? fromPos.clone() : toPos.clone();
    const particleCurve = new THREE.LineCurve3(particleStart, particleEnd);
    for (const offset of [0, 0.5]) {
      const mesh = new THREE.Mesh(particleGeo, particleMat);
      scene.add(mesh);
      particles.push({ curve: particleCurve, mesh, t: offset, speed: 0.004 });
    }
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
    for (const p of particles) {
      p.t = (p.t + p.speed) % 1;
      p.mesh.position.copy(p.curve.getPoint(p.t));
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
