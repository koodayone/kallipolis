/**
 * Renders a single platonic form centered in a canvas.
 *
 * Stripped-down version of atlasPreviewScene — one form, ambient rotation,
 * no interactivity, no raycasting. Used by FormCard on the Explore Atlas page.
 */

import * as THREE from "three";

const BG_COLOR = 0x060d1f;
const DEFAULT_COLOR = 0xf0425e;

export type SingleFormResult = {
  cleanup: () => void;
};

export function buildSingleFormScene(
  canvas: HTMLCanvasElement,
  factory: (color: number) => THREE.Group,
  color: number = DEFAULT_COLOR,
): SingleFormResult {
  const rect = canvas.getBoundingClientRect();
  const width = rect.width || canvas.clientWidth || 200;
  const height = rect.height || canvas.clientHeight || 200;

  const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.setSize(width, height, false);
  renderer.setClearColor(BG_COLOR, 0);

  const scene = new THREE.Scene();

  const camera = new THREE.PerspectiveCamera(40, width / height, 0.1, 50);
  camera.position.set(0, 0, 5);

  // Lighting — matches atlas scenes
  scene.add(new THREE.AmbientLight(0xffffff, 0.08));
  const keyLight = new THREE.DirectionalLight(color, 0.5);
  keyLight.position.set(5, 8, 4);
  scene.add(keyLight);
  const rimLight = new THREE.DirectionalLight(0x2244aa, 0.25);
  rimLight.position.set(-4, -2, -6);
  scene.add(rimLight);
  const fillLight = new THREE.DirectionalLight(0xffffff, 0.12);
  fillLight.position.set(0, 5, 8);
  scene.add(fillLight);

  const group = factory(color);
  group.scale.setScalar(1.2);
  scene.add(group);

  // Resize
  const resizeObserver = new ResizeObserver((obs) => {
    const entry = obs[0];
    const w = entry.contentRect.width;
    const h = entry.contentRect.height;
    if (w === 0 || h === 0) return;
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
    renderer.setSize(w, h, false);
  });
  resizeObserver.observe(canvas);

  // Animation
  let rafId = 0;

  function tick() {
    rafId = requestAnimationFrame(tick);
    group.rotation.x += 0.0018;
    group.rotation.y += 0.0025;
    group.rotation.z += 0.001;
    renderer.render(scene, camera);
  }
  tick();

  return {
    cleanup: () => {
      cancelAnimationFrame(rafId);
      resizeObserver.disconnect();
      renderer.dispose();
    },
  };
}
