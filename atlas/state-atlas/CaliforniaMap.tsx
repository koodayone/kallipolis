"use client";

import { ComposableMap, Geographies, Geography, Marker } from "react-simple-maps";
import {
  College,
  Region,
  CALIFORNIA_COLLEGES,
  COUNTY_TO_REGION,
} from "@/state-atlas/californiaColleges";
import { getCollegeAtlasConfig } from "@/config/collegeAtlasConfigs";

const GEO_URL = "/california-counties.geojson";

const BASE_CENTER: [number, number] = [-119.5, 37.5];
const BASE_SCALE = 2500;

const DIAMOND = 6;

export const FEATURED_COLLEGES = new Set([
  "lassen", "shasta", "redwoods", "mendocino", "butte", "saccc", "laketahoe",
  "foothill", "laney", "sequoias", "merced",
  "montereypen", "hancock", "oxnard", "desert", "imperial", "sandiegocity",
  "compton", "irvinevalley",
]);

type Props = {
  hoveredRegionId: string | null;
  hoveredCollegeId: string | null;
  selectedCollegeId: string | null;
  dimMarkers?: boolean;
  onRegionHover: (id: string | null) => void;
  onCollegeHover: (college: College | null) => void;
  onCollegeSelect: (college: College) => void;
};

function countyFill(region: Region | undefined, hoveredRegionId: string | null): string {
  if (!region) return "rgba(255,255,255,0.02)";
  if (region.id === hoveredRegionId) return "rgba(201,168,76,0.14)";
  return "rgba(255,255,255,0.04)";
}

export default function CaliforniaMap({
  hoveredRegionId,
  hoveredCollegeId,
  selectedCollegeId,
  dimMarkers = false,
  onRegionHover,
  onCollegeHover,
  onCollegeSelect,
}: Props) {
  return (
    <div style={{ position: "relative", width: "100%", height: "100%", overflow: "visible" }}>
      <div style={{ width: "100%", height: "100%", overflow: "visible" }}>
        <ComposableMap
          projection="geoMercator"
          projectionConfig={{ center: BASE_CENTER, scale: BASE_SCALE }}
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
                const fill = countyFill(region, hoveredRegionId);

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
                    onMouseEnter={region ? () => onRegionHover(region.id) : undefined}
                    onMouseLeave={region ? () => onRegionHover(null) : undefined}
                    cursor="default"
                  />
                );
              })
            }
          </Geographies>

          {/* College markers */}
          {CALIFORNIA_COLLEGES.filter((c) => FEATURED_COLLEGES.has(c.id)).map((college) => {
            const isHovered = hoveredCollegeId === college.id;
            const isSelected = selectedCollegeId === college.id;
            const isActive = isHovered || isSelected;
            const brandColor = getCollegeAtlasConfig(college.id)?.brandColorNeon ?? "#3ab26e";
            const size = isActive ? DIAMOND * 1.4 : DIAMOND;
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
                  {isActive && (
                    <circle
                      r={size * 1.7}
                      fill="none"
                      stroke={brandColor}
                      strokeWidth="0.8"
                      strokeOpacity={0.45}
                    />
                  )}
                  <rect
                    x={-size / 2}
                    y={-size / 2}
                    width={size}
                    height={size}
                    fill={brandColor}
                    transform="rotate(45)"
                    style={{ transition: "fill 0.15s" }}
                  />
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
          })}
        </ComposableMap>
      </div>
    </div>
  );
}
