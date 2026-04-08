import * as THREE from "three";
import { buildScene, createPrimitiveForm } from "./sceneEngine";
import { createDumbbellForm } from "./forms/dumbbell";
import type { SceneConfig } from "./sceneEngine";

export type GovReportKey = "strong_workforce" | "perkins_v";

export type GovSceneCallbacks = {
  onReportClick: (report: GovReportKey) => void;
  onHoverChange: (report: GovReportKey | null) => void;
  solidColor: number;
};

const config: SceneConfig<GovReportKey> = {
  forms: [
    {
      key: "strong_workforce",
      factory: createDumbbellForm,
      position: new THREE.Vector3(-1.8, 0, 0),
      rotSpeed: new THREE.Vector3(0.0018, 0.0025, 0.001),
    },
    {
      key: "perkins_v",
      factory: (color: number) => createPrimitiveForm(new THREE.OctahedronGeometry(1.1, 0), color),
      position: new THREE.Vector3(1.8, 0, 0),
      rotSpeed: new THREE.Vector3(0.001, 0.003, 0.002),
    },
  ],
  camera: { position: new THREE.Vector3(0, 0, 5.5), fov: 50 },
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
