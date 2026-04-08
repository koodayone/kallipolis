/**
 * Platonic form: Hard Hat
 * Represents the Occupation node in the Kallipolis ontology.
 *
 * Simple and clean: oval dome + full brim ring.
 * No separate visor — the oval shape and brim are enough.
 */

import * as THREE from "three";
import { createFormMaterial } from "../sceneEngine";

export function createHardhatForm(color: number): THREE.Group {
  const group = new THREE.Group();
  group.name = "platonic-hardhat";
  const mat = createFormMaterial(color);

  // 1. Dome — oval hemisphere (elongated front-to-back)
  const domeGeo = new THREE.SphereGeometry(
    0.75, 32, 20,
    0, Math.PI * 2,
    0, Math.PI / 2
  );
  const domeMesh = new THREE.Mesh(domeGeo, mat);
  domeMesh.scale.set(0.9, 1.1, 1.15);
  group.add(domeMesh);

  // 2. Brim — full torus ring around the base, slightly wider than the dome
  const brimGeo = new THREE.TorusGeometry(0.775, 0.05, 12, 48);
  const brimMesh = new THREE.Mesh(brimGeo, mat);
  brimMesh.rotation.x = Math.PI / 2;
  brimMesh.scale.set(0.9, 1.15, 1.0);
  group.add(brimMesh);

  // 3. Reinforcement ridges — arcs running front-to-back across the dome
  const ridgeRadius = 0.76; // slightly larger than dome to sit on surface
  const ridgeTube = 0.007;
  const ridgeSegments = 32;

  const ridgeMat = new THREE.MeshBasicMaterial({
    color: 0xffffff,
    transparent: true,
    opacity: 0.35,
  });

  // Center ridge
  const centerRidgeGeo = new THREE.TorusGeometry(ridgeRadius, ridgeTube, 6, ridgeSegments, Math.PI);
  const centerRidge = new THREE.Mesh(centerRidgeGeo, ridgeMat);
  centerRidge.rotation.set(0, Math.PI / 2, 0);
  centerRidge.scale.set(1.15, 1.1, 0.9);
  group.add(centerRidge);

  // Left ridge
  const leftRidgeGeo = new THREE.TorusGeometry(ridgeRadius, ridgeTube, 6, ridgeSegments, Math.PI);
  const leftRidge = new THREE.Mesh(leftRidgeGeo, ridgeMat);
  leftRidge.rotation.set(0, Math.PI / 2, 0);
  leftRidge.position.x = -0.22;
  leftRidge.scale.set(1.1, 1.05, 0.8);
  group.add(leftRidge);

  // Right ridge
  const rightRidgeGeo = new THREE.TorusGeometry(ridgeRadius, ridgeTube, 6, ridgeSegments, Math.PI);
  const rightRidge = new THREE.Mesh(rightRidgeGeo, ridgeMat);
  rightRidge.rotation.set(0, Math.PI / 2, 0);
  rightRidge.position.x = 0.22;
  rightRidge.scale.set(1.1, 1.05, 0.8);
  group.add(rightRidge);

  group.position.y = -0.15;

  return group;
}
