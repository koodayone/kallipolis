/**
 * Platonic form: Chain Link (two interlocked torus rings)
 * Represents the Partnership node in the Kallipolis ontology.
 *
 * Two torus rings interlocked — each passes through the other's hole.
 * No edge wireframe — clean solid rings.
 */

import * as THREE from "three";
import { createFormMaterial } from "../sceneEngine";

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

  return group;
}
