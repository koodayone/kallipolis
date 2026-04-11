"use client";

import { useState, useRef, useEffect } from "react";
import { AnimatePresence, motion } from "framer-motion";
import DataCitation from "@/ui/DataCitation";

const FONT = "var(--font-inter), Inter, system-ui, sans-serif";

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
  matchingSkills?: number;
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
  skills: string[];
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
  // Show skills match instead of courses (proposal context)
  totalCoreSkills?: number;
};

export default function StudentRow({ student, index, brandColor, isOpen: controlledOpen, onToggle, detail, isLoading, onExpand, totalCoreSkills }: Props) {
  const [internalOpen, setInternalOpen] = useState(false);
  const [tab, setTab] = useState<"history" | "skills">("history");
  const isOpen = controlledOpen ?? internalOpen;

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
        {totalCoreSkills != null ? (
          <span style={{ display: "flex" }}>
            <span style={{
              fontFamily: FONT, fontSize: "10px", fontWeight: 600,
              padding: "3px 8px", borderRadius: "100px",
              background: `${brandColor}15`, color: brandColor, border: `1px solid ${brandColor}40`,
              whiteSpace: "nowrap",
            }}>
              {student.matchingSkills ?? 0}/{totalCoreSkills} SKILLS
            </span>
          </span>
        ) : (
          <span style={{ fontFamily: FONT, fontSize: "12px", fontWeight: 500, color: "rgba(255,255,255,0.6)" }}>
            {student.coursesCompleted} courses
          </span>
        )}
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
                    {(["history", "skills"] as const).map((t) => (
                      <button key={t} onClick={(e) => { e.stopPropagation(); setTab(t); }}
                        style={{
                          background: "none", border: "none",
                          borderBottom: tab === t ? `2px solid ${brandColor}` : "2px solid transparent",
                          cursor: "pointer", padding: "8px 16px", fontFamily: FONT, fontSize: "11px",
                          fontWeight: 600, letterSpacing: "0.1em", textTransform: "uppercase",
                          color: tab === t ? brandColor : "rgba(255,255,255,0.35)",
                          transition: "color 0.15s", marginBottom: "-1px",
                        }}>
                        {t === "history" ? "Course History" : "Skill Profile"}
                      </button>
                    ))}
                  </div>
                  {tab === "history" && (
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
                  {tab === "skills" && (
                    <div style={{ display: "flex", flexWrap: "wrap", gap: "6px" }}>
                      {detail.skills.length === 0 ? (
                        <p style={{ fontFamily: FONT, fontSize: "13px", color: "rgba(255,255,255,0.3)" }}>No skills derived yet.</p>
                      ) : detail.skills.map((skill) => (
                        <span key={skill} style={{
                          padding: "5px 12px", background: "rgba(255,255,255,0.03)",
                          border: `1px solid ${brandColor}60`, borderRadius: "6px",
                          fontFamily: FONT, fontSize: "12px", fontWeight: 500, color: brandColor,
                        }}>{skill}</span>
                      ))}
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
