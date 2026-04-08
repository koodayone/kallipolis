import * as THREE from "three";
import { buildScene } from "./sceneEngine";
import { createMortarboardForm } from "./forms/mortarboard";
import { createBookForm } from "./forms/book";
import type { SceneConfig } from "./sceneEngine";

export type CollegeNodeKey = "students" | "courses";

export type CollegeSceneCallbacks = {
  onNodeClick: (node: CollegeNodeKey) => void;
  onHoverChange: (node: CollegeNodeKey | null) => void;
  solidColor: number;
};

const config: SceneConfig<CollegeNodeKey> = {
  forms: [
    {
      key: "students",
      factory: createMortarboardForm,
      position: new THREE.Vector3(-1.8, 0, 0),
      rotSpeed: new THREE.Vector3(0.002, 0.0028, 0.0012),
    },
    {
      key: "courses",
      factory: createBookForm,
      position: new THREE.Vector3(1.8, 0, 0),
      rotSpeed: new THREE.Vector3(0.0015, 0.002, 0.001),
    },
  ],
  camera: { position: new THREE.Vector3(0, 0, 5.5), fov: 50 },
  ambientIntensity: 0.5,
};

export function buildCollegeScene(
  canvas: HTMLCanvasElement,
  callbacks: CollegeSceneCallbacks
): {
  cleanup: () => void;
  resetScene: () => void;
} {
  return buildScene<CollegeNodeKey>(canvas, config, {
    onClick: callbacks.onNodeClick,
    onHoverChange: callbacks.onHoverChange,
    solidColor: callbacks.solidColor,
  });
}
