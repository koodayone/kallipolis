/**
 * Convergence scene: horizontal flow diagram showing the ontology in motion.
 * Four analytical forms on the left converge via gold connectors into the
 * partnerships chainlink at center, which connects via a blue connector to
 * the strong workforce dumbbell on the right.
 *
 * Used on the /partnerships documentation page.
 */

import * as THREE from "three";
import {
  createMortarboardForm,
  createBookForm,
  createHardhatForm,
  createSkyscraperForm,
  createChainlinkForm,
  createDumbbellForm,
} from "./formFactories";

// ── Colors ───────────────────────────────────────────────────────────────────

const GOLD = 0xc9a84c;
const BLUE = 0x4fd1fd;

// ── Layout ───────────────────────────────────────────────────────────────────

type FormDef = {
  label: string;
  factory: (color: number) => THREE.Group;
  position: THREE.Vector3;
  scale: number;
  color: number;
};

const formDefs: FormDef[] = [
  { label: "Students",         factory: createMortarboardForm, position: new THREE.Vector3(-7, 3.5, 0),  scale: 0.7,  color: BLUE },
  { label: "Courses",          factory: createBookForm,        position: new THREE.Vector3(-7, 1.2, 0),  scale: 0.7,  color: BLUE },
  { label: "Occupations",      factory: createHardhatForm,     position: new THREE.Vector3(-7, -1.2, 0), scale: 0.7,  color: BLUE },
  { label: "Employers",        factory: createSkyscraperForm,  position: new THREE.Vector3(-7, -3.5, 0), scale: 0.65, color: BLUE },
  { label: "Partnerships",     factory: createChainlinkForm,   position: new THREE.Vector3(-0.5, 0, 0),  scale: 1.2,  color: BLUE },
  { label: "Strong Workforce", factory: createDumbbellForm,    position: new THREE.Vector3(5.5, 0, 0),   scale: 1.2,  color: BLUE },
];

export const CONVERGENCE_LABELS = formDefs.map((f) => f.label);

// ── Connector helpers ────────────────────────────────────────────────────────

function positionCylinderBetween(
  cyl: THREE.Mesh,
  start: THREE.Vector3,
  end: THREE.Vector3,
  length: number,
) {
  const mid = new THREE.Vector3().addVectors(start, end).multiplyScalar(0.5);
  cyl.position.copy(mid);
  const dir = new THREE.Vector3().subVectors(end, start).normalize();
  cyl.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), dir);
  cyl.scale.y = length;
}

// ── Scene builder ────────────────────────────────────────────────────────────

export type ConvergenceResult = {
  cleanup: () => void;
  getProjectedPositions: () => Record<string, { x: number; y: number }>;
};

export function buildConvergenceScene(canvas: HTMLCanvasElement): ConvergenceResult {
  const rect = canvas.getBoundingClientRect();
  const width = rect.width || canvas.clientWidth || 900;
  const height = rect.height || canvas.clientHeight || 500;

  const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.setSize(width, height, false);
  renderer.setClearColor(0x000000, 0);

  const scene = new THREE.Scene();

  const camera = new THREE.PerspectiveCamera(50, width / height, 0.1, 100);
  camera.position.set(-0.5, -0.8, 13);

  // Lighting
  scene.add(new THREE.AmbientLight(0xffffff, 0.08));
  const keyLight = new THREE.DirectionalLight(GOLD, 0.5);
  keyLight.position.set(5, 8, 4);
  scene.add(keyLight);
  const rimLight = new THREE.DirectionalLight(0x2244aa, 0.25);
  rimLight.position.set(-4, -2, -6);
  scene.add(rimLight);
  const fillLight = new THREE.DirectionalLight(0xffffff, 0.12);
  fillLight.position.set(0, 5, 8);
  scene.add(fillLight);

  // Build forms
  const groups: THREE.Group[] = [];
  for (const f of formDefs) {
    const g = f.factory(f.color);
    g.position.copy(f.position);
    g.scale.setScalar(f.scale);
    scene.add(g);
    groups.push(g);
  }

  // ── Connector materials ──────────────────────────────────────────────

  const connectorMats: THREE.MeshPhongMaterial[] = [];
  const glowMats: THREE.MeshPhongMaterial[] = [];

  function newConnectorMat(color: number) {
    const m = new THREE.MeshPhongMaterial({
      color, emissive: color, emissiveIntensity: 0.8,
      transparent: true, opacity: 0.7,
    });
    connectorMats.push(m);
    return m;
  }
  function newGlowMat(color: number) {
    const m = new THREE.MeshPhongMaterial({
      color, emissive: color, emissiveIntensity: 0.4,
      transparent: true, opacity: 0.12,
    });
    glowMats.push(m);
    return m;
  }

  const junctionGeo = new THREE.SphereGeometry(0.07, 8, 8);

  type ConnectorRefs = {
    length: number;
    direction: THREE.Vector3;
    start: THREE.Vector3;
    pulseLight: THREE.PointLight;
    color: number;
  };

  const connectors: ConnectorRefs[] = [];

  function buildConnector(start: THREE.Vector3, end: THREE.Vector3, color: number) {
    const length = start.distanceTo(end);
    const direction = new THREE.Vector3().subVectors(end, start).normalize();

    const junctionMat = new THREE.MeshPhongMaterial({
      color, emissive: color, emissiveIntensity: 1.0,
      transparent: true, opacity: 0.85,
    });

    // Core cylinder
    const coreGeo = new THREE.CylinderGeometry(0.035, 0.035, 1, 8);
    const core = new THREE.Mesh(coreGeo, newConnectorMat(color));
    positionCylinderBetween(core, start, end, length);
    scene.add(core);

    // Glow halo
    const glowGeo = new THREE.CylinderGeometry(0.10, 0.10, 1, 8);
    const glow = new THREE.Mesh(glowGeo, newGlowMat(color));
    positionCylinderBetween(glow, start, end, length);
    scene.add(glow);

    // Junction spheres
    const jStart = new THREE.Mesh(junctionGeo, junctionMat);
    jStart.position.copy(start);
    scene.add(jStart);
    const jEnd = new THREE.Mesh(junctionGeo, junctionMat);
    jEnd.position.copy(end);
    scene.add(jEnd);

    // Traveling pulse light
    const pulseLight = new THREE.PointLight(color, 0.6, 3);
    pulseLight.position.copy(start);
    scene.add(pulseLight);

    connectors.push({ length, direction, start, pulseLight, color });
  }

  // Connectors: left forms → partnerships chainlink
  const chainlinkLeft = new THREE.Vector3(-2.2, 0, 0);
  for (let i = 0; i < 4; i++) {
    const formRight = new THREE.Vector3(-5.8, formDefs[i].position.y, 0);
    buildConnector(formRight, chainlinkLeft, GOLD);
  }

  // Connector: partnerships → strong workforce
  const chainlinkRight = new THREE.Vector3(1.2, 0, 0);
  const dumbbellLeft = new THREE.Vector3(3.8, 0, 0);
  buildConnector(chainlinkRight, dumbbellLeft, GOLD);

  // Resize
  const resizeObserver = new ResizeObserver((obs) => {
    const e = obs[0];
    const w = e.contentRect.width;
    const h = e.contentRect.height;
    if (w === 0 || h === 0) return;
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
    renderer.setSize(w, h, false);
  });
  resizeObserver.observe(canvas);

  // Animation
  let rafId = 0;
  const startTime = performance.now();

  function tick() {
    rafId = requestAnimationFrame(tick);
    const elapsed = (performance.now() - startTime) / 1000;

    // Form rotation
    for (const g of groups) {
      g.rotation.x += 0.002;
      g.rotation.y += 0.003;
      g.rotation.z += 0.001;
    }

    // Glow shimmer
    glowMats.forEach((m, i) => {
      m.opacity = 0.08 + 0.08 * Math.sin(elapsed * 1.8 + i * 1.2);
    });

    // Core connector pulse
    connectorMats.forEach((m) => {
      m.opacity = 0.55 + 0.2 * Math.sin(elapsed * 2.2);
    });

    // Traveling pulse lights
    connectors.forEach((c, i) => {
      const t = (Math.sin(elapsed * 1.5 + i * 0.8) + 1) / 2;
      const pos = new THREE.Vector3()
        .copy(c.start)
        .addScaledVector(c.direction, t * c.length);
      pos.z += 1.0;
      c.pulseLight.position.copy(pos);
    });

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
      const positions: Record<string, { x: number; y: number }> = {};
      for (let i = 0; i < formDefs.length; i++) {
        const pos = formDefs[i].position.clone();
        pos.project(camera);
        positions[formDefs[i].label] = {
          x: ((pos.x + 1) / 2) * 100,
          y: ((1 - pos.y) / 2) * 100,
        };
      }
      return positions;
    },
  };
}
