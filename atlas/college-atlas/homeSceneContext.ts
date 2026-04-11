"use client";

import { createContext, useContext } from "react";
import type { FormKey } from "@/college-atlas/scene";

export type ProjectedPosition = { x: number; y: number };

export type HomeSceneState = {
  projectedPositions: Record<string, ProjectedPosition>;
  hoveredForm: FormKey | null;
  setHoveredForm: (form: FormKey | null) => void;
};

export const HomeSceneContext = createContext<HomeSceneState>({
  projectedPositions: {},
  hoveredForm: null,
  setHoveredForm: () => {},
});

export function useHomeSceneContext(): HomeSceneState {
  return useContext(HomeSceneContext);
}
