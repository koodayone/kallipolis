"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { SchoolConfig } from "@/lib/schoolConfig";
import { getDepartments, getCourses } from "@/lib/api";
import type { ApiDepartmentSummary, ApiCourseSummary } from "@/lib/api";
import type { DepartmentSummary, CourseSummary } from "@/lib/curricula/types";
import LeafHeader from "@/components/ui/LeafHeader";
import RisingSun from "@/components/ui/RisingSun";

const FONT = "var(--font-inter), Inter, system-ui, sans-serif";

function mapDept(api: ApiDepartmentSummary): DepartmentSummary {
  return { department: api.department, courseCount: api.course_count };
}

function mapCourse(api: ApiCourseSummary): CourseSummary {
  return {
    name: api.name, code: api.code, description: api.description,
    learningOutcomes: api.learning_outcomes, courseObjectives: api.course_objectives,
    skillMappings: api.skill_mappings,
  };
}

const SUGGESTIONS = [
  "Computer Science courses",
  "Departments with most courses",
  "Nursing department",
  "Courses with Programming skills",
  "Mathematics courses",
];

function filterDepartments(query: string, departments: DepartmentSummary[]): DepartmentSummary[] {
  const q = query.toLowerCase().trim();
  if (!q) return [];
  if (q.includes("most courses") || q.includes("largest")) {
    return [...departments].sort((a, b) => b.courseCount - a.courseCount).slice(0, 20);
  }
  const cleaned = q.replace(" courses", "").replace(" department", "").replace("courses", "").replace("department", "").trim();
  const match = departments.filter((d) => d.department.toLowerCase().includes(cleaned));
  if (match.length > 0) return match;
  return departments.filter((d) => d.department.toLowerCase().includes(q));
}

type Props = { school: SchoolConfig; onBack: () => void };

export default function CoursesView({ school, onBack }: Props) {
  const [departments, setDepartments] = useState<DepartmentSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [userName, setUserName] = useState<string>("");
  const [query, setQuery] = useState("");
  const [submitted, setSubmitted] = useState(false);
  const [results, setResults] = useState<DepartmentSummary[]>([]);
  const [expandedDept, setExpandedDept] = useState<string | null>(null);
  const [deptCourses, setDeptCourses] = useState<CourseSummary[]>([]);
  const [coursesLoading, setCoursesLoading] = useState(false);
  const [expandedCourse, setExpandedCourse] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    getDepartments(school.name)
      .then((data) => setDepartments(data.map(mapDept).sort((a, b) => a.department.localeCompare(b.department))))
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
    fetch("/api/auth/me")
      .then((r) => r.json())
      .then((data) => { if (data?.user?.name) setUserName(data.user.name.split(" ")[0]); })
      .catch(() => {});
  }, []);

  const handleSubmit = useCallback(() => {
    if (!query.trim()) return;
    setResults(filterDepartments(query, departments));
    setSubmitted(true);
    setExpandedDept(null);
    setDeptCourses([]);
    setExpandedCourse(null);
  }, [query, departments]);

  const handleChip = useCallback((text: string) => {
    setQuery(text);
    setResults(filterDepartments(text, departments));
    setSubmitted(true);
    setExpandedDept(null);
    setDeptCourses([]);
    setExpandedCourse(null);
  }, [departments]);

  const handleDeptExpand = useCallback(async (dept: string) => {
    if (expandedDept === dept) { setExpandedDept(null); setDeptCourses([]); setExpandedCourse(null); return; }
    setExpandedDept(dept);
    setExpandedCourse(null);
    setCoursesLoading(true);
    try {
      const data = await getCourses(dept, school.name);
      setDeptCourses(data.map(mapCourse).sort((a, b) => {
        const numA = parseInt((a.code.match(/(\d+)/) || ["0"])[0]);
        const numB = parseInt((b.code.match(/(\d+)/) || ["0"])[0]);
        return numA - numB || a.code.localeCompare(b.code);
      }));
    } catch { setDeptCourses([]); }
    finally { setCoursesLoading(false); }
  }, [expandedDept, school.name]);

  const handleReset = useCallback(() => {
    setQuery(""); setSubmitted(false); setResults([]);
    setExpandedDept(null); setDeptCourses([]); setExpandedCourse(null);
    setTimeout(() => inputRef.current?.focus(), 100);
  }, []);

  const totalCourses = departments.reduce((sum, d) => sum + d.courseCount, 0);

  return (
    <>
      <LeafHeader school={school} onBack={onBack} parentShape="cube" />
      <div style={{ display: "flex", justifyContent: "center", paddingTop: "32px", paddingBottom: "16px" }}>
        <img src={school.logoPath} alt={school.name} style={{ height: "100px", width: "auto", objectFit: "contain" }} />
      </div>

      <div style={{ maxWidth: "760px", margin: "0 auto", padding: "0 40px 80px" }}>
        {error && <p style={{ fontFamily: FONT, fontSize: "14px", color: "#e55", textAlign: "center", paddingTop: "40px" }}>{error}</p>}
        {loading && (
          <div style={{ display: "flex", justifyContent: "center", paddingTop: "80px" }}>
            <RisingSun style={{ width: "70px", height: "auto", opacity: 0.4 }} />
          </div>
        )}

        {/* ── Initial State ── */}
        {!submitted && !loading && (
          <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.4 }}
            style={{ display: "flex", flexDirection: "column", gap: "24px" }}>

            <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: "24px", paddingTop: "40px" }}>
              <RisingSun style={{ width: "70px", height: "auto" }} />
              <h1 style={{ fontFamily: FONT, fontSize: "28px", fontWeight: 600, color: "#f0eef4", letterSpacing: "-0.02em", textAlign: "center" }}>
                What&apos;s up{userName ? `, ${userName}` : ""}?
              </h1>
              <div style={{ width: "100%" }}>
                <input ref={inputRef} type="text" value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  onKeyDown={(e) => { if (e.key === "Enter") handleSubmit(); }}
                  placeholder={`Ask me a question about ${school.name} courses.`}
                  style={{
                    width: "100%", padding: "18px 24px", fontFamily: FONT, fontSize: "15px",
                    color: "#f0eef4", background: "rgba(255,255,255,0.04)",
                    border: "1px solid rgba(255,255,255,0.10)", borderRadius: "16px",
                    outline: "none", transition: "border-color 0.2s, box-shadow 0.2s",
                  }}
                  onFocus={(e) => { e.currentTarget.style.borderColor = `${school.brandColorLight}50`; e.currentTarget.style.boxShadow = `0 0 0 3px ${school.brandColorLight}15`; }}
                  onBlur={(e) => { e.currentTarget.style.borderColor = "rgba(255,255,255,0.10)"; e.currentTarget.style.boxShadow = "none"; }}
                />
              </div>
              <div style={{ display: "flex", flexWrap: "wrap", gap: "10px", justifyContent: "center" }}>
                {SUGGESTIONS.map((s) => (
                  <button key={s} onClick={() => handleChip(s)}
                    style={{
                      fontFamily: FONT, fontSize: "13px", color: "rgba(255,255,255,0.55)",
                      background: "transparent", border: "1px solid rgba(255,255,255,0.12)",
                      borderRadius: "100px", padding: "8px 18px", cursor: "pointer",
                      transition: "background 0.15s, color 0.15s, border-color 0.15s",
                    }}
                    onMouseEnter={(e) => { const el = e.currentTarget as HTMLElement; el.style.background = `${school.brandColorLight}15`; el.style.borderColor = `${school.brandColorLight}40`; el.style.color = school.brandColorLight; }}
                    onMouseLeave={(e) => { const el = e.currentTarget as HTMLElement; el.style.background = "transparent"; el.style.borderColor = "rgba(255,255,255,0.12)"; el.style.color = "rgba(255,255,255,0.55)"; }}
                  >{s}</button>
                ))}
              </div>
            </div>

            {/* Department list */}
            <div style={{ marginTop: "16px" }}>
              <p style={{ fontFamily: FONT, fontSize: "13px", color: "rgba(255,255,255,0.35)", marginBottom: "12px" }}>
                {departments.length} departments · {totalCourses.toLocaleString()} courses
              </p>
              <DepartmentList
                departments={departments} school={school}
                expandedDept={expandedDept} deptCourses={deptCourses}
                coursesLoading={coursesLoading} expandedCourse={expandedCourse}
                onDeptExpand={handleDeptExpand}
                onCourseToggle={(code) => setExpandedCourse(expandedCourse === code ? null : code)}
              />
            </div>
          </motion.div>
        )}

        {/* ── Results State ── */}
        {submitted && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.3 }}
            style={{ display: "flex", flexDirection: "column", gap: "16px" }}>

            <div style={{ display: "flex", gap: "10px", alignItems: "center" }}>
              <input ref={inputRef} type="text" value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyDown={(e) => { if (e.key === "Enter") handleSubmit(); }}
                placeholder={`Ask me a question about ${school.name} courses.`}
                style={{
                  flex: 1, padding: "14px 20px", fontFamily: FONT, fontSize: "14px",
                  color: "#f0eef4", background: "rgba(255,255,255,0.04)",
                  border: "1px solid rgba(255,255,255,0.10)", borderRadius: "12px",
                  outline: "none", transition: "border-color 0.2s, box-shadow 0.2s",
                }}
                onFocus={(e) => { e.currentTarget.style.borderColor = `${school.brandColorLight}50`; e.currentTarget.style.boxShadow = `0 0 0 3px ${school.brandColorLight}15`; }}
                onBlur={(e) => { e.currentTarget.style.borderColor = "rgba(255,255,255,0.10)"; e.currentTarget.style.boxShadow = "none"; }}
              />
              <button onClick={handleReset}
                style={{ fontFamily: FONT, fontSize: "12px", color: "rgba(255,255,255,0.4)", background: "none", border: "none", cursor: "pointer", padding: "8px", transition: "color 0.15s" }}
                onMouseEnter={(e) => { (e.currentTarget as HTMLElement).style.color = "rgba(255,255,255,0.8)"; }}
                onMouseLeave={(e) => { (e.currentTarget as HTMLElement).style.color = "rgba(255,255,255,0.4)"; }}
              >Clear</button>
            </div>

            <p style={{ fontFamily: FONT, fontSize: "14px", color: "rgba(255,255,255,0.5)" }}>
              {results.length} department{results.length !== 1 ? "s" : ""} found
            </p>

            <DepartmentList
              departments={results} school={school}
              expandedDept={expandedDept} deptCourses={deptCourses}
              coursesLoading={coursesLoading} expandedCourse={expandedCourse}
              onDeptExpand={handleDeptExpand}
              onCourseToggle={(code) => setExpandedCourse(expandedCourse === code ? null : code)}
            />
          </motion.div>
        )}
      </div>
    </>
  );
}

/* ── Department List (shared) ──────────────────────────────────────────── */

function DepartmentList({
  departments, school, expandedDept, deptCourses, coursesLoading, expandedCourse,
  onDeptExpand, onCourseToggle,
}: {
  departments: DepartmentSummary[];
  school: SchoolConfig;
  expandedDept: string | null;
  deptCourses: CourseSummary[];
  coursesLoading: boolean;
  expandedCourse: string | null;
  onDeptExpand: (dept: string) => void;
  onCourseToggle: (code: string) => void;
}) {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "2px" }}>
      {/* Column headers */}
      <div style={{
        display: "grid", gridTemplateColumns: "24px 1fr auto",
        padding: "8px 16px", gap: "12px", alignItems: "center",
      }}>
        <span />
        <span style={{ fontFamily: "var(--font-inter), Inter, system-ui, sans-serif", fontSize: "10px", fontWeight: 600, letterSpacing: "0.1em", textTransform: "uppercase", color: school.brandColorLight, opacity: 0.6 }}>Department</span>
        <span style={{ fontFamily: "var(--font-inter), Inter, system-ui, sans-serif", fontSize: "10px", fontWeight: 600, letterSpacing: "0.1em", textTransform: "uppercase", color: school.brandColorLight, opacity: 0.6 }}>Courses</span>
      </div>
      {departments.map((dept, i) => (
        <div key={dept.department}>
          <motion.button
            initial={{ opacity: 0, y: 6 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.2, delay: Math.min(i * 0.01, 0.2) }}
            onClick={() => onDeptExpand(dept.department)}
            style={{
              width: "100%", textAlign: "left",
              display: "grid", gridTemplateColumns: "24px 1fr auto",
              padding: "14px 16px", gap: "12px", alignItems: "center",
              background: expandedDept === dept.department ? "rgba(255,255,255,0.06)" : "rgba(255,255,255,0.03)",
              border: "none", borderBottom: "1px solid rgba(255,255,255,0.05)",
              cursor: "pointer", transition: "background 0.15s",
            }}
            onMouseEnter={(e) => { if (expandedDept !== dept.department) (e.currentTarget as HTMLElement).style.background = "rgba(255,255,255,0.05)"; }}
            onMouseLeave={(e) => { if (expandedDept !== dept.department) (e.currentTarget as HTMLElement).style.background = "rgba(255,255,255,0.03)"; }}
          >
            <svg width="12" height="12" viewBox="0 0 12 12" fill="none"
              style={{ transform: expandedDept === dept.department ? "rotate(90deg)" : "rotate(0deg)", transition: "transform 0.2s" }}>
              <path d="M4 2l4 4-4 4" stroke="rgba(255,255,255,0.3)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
            <span style={{ fontFamily: "var(--font-inter), Inter, system-ui, sans-serif", fontSize: "14px", fontWeight: 500, color: "rgba(255,255,255,0.85)" }}>
              {dept.department}
            </span>
            <span style={{ fontFamily: "var(--font-inter), Inter, system-ui, sans-serif", fontSize: "12px", color: "rgba(255,255,255,0.4)" }}>
              {dept.courseCount} {dept.courseCount === 1 ? "course" : "courses"}
            </span>
          </motion.button>

          <AnimatePresence>
            {expandedDept === dept.department && (
              <motion.div
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: "auto", opacity: 1 }}
                exit={{ height: 0, opacity: 0 }}
                transition={{ duration: 0.25 }}
                style={{ overflow: "hidden", background: "rgba(255,255,255,0.02)" }}
              >
                <div style={{ padding: "8px 16px 16px 52px" }}>
                  {coursesLoading && (
                    <p style={{ fontFamily: "var(--font-inter), Inter, system-ui, sans-serif", fontSize: "13px", color: "rgba(255,255,255,0.3)" }}>Loading courses...</p>
                  )}
                  {!coursesLoading && deptCourses.map((course) => {
                    const isOpen = expandedCourse === course.code;
                    return (
                      <div key={course.code} style={{ marginBottom: "2px" }}>
                        <button
                          onClick={(e) => { e.stopPropagation(); onCourseToggle(course.code); }}
                          style={{
                            width: "100%", textAlign: "left",
                            display: "flex", padding: "10px 12px", alignItems: "baseline", gap: "10px",
                            background: isOpen ? "rgba(255,255,255,0.04)" : "transparent",
                            border: "none", borderRadius: isOpen ? "6px 6px 0 0" : "6px",
                            cursor: "pointer", transition: "background 0.15s",
                          }}
                          onMouseEnter={(e) => { if (!isOpen) (e.currentTarget as HTMLElement).style.background = "rgba(255,255,255,0.03)"; }}
                          onMouseLeave={(e) => { if (!isOpen) (e.currentTarget as HTMLElement).style.background = "transparent"; }}
                        >
                          <span style={{ fontFamily: "var(--font-inter), Inter, system-ui, sans-serif", fontSize: "12px", fontWeight: 600, color: school.brandColorLight, flexShrink: 0 }}>
                            {course.code}
                          </span>
                          <span style={{ fontFamily: "var(--font-inter), Inter, system-ui, sans-serif", fontSize: "13px", color: "rgba(255,255,255,0.75)", flex: 1 }}>
                            {course.name}
                          </span>
                          <svg width="12" height="12" viewBox="0 0 12 12" fill="none"
                            style={{ transform: isOpen ? "rotate(180deg)" : "rotate(0deg)", transition: "transform 0.2s", flexShrink: 0 }}>
                            <path d="M3 4.5l3 3 3-3" stroke="rgba(255,255,255,0.3)" strokeWidth="1.2" strokeLinecap="round" strokeLinejoin="round" />
                          </svg>
                        </button>

                        <AnimatePresence>
                          {isOpen && (
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
                                    <span style={{ fontFamily: "var(--font-inter), Inter, system-ui, sans-serif", fontSize: "10px", fontWeight: 600, letterSpacing: "0.1em", textTransform: "uppercase", color: school.brandColorLight, opacity: 0.6, display: "block", marginBottom: "8px" }}>
                                      Description
                                    </span>
                                    <p style={{ fontFamily: "var(--font-inter), Inter, system-ui, sans-serif", fontSize: "13px", color: "rgba(255,255,255,0.6)", lineHeight: 1.6, margin: 0 }}>
                                      {course.description}
                                    </p>
                                  </div>
                                )}
                                {course.learningOutcomes.length > 0 && (
                                  <div>
                                    <span style={{ fontFamily: "var(--font-inter), Inter, system-ui, sans-serif", fontSize: "10px", fontWeight: 600, letterSpacing: "0.1em", textTransform: "uppercase", color: school.brandColorLight, opacity: 0.6, display: "block", marginBottom: "8px" }}>
                                      Learning Outcomes
                                    </span>
                                    <ul style={{ margin: 0, paddingLeft: "16px", display: "flex", flexDirection: "column", gap: "4px" }}>
                                      {course.learningOutcomes.map((o) => (
                                        <li key={o} style={{ fontFamily: "var(--font-inter), Inter, system-ui, sans-serif", fontSize: "12px", color: "rgba(255,255,255,0.6)", lineHeight: 1.5 }}>{o}</li>
                                      ))}
                                    </ul>
                                  </div>
                                )}
                                {course.learningOutcomes.length === 0 && course.courseObjectives.length > 0 && (
                                  <div>
                                    <span style={{ fontFamily: "var(--font-inter), Inter, system-ui, sans-serif", fontSize: "10px", fontWeight: 600, letterSpacing: "0.1em", textTransform: "uppercase", color: school.brandColorLight, opacity: 0.6, display: "block", marginBottom: "8px" }}>
                                      Learning Outcomes
                                    </span>
                                    <ul style={{ margin: 0, paddingLeft: "16px", display: "flex", flexDirection: "column", gap: "4px" }}>
                                      {course.courseObjectives.map((o) => (
                                        <li key={o} style={{ fontFamily: "var(--font-inter), Inter, system-ui, sans-serif", fontSize: "12px", color: "rgba(255,255,255,0.6)", lineHeight: 1.5 }}>{o}</li>
                                      ))}
                                    </ul>
                                  </div>
                                )}
                                {course.skillMappings.length > 0 && (
                                  <div>
                                    <span style={{ fontFamily: "var(--font-inter), Inter, system-ui, sans-serif", fontSize: "10px", fontWeight: 600, letterSpacing: "0.1em", textTransform: "uppercase", color: school.brandColorLight, opacity: 0.6, display: "block", marginBottom: "8px" }}>
                                      Derived Skills
                                    </span>
                                    <div style={{ display: "flex", flexWrap: "wrap", gap: "6px" }}>
                                      {course.skillMappings.map((skill) => (
                                        <span key={skill} style={{
                                          padding: "5px 12px", background: "rgba(255,255,255,0.02)",
                                          border: `1px solid ${school.brandColorLight}60`, borderRadius: "6px",
                                          fontFamily: "var(--font-inter), Inter, system-ui, sans-serif", fontSize: "12px", fontWeight: 500, color: school.brandColorLight,
                                        }}>{skill}</span>
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
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      ))}
      {departments.length === 0 && (
        <p style={{ fontFamily: "var(--font-inter), Inter, system-ui, sans-serif", fontSize: "14px", color: "rgba(255,255,255,0.35)", padding: "40px 0", textAlign: "center" }}>
          No departments match that query. Try a different question.
        </p>
      )}
    </div>
  );
}
