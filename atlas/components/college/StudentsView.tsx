"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { SchoolConfig } from "@/lib/schoolConfig";
import { getStudents, getStudent } from "@/lib/api";
import type { ApiStudentSummary, ApiStudentDetail } from "@/lib/api";
import type { StudentSummary, StudentDetail } from "@/lib/students/types";
import LeafHeader from "@/components/ui/LeafHeader";
import RisingSun from "@/components/ui/RisingSun";

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

function mapSummary(api: ApiStudentSummary, index: number): StudentSummary {
  return {
    uuid: api.uuid,
    displayNumber: index + 1,
    primaryFocus: api.primary_focus,
    coursesCompleted: api.courses_completed,
    gpa: api.gpa,
  };
}

function mapDetail(api: ApiStudentDetail, displayNumber: number): StudentDetail {
  return {
    uuid: api.uuid,
    displayNumber,
    primaryFocus: api.primary_focus,
    coursesCompleted: api.courses_completed,
    gpa: api.gpa,
    enrollments: api.enrollments.map((e) => ({
      courseName: e.course_name,
      department: e.department,
      grade: e.grade,
      term: e.term,
      status: e.status,
    })),
    skills: api.skills,
  };
}

const SUGGESTIONS = [
  "Students with highest GPA",
  "Computer Science students",
  "Who has Programming skills?",
  "15+ courses completed",
  "Dental Hygiene skill profiles",
];

function filterStudents(query: string, students: StudentSummary[]): StudentSummary[] {
  const q = query.toLowerCase().trim();
  if (!q) return [];

  // GPA filter
  const gpaMatch = q.match(/gpa\s*(?:above|over|>)\s*([\d.]+)/);
  if (gpaMatch) return students.filter((s) => s.gpa >= parseFloat(gpaMatch[1]));
  if (q.includes("highest gpa")) return [...students].sort((a, b) => b.gpa - a.gpa).slice(0, 50);
  if (q.includes("lowest gpa")) return [...students].sort((a, b) => a.gpa - b.gpa).slice(0, 50);

  // Course count
  const courseMatch = q.match(/(\d+)\+?\s*courses|more than\s*(\d+)\s*courses/);
  if (courseMatch) {
    const n = parseInt(courseMatch[1] || courseMatch[2]);
    return students.filter((s) => s.coursesCompleted >= n);
  }

  // Department/focus filter (fallback — matches against primaryFocus)
  const deptMatch = students.filter((s) => s.primaryFocus.toLowerCase().includes(q.replace(" students", "").replace("students", "").trim()));
  if (deptMatch.length > 0 && deptMatch.length < students.length) return deptMatch;

  // Broad fallback
  return students.filter((s) => s.primaryFocus.toLowerCase().includes(q));
}

type Props = {
  school: SchoolConfig;
  onBack: () => void;
};

export default function StudentsView({ school, onBack }: Props) {
  const [students, setStudents] = useState<StudentSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [userName, setUserName] = useState<string>("");
  const [query, setQuery] = useState("");
  const [submitted, setSubmitted] = useState(false);
  const [results, setResults] = useState<StudentSummary[]>([]);
  const [expandedUuid, setExpandedUuid] = useState<string | null>(null);
  const [expandedDetail, setExpandedDetail] = useState<StudentDetail | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [detailTab, setDetailTab] = useState<"history" | "skills">("history");
  const inputRef = useRef<HTMLInputElement>(null);

  // Load students and user name on mount
  useEffect(() => {
    getStudents(school.name)
      .then((data) => setStudents(data.map(mapSummary)))
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));

    fetch("/api/auth/me")
      .then((r) => r.json())
      .then((data) => {
        if (data?.user?.name) setUserName(data.user.name.split(" ")[0]);
      })
      .catch(() => {});
  }, []);

  const handleSubmit = useCallback(() => {
    if (!query.trim()) return;
    const filtered = filterStudents(query, students);
    setResults(filtered);
    setSubmitted(true);
    setExpandedUuid(null);
    setExpandedDetail(null);
  }, [query, students]);

  const handleChip = useCallback((text: string) => {
    setQuery(text);
    const filtered = filterStudents(text, students);
    setResults(filtered);
    setSubmitted(true);
    setExpandedUuid(null);
    setExpandedDetail(null);
  }, [students]);

  const handleExpand = useCallback(async (student: StudentSummary) => {
    if (expandedUuid === student.uuid) {
      setExpandedUuid(null);
      setExpandedDetail(null);
      return;
    }
    setExpandedUuid(student.uuid);
    setDetailLoading(true);
    setDetailTab("history");
    try {
      const data = await getStudent(student.uuid, school.name);
      setExpandedDetail(mapDetail(data, student.displayNumber));
    } catch {
      setExpandedDetail(null);
    } finally {
      setDetailLoading(false);
    }
  }, [expandedUuid, school.name]);

  const handleReset = useCallback(() => {
    setQuery("");
    setSubmitted(false);
    setResults([]);
    setExpandedUuid(null);
    setExpandedDetail(null);
    setTimeout(() => inputRef.current?.focus(), 100);
  }, []);

  const showInitial = !submitted && !loading;
  const showResults = submitted;

  return (
    <>
      <LeafHeader school={school} onBack={onBack} parentShape="cube" />
      <div style={{ display: "flex", justifyContent: "center", paddingTop: "32px", paddingBottom: "16px" }}>
        <img src={school.logoPath} alt={school.name} style={{ height: "100px", width: "auto", objectFit: "contain" }} />
      </div>

      <div style={{ maxWidth: "760px", margin: "0 auto", padding: "0 40px 80px" }}>
        {error && (
          <p style={{ fontFamily: FONT, fontSize: "14px", color: "#e55", textAlign: "center", paddingTop: "40px" }}>{error}</p>
        )}

        {loading && (
          <div style={{ display: "flex", justifyContent: "center", paddingTop: "80px" }}>
            <RisingSun style={{ width: "70px", height: "auto", opacity: 0.4 }} />
          </div>
        )}

        {/* ── Initial State ── */}
        {showInitial && (
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4 }}
            style={{
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              gap: "28px",
              paddingTop: "60px",
            }}
          >
            <RisingSun style={{ width: "70px", height: "auto" }} />

            <h1
              style={{
                fontFamily: FONT,
                fontSize: "28px",
                fontWeight: 600,
                color: "#f0eef4",
                letterSpacing: "-0.02em",
                textAlign: "center",
              }}
            >
              What&apos;s up{userName ? `, ${userName}` : ""}?
            </h1>

            {/* Input */}
            <div style={{ width: "100%" }}>
              <input
                ref={inputRef}
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyDown={(e) => { if (e.key === "Enter") handleSubmit(); }}
                placeholder={`Ask me a question about ${school.name} students.`}
                style={{
                  width: "100%",
                  padding: "18px 24px",
                  fontFamily: FONT,
                  fontSize: "15px",
                  color: "#f0eef4",
                  background: "rgba(255,255,255,0.04)",
                  border: "1px solid rgba(255,255,255,0.10)",
                  borderRadius: "16px",
                  outline: "none",
                  transition: "border-color 0.2s, box-shadow 0.2s",
                }}
                onFocus={(e) => {
                  e.currentTarget.style.borderColor = `${school.brandColorLight}50`;
                  e.currentTarget.style.boxShadow = `0 0 0 3px ${school.brandColorLight}15`;
                }}
                onBlur={(e) => {
                  e.currentTarget.style.borderColor = "rgba(255,255,255,0.10)";
                  e.currentTarget.style.boxShadow = "none";
                }}
              />
            </div>

            {/* Suggestion chips */}
            <div style={{ display: "flex", flexWrap: "wrap", gap: "10px", justifyContent: "center" }}>
              {SUGGESTIONS.map((s) => (
                <button
                  key={s}
                  onClick={() => handleChip(s)}
                  style={{
                    fontFamily: FONT,
                    fontSize: "13px",
                    color: "rgba(255,255,255,0.55)",
                    background: "transparent",
                    border: "1px solid rgba(255,255,255,0.12)",
                    borderRadius: "100px",
                    padding: "8px 18px",
                    cursor: "pointer",
                    transition: "background 0.15s, color 0.15s, border-color 0.15s",
                  }}
                  onMouseEnter={(e) => {
                    (e.currentTarget as HTMLElement).style.background = `${school.brandColorLight}15`;
                    (e.currentTarget as HTMLElement).style.borderColor = `${school.brandColorLight}40`;
                    (e.currentTarget as HTMLElement).style.color = school.brandColorLight;
                  }}
                  onMouseLeave={(e) => {
                    (e.currentTarget as HTMLElement).style.background = "transparent";
                    (e.currentTarget as HTMLElement).style.borderColor = "rgba(255,255,255,0.12)";
                    (e.currentTarget as HTMLElement).style.color = "rgba(255,255,255,0.55)";
                  }}
                >
                  {s}
                </button>
              ))}
            </div>
          </motion.div>
        )}

        {/* ── Results State ── */}
        {showResults && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.3 }}
            style={{ display: "flex", flexDirection: "column", gap: "20px" }}
          >
            {/* Input bar (top) */}
            <div style={{ display: "flex", gap: "10px", alignItems: "center" }}>
              <input
                ref={inputRef}
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyDown={(e) => { if (e.key === "Enter") handleSubmit(); }}
                placeholder={`Ask me a question about ${school.name} students.`}
                style={{
                  flex: 1,
                  padding: "14px 20px",
                  fontFamily: FONT,
                  fontSize: "14px",
                  color: "#f0eef4",
                  background: "rgba(255,255,255,0.04)",
                  border: "1px solid rgba(255,255,255,0.10)",
                  borderRadius: "12px",
                  outline: "none",
                  transition: "border-color 0.2s, box-shadow 0.2s",
                }}
                onFocus={(e) => {
                  e.currentTarget.style.borderColor = `${school.brandColorLight}50`;
                  e.currentTarget.style.boxShadow = `0 0 0 3px ${school.brandColorLight}15`;
                }}
                onBlur={(e) => {
                  e.currentTarget.style.borderColor = "rgba(255,255,255,0.10)";
                  e.currentTarget.style.boxShadow = "none";
                }}
              />
              <button
                onClick={handleReset}
                style={{
                  fontFamily: FONT,
                  fontSize: "12px",
                  color: "rgba(255,255,255,0.4)",
                  background: "none",
                  border: "none",
                  cursor: "pointer",
                  padding: "8px",
                  transition: "color 0.15s",
                }}
                onMouseEnter={(e) => { (e.currentTarget as HTMLElement).style.color = "rgba(255,255,255,0.8)"; }}
                onMouseLeave={(e) => { (e.currentTarget as HTMLElement).style.color = "rgba(255,255,255,0.4)"; }}
              >
                Clear
              </button>
            </div>

            {/* Summary */}
            <p style={{ fontFamily: FONT, fontSize: "14px", color: "rgba(255,255,255,0.5)" }}>
              {results.length.toLocaleString()} student{results.length !== 1 ? "s" : ""} found
            </p>

            {/* Student rows */}
            <div style={{ display: "flex", flexDirection: "column", gap: "2px" }}>
              {results.slice(0, 200).map((student, i) => (
                <div key={student.uuid}>
                  <motion.button
                    initial={{ opacity: 0, y: 6 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.2, delay: Math.min(i * 0.015, 0.3) }}
                    onClick={() => handleExpand(student)}
                    style={{
                      width: "100%",
                      textAlign: "left",
                      display: "grid",
                      gridTemplateColumns: "24px 100px 1fr 90px 70px",
                      padding: "14px 16px",
                      gap: "12px",
                      alignItems: "center",
                      background: expandedUuid === student.uuid ? "rgba(255,255,255,0.06)" : "rgba(255,255,255,0.03)",
                      border: "none",
                      borderBottom: "1px solid rgba(255,255,255,0.05)",
                      cursor: "pointer",
                      transition: "background 0.15s",
                    }}
                    onMouseEnter={(e) => {
                      if (expandedUuid !== student.uuid)
                        (e.currentTarget as HTMLElement).style.background = "rgba(255,255,255,0.05)";
                    }}
                    onMouseLeave={(e) => {
                      if (expandedUuid !== student.uuid)
                        (e.currentTarget as HTMLElement).style.background = "rgba(255,255,255,0.03)";
                    }}
                  >
                    {/* Expand indicator */}
                    <svg
                      width="12" height="12" viewBox="0 0 12 12" fill="none"
                      style={{
                        transform: expandedUuid === student.uuid ? "rotate(90deg)" : "rotate(0deg)",
                        transition: "transform 0.2s",
                      }}
                    >
                      <path d="M4 2l4 4-4 4" stroke="rgba(255,255,255,0.3)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
                    </svg>
                    <span style={{ fontFamily: FONT, fontSize: "13px", fontWeight: 600, color: "rgba(255,255,255,0.8)" }}>
                      #{student.displayNumber}
                    </span>
                    <span style={{ fontFamily: FONT, fontSize: "13px", color: "rgba(255,255,255,0.55)", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                      {student.primaryFocus}
                    </span>
                    <span style={{ fontFamily: FONT, fontSize: "13px", fontWeight: 500, color: "rgba(255,255,255,0.7)" }}>
                      {student.coursesCompleted} courses
                    </span>
                    <span style={{ fontFamily: FONT, fontSize: "13px", fontWeight: 700, color: gpaColor(student.gpa) }}>
                      {student.gpa.toFixed(2)}
                    </span>
                  </motion.button>

                  {/* Expanded detail */}
                  <AnimatePresence>
                    {expandedUuid === student.uuid && (
                      <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: "auto", opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        transition={{ duration: 0.25 }}
                        style={{ overflow: "hidden", background: "rgba(255,255,255,0.02)" }}
                      >
                        <div style={{ padding: "16px 20px 24px" }}>
                          {detailLoading && (
                            <p style={{ fontFamily: FONT, fontSize: "13px", color: "rgba(255,255,255,0.3)" }}>Loading...</p>
                          )}
                          {expandedDetail && expandedDetail.uuid === student.uuid && (
                            <>
                              {/* Tabs */}
                              <div style={{ display: "flex", gap: "0", borderBottom: "1px solid rgba(255,255,255,0.08)", marginBottom: "16px" }}>
                                {(["history", "skills"] as const).map((tab) => (
                                  <button
                                    key={tab}
                                    onClick={(e) => { e.stopPropagation(); setDetailTab(tab); }}
                                    style={{
                                      background: "none",
                                      border: "none",
                                      borderBottom: detailTab === tab ? `2px solid ${school.brandColorLight}` : "2px solid transparent",
                                      cursor: "pointer",
                                      padding: "8px 16px",
                                      fontFamily: FONT,
                                      fontSize: "11px",
                                      fontWeight: 600,
                                      letterSpacing: "0.1em",
                                      textTransform: "uppercase",
                                      color: detailTab === tab ? school.brandColorLight : "rgba(255,255,255,0.35)",
                                      transition: "color 0.15s",
                                      marginBottom: "-1px",
                                    }}
                                  >
                                    {tab === "history" ? "Course History" : "Skill Profile"}
                                  </button>
                                ))}
                              </div>

                              {/* Course History */}
                              {detailTab === "history" && (
                                <div style={{ display: "flex", flexDirection: "column", gap: "2px" }}>
                                  {expandedDetail.enrollments.map((e, ei) => (
                                    <div
                                      key={ei}
                                      style={{
                                        display: "grid",
                                        gridTemplateColumns: "2fr 1fr 50px 80px 80px",
                                        padding: "8px 12px",
                                        gap: "8px",
                                        alignItems: "center",
                                        background: "rgba(255,255,255,0.02)",
                                        borderRadius: "4px",
                                      }}
                                    >
                                      <span style={{ fontFamily: FONT, fontSize: "12px", fontWeight: 500, color: "rgba(255,255,255,0.75)", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                                        {e.courseName}
                                      </span>
                                      <span style={{ fontFamily: FONT, fontSize: "11px", color: "rgba(255,255,255,0.4)", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                                        {e.department}
                                      </span>
                                      <span style={{ fontFamily: FONT, fontSize: "12px", fontWeight: 700, color: GRADE_COLORS[e.grade] ?? "rgba(255,255,255,0.5)" }}>
                                        {e.grade}
                                      </span>
                                      <span style={{ fontFamily: FONT, fontSize: "11px", color: "rgba(255,255,255,0.4)" }}>
                                        {e.term}
                                      </span>
                                      <span style={{ fontFamily: FONT, fontSize: "11px", color: e.status === "Withdrawn" ? "rgba(248,113,113,0.7)" : "rgba(255,255,255,0.4)" }}>
                                        {e.status}
                                      </span>
                                    </div>
                                  ))}
                                </div>
                              )}

                              {/* Skill Profile */}
                              {detailTab === "skills" && (
                                <div style={{ display: "flex", flexWrap: "wrap", gap: "6px" }}>
                                  {expandedDetail.skills.length === 0 ? (
                                    <p style={{ fontFamily: FONT, fontSize: "13px", color: "rgba(255,255,255,0.3)" }}>No skills derived yet.</p>
                                  ) : (
                                    expandedDetail.skills.map((skill) => (
                                      <span
                                        key={skill}
                                        style={{
                                          padding: "5px 12px",
                                          background: "rgba(255,255,255,0.03)",
                                          border: `1px solid ${school.brandColorLight}60`,
                                          borderRadius: "6px",
                                          fontFamily: FONT,
                                          fontSize: "12px",
                                          fontWeight: 500,
                                          color: school.brandColorLight,
                                        }}
                                      >
                                        {skill}
                                      </span>
                                    ))
                                  )}
                                </div>
                              )}
                            </>
                          )}
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </div>
              ))}
              {results.length > 200 && (
                <p style={{ fontFamily: FONT, fontSize: "13px", color: "rgba(255,255,255,0.3)", padding: "16px", textAlign: "center" }}>
                  Showing first 200 of {results.length.toLocaleString()} results. Refine your query to narrow down.
                </p>
              )}
              {results.length === 0 && (
                <p style={{ fontFamily: FONT, fontSize: "14px", color: "rgba(255,255,255,0.35)", padding: "40px 0", textAlign: "center" }}>
                  No students match that query. Try a different question.
                </p>
              )}
            </div>
          </motion.div>
        )}
      </div>
    </>
  );
}
