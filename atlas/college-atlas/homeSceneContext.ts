"use client";

import { createContext, useContext } from "react";

export type ProjectedPosition = { x: number; y: number };

export type HomeSceneState = {
  projectedPositions: Record<string, ProjectedPosition>;
};

export const HomeSceneContext = createContext<HomeSceneState>({
  projectedPositions: {},
});

export function useHomeSceneContext(): HomeSceneState {
  return useContext(HomeSceneContext);
}
