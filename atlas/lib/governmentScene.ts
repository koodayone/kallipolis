import * as THREE from "three";
import { buildScene } from "./sceneEngine";
import { createMortarboardForm } from "./forms/mortarboard";
import { createBookForm } from "./forms/book";
import { createChainlinkForm } from "./forms/chainlink";
import { createHardhatForm } from "./forms/hardhat";
import { createSkyscraperForm } from "./forms/skyscraper";
import { createDumbbellForm } from "./forms/dumbbell";
import type { SceneConfig } from "./sceneEngine";

export type GovReportKey =
  | "students"
  | "courses"
  | "partnerships"
  | "occupations"
  | "employers"
  | "strong_workforce";

export type GovSceneCallbacks = {
  onReportClick: (report: GovReportKey) => void;
  onHoverChange: (report: GovReportKey | null) => void;
  solidColor: number;
};

const config: SceneConfig<GovReportKey> = {
  forms: [
    // Top row (y = +0.8)
    {
      key: "students",
      factory: createMortarboardForm,
      position: new THREE.Vector3(-4.2, 1.5, 0),
      rotSpeed: new THREE.Vector3(0.0018, 0.0025, 0.001),
    },
    {
      key: "partnerships",
      factory: createChainlinkForm,
      position: new THREE.Vector3(0, 1.5, 0),
      rotSpeed: new THREE.Vector3(0.0018, 0.0025, 0.001),
    },
    {
      key: "employers",
      factory: createSkyscraperForm,
      position: new THREE.Vector3(4.2, 1.5, 0),
      rotSpeed: new THREE.Vector3(0.0015, 0.002, 0.0018),
    },
    // Bottom row (y = -0.8)
    {
      key: "courses",
      factory: createBookForm,
      position: new THREE.Vector3(-4.2, -2.0, 0),
      rotSpeed: new THREE.Vector3(0.0015, 0.002, 0.001),
    },
    {
      key: "occupations",
      factory: createHardhatForm,
      position: new THREE.Vector3(0, -2.0, 0),
      rotSpeed: new THREE.Vector3(0.002, 0.0028, 0.0012),
    },
    {
      key: "strong_workforce",
      factory: createDumbbellForm,
      position: new THREE.Vector3(4.2, -2.0, 0),
      rotSpeed: new THREE.Vector3(0.0018, 0.0025, 0.001),
    },
  ],
  camera: { position: new THREE.Vector3(0, 0.2, 8.5), fov: 50 },
  ambientIntensity: 0.5,
};

export function buildGovernmentScene(
  canvas: HTMLCanvasElement,
  callbacks: GovSceneCallbacks
): {
  cleanup: () => void;
  resetScene: () => void;
} {
  return buildScene<GovReportKey>(canvas, config, {
    onClick: callbacks.onReportClick,
    onHoverChange: callbacks.onHoverChange,
    solidColor: callbacks.solidColor,
  });
}
