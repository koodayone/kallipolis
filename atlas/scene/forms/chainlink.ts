/**
 * Platonic form: Chain Link (two interlocked torus rings)
 * Represents the Partnership node in the Kallipolis ontology.
 *
 * Two torus rings interlocked — each passes through the other's hole.
 * No edge wireframe — clean solid rings.
 */

import * as THREE from "three";
import { createFormMaterial } from "@/scene/engine";

export function createChainlinkForm(color: number): THREE.Group {
  const group = new THREE.Group();
  group.name = "platonic-chainlink";
  const mat = createFormMaterial(color);

  const ringRadius = 0.65;
  const tubeRadius = 0.12;
  const radialSegments = 32;
  const tubularSegments = 64;

  // Ring 1
  const ring1Geo = new THREE.TorusGeometry(ringRadius, tubeRadius, radialSegments, tubularSegments);
  const ring1 = new THREE.Mesh(ring1Geo, mat);
  ring1.position.set(0, -ringRadius / 2 - 0.15, 0);
  group.add(ring1);

  // Ring 2 — rotated 90° around Y, interlocked through Ring 1
  const ring2Geo = new THREE.TorusGeometry(ringRadius, tubeRadius, radialSegments, tubularSegments);
  const ring2 = new THREE.Mesh(ring2Geo, mat);
  ring2.position.set(0, ringRadius / 2 - 0.15, 0);
  ring2.rotation.set(0, Math.PI / 2, 0);
  group.add(ring2);

  // Invisible disc fills for click targets
  const invisMat = new THREE.MeshBasicMaterial({
    opacity: 0,
    transparent: true,
    side: THREE.DoubleSide,
    depthWrite: false,
    colorWrite: false,
  });

  // Fill ring 1's hole
  const fill1 = new THREE.Mesh(new THREE.CircleGeometry(ringRadius, 24), invisMat);
  fill1.position.copy(ring1.position);
  group.add(fill1);

  // Fill ring 2's hole
  const fill2 = new THREE.Mesh(new THREE.CircleGeometry(ringRadius, 24), invisMat);
  fill2.position.copy(ring2.position);
  fill2.rotation.copy(ring2.rotation);
  group.add(fill2);

  return group;
}
