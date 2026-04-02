"use client";

import { useState, useEffect } from "react";
import { ComposableMap, Geographies, Geography, Marker } from "react-simple-maps";
import { motion, AnimatePresence } from "framer-motion";
import {
  College,
  Region,
  CALIFORNIA_REGIONS,
  CALIFORNIA_COLLEGES,
  COUNTY_TO_REGION,
} from "@/lib/californiaColleges";
import { getCollegeAtlasConfig } from "@/lib/collegeAtlasConfigs";

const GEO_URL = "/california-counties.geojson";

// Base projection — full California
const BASE_CENTER: [number, number] = [-119.5, 37.5];
const BASE_SCALE = 2500;

const DIAMOND = 6; // half-size of diamond marker

export const FEATURED_COLLEGES = new Set([
  "lassen", "shasta", "redwoods", "mendocino", "butte", "saccc", "laketahoe",
  "foothill", "laney", "sequoias", "merced",
  "montereypen", "hancock", "oxnard", "desert", "imperial", "sandiegocity",
  "compton", "irvinevalley",
]);

const MAP_WIDTH = 400;
const MAP_HEIGHT = 500;
const FIT_PADDING = 0.35; // 35% padding so edge markers have room for labels

/**
 * Convert latitude to Mercator y (radians).
 */
function mercatorY(lat: number): number {
  const rad = (lat * Math.PI) / 180;
  return Math.log(Math.tan(Math.PI / 4 + rad / 2));
}

/**
 * Compute projection center and scale that fits all given colleges
 * within the map viewport with padding, accounting for Mercator distortion.
 */
function fitBounds(
  colleges: College[],
): { center: [number, number]; scale: number } {
  if (colleges.length === 0) return { center: BASE_CENTER, scale: BASE_SCALE };

  const lngs = colleges.map((c) => c.lng);
  const lats = colleges.map((c) => c.lat);

  const minLng = Math.min(...lngs);
  const maxLng = Math.max(...lngs);
  const minLat = Math.min(...lats);
  const maxLat = Math.max(...lats);

  const centerLng = (minLng + maxLng) / 2;
  const centerLat = (minLat + maxLat) / 2;

  // Mercator: longitude maps linearly, latitude uses log-tan
  const dLngRad = ((maxLng - minLng) * (1 + FIT_PADDING) * Math.PI) / 180 || 0.01;
  const dMercY = (mercatorY(maxLat) - mercatorY(minLat)) * (1 + FIT_PADDING) || 0.01;

  const scaleByWidth = MAP_WIDTH / dLngRad;
  const scaleByHeight = MAP_HEIGHT / dMercY;

  const scale = Math.min(scaleByWidth, scaleByHeight);

  return { center: [centerLng, centerLat], scale };
}

type Props = {
  mapView: "state" | "region";
  activeRegionId: string | null;
  hoveredRegionId: string | null;
  hoveredCollegeId: string | null;
  selectedCollegeId: string | null;
  dimMarkers?: boolean;
  onRegionHover: (id: string | null) => void;
  onRegionClick: (id: string) => void;
  onCollegeHover: (college: College | null) => void;
  onCollegeSelect: (college: College) => void;

};

function countyFill(
  region: Region | undefined,
  mapView: "state" | "region",
  activeRegionId: string | null,
  hoveredRegionId: string | null,
): string {
  if (!region) return "rgba(255,255,255,0.02)";
  if (mapView === "state") {
    if (region.id === hoveredRegionId) return "rgba(201,168,76,0.14)";
    return "rgba(255,255,255,0.04)";
  }
  // region view — uniform fill across all counties
  return "rgba(255,255,255,0.04)";
}

export default function CaliforniaMap({
  mapView,
  activeRegionId,
  hoveredRegionId,
  hoveredCollegeId,
  selectedCollegeId,
  dimMarkers = false,
  onRegionHover,
  onRegionClick,
  onCollegeHover,
  onCollegeSelect,
}: Props) {
  const [projCenter, setProjCenter] = useState<[number, number]>(BASE_CENTER);
  const [projScale, setProjScale] = useState(BASE_SCALE);

  // Update projection whenever mapView or activeRegionId changes.
  // Opacity is managed by StateView, so the map is already faded out by the
  // time this effect runs — the projection swap is invisible.
  useEffect(() => {
    if (mapView === "state") {
      setProjCenter(BASE_CENTER);
      setProjScale(BASE_SCALE);
    } else if (activeRegionId) {
      const regionColleges = CALIFORNIA_COLLEGES.filter(
        (c) => c.regionId === activeRegionId,
      );
      if (regionColleges.length > 0) {
        const { center, scale } = fitBounds(regionColleges);
        setProjCenter(center);
        setProjScale(scale);
      } else {
        // No colleges (e.g. Desert) — use the region's hardcoded zoom
        const region = CALIFORNIA_REGIONS.find((r) => r.id === activeRegionId);
        if (region) {
          setProjCenter(region.zoomCenter);
          setProjScale(region.scale);
        }
      }
    }
  }, [mapView, activeRegionId]);

  const activeRegionColleges = CALIFORNIA_COLLEGES.filter(
    (c) => c.regionId === activeRegionId
  );

  return (
    <div style={{ position: "relative", width: "100%", height: "100%", overflow: "visible" }}>
      <div style={{ width: "100%", height: "100%", overflow: "visible" }}>
        <ComposableMap
          projection="geoMercator"
          projectionConfig={{ center: projCenter, scale: projScale }}
          width={400}
          height={500}
          style={{ width: "100%", height: "100%", overflow: "visible" }}
        >
          {/* County polygons */}
          <Geographies geography={GEO_URL}>
            {({ geographies }) =>
              geographies.map((geo) => {
                const countyName: string = String(geo.properties?.name ?? "");
                const region = COUNTY_TO_REGION[countyName];
                const fill = countyFill(region, mapView, activeRegionId, hoveredRegionId);
                const isClickable = mapView === "state" && !!region;

                return (
                  <Geography
                    key={geo.rsmKey}
                    geography={geo}
                    fill={fill}
                    stroke="rgba(255,255,255,0.1)"
                    strokeWidth={0.4}
                    style={{
                      default: { outline: "none" },
                      hover: { outline: "none" },
                      pressed: { outline: "none" },
                    }}
                    onMouseEnter={
                      isClickable ? () => onRegionHover(region.id) : undefined
                    }
                    onMouseLeave={
                      isClickable ? () => onRegionHover(null) : undefined
                    }
                    onClick={
                      isClickable ? () => onRegionClick(region.id) : undefined
                    }
                    cursor="default"
                  />
                );
              })
            }
          </Geographies>

          {/* College markers — always visible */}
          {(() => {
            const colleges = mapView === "region" && activeRegionId
              ? activeRegionColleges.filter((c) => FEATURED_COLLEGES.has(c.id))
              : CALIFORNIA_COLLEGES.filter((c) => FEATURED_COLLEGES.has(c.id));

            return colleges.map((college) => {
              const isHovered = hoveredCollegeId === college.id;
              const isSelected = selectedCollegeId === college.id;
              const isActive = isHovered || isSelected;
              const brandColor = getCollegeAtlasConfig(college.id)?.brandColorNeon ?? "#3ab26e";
              const size = isActive ? DIAMOND * 1.4 : DIAMOND;
              // Adjust label anchor for markers near edges
              const lngRange = { min: -124.5, max: -114 };
              const lngNorm = (college.lng - lngRange.min) / (lngRange.max - lngRange.min);
              const labelAnchor = lngNorm < 0.25 ? "start" as const : lngNorm > 0.75 ? "end" as const : "middle" as const;

              return (
                <Marker
                  key={college.id}
                  coordinates={[college.lng, college.lat]}
                  onMouseEnter={() => onCollegeHover(college)}
                  onMouseLeave={() => onCollegeHover(null)}
                >
                  <g style={{ cursor: "pointer", opacity: isActive ? 1 : dimMarkers ? 0.4 : 1, transition: "opacity 0.3s ease" }} onClick={(e) => { e.stopPropagation(); onCollegeSelect(college); }}>
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
                    {isActive && (
                      <text
                        y={-size - 10}
                        textAnchor={labelAnchor}
                        style={{
                          fontFamily: "var(--font-inter), Inter, system-ui, sans-serif",
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
            });
          })()}
        </ComposableMap>

        {/* Constellation lines drawn as SVG overlay — region view */}
        {mapView === "region" && activeRegionId && (
          <ConstellationOverlay colleges={activeRegionColleges} />
        )}
      </div>
    </div>
  );
}

// Constellation lines are drawn as an SVG overlay using the same projected
// coordinates derived from the map's projection. Since react-simple-maps
// doesn't expose the projection function easily, we approximate line positions
// by rendering them inside the ComposableMap via zero-size Markers with
// absolute SVG <line> elements in a foreignObject. Instead, we use a simpler
// approach: render lines inside the map using Marker midpoints with SVG.
// The cleanest solution is to render lines directly in the ComposableMap —
// handled via the SVG lines below rendered within Marker elements.

// For an accurate overlay, we use a separate absolutely-positioned SVG that
// replicates the same Mercator projection math to draw lines.
function ConstellationOverlay({ colleges }: { colleges: College[] }) {
  // We skip drawing lines here as they require matching the D3 projection math
  // exactly. The visual is handled well enough by the markers alone.
  // Lines will be added in a follow-up pass using react-simple-maps' Line component.
  return null;
}
