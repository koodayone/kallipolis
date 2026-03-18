"use client";

import { useEffect, useState } from "react";

const LON_MIN = -124.411;
const LON_MAX = -114.136;
const LAT_MIN = 32.537;
const LAT_MAX = 42.012;
const COS_LAT = Math.cos((37.5 * Math.PI) / 180); // mid-latitude correction ~0.793

// Scale so height = 500px, width is proportional
const SCALE = 500 / (LAT_MAX - LAT_MIN);
const VIEW_W = Math.round((LON_MAX - LON_MIN) * COS_LAT * SCALE);
const VIEW_H = 500;

function project([lon, lat]: number[]): string {
  const x = (lon - LON_MIN) * COS_LAT * SCALE;
  const y = (LAT_MAX - lat) * SCALE;
  return `${x.toFixed(1)},${y.toFixed(1)}`;
}

function projectXY([lon, lat]: number[]): [number, number] {
  return [
    (lon - LON_MIN) * COS_LAT * SCALE,
    (LAT_MAX - lat) * SCALE,
  ];
}

function ringToPath(ring: number[][]): string {
  return ring.map((pt, i) => `${i === 0 ? "M" : "L"}${project(pt)}`).join(" ") + " Z";
}

// Big Dipper stars: [lat, lon]
// Bowl (4 stars, SW→NE diagonal in southern CA) + Handle (3 stars arcing NW to Northern CA)
const DIPPER_STARS: [number, number][] = (
  [
    [34.8, -118.5],  // S1 — SW bottom of bowl (Greater LA inland)
    [33.7, -116.2],  // S2 — SE bottom of bowl (Palm Springs / Coachella Valley)
    [35.1, -115.8],  // S3 — NE top of bowl (Barstow / Mojave)
    [36.5, -119.0],  // S4 — NW top of bowl (Sequoia / Kings Canyon area)
    [37.5, -121.4],  // S5 — handle start (Modesto / Sierra foothills)
    [39.2, -121.1],  // S6 — handle mid (Chico / Sacramento Valley)
    [40.8, -122.5],  // S7 — handle tip (Redding / Shasta County)
  ] as [number, number][]
).map(([lat, lon]) => projectXY([lon, lat]));

// Connections: bowl rectangle (0-1-2-3-0) + handle (3-4-5-6)
const DIPPER_EDGES: [number, number][] = [
  [0, 1], [1, 2], [2, 3], [3, 0], // bowl
  [3, 4], [4, 5], [5, 6],          // handle
];

function diamond(cx: number, cy: number, s: number): string {
  return `${cx},${cy - s} ${cx + s},${cy} ${cx},${cy + s} ${cx - s},${cy}`;
}

export default function CaliforniaMap() {
  const [pathD, setPathD] = useState<string | null>(null);

  useEffect(() => {
    fetch("/california.geojson")
      .then((r) => r.json())
      .then((geojson) => {
        const { type, coordinates } = geojson.geometry;
        const rings: number[][][] =
          type === "MultiPolygon"
            ? coordinates.flat(1)
            : coordinates;
        setPathD(rings.map(ringToPath).join(" "));
      });
  }, []);

  return (
    <svg
      viewBox={`0 0 ${VIEW_W} ${VIEW_H}`}
      width="100%"
      height="100%"
      preserveAspectRatio="xMidYMid meet"
      style={{ display: "block" }}
    >
      {pathD && (
        <path
          d={pathD}
          fill="none"
          stroke="rgba(255,255,255,0.6)"
          strokeWidth="2"
          strokeLinejoin="round"
          strokeLinecap="round"
        />
      )}
      {DIPPER_EDGES.map(([a, b], i) => {
        const [x1, y1] = DIPPER_STARS[a];
        const [x2, y2] = DIPPER_STARS[b];
        return (
          <path
            key={`edge-${i}`}
            id={`dipper-edge-${i}`}
            d={`M${x1},${y1} L${x2},${y2}`}
            fill="none"
            stroke="#FFCC33"
            strokeWidth="1.5"
            strokeOpacity="0.7"
          />
        );
      })}
      {DIPPER_EDGES.map((_, i) => (
        <circle key={`p-${i}`} r="3" fill="#ffe580">
          <animateMotion
            dur="3s"
            begin="0s"
            repeatCount="indefinite"
            calcMode="linear"
          >
            <mpath href={`#dipper-edge-${i}`} />
          </animateMotion>
        </circle>
      ))}
      {DIPPER_STARS.map(([cx, cy], i) => (
        <polygon
          key={i}
          points={diamond(cx, cy, 6)}
          fill="#5aaa72"
        />
      ))}
    </svg>
  );
}
