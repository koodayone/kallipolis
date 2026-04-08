/**
 * Platonic form: Hex Dumbbell
 * Represents the Strong Workforce node in the Kallipolis ontology.
 *
 * Essential properties:
 *   1. Two hex weight heads — each a chamfered hexagonal form
 *      (inner chamfer + wide middle + outer chamfer)
 *   2. Bar — connecting cylinder between the weights
 *
 * Each weight head is composed of three stacked hexagonal frustums:
 *   - Inner chamfer: tapers from bar radius up to full weight radius
 *   - Middle body: full-width hexagonal prism
 *   - Outer chamfer: tapers from full weight radius down to the flat end face
 */

import * as THREE from "three";
import { addWithEdges, createFormMaterial } from "../sceneEngine";

export function createDumbbellForm(color: number): THREE.Group {
  const group = new THREE.Group();
  group.name = "platonic-dumbbell";
  const mat = createFormMaterial(color);

  const barLength = 1.35;
  const barRadius = 0.0825;
  const weightRadius = 0.48;
  const endFaceRadius = 0.39;
  const innerChamferHeight = 0.15;
  const bodyHeight = 0.35;
  const outerChamferHeight = 0.15;
  const totalWeightHeight = innerChamferHeight + bodyHeight + outerChamferHeight;

  // 1. Bar — horizontal connecting cylinder
  const barGeo = new THREE.CylinderGeometry(barRadius, barRadius, barLength, 8);
  addWithEdges(
    group, barGeo, mat,
    new THREE.Vector3(0, 0, 0),
    new THREE.Euler(0, 0, Math.PI / 2)
  );

  // Helper: build one weight head at a given X position
  // direction: 1 = right side, -1 = left side
  function addWeightHead(xCenter: number, direction: number) {
    const baseX = xCenter - direction * totalWeightHeight / 2;

    // All cylinders rotated to lay along X axis with consistent orientation
    // CylinderGeometry(topRadius, bottomRadius) — "top" faces +Y before rotation
    // Euler(0, 0, PI/2) rotates +Y to +X, so "top" faces +X
    // Euler(0, 0, -PI/2) rotates +Y to -X, so "top" faces -X

    const rot = new THREE.Euler(0, 0, direction === 1 ? Math.PI / 2 : -Math.PI / 2);

    // Inner chamfer — small face toward bar, wide face toward body
    // "top" = toward bar (small), "bottom" = toward body (wide)
    const innerGeo = new THREE.CylinderGeometry(barRadius * 2.5, weightRadius, innerChamferHeight, 6);
    addWithEdges(
      group, innerGeo, mat,
      new THREE.Vector3(baseX + direction * innerChamferHeight / 2, 0, 0),
      rot
    );

    // Middle body — full-width hex prism
    const bodyGeo = new THREE.CylinderGeometry(weightRadius, weightRadius, bodyHeight, 6);
    addWithEdges(
      group, bodyGeo, mat,
      new THREE.Vector3(baseX + direction * (innerChamferHeight + bodyHeight / 2), 0, 0),
      rot
    );

    // Outer chamfer — wide face toward body, small face toward outside
    // "top" = toward body (wide), "bottom" = toward outside (small)
    const outerGeo = new THREE.CylinderGeometry(weightRadius, endFaceRadius, outerChamferHeight, 6);
    addWithEdges(
      group, outerGeo, mat,
      new THREE.Vector3(baseX + direction * (innerChamferHeight + bodyHeight + outerChamferHeight / 2), 0, 0),
      rot
    );
  }

  // 2. Left weight head
  addWeightHead(-barLength / 2, -1);

  // 3. Right weight head
  addWeightHead(barLength / 2, 1);

  return group;
}
