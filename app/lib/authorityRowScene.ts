/**
 * Single-row epistemology scene: one platonic form connected by a gold
 * cylinder to a data authority endpoint. Used per-authority on the
 * Explore Sources page.
 */

import * as THREE from "three";

const GOLD = 0xc9a84c;
const BG_COLOR = 0x060d1f;
const FORM_SCALE = 2.0;

export type AuthorityRowResult = {
  cleanup: () => void;
  getEndpointPosition: () => { x: number; y: number };
  getFormPosition: () => { x: number; y: number };
};

export function buildAuthorityRowScene(
  canvas: HTMLCanvasElement,
  factory: (color: number) => THREE.Group,
): AuthorityRowResult {
  const rect = canvas.getBoundingClientRect();
  const width = rect.width || canvas.clientWidth || 600;
  const height = rect.height || canvas.clientHeight || 120;

  const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.setSize(width, height, false);
  renderer.setClearColor(BG_COLOR, 0);

  const scene = new THREE.Scene();

  const camera = new THREE.PerspectiveCamera(50, width / height, 0.1, 100);
  camera.position.set(0, 0.5, 12);

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

  // Form — left side
  const formX = -8.0;
  const endX = 5.0;
  const group = factory(GOLD);
  group.position.set(formX, 0, 0);
  group.scale.setScalar(FORM_SCALE);
  scene.add(group);

  // Connector materials
  const connectorMat = new THREE.MeshPhongMaterial({
    color: GOLD, emissive: GOLD, emissiveIntensity: 0.8,
    transparent: true, opacity: 0.7,
  });
  const glowMat = new THREE.MeshPhongMaterial({
    color: GOLD, emissive: GOLD, emissiveIntensity: 0.4,
    transparent: true, opacity: 0.12,
  });
  const junctionMat = new THREE.MeshPhongMaterial({
    color: GOLD, emissive: GOLD, emissiveIntensity: 1.0,
    transparent: true, opacity: 0.85,
  });

  // Connector
  const startX = formX + 2.8;
  const connEndX = endX - 0.5;
  const length = connEndX - startX;
  const midX = startX + length / 2;

  const cylGeo = new THREE.CylinderGeometry(0.035, 0.035, length, 8);
  const cyl = new THREE.Mesh(cylGeo, connectorMat);
  cyl.position.set(midX, 0, 0);
  cyl.rotation.z = Math.PI / 2;
  scene.add(cyl);

  const glowGeo = new THREE.CylinderGeometry(0.1, 0.1, length, 8);
  const glowCyl = new THREE.Mesh(glowGeo, glowMat);
  glowCyl.position.set(midX, 0, 0);
  glowCyl.rotation.z = Math.PI / 2;
  scene.add(glowCyl);

  // Junction spheres
  const junctionGeo = new THREE.SphereGeometry(0.07, 8, 8);
  const jStart = new THREE.Mesh(junctionGeo, junctionMat);
  jStart.position.set(startX, 0, 0);
  scene.add(jStart);
  const jEnd = new THREE.Mesh(junctionGeo, junctionMat);
  jEnd.position.set(connEndX, 0, 0);
  scene.add(jEnd);

  // Point lights — more spread for richer glow
  const glowLights: THREE.PointLight[] = [];
  for (let i = 0; i < 4; i++) {
    const t = (i + 0.5) / 4;
    const lx = startX + t * length;
    const light = new THREE.PointLight(GOLD, 0.4, 4);
    light.position.set(lx, 0, 0.8);
    scene.add(light);
    glowLights.push(light);
  }

  // Traveling pulse light
  const pulseLight = new THREE.PointLight(GOLD, 0.8, 3);
  pulseLight.position.set(startX, 0, 1.2);
  scene.add(pulseLight);

  // Endpoint position for logo overlay
  const endPos = new THREE.Vector3(endX, 0, 0);

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

    group.rotation.x += 0.002;
    group.rotation.y += 0.0028;
    group.rotation.z += 0.0012;

    // Glow halo shimmer — richer range
    glowMat.opacity = 0.1 + 0.1 * Math.sin(elapsed * 1.8);

    // Core connector pulse
    connectorMat.opacity = 0.55 + 0.2 * Math.sin(elapsed * 2.2);
    connectorMat.emissiveIntensity = 0.7 + 0.3 * Math.sin(elapsed * 1.5);

    // Traveling pulse — moves from form to endpoint
    const pulseT = (Math.sin(elapsed * 0.8) + 1) / 2; // 0 → 1 → 0
    pulseLight.position.x = startX + pulseT * length;
    pulseLight.intensity = 0.5 + 0.5 * Math.sin(elapsed * 1.2);

    // Staggered glow light shimmer
    for (let i = 0; i < glowLights.length; i++) {
      glowLights[i].intensity = 0.3 + 0.25 * Math.sin(elapsed * 1.6 + i * 0.8);
    }

    renderer.render(scene, camera);
  }
  tick();

  return {
    cleanup: () => {
      cancelAnimationFrame(rafId);
      resizeObserver.disconnect();
      renderer.dispose();
    },
    getEndpointPosition: () => {
      const p = endPos.clone();
      p.project(camera);
      return {
        x: ((p.x + 1) / 2) * 100,
        y: ((1 - p.y) / 2) * 100,
      };
    },
    getFormPosition: () => {
      const p = new THREE.Vector3(formX, 0, 0);
      p.project(camera);
      return {
        x: ((p.x + 1) / 2) * 100,
        y: ((1 - p.y) / 2) * 100,
      };
    },
  };
}
