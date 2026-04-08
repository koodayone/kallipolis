/**
 * Platonic form: Hard Hat
 * Represents the Occupation node in the Kallipolis ontology.
 * Source: handshake3.blend
 */

import * as THREE from "three";
import { GLTFLoader } from "three/examples/jsm/loaders/GLTFLoader.js";
import { createFormMaterial } from "../sceneEngine";

const loader = new GLTFLoader();

export function createHardhatForm(color: number): THREE.Group {
  const group = new THREE.Group();
  group.name = "platonic-hardhat";

  loader.load("/models/hardhat.glb", (gltf) => {
    const mat = createFormMaterial(color);
    const edgeMat = new THREE.LineBasicMaterial({
      color: 0xffffff,
      transparent: true,
      opacity: 0.8,
    });

    gltf.scene.traverse((child) => {
      if (child instanceof THREE.Mesh) {
        const childMat = mat.clone();
        childMat.side = THREE.DoubleSide;
        child.material = childMat;
        child.userData.formKey = "occupations";

        const edges = new THREE.LineSegments(
          new THREE.EdgesGeometry(child.geometry, 15),
          edgeMat.clone()
        );
        child.add(edges);
      }
    });

    const box = new THREE.Box3().setFromObject(gltf.scene);
    const center = box.getCenter(new THREE.Vector3());
    const size = box.getSize(new THREE.Vector3());
    const maxDim = Math.max(size.x, size.y, size.z);
    const scale = 2.0 / maxDim;

    const pivot = new THREE.Group();
    pivot.add(gltf.scene);
    gltf.scene.position.set(-center.x, -center.y, -center.z);
    pivot.scale.setScalar(scale);
    pivot.rotation.x = Math.PI / 2;

    group.add(pivot);
  });

  return group;
}
