"use client";

import { useDemoJourney, phaseAtLeast } from "../hooks/useDemoJourney";

const FONT = "var(--font-geist), system-ui, sans-serif";
const ACCENT = "#c9a84c";

const STUDENTS = [
  { id: "#412", focus: "Industrial Technology", courses: 11, gpa: 3.91 },
  { id: "#738", focus: "CNC Machining", courses: 9, gpa: 3.87 },
  { id: "#1055", focus: "Welding Technology", courses: 10, gpa: 3.82 },
];

const ENROLLMENTS = [
  { code: "MFGT 110", name: "Intro to Mfg Processes", grade: "A", term: "Fall 2024" },
  { code: "MFGT 145", name: "Industrial Safety", grade: "A", term: "Fall 2024" },
  { code: "MFGT 210", name: "Computer-Aided Mfg", grade: "B", term: "Spr 2025" },
  { code: "WELD 101", name: "Welding Fundamentals", grade: "A", term: "Spr 2025" },
];

const SKILLS = ["CNC Operation", "Blueprint Reading", "Quality Control", "Industrial Safety", "CAM Software"];

const GRADE_COLORS: Record<string, string> = {
  A: "rgba(74, 222, 128, 0.8)", B: "rgba(96, 165, 250, 0.8)", C: "rgba(251, 191, 36, 0.8)",
};

function gpaColor(gpa: number): string {
  if (gpa >= 3.5) return "rgba(74, 222, 128, 0.9)";
  if (gpa >= 2.5) return "rgba(96, 165, 250, 0.9)";
  return "rgba(251, 191, 36, 0.9)";
}

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
  "What courses has this student taken?",
  "How did they perform?",
  "What competencies have they developed?",
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

// Enrollment table is the shared focus for steps 1 (courses) and 2 (grades).
// Stay "active" for both steps, fade to past state at step 3+.
function enrollmentStepStyle(currentStep: number, totalSteps = 3): React.CSSProperties {
  const isVisible = currentStep >= 1;
  const isActive = currentStep === 1 || currentStep === 2;
  const isResting = currentStep > totalSteps;
  const isPast = currentStep > 2 && !isResting;
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
const GRID = "24px 60px 1fr 55px 44px";

export default function DemoStudents() {
  const { phase, typedText, isRowExpanded, highlightedRow, dimOtherRows, showRows, detailStep, containerRef } = useDemoJourney({
    query: "students in advanced manufacturing with highest GPA",
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
          <span style={{ fontSize: 13, color: "rgba(255,255,255,0.25)" }}>Ask me a question about students.</span>
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
          <span style={{ fontSize: 9, fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.1em", color: `${ACCENT}90` }}>Student</span>
          <span style={{ fontSize: 9, fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.1em", color: `${ACCENT}60` }}>Primary Focus</span>
          <span style={{ fontSize: 9, fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.1em", color: `${ACCENT}60`, textAlign: "right" }}>Courses</span>
          <span style={{ fontSize: 9, fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.1em", color: `${ACCENT}60`, textAlign: "right" }}>GPA</span>
        </div>

        {STUDENTS.map((s, i) => {
          const isTarget = i === EXPAND_ROW;
          const isDimmed = dimOtherRows && !isTarget;
          return (
            <div key={s.id} style={{ opacity: isDimmed ? 0.35 : 1, transition: "opacity 0.4s ease" }}>
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
                <span style={{ fontSize: 12, fontWeight: 600, color: "rgba(255,255,255,0.8)" }}>{s.id}</span>
                <span style={{ fontSize: 12, color: "rgba(255,255,255,0.55)", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{s.focus}</span>
                <span style={{ fontSize: 11, fontWeight: 500, color: "rgba(255,255,255,0.6)", textAlign: "right" }}>{s.courses}</span>
                <span style={{ fontSize: 12, fontWeight: 700, color: gpaColor(s.gpa), textAlign: "right" }}>{s.gpa.toFixed(2)}</span>
              </div>

              {isTarget && (
                <div style={{
                  maxHeight: isRowExpanded ? 600 : 0,
                  opacity: isRowExpanded ? 1 : 0,
                  overflow: "hidden",
                  transition: "max-height 0.3s ease, opacity 0.3s ease",
                }}>
                  <div style={{ padding: "14px 16px 18px", background: "rgba(255,255,255,0.02)" }}>
                    {/* Tabs */}
                    <div style={{ display: "flex", gap: 0, borderBottom: "1px solid rgba(255,255,255,0.08)", marginBottom: 12 }}>
                      <span style={{ padding: "6px 14px", fontSize: 10, fontWeight: 600, letterSpacing: "0.1em", textTransform: "uppercase", color: ACCENT, borderBottom: `2px solid ${ACCENT}`, marginBottom: -1 }}>Course History</span>
                      <span style={{ padding: "6px 14px", fontSize: 10, fontWeight: 600, letterSpacing: "0.1em", textTransform: "uppercase", color: "rgba(255,255,255,0.3)", borderBottom: "2px solid transparent", marginBottom: -1 }}>Skill Profile</span>
                    </div>

                    {/* Steps 1-2: Enrollment rows (active during both steps) */}
                    <div style={enrollmentStepStyle(detailStep)}>
                      <div style={{ display: "flex", flexDirection: "column", gap: 1 }}>
                        {ENROLLMENTS.map((e) => (
                          <div key={e.code} style={{ display: "flex", alignItems: "baseline", gap: 8, padding: "5px 0" }}>
                            <span style={{ fontSize: 10, fontWeight: 600, color: ACCENT, flexShrink: 0, width: 65 }}>{e.code}</span>
                            <span style={{ fontSize: 11, fontWeight: 500, color: "rgba(255,255,255,0.7)", flex: 1, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{e.name}</span>
                            {/* Step 2: Grades appear */}
                            <span style={{
                              fontSize: 11, fontWeight: 700,
                              color: GRADE_COLORS[e.grade] ?? "rgba(255,255,255,0.5)",
                              flexShrink: 0,
                              opacity: detailStep >= 2 ? 1 : 0,
                              transition: "opacity 0.5s ease",
                            }}>{e.grade}</span>
                            <span style={{
                              fontSize: 10, color: "rgba(255,255,255,0.3)", width: 60, textAlign: "right", flexShrink: 0,
                              opacity: detailStep >= 2 ? 1 : 0,
                              transition: "opacity 0.5s ease",
                            }}>{e.term}</span>
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Step 3: Skills */}
                    <div style={{ ...stepStyle(3, detailStep), marginTop: 10 }}>
                      <span style={{ fontSize: 9, fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.1em", color: `${ACCENT}99`, display: "block", marginBottom: 6 }}>Skills</span>
                      <div style={{ display: "flex", flexWrap: "wrap", gap: 5 }}>
                        {SKILLS.map((sk) => (
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
