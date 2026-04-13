/**
 * Shared platonic-form factories used by the landing page Three.js scenes.
 *
 * Canonical implementations — each scene imports from here instead of
 * maintaining its own copy.
 */

import * as THREE from "three";

// ── Shared helpers ───────────────────────────────────────────────────────────

export function createFormMaterial(color: number): THREE.MeshPhongMaterial {
  return new THREE.MeshPhongMaterial({
    color,
    emissive: color,
    emissiveIntensity: 0.45,
    transparent: false,
    side: THREE.FrontSide,
    depthWrite: true,
  });
}

export function addWithEdges(
  group: THREE.Group,
  geometry: THREE.BufferGeometry,
  material: THREE.Material,
  position?: THREE.Vector3,
  rotation?: THREE.Euler
): void {
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

// ── Form factories ───────────────────────────────────────────────────────────

export function createMortarboardForm(color: number): THREE.Group {
  const group = new THREE.Group();
  group.name = "platonic-mortarboard";
  const mat = createFormMaterial(color);

  const boardGeo = new THREE.BoxGeometry(1.53, 0.077, 1.53);
  addWithEdges(group, boardGeo, mat, new THREE.Vector3(0, 0.281, 0));

  const capGeo = new THREE.CylinderGeometry(0.523, 0.612, 0.255, 6);
  addWithEdges(group, capGeo, mat, new THREE.Vector3(0, 0.102, 0));

  const buttonGeo = new THREE.SphereGeometry(0.089, 8, 6);
  addWithEdges(group, buttonGeo, mat, new THREE.Vector3(0, 0.37, 0));

  const cordLength = 0.765;
  const cordGeo = new THREE.CylinderGeometry(0.026, 0.026, cordLength, 4);
  addWithEdges(group, cordGeo, mat, new THREE.Vector3(cordLength / 2, 0.344, 0), new THREE.Euler(0, 0, Math.PI / 2));

  const tasselLen = 0.638;
  const tasselGeo = new THREE.CylinderGeometry(0.026, 0.026, tasselLen, 4);
  addWithEdges(group, tasselGeo, mat, new THREE.Vector3(0.765, 0.344 - tasselLen / 2, 0));

  const tasselEndGeo = new THREE.SphereGeometry(0.089, 6, 4);
  addWithEdges(group, tasselEndGeo, mat, new THREE.Vector3(0.765, 0.344 - tasselLen, 0));

  group.position.y = -0.128;
  return group;
}

export function createBookForm(color: number): THREE.Group {
  const group = new THREE.Group();
  group.name = "platonic-book";
  const mat = createFormMaterial(color);

  const coverWidth = 1.05;
  const coverHeight = 1.35;
  const coverThickness = 0.06;
  const openAngle = 0.25;

  const leftCoverGeo = new THREE.BoxGeometry(coverWidth, coverHeight, coverThickness);
  addWithEdges(group, leftCoverGeo, mat,
    new THREE.Vector3(-coverWidth / 2 * Math.cos(openAngle), 0, -coverWidth / 2 * Math.sin(openAngle)),
    new THREE.Euler(0, openAngle, 0));

  const rightCoverGeo = new THREE.BoxGeometry(coverWidth, coverHeight, coverThickness);
  addWithEdges(group, rightCoverGeo, mat,
    new THREE.Vector3(coverWidth / 2 * Math.cos(openAngle), 0, -coverWidth / 2 * Math.sin(openAngle)),
    new THREE.Euler(0, -openAngle, 0));

  const pageWidth = coverWidth * 0.88;
  const pageHeight = coverHeight * 0.92;
  const pageDepth = 0.225;

  const spineGeo = new THREE.BoxGeometry(0.03, coverHeight, pageDepth);
  addWithEdges(group, spineGeo, mat, new THREE.Vector3(0, 0, -coverWidth * Math.sin(openAngle) * 0.65));

  const pageGeo = new THREE.BoxGeometry(pageWidth, pageHeight, pageDepth);
  addWithEdges(group, pageGeo, mat,
    new THREE.Vector3(-pageWidth / 2 * Math.cos(openAngle), 0, -pageWidth / 2 * Math.sin(openAngle)),
    new THREE.Euler(0, openAngle, 0));

  const pageGeo2 = new THREE.BoxGeometry(pageWidth, pageHeight, pageDepth);
  addWithEdges(group, pageGeo2, mat,
    new THREE.Vector3(pageWidth / 2 * Math.cos(openAngle), 0, -pageWidth / 2 * Math.sin(openAngle)),
    new THREE.Euler(0, -openAngle, 0));

  return group;
}

export function createChainlinkForm(color: number): THREE.Group {
  const group = new THREE.Group();
  group.name = "platonic-chainlink";
  const mat = createFormMaterial(color);

  const ringRadius = 0.65;
  const tubeRadius = 0.12;

  const ring1Geo = new THREE.TorusGeometry(ringRadius, tubeRadius, 32, 64);
  const ring1 = new THREE.Mesh(ring1Geo, mat);
  ring1.position.set(0, -ringRadius / 2 - 0.15, 0);
  group.add(ring1);

  const ring2Geo = new THREE.TorusGeometry(ringRadius, tubeRadius, 32, 64);
  const ring2 = new THREE.Mesh(ring2Geo, mat);
  ring2.position.set(0, ringRadius / 2 - 0.15, 0);
  ring2.rotation.set(0, Math.PI / 2, 0);
  group.add(ring2);

  // Invisible disc fills for hover/click targets
  const invisMat = new THREE.MeshBasicMaterial({ opacity: 0, transparent: true, side: THREE.DoubleSide, depthWrite: false, colorWrite: false });
  const fill1 = new THREE.Mesh(new THREE.CircleGeometry(ringRadius, 24), invisMat);
  fill1.position.copy(ring1.position);
  group.add(fill1);
  const fill2 = new THREE.Mesh(new THREE.CircleGeometry(ringRadius, 24), invisMat);
  fill2.position.copy(ring2.position);
  fill2.rotation.copy(ring2.rotation);
  group.add(fill2);

  return group;
}

export function createHardhatForm(color: number): THREE.Group {
  const group = new THREE.Group();
  group.name = "platonic-hardhat";
  const mat = createFormMaterial(color);

  const domeGeo = new THREE.SphereGeometry(0.75, 32, 20, 0, Math.PI * 2, 0, Math.PI / 2);
  const domeMesh = new THREE.Mesh(domeGeo, mat);
  domeMesh.scale.set(0.9, 1.1, 1.15);
  group.add(domeMesh);

  const brimGeo = new THREE.TorusGeometry(0.80, 0.10, 12, 48);
  const brimMesh = new THREE.Mesh(brimGeo, mat);
  brimMesh.rotation.x = Math.PI / 2;
  brimMesh.scale.set(0.9, 1.15, 1.0);
  group.add(brimMesh);

  const ridgeMat = new THREE.MeshBasicMaterial({ color: 0xffffff, transparent: true, opacity: 1.0 });
  const ridgeRadius = 0.75;
  const ridgeTube = 0.012;

  const centerRidgeGeo = new THREE.TorusGeometry(ridgeRadius, ridgeTube, 4, 32, Math.PI);
  const centerRidge = new THREE.Mesh(centerRidgeGeo, ridgeMat);
  centerRidge.rotation.set(0, Math.PI / 2, 0);
  centerRidge.scale.set(1.15, 1.1, 0.9);
  group.add(centerRidge);

  for (const xOff of [-0.22, 0.22]) {
    const ridgeGeo = new THREE.TorusGeometry(ridgeRadius, ridgeTube, 4, 32, Math.PI);
    const ridge = new THREE.Mesh(ridgeGeo, ridgeMat);
    ridge.rotation.set(0, Math.PI / 2, 0);
    ridge.position.x = xOff;
    ridge.scale.set(1.1, 1.05, 0.8);
    group.add(ridge);
  }

  // Invisible base disc for hover target
  const baseMat = new THREE.MeshBasicMaterial({ opacity: 0, transparent: true, side: THREE.DoubleSide, depthWrite: false, colorWrite: false });
  const baseMesh = new THREE.Mesh(new THREE.CircleGeometry(0.7, 24), baseMat);
  baseMesh.rotation.x = -Math.PI / 2;
  group.add(baseMesh);

  group.position.y = -0.15;
  return group;
}

export function createSkyscraperForm(color: number): THREE.Group {
  const group = new THREE.Group();
  group.name = "platonic-skyscraper";
  const mat = createFormMaterial(color);
  mat.side = THREE.DoubleSide;

  const baseW = 0.3;
  const topW = 0.2;
  const baseY = -1.0;
  const midY = 0.0;
  const topY = 1.0;

  const b0: [number, number, number] = [-baseW, baseY, -baseW];
  const b1: [number, number, number] = [baseW, baseY, -baseW];
  const b2: [number, number, number] = [baseW, baseY, baseW];
  const b3: [number, number, number] = [-baseW, baseY, baseW];

  const t0: [number, number, number] = [0, topY, -topW * Math.SQRT2];
  const t1: [number, number, number] = [topW * Math.SQRT2, topY, 0];
  const t2: [number, number, number] = [0, topY, topW * Math.SQRT2];
  const t3: [number, number, number] = [-topW * Math.SQRT2, topY, 0];

  const midScale = 0.85;
  const mb0: [number, number, number] = [-baseW * midScale, midY, -baseW * midScale];
  const mb1: [number, number, number] = [baseW * midScale, midY, -baseW * midScale];
  const mb2: [number, number, number] = [baseW * midScale, midY, baseW * midScale];
  const mb3: [number, number, number] = [-baseW * midScale, midY, baseW * midScale];
  const mt0: [number, number, number] = [0, midY, -topW * Math.SQRT2 * 1.1];
  const mt1: [number, number, number] = [topW * Math.SQRT2 * 1.1, midY, 0];
  const mt2: [number, number, number] = [0, midY, topW * Math.SQRT2 * 1.1];
  const mt3: [number, number, number] = [-topW * Math.SQRT2 * 1.1, midY, 0];

  const allVerts = [
    ...b0, ...b1, ...b2, ...b3,
    ...mb0, ...mt0, ...mb1, ...mt1,
    ...mb2, ...mt2, ...mb3, ...mt3,
    ...t0, ...t1, ...t2, ...t3,
  ];

  const faces = [
    0, 2, 1, 0, 3, 2,
    0, 5, 4, 0, 1, 5, 1, 6, 5,
    1, 7, 6, 1, 2, 7, 2, 8, 7,
    2, 9, 8, 2, 3, 9, 3, 10, 9,
    3, 11, 10, 3, 0, 11, 0, 4, 11,
    4, 5, 12, 5, 6, 12, 6, 13, 12,
    6, 7, 13, 7, 8, 13, 8, 14, 13,
    8, 9, 14, 9, 10, 14, 10, 15, 14,
    10, 11, 15, 11, 4, 15, 4, 12, 15,
    12, 13, 14, 12, 14, 15,
  ];

  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute("position", new THREE.Float32BufferAttribute(allVerts, 3));
  geometry.setIndex(faces);
  geometry.computeVertexNormals();

  group.add(new THREE.Mesh(geometry, mat));

  const edgesGeo = new THREE.EdgesGeometry(geometry, 5);
  const edgeMat = new THREE.LineBasicMaterial({ color: 0xffffff, transparent: true, opacity: 0.7 });
  group.add(new THREE.LineSegments(edgesGeo, edgeMat));

  const spireGeo = new THREE.CylinderGeometry(0.005, 0.025, 0.35, 6);
  const spire = new THREE.Mesh(spireGeo, mat);
  spire.position.y = topY + 0.175;
  group.add(spire);

  return group;
}

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

  const barGeo = new THREE.CylinderGeometry(barRadius, barRadius, barLength, 8);
  addWithEdges(group, barGeo, mat, new THREE.Vector3(0, 0, 0), new THREE.Euler(0, 0, Math.PI / 2));

  function addWeightHead(xCenter: number, direction: number) {
    const baseX = xCenter - direction * totalWeightHeight / 2;
    const rot = new THREE.Euler(0, 0, direction === 1 ? Math.PI / 2 : -Math.PI / 2);

    const innerGeo = new THREE.CylinderGeometry(barRadius * 2.5, weightRadius, innerChamferHeight, 6);
    addWithEdges(group, innerGeo, mat, new THREE.Vector3(baseX + direction * innerChamferHeight / 2, 0, 0), rot);

    const bodyGeo = new THREE.CylinderGeometry(weightRadius, weightRadius, bodyHeight, 6);
    addWithEdges(group, bodyGeo, mat, new THREE.Vector3(baseX + direction * (innerChamferHeight + bodyHeight / 2), 0, 0), rot);

    const outerGeo = new THREE.CylinderGeometry(weightRadius, endFaceRadius, outerChamferHeight, 6);
    addWithEdges(group, outerGeo, mat, new THREE.Vector3(baseX + direction * (innerChamferHeight + bodyHeight + outerChamferHeight / 2), 0, 0), rot);
  }

  addWeightHead(-barLength / 2, -1);
  addWeightHead(barLength / 2, 1);

  return group;
}
