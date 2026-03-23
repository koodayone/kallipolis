"use client";

import { useState, useEffect, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { SchoolConfig } from "@/lib/schoolConfig";
import { getDepartments, getCourses } from "@/lib/api";
import type { ApiDepartmentSummary, ApiCourseSummary } from "@/lib/api";
import type { DepartmentSummary, CourseSummary } from "@/lib/curricula/types";
import LeafHeader from "@/components/ui/LeafHeader";

const FONT = "var(--font-inter), Inter, system-ui, sans-serif";

type ViewState = "departments" | "courses";

function mapDept(api: ApiDepartmentSummary): DepartmentSummary {
  return { department: api.department, courseCount: api.course_count };
}

function mapCourse(api: ApiCourseSummary): CourseSummary {
  return {
    name: api.name,
    code: api.code,
    learningOutcomes: api.learning_outcomes,
    skillMappings: api.skill_mappings,
  };
}

type Props = {
  school: SchoolConfig;
  onBack: () => void;
};

export default function CurriculaView({ school, onBack }: Props) {
  const [view, setView] = useState<ViewState>("departments");
  const [departments, setDepartments] = useState<DepartmentSummary[]>([]);
  const [courses, setCourses] = useState<CourseSummary[]>([]);
  const [activeDept, setActiveDept] = useState<string>("");
  const [expandedCourses, setExpandedCourses] = useState<Set<string>>(new Set());
  const [loading, setLoading] = useState(true);
  const [coursesLoading, setCoursesLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getDepartments()
      .then((data) => setDepartments(data.map(mapDept)))
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  const handleDeptClick = useCallback(async (dept: string) => {
    setCoursesLoading(true);
    setActiveDept(dept);
    setExpandedCourses(new Set());
    try {
      const data = await getCourses(dept);
      setCourses(data.map(mapCourse));
      setView("courses");
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setCoursesLoading(false);
    }
  }, []);

  const toggleCourse = useCallback((name: string) => {
    setExpandedCourses((prev) => {
      const next = new Set(prev);
      if (next.has(name)) next.delete(name);
      else next.add(name);
      return next;
    });
  }, []);

  return (
    <>
      <LeafHeader school={school} onBack={onBack} parentShape="cube" />
      <div style={{ display: "flex", justifyContent: "center", paddingTop: "32px", paddingBottom: "16px" }}>
        <img src={school.logoPath} alt={school.name} style={{ height: "100px", width: "auto", objectFit: "contain" }} />
      </div>
    <div style={{ maxWidth: "800px", margin: "0 auto", padding: "32px 40px 80px", display: "flex", flexDirection: "column", gap: "32px" }}>
      {/* Internal back (courses → departments) */}
      {view === "courses" && (
        <button
          onClick={() => setView("departments")}
          style={{
            display: "flex", alignItems: "center", gap: "6px",
            background: "none", border: "none", cursor: "pointer", padding: 0,
            color: "rgba(255,255,255,0.4)", fontFamily: FONT, fontSize: "12px",
            fontWeight: 500, letterSpacing: "0.08em", textTransform: "uppercase",
            transition: "color 0.15s", alignSelf: "flex-start",
          }}
          onMouseEnter={(e) => ((e.currentTarget as HTMLElement).style.color = "rgba(255,255,255,0.85)")}
          onMouseLeave={(e) => ((e.currentTarget as HTMLElement).style.color = "rgba(255,255,255,0.4)")}
        >
          <svg width="14" height="14" viewBox="0 0 16 16" fill="none">
            <path d="M10 12L6 8l4-4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
          All Departments
        </button>
      )}

      {error && (
        <p style={{ fontFamily: FONT, fontSize: "14px", color: "#e55" }}>{error}</p>
      )}

      {/* ── Level 1: Department List ── */}
      {view === "departments" && (
        <>
          <div>
            <h1 style={{ fontFamily: FONT, fontSize: "24px", fontWeight: 600, color: "#f0eef4", letterSpacing: "-0.02em", marginBottom: "8px" }}>
              Curricula
            </h1>
            <p style={{ fontFamily: FONT, fontSize: "14px", color: "rgba(255,255,255,0.5)", lineHeight: 1.6 }}>
              Academic departments and their course offerings. Select a department to explore courses, learning outcomes, and derived skill mappings.
            </p>
          </div>

          {loading ? (
            <p style={{ fontFamily: FONT, fontSize: "14px", color: "rgba(255,255,255,0.4)" }}>Loading...</p>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: "2px" }}>
              {departments.map((dept) => (
                <button
                  key={dept.department}
                  onClick={() => handleDeptClick(dept.department)}
                  style={{
                    display: "flex", padding: "18px 24px", justifyContent: "space-between", alignItems: "center",
                    background: "rgba(255,255,255,0.04)", border: "1px solid rgba(255,255,255,0.06)",
                    borderRadius: "6px", cursor: "pointer", transition: "background 0.15s",
                    width: "100%", textAlign: "left",
                  }}
                  onMouseEnter={(e) => (e.currentTarget.style.background = "rgba(255,255,255,0.06)")}
                  onMouseLeave={(e) => (e.currentTarget.style.background = "rgba(255,255,255,0.04)")}
                >
                  <span style={{ fontFamily: FONT, fontSize: "15px", fontWeight: 600, color: "rgba(255,255,255,0.9)" }}>
                    {dept.department}
                  </span>
                  <span style={{ fontFamily: FONT, fontSize: "13px", color: "rgba(255,255,255,0.4)" }}>
                    {dept.courseCount} {dept.courseCount === 1 ? "course" : "courses"}
                  </span>
                </button>
              ))}
            </div>
          )}
        </>
      )}

      {/* ── Level 2: Course List ── */}
      {view === "courses" && (
        <>
          <div>
            <h1 style={{ fontFamily: FONT, fontSize: "24px", fontWeight: 600, color: "#f0eef4", letterSpacing: "-0.02em", marginBottom: "8px" }}>
              {activeDept}
            </h1>
            <p style={{ fontFamily: FONT, fontSize: "14px", color: "rgba(255,255,255,0.5)", lineHeight: 1.6 }}>
              {courses.length} courses. Select a course to view learning outcomes and derived skill mappings.
            </p>
          </div>

          {coursesLoading ? (
            <p style={{ fontFamily: FONT, fontSize: "14px", color: "rgba(255,255,255,0.4)" }}>Loading...</p>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
              {courses.map((course) => {
                const isExpanded = expandedCourses.has(course.name);
                return (
                  <div key={course.name}>
                    <button
                      onClick={() => toggleCourse(course.name)}
                      style={{
                        display: "flex", padding: "16px 24px", justifyContent: "space-between", alignItems: "center",
                        background: "rgba(255,255,255,0.04)", border: "1px solid rgba(255,255,255,0.06)",
                        borderRadius: isExpanded ? "6px 6px 0 0" : "6px",
                        cursor: "pointer", transition: "background 0.15s",
                        width: "100%", textAlign: "left",
                      }}
                      onMouseEnter={(e) => (e.currentTarget.style.background = "rgba(255,255,255,0.06)")}
                      onMouseLeave={(e) => (e.currentTarget.style.background = "rgba(255,255,255,0.04)")}
                    >
                      <div style={{ display: "flex", alignItems: "baseline", gap: "12px" }}>
                        <span style={{ fontFamily: FONT, fontSize: "12px", fontWeight: 600, letterSpacing: "0.06em", color: school.brandColorLight }}>
                          {course.code}
                        </span>
                        <span style={{ fontFamily: FONT, fontSize: "14px", fontWeight: 500, color: "rgba(255,255,255,0.9)" }}>
                          {course.name}
                        </span>
                      </div>
                      <svg
                        width="14" height="14" viewBox="0 0 16 16" fill="none"
                        style={{ transform: isExpanded ? "rotate(180deg)" : "rotate(0deg)", transition: "transform 0.2s", flexShrink: 0 }}
                      >
                        <path d="M4 6l4 4 4-4" stroke="rgba(255,255,255,0.4)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
                      </svg>
                    </button>

                    <AnimatePresence>
                      {isExpanded && (
                        <motion.div
                          initial={{ height: 0, opacity: 0 }}
                          animate={{ height: "auto", opacity: 1 }}
                          exit={{ height: 0, opacity: 0 }}
                          transition={{ duration: 0.2 }}
                          style={{ overflow: "hidden" }}
                        >
                          <div
                            style={{
                              padding: "20px 24px",
                              background: "rgba(255,255,255,0.04)",
                              borderLeft: "1px solid rgba(255,255,255,0.06)",
                              borderRight: "1px solid rgba(255,255,255,0.06)",
                              borderBottom: "1px solid rgba(255,255,255,0.06)",
                              borderRadius: "0 0 6px 6px",
                              display: "flex",
                              flexDirection: "column",
                              gap: "20px",
                            }}
                          >
                            {/* Learning Outcomes */}
                            {course.learningOutcomes.length > 0 && (
                              <div>
                                <span style={{ fontFamily: FONT, fontSize: "11px", fontWeight: 600, letterSpacing: "0.1em", textTransform: "uppercase", color: "rgba(255,255,255,0.35)", display: "block", marginBottom: "10px" }}>
                                  Learning Outcomes
                                </span>
                                <ul style={{ margin: 0, paddingLeft: "18px", display: "flex", flexDirection: "column", gap: "6px" }}>
                                  {course.learningOutcomes.map((outcome) => (
                                    <li key={outcome} style={{ fontFamily: FONT, fontSize: "13px", color: "rgba(255,255,255,0.7)", lineHeight: 1.5 }}>
                                      {outcome}
                                    </li>
                                  ))}
                                </ul>
                              </div>
                            )}

                            {/* Skill Mappings */}
                            {course.skillMappings.length > 0 && (
                              <div>
                                <span style={{ fontFamily: FONT, fontSize: "11px", fontWeight: 600, letterSpacing: "0.1em", textTransform: "uppercase", color: "rgba(255,255,255,0.35)", display: "block", marginBottom: "10px" }}>
                                  Derived Skills
                                </span>
                                <div style={{ display: "flex", flexWrap: "wrap", gap: "8px" }}>
                                  {course.skillMappings.map((skill) => (
                                    <span
                                      key={skill}
                                      style={{
                                        padding: "6px 14px",
                                        background: "transparent",
                                        border: `1px solid ${school.brandColorLight}`,
                                        borderRadius: "6px",
                                        fontFamily: FONT,
                                        fontSize: "12px",
                                        fontWeight: 500,
                                        color: school.brandColorLight,
                                      }}
                                    >
                                      {skill}
                                    </span>
                                  ))}
                                </div>
                              </div>
                            )}
                          </div>
                        </motion.div>
                      )}
                    </AnimatePresence>
                  </div>
                );
              })}
            </div>
          )}
        </>
      )}
    </div>
    </>
  );
}
