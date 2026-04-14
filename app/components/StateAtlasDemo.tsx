"use client";

import { useState, useRef, useEffect, useMemo } from "react";
import dynamic from "next/dynamic";

const StateMap = dynamic(() => import("./StateMap"), { ssr: false });

// ── Inline RisingSun (adapted from atlas/ui/RisingSun.tsx) ───────────────────

const RAYS = [
  { angle: -90, long: true  },
  { angle: -75, long: false },
  { angle: -60, long: true  },
  { angle: -45, long: false },
  { angle: -30, long: true  },
  { angle: -15, long: false },
  { angle:   0, long: true  },
  { angle:  15, long: false },
  { angle:  30, long: true  },
  { angle:  45, long: false },
  { angle:  60, long: true  },
  { angle:  75, long: false },
  { angle:  90, long: true  },
];

function toRad(deg: number) { return (deg * Math.PI) / 180; }

function RisingSun({ color }: { color: string }) {
  const cx = 28, cy = 36, innerR = 15;
  return (
    <svg
      width="94" height="60" viewBox="0 0 56 36" fill="none"
      style={{ filter: `drop-shadow(0 0 8px ${color}55)`, animation: "sun-glow 3s ease-in-out infinite", overflow: "hidden", display: "block", margin: "0 auto" }}
    >
      <defs>
        <clipPath id="demo-sun-clip">
          <rect x="0" y="0" width="56" height="37" />
        </clipPath>
      </defs>
      <g clipPath="url(#demo-sun-clip)">
        {RAYS.map((r, i) => {
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

// ── College data (subset for demo) ──────────────────────────────────────────

type DemoCollege = {
  id: string;
  name: string;
  district: string;
  neonColor: string;
};

const DEMO_COLLEGES: DemoCollege[] = [
  { id: "shasta",      name: "Shasta College",                 district: "Shasta-Tehama-Trinity JCCD", neonColor: "#2bee64" },
  { id: "lassen",      name: "Lassen College",                 district: "Lassen CCD",                 neonColor: "#f07c42" },
  { id: "laketahoe",   name: "Lake Tahoe Community College",   district: "Lake Tahoe CCD",             neonColor: "#4fd1fd" },
  { id: "foothill",    name: "Foothill College",               district: "Foothill-De Anza CCD",       neonColor: "#f0425e" },
  { id: "sequoias",    name: "College of the Sequoias",        district: "Sequoias CCD",               neonColor: "#b9ff1a" },
  { id: "compton",     name: "Compton College",                district: "Compton CCD",                neonColor: "#f04283" },
  { id: "desert",      name: "College of the Desert",          district: "Desert CCD",                 neonColor: "#ffc933" },
  { id: "butte",       name: "Butte College",                  district: "Butte-Glenn CCD",            neonColor: "#f07c42" },
  { id: "redwoods",    name: "College of the Redwoods",        district: "Redwoods CCD",               neonColor: "#2bee64" },
  { id: "mendocino",   name: "Mendocino College",              district: "Mendocino-Lake CCD",         neonColor: "#4fd1fd" },
  { id: "saccc",       name: "Sacramento City College",        district: "Los Rios CCD",               neonColor: "#f0425e" },
  { id: "montereypen", name: "Monterey Peninsula College",     district: "Monterey Peninsula CCD",     neonColor: "#4fd1fd" },
  { id: "sandiegocity",name: "San Diego City College",         district: "San Diego CCD",              neonColor: "#f07c42" },
  { id: "imperial",    name: "Imperial Valley College",        district: "Imperial CCD",               neonColor: "#ffc933" },
  { id: "irvinevalley",name: "Irvine Valley College",          district: "South Orange County CCD",    neonColor: "#2bee64" },
];

// ── Demo target ─────────────────────────────────────────────────────────────

const TARGET_COLLEGE = DEMO_COLLEGES.find((c) => c.id === "foothill")!;
const TARGET_QUERY = "foothill college";

// ── Component ───────────────────────────────────────────────────────────────

export default function StateAtlasDemo() {
  const [searchQuery, setSearchQuery] = useState("");
  const [searchFocused, setSearchFocused] = useState(false);
  const [selectedCollege, setSelectedCollege] = useState<DemoCollege | null>(null);
  const [activeIndex, setActiveIndex] = useState(-1);
  const [visible, setVisible] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const searchResults = useMemo(() => {
    const q = searchQuery.trim().toLowerCase();
    if (q.length === 0) return DEMO_COLLEGES;
    return DEMO_COLLEGES.filter((c) =>
      c.name.toLowerCase().includes(q) || c.district.toLowerCase().includes(q)
    );
  }, [searchQuery]);

  const showResults = searchFocused || searchQuery.trim().length > 0;

  const sunColor = "#c9a84c";
  const sunLabel = selectedCollege?.name ?? "Select a college";

  // Viewport observer
  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    const observer = new IntersectionObserver(
      ([entry]) => { if (entry.isIntersecting && !visible) setVisible(true); },
      { threshold: 0.3 },
    );
    observer.observe(el);
    return () => observer.disconnect();
  }, [visible]);

  // Automated demo sequence
  useEffect(() => {
    if (!visible) return;

    function clearTimer() {
      if (timerRef.current) clearTimeout(timerRef.current);
    }

    function runCycle() {
      // Reset
      setSearchQuery("");
      setSearchFocused(false);
      setSelectedCollege(null);
      setActiveIndex(-1);

      // Step 1: Focus search bar — shows full college list
      timerRef.current = setTimeout(() => {
        setSearchFocused(true);

        // Step 2: Pause to let the full list be visible, then start typing
        timerRef.current = setTimeout(() => {
          let i = 0;
          const typeInterval = setInterval(() => {
            i++;
            setSearchQuery(TARGET_QUERY.slice(0, i));
            if (i >= TARGET_QUERY.length) {
              clearInterval(typeInterval);

              // Step 3: Pause after typing, then highlight Foothill in results
              timerRef.current = setTimeout(() => {
                const filtered = DEMO_COLLEGES.filter((c) =>
                  c.name.toLowerCase().includes(TARGET_QUERY)
                );
                const idx = filtered.findIndex((c) => c.id === TARGET_COLLEGE.id);
                setActiveIndex(idx >= 0 ? idx : 0);

                // Step 4: Pause on highlight, then select
                timerRef.current = setTimeout(() => {
                  setSearchQuery("");
                  setSearchFocused(false);
                  setActiveIndex(-1);
                  setSelectedCollege(TARGET_COLLEGE);

                  // Step 5: Hold on selected state, then restart
                  timerRef.current = setTimeout(runCycle, 8000);
                }, 2000);
              }, 1500);
            }
          }, 95);
        }, 3000);
      }, 2500);
    }

    runCycle();

    return clearTimer;
  }, [visible]);

  return (
    <div ref={containerRef} style={{ display: "flex", gap: 0, alignItems: "stretch" }}>

      {/* Left — Map panel containing search, map, sun, and results */}
      <div style={{
        flex: "0 0 55%", position: "relative", minHeight: 480,
        borderRadius: 10, overflow: "hidden",
        border: "1px solid rgba(255,255,255,0.06)",
        padding: "8px 24px 24px",
      }}>
        {/* Search bar */}
        <div style={{ marginBottom: 0 }}>
          <div
            style={{
              display: "flex", alignItems: "center", gap: 12,
              padding: "0 16px", height: 40,
              background: searchFocused ? "rgba(255,255,255,0.06)" : "rgba(255,255,255,0.03)",
              border: `1px solid ${searchFocused ? "rgba(240,66,94,0.4)" : "rgba(255,255,255,0.08)"}`,
              borderRadius: 6,
              transition: "all 0.2s ease",
            }}
          >
            <svg width="14" height="14" viewBox="0 0 16 16" fill="none" style={{ flexShrink: 0, opacity: searchFocused ? 0.8 : 0.4, transition: "opacity 0.2s" }}>
              <circle cx="7" cy="7" r="5" stroke="rgba(255,255,255,0.9)" strokeWidth="1.3" />
              <path d="M11 11l3.5 3.5" stroke="rgba(255,255,255,0.9)" strokeWidth="1.3" strokeLinecap="round" />
            </svg>
            <div style={{ flex: 1, minHeight: 20 }}>
              {searchQuery ? (
                <span style={{ fontSize: 13, color: "rgba(255,255,255,0.85)" }}>
                  {searchQuery}
                  {searchFocused && <span style={{ opacity: 0.6, animation: "blink 1s step-end infinite" }}>|</span>}
                </span>
              ) : (
                <span style={{ fontSize: 13, color: "rgba(255,255,255,0.25)" }}>
                  Search colleges...
                </span>
              )}
            </div>
          </div>
        </div>

        {/* Map */}
        <div style={{ maxWidth: 440, marginTop: 28 }}>
          <StateMap activeCollegeId={selectedCollege?.id ?? null} brightenAll={!selectedCollege} />
        </div>

        {/* RisingSun + label — absolute in Nevada space, hidden when results show */}
        {!showResults && (
          <div
            style={{
              position: "absolute",
              right: "22%",
              top: "22%",
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              pointerEvents: "none",
            }}
          >
            <div style={{ transition: "opacity 0.4s ease-in-out", opacity: selectedCollege ? 1 : 0.45 }}>
              <RisingSun color={sunColor} />
            </div>
            <div style={{ position: "relative", height: 16, width: 0, marginTop: 10 }}>
              <span style={{
                position: "absolute",
                left: "50%",
                transform: "translateX(-50%)",
                fontSize: 11, fontWeight: 500,
                letterSpacing: "0.14em", textTransform: "uppercase",
                color: selectedCollege ? "rgba(255,255,255,0.9)" : "rgba(255,255,255,0.55)",
                whiteSpace: "nowrap",
                transition: "color 0.3s ease-in-out",
              }}>
                {sunLabel}
              </span>
            </div>
          </div>
        )}

        {/* Search results dropdown — absolute in Nevada space, replaces sun */}
        {showResults && (
          <div
            style={{
              position: "absolute",
              right: "24px",
              top: "12%",
              width: "40%",
              maxHeight: 260,
              overflowY: "auto",
              background: "rgba(6,13,31,0.95)",
              border: "1px solid rgba(255,255,255,0.08)",
              borderRadius: 6,
              padding: "4px 0",
              backdropFilter: "blur(12px)",
            }}
          >
            {searchResults.length === 0 ? (
              <div style={{ padding: "12px 16px", fontSize: 13, color: "rgba(255,255,255,0.4)" }}>
                No colleges matching &ldquo;{searchQuery}&rdquo;
              </div>
            ) : (
              searchResults.map((college, i) => (
                <div
                  key={college.id}
                  style={{
                    display: "flex", alignItems: "center", gap: 12,
                    padding: "10px 14px", width: "100%",
                    background: i === activeIndex ? "rgba(255,255,255,0.06)" : "transparent",
                    borderRadius: 2,
                    transition: "background 0.12s ease",
                  }}
                >
                  <div style={{
                    width: 3, height: 28, borderRadius: 2,
                    background: college.neonColor, opacity: 0.7, flexShrink: 0,
                  }} />
                  <div style={{ display: "flex", flexDirection: "column", gap: 2, minWidth: 0 }}>
                    <span style={{ fontSize: 13, fontWeight: 600, color: "#ffffff", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
                      {college.name}
                    </span>
                    <span style={{ fontSize: 10, color: "rgba(255,255,255,0.35)", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
                      {college.district}
                    </span>
                  </div>
                </div>
              ))
            )}
          </div>
        )}
      </div>

      {/* Right — text */}
      <div style={{ flex: 1, display: "flex", flexDirection: "column", justifyContent: "center", gap: 40, paddingLeft: 48 }}>
        <div style={{ textAlign: "center" }}>
          <p style={{ fontSize: 13, fontWeight: 500, textTransform: "uppercase", letterSpacing: "0.15em", color: "rgba(255,255,255,0.4)", marginBottom: 16 }}>
            Two Scales
          </p>
          <div style={{ width: 64, height: 2, background: "#f0425e", borderRadius: 1, opacity: 0.9, margin: "0 auto 24px" }} />
          <h2
            className="text-[24px] md:text-[32px] leading-[1.12] tracking-[-0.02em] text-white"
            style={{ fontFamily: "var(--font-days-one)", fontWeight: 400 }}
          >
            From the state<br />to the college
          </h2>
        </div>

        <div style={{ display: "flex", flexDirection: "column", gap: 24 }}>
          <div>
            <span style={{ fontSize: 13, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.1em", color: "#f0425e", display: "block", marginBottom: 6 }}>
              State Atlas
            </span>
            <p style={{ fontSize: 16, lineHeight: 1.6, color: "rgba(255,255,255,0.65)", margin: 0 }}>
              116 colleges across 73 districts and 8 regional consortia. Search for any college, and the atlas surfaces it in context.
            </p>
          </div>
          <div>
            <span style={{ fontSize: 13, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.1em", color: "#f0425e", display: "block", marginBottom: 6 }}>
              College Atlas
            </span>
            <p style={{ fontSize: 16, lineHeight: 1.6, color: "rgba(255,255,255,0.65)", margin: 0 }}>
              A college atlas opens into six forms, each representing an element of a workforce development worldview.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
