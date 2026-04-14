"use client";

import { useDemoJourney, phaseAtLeast } from "../hooks/useDemoJourney";

const FONT = "var(--font-geist), system-ui, sans-serif";
const ACCENT = "#c9a84c";

const OCCUPATIONS = [
  { title: "Industrial Engineers", wage: 108200, openings: 340, growth: 6.4 },
  { title: "Machinists", wage: 58400, openings: 890, growth: 4.8 },
  { title: "CNC Tool Operators", wage: 52100, openings: 1240, growth: 5.2 },
];

const EXPANDED = {
  soc: "51-4041",
  description: "Set up and operate machine tools to produce precision metal parts, instruments, and tools.",
  skills: [
    { skill: "CNC Operation", course: "MFGT 210" },
    { skill: "Blueprint Reading", course: "MFGT 145" },
    { skill: "Quality Control", course: "MFGT 145" },
    { skill: "Precision Measurement", course: "MFGT 110" },
  ],
  region: "Bay Area / Peninsula",
  employed: 2340,
};

function Chevron({ open = false }: { open?: boolean }) {
  return (
    <svg width="12" height="12" viewBox="0 0 12 12" fill="none"
      style={{ opacity: open ? 0.5 : 0.2, transform: open ? "rotate(90deg)" : "none", transition: "transform 0.3s ease, opacity 0.3s ease" }}>
      <path d="M4 2l4 4-4 4" stroke="rgba(255,255,255,0.5)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

function Checkmark() {
  return (
    <svg width="12" height="12" viewBox="0 0 12 12" fill="none" style={{ flexShrink: 0 }}>
      <circle cx="6" cy="6" r="5" stroke={ACCENT} strokeWidth="1" />
      <path d="M4 6l1.5 1.5L8 5" stroke={ACCENT} strokeWidth="1" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

const NARRATIONS = [
  "",
  "What is this occupation?",
  "What skills does it require that our curriculum develops?",
  "What does regional demand look like?",
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

const EXPAND_ROW = 1;
const GRID = "24px 1fr 80px 60px 70px";

export default function DemoOccupations() {
  const { phase, typedText, isRowExpanded, highlightedRow, showRows, detailStep, containerRef } = useDemoJourney({
    query: "highest paying manufacturing occupations in our region",
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
          <span style={{ fontSize: 13, color: "rgba(255,255,255,0.25)" }}>Ask me a question about occupations.</span>
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
        }}>
          <span style={{ fontSize: 10, fontWeight: 500, fontStyle: "italic", color: `${ACCENT}80`, letterSpacing: "0.02em" }}>
            {NARRATIONS[detailStep] ?? ""}
          </span>
        </div>

        {/* Column headers */}
        <div style={{ display: "grid", gridTemplateColumns: GRID, padding: "8px 12px", borderBottom: `1px solid ${ACCENT}20` }}>
          <span />
          <span style={{ fontSize: 9, fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.1em", color: `${ACCENT}90` }}>Occupation</span>
          <span style={{ fontSize: 9, fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.1em", color: `${ACCENT}60`, textAlign: "right" }}>Wage</span>
          <span style={{ fontSize: 9, fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.1em", color: `${ACCENT}60`, textAlign: "right" }}>Openings</span>
          <span style={{ fontSize: 9, fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.1em", color: `${ACCENT}60`, textAlign: "right" }}>Growth</span>
        </div>

        {OCCUPATIONS.map((o, i) => {
          const isTarget = i === EXPAND_ROW;
          const isDimmed = highlightedRow && !isTarget;
          return (
            <div key={o.title} style={{ opacity: isDimmed ? 0.35 : 1, transition: "opacity 0.4s ease" }}>
              <div style={{
                display: "grid", gridTemplateColumns: GRID, alignItems: "center",
                padding: "10px 12px",
                background: highlightedRow && isTarget ? "rgba(255,255,255,0.08)" : "rgba(255,255,255,0.03)",
                boxShadow: highlightedRow && isTarget ? `0 0 12px 2px ${ACCENT}30, inset 0 0 0 1px ${ACCENT}25` : "none",
                borderBottom: "1px solid rgba(255,255,255,0.05)",
                borderRadius: highlightedRow && isTarget ? 4 : 0,
                transition: "background 0.3s ease, box-shadow 0.5s ease, border-radius 0.3s ease",
              }}>
                <Chevron open={isTarget && isRowExpanded} />
                <span style={{ fontSize: 12, fontWeight: 500, color: "rgba(255,255,255,0.85)" }}>{o.title}</span>
                <span style={{ fontSize: 11, color: "rgba(255,255,255,0.5)", textAlign: "right" }}>${o.wage.toLocaleString()}</span>
                <span style={{ fontSize: 11, color: "rgba(255,255,255,0.45)", textAlign: "right" }}>{o.openings.toLocaleString()}/yr</span>
                <span style={{ fontSize: 11, fontWeight: 500, color: "#4ade80", textAlign: "right" }}>+{o.growth}%</span>
              </div>

              {isTarget && (
                <div style={{
                  maxHeight: isRowExpanded ? 600 : 0,
                  opacity: isRowExpanded ? 1 : 0,
                  overflow: "hidden",
                  transition: "max-height 0.3s ease, opacity 0.3s ease",
                }}>
                  <div style={{ padding: "14px 16px 18px", background: "rgba(255,255,255,0.02)" }}>
                    {/* Step 1: SOC + Description */}
                    <div style={stepStyle(1, detailStep)}>
                      <span style={{ fontSize: 10, fontWeight: 600, color: "rgba(255,255,255,0.4)", letterSpacing: "0.05em" }}>SOC {EXPANDED.soc}</span>
                      <p style={{ fontSize: 12, color: "rgba(255,255,255,0.55)", lineHeight: 1.6, margin: "8px 0 14px" }}>{EXPANDED.description}</p>
                    </div>

                    {/* Step 2: Aligned Skills */}
                    <div style={stepStyle(2, detailStep)}>
                      <span style={{ fontSize: 9, fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.1em", color: `${ACCENT}99`, display: "block", marginBottom: 8 }}>Aligned Skills ({EXPANDED.skills.length})</span>
                      <div style={{ display: "flex", flexDirection: "column", gap: 5 }}>
                        {EXPANDED.skills.map((s) => (
                          <div key={s.skill} style={{ display: "flex", alignItems: "center", gap: 7 }}>
                            <Checkmark />
                            <span style={{ fontSize: 12, color: ACCENT }}>{s.skill}</span>
                            <span style={{ fontSize: 10, color: "rgba(255,255,255,0.3)", marginLeft: "auto" }}>{s.course}</span>
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Step 3: Regional */}
                    <div style={stepStyle(3, detailStep)}>
                      <span style={{ fontSize: 9, fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.1em", color: "rgba(255,255,255,0.3)", display: "block", marginBottom: 4 }}>Regional Employment</span>
                      <span style={{ fontSize: 11, color: "rgba(255,255,255,0.45)" }}>{EXPANDED.region}: <span style={{ color: "rgba(255,255,255,0.65)", fontWeight: 500 }}>{EXPANDED.employed.toLocaleString()}</span> currently employed</span>
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
