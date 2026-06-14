/**
 * EmployerMap — the SVAMP Employers lens: advanced manufacturing employers of
 * the Bay Area plotted on the same map base + design language as the State
 * Atlas (react-simple-maps / geoMercator over the California counties GeoJSON),
 * but plotting employers instead of schools, framed to the Silicon Valley core,
 * with the five member colleges overlaid as brand-colored diamond anchors.
 *
 * Reuses the State Atlas's marker craft: neon full-opacity fills with a crisp
 * white edge, and a JOINT collision-nudge — employers are pushed off each other
 * AND off the colleges (which stay fixed) so the two layers never overlap.
 * Employers are an upright square (distinct from the colleges' diamond);
 * selection/hover lifts a name label + a focus ring, brightened.
 */

"use client";

import { useState } from "react";
import { ComposableMap, Geographies, Geography, Marker } from "react-simple-maps";
import { FONT } from "@/college-atlas/partnerships/reportChrome";

const GEO_URL = "/california-counties.geojson";
const W = 400, H = 500;            // ComposableMap viewBox (matches the State Atlas)
const EMPLOYER = "#5a9bd4";        // employers-lens blue
const EMPLOYER_BRIGHT = "#7fc0ff"; // selected/hover — lifted, brighter
const PAD = 0.16;                  // bbox padding (fraction of the binding axis)

export type MapEmployer = {
  name: string; lat: number; lng: number;
  socs: string[]; soc_count: number;
  sector?: string | null; website?: string | null; description?: string | null;
};
export type MapCollege = { name: string; lat: number; lng: number; brand: string };

const toRad = (d: number) => (d * Math.PI) / 180;
const mercY = (lat: number) => Math.log(Math.tan(Math.PI / 4 + toRad(lat) / 2));

/** Fit a geoMercator camera (center + scale) to a set of points, padded — the
 * same approach the State Atlas region cameras were derived from. */
function fitCamera(pts: { lat: number; lng: number }[]) {
  const lngs = pts.map((p) => p.lng), lats = pts.map((p) => p.lat);
  const minLng = Math.min(...lngs), maxLng = Math.max(...lngs);
  const minLat = Math.min(...lats), maxLat = Math.max(...lats);
  const center: [number, number] = [(minLng + maxLng) / 2, (minLat + maxLat) / 2];
  // px-per-radian needed to fit each axis into the padded viewBox; take the
  // binding (smaller) scale so both fit.
  const dLng = Math.max(toRad(maxLng - minLng), 1e-4);
  const dLat = Math.max(mercY(maxLat) - mercY(minLat), 1e-4);
  const sx = (W * (1 - 2 * PAD)) / dLng;
  const sy = (H * (1 - 2 * PAD)) / dLat;
  return { center, scale: Math.min(sx, sy) };
}

export default function EmployerMap({
  employers, colleges, selected, hover, onSelect, onHover,
}: {
  employers: MapEmployer[];
  colleges: MapCollege[];
  selected: string | null;
  hover: string | null;                       // controlled — synced with the list
  onSelect: (name: string | null) => void;
  onHover: (name: string | null) => void;
}) {
  const [colHover, setColHover] = useState<string | null>(null);
  // Render whenever there's anything to plot. A landscape can have its member
  // colleges anchored before any employers are matched to its sector (e.g. a
  // draft instance) — show the schools framed on the base map regardless.
  if (!employers.length && !colleges.length) return null;

  // Frame to fit EVERY employer + college, padded — so no marker is ever clipped
  // off the edge (the far-SE outliers in Morgan Hill/Gilroy used to fly off when
  // the camera was fit to a tight cluster). The dense Santa-Clara cluster stays
  // legible at the smaller scale because the collision nudge below enforces a
  // minimum mark spacing regardless of how tightly the raw points pack.
  const cam = fitCamera([...employers, ...colleges]);
  // Project lng/lat → viewBox px (replicating react-simple-maps' geoMercator
  // with this center/scale) so we can nudge overlapping markers apart.
  const project = (lng: number, lat: number): [number, number] => [
    cam.scale * toRad(lng - cam.center[0]) + W / 2,
    -cam.scale * (mercY(lat) - mercY(cam.center[1])) + H / 2,
  ];

  // Joint collision-nudge (px offsets), ported from the State Atlas: employers
  // are pushed off each other AND off the colleges (which stay fixed as
  // anchors), so the two layers never overlap.
  const MIN_EE = 19, MIN_EC = 24, SPRING = 0.16, ITERS = 90;  // wider spacing so the larger labels breathe
  const cpos = colleges.map((c) => { const [x, y] = project(c.lng, c.lat); return { x, y }; });
  const pos = employers.map((e) => { const [x, y] = project(e.lng, e.lat); return { x, y }; });
  for (let it = 0; it < ITERS; it++) {
    for (let i = 0; i < pos.length; i++) {
      for (let j = i + 1; j < pos.length; j++) {
        const dx = pos[j].x - pos[i].x, dy = pos[j].y - pos[i].y;
        const d = Math.hypot(dx, dy) || 0.01;
        if (d < MIN_EE) {
          const push = ((MIN_EE - d) / 2) * SPRING;
          const ux = dx / d, uy = dy / d;
          pos[i].x -= ux * push; pos[i].y -= uy * push;
          pos[j].x += ux * push; pos[j].y += uy * push;
        }
      }
      for (let k = 0; k < cpos.length; k++) {
        const dx = pos[i].x - cpos[k].x, dy = pos[i].y - cpos[k].y;
        const d = Math.hypot(dx, dy) || 0.01;
        if (d < MIN_EC) {
          const push = (MIN_EC - d) * SPRING, ux = dx / d, uy = dy / d;
          pos[i].x += ux * push; pos[i].y += uy * push;
        }
      }
    }
  }
  const offset = employers.map((e, i) => {
    const [bx, by] = project(e.lng, e.lat);
    return { dx: pos[i].x - bx, dy: pos[i].y - by };
  });

  // Active-label de-clutter (ported from the State Atlas): when a marker's label
  // is showing, hide any OTHER marker whose center falls under that label's
  // bounding rect, so the name reads cleanly. Rects are computed at the marker's
  // nudged center, mirroring the <text> geometry (anchor middle, label above).
  const labelRects: { id: string; x1: number; y1: number; x2: number; y2: number }[] = [];
  const addRect = (id: string, cx: number, cy: number, name: string, fontSize: number, dy: number) => {
    const w = name.length * fontSize * 0.58, PAD_X = 12, PAD_Y = 7, baseY = cy + dy;
    labelRects.push({ id, x1: cx - w / 2 - PAD_X, x2: cx + w / 2 + PAD_X, y1: baseY - fontSize - PAD_Y, y2: baseY + PAD_Y });
  };
  employers.forEach((e, i) => {
    if (selected === e.name || hover === e.name) addRect("e:" + e.name, pos[i].x, pos[i].y, e.display_name ?? e.name, 12.5, -16);
  });
  colleges.forEach((c, i) => {
    if (colHover === c.name) addRect("c:" + c.name, cpos[i].x, cpos[i].y, c.name, 12.5, -16);
  });
  const underLabel = (id: string, x: number, y: number) =>
    labelRects.some((r) => r.id !== id && x >= r.x1 && x <= r.x2 && y >= r.y1 && y <= r.y2);

  return (
    <div
      onClick={() => onSelect(null)}  // click empty map space (counties/gaps) clears the selection; markers stopPropagation
      style={{ position: "relative", width: "100%", height: "100%", background: "#060d1f", borderRadius: 12, border: "1px solid rgba(255,255,255,0.08)", overflow: "hidden" }}
    >
      <ComposableMap
        projection="geoMercator"
        projectionConfig={{ center: cam.center, scale: cam.scale }}
        width={W} height={H}
        style={{ width: "100%", height: "100%" }}
      >
        <Geographies geography={GEO_URL}>
          {({ geographies }) =>
            geographies.map((geo) => (
              <Geography
                key={geo.rsmKey}
                geography={geo}
                fill="rgba(255,255,255,0.04)"
                stroke="rgba(255,255,255,0.1)"
                strokeWidth={0.4}
                style={{ default: { outline: "none" }, hover: { outline: "none" }, pressed: { outline: "none" } }}
              />
            ))
          }
        </Geographies>

        {/* Member-college anchors — quiet brand diamonds by default (no label,
            no ring); the name + ring reveal on hover, same as the employers, so
            the default view stays clean. */}
        {colleges.map((c, i) => {
          const on = colHover === c.name;
          if (!on && underLabel("c:" + c.name, cpos[i].x, cpos[i].y)) return null;
          return (
            <Marker
              key={"col-" + c.name}
              coordinates={[c.lng, c.lat]}
              onMouseEnter={() => setColHover(c.name)}
              onMouseLeave={() => setColHover(null)}
              onClick={(ev) => ev?.stopPropagation?.()}
            >
              {on && <circle r={10} fill="none" stroke={c.brand} strokeOpacity={0.45} strokeWidth={1} />}
              <rect x={-5.4} y={-5.4} width={10.8} height={10.8} transform="rotate(45)" fill={c.brand} stroke="rgba(255,255,255,0.7)" strokeWidth={0.8} opacity={on ? 1 : 0.9} />
              {on && (
                <text textAnchor="middle" y={-16} style={{ fontFamily: FONT, fontSize: 12.5, fontWeight: 600, fill: "rgba(255,255,255,0.92)", pointerEvents: "none" }}>
                  {c.name}
                </text>
              )}
            </Marker>
          );
        })}

        {/* Employers — upright blue squares, collision-nudged. */}
        {employers.map((e, i) => {
          const on = selected === e.name || hover === e.name;
          const { dx, dy } = offset[i];
          if (!on && underLabel("e:" + e.name, pos[i].x, pos[i].y)) return null;
          return (
            <Marker
              key={e.name}
              coordinates={[e.lng, e.lat]}
              onMouseEnter={() => onHover(e.name)}
              onMouseLeave={() => onHover(null)}
              onClick={(ev) => { ev?.stopPropagation?.(); onSelect(e.name); }}
            >
              <g transform={`translate(${dx}, ${dy})`} style={{ cursor: "pointer" }}>
                {on && <circle r={9} fill="none" stroke={EMPLOYER_BRIGHT} strokeOpacity={0.6} strokeWidth={1} />}
                <rect x={-4.6} y={-4.6} width={9.2} height={9.2} rx={1.9}
                  fill={on ? EMPLOYER_BRIGHT : EMPLOYER}
                  stroke="#ffffff" strokeOpacity={on ? 0.9 : 0.55} strokeWidth={on ? 0.9 : 0.7} />
                {on && (
                  <text textAnchor="middle" y={-16} style={{ fontFamily: FONT, fontSize: 12.5, fontWeight: 600, fill: "#ffffff", pointerEvents: "none" }}>
                    {e.display_name ?? e.name}
                  </text>
                )}
              </g>
            </Marker>
          );
        })}
      </ComposableMap>

      {/* Legend — bottom-left, the map convention, clear of the Santa-Clara
          cluster; swatches mirror the marks exactly (blue rounded square =
          employer, light diamond = member college). Non-interactive, so a click
          here falls through to the container and clears any selection. */}
      <div style={{
        position: "absolute", left: 12, bottom: 12, pointerEvents: "none",
        display: "flex", flexDirection: "column", gap: 6, padding: "8px 10px",
        borderRadius: 9, background: "rgba(8,15,33,0.72)",
        border: "1px solid rgba(255,255,255,0.1)", backdropFilter: "blur(6px)",
      }}>
        {employers.length > 0 && (
          <div style={{ display: "flex", alignItems: "center", gap: 7, fontSize: 11, color: "rgba(255,255,255,0.82)", whiteSpace: "nowrap" }}>
            <span style={{ width: 9, height: 9, borderRadius: 2, background: EMPLOYER, border: "0.8px solid rgba(255,255,255,0.55)" }} />
            Employer
          </div>
        )}
        <div style={{ display: "flex", alignItems: "center", gap: 7, fontSize: 11, color: "rgba(255,255,255,0.82)", whiteSpace: "nowrap" }}>
          <span style={{ width: 8, height: 8, transform: "rotate(45deg)", background: "#cdd6e6", border: "0.8px solid rgba(255,255,255,0.6)" }} />
          Member college
        </div>
      </div>
    </div>
  );
}
