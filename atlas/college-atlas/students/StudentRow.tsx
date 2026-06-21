"use client";

import { useState, useRef, useEffect } from "react";
import { AnimatePresence, motion } from "framer-motion";
import DataCitation from "@/ui/DataCitation";

const FONT = "var(--font-inter), Inter, system-ui, sans-serif";
const MONO = "var(--font-mono), ui-monospace, SFMono-Regular, monospace";

const GRADE_COLORS: Record<string, string> = {
  A: "rgba(74, 222, 128, 0.8)",
  B: "rgba(96, 165, 250, 0.8)",
  C: "rgba(251, 191, 36, 0.8)",
  D: "rgba(251, 146, 60, 0.8)",
  F: "rgba(248, 113, 113, 0.8)",
  W: "rgba(156, 163, 175, 0.6)",
};

function gpaColor(gpa: number): string {
  if (gpa >= 3.5) return "rgba(74, 222, 128, 0.9)";
  if (gpa >= 2.5) return "rgba(96, 165, 250, 0.9)";
  if (gpa >= 1.5) return "rgba(251, 191, 36, 0.9)";
  return "rgba(248, 113, 113, 0.9)";
}

export type StudentData = {
  uuid: string;
  displayNumber: number;
  primaryFocus: string;
  coursesCompleted: number;
  gpa: number;
};

export type StudentDetailData = {
  enrollments: Array<{
    courseCode?: string;
    courseName: string;
    department: string;
    grade: string;
    term: string;
    status: string;
  }>;
  // Occupations the student aligns with via the institutional TOP-SOC
  // crosswalk. Matched courses are pre-grouped by the TOP6 each course
  // is institutionally tagged with — making the program-area structure
  // of the alignment visible as a top-level grouping in the accordion
  // rather than as metadata at the end of each course row.
  occupationAlignment: Array<{
    socCode: string;
    title: string;
    matchedCourseCount: number;
    matchedTopGroups: Array<{
      topCode: string;
      topTitle: string;
      courses: Array<{
        code: string;
        name: string;
      }>;
    }>;
  }>;
};

type Props = {
  student: StudentData;
  index: number;
  brandColor: string;
  // Controlled mode
  isOpen?: boolean;
  onToggle?: () => void;
  // Detail data
  detail?: StudentDetailData | null;
  isLoading?: boolean;
  onExpand?: () => void;
  // Context-mode flag — when this row is rendered inside a partnership
  // opportunity report, suppress the "Competency Profile" tab and show
  // only the course history. The report is already scoped to a single
  // SOC, so the cross-occupation competency view would be off-topic.
  hideCompetencyProfile?: boolean;
};

export default function StudentRow({ student, index, brandColor, isOpen: controlledOpen, onToggle, detail, isLoading, onExpand, hideCompetencyProfile }: Props) {
  const [internalOpen, setInternalOpen] = useState(false);
  const [tab, setTab] = useState<"history" | "competency">("history");
  const [expandedOccs, setExpandedOccs] = useState<Set<string>>(new Set());
  const isOpen = controlledOpen ?? internalOpen;

  const toggleOcc = (socCode: string) => {
    setExpandedOccs((prev) => {
      const next = new Set(prev);
      if (next.has(socCode)) next.delete(socCode); else next.add(socCode);
      return next;
    });
  };

  const hasMounted = useRef(false);
  useEffect(() => { hasMounted.current = true; }, []);

  const handleClick = () => {
    if (onToggle) {
      onToggle();
    } else {
      setInternalOpen(!internalOpen);
    }
    onExpand?.();
  };

  return (
    <div style={{ overflowX: "auto" }}>
      <motion.button
        initial={hasMounted.current ? false : { opacity: 0, y: 6 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.2, delay: hasMounted.current ? 0 : Math.min(index * 0.01, 0.2) }}
        onClick={handleClick}
        style={{
          width: "100%", textAlign: "left",
          display: "grid", gridTemplateColumns: "24px 110px 1fr 90px 60px", minWidth: "500px",
          padding: "12px 16px", gap: "10px", alignItems: "center",
          background: isOpen ? "rgba(255,255,255,0.06)" : "rgba(255,255,255,0.03)",
          border: "none", borderBottom: "1px solid rgba(255,255,255,0.05)",
          cursor: "pointer", transition: "background 0.15s",
        }}
        onMouseEnter={(e) => { if (!isOpen) (e.currentTarget as HTMLElement).style.background = "rgba(255,255,255,0.05)"; }}
        onMouseLeave={(e) => { if (!isOpen) (e.currentTarget as HTMLElement).style.background = "rgba(255,255,255,0.03)"; }}
      >
        <svg width="12" height="12" viewBox="0 0 12 12" fill="none"
          style={{ transform: isOpen ? "rotate(90deg)" : "rotate(0deg)", transition: "transform 0.2s" }}>
          <path d="M4 2l4 4-4 4" stroke="rgba(255,255,255,0.3)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
        <span style={{ fontFamily: FONT, fontSize: "13px", fontWeight: 600, color: "rgba(255,255,255,0.8)" }}>
          Student #{student.displayNumber}
        </span>
        <span style={{ fontFamily: FONT, fontSize: "13px", color: "rgba(255,255,255,0.55)", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
          {student.primaryFocus}
        </span>
        <span style={{ fontFamily: FONT, fontSize: "12px", fontWeight: 500, color: "rgba(255,255,255,0.6)" }}>
          {student.coursesCompleted} courses
        </span>
        <span style={{ fontFamily: FONT, fontSize: "13px", fontWeight: 700, color: gpaColor(student.gpa) }}>
          {student.gpa.toFixed(2)}
        </span>
      </motion.button>

      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.25 }}
            style={{ overflow: "hidden", background: "rgba(255,255,255,0.02)" }}
          >
            <div style={{ padding: "16px 20px 24px", overflowX: "auto" }}>
              {isLoading && <p style={{ fontFamily: FONT, fontSize: "13px", color: "rgba(255,255,255,0.3)" }}>Loading...</p>}
              {detail && (
                <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
                  <div style={{ display: "flex", gap: "0", borderBottom: "1px solid rgba(255,255,255,0.08)" }}>
                    {(hideCompetencyProfile ? (["history"] as const) : (["history", "competency"] as const)).map((t) => (
                      <button key={t} onClick={(e) => { e.stopPropagation(); setTab(t); }}
                        style={{
                          background: "none", border: "none",
                          borderBottom: tab === t ? `2px solid ${brandColor}` : "2px solid transparent",
                          cursor: hideCompetencyProfile ? "default" : "pointer",
                          padding: "8px 16px", fontFamily: FONT, fontSize: "11px",
                          fontWeight: 600, letterSpacing: "0.1em", textTransform: "uppercase",
                          color: tab === t ? brandColor : "rgba(255,255,255,0.35)",
                          transition: "color 0.15s", marginBottom: "-1px",
                        }}>
                        {t === "history" ? "Course History" : "Competency Profile"}
                      </button>
                    ))}
                  </div>
                  {(hideCompetencyProfile || tab === "history") && (
                    <div style={{ display: "flex", flexDirection: "column", gap: "1px" }}>
                      {detail.enrollments.map((e, ei) => (
                        <div key={ei} style={{
                          display: "flex", alignItems: "baseline",
                          padding: "6px 12px",
                          background: "rgba(255,255,255,0.02)", borderRadius: "4px",
                          gap: "8px",
                        }}>
                          {e.courseCode && <span style={{ fontFamily: FONT, fontSize: "11px", fontWeight: 600, color: brandColor, flexShrink: 0 }}>{e.courseCode}</span>}
                          <span style={{ fontFamily: FONT, fontSize: "12px", fontWeight: 500, color: "rgba(255,255,255,0.7)", flex: 1 }}>{e.courseName}</span>
                          <span style={{ fontFamily: FONT, fontSize: "12px", fontWeight: 700, color: GRADE_COLORS[e.grade] ?? "rgba(255,255,255,0.5)", flexShrink: 0 }}>{e.grade}</span>
                          <span style={{ fontFamily: FONT, fontSize: "11px", color: "rgba(255,255,255,0.35)", flexShrink: 0, width: "80px", textAlign: "right" }}>{e.term}</span>
                        </div>
                      ))}
                    </div>
                  )}
                  {!hideCompetencyProfile && tab === "competency" && (
                    <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
                      <p style={{ fontFamily: FONT, fontSize: "11px", color: "rgba(255,255,255,0.4)", margin: 0, lineHeight: 1.5 }}>
                        Deepest occupational pathways in this student&rsquo;s transcript, traced through TOP-SOC crosswalk.
                      </p>
                      {detail.occupationAlignment.length === 0 ? (
                        <p style={{ fontFamily: FONT, fontSize: "13px", color: "rgba(255,255,255,0.3)" }}>
                          No competency profile yet — this student hasn&rsquo;t completed 4 or more courses concentrated on any single occupational pathway.
                        </p>
                      ) : detail.occupationAlignment.map((occ) => {
                        const occOpen = expandedOccs.has(occ.socCode);
                        return (
                          <div key={occ.socCode} style={{
                            background: "rgba(255,255,255,0.02)", borderRadius: "4px", overflow: "hidden",
                          }}>
                            <button
                              onClick={(e) => { e.stopPropagation(); toggleOcc(occ.socCode); }}
                              style={{
                                width: "100%", textAlign: "left",
                                display: "flex", alignItems: "baseline", gap: "12px",
                                padding: "8px 12px",
                                background: "transparent", border: "none",
                                cursor: "pointer", transition: "background 0.15s",
                              }}
                              onMouseEnter={(e) => { (e.currentTarget as HTMLElement).style.background = "rgba(255,255,255,0.025)"; }}
                              onMouseLeave={(e) => { (e.currentTarget as HTMLElement).style.background = "transparent"; }}
                            >
                              <svg width="10" height="10" viewBox="0 0 12 12" fill="none"
                                style={{ transform: occOpen ? "rotate(90deg)" : "rotate(0deg)", transition: "transform 0.2s", flexShrink: 0, alignSelf: "center" }}>
                                <path d="M4 2l4 4-4 4" stroke="rgba(255,255,255,0.4)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
                              </svg>
                              <span style={{ fontFamily: MONO, fontSize: "11px", color: brandColor, opacity: 0.7, flexShrink: 0, whiteSpace: "nowrap" }}>
                                SOC {occ.socCode}
                              </span>
                              <span style={{ fontFamily: FONT, fontSize: "12px", color: "rgba(255,255,255,0.75)", flex: 1 }}>
                                {occ.title}
                              </span>
                              <span style={{ fontFamily: FONT, fontSize: "11px", color: brandColor, opacity: 0.7, flexShrink: 0, whiteSpace: "nowrap", textAlign: "right" }}>
                                {occ.matchedCourseCount} course{occ.matchedCourseCount === 1 ? "" : "s"}
                              </span>
                            </button>
                            <AnimatePresence>
                              {occOpen && (
                                <motion.div
                                  initial={{ height: 0, opacity: 0 }}
                                  animate={{ height: "auto", opacity: 1 }}
                                  exit={{ height: 0, opacity: 0 }}
                                  transition={{ duration: 0.2 }}
                                  style={{ overflow: "hidden" }}
                                >
                                  <div style={{
                                    padding: "4px 12px 12px 28px",
                                    display: "flex", flexDirection: "column", gap: "10px",
                                  }}>
                                    {occ.matchedTopGroups.map((group) => {
                                      const topDisplay = group.topCode && /^\d{6}$/.test(group.topCode)
                                        ? `${group.topCode.slice(0, 4)}.${group.topCode.slice(4, 6)}`
                                        : group.topCode;
                                      return (
                                        <div key={group.topCode || "unknown"}>
                                          <div style={{
                                            display: "flex", alignItems: "baseline", gap: "8px",
                                            padding: "4px 0 6px",
                                          }}>
                                            <span style={{
                                              display: "inline-block",
                                              width: "4px", height: "4px", borderRadius: "50%",
                                              background: "rgba(255,255,255,0.3)", flexShrink: 0,
                                              alignSelf: "center",
                                            }} />
                                            <span style={{
                                              fontFamily: MONO, fontSize: "11px", fontWeight: 500,
                                              color: "rgba(255,255,255,0.5)", flexShrink: 0, whiteSpace: "nowrap",
                                              letterSpacing: "0.02em",
                                            }}>
                                              TOP {topDisplay || "—"}
                                            </span>
                                            {group.topTitle && (
                                              <>
                                                <span style={{
                                                  fontFamily: FONT, fontSize: "11px",
                                                  color: "rgba(255,255,255,0.3)", flexShrink: 0,
                                                }}>·</span>
                                                <span style={{
                                                  fontFamily: FONT, fontSize: "11px",
                                                  color: "rgba(255,255,255,0.7)",
                                                }}>
                                                  {group.topTitle}
                                                </span>
                                              </>
                                            )}
                                          </div>
                                          <div style={{
                                            display: "flex", flexDirection: "column", gap: "2px",
                                            paddingLeft: "13px",
                                            borderLeft: `1px solid rgba(255,255,255,0.08)`,
                                            marginLeft: "2px",
                                          }}>
                                            {group.courses.map((c) => (
                                              <div key={c.code} style={{
                                                display: "flex", alignItems: "baseline", gap: "10px",
                                                padding: "3px 8px",
                                                fontSize: "11px", lineHeight: 1.4,
                                              }}>
                                                <span style={{ fontFamily: FONT, fontWeight: 600, color: brandColor, flexShrink: 0, whiteSpace: "nowrap" }}>
                                                  {c.code}
                                                </span>
                                                <span style={{ fontFamily: FONT, color: "rgba(255,255,255,0.7)", flex: 1 }}>
                                                  {c.name}
                                                </span>
                                              </div>
                                            ))}
                                          </div>
                                        </div>
                                      );
                                    })}
                                  </div>
                                </motion.div>
                              )}
                            </AnimatePresence>
                          </div>
                        );
                      })}
                    </div>
                  )}
                  <DataCitation source="California Community Colleges Chancellor's Office MIS Data Mart" />
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
