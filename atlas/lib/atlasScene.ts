import * as THREE from "three";
import { buildScene, createPrimitiveForm } from "./sceneEngine";
import type { SceneConfig } from "./sceneEngine";

export type DomainKey = "government" | "college" | "industry";

export type SceneCallbacks = {
  onDomainClick: (domain: DomainKey) => void;
  onHoverChange: (domain: DomainKey | null) => void;
  solidColor: number;
};

const config: SceneConfig<DomainKey> = {
  forms: [
    {
      key: "government",
      factory: (color: number) => createPrimitiveForm(new THREE.DodecahedronGeometry(1.05, 0), color),
      position: new THREE.Vector3(-3.6, 0, 0),
      rotSpeed: new THREE.Vector3(0.0018, 0.0025, 0.001),
    },
    {
      key: "college",
      factory: (color: number) => createPrimitiveForm(new THREE.BoxGeometry(1.5, 1.5, 1.5), color),
      position: new THREE.Vector3(0, 0, 0),
      rotSpeed: new THREE.Vector3(0.001, 0.004, 0.002),
    },
    {
      key: "industry",
      id: "industry_top",
      factory: (color: number) => createPrimitiveForm(new THREE.TetrahedronGeometry(0.85, 0), color),
      position: new THREE.Vector3(3.6, 1.3, -0.4),
      rotSpeed: new THREE.Vector3(0.003, 0.002, 0.0025),
    },
    {
      key: "industry",
      id: "industry_mid",
      factory: (color: number) => createPrimitiveForm(new THREE.TetrahedronGeometry(0.95, 0), color),
      position: new THREE.Vector3(4.4, 0, 0.2),
      rotSpeed: new THREE.Vector3(0.002, 0.003, 0.002),
    },
    {
      key: "industry",
      id: "industry_bot",
      factory: (color: number) => createPrimitiveForm(new THREE.TetrahedronGeometry(0.85, 0), color),
      position: new THREE.Vector3(3.6, -1.3, -0.4),
      rotSpeed: new THREE.Vector3(0.0025, 0.002, 0.003),
    },
  ],
  connectors: [
    { fromId: "government", toId: "college", triggerKey: "government" },
    { fromId: "college", toId: "industry_top", triggerKey: "industry" },
    { fromId: "college", toId: "industry_mid", triggerKey: "industry" },
    { fromId: "college", toId: "industry_bot", triggerKey: "industry" },
  ],
  camera: { position: new THREE.Vector3(0, 0.4, 9), fov: 50 },
  ambientIntensity: 0.08,
  clearAlpha: 1,
  fog: { density: 0.03 },
  sceneHalfWidth: 5.5,
};

export function buildAtlasScene(
  canvas: HTMLCanvasElement,
  callbacks: SceneCallbacks
): {
  cleanup: () => void;
  resetScene: () => void;
} {
  return buildScene<DomainKey>(canvas, config, {
    onClick: callbacks.onDomainClick,
    onHoverChange: callbacks.onHoverChange,
    solidColor: callbacks.solidColor,
  });
}
