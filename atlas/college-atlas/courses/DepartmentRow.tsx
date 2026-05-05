"use client";

import { useState, useRef, useEffect } from "react";
import { AnimatePresence, motion } from "framer-motion";
import DataCitation from "@/ui/DataCitation";
import CourseOccupationsCallout from "@/college-atlas/courses/CourseOccupationsCallout";

const FONT = "var(--font-inter), Inter, system-ui, sans-serif";

export type CourseItem = {
  code: string;
  name: string;
  description?: string;
  learningOutcomes?: string[];
  courseObjectives?: string[];
  topCode?: string | null;
};

type Props = {
  department: string;
  courseCount: number;
  index: number;
  brandColor: string;
  // Controlled mode
  isOpen?: boolean;
  onToggle?: () => void;
  // Course data
  courses?: CourseItem[] | null;
  isLoading?: boolean;
  onExpand?: () => void;
  schoolName?: string;
  // Context-mode flag — when this row is rendered inside a partnership
  // opportunity report scoped to a specific SOC, suppress the per-course
  // "Occupational Pathways" callout (the report's anchoring occupation
  // is implicit at this level and the callout would surface redundant
  // SOC information).
  hideOccupationPathways?: boolean;
};

export default function DepartmentRow({ department, courseCount, index, brandColor, isOpen: controlledOpen, onToggle, courses, isLoading, onExpand, schoolName, hideOccupationPathways }: Props) {
  const [internalOpen, setInternalOpen] = useState(false);
  const [expandedCourses, setExpandedCourses] = useState<Set<string>>(new Set());
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

  const toggleCourse = (code: string) => {
    setExpandedCourses(prev => {
      const next = new Set(prev);
      if (next.has(code)) next.delete(code); else next.add(code);
      return next;
    });
  };

  return (
    <div>
      <motion.button
        initial={hasMounted.current ? false : { opacity: 0, y: 6 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.2, delay: hasMounted.current ? 0 : Math.min(index * 0.01, 0.2) }}
        onClick={handleClick}
        style={{
          width: "100%", textAlign: "left",
          display: "grid", gridTemplateColumns: "24px 1fr auto",
          padding: "18px 16px", gap: "12px", alignItems: "center",
          background: isOpen ? "rgba(255,255,255,0.08)" : "rgba(255,255,255,0.035)",
          border: "none", borderBottom: `1px solid ${isOpen ? "rgba(255,255,255,0.08)" : "rgba(255,255,255,0.05)"}`,
          borderTop: isOpen ? `2px solid ${brandColor}80` : "2px solid transparent",
          cursor: "pointer", transition: "background 0.15s, border-color 0.15s",
        }}
        onMouseEnter={(e) => { if (!isOpen) (e.currentTarget as HTMLElement).style.background = "rgba(255,255,255,0.055)"; }}
        onMouseLeave={(e) => { if (!isOpen) (e.currentTarget as HTMLElement).style.background = "rgba(255,255,255,0.035)"; }}
      >
        <svg width="14" height="14" viewBox="0 0 12 12" fill="none"
          style={{ transform: isOpen ? "rotate(90deg)" : "rotate(0deg)", transition: "transform 0.2s" }}>
          <path d="M4 2l4 4-4 4" stroke="rgba(255,255,255,0.5)" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
        <span style={{
          fontFamily: FONT, fontSize: "11px", fontWeight: 700, letterSpacing: "0.12em",
          textTransform: "uppercase", color: "rgba(255,255,255,0.98)",
          lineHeight: 1.4,
        }}>
          {department}
        </span>
        <span style={{ fontFamily: FONT, fontSize: "11px", fontWeight: 600, letterSpacing: "0.08em", textTransform: "uppercase", color: "rgba(255,255,255,0.45)" }}>
          {courseCount} {courseCount === 1 ? "course" : "courses"}
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
            <div style={{ padding: "8px 16px 16px 52px" }}>
              {isLoading && (
                <p style={{ fontFamily: FONT, fontSize: "13px", color: "rgba(255,255,255,0.3)" }}>Loading courses...</p>
              )}
              {!isLoading && (courses || []).map((course) => {
                const isCourseOpen = expandedCourses.has(course.code);
                const outcomes = course.learningOutcomes ?? [];
                const objectives = course.courseObjectives ?? [];
                const topCode = course.topCode ?? null;
                const topCodeDisplay = topCode && /^\d{6}$/.test(topCode)
                  ? `${topCode.slice(0, 4)}.${topCode.slice(4, 6)}`
                  : topCode;
                return (
                  <div key={course.code} style={{ marginBottom: "2px" }}>
                    <button
                      onClick={(e) => { e.stopPropagation(); toggleCourse(course.code); }}
                      style={{
                        width: "100%", textAlign: "left",
                        display: "flex", padding: "10px 12px", alignItems: "baseline", gap: "10px",
                        background: isCourseOpen ? "rgba(255,255,255,0.04)" : "transparent",
                        border: "none", borderRadius: isCourseOpen ? "6px 6px 0 0" : "6px",
                        cursor: "pointer", transition: "background 0.15s",
                      }}
                      onMouseEnter={(e) => { if (!isCourseOpen) (e.currentTarget as HTMLElement).style.background = "rgba(255,255,255,0.03)"; }}
                      onMouseLeave={(e) => { if (!isCourseOpen) (e.currentTarget as HTMLElement).style.background = "transparent"; }}
                    >
                      <span style={{ fontFamily: FONT, fontSize: "12px", fontWeight: 600, color: brandColor, flexShrink: 0 }}>
                        {course.code}
                      </span>
                      <span style={{ fontFamily: FONT, fontSize: "13px", color: "rgba(255,255,255,0.75)", flex: 1 }}>
                        {course.name}
                      </span>
                      {topCodeDisplay && (
                        <span style={{
                          fontFamily: "var(--font-mono), ui-monospace, SFMono-Regular, monospace",
                          fontSize: "11px", color: "rgba(255,255,255,0.4)",
                          letterSpacing: "0.02em", flexShrink: 0,
                        }}>
                          TOP {topCodeDisplay}
                        </span>
                      )}
                      <svg width="12" height="12" viewBox="0 0 12 12" fill="none"
                        style={{ transform: isCourseOpen ? "rotate(180deg)" : "rotate(0deg)", transition: "transform 0.2s", flexShrink: 0 }}>
                        <path d="M3 4.5l3 3 3-3" stroke="rgba(255,255,255,0.3)" strokeWidth="1.2" strokeLinecap="round" strokeLinejoin="round" />
                      </svg>
                    </button>

                    <AnimatePresence>
                      {isCourseOpen && (
                        <motion.div
                          initial={{ height: 0, opacity: 0 }}
                          animate={{ height: "auto", opacity: 1 }}
                          exit={{ height: 0, opacity: 0 }}
                          transition={{ duration: 0.2 }}
                          style={{ overflow: "hidden" }}
                        >
                          <div style={{
                            padding: "16px 16px 20px",
                            background: "rgba(255,255,255,0.03)",
                            borderRadius: "0 0 6px 6px",
                            display: "flex", flexDirection: "column", gap: "16px",
                          }}>
                            {course.description && (
                              <div>
                                <span style={{ fontFamily: FONT, fontSize: "10px", fontWeight: 600, letterSpacing: "0.1em", textTransform: "uppercase", color: brandColor, opacity: 0.6, display: "block", marginBottom: "8px" }}>
                                  Description
                                </span>
                                <p style={{ fontFamily: FONT, fontSize: "13px", color: "rgba(255,255,255,0.6)", lineHeight: 1.6, margin: 0 }}>
                                  {course.description}
                                </p>
                              </div>
                            )}
                            {outcomes.length > 0 && (
                              <div>
                                <span style={{ fontFamily: FONT, fontSize: "10px", fontWeight: 600, letterSpacing: "0.1em", textTransform: "uppercase", color: brandColor, opacity: 0.6, display: "block", marginBottom: "8px" }}>
                                  Learning Outcomes
                                </span>
                                <ul style={{ margin: 0, paddingLeft: "16px", display: "flex", flexDirection: "column", gap: "4px" }}>
                                  {outcomes.map((o) => (
                                    <li key={o} style={{ fontFamily: FONT, fontSize: "12px", color: "rgba(255,255,255,0.6)", lineHeight: 1.5 }}>{o}</li>
                                  ))}
                                </ul>
                              </div>
                            )}
                            {outcomes.length === 0 && objectives.length > 0 && (
                              <div>
                                <span style={{ fontFamily: FONT, fontSize: "10px", fontWeight: 600, letterSpacing: "0.1em", textTransform: "uppercase", color: brandColor, opacity: 0.6, display: "block", marginBottom: "8px" }}>
                                  Course Objectives
                                </span>
                                <ul style={{ margin: 0, paddingLeft: "16px", display: "flex", flexDirection: "column", gap: "4px" }}>
                                  {objectives.map((o) => (
                                    <li key={o} style={{ fontFamily: FONT, fontSize: "12px", color: "rgba(255,255,255,0.6)", lineHeight: 1.5 }}>{o}</li>
                                  ))}
                                </ul>
                              </div>
                            )}
                            {schoolName && !hideOccupationPathways && (
                              <CourseOccupationsCallout
                                courseCode={course.code}
                                collegeName={schoolName}
                                brandColor={brandColor}
                              />
                            )}
                          </div>
                        </motion.div>
                      )}
                    </AnimatePresence>
                  </div>
                );
              })}
              {schoolName && <DataCitation source={`${schoolName} Catalog`} />}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
