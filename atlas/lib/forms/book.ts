/**
 * Platonic form: Book (open)
 * Represents the Course node in the Kallipolis ontology.
 *
 * Essential properties:
 *   1. Two cover planes — angled slightly open from the spine
 *   2. Spine — vertical edge where the covers hinge
 *   3. Page block — layered block between the covers, slightly recessed
 */

import * as THREE from "three";
import { addWithEdges, createFormMaterial } from "../sceneEngine";

export function createBookForm(color: number): THREE.Group {
  const group = new THREE.Group();
  group.name = "platonic-book";
  const mat = createFormMaterial(color);

  const coverWidth = 1.05;
  const coverHeight = 1.35;
  const coverThickness = 0.06;
  const openAngle = 0.25; // radians — how far each cover opens from center

  // 1. Left cover
  const leftCoverGeo = new THREE.BoxGeometry(coverWidth, coverHeight, coverThickness);
  addWithEdges(
    group, leftCoverGeo, mat,
    new THREE.Vector3(-coverWidth / 2 * Math.cos(openAngle), 0, -coverWidth / 2 * Math.sin(openAngle)),
    new THREE.Euler(0, openAngle, 0)
  );

  // 2. Right cover
  const rightCoverGeo = new THREE.BoxGeometry(coverWidth, coverHeight, coverThickness);
  addWithEdges(
    group, rightCoverGeo, mat,
    new THREE.Vector3(coverWidth / 2 * Math.cos(openAngle), 0, -coverWidth / 2 * Math.sin(openAngle)),
    new THREE.Euler(0, -openAngle, 0)
  );

  // 3. Page block — slightly smaller than covers, recessed between them
  const pageWidth = coverWidth * 0.88;
  const pageHeight = coverHeight * 0.92;
  const pageDepth = 0.225;

  // 4. Spine — thin binding strip at the hinge, flush with covers
  const spineDepth = pageDepth;
  const spineGeo = new THREE.BoxGeometry(0.03, coverHeight, spineDepth);
  addWithEdges(group, spineGeo, mat, new THREE.Vector3(0, 0, -coverWidth * Math.sin(openAngle) * 0.65));
  const pageGeo = new THREE.BoxGeometry(pageWidth, pageHeight, pageDepth);

  // Left page block
  addWithEdges(
    group, pageGeo, mat,
    new THREE.Vector3(-pageWidth / 2 * Math.cos(openAngle), 0, -pageWidth / 2 * Math.sin(openAngle)),
    new THREE.Euler(0, openAngle, 0)
  );

  // Right page block
  const pageGeo2 = new THREE.BoxGeometry(pageWidth, pageHeight, pageDepth);
  addWithEdges(
    group, pageGeo2, mat,
    new THREE.Vector3(pageWidth / 2 * Math.cos(openAngle), 0, -pageWidth / 2 * Math.sin(openAngle)),
    new THREE.Euler(0, -openAngle, 0)
  );

  group.scale.setScalar(1);
  return group;
}
