"use client";

import { ComposableMap, Geographies, Geography, Marker } from "react-simple-maps";
import {
  College,
  Region,
  CALIFORNIA_COLLEGES,
  CALIFORNIA_REGIONS,
  COUNTY_TO_REGION,
} from "@/state-atlas/californiaColleges";
import { getCollegeAtlasConfig } from "@/config/collegeAtlasConfigs";
import { FEATURED_COLLEGES } from "@/state-atlas/featuredColleges";
import { REGION_VIEWS } from "@/state-atlas/regionViews";

export { FEATURED_COLLEGES };

const GEO_URL = "/california-counties.geojson";

const DIAMOND = 6;

// At state view, diamonds are pure aesthetic — a constellation of dimmed
// brand-colored marks. They're not click targets; the regions are. When a
// region is hovered, its constellation lights up to full brightness; the
// rest stay dimmed.
const STATE_DIAMOND_DIM = 0.35;
const STATE_DIAMOND_LIT = 1.0;

type Props = {
  /** Animated camera. Tweens between STATE_VIEW and REGION_VIEWS[activeRegionId]. */
  cameraCenter: [number, number];
  cameraScale: number;

  /** Which view mode the atlas is in — drives which markers are clickable. */
  viewMode: "state" | "region";
  /** When viewMode === "region", the consortium currently filling the frame. */
  activeRegionId: string | null;

  hoveredRegionId: string | null;
  hoveredCollegeId: string | null;
  selectedCollegeId: string | null;
  dimMarkers?: boolean;

  onRegionHover: (id: string | null) => void;
  onRegionSelect: (id: string) => void;
  onCollegeHover: (college: College | null) => void;
  onCollegeSelect: (college: College) => void;
};

function countyFill(
  region: Region | undefined,
  hoveredRegionId: string | null,
  activeRegionId: string | null,
  viewMode: "state" | "region",
): string {
  if (!region) return "rgba(255,255,255,0.02)";

  if (viewMode === "region") {
    // Active region keeps its tint; other regions fade so the camera's
    // chosen region reads as foreground.
    if (region.id === activeRegionId) return "rgba(201,168,76,0.10)";
    return "rgba(255,255,255,0.015)";
  }

  // State view: hovered region tinted; others a soft baseline.
  if (region.id === hoveredRegionId) return "rgba(201,168,76,0.14)";
  return "rgba(255,255,255,0.04)";
}

export default function CaliforniaMap({
  cameraCenter,
  cameraScale,
  viewMode,
  activeRegionId,
  hoveredRegionId,
  hoveredCollegeId,
  selectedCollegeId,
  dimMarkers = false,
  onRegionHover,
  onRegionSelect,
  onCollegeHover,
  onCollegeSelect,
}: Props) {
  // Mercator projection matching the ComposableMap config below. Used to
  // compute the bounding rectangles of region labels in screen space so
  // diamonds that would peek out from under a label can be hidden at
  // state view (only). geoMercator with translate=[w/2, h/2] is the
  // d3-geo / react-simple-maps default.
  const project = (lng: number, lat: number): [number, number] => {
    const toRad = (d: number) => (d * Math.PI) / 180;
    const mercY = (l: number) => Math.log(Math.tan(Math.PI / 4 + toRad(l) / 2));
    const x = cameraScale * toRad(lng - cameraCenter[0]) + 200;
    const y = -cameraScale * (mercY(lat) - mercY(cameraCenter[1])) + 250;
    return [x, y];
  };

  // Pre-compute label rectangles in projected space. A diamond whose
  // center falls inside any rectangle will be skipped at state view —
  // keeps the labels readable instead of fighting a half-buried diamond.
  const labelRects: Array<{ x1: number; y1: number; x2: number; y2: number }> =
    viewMode !== "state" ? [] : CALIFORNIA_REGIONS.flatMap((region) => {
      const view = REGION_VIEWS[region.id];
      if (!view) return [];
      const [cx, cy] = project(view.labelAnchor[0], view.labelAnchor[1]);
      const parts = region.name.includes(" / ") ? region.name.split(" / ") : [region.name];
      // 10px uppercase Inter with 0.14em letter-spacing → ~6.5 px per char.
      const maxChars = Math.max(...parts.map((p) => p.length));
      const w = maxChars * 6.5;
      const h = parts.length === 2 ? 24 : 12;
      const padX = 8;
      const padY = 6;
      return [{
        x1: cx - w / 2 - padX,
        y1: cy - h / 2 - padY,
        x2: cx + w / 2 + padX,
        y2: cy + h / 2 + padY,
      }];
    });

  const inAnyLabelRect = (x: number, y: number): boolean =>
    labelRects.some((r) => x >= r.x1 && x <= r.x2 && y >= r.y1 && y <= r.y2);

  // Force-directed nudge for in-region markers at region view. Every
  // marker repels neighbors within MIN_DIST, with a weak spring pulling
  // it back to its true projected position. With ≤13 markers per region
  // and only one truly clipping pair across all regions (Foothill / De
  // Anza in BACCC, ~5 px apart at scale 4833), the nudge is bounded —
  // a few px translates to a couple of miles at regional zoom, well
  // under the floor of perceptual geographic precision.
  const nudgeOffsets = new Map<string, [number, number]>();
  if (viewMode === "region" && activeRegionId) {
    const inRegion = CALIFORNIA_COLLEGES.filter(
      (c) => FEATURED_COLLEGES.has(c.id) && c.regionId === activeRegionId,
    );
    type Pos = { id: string; x0: number; y0: number; x: number; y: number };
    const positions: Pos[] = inRegion.map((c) => {
      const [px, py] = project(c.lng, c.lat);
      return { id: c.id, x0: px, y0: py, x: px, y: py };
    });
    const MIN_DIST = 14;
    const SPRING = 0.15;
    const ITERATIONS = 40;
    for (let it = 0; it < ITERATIONS; it++) {
      for (let i = 0; i < positions.length; i++) {
        for (let j = i + 1; j < positions.length; j++) {
          const a = positions[i], b = positions[j];
          const dx = b.x - a.x;
          const dy = b.y - a.y;
          const d = Math.hypot(dx, dy) || 0.01;
          if (d < MIN_DIST) {
            const push = (MIN_DIST - d) / 2;
            const nx = dx / d;
            const ny = dy / d;
            a.x -= nx * push; a.y -= ny * push;
            b.x += nx * push; b.y += ny * push;
          }
        }
      }
      for (const p of positions) {
        p.x += (p.x0 - p.x) * SPRING;
        p.y += (p.y0 - p.y) * SPRING;
      }
    }
    for (const p of positions) {
      const dx = p.x - p.x0;
      const dy = p.y - p.y0;
      if (dx * dx + dy * dy > 0.25) {  // skip ~null offsets
        nudgeOffsets.set(p.id, [dx, dy]);
      }
    }
  }

  return (
    <div style={{ position: "relative", width: "100%", height: "100%", overflow: "visible" }}>
      <div style={{ width: "100%", height: "100%", overflow: "visible" }}>
        <ComposableMap
          projection="geoMercator"
          projectionConfig={{ center: cameraCenter, scale: cameraScale }}
          width={400}
          height={500}
          style={{ width: "100%", height: "100%", overflow: "visible" }}
        >
          {/* County polygons — at state view, clicks zoom to the region.
              At region view, they're inert. */}
          <Geographies geography={GEO_URL}>
            {({ geographies }) =>
              geographies.map((geo) => {
                const countyName: string = String(geo.properties?.name ?? "");
                const region = COUNTY_TO_REGION[countyName];
                const fill = countyFill(region, hoveredRegionId, activeRegionId, viewMode);
                const interactive = viewMode === "state" && !!region;

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
                    onMouseEnter={interactive ? () => onRegionHover(region.id) : undefined}
                    onMouseLeave={interactive ? () => onRegionHover(null) : undefined}
                    onClick={interactive ? () => onRegionSelect(region.id) : undefined}
                    cursor={interactive ? "pointer" : "default"}
                  />
                );
              })
            }
          </Geographies>

          {/* College markers */}
          {CALIFORNIA_COLLEGES.filter((c) => FEATURED_COLLEGES.has(c.id)).map((college) => {
            // At region view, only render in-region markers — out-of-region
            // colleges would clutter the frame and aren't selectable here.
            if (viewMode === "region" && college.regionId !== activeRegionId) {
              return null;
            }

            // At state view, hide diamonds that would sit under a region
            // label — otherwise the dimmed diamond peeks out from under
            // the white text and looks half-buried.
            if (viewMode === "state") {
              const [px, py] = project(college.lng, college.lat);
              if (inAnyLabelRect(px, py)) return null;
            }

            const isHovered = hoveredCollegeId === college.id;
            const isSelected = selectedCollegeId === college.id;
            const isActive = isHovered || isSelected;
            const brandColor = getCollegeAtlasConfig(college.id)?.brandColorNeon ?? "#3ab26e";
            const size = isActive ? DIAMOND * 1.4 : DIAMOND;

            // Opacity rule:
            //   region view → always full (1.0)
            //   state view, region hovered → that region's constellation lights up
            //   state view, no hover → all dim
            //   dimMarkers prop forces dim regardless (legacy escape hatch)
            let opacity: number;
            if (dimMarkers) {
              opacity = 0.4;
            } else if (viewMode === "region") {
              opacity = STATE_DIAMOND_LIT;
            } else if (hoveredRegionId === college.regionId) {
              opacity = STATE_DIAMOND_LIT;
            } else {
              opacity = STATE_DIAMOND_DIM;
            }

            // At state view, diamonds are not click targets. The whole
            // region is the target — clicks bubble to the polygon below.
            const markerInteractive = viewMode === "region";

            // Label rule: only show on hover or selection. Tried labels-at-
            // rest in regional view but tight clusters (Foothill/De Anza,
            // Berkeley/SF, etc.) still collide even at 2-3× zoom — the text
            // bounding boxes are wider than the inter-marker gaps. On-hover
            // labels keep the rest state clean.
            const showLabel = isActive;

            // Label anchor heuristic — point left or right so labels don't
            // run off the edge of the SVG.
            const lngRange = { min: -124.5, max: -114 };
            const lngNorm = (college.lng - lngRange.min) / (lngRange.max - lngRange.min);
            const labelAnchor = lngNorm < 0.25 ? "start" as const : lngNorm > 0.75 ? "end" as const : "middle" as const;

            // Apply force-directed nudge offset (region view only). For
            // most markers this is undefined — only clipping pairs move.
            const nudge = nudgeOffsets.get(college.id);
            const nudgeTransform = nudge ? `translate(${nudge[0]} ${nudge[1]})` : undefined;

            return (
              <Marker
                key={college.id}
                coordinates={[college.lng, college.lat]}
                onMouseEnter={markerInteractive ? () => onCollegeHover(college) : undefined}
                onMouseLeave={markerInteractive ? () => onCollegeHover(null) : undefined}
              >
                <g
                  style={{
                    cursor: markerInteractive ? "pointer" : "default",
                    pointerEvents: markerInteractive ? "auto" : "none",
                    opacity,
                    transition: "opacity 0.3s ease",
                  }}
                  transform={nudgeTransform}
                  onClick={
                    markerInteractive
                      ? (e) => { e.stopPropagation(); onCollegeSelect(college); }
                      : undefined
                  }
                >
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
                  {showLabel && (
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

          {/* Region labels — always-on at state view, hidden at region view
              (region context lives in the right-panel header when zoomed).
              Two-tier: name on top, acronym + featured count below. */}
          {viewMode === "state" && CALIFORNIA_REGIONS.map((region) => {
            const view = REGION_VIEWS[region.id];
            if (!view) return null;
            const isHovered = hoveredRegionId === region.id;

            // Compound names like "North / Far North" wrap to two lines so
            // they don't run wider than their territory at 12px.
            const parts = region.name.includes(" / ")
              ? region.name.split(" / ")
              : [region.name];

            const textStyle = {
              fontFamily: "var(--font-inter), Inter, system-ui, sans-serif",
              fontSize: "10px",
              fontWeight: 700,
              letterSpacing: "0.14em",
              textTransform: "uppercase" as const,
              fill: "#ffffff",
              userSelect: "none" as const,
            };

            return (
              <Marker key={`label-${region.id}`} coordinates={view.labelAnchor}>
                <g
                  style={{
                    pointerEvents: "none",          // clicks pass through to the polygon
                    opacity: isHovered ? 1.0 : 0.7,
                    transition: "opacity 0.25s ease",
                  }}
                >
                  {parts.length === 1 ? (
                    <text textAnchor="middle" y={4} style={textStyle}>
                      {parts[0]}
                    </text>
                  ) : (
                    <>
                      <text textAnchor="middle" y={-3} style={textStyle}>
                        {parts[0]}
                      </text>
                      <text textAnchor="middle" y={11} style={textStyle}>
                        {parts[1]}
                      </text>
                    </>
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
