"use client";

import { useState, useRef, useEffect, useMemo } from "react";
import dynamic from "next/dynamic";
import MiniFormCell from "./MiniFormCell";
import {
  createMortarboardForm,
  createBookForm,
  createChainlinkForm,
  createHardhatForm,
  createSkyscraperForm,
  createDumbbellForm,
} from "../lib/formFactories";

const StateMap = dynamic(() => import("./StateMap"), { ssr: false });

// ── Inline RisingSun ───────────────────────────────────────────────────────

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

// ── College data ───────────────────────────────────────────────────────────

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

const TARGET_COLLEGE = DEMO_COLLEGES.find((c) => c.id === "foothill")!;
const TARGET_QUERY = "foothill college";

const COLLEGE_FORMS = [
  { factory: createMortarboardForm, label: "Students" },
  { factory: createChainlinkForm,   label: "Partnerships" },
  { factory: createSkyscraperForm,  label: "Employers" },
  { factory: createBookForm,        label: "Courses" },
  { factory: createDumbbellForm,    label: "Strong Workforce" },
  { factory: createHardhatForm,     label: "Occupations" },
];

// ── Component ──────────────────────────────────────────────────────────────

export default function StateAtlasDemo() {
  const [searchQuery, setSearchQuery] = useState("");
  const [searchFocused, setSearchFocused] = useState(false);
  const [selectedCollege, setSelectedCollege] = useState<DemoCollege | null>(null);
  const [activeIndex, setActiveIndex] = useState(-1);
  const [visible, setVisible] = useState(false);
  const [phase, setPhase] = useState<"atlas" | "college">("atlas");
  const [showOpenButton, setShowOpenButton] = useState(false);
  const [buttonPressed, setButtonPressed] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const intervalsRef = useRef<ReturnType<typeof setInterval>[]>([]);

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

  useEffect(() => {
    if (!visible) return;

    function clearTimers() {
      if (timerRef.current) clearTimeout(timerRef.current);
      for (const id of intervalsRef.current) clearInterval(id);
      intervalsRef.current = [];
    }

    function schedule(fn: () => void, ms: number) {
      timerRef.current = setTimeout(fn, ms);
    }

    function runCycle() {
      clearTimers();
      setSearchQuery("");
      setSearchFocused(false);
      setSelectedCollege(null);
      setActiveIndex(-1);
      setShowOpenButton(false);
      setButtonPressed(false);
      setPhase("atlas");

      schedule(() => {
        setSearchFocused(true);

        schedule(() => {
          let i = 0;
          const typeInterval = setInterval(() => {
            i++;
            setSearchQuery(TARGET_QUERY.slice(0, i));
            if (i >= TARGET_QUERY.length) {
              clearInterval(typeInterval);

              schedule(() => {
                const filtered = DEMO_COLLEGES.filter((c) =>
                  c.name.toLowerCase().includes(TARGET_QUERY)
                );
                const idx = filtered.findIndex((c) => c.id === TARGET_COLLEGE.id);
                setActiveIndex(idx >= 0 ? idx : 0);

                schedule(() => {
                  setSearchQuery("");
                  setSearchFocused(false);
                  setActiveIndex(-1);
                  setSelectedCollege(TARGET_COLLEGE);

                  // Show the "Open College Atlas" button
                  schedule(() => {
                    setShowOpenButton(true);

                    // Press the button
                    schedule(() => {
                      setButtonPressed(true);

                      // Transition to college forms
                      schedule(() => {
                        setPhase("college");

                        // Cycle back to atlas
                        schedule(runCycle, 5000);
                      }, 600);
                    }, 1200);
                  }, 1500);
                }, 2000);
              }, 1500);
            }
          }, 95);
          intervalsRef.current.push(typeInterval);
        }, 3000);
      }, 2500);
    }

    runCycle();

    return clearTimers;
  }, [visible]);

  const collegeColor = 0xf0425e;

  return (
    <div ref={containerRef} style={{ display: "flex", gap: 0, alignItems: "stretch" }}>

      {/* Left — Map / College forms panel */}
      <div style={{
        flex: "0 0 55%", position: "relative", minHeight: 530,
        borderRadius: 10, overflow: "hidden",
        border: "1px solid rgba(255,255,255,0.06)",
      }}>

        {/* Atlas phase — map + search */}
        <div style={{
          position: "absolute",
          inset: 0,
          padding: "8px 24px 40px",
          opacity: phase === "atlas" ? 1 : 0,
          transition: "opacity 0.8s ease",
          pointerEvents: phase === "atlas" ? "auto" : "none",
          display: "flex",
          flexDirection: "column",
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
          <div style={{ maxWidth: 500, marginTop: 28, flex: 1, minHeight: 0 }}>
            <StateMap activeCollegeId={selectedCollege?.id ?? null} brightenAll={!selectedCollege} />
          </div>

          {/* RisingSun + label + Open button */}
          {!showResults && (
            <div
              style={{
                position: "absolute",
                right: "12%",
                top: "16%",
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

              {/* Open College Atlas button */}
              <div style={{
                marginTop: 20,
                opacity: showOpenButton ? 1 : 0,
                transform: showOpenButton ? "translateY(0)" : "translateY(6px)",
                transition: "opacity 0.4s ease, transform 0.4s ease",
              }}>
                <div style={{
                  display: "inline-flex",
                  alignItems: "center",
                  gap: 8,
                  padding: "6px 14px",
                  border: `1px solid ${buttonPressed ? "#f0425e" : "rgba(240,66,94,0.5)"}`,
                  borderRadius: 5,
                  background: buttonPressed ? "rgba(240,66,94,0.15)" : "transparent",
                  boxShadow: buttonPressed ? "0 0 12px rgba(240,66,94,0.3)" : "none",
                  transform: buttonPressed ? "scale(1.05)" : "scale(1)",
                  transition: "all 0.25s ease",
                }}>
                  <span style={{
                    fontSize: 9,
                    fontWeight: 600,
                    letterSpacing: "0.14em",
                    textTransform: "uppercase",
                    color: buttonPressed ? "#ffffff" : "#f0425e",
                    transition: "color 0.25s ease",
                    whiteSpace: "nowrap",
                  }}>
                    Open College Atlas
                  </span>
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none">
                    <path d="M12 2L3 7.5 12 13l9-5.5L12 2z" fill={buttonPressed ? "#ffffff" : "#f0425e"} opacity="0.85" />
                    <path d="M12 13v9l9-5.5v-9L12 13z" fill={buttonPressed ? "#ffffff" : "#f0425e"} opacity="0.55" />
                    <path d="M12 13v9L3 16.5v-9L12 13z" fill={buttonPressed ? "#ffffff" : "#f0425e"} opacity="0.4" />
                  </svg>
                </div>
              </div>
            </div>
          )}

          {/* Search results dropdown */}
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

        {/* College phase — six forms grid */}
        <div style={{
          position: "absolute",
          inset: 0,
          padding: "8px 24px 24px",
          opacity: phase === "college" ? 1 : 0,
          transition: "opacity 0.8s ease",
          pointerEvents: phase === "college" ? "auto" : "none",
          display: "flex",
          flexDirection: "column",
        }}>
          <h3 style={{
            fontFamily: "var(--font-days-one)",
            fontWeight: 400,
            fontSize: 18,
            color: "rgba(255,255,255,0.85)",
            textAlign: "center",
            textTransform: "uppercase",
            letterSpacing: "0.08em",
            margin: "12px 0 16px",
          }}>
            Foothill College
          </h3>
          <div style={{
            width: "100%", height: 1, background: "rgba(255,255,255,0.08)",
            margin: "0 0 12px",
          }} />
          <div style={{
            display: "grid",
            gridTemplateColumns: "repeat(3, 1fr)",
            gap: 16,
            flex: 1,
            alignContent: "center",
            padding: "8px 12px",
          }}>
            {COLLEGE_FORMS.map((form) => (
              <MiniFormCell
                key={form.label}
                factory={form.factory}
                label={form.label}
                color={collegeColor}
                active={phase === "college"}
              />
            ))}
          </div>
        </div>
      </div>

      {/* Right — text */}
      <div style={{ flex: 1, display: "flex", flexDirection: "column", justifyContent: "flex-start", gap: 40, paddingLeft: 48, paddingTop: 16 }}>
        <div style={{ textAlign: "center" }}>
          <p style={{ fontSize: 13, fontWeight: 500, textTransform: "uppercase", letterSpacing: "0.15em", color: "rgba(255,255,255,0.4)", marginBottom: 16 }}>
            Two Scales
          </p>
          <div style={{ width: 64, height: 2, background: "#f0425e", borderRadius: 1, opacity: 0.9, margin: "0 auto 24px" }} />
          <h2
            className="text-[26px] md:text-[30px] leading-[1.12] tracking-[-0.02em] text-white"
            style={{ fontFamily: "var(--font-days-one)", fontWeight: 400 }}
          >
            One system.<br />Every California college.
          </h2>
        </div>

        <div style={{ display: "flex", flexDirection: "column", gap: 36 }}>
          <div>
            <span style={{ fontSize: 12, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.12em", color: "#f0425e", display: "block", marginBottom: 6 }}>
              State Atlas
            </span>
            <p style={{ fontSize: 17, lineHeight: 1.6, color: "rgba(255,255,255,0.65)", margin: 0 }}>
              116 colleges across 73 districts and 8 regional consortia. Search for any college, and the atlas surfaces it in context.
            </p>
          </div>
          <div>
            <span style={{ fontSize: 12, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.12em", color: "#f0425e", display: "block", marginBottom: 6 }}>
              College Atlas
            </span>
            <p style={{ fontSize: 17, lineHeight: 1.6, color: "rgba(255,255,255,0.65)", margin: 0 }}>
              A college atlas opens into six forms, each representing an element of a workforce development worldview.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
