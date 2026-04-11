/**
 * Platonic form: Skyscraper (One World Trade Center)
 * Represents the Employer node in the Kallipolis ontology.
 *
 * Geometry: Square base → 8 triangular facets → 45° rotated square top → spire
 * The cross-section transitions from a square at the base through an octagon
 * in the middle to a rotated square at the top.
 */

import * as THREE from "three";
import { createFormMaterial } from "@/scene/engine";

export function createSkyscraperForm(color: number): THREE.Group {
  const group = new THREE.Group();
  group.name = "platonic-skyscraper";
  const mat = createFormMaterial(color);
  mat.side = THREE.DoubleSide;

  const baseW = 0.3;   // half-width of base square
  const topW = 0.2;    // half-width of top square (tapered)
  const baseY = -1.0;  // bottom of building
  const midY = 0.0;    // octagon transition
  const topY = 1.0;    // top parapet

  // ── Vertices ──────────────────────────────────────────────────────────────

  // Base square (y = baseY) — aligned to axes
  // 0: (-w, y, -w)  1: (w, y, -w)  2: (w, y, w)  3: (-w, y, w)
  const b0: [number, number, number] = [-baseW, baseY, -baseW];
  const b1: [number, number, number] = [baseW, baseY, -baseW];
  const b2: [number, number, number] = [baseW, baseY, baseW];
  const b3: [number, number, number] = [-baseW, baseY, baseW];

  // Top square (y = topY) — rotated 45 degrees
  // Corners at midpoints of base square edges, scaled by topW/baseW
  const t0: [number, number, number] = [0, topY, -topW * Math.SQRT2];
  const t1: [number, number, number] = [topW * Math.SQRT2, topY, 0];
  const t2: [number, number, number] = [0, topY, topW * Math.SQRT2];
  const t3: [number, number, number] = [-topW * Math.SQRT2, topY, 0];

  // Mid octagon (y = midY) — 8 points, interpolated between base and top
  // Base corner projections (tapered inward)
  const midScale = 0.85;
  const mb0: [number, number, number] = [-baseW * midScale, midY, -baseW * midScale];
  const mb1: [number, number, number] = [baseW * midScale, midY, -baseW * midScale];
  const mb2: [number, number, number] = [baseW * midScale, midY, baseW * midScale];
  const mb3: [number, number, number] = [-baseW * midScale, midY, baseW * midScale];

  // Top corner projections downward
  const mt0: [number, number, number] = [0, midY, -topW * Math.SQRT2 * 1.1];
  const mt1: [number, number, number] = [topW * Math.SQRT2 * 1.1, midY, 0];
  const mt2: [number, number, number] = [0, midY, topW * Math.SQRT2 * 1.1];
  const mt3: [number, number, number] = [-topW * Math.SQRT2 * 1.1, midY, 0];

  // All vertices in order
  const allVerts = [
    ...b0, ...b1, ...b2, ...b3,           // 0-3: base square
    ...mb0, ...mt0, ...mb1, ...mt1,        // 4-7: mid octagon (alternating base-corner, top-corner)
    ...mb2, ...mt2, ...mb3, ...mt3,        // 8-11: mid octagon continued
    ...t0, ...t1, ...t2, ...t3,           // 12-15: top square
  ];

  // ── Faces ─────────────────────────────────────────────────────────────────
  // Connect base → mid octagon → top with triangles

  const faces = [
    // Bottom cap (reversed winding so normal faces downward)
    0, 2, 1,
    0, 3, 2,

    // Base to mid — 8 triangles (base square to octagon)
    // Front face: b0, b1 → mt0, mb0, mb1
    0, 5, 4,    // b0 → mt0 → mb0
    0, 1, 5,    // b0 → b1 → mt0
    1, 6, 5,    // b1 → mb1 → mt0
    // Right face
    1, 7, 6,
    1, 2, 7,
    2, 8, 7,
    // Back face
    2, 9, 8,
    2, 3, 9,
    3, 10, 9,
    // Left face
    3, 11, 10,
    3, 0, 11,
    0, 4, 11,

    // Mid to top — 8 triangles (octagon to top square)
    // Front
    4, 5, 12,
    5, 6, 12,
    6, 13, 12,
    // Right
    6, 7, 13,
    7, 8, 13,
    8, 14, 13,
    // Back
    8, 9, 14,
    9, 10, 14,
    10, 15, 14,
    // Left
    10, 11, 15,
    11, 4, 15,
    4, 12, 15,

    // Top cap
    12, 13, 14,
    12, 14, 15,
  ];

  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute("position", new THREE.Float32BufferAttribute(allVerts, 3));
  geometry.setIndex(faces);
  geometry.computeVertexNormals();

  const tower = new THREE.Mesh(geometry, mat);
  group.add(tower);

  // Edge wireframe — the facets create sharp edges that define the building
  const edgesGeo = new THREE.EdgesGeometry(geometry, 5);
  const edgeMat = new THREE.LineBasicMaterial({
    color: 0xffffff,
    transparent: true,
    opacity: 0.7,
  });
  group.add(new THREE.LineSegments(edgesGeo, edgeMat));

  // Spire
  const spireGeo = new THREE.CylinderGeometry(0.005, 0.025, 0.35, 6);
  const spire = new THREE.Mesh(spireGeo, mat);
  spire.position.y = topY + 0.175;
  group.add(spire);

  return group;
}
