import * as THREE from "three";
import { buildScene } from "./sceneEngine";
import { createMortarboardForm } from "./forms/mortarboard";
import { createBookForm } from "./forms/book";
import { createChainlinkForm } from "./forms/chainlink";
import { createHardhatForm } from "./forms/hardhat";
import { createSkyscraperForm } from "./forms/skyscraper";
import { createDumbbellForm } from "./forms/dumbbell";
import type { SceneConfig } from "./sceneEngine";

export type AtlasNodeKey =
  | "students"
  | "courses"
  | "partnerships"
  | "occupations"
  | "employers"
  | "strong_workforce";

export type SceneCallbacks = {
  onNodeClick: (node: AtlasNodeKey) => void;
  onHoverChange: (node: AtlasNodeKey | null) => void;
  solidColor: number;
};

export const NODE_NAMES: Record<AtlasNodeKey, string> = {
  students: "Students",
  courses: "Courses",
  partnerships: "Partnerships",
  occupations: "Occupations",
  employers: "Employers",
  strong_workforce: "Strong Workforce",
};

export const ALL_NODE_KEYS: AtlasNodeKey[] = [
  "students", "partnerships", "employers",
  "courses", "occupations", "strong_workforce",
];

const config: SceneConfig<AtlasNodeKey> = {
  forms: [
    // Top row
    {
      key: "students",
      factory: createMortarboardForm,
      position: new THREE.Vector3(-4.2, 1.9, 0),
      rotSpeed: new THREE.Vector3(0.0018, 0.0025, 0.001),
    },
    {
      key: "partnerships",
      factory: createChainlinkForm,
      position: new THREE.Vector3(0, 1.9, 0),
      rotSpeed: new THREE.Vector3(0.0018, 0.0025, 0.001),
    },
    {
      key: "employers",
      factory: createSkyscraperForm,
      position: new THREE.Vector3(4.2, 1.9, 0),
      rotSpeed: new THREE.Vector3(0.0015, 0.002, 0.0018),
    },
    // Bottom row
    {
      key: "courses",
      factory: createBookForm,
      position: new THREE.Vector3(-4.2, -2.1, 0),
      rotSpeed: new THREE.Vector3(0.0015, 0.002, 0.001),
    },
    {
      key: "occupations",
      factory: createHardhatForm,
      position: new THREE.Vector3(0, -2.1, 0),
      rotSpeed: new THREE.Vector3(0.002, 0.0028, 0.0012),
    },
    {
      key: "strong_workforce",
      factory: createDumbbellForm,
      position: new THREE.Vector3(4.2, -2.1, 0),
      rotSpeed: new THREE.Vector3(0.0018, 0.0025, 0.001),
    },
  ],
  camera: { position: new THREE.Vector3(0, -0.15, 11), fov: 50 },
  ambientIntensity: 0.08,
  clearAlpha: 1,
  fog: { density: 0.015 },
};

export function buildAtlasScene(
  canvas: HTMLCanvasElement,
  callbacks: SceneCallbacks
): {
  cleanup: () => void;
  resetScene: () => void;
  getProjectedPositions: () => Record<string, { x: number; y: number }>;
} {
  return buildScene<AtlasNodeKey>(canvas, config, {
    onClick: callbacks.onNodeClick,
    onHoverChange: callbacks.onHoverChange,
    solidColor: callbacks.solidColor,
  });
}
