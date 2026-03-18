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

function ringToPath(ring: number[][]): string {
  return ring.map((pt, i) => `${i === 0 ? "M" : "L"}${project(pt)}`).join(" ") + " Z";
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
    </svg>
  );
}
