"use client";

import { useMemo } from "react";
import { ComposableMap, Geographies, Geography, Marker } from "react-simple-maps";
import { geoMercator } from "d3-geo";

const BRAND = "#4fd1fd";

const PROJECTION_CONFIG = { center: [-119.5, 37.0] as [number, number], scale: 2100 };
const MAP_WIDTH = 460;
const MAP_HEIGHT = 520;

// ── Consortium centers (lat/lng) ────────────────────────────────────────

const CONSORTIA = [
  { key: "NFN",  label: "North / Far North",    coords: [-121.5, 40.5] as [number, number] },
  { key: "Bay",  label: "Bay Area",              coords: [-122.6, 38.1] as [number, number] },
  { key: "CVML", label: "Central Valley /\nMother Lode", coords: [-119.4, 37.1] as [number, number] },
  { key: "SCC",  label: "South Central Coast",   coords: [-120.6, 35.1] as [number, number] },
  { key: "LA",   label: "Los Angeles",           coords: [-118.2, 34.3] as [number, number] },
  { key: "OC",   label: "Orange County",         coords: [-117.8, 33.6] as [number, number] },
  { key: "IE/D", label: "Inland Empire /\nDesert", coords: [-116.0, 34.8] as [number, number] },
  { key: "SD/I", label: "San Diego / Imperial",  coords: [-116.5, 32.8] as [number, number] },
];

// Label anchor directions
const LABEL_ANCHORS: Record<string, { side: "left" | "right" | "center"; dx?: number; dy?: number }> = {
  "NFN":  { side: "center", dx: 24, dy: -36 },
  "Bay":  { side: "right" },
  "CVML": { side: "left", dx: 2, dy: -8 },
  "SCC":  { side: "right" },
  "LA":   { side: "right", dy: 10 },
  "OC":   { side: "right", dy: 14 },
  "IE/D": { side: "left", dy: -12 },
  "SD/I": { side: "center", dy: 16 },
};

// ── Component ───────────────────────────────────────────────────────────

export default function RegionalUnificationMap() {
  // Project lat/lng to screen pixels for the constellation lines
  const projected = useMemo(() => {
    const projection = geoMercator()
      .center(PROJECTION_CONFIG.center)
      .scale(PROJECTION_CONFIG.scale)
      .translate([MAP_WIDTH / 2, MAP_HEIGHT / 2]);

    return CONSORTIA.map((c) => {
      const p = projection(c.coords);
      return { key: c.key, x: p ? p[0] : 0, y: p ? p[1] : 0 };
    });
  }, []);

  // Constellation edges — pairs of consortium keys
  const EDGES: [string, string][] = [
    // Perimeter loop
    ["NFN", "Bay"],
    ["Bay", "SCC"],
    ["SCC", "LA"],
    ["LA", "OC"],
    ["OC", "SD/I"],
    ["SD/I", "IE/D"],
    ["IE/D", "CVML"],
    ["CVML", "NFN"],
    // Interior cross-connections
    ["Bay", "CVML"],
    ["CVML", "SCC"],
    ["CVML", "LA"],
    ["LA", "IE/D"],
  ];

  const projectedMap = Object.fromEntries(projected.map((p) => [p.key, p]));

  return (
    <div style={{ position: "relative", width: "100%", minHeight: 480 }}>
      <ComposableMap
        width={MAP_WIDTH}
        height={MAP_HEIGHT}
        projection="geoMercator"
        projectionConfig={PROJECTION_CONFIG}
        style={{ width: "100%", height: "auto" }}
      >
        {/* Base map — unified white California */}
        <Geographies geography="/california-counties.geojson">
          {({ geographies }) =>
            geographies.map((geo) => (
              <Geography
                key={geo.rsmKey}
                geography={geo}
                style={{
                  default: { fill: "rgba(255,255,255,0.07)", stroke: "rgba(255,255,255,0.13)", strokeWidth: 0.3, outline: "none" },
                  hover: { fill: "rgba(255,255,255,0.07)", outline: "none" },
                  pressed: { fill: "rgba(255,255,255,0.07)", outline: "none" },
                }}
              />
            ))
          }
        </Geographies>

        {/* Constellation lines — breathing pulse */}
        {EDGES.map(([fromKey, toKey], i) => {
          const from = projectedMap[fromKey];
          const to = projectedMap[toKey];
          if (!from || !to) return null;
          const avgY = (from.y + to.y) / 2;
          const delay = (avgY / MAP_HEIGHT) * 1.8;
          return (
            <line
              key={`${fromKey}-${toKey}`}
              x1={from.x} y1={from.y}
              x2={to.x} y2={to.y}
              stroke="#c9a84c"
              strokeWidth={1.2}
              strokeLinecap="round"
              className="constellation-breathe"
              style={{ animationDelay: `${delay}s` }}
            />
          );
        })}

        {/* Diamond markers at consortium centers */}
        {CONSORTIA.map((c, i) => {
          const p = projected[i];
          const delay = (p.y / MAP_HEIGHT) * 2;
          return (
            <Marker key={c.key} coordinates={c.coords}>
              <rect
                x={-5} y={-5} width={10} height={10}
                transform="rotate(45)"
                fill={BRAND}
                className="constellation-diamond"
                style={{ animationDelay: `${delay}s` }}
              />
            </Marker>
          );
        })}
      </ComposableMap>

      {/* Labels — positioned using projected coordinates */}
      {CONSORTIA.map((c, i) => {
        const p = projected[i];
        const anchor = LABEL_ANCHORS[c.key] ?? { side: "left" as const };
        const xPct = (p.x / MAP_WIDTH) * 100;
        const yPct = (p.y / MAP_HEIGHT) * 100;
        const dx = anchor.dx ?? 0;
        const dy = anchor.dy ?? 0;
        return (
          <span
            key={c.key}
            style={{
              position: "absolute",
              left: `calc(${xPct}% + ${dx}px)`,
              top: `calc(${yPct}% + ${dy}px)`,
              transform: anchor.side === "center" ? "translate(-50%, 0)" : anchor.side === "right" ? "translate(calc(-100% - 12px), -50%)" : "translate(12px, -50%)",
              fontSize: 10,
              fontWeight: 700,
              textTransform: "uppercase",
              letterSpacing: "0.12em",
              color: "rgba(255,255,255,0.6)",
              textShadow: "0 1px 3px rgba(0,0,0,0.5)",
              whiteSpace: "pre",
              pointerEvents: "none",
            }}
          >
            {c.label}
          </span>
        );
      })}
    </div>
  );
}
