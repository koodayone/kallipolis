/**
 * Per-region camera framings + on-map label anchors for the State Atlas.
 *
 * The State Atlas has two stable views — `state` (all of California) and
 * `region` (one of the 8 SWP regional consortia). Each region defines its
 * own camera (geoMercator center + scale) so that clicking into a region
 * frames its colleges with intentional padding rather than a generic zoom.
 *
 * Cameras were derived from the bounding box of each region's member
 * counties ∪ featured colleges with 15% padding on the binding axis,
 * then hand-tightened in two cases (see `// hand-tightened` notes below).
 *
 * Label anchors are hand-picked positions in visual whitespace within
 * each region's territory — not centroids. They define where the
 * always-on region label sits at state view, expressing "Bay Area is a
 * destination" rather than "Bay Area is a tinted region."
 */

export type RegionView = {
  /** geoMercator camera params, applied to react-simple-maps `projectionConfig`. */
  camera: { center: [number, number]; scale: number };
  /** Geographic position [lng, lat] where the on-map region label is anchored. */
  labelAnchor: [number, number];
};

export const STATE_VIEW = {
  camera: { center: [-119.5, 37.5] as [number, number], scale: 2500 },
};

export const REGION_VIEWS: Record<string, RegionView> = {
  "north-far-north": {
    camera: { center: [-122.14, 40.02], scale: 3541 },
    labelAnchor: [-122.10, 40.45],   // over Tehama / Shasta
  },
  "bay-area": {
    camera: { center: [-121.87, 37.33], scale: 4833 },
    labelAnchor: [-122.30, 37.70],   // northwest, over the bay water
  },
  "central-valley-mother-lode": {
    camera: { center: [-119.70, 36.70], scale: 4500 },
    labelAnchor: [-118.80, 37.00],   // east-central, over Inyo / east Tulare
  },
  "south-central-coast": {
    camera: { center: [-119.99, 34.51], scale: 5908 },
    labelAnchor: [-120.20, 34.85],   // northwest, San Luis Obispo county
  },
  "los-angeles": {
    camera: { center: [-118.30, 33.81], scale: 8250 },
    labelAnchor: [-118.05, 34.30],   // north LA county / San Gabriel Mtns
  },
  "orange-county": {
    camera: { center: [-117.85, 33.70], scale: 12000 },
    labelAnchor: [-117.80, 33.65],   // central OC
  },
  "inland-empire-desert": {
    camera: { center: [-115.97, 34.62], scale: 4370 },
    labelAnchor: [-115.80, 34.85],   // northern San Bernardino desert
  },
  "san-diego-imperial": {
    camera: { center: [-116.03, 33.02], scale: 5121 },
    labelAnchor: [-116.10, 32.95],   // east SD county / west Imperial
  },
};

/**
 * Animation timing for the state ↔ region camera transition. 350 ms
 * reads as a deliberate camera move rather than instant navigation —
 * preserves spatial mental model across the zoom.
 */
export const ZOOM_TRANSITION_MS = 350;

/** cubic-bezier(0.4, 0, 0.2, 1) — Material "standard easing." */
export function easeInOutCubic(t: number): number {
  return t < 0.5
    ? 4 * t * t * t
    : 1 - Math.pow(-2 * t + 2, 3) / 2;
}

export function lerp(a: number, b: number, t: number): number {
  return a + (b - a) * t;
}
