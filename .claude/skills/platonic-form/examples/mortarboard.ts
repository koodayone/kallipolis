/**
 * Platonic form: Mortarboard (graduation cap)
 *
 * Essential properties:
 *   1. Flat square board (the defining feature)
 *   2. Cylindrical skull cap (truncated, sits below the board)
 *   3. Tassel button (small sphere at center of board)
 *   4. Tassel cord (thin cylinder hanging from button)
 *
 * Proportions:
 *   - Board width is ~2.5x the cap diameter
 *   - Cap height is ~0.4x cap diameter
 *   - Board thickness is thin (~0.06 units)
 *   - Tassel hangs to roughly mid-cap height
 */

import * as THREE from "three";

function addWithEdges(
  group: THREE.Group,
  geometry: THREE.BufferGeometry,
  material: THREE.Material,
  position?: THREE.Vector3,
  rotation?: THREE.Euler
) {
  const mesh = new THREE.Mesh(geometry, material);
  if (position) mesh.position.copy(position);
  if (rotation) mesh.rotation.copy(rotation);
  group.add(mesh);

  const edgesGeo = new THREE.EdgesGeometry(geometry, 12);
  const edgeMat = new THREE.LineBasicMaterial({
    color: 0xffffff,
    transparent: true,
    opacity: 0.7,
  });
  const edges = new THREE.LineSegments(edgesGeo, edgeMat);
  if (position) edges.position.copy(position);
  if (rotation) edges.rotation.copy(rotation);
  group.add(edges);
}

export function createMortarboardForm(color: number): THREE.Group {
  const group = new THREE.Group();
  group.name = "platonic-mortarboard";

  const mat = new THREE.MeshPhongMaterial({
    color,
    emissive: color,
    emissiveIntensity: 0.45,
    transparent: false,
    side: THREE.FrontSide,
    depthWrite: true,
  });

  // 1. Flat square board — the defining silhouette
  const boardSize = 1.2;
  const boardThickness = 0.06;
  const boardGeo = new THREE.BoxGeometry(boardSize, boardThickness, boardSize);
  addWithEdges(group, boardGeo, mat, new THREE.Vector3(0, 0.22, 0));

  // 2. Skull cap — truncated cylinder
  const capRadius = 0.48;
  const capHeight = 0.2;
  const capGeo = new THREE.CylinderGeometry(
    capRadius * 0.85, // top radius (slightly narrower)
    capRadius,        // bottom radius
    capHeight,
    6                 // hexagonal for geometric character
  );
  addWithEdges(group, capGeo, mat, new THREE.Vector3(0, 0.08, 0));

  // 3. Tassel button — small sphere at board center
  const buttonGeo = new THREE.SphereGeometry(0.06, 8, 6);
  addWithEdges(group, buttonGeo, mat, new THREE.Vector3(0, 0.28, 0));

  // 4. Tassel cord — thin cylinder hanging from button
  const tasselLength = 0.35;
  const tasselGeo = new THREE.CylinderGeometry(0.015, 0.015, tasselLength, 4);
  addWithEdges(
    group,
    tasselGeo,
    mat,
    new THREE.Vector3(0.25, 0.25 - tasselLength / 2, 0.25),
    new THREE.Euler(0, 0, -0.3) // slight angle — tassels hang, they don't dangle straight
  );

  // Center the group vertically
  group.position.y = -0.1;

  return group;
}
