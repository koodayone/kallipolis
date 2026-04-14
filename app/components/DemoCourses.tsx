"use client";

import { useDemoJourney, phaseAtLeast } from "../hooks/useDemoJourney";

const FONT = "var(--font-geist), system-ui, sans-serif";
const ACCENT = "#c9a84c";

const COURSES = [
  { code: "MFGT 110", name: "Introduction to Manufacturing Processes" },
  { code: "MFGT 145", name: "Industrial Safety and Quality Control" },
  { code: "MFGT 210", name: "Computer-Aided Manufacturing" },
];

const EXPANDED_COURSE = {
  description: "Advanced computer-aided manufacturing techniques including CNC programming, toolpath optimization, and production workflow design.",
  outcomes: [
    "Program CNC machines using industry-standard G-code and CAM software",
    "Design and optimize toolpaths for multi-axis machining operations",
    "Develop production workflow plans integrating quality checkpoints",
    "Apply lean manufacturing principles to CNC production environments",
  ],
  skills: ["CAM Software", "CNC Programming", "Toolpath Optimization", "Production Planning"],
};

function Chevron({ open = false }: { open?: boolean }) {
  return (
    <svg width="12" height="12" viewBox="0 0 12 12" fill="none"
      style={{ opacity: open ? 0.5 : 0.2, transform: open ? "rotate(90deg)" : "none", transition: "transform 0.3s ease, opacity 0.3s ease" }}>
      <path d="M4 2l4 4-4 4" stroke="rgba(255,255,255,0.5)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

const NARRATIONS = [
  "",
  "What does this course teach?",
  "What outcomes does it promise?",
  "What skills does it develop?",
];

function stepStyle(step: number, currentStep: number, totalSteps = 3): React.CSSProperties {
  const isVisible = currentStep >= step;
  const isActive = currentStep === step;
  const isResting = currentStep > totalSteps;
  const isPast = currentStep > step && !isResting;
  return {
    opacity: isVisible ? (isPast ? 0.5 : 1) : 0,
    transform: isVisible ? "translateY(0)" : "translateY(8px)",
    transition: "opacity 0.5s ease, transform 0.5s ease, border-color 0.4s ease, background 0.4s ease",
    borderLeft: isActive ? `2px solid ${ACCENT}` : "2px solid transparent",
    paddingLeft: 12,
    background: isActive ? `${ACCENT}08` : "transparent",
    borderRadius: isActive ? "0 4px 4px 0" : 0,
    marginBottom: 10,
  };
}

const EXPAND_COURSE = 2;

export default function DemoCourses() {
  const { phase, typedText, isRowExpanded, highlightedRow, dimOtherRows, showRows, detailStep, containerRef } = useDemoJourney({
    query: "courses that develop industrial manufacturing skills",
    detailSteps: 3,
  });

  const isActive = phase !== "hold";

  return (
    <div ref={containerRef} style={{ fontFamily: FONT }}>
      {/* Search input */}
      <div style={{
        padding: "12px 40px 12px 16px",
        background: "rgba(255,255,255,0.04)",
        border: `1px solid ${phaseAtLeast(phase, "typing") && isActive ? `${ACCENT}50` : "rgba(255,255,255,0.10)"}`,
        borderRadius: 16,
        boxShadow: phaseAtLeast(phase, "typing") && isActive ? `0 0 0 3px ${ACCENT}15` : "none",
        transition: "border-color 0.2s, box-shadow 0.2s, opacity 0.4s",
        position: "relative",
        opacity: isActive ? 1 : 0.3,
      }}>
        {typedText ? (
          <span style={{ fontSize: 13, color: "rgba(255,255,255,0.85)" }}>
            {typedText}
            {phase === "typing" && <span style={{ opacity: 0.6, animation: "blink 1s step-end infinite" }}>|</span>}
          </span>
        ) : (
          <span style={{ fontSize: 13, color: "rgba(255,255,255,0.25)" }}>Ask me a question about courses.</span>
        )}
        <div style={{ position: "absolute", right: 12, top: "50%", transform: "translateY(-50%)" }}>
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
            <circle cx="8" cy="8" r="7" strokeWidth="1.2" stroke="rgba(255,255,255,0.2)" />
            <text x="8" y="11.5" textAnchor="middle" fontSize="9" fontWeight="600" fill="rgba(255,255,255,0.2)">?</text>
          </svg>
        </div>
      </div>

      {/* Results */}
      <div style={{
        maxHeight: showRows ? 800 : 0,
        opacity: showRows && isActive ? 1 : 0,
        overflow: "hidden",
        transition: "max-height 0.5s ease, opacity 0.4s ease",
        marginTop: 12,
      }}>
        {/* Narration */}
        <div style={{
          overflow: "hidden",
          maxHeight: detailStep >= 1 ? 28 : 0,
          opacity: detailStep >= 1 ? 1 : 0,
          transition: "max-height 0.4s ease, opacity 0.4s ease",
          marginBottom: detailStep >= 1 ? 6 : 0,
          paddingLeft: 36,
        }}>
          <span style={{ fontSize: 10, fontWeight: 500, fontStyle: "italic", color: `${ACCENT}80`, letterSpacing: "0.02em" }}>
            {NARRATIONS[detailStep] ?? ""}
          </span>
        </div>

        {/* Column headers */}
        <div style={{ display: "grid", gridTemplateColumns: "24px 1fr auto", padding: "8px 12px", borderBottom: `1px solid ${ACCENT}20` }}>
          <span />
          <span style={{ fontSize: 9, fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.1em", color: `${ACCENT}90` }}>Department</span>
          <span style={{ fontSize: 9, fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.1em", color: `${ACCENT}60`, textAlign: "right" }}>Courses</span>
        </div>

        {/* Department header */}
        <div style={{
          display: "grid", gridTemplateColumns: "24px 1fr auto", alignItems: "center",
          padding: "12px 12px", background: "rgba(255,255,255,0.06)",
        }}>
          <Chevron open />
          <span style={{ fontSize: 13, fontWeight: 500, color: "rgba(255,255,255,0.85)" }}>Manufacturing Technology</span>
          <span style={{ fontSize: 11, color: "rgba(255,255,255,0.4)", textAlign: "right" }}>5 courses</span>
        </div>

        {/* Course rows */}
        {COURSES.map((c, i) => {
          const isTarget = i === EXPAND_COURSE;
          const isDimmed = dimOtherRows && !isTarget;
          return (
            <div key={c.code} style={{ opacity: isDimmed ? 0.35 : 1, transition: "opacity 0.4s ease" }}>
              <div style={{
                display: "flex", alignItems: "center", gap: 8,
                padding: "9px 12px 9px 36px",
                background: highlightedRow && isTarget ? "rgba(255,255,255,0.08)" : "rgba(255,255,255,0.02)",
                boxShadow: highlightedRow && isTarget ? `0 0 12px 2px ${ACCENT}30, inset 0 0 0 1px ${ACCENT}25` : "none",
                borderBottom: "1px solid rgba(255,255,255,0.04)",
                borderRadius: highlightedRow && isTarget ? 4 : 0,
                transition: "background 0.3s ease, box-shadow 0.5s ease, border-radius 0.3s ease",
              }}>
                <Chevron open={isTarget && isRowExpanded} />
                <span style={{ fontSize: 11, fontWeight: 600, color: ACCENT, flexShrink: 0 }}>{c.code}</span>
                <span style={{ fontSize: 12, color: "rgba(255,255,255,0.75)", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{c.name}</span>
              </div>

              {isTarget && (
                <div style={{
                  maxHeight: isRowExpanded ? 600 : 0,
                  opacity: isRowExpanded ? 1 : 0,
                  overflow: "hidden",
                  transition: "max-height 0.3s ease, opacity 0.3s ease",
                }}>
                  <div style={{ padding: "14px 16px 18px 48px", background: "rgba(255,255,255,0.03)" }}>
                    {/* Step 1: Description */}
                    <div style={stepStyle(1, detailStep)}>
                      <span style={{ fontSize: 9, fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.1em", color: `${ACCENT}99`, display: "block", marginBottom: 6 }}>Description</span>
                      <p style={{ fontSize: 12, color: "rgba(255,255,255,0.6)", lineHeight: 1.6, margin: "0 0 14px" }}>{EXPANDED_COURSE.description}</p>
                    </div>

                    {/* Step 2: Learning Outcomes */}
                    <div style={stepStyle(2, detailStep)}>
                      <span style={{ fontSize: 9, fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.1em", color: `${ACCENT}99`, display: "block", marginBottom: 6 }}>Learning Outcomes</span>
                      <ul style={{ margin: "0 0 14px", paddingLeft: 16, display: "flex", flexDirection: "column", gap: 3 }}>
                        {EXPANDED_COURSE.outcomes.map((o) => (
                          <li key={o} style={{ fontSize: 11, color: "rgba(255,255,255,0.6)", lineHeight: 1.5 }}>{o}</li>
                        ))}
                      </ul>
                    </div>

                    {/* Step 3: Derived Skills */}
                    <div style={stepStyle(3, detailStep)}>
                      <span style={{ fontSize: 9, fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.1em", color: `${ACCENT}99`, display: "block", marginBottom: 6 }}>Derived Skills</span>
                      <div style={{ display: "flex", flexWrap: "wrap", gap: 5 }}>
                        {EXPANDED_COURSE.skills.map((sk) => (
                          <span key={sk} style={{ padding: "4px 10px", border: `1px solid ${ACCENT}60`, borderRadius: 6, fontSize: 11, fontWeight: 500, color: ACCENT }}>{sk}</span>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
