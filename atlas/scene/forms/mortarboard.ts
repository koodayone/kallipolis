/**
 * Platonic form: Mortarboard (graduation cap)
 * Represents the Student node in the Kallipolis ontology.
 *
 * Essential properties:
 *   1. Flat square board (the defining feature)
 *   2. Cylindrical skull cap (truncated, sits below the board)
 *   3. Tassel button (small sphere at center of board)
 *   4. Tassel cord (thin cylinder hanging from button)
 */

import * as THREE from "three";
import { addWithEdges, createFormMaterial } from "../sceneEngine";

export function createMortarboardForm(color: number): THREE.Group {
  const group = new THREE.Group();
  group.name = "platonic-mortarboard";
  const mat = createFormMaterial(color);

  // 1. Flat square board — the defining silhouette
  const boardGeo = new THREE.BoxGeometry(1.53, 0.077, 1.53);
  addWithEdges(group, boardGeo, mat, new THREE.Vector3(0, 0.281, 0));

  // 2. Skull cap — truncated hexagonal cylinder
  const capGeo = new THREE.CylinderGeometry(0.523, 0.612, 0.255, 6);
  addWithEdges(group, capGeo, mat, new THREE.Vector3(0, 0.102, 0));

  // 3. Tassel button — small sphere at center top of board
  const buttonGeo = new THREE.SphereGeometry(0.089, 8, 6);
  addWithEdges(group, buttonGeo, mat, new THREE.Vector3(0, 0.37, 0));

  // 4. Tassel horizontal cord — runs across the top of the board from button to edge
  const cordLength = 0.765;
  const cordGeo = new THREE.CylinderGeometry(0.026, 0.026, cordLength, 4);
  addWithEdges(
    group, cordGeo, mat,
    new THREE.Vector3(cordLength / 2, 0.344, 0),
    new THREE.Euler(0, 0, Math.PI / 2)
  );

  // 5. Tassel vertical drop — falls from where the horizontal cord ends
  const dropStart = 0.344;
  const tasselLen = 0.638;
  const tasselGeo = new THREE.CylinderGeometry(0.026, 0.026, tasselLen, 4);
  addWithEdges(
    group, tasselGeo, mat,
    new THREE.Vector3(0.765, dropStart - tasselLen / 2, 0)
  );

  // 6. Tassel end — small weighted tip at the bottom
  const tasselEndGeo = new THREE.SphereGeometry(0.089, 6, 4);
  addWithEdges(group, tasselEndGeo, mat, new THREE.Vector3(0.765, dropStart - tasselLen, 0));

  group.position.y = -0.128;
  return group;
}
