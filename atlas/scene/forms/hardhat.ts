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
  const brimGeo = new THREE.TorusGeometry(0.80, 0.10, 12, 48);
  const brimMesh = new THREE.Mesh(brimGeo, mat);
  brimMesh.rotation.x = Math.PI / 2;
  brimMesh.scale.set(0.9, 1.15, 1.0);
  group.add(brimMesh);

  // 3. Reinforcement ridges — thin torus arcs across the dome
  const ridgeRadius = 0.75;
  const ridgeTube = 0.004;
  const ridgeSegments = 32;

  const ridgeMat = new THREE.MeshBasicMaterial({
    color: 0xffffff,
    transparent: true,
    opacity: 0.15,
  });

  // Center ridge
  const centerRidgeGeo = new THREE.TorusGeometry(ridgeRadius, ridgeTube, 4, ridgeSegments, Math.PI);
  const centerRidge = new THREE.Mesh(centerRidgeGeo, ridgeMat);
  centerRidge.rotation.set(0, Math.PI / 2, 0);
  centerRidge.scale.set(1.15, 1.1, 0.9);
  group.add(centerRidge);

  // Left ridge
  const leftRidgeGeo = new THREE.TorusGeometry(ridgeRadius, ridgeTube, 4, ridgeSegments, Math.PI);
  const leftRidge = new THREE.Mesh(leftRidgeGeo, ridgeMat);
  leftRidge.rotation.set(0, Math.PI / 2, 0);
  leftRidge.position.x = -0.22;
  leftRidge.scale.set(1.1, 1.05, 0.8);
  group.add(leftRidge);

  // Right ridge
  const rightRidgeGeo = new THREE.TorusGeometry(ridgeRadius, ridgeTube, 4, ridgeSegments, Math.PI);
  const rightRidge = new THREE.Mesh(rightRidgeGeo, ridgeMat);
  rightRidge.rotation.set(0, Math.PI / 2, 0);
  rightRidge.position.x = 0.22;
  rightRidge.scale.set(1.1, 1.05, 0.8);
  group.add(rightRidge);

  // Invisible base disc — makes the empty space under the dome clickable
  const baseGeo = new THREE.CircleGeometry(0.7, 24);
  const baseMat = new THREE.MeshBasicMaterial({
    opacity: 0,
    transparent: true,
    side: THREE.DoubleSide,
    depthWrite: false,
    colorWrite: false,
  });
  const baseMesh = new THREE.Mesh(baseGeo, baseMat);
  baseMesh.rotation.x = -Math.PI / 2;
  baseMesh.position.y = 0;
  group.add(baseMesh);

  group.position.y = -0.15;

  return group;
}
