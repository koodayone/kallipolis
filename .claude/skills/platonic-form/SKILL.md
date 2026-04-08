---
name: platonic-form
description: Generate a Three.js geometric form representing the platonic ideal of a concept. Use when creating 3D symbolic representations for Kallipolis atlas nodes (e.g., mortarboard for students, handshake for partnerships).
---

# Platonic Form Generator

You are designing a 3D geometric form that represents the **platonic ideal** of a given concept. The form should be the universal, essential representation — the shape that every real-world instance of the concept is an imperfect copy of.

## Design Philosophy

**Platonic idealism**: Distill the concept to its most essential geometric structure. Not a photorealistic model. Not a stylized icon. The minimum set of geometric primitives that makes the form unmistakably recognizable as the concept it represents.

**Canonical proportions**: The proportions should feel inevitable — like they couldn't be any other way. A mortarboard's board is wider than its base by exactly the ratio that makes it read as a mortarboard, not a table. Study the real object's essential proportions and preserve them.

**Recognition from all angles**: The form will rotate slowly in 3D space. It must be identifiable from the front, side, and at oblique angles. If the form only reads correctly from one viewing angle, it is not yet the ideal.

**Geometric purity**: Use Three.js geometric primitives and BufferGeometry. Prefer clean mathematical forms — boxes, cylinders, spheres, planes, toruses, extrusions. Avoid organic curves unless they are essential to recognition (e.g., the curve of a handshake's fingers).

**Minimum primitives**: Use the fewest shapes necessary. Every primitive must contribute to recognition. If removing a primitive doesn't reduce recognizability, remove it.

## Concept Input

$ARGUMENTS

## Output Format

Generate a TypeScript function that returns a `THREE.Group` containing the composed form. The function signature:

```typescript
export function create[ConceptName]Form(color: number): THREE.Group {
  const group = new THREE.Group();
  // ... compose primitives ...
  return group;
}
```

## Material System

All forms use the same material conventions as the Kallipolis atlas scene:

```typescript
// Solid fill — the form's body
new THREE.MeshPhongMaterial({
  color: color,
  emissive: color,
  emissiveIntensity: 0.45,
  transparent: false,
  side: THREE.FrontSide,
  depthWrite: true,
});

// Edge lines — white wireframe overlay for geometric definition
const edgesGeo = new THREE.EdgesGeometry(geometry, 12);
new THREE.LineBasicMaterial({
  color: 0xffffff,
  transparent: true,
  opacity: 0.7,
});
```

The `color` parameter is the college's brand color (passed as a THREE hex int, e.g., `0x84be00`). The form should look beautiful against a dark background (`#060d1f`).

## Composition Rules

1. **Center the form at origin (0, 0, 0)**. The scene will position it.
2. **Scale to fit within a ~1.5 unit bounding sphere**. The scene handles final scaling.
3. **Orient the form so its most recognizable face points toward positive Z** (toward the camera's default position).
4. **Group all primitives** — meshes and their edge overlays — into a single `THREE.Group`.
5. **Each primitive gets its own mesh + edges pair**. Do not merge geometries.
6. **Name the group**: `group.name = "platonic-[concept]"` (e.g., `"platonic-mortarboard"`).

## Edge Handling

Every mesh in the form gets a corresponding edge overlay:

```typescript
function addWithEdges(group: THREE.Group, geometry: THREE.BufferGeometry, material: THREE.Material, position?: THREE.Vector3, rotation?: THREE.Euler) {
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
```

## Process

1. **Identify the essential properties** of the concept. What are the 2-4 geometric features that make this object recognizable? A mortarboard: flat square board + cylindrical base + tassel. A book: angled cover planes + spine + page block.

2. **Choose primitives** for each essential property. Map each feature to the simplest Three.js geometry that represents it.

3. **Establish proportions** by studying the real object. What is the ratio of the board to the base? How thick is the spine relative to the cover? Get these ratios right — they are what make the form feel canonical.

4. **Compose and position** the primitives relative to each other within the group. Use precise offsets.

5. **Test mentally from multiple angles**. Would this form be recognizable if rotated 45 degrees? 90 degrees? If not, adjust.

6. **Output the complete function** with all imports, geometry creation, material application, and group composition.

## Reference: Existing Atlas Integration Pattern

The form will be used in atlas scenes that follow this pattern:

```typescript
// In the scene builder, the form replaces a primitive geometry:
const formGroup = createMortarboardForm(solidColor);
formGroup.position.copy(position);
scene.add(formGroup);
```

The scene handles rotation, hover effects, click detection, and scaling. The form function only handles geometry and materials.
