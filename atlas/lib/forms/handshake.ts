/**
 * Platonic form: Handshake (extruded SVG)
 * Represents the Partnership node in the Kallipolis ontology.
 */

import * as THREE from "three";
import { GLTFLoader } from "three/examples/jsm/loaders/GLTFLoader.js";
import { createFormMaterial } from "../sceneEngine";

const loader = new GLTFLoader();

export function createHandshakeForm(color: number): THREE.Group {
  const group = new THREE.Group();
  group.name = "platonic-handshake";

  loader.load("/models/handshake.glb", (gltf) => {
    const mat = createFormMaterial(color);
    mat.side = THREE.DoubleSide;

    // Apply material and tag all meshes
    gltf.scene.traverse((child) => {
      if (child instanceof THREE.Mesh) {
        child.material = mat.clone();
        child.userData.formKey = "partnerships";
      }
    });

    // Center and scale
    const box = new THREE.Box3().setFromObject(gltf.scene);
    const center = box.getCenter(new THREE.Vector3());
    const maxDim = Math.max(...box.getSize(new THREE.Vector3()).toArray());
    const scale = 2.0 / maxDim;

    gltf.scene.position.set(-center.x, -center.y, -center.z);

    const pivot = new THREE.Group();
    pivot.add(gltf.scene);
    pivot.scale.setScalar(scale);
    // Y rotation handled by oscillate in scene config

    group.add(pivot);
  });

  return group;
}
