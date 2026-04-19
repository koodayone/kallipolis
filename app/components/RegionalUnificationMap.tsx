"use client";

import { useState, useEffect, useRef } from "react";
import { ComposableMap, Geographies, Geography } from "react-simple-maps";

// ── County → COE Region mapping (from backend/ontology/regions.py) ──────

const COUNTY_TO_REGION: Record<string, string> = {
  Alameda: "Bay", "Contra Costa": "Bay", Marin: "Bay", Monterey: "Bay",
  Napa: "Bay", "San Benito": "Bay", "San Francisco": "Bay", "San Mateo": "Bay",
  "Santa Clara": "Bay", "Santa Cruz": "Bay", Solano: "Bay", Sonoma: "Bay",

  Alpine: "CVML", Amador: "CVML", Calaveras: "CVML", Fresno: "CVML",
  Inyo: "CVML", Kern: "CVML", Kings: "CVML", Madera: "CVML",
  Mariposa: "CVML", Merced: "CVML", Mono: "CVML", "San Joaquin": "CVML",
  Stanislaus: "CVML", Tulare: "CVML", Tuolumne: "CVML",

  "Del Norte": "FN", Humboldt: "FN", Lake: "FN", Lassen: "FN",
  Mendocino: "FN", Modoc: "FN", Siskiyou: "FN", Trinity: "FN",

  Butte: "GS", Colusa: "GS", "El Dorado": "GS", Glenn: "GS",
  Nevada: "GS", Placer: "GS", Sacramento: "GS", Shasta: "GS",
  Sierra: "GS", Sutter: "GS", Tehama: "GS", Yolo: "GS", Yuba: "GS",
  Plumas: "GS",

  Riverside: "IE/D", "San Bernardino": "IE/D",

  "Los Angeles": "LA",

  Orange: "OC",

  "San Luis Obispo": "SCC", "Santa Barbara": "SCC", Ventura: "SCC",

  "San Diego": "SD/I", Imperial: "SD/I",
};

// ── Region config ───────────────────────────────────────────────────────

const REGIONS: Record<string, { color: string; dx: number; dy: number; delay: number }> = {
  "FN":   { color: "#2a7a9c", dx: 0,   dy: -25, delay: 0.3 },
  "GS":   { color: "#3498b8", dx: 12,  dy: -12, delay: 0.2 },
  "Bay":  { color: "#4fd1fd", dx: -25, dy: -8,  delay: 0.15 },
  "CVML": { color: "#3bb5d9", dx: 8,   dy: 5,   delay: 0.1 },
  "SCC":  { color: "#2a8aad", dx: -20, dy: 12,  delay: 0.2 },
  "LA":   { color: "#45c4ed", dx: -12, dy: 20,  delay: 0.25 },
  "OC":   { color: "#5dd8ff", dx: 0,   dy: 25,  delay: 0.3 },
  "IE/D": { color: "#3098ba", dx: 18,  dy: 18,  delay: 0.25 },
  "SD/I": { color: "#2580a0", dx: 12,  dy: 28,  delay: 0.35 },
};

// ── RisingSun ───────────────────────────────────────────────────────────

const SUN_RAYS = [
  { angle: -90, long: true },  { angle: -75, long: false },
  { angle: -60, long: true },  { angle: -45, long: false },
  { angle: -30, long: true },  { angle: -15, long: false },
  { angle:   0, long: true },  { angle:  15, long: false },
  { angle:  30, long: true },  { angle:  45, long: false },
  { angle:  60, long: true },  { angle:  75, long: false },
  { angle:  90, long: true },
];

function toRad(deg: number) { return (deg * Math.PI) / 180; }

function RisingSun() {
  const cx = 28, cy = 36, innerR = 15;
  const color = "#c9a84c";
  return (
    <svg
      width="80" height="50" viewBox="0 0 56 36" fill="none"
      style={{ filter: `drop-shadow(0 0 8px ${color}55)`, animation: "sun-glow 3s ease-in-out infinite", overflow: "hidden", display: "block" }}
    >
      <defs>
        <clipPath id="regional-sun-clip">
          <rect x="0" y="0" width="56" height="37" />
        </clipPath>
      </defs>
      <g clipPath="url(#regional-sun-clip)">
        {SUN_RAYS.map((r, i) => {
          const rad = toRad(r.angle - 90);
          const len = r.long ? 9 : 6;
          const x1 = cx + Math.cos(rad) * (innerR + 3);
          const y1 = cy + Math.sin(rad) * (innerR + 3);
          const x2 = cx + Math.cos(rad) * (innerR + 3 + len);
          const y2 = cy + Math.sin(rad) * (innerR + 3 + len);
          return (
            <line
              key={i}
              x1={x1} y1={y1} x2={x2} y2={y2}
              className="sun-ray"
              style={{ stroke: color, animationDelay: `${i * 0.18}s` }}
            />
          );
        })}
        <path
          d={`M ${cx - innerR} ${cy} A ${innerR} ${innerR} 0 0 1 ${cx + innerR} ${cy} Z`}
          fill={color}
        />
      </g>
    </svg>
  );
}

// ── Component ───────────────────────────────────────────────────────────

export default function RegionalUnificationMap() {
  const [unified, setUnified] = useState(false);
  const [visible, setVisible] = useState(false);
  const ref = useRef<HTMLDivElement>(null);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const observer = new IntersectionObserver(
      ([entry]) => setVisible(entry.isIntersecting),
      { threshold: 0.1 },
    );
    observer.observe(el);
    return () => observer.disconnect();
  }, []);

  useEffect(() => {
    if (!visible) {
      setUnified(false);
      if (timerRef.current) clearTimeout(timerRef.current);
      return;
    }

    function cycle() {
      setUnified(true);
      timerRef.current = setTimeout(() => {
        setUnified(false);
        timerRef.current = setTimeout(cycle, 2000);
      }, 5000);
    }

    timerRef.current = setTimeout(cycle, 500);

    return () => { if (timerRef.current) clearTimeout(timerRef.current); };
  }, [visible]);

  return (
    <div ref={ref} style={{ position: "relative", width: "100%", minHeight: 440 }}>
      {/* Kallipolis sun — centered on the map */}
      <div style={{
        position: "absolute",
        top: "42%",
        left: "38%",
        transform: "translate(-50%, -50%)",
        zIndex: 10,
        opacity: 0.8,
      }}>
        <RisingSun />
      </div>

      <ComposableMap
        width={460}
        height={440}
        projection="geoMercator"
        projectionConfig={{ center: [-119, 37.5], scale: 2400 }}
        style={{ width: "100%", height: "auto" }}
      >
        <Geographies geography="/california-counties.geojson">
          {({ geographies }) => {
            const grouped = new Map<string, typeof geographies>();
            for (const geo of geographies) {
              const region = COUNTY_TO_REGION[geo.properties.name as string] ?? "CVML";
              if (!grouped.has(region)) grouped.set(region, []);
              grouped.get(region)!.push(geo);
            }

            return Array.from(grouped.entries()).map(([regionKey, geos]) => {
              const region = REGIONS[regionKey];
              if (!region) return null;
              return (
                <g
                  key={regionKey}
                  style={{
                    transform: unified
                      ? "translate(0px, 0px)"
                      : `translate(${region.dx}px, ${region.dy}px)`,
                    opacity: unified ? 1 : 0.6,
                    transition: `transform 2.2s ease-out ${region.delay}s, opacity 1.5s ease-out ${region.delay}s`,
                  }}
                >
                  {geos.map((geo) => (
                    <Geography
                      key={geo.rsmKey}
                      geography={geo}
                      style={{
                        default: { fill: region.color, stroke: "#060d1f", strokeWidth: 0.5, outline: "none" },
                        hover: { fill: region.color, outline: "none" },
                        pressed: { fill: region.color, outline: "none" },
                      }}
                    />
                  ))}
                </g>
              );
            });
          }}
        </Geographies>
      </ComposableMap>
    </div>
  );
}
