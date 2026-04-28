import * as THREE from "three";
import { buildScene } from "@/scene/engine";
import { createMortarboardForm } from "@/scene/forms/mortarboard";
import { createBookForm } from "@/scene/forms/book";
import { createChainlinkForm } from "@/scene/forms/chainlink";
import { createHardhatForm } from "@/scene/forms/hardhat";
import { createSkyscraperForm } from "@/scene/forms/skyscraper";
import type { SceneConfig } from "@/scene/engine";

export type FormKey =
  | "students"
  | "courses"
  | "partnerships"
  | "occupations"
  | "employers";

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
};

export const ALL_FORM_KEYS: FormKey[] = [
  "students", "courses", "partnerships", "occupations", "employers",
];

// URL slugs for each form. Kebab-case to match backend conventions
// and the docs. All five slugs round-trip with their FormKey.
export const FORM_URL_SLUGS: Record<FormKey, string> = {
  students: "students",
  courses: "courses",
  partnerships: "partnerships",
  occupations: "occupations",
  employers: "employers",
};

// Layout: three forms on the top row, two on the bottom row.
//
// Top row (y=+1.9): students — partnerships — employers
//   Partnerships sits at the horizontal center, between the supply-side
//   (students) and demand-side (employers) people, as the unit of action
//   that connects them.
//
// Bottom row (y=-2.1): courses — occupations
//   Tightened to x=±2.1 (vs. the ±4.2 of the top row) so the bottom forms
//   sit centered under the gaps in the top row, producing a slight pyramid
//   distribution rather than two stranded corner forms.
//
// Reading bottom-up: courses + occupations are the curricular and labor-
// market substrates feeding into students + employers, which feed into
// partnerships at the apex.
const config: SceneConfig<FormKey> = {
  forms: [
    // Top row — supply-side person | unit of action | demand-side person
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
    // Bottom row — curricular substrate | labor-market substrate
    {
      key: "courses",
      factory: createBookForm,
      position: new THREE.Vector3(-2.1, -2.1, 0),
      rotSpeed: new THREE.Vector3(0.0015, 0.002, 0.001),
    },
    {
      key: "occupations",
      factory: createHardhatForm,
      position: new THREE.Vector3(2.1, -2.1, 0),
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
  setExternalHover: (form: FormKey | null) => void;
} {
  return buildScene<FormKey>(canvas, config, {
    onClick: callbacks.onFormClick,
    onHoverChange: callbacks.onHoverChange,
    solidColor: callbacks.solidColor,
  });
}
