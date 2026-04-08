import * as THREE from "three";
import { buildScene, createPrimitiveForm } from "./sceneEngine";
import { createChainlinkForm } from "./forms/chainlink";
import type { SceneConfig } from "./sceneEngine";

export type IndustryNodeKey = "partnerships" | "occupations" | "employers";

export type IndustrySceneCallbacks = {
  onNodeClick: (node: IndustryNodeKey) => void;
  onHoverChange: (node: IndustryNodeKey | null) => void;
  solidColor: number;
};

const config: SceneConfig<IndustryNodeKey> = {
  forms: [
    {
      key: "partnerships",
      factory: createChainlinkForm,
      position: new THREE.Vector3(-3.2, 0, 0),
      rotSpeed: new THREE.Vector3(0.0018, 0.0025, 0.001),
    },
    {
      key: "occupations",
      factory: (color: number) => createPrimitiveForm(new THREE.TetrahedronGeometry(0.95, 0), color),
      position: new THREE.Vector3(0, 0, 0),
      rotSpeed: new THREE.Vector3(0.002, 0.0028, 0.0015),
    },
    {
      key: "employers",
      factory: (color: number) => createPrimitiveForm(new THREE.DodecahedronGeometry(0.85, 0), color),
      position: new THREE.Vector3(3.2, 0, 0),
      rotSpeed: new THREE.Vector3(0.0015, 0.002, 0.0018),
    },
  ],
  camera: { position: new THREE.Vector3(0, 0, 5.5), fov: 50 },
  ambientIntensity: 0.5,
};

export function buildIndustryScene(
  canvas: HTMLCanvasElement,
  callbacks: IndustrySceneCallbacks
): {
  cleanup: () => void;
  resetScene: () => void;
} {
  return buildScene<IndustryNodeKey>(canvas, config, {
    onClick: callbacks.onNodeClick,
    onHoverChange: callbacks.onHoverChange,
    solidColor: callbacks.solidColor,
  });
}
