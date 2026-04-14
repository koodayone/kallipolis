/**
 * Unified Knowledge scene: three-row architecture diagram for the
 * Sources page. Bottom row: four data authority logos (HTML overlay
 * anchors). Middle row: four rotating platonic forms. Top row: a single
 * cube representing the College Atlas. Vertical connectors link forms
 * to authorities; four convergent connectors rise from the forms to
 * meet at the cube's base.
 */

import * as THREE from "three";
import {
  createMortarboardForm,
  createBookForm,
  createHardhatForm,
  createSkyscraperForm,
  createCubeForm,
} from "./formFactories";

const GOLD = 0xc9a84c;
const BG_COLOR = 0x060d1f;
const FORM_SCALE = 0.85;
const CUBE_SCALE = 1.0;

// Layout
const COLUMNS_X = [-5.4, -1.8, 1.8, 5.4];
const FORM_Y = 0;
const LOGO_Y = -3.8;
const CUBE_Y = 3.8;

const FORM_BASE_OFFSET = 1.8;
const FORM_TOP_OFFSET = 1.5;
const FORM_LABEL_Y = FORM_Y - 1.35;
const LOGO_TOP = LOGO_Y + 0.6;
const LOGO_ANCHOR_Y = LOGO_Y - 0.6;
const CUBE_BASE = CUBE_Y - CUBE_SCALE * 0.8;
const CUBE_LABEL_Y = CUBE_Y + 1.7;

type AuthorityKey = "chancellor" | "colleges" | "coe" | "edd";

type FormDef = {
  key: AuthorityKey;
  factory: (color: number) => THREE.Group;
  columnIndex: number;
};

const FORMS: FormDef[] = [
  { key: "chancellor", factory: createMortarboardForm, columnIndex: 0 },
  { key: "colleges",   factory: createBookForm,        columnIndex: 1 },
  { key: "coe",        factory: createHardhatForm,     columnIndex: 2 },
  { key: "edd",        factory: createSkyscraperForm,  columnIndex: 3 },
];

export type UnifiedKnowledgeResult = {
  cleanup: () => void;
  getLogoPositions: () => Record<AuthorityKey, { x: number; y: number }>;
  getFormLabelPositions: () => Record<AuthorityKey, { x: number; y: number }>;
  getCubeLabelPosition: () => { x: number; y: number };
};

export function buildUnifiedKnowledgeScene(canvas: HTMLCanvasElement): UnifiedKnowledgeResult {
  const rect = canvas.getBoundingClientRect();
  const width = rect.width || canvas.clientWidth || 900;
  const height = rect.height || canvas.clientHeight || 640;

  const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.setSize(width, height, false);
  renderer.setClearColor(BG_COLOR, 0);

  const scene = new THREE.Scene();

  const camera = new THREE.PerspectiveCamera(50, width / height, 0.1, 100);
  camera.position.set(0, -3.0, 19);

  // Lighting — match authorityRowScene pattern
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

  // Build middle-row forms
  const formGroups: { group: THREE.Group; columnIndex: number }[] = [];
  for (const f of FORMS) {
    const g = f.factory(GOLD);
    g.position.set(COLUMNS_X[f.columnIndex], FORM_Y, 0);
    g.scale.setScalar(FORM_SCALE);
    scene.add(g);
    formGroups.push({ group: g, columnIndex: f.columnIndex });
  }

  // Build cube
  const cube = createCubeForm(GOLD);
  cube.position.set(0, CUBE_Y, 0);
  cube.scale.setScalar(CUBE_SCALE);
  scene.add(cube);

  // ── Connector materials (shared) ─────────────────────────────────
  const connectorMats: THREE.MeshPhongMaterial[] = [];
  const glowMats: THREE.MeshPhongMaterial[] = [];
  const junctionMat = new THREE.MeshPhongMaterial({
    color: GOLD, emissive: GOLD, emissiveIntensity: 1.0,
    transparent: true, opacity: 0.85,
  });
  const junctionGeo = new THREE.SphereGeometry(0.07, 8, 8);

  function newConnectorMat() {
    const m = new THREE.MeshPhongMaterial({
      color: GOLD, emissive: GOLD, emissiveIntensity: 0.8,
      transparent: true, opacity: 0.7,
    });
    connectorMats.push(m);
    return m;
  }
  function newGlowMat() {
    const m = new THREE.MeshPhongMaterial({
      color: GOLD, emissive: GOLD, emissiveIntensity: 0.4,
      transparent: true, opacity: 0.12,
    });
    glowMats.push(m);
    return m;
  }

  type ConnectorRefs = {
    length: number;
    direction: THREE.Vector3;
    start: THREE.Vector3;
    pulseLight: THREE.PointLight;
    glowLights: THREE.PointLight[];
  };

  const connectors: ConnectorRefs[] = [];

  function positionCylinderBetween(cyl: THREE.Mesh, start: THREE.Vector3, end: THREE.Vector3, length: number) {
    const mid = new THREE.Vector3().addVectors(start, end).multiplyScalar(0.5);
    cyl.position.copy(mid);
    const dir = new THREE.Vector3().subVectors(end, start).normalize();
    cyl.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), dir);
    cyl.scale.y = length;
  }

  function buildConnector(start: THREE.Vector3, end: THREE.Vector3, skipEndJunction = false) {
    const length = start.distanceTo(end);
    const direction = new THREE.Vector3().subVectors(end, start).normalize();

    // Core cylinder — unit height, scaled via positionCylinderBetween
    const coreGeo = new THREE.CylinderGeometry(0.035, 0.035, 1, 8);
    const core = new THREE.Mesh(coreGeo, newConnectorMat());
    positionCylinderBetween(core, start, end, length);
    scene.add(core);

    // Glow halo
    const glowGeo = new THREE.CylinderGeometry(0.10, 0.10, 1, 8);
    const glow = new THREE.Mesh(glowGeo, newGlowMat());
    positionCylinderBetween(glow, start, end, length);
    scene.add(glow);

    // Junction spheres
    const jStart = new THREE.Mesh(junctionGeo, junctionMat);
    jStart.position.copy(start);
    scene.add(jStart);
    if (!skipEndJunction) {
      const jEnd = new THREE.Mesh(junctionGeo, junctionMat);
      jEnd.position.copy(end);
      scene.add(jEnd);
    }

    // Static glow lights along the connector
    const glowLights: THREE.PointLight[] = [];
    for (let i = 0; i < 3; i++) {
      const t = (i + 0.5) / 3;
      const pos = new THREE.Vector3().lerpVectors(start, end, t);
      const light = new THREE.PointLight(GOLD, 0.3, 4);
      light.position.copy(pos).add(new THREE.Vector3(0, 0, 0.6));
      scene.add(light);
      glowLights.push(light);
    }

    // Traveling pulse light
    const pulseLight = new THREE.PointLight(GOLD, 0.6, 3);
    pulseLight.position.copy(start).add(new THREE.Vector3(0, 0, 1.0));
    scene.add(pulseLight);

    connectors.push({ length, direction, start, pulseLight, glowLights });
  }

  // Vertical connectors: form base → above logo
  for (const f of FORMS) {
    const x = COLUMNS_X[f.columnIndex];
    const start = new THREE.Vector3(x, FORM_Y - FORM_BASE_OFFSET, 0);
    const end = new THREE.Vector3(x, LOGO_TOP, 0);
    buildConnector(start, end);
  }

  // Convergent connectors: form top → cube base
  const cubeBaseCenter = new THREE.Vector3(0, CUBE_BASE, 0);
  for (const f of FORMS) {
    const x = COLUMNS_X[f.columnIndex];
    const start = new THREE.Vector3(x, FORM_Y + FORM_TOP_OFFSET, 0);
    buildConnector(start, cubeBaseCenter.clone(), true);
  }

  // ── Resize ─────────────────────────────────────────────────────
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

  // ── Animation ──────────────────────────────────────────────────
  let rafId = 0;
  const startTime = performance.now();

  function tick() {
    rafId = requestAnimationFrame(tick);
    const elapsed = (performance.now() - startTime) / 1000;

    // Form rotation
    for (const f of formGroups) {
      f.group.rotation.x += 0.002;
      f.group.rotation.y += 0.0028;
      f.group.rotation.z += 0.0012;
    }

    // Cube rotation — slower, different axes
    cube.rotation.y += 0.0035;
    cube.rotation.x += 0.0014;

    // Connector shimmer — unified across all connectors
    const glowOpacity = 0.1 + 0.1 * Math.sin(elapsed * 1.8);
    const coreOpacity = 0.55 + 0.2 * Math.sin(elapsed * 2.2);
    const coreEmissive = 0.7 + 0.3 * Math.sin(elapsed * 1.5);
    for (const m of glowMats) m.opacity = glowOpacity;
    for (const m of connectorMats) {
      m.opacity = coreOpacity;
      m.emissiveIntensity = coreEmissive;
    }

    // Traveling pulses — staggered per connector
    for (let i = 0; i < connectors.length; i++) {
      const c = connectors[i];
      const offset = i * 0.6;
      const pulseT = (Math.sin(elapsed * 0.8 + offset) + 1) / 2;
      const pos = new THREE.Vector3().copy(c.start).addScaledVector(c.direction, pulseT * c.length);
      c.pulseLight.position.copy(pos).add(new THREE.Vector3(0, 0, 1.0));
      c.pulseLight.intensity = 0.4 + 0.4 * Math.sin(elapsed * 1.2 + offset);

      // Staggered glow light shimmer
      for (let g = 0; g < c.glowLights.length; g++) {
        c.glowLights[g].intensity = 0.25 + 0.2 * Math.sin(elapsed * 1.6 + i * 0.8 + g * 0.4);
      }
    }

    renderer.render(scene, camera);
  }
  tick();

  // Logo position projection
  const logoWorldPositions: Record<AuthorityKey, THREE.Vector3> = {
    chancellor: new THREE.Vector3(COLUMNS_X[0], LOGO_ANCHOR_Y, 0),
    colleges:   new THREE.Vector3(COLUMNS_X[1], LOGO_ANCHOR_Y, 0),
    coe:        new THREE.Vector3(COLUMNS_X[2], LOGO_ANCHOR_Y, 0),
    edd:        new THREE.Vector3(COLUMNS_X[3], LOGO_ANCHOR_Y, 0),
  };

  const formLabelWorldPositions: Record<AuthorityKey, THREE.Vector3> = {
    chancellor: new THREE.Vector3(COLUMNS_X[0], FORM_LABEL_Y, 0),
    colleges:   new THREE.Vector3(COLUMNS_X[1], FORM_LABEL_Y, 0),
    coe:        new THREE.Vector3(COLUMNS_X[2], FORM_LABEL_Y, 0),
    edd:        new THREE.Vector3(COLUMNS_X[3], FORM_LABEL_Y, 0),
  };
  const cubeLabelWorldPosition = new THREE.Vector3(0, CUBE_LABEL_Y, 0);

  function projectToScreen(v: THREE.Vector3): { x: number; y: number } {
    const p = v.clone().project(camera);
    return { x: ((p.x + 1) / 2) * 100, y: ((1 - p.y) / 2) * 100 };
  }

  return {
    cleanup: () => {
      cancelAnimationFrame(rafId);
      resizeObserver.disconnect();
      renderer.dispose();
    },
    getLogoPositions: () => {
      const out: Record<AuthorityKey, { x: number; y: number }> = {
        chancellor: { x: 0, y: 0 }, colleges: { x: 0, y: 0 },
        coe: { x: 0, y: 0 }, edd: { x: 0, y: 0 },
      };
      (Object.keys(logoWorldPositions) as AuthorityKey[]).forEach((k) => {
        out[k] = projectToScreen(logoWorldPositions[k]);
      });
      return out;
    },
    getFormLabelPositions: () => {
      const out: Record<AuthorityKey, { x: number; y: number }> = {
        chancellor: { x: 0, y: 0 }, colleges: { x: 0, y: 0 },
        coe: { x: 0, y: 0 }, edd: { x: 0, y: 0 },
      };
      (Object.keys(formLabelWorldPositions) as AuthorityKey[]).forEach((k) => {
        out[k] = projectToScreen(formLabelWorldPositions[k]);
      });
      return out;
    },
    getCubeLabelPosition: () => projectToScreen(cubeLabelWorldPosition),
  };
}
