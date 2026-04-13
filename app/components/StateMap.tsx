"use client";

import { useState } from "react";
import { ComposableMap, Geographies, Geography, Marker } from "react-simple-maps";

const GEO_URL = "/california-counties.geojson";

const DIAMOND = 6;

// Neon color derivation (subset of atlas/config/schoolConfig.ts)
function hexToHsl(hex: string): [number, number, number] {
  const r = parseInt(hex.slice(1, 3), 16) / 255;
  const g = parseInt(hex.slice(3, 5), 16) / 255;
  const b = parseInt(hex.slice(5, 7), 16) / 255;
  const max = Math.max(r, g, b), min = Math.min(r, g, b);
  const l = (max + min) / 2;
  if (max === min) return [0, 0, l];
  const d = max - min;
  const s = l > 0.5 ? d / (2 - max - min) : d / (max + min);
  let h = 0;
  if (max === r) h = ((g - b) / d + (g < b ? 6 : 0)) / 6;
  else if (max === g) h = ((b - r) / d + 2) / 6;
  else h = ((r - g) / d + 4) / 6;
  return [h * 360, s * 100, l * 100];
}

function hslToHex(h: number, s: number, l: number): string {
  const hNorm = h / 360, sNorm = s / 100, lNorm = l / 100;
  const hue2rgb = (p: number, q: number, t: number) => {
    if (t < 0) t += 1; if (t > 1) t -= 1;
    if (t < 1 / 6) return p + (q - p) * 6 * t;
    if (t < 1 / 2) return q;
    if (t < 2 / 3) return p + (q - p) * (2 / 3 - t) * 6;
    return p;
  };
  if (sNorm === 0) { const v = Math.round(lNorm * 255); return `#${v.toString(16).padStart(2, "0").repeat(3)}`; }
  const q = lNorm < 0.5 ? lNorm * (1 + sNorm) : lNorm + sNorm - lNorm * sNorm;
  const p = 2 * lNorm - q;
  const rv = Math.round(hue2rgb(p, q, hNorm + 1 / 3) * 255);
  const gv = Math.round(hue2rgb(p, q, hNorm) * 255);
  const bv = Math.round(hue2rgb(p, q, hNorm - 1 / 3) * 255);
  return `#${rv.toString(16).padStart(2, "0")}${gv.toString(16).padStart(2, "0")}${bv.toString(16).padStart(2, "0")}`;
}

function toNeon(brandHex: string): string {
  const [h, s] = hexToHsl(brandHex);
  if (s < 12) return "#c9a84c";
  const BG_HUE = 223, SHIFT_RANGE = 20;
  let neonH = h;
  const hueDist = Math.abs(h - BG_HUE);
  if (hueDist < SHIFT_RANGE) neonH = BG_HUE - SHIFT_RANGE - (SHIFT_RANGE - hueDist);
  const neonS = Math.max(85, s);
  let neonL: number;
  if (neonH >= 50 && neonH <= 170) neonL = 55;
  else if (neonH < 50 || neonH > 330) neonL = 60;
  else neonL = 65;
  return hslToHex(neonH, neonS, neonL);
}

// Brand colors from atlas/config/collegeColors.generated.ts + overrides
const BRAND_COLORS: Record<string, string> = {
  foothill: "#7B2D3E", shasta: "#3A6F3A", lassen: "#b64d19",
  laketahoe: "#013d51", sequoias: "#84be00", desert: "#ffc82e",
  compton: "#bd1051", sandiegomira: "#117882",
  redwoods: "#7B2D3E", mendocino: "#121a47", butte: "#c4aa65",
  saccc: "#840029", laney: "#2c784c", merced: "#1e3a5f",
  montereypen: "#b36282", hancock: "#00405e", oxnard: "#29b063",
  imperial: "#ae3237", sandiegocity: "#c11e2e", irvinevalley: "#4679a9",
  ccsf: "#1e3a5f", featherriver: "#1f693c",
};

export type College = { id: string; name: string; district: string; lat: number; lng: number };

export const FEATURED: College[] = [
  { id: "shasta", name: "Shasta College", district: "Shasta-Tehama-Trinity JCCD", lat: 40.61, lng: -122.37 },
  { id: "lassen", name: "Lassen College", district: "Lassen CCD", lat: 40.44, lng: -120.65 },
  { id: "laketahoe", name: "Lake Tahoe Community College", district: "Lake Tahoe CCD", lat: 38.93, lng: -119.97 },
  { id: "foothill", name: "Foothill College", district: "Foothill-De Anza CCD", lat: 37.36, lng: -122.05 },
  { id: "sequoias", name: "College of the Sequoias", district: "Sequoias CCD", lat: 36.32, lng: -119.30 },
  { id: "compton", name: "Compton College", district: "Compton CCD", lat: 33.87, lng: -118.21 },
  { id: "desert", name: "College of the Desert", district: "Desert CCD", lat: 33.73, lng: -116.37 },
  { id: "sandiegomira", name: "San Diego Miramar College", district: "San Diego CCD", lat: 32.90, lng: -117.14 },
];

// Background colleges — visible on map but never in the rotation
const BACKGROUND: College[] = [
  { id: "redwoods", name: "College of the Redwoods", district: "Redwoods CCD", lat: 40.80, lng: -124.16 },
  { id: "mendocino", name: "Mendocino College", district: "Mendocino-Lake CCD", lat: 39.19, lng: -123.23 },
  { id: "butte", name: "Butte College", district: "Butte-Glenn CCD", lat: 39.52, lng: -121.65 },
  { id: "featherriver", name: "Feather River College", district: "Feather River CCD", lat: 39.93, lng: -120.95 },
  { id: "saccc", name: "Sacramento City College", district: "Los Rios CCD", lat: 38.56, lng: -121.49 },
  { id: "ccsf", name: "City College of San Francisco", district: "San Francisco CCD", lat: 37.72, lng: -122.45 },
  { id: "laney", name: "Laney College", district: "Peralta CCD", lat: 37.80, lng: -122.27 },
  { id: "merced", name: "Merced College", district: "Merced CCD", lat: 37.35, lng: -120.49 },
  { id: "montereypen", name: "Monterey Peninsula College", district: "Monterey Peninsula CCD", lat: 36.60, lng: -121.87 },
  { id: "hancock", name: "Allan Hancock College", district: "Allan Hancock JCCD", lat: 34.90, lng: -120.43 },
  { id: "oxnard", name: "Oxnard College", district: "Ventura CCD", lat: 34.22, lng: -119.18 },
  { id: "irvinevalley", name: "Irvine Valley College", district: "South Orange County CCD", lat: 33.69, lng: -117.83 },
  { id: "sandiegocity", name: "San Diego City College", district: "San Diego CCD", lat: 32.71, lng: -117.16 },
  { id: "imperial", name: "Imperial Valley College", district: "Imperial CCD", lat: 32.79, lng: -115.55 },
];

// Pre-compute neon colors for all colleges
export const NEON_COLORS: Record<string, string> = {};
for (const c of [...FEATURED, ...BACKGROUND]) {
  NEON_COLORS[c.id] = toNeon(BRAND_COLORS[c.id] ?? "#1e3a5f");
}

type Props = {
  activeCollegeId?: string | null;
  brightenAll?: boolean;
};

export default function StateMap({ activeCollegeId = null, brightenAll = false }: Props) {
  const [hoveredId, setHoveredId] = useState<string | null>(null);

  return (
    <div style={{ position: "relative", width: "100%", height: "100%" }}>
      <ComposableMap
        projection="geoMercator"
        projectionConfig={{ center: [-118.2, 37.5], scale: 2500 }}
        width={520}
        height={500}
        style={{ width: "100%", height: "100%", overflow: "visible" }}
      >
        {/* County polygons */}
        <Geographies geography={GEO_URL}>
          {({ geographies }) =>
            geographies.map((geo) => (
              <Geography
                key={geo.rsmKey}
                geography={geo}
                fill="rgba(255,255,255,0.04)"
                stroke="rgba(255,255,255,0.1)"
                strokeWidth={0.4}
                style={{
                  default: { outline: "none" },
                  hover: { outline: "none" },
                  pressed: { outline: "none" },
                }}
              />
            ))
          }
        </Geographies>

        {/* Background college markers — static, dimmed */}
        {BACKGROUND.map((college) => {
          const brandColor = NEON_COLORS[college.id];
          return (
            <Marker key={college.id} coordinates={[college.lng, college.lat]}>
              <g style={{ opacity: brightenAll ? 0.85 : 0.3, transition: "opacity 0.6s ease" }}>
                <rect
                  x={-DIAMOND / 2}
                  y={-DIAMOND / 2}
                  width={DIAMOND}
                  height={DIAMOND}
                  fill={brandColor}
                  transform="rotate(45)"
                />
              </g>
            </Marker>
          );
        })}

        {/* Featured college markers */}
        {FEATURED.map((college) => {
          const isActive = hoveredId === college.id || activeCollegeId === college.id;
          const isDimmed = !brightenAll && (hoveredId !== null || activeCollegeId !== null) && !isActive;
          const brandColor = NEON_COLORS[college.id];
          const size = isActive ? DIAMOND * 1.4 : DIAMOND;

          return (
            <Marker
              key={college.id}
              coordinates={[college.lng, college.lat]}
              onMouseEnter={() => setHoveredId(college.id)}
              onMouseLeave={() => setHoveredId(null)}
            >
              <g style={{ cursor: "pointer", opacity: isDimmed ? 0.3 : 1, transition: "opacity 0.3s ease" }}>
                {/* Glow ring */}
                {isActive && (
                  <circle
                    r={size * 1.7}
                    fill="none"
                    stroke={brandColor}
                    strokeWidth="0.8"
                    strokeOpacity={0.45}
                  />
                )}
                {/* Diamond */}
                <rect
                  x={-size / 2}
                  y={-size / 2}
                  width={size}
                  height={size}
                  fill={brandColor}
                  transform="rotate(45)"
                  style={{ transition: "fill 0.15s" }}
                />
                {/* College name on hover */}
                {hoveredId === college.id && (
                  <text
                    y={-size - 10}
                    textAnchor="middle"
                    style={{
                      fontFamily: "var(--font-geist), system-ui, sans-serif",
                      fontSize: "12px",
                      fontWeight: 600,
                      fill: "#ffffff",
                      pointerEvents: "none",
                      userSelect: "none",
                    }}
                  >
                    {college.name}
                  </text>
                )}
              </g>
            </Marker>
          );
        })}
      </ComposableMap>
    </div>
  );
}
