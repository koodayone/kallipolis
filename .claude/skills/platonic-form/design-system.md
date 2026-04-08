# Kallipolis Atlas Design System

## Scene Environment

- **Background**: `#060d1f` (deep navy)
- **Fog**: `FogExp2(0x060d1f, 0.03)` — forms fade into darkness at distance
- **Camera**: Perspective, 50° FOV, positioned at z ≈ 5-9

## Lighting Rig

All scenes use the same three-light setup:

| Light | Type | Color | Intensity | Position |
|-------|------|-------|-----------|----------|
| Key | Directional | `#c9a84c` (gold) | 0.5 | (5, 8, 4) |
| Rim | Directional | `#2244aa` (blue) | 0.25 | (-4, -2, -6) |
| Fill | Directional | `#ffffff` | 0.12 | (0, 5, 8) |
| Ambient | Ambient | `#ffffff` | 0.08-0.5 | — |

The gold key light is the primary illumination. It gives forms a warm highlight on the upper-right face. The blue rim light creates depth separation from the dark background. The fill softens shadows.

## Color Palette

- **Brand color**: Each college has a unique brand color (e.g., `0x84be00` for Sequoias). Forms use this as both `color` and `emissive`.
- **Gold accent**: `0xc9a84c` — used for hover states, labels, and the key light
- **Edge white**: `0xffffff` at 70% opacity — wireframe overlay that defines geometric edges

## Rotation Conventions

Forms rotate continuously at slow speeds. Typical rotation speeds:

```typescript
// Radians per frame (at 60fps)
rotSpeed: new THREE.Vector3(
  0.001 - 0.003,  // x-axis (pitch)
  0.002 - 0.004,  // y-axis (yaw — primary rotation)
  0.001 - 0.003   // z-axis (roll)
);
```

Y-axis rotation should be slightly faster than X and Z to create a "turntable" feel while maintaining organic movement.

## Scale Conventions

- **Main atlas forms**: ~1.0-1.5 unit bounding radius
- **Domain hub forms**: ~0.85-0.95 unit bounding radius (slightly smaller)
- Hover scales to 1.12x. Click pulses to 1.18x then settles.

## Interaction States

| State | Scale | Edge Opacity | Fill Opacity | Point Light |
|-------|-------|-------------|-------------|-------------|
| Default | 1.0 | 0.7 | 1.0 | off (0) |
| Hover | 1.12 | 1.0 | 1.0 | on (1.5) |
| Click pulse | 1.18 → 1.0 | 1.0 | 1.0 | on (2.0) |
| Dissolve | 1.0 → 0 | 0 | 0 | off |

Transitions use lerp at speed 0.08 per frame.

## Form Placement in Scenes

### Main Atlas (3 domains)
```
Left: (-3.6, 0, 0)     — Government
Center: (0, 0, 0)       — College
Right: (3.6-4.4, ±1.3)  — Industry (cluster of 3)
```

### Domain Hubs (2-3 leaf views)
```
2 nodes: (-2.0, 0, 0) and (2.0, 0, 0)
3 nodes: (-3.2, 0, 0), (0, 0, 0), (3.2, 0, 0)
```

## Ontological Node → Form Mapping

| Node Type | Concept | Form |
|-----------|---------|------|
| Student | Mortarboard | Flat square board + cylindrical cap + tassel |
| Course | Book | Angled cover planes + spine + page block |
| Employer | Apple Park | Circular ring building + central courtyard |
| Partnership | Handshake | Two interlocking hand forms |
| Occupation | Hard hat | Domed shell + brim |
| Strong Workforce | Dumbbell | Two spheres + connecting bar |
| Perkins V | Scroll | Rolled cylinder with unfurling plane |
| Government | Capitol dome | Hemispherical dome + columned base |
| College | Pillar | Classical column with capital |
| Industry | Gear | Toothed ring with central hub |
