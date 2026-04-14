"use client";

import { useDemoJourney, phaseAtLeast } from "../hooks/useDemoJourney";

const FONT = "var(--font-geist), system-ui, sans-serif";
const ACCENT = "#c9a84c";

const EMPLOYERS = [
  { name: "Pacific Precision Mfg.", sector: "Aerospace", roles: 12, skills: 18 },
  { name: "Central Valley Fabrication", sector: "Metalwork", roles: 8, skills: 14 },
  { name: "Sierra Machining Group", sector: "Contract Mfg.", roles: 6, skills: 11 },
];

const EXPANDED = {
  description: "Aerospace components manufacturer specializing in precision-machined parts for commercial and defense aviation.",
  occupation: {
    title: "Machinists",
    wage: 58400,
    description: "Precision metal parts production for aerospace applications.",
    skills: [
      { skill: "CNC Operation", course: "MFGT 210" },
      { skill: "Blueprint Reading", course: "MFGT 145" },
      { skill: "Quality Control", course: "MFGT 145" },
    ],
  },
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
  "Who is this employer?",
  "Are they verifiable?",
  "What do they hire for?",
  "How does their workforce need align with our curriculum?",
];

function stepStyle(step: number, currentStep: number, totalSteps = 4): React.CSSProperties {
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

// Occupation card holds both step 3 (card reveal) and step 4 (aligned skills).
// Stay active during both steps, fade to past at rest.
function occupationCardStepStyle(currentStep: number, totalSteps = 4): React.CSSProperties {
  const isVisible = currentStep >= 3;
  const isActive = currentStep === 3;  // Only highlight outer card for step 3; step 4's own stepStyle takes over
  const isResting = currentStep > totalSteps;
  const isPast = currentStep > 4 && !isResting;
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

const EXPAND_ROW = 0;
const GRID = "24px 1.2fr 1fr 50px 85px";

export default function DemoEmployers() {
  const { phase, typedText, isRowExpanded, highlightedRow, dimOtherRows, showRows, detailStep, containerRef } = useDemoJourney({
    query: "employers aligned with our manufacturing program",
    detailSteps: 4,
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
          <span style={{ fontSize: 13, color: "rgba(255,255,255,0.25)" }}>Ask me a question about employers.</span>
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
        maxHeight: showRows ? 900 : 0,
        opacity: showRows && isActive ? 1 : 0,
        overflow: "hidden",
        transition: "max-height 0.5s ease, opacity 0.4s ease",
        marginTop: 12,
      }}>
        {/* Narration */}
        <div style={{
          overflow: "hidden",
          maxHeight: detailStep >= 1 ? 32 : 0,
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
          <span style={{ fontSize: 9, fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.1em", color: `${ACCENT}90` }}>Employer</span>
          <span style={{ fontSize: 9, fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.1em", color: `${ACCENT}60` }}>Sector</span>
          <span style={{ fontSize: 9, fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.1em", color: `${ACCENT}60`, textAlign: "center" }}>Roles</span>
          <span style={{ fontSize: 9, fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.1em", color: `${ACCENT}60`, textAlign: "right" }}>Skills</span>
        </div>

        {EMPLOYERS.map((e, i) => {
          const isTarget = i === EXPAND_ROW;
          const isDimmed = dimOtherRows && !isTarget;
          return (
            <div key={e.name} style={{ opacity: isDimmed ? 0.35 : 1, transition: "opacity 0.4s ease" }}>
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
                <span style={{ fontSize: 12, fontWeight: 500, color: "rgba(255,255,255,0.85)", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{e.name}</span>
                <span style={{ fontSize: 11, color: "rgba(255,255,255,0.4)", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{e.sector}</span>
                <span style={{ fontSize: 11, color: "rgba(255,255,255,0.4)", textAlign: "center" }}>{e.roles}</span>
                <span style={{ fontSize: 10, color: ACCENT, background: `${ACCENT}20`, border: `1px solid ${ACCENT}30`, borderRadius: 100, padding: "3px 8px", textAlign: "center", whiteSpace: "nowrap", textTransform: "uppercase", letterSpacing: "0.05em" }}>{e.skills} Skills</span>
              </div>

              {isTarget && (
                <div style={{
                  maxHeight: isRowExpanded ? 700 : 0,
                  opacity: isRowExpanded ? 1 : 0,
                  overflow: "hidden",
                  transition: "max-height 0.3s ease, opacity 0.3s ease",
                }}>
                  <div style={{ padding: "14px 16px 18px", background: "rgba(255,255,255,0.02)" }}>
                    {/* Step 1: Description */}
                    <div style={stepStyle(1, detailStep)}>
                      <p style={{ fontSize: 12, color: "rgba(255,255,255,0.7)", lineHeight: 1.55, margin: "0 0 12px" }}>{EXPANDED.description}</p>
                    </div>

                    {/* Step 2: Website link */}
                    <div style={stepStyle(2, detailStep)}>
                      <span style={{
                        display: "inline-flex", alignItems: "center", gap: 5,
                        padding: "3px 10px", borderRadius: 100,
                        fontSize: 10, fontWeight: 600, letterSpacing: "0.07em", textTransform: "uppercase",
                        color: "rgba(255,255,255,0.4)", border: "1px solid rgba(255,255,255,0.12)",
                      }}>
                        <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="rgba(255,255,255,0.4)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                          <circle cx="12" cy="12" r="10" /><path d="M2 12h20" /><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z" />
                        </svg>
                        Employer Home Page
                      </span>
                    </div>

                    {/* Step 3: Occupation card (keeps full opacity during step 4) */}
                    <div style={occupationCardStepStyle(detailStep)}>
                      <span style={{ fontSize: 10, fontWeight: 600, letterSpacing: "0.07em", textTransform: "uppercase", color: "rgba(255,255,255,0.4)", display: "block", marginBottom: 8 }}>Employer Occupations (1)</span>
                      <div style={{ background: "rgba(255,255,255,0.03)", borderRadius: 8, padding: "14px 16px" }}>
                        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline" }}>
                          <span style={{ fontSize: 13, fontWeight: 500, color: "#f0eef4" }}>{EXPANDED.occupation.title}</span>
                          <span style={{ fontSize: 11, fontWeight: 500, color: "rgba(255,255,255,0.55)", whiteSpace: "nowrap" }}>${EXPANDED.occupation.wage.toLocaleString()} annual</span>
                        </div>
                        <p style={{ fontSize: 11, color: "rgba(255,255,255,0.45)", lineHeight: 1.5, margin: "6px 0 10px" }}>{EXPANDED.occupation.description}</p>

                        {/* Step 4: Aligned skills within occupation card */}
                        <div style={stepStyle(4, detailStep)}>
                          <span style={{ fontSize: 9, fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.1em", color: `${ACCENT}99`, display: "block", marginBottom: 6 }}>Aligned Skills ({EXPANDED.occupation.skills.length})</span>
                          <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
                            {EXPANDED.occupation.skills.map((s) => (
                              <div key={s.skill} style={{ display: "flex", alignItems: "center", gap: 7 }}>
                                <Checkmark />
                                <span style={{ fontSize: 12, color: ACCENT }}>{s.skill}</span>
                                <span style={{ fontSize: 10, color: "rgba(255,255,255,0.3)", marginLeft: "auto" }}>{s.course}</span>
                              </div>
                            ))}
                          </div>
                        </div>
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
