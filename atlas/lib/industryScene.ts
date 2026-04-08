import * as THREE from "three";
import { buildScene, createPrimitiveForm } from "./sceneEngine";
import { createChainlinkForm } from "./forms/chainlink";
import { createHardhatForm } from "./forms/hardhat";
import { createSkyscraperForm } from "./forms/skyscraper";
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
      factory: createHardhatForm,
      position: new THREE.Vector3(0, 0, 0),
      rotSpeed: new THREE.Vector3(0.002, 0.0028, 0.0015),
    },
    {
      key: "employers",
      factory: createSkyscraperForm,
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
