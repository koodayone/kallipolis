"use client";

import { useState, useEffect, useCallback } from "react";
import { SchoolConfig } from "@/lib/schoolConfig";
import { getStudents, getStudent } from "@/lib/api";
import type { ApiStudentSummary, ApiStudentDetail } from "@/lib/api";
import type { StudentSummary, StudentDetail } from "@/lib/students/types";
import LeafHeader from "@/components/ui/LeafHeader";

const FONT = "var(--font-inter), Inter, system-ui, sans-serif";

type ViewState = "list" | "detail";
type SortKey = "primaryFocus" | "coursesCompleted" | "gpa";
type SortDir = "asc" | "desc";
type DetailTab = "history" | "skills";

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

type Props = {
  school: SchoolConfig;
  onBack: () => void;
};

export default function StudentsView({ school, onBack }: Props) {
  const [view, setView] = useState<ViewState>("list");
  const [students, setStudents] = useState<StudentSummary[]>([]);
  const [detail, setDetail] = useState<StudentDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [detailLoading, setDetailLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [sortKey, setSortKey] = useState<SortKey>("coursesCompleted");
  const [sortDir, setSortDir] = useState<SortDir>("desc");
  const [detailTab, setDetailTab] = useState<DetailTab>("history");

  useEffect(() => {
    getStudents(school.name)
      .then((data) => setStudents(data.map(mapSummary)))
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  const handleSort = useCallback((key: SortKey) => {
    setSortDir((prev) => (sortKey === key && prev === "desc" ? "asc" : "desc"));
    setSortKey(key);
  }, [sortKey]);

  const handleStudentClick = useCallback(async (student: StudentSummary) => {
    setDetailLoading(true);
    setDetailTab("history");
    try {
      const data = await getStudent(student.uuid, school.name);
      setDetail(mapDetail(data, student.displayNumber));
      setView("detail");
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setDetailLoading(false);
    }
  }, []);

  const sorted = [...students].sort((a, b) => {
    const dir = sortDir === "desc" ? -1 : 1;
    if (sortKey === "primaryFocus") return a.primaryFocus.localeCompare(b.primaryFocus) * dir;
    if (sortKey === "coursesCompleted") return (a.coursesCompleted - b.coursesCompleted) * dir;
    if (sortKey === "gpa") return (a.gpa - b.gpa) * dir;
    return 0;
  });

  return (
    <>
      <LeafHeader school={school} onBack={onBack} parentShape="cube" />
      <div style={{ display: "flex", justifyContent: "center", paddingTop: "32px", paddingBottom: "16px" }}>
        <img src={school.logoPath} alt={school.name} style={{ height: "100px", width: "auto", objectFit: "contain" }} />
      </div>
    <div style={{ maxWidth: "800px", margin: "0 auto", padding: "32px 40px 80px", display: "flex", flexDirection: "column", gap: "32px" }}>
      {/* Internal back (detail → list) */}
      {view === "detail" && (
        <button
          onClick={() => setView("list")}
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
          All Students
        </button>
      )}

      {error && (
        <p style={{ fontFamily: FONT, fontSize: "14px", color: "#e55" }}>{error}</p>
      )}

      {/* ── Level 1: Student List ── */}
      {view === "list" && (
        <>
          <div>
            <h1 style={{ fontFamily: FONT, fontSize: "24px", fontWeight: 600, color: "#f0eef4", letterSpacing: "-0.02em", marginBottom: "8px" }}>
              Students
            </h1>
            <p style={{ fontFamily: FONT, fontSize: "14px", color: "rgba(255,255,255,0.5)", lineHeight: 1.6 }}>
              {students.length.toLocaleString()} anonymous student records. Select a student to view their course history and derived skill profile.
            </p>
          </div>

          {loading ? (
            <p style={{ fontFamily: FONT, fontSize: "14px", color: "rgba(255,255,255,0.4)" }}>Loading...</p>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: "2px" }}>
              {/* Sort header */}
              <div style={{ display: "grid", gridTemplateColumns: "100px 1fr 90px 70px", padding: "10px 20px", gap: "16px", alignItems: "center" }}>
                <span style={{ fontFamily: FONT, fontSize: "11px", fontWeight: 600, letterSpacing: "0.1em", textTransform: "uppercase", color: "rgba(255,255,255,0.3)" }}>
                  Student
                </span>
                {([
                  { key: "primaryFocus" as SortKey, label: "Primary Focus" },
                  { key: "coursesCompleted" as SortKey, label: "Completed" },
                  { key: "gpa" as SortKey, label: "GPA" },
                ]).map((col) => (
                  <button
                    key={col.key}
                    onClick={() => handleSort(col.key)}
                    style={{
                      background: "none", border: "none", cursor: "pointer",
                      padding: 0, fontFamily: FONT, fontSize: "11px", fontWeight: 600,
                      letterSpacing: "0.1em", textTransform: "uppercase",
                      color: sortKey === col.key ? school.brandColorLight : "rgba(255,255,255,0.3)",
                      display: "flex", alignItems: "center", gap: "4px", transition: "color 0.15s",
                    }}
                  >
                    {col.label}
                    {sortKey === col.key && (
                      <span style={{ fontSize: "9px" }}>{sortDir === "desc" ? "▼" : "▲"}</span>
                    )}
                  </button>
                ))}
              </div>

              {/* Rows */}
              {sorted.map((student) => (
                <button
                  key={student.uuid}
                  onClick={() => handleStudentClick(student)}
                  disabled={detailLoading}
                  style={{
                    display: "grid", gridTemplateColumns: "100px 1fr 90px 70px", padding: "14px 20px", gap: "16px", alignItems: "center",
                    background: "rgba(255,255,255,0.04)", border: "1px solid rgba(255,255,255,0.06)",
                    borderRadius: "6px", cursor: "pointer", transition: "background 0.15s",
                    width: "100%", textAlign: "left",
                  }}
                  onMouseEnter={(e) => (e.currentTarget.style.background = "rgba(255,255,255,0.06)")}
                  onMouseLeave={(e) => (e.currentTarget.style.background = "rgba(255,255,255,0.04)")}
                >
                  <span style={{ fontFamily: FONT, fontSize: "14px", fontWeight: 600, color: "rgba(255,255,255,0.85)" }}>
                    Student #{student.displayNumber}
                  </span>
                  <span style={{ fontFamily: FONT, fontSize: "13px", color: "rgba(255,255,255,0.6)", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                    {student.primaryFocus}
                  </span>
                  <span style={{ fontFamily: FONT, fontSize: "14px", fontWeight: 600, color: "rgba(255,255,255,0.8)" }}>
                    {student.coursesCompleted}
                  </span>
                  <span style={{ fontFamily: FONT, fontSize: "14px", fontWeight: 700, color: gpaColor(student.gpa) }}>
                    {student.gpa.toFixed(2)}
                  </span>
                </button>
              ))}
            </div>
          )}
        </>
      )}

      {/* ── Level 2: Student Detail ── */}
      {view === "detail" && detail && (
        <>
          <div>
            <h1 style={{ fontFamily: FONT, fontSize: "24px", fontWeight: 600, color: "#f0eef4", letterSpacing: "-0.02em", marginBottom: "8px" }}>
              Student #{detail.displayNumber}
            </h1>
            <div style={{ display: "flex", gap: "16px", alignItems: "center" }}>
              <span style={{ fontFamily: FONT, fontSize: "13px", color: "rgba(255,255,255,0.5)" }}>
                {detail.primaryFocus}
              </span>
              <span style={{ fontFamily: FONT, fontSize: "13px", color: "rgba(255,255,255,0.5)" }}>
                {detail.coursesCompleted} courses completed
              </span>
              <span style={{ fontFamily: FONT, fontSize: "14px", fontWeight: 700, color: gpaColor(detail.gpa) }}>
                {detail.gpa.toFixed(2)} GPA
              </span>
            </div>
          </div>

          {/* Tabs */}
          <div style={{ display: "flex", gap: "0", borderBottom: "1px solid rgba(255,255,255,0.1)" }}>
            {([
              { key: "history" as DetailTab, label: "Course History" },
              { key: "skills" as DetailTab, label: "Skill Profile" },
            ]).map((tab) => (
              <button
                key={tab.key}
                onClick={() => setDetailTab(tab.key)}
                style={{
                  background: "none", border: "none",
                  borderBottom: detailTab === tab.key ? `2px solid ${school.brandColorLight}` : "2px solid transparent",
                  cursor: "pointer", padding: "12px 20px", fontFamily: FONT, fontSize: "12px",
                  fontWeight: 600, letterSpacing: "0.1em", textTransform: "uppercase",
                  color: detailTab === tab.key ? school.brandColorLight : "rgba(255,255,255,0.4)",
                  transition: "color 0.15s, border-color 0.15s", marginBottom: "-1px",
                }}
              >
                {tab.label}
              </button>
            ))}
          </div>

          {/* Course History */}
          {detailTab === "history" && (
            <div style={{ display: "flex", flexDirection: "column", gap: "2px" }}>
              <div style={{ display: "flex", padding: "10px 20px", gap: "16px" }}>
                {["Course", "Department", "Grade", "Term", "Status"].map((h, i) => (
                  <span key={h} style={{
                    flex: i === 0 ? 2 : 1, fontFamily: FONT, fontSize: "11px", fontWeight: 600,
                    letterSpacing: "0.1em", textTransform: "uppercase", color: "rgba(255,255,255,0.3)",
                  }}>
                    {h}
                  </span>
                ))}
              </div>
              {detail.enrollments.map((e, i) => (
                <div
                  key={i}
                  style={{
                    display: "flex", padding: "12px 20px", gap: "16px", alignItems: "center",
                    background: "rgba(255,255,255,0.04)", border: "1px solid rgba(255,255,255,0.06)",
                    borderRadius: "6px",
                  }}
                >
                  <span style={{ flex: 2, fontFamily: FONT, fontSize: "13px", fontWeight: 500, color: "rgba(255,255,255,0.85)" }}>
                    {e.courseName}
                  </span>
                  <span style={{ flex: 1, fontFamily: FONT, fontSize: "12px", color: "rgba(255,255,255,0.5)" }}>
                    {e.department}
                  </span>
                  <span style={{ flex: 1, fontFamily: FONT, fontSize: "13px", fontWeight: 700, color: GRADE_COLORS[e.grade] ?? "rgba(255,255,255,0.6)" }}>
                    {e.grade}
                  </span>
                  <span style={{ flex: 1, fontFamily: FONT, fontSize: "12px", color: "rgba(255,255,255,0.5)" }}>
                    {e.term}
                  </span>
                  <span style={{ flex: 1, fontFamily: FONT, fontSize: "12px", color: e.status === "Withdrawn" ? "rgba(248,113,113,0.7)" : "rgba(255,255,255,0.5)" }}>
                    {e.status}
                  </span>
                </div>
              ))}
            </div>
          )}

          {/* Skill Profile */}
          {detailTab === "skills" && (
            <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
              <p style={{ fontFamily: FONT, fontSize: "13px", color: "rgba(255,255,255,0.45)", lineHeight: 1.6, marginBottom: "8px" }}>
                Skills derived from completed coursework and mapped learning outcomes.
              </p>
              {detail.skills.length === 0 ? (
                <p style={{ fontFamily: FONT, fontSize: "14px", color: "rgba(255,255,255,0.35)" }}>
                  No skills derived yet.
                </p>
              ) : (
                <div style={{ display: "flex", flexWrap: "wrap", gap: "8px" }}>
                  {detail.skills.map((skill) => (
                    <span
                      key={skill}
                      style={{
                        padding: "8px 16px",
                        background: "rgba(255,255,255,0.04)",
                        border: `1px solid ${school.brandColorLight}`,
                        borderRadius: "6px",
                        fontFamily: FONT,
                        fontSize: "13px",
                        fontWeight: 500,
                        color: school.brandColorLight,
                      }}
                    >
                      {skill}
                    </span>
                  ))}
                </div>
              )}
            </div>
          )}
        </>
      )}
    </div>
    </>
  );
}
