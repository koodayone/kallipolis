import * as THREE from "three";
import { buildScene } from "@/scene/engine";
import { createMortarboardForm } from "@/scene/forms/mortarboard";
import { createBookForm } from "@/scene/forms/book";
import { createChainlinkForm } from "@/scene/forms/chainlink";
import { createHardhatForm } from "@/scene/forms/hardhat";
import { createSkyscraperForm } from "@/scene/forms/skyscraper";
import { createDumbbellForm } from "@/scene/forms/dumbbell";
import type { SceneConfig } from "@/scene/engine";

export type FormKey =
  | "students"
  | "courses"
  | "partnerships"
  | "occupations"
  | "employers"
  | "strong_workforce";

export type SceneCallbacks = {
  onFormClick: (form: FormKey) => void;
  onHoverChange: (form: FormKey | null) => void;
  solidColor: number;
};

export const FORM_NAMES: Record<FormKey, string> = {
  students: "Students",
  courses: "Courses",
  partnerships: "Partnerships",
  occupations: "Occupations",
  employers: "Employers",
  strong_workforce: "Strong Workforce",
};

export const ALL_FORM_KEYS: FormKey[] = [
  "students", "partnerships", "employers",
  "courses", "strong_workforce", "occupations",
];

const config: SceneConfig<FormKey> = {
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
      key: "strong_workforce",
      factory: createDumbbellForm,
      position: new THREE.Vector3(0, -2.1, 0),
      rotSpeed: new THREE.Vector3(0.0018, 0.0025, 0.001),
    },
    {
      key: "occupations",
      factory: createHardhatForm,
      position: new THREE.Vector3(4.2, -2.1, 0),
      rotSpeed: new THREE.Vector3(0.002, 0.0028, 0.0012),
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
  setPaused: (paused: boolean) => void;
} {
  return buildScene<FormKey>(canvas, config, {
    onClick: callbacks.onFormClick,
    onHoverChange: callbacks.onHoverChange,
    solidColor: callbacks.solidColor,
  });
}
