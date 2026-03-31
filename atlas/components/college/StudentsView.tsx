"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { SchoolConfig } from "@/lib/schoolConfig";
import { getStudents, getStudent, queryStudents } from "@/lib/api";
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
  return { uuid: api.uuid, displayNumber: index + 1, primaryFocus: api.primary_focus, coursesCompleted: api.courses_completed, gpa: api.gpa };
}

function mapDetail(api: ApiStudentDetail, displayNumber: number): StudentDetail {
  return {
    uuid: api.uuid, displayNumber, primaryFocus: api.primary_focus,
    coursesCompleted: api.courses_completed, gpa: api.gpa,
    enrollments: api.enrollments.map((e) => ({ courseName: e.course_name, department: e.department, grade: e.grade, term: e.term, status: e.status })),
    skills: api.skills,
  };
}

const SUGGESTIONS = [
  "Students with highest GPA",
  "Computer Science students",
  "Who has Programming skills?",
  "Students with more than 15 courses",
  "Biology students with GPA above 3.0",
];

/* ── Student List (shared between initial and results state) ────────────── */

function StudentList({
  students, cap, school, expandedUuids, studentDetails, loadingUuids, onExpand,
}: {
  students: StudentSummary[];
  cap: number;
  school: SchoolConfig;
  expandedUuids: Set<string>;
  studentDetails: Record<string, StudentDetail>;
  loadingUuids: Set<string>;
  onExpand: (student: StudentSummary) => void;
}) {
  const [tabState, setTabState] = useState<Record<string, "history" | "skills">>({});
  const visible = students.slice(0, cap);

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "2px" }}>
      {/* Column headers */}
      <div style={{
        display: "grid", gridTemplateColumns: "24px 110px 1fr 90px 60px",
        padding: "8px 16px", gap: "10px", alignItems: "center",
      }}>
        <span />
        <span style={{ fontFamily: FONT, fontSize: "10px", fontWeight: 600, letterSpacing: "0.1em", textTransform: "uppercase", color: school.brandColorLight, opacity: 0.6 }}>Student</span>
        <span style={{ fontFamily: FONT, fontSize: "10px", fontWeight: 600, letterSpacing: "0.1em", textTransform: "uppercase", color: school.brandColorLight, opacity: 0.6 }}>Primary Focus</span>
        <span style={{ fontFamily: FONT, fontSize: "10px", fontWeight: 600, letterSpacing: "0.1em", textTransform: "uppercase", color: school.brandColorLight, opacity: 0.6 }}>Courses</span>
        <span style={{ fontFamily: FONT, fontSize: "10px", fontWeight: 600, letterSpacing: "0.1em", textTransform: "uppercase", color: school.brandColorLight, opacity: 0.6 }}>GPA</span>
      </div>
      {visible.map((student, i) => {
        const isOpen = expandedUuids.has(student.uuid);
        const detail = studentDetails[student.uuid];
        const isLoading = loadingUuids.has(student.uuid);
        const tab = tabState[student.uuid] || "history";
        return (
        <div key={student.uuid}>
          <motion.button
            initial={{ opacity: 0, y: 6 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.2, delay: Math.min(i * 0.01, 0.2) }}
            onClick={() => onExpand(student)}
            style={{
              width: "100%", textAlign: "left",
              display: "grid", gridTemplateColumns: "24px 110px 1fr 90px 60px",
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
            <span style={{ fontFamily: FONT, fontSize: "13px", fontWeight: 600, color: "rgba(255,255,255,0.8)" }}>Student #{student.displayNumber}</span>
            <span style={{ fontFamily: FONT, fontSize: "13px", color: "rgba(255,255,255,0.55)", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{student.primaryFocus}</span>
            <span style={{ fontFamily: FONT, fontSize: "12px", fontWeight: 500, color: "rgba(255,255,255,0.6)" }}>{student.coursesCompleted} courses</span>
            <span style={{ fontFamily: FONT, fontSize: "13px", fontWeight: 700, color: gpaColor(student.gpa) }}>{student.gpa.toFixed(2)}</span>
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
                <div style={{ padding: "16px 20px 24px" }}>
                  {isLoading && <p style={{ fontFamily: FONT, fontSize: "13px", color: "rgba(255,255,255,0.3)" }}>Loading...</p>}
                  {detail && (
                    <>
                      <div style={{ display: "flex", gap: "0", borderBottom: "1px solid rgba(255,255,255,0.08)", marginBottom: "16px" }}>
                        {(["history", "skills"] as const).map((t) => (
                          <button key={t} onClick={(e) => { e.stopPropagation(); setTabState((prev) => ({ ...prev, [student.uuid]: t })); }}
                            style={{
                              background: "none", border: "none",
                              borderBottom: tab === t ? `2px solid ${school.brandColorLight}` : "2px solid transparent",
                              cursor: "pointer", padding: "8px 16px", fontFamily: FONT, fontSize: "11px",
                              fontWeight: 600, letterSpacing: "0.1em", textTransform: "uppercase",
                              color: tab === t ? school.brandColorLight : "rgba(255,255,255,0.35)",
                              transition: "color 0.15s", marginBottom: "-1px",
                            }}>
                            {t === "history" ? "Course History" : "Skill Profile"}
                          </button>
                        ))}
                      </div>
                      {tab === "history" && (
                        <div style={{ display: "flex", flexDirection: "column", gap: "2px" }}>
                          {detail.enrollments.map((e, ei) => (
                            <div key={ei} style={{
                              display: "grid", gridTemplateColumns: "2fr 1fr 50px 80px 80px",
                              padding: "8px 12px", gap: "8px", alignItems: "center",
                              background: "rgba(255,255,255,0.02)", borderRadius: "4px",
                            }}>
                              <span style={{ fontFamily: FONT, fontSize: "12px", fontWeight: 500, color: "rgba(255,255,255,0.75)", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{e.courseName}</span>
                              <span style={{ fontFamily: FONT, fontSize: "11px", color: "rgba(255,255,255,0.4)", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{e.department}</span>
                              <span style={{ fontFamily: FONT, fontSize: "12px", fontWeight: 700, color: GRADE_COLORS[e.grade] ?? "rgba(255,255,255,0.5)" }}>{e.grade}</span>
                              <span style={{ fontFamily: FONT, fontSize: "11px", color: "rgba(255,255,255,0.4)" }}>{e.term}</span>
                              <span style={{ fontFamily: FONT, fontSize: "11px", color: e.status === "Withdrawn" ? "rgba(248,113,113,0.7)" : "rgba(255,255,255,0.4)" }}>{e.status}</span>
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
                              border: `1px solid ${school.brandColorLight}60`, borderRadius: "6px",
                              fontFamily: FONT, fontSize: "12px", fontWeight: 500, color: school.brandColorLight,
                            }}>{skill}</span>
                          ))}
                        </div>
                      )}
                    </>
                  )}
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
        );
      })}
      {students.length > cap && (
        <p style={{ fontFamily: FONT, fontSize: "12px", color: "rgba(255,255,255,0.25)", padding: "14px", textAlign: "center" }}>
          Showing {cap} of {students.length.toLocaleString()} students. {students.length > cap ? "Ask a question to narrow down." : ""}
        </p>
      )}
      {students.length === 0 && (
        <p style={{ fontFamily: FONT, fontSize: "14px", color: "rgba(255,255,255,0.35)", padding: "40px 0", textAlign: "center" }}>
          No students match that query. Try a different question.
        </p>
      )}
    </div>
  );
}

/* ── Main Component ─────────────────────────────────────────────────────── */

function findScrollParent(el: HTMLElement | null): HTMLElement | null {
  while (el) {
    if (el.scrollHeight > el.clientHeight && getComputedStyle(el).overflowY !== "visible") return el;
    el = el.parentElement;
  }
  return null;
}

type Props = { school: SchoolConfig; onBack: () => void };

export default function StudentsView({ school, onBack }: Props) {
  const [students, setStudents] = useState<StudentSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [userName, setUserName] = useState<string>("");
  const [query, setQuery] = useState("");
  const [submitted, setSubmitted] = useState(false);
  const [results, setResults] = useState<StudentSummary[]>([]);
  const [queryLoading, setQueryLoading] = useState(false);
  const [queryMessage, setQueryMessage] = useState<string | null>(null);
  const [expandedUuids, setExpandedUuids] = useState<Set<string>>(new Set());
  const [studentDetails, setStudentDetails] = useState<Record<string, StudentDetail>>({});
  const [loadingUuids, setLoadingUuids] = useState<Set<string>>(new Set());
  const inputRef = useRef<HTMLInputElement>(null);
  const rootRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    getStudents(school.name)
      .then((data) => setStudents(data.map(mapSummary)))
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
    fetch("/api/auth/me")
      .then((r) => r.json())
      .then((data) => { if (data?.user?.name) setUserName(data.user.name.split(" ")[0]); })
      .catch(() => {});
  }, []);

  const handleSubmit = useCallback(async () => {
    if (!query.trim()) return;
    setQueryLoading(true);
    setSubmitted(true);
    setExpandedUuids(new Set());
    setQueryMessage(null);
    try {
      const resp = await queryStudents(query, school.name);
      setResults(resp.students.map(mapSummary));
      setQueryMessage(resp.message);
    } catch {
      setResults([]);
      setQueryMessage("Something went wrong. Try rephrasing your question.");
    } finally {
      setQueryLoading(false);
    }
  }, [query, school.name]);

  const handleChip = useCallback(async (text: string) => {
    setQuery(text);
    setQueryLoading(true);
    setSubmitted(true);
    setExpandedUuids(new Set());
    setQueryMessage(null);
    try {
      const resp = await queryStudents(text, school.name);
      setResults(resp.students.map(mapSummary));
      setQueryMessage(resp.message);
    } catch {
      setResults([]);
      setQueryMessage("Something went wrong. Try rephrasing your question.");
    } finally {
      setQueryLoading(false);
    }
  }, [school.name]);

  const handleExpand = useCallback(async (student: StudentSummary) => {
    const scrollEl = findScrollParent(rootRef.current);
    const savedScroll = scrollEl?.scrollTop ?? 0;
    const restoreScroll = () => requestAnimationFrame(() => { if (scrollEl) scrollEl.scrollTop = savedScroll; });

    const uuid = student.uuid;
    if (expandedUuids.has(uuid)) {
      setExpandedUuids((prev) => { const next = new Set(prev); next.delete(uuid); return next; });
      restoreScroll();
      return;
    }
    setExpandedUuids((prev) => new Set(prev).add(uuid));
    restoreScroll();
    if (!studentDetails[uuid]) {
      setLoadingUuids((prev) => new Set(prev).add(uuid));
      try {
        const data = await getStudent(uuid, school.name);
        setStudentDetails((prev) => ({ ...prev, [uuid]: mapDetail(data, student.displayNumber) }));
      } catch {}
      finally { setLoadingUuids((prev) => { const next = new Set(prev); next.delete(uuid); return next; }); }
    }
  }, [expandedUuids, studentDetails, school.name]);

  const handleReset = useCallback(() => {
    setQuery(""); setSubmitted(false); setResults([]);
    setExpandedUuids(new Set());
    setTimeout(() => inputRef.current?.focus(), 100);
  }, []);

  // Default sort: courses completed descending
  const defaultStudents = [...students].sort((a, b) => b.coursesCompleted - a.coursesCompleted);

  return (
    <div ref={rootRef}>
      <LeafHeader school={school} onBack={onBack} parentShape="cube" />
      <div style={{ maxWidth: "760px", margin: "0 auto", padding: "32px 40px 80px" }}>
        {error && <p style={{ fontFamily: FONT, fontSize: "14px", color: "#e55", textAlign: "center", paddingTop: "40px" }}>{error}</p>}
        {loading && (
          <div style={{ display: "flex", justifyContent: "center", paddingTop: "80px" }}>
            <RisingSun style={{ width: "90px", height: "auto", opacity: 0.4 }} />
          </div>
        )}

        {/* ── Initial State ── */}
        {!submitted && !loading && (
          <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.4 }}
            style={{ display: "flex", flexDirection: "column", gap: "24px" }}>

            {/* Chat greeting */}
            <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: "24px", paddingTop: "40px" }}>
              <RisingSun style={{ width: "90px", height: "auto" }} />
              <h1 style={{ fontFamily: FONT, fontSize: "28px", fontWeight: 600, color: "#f0eef4", letterSpacing: "-0.02em", textAlign: "center" }}>
                What&apos;s up{userName ? `, ${userName}` : ""}?
              </h1>
              <div style={{ width: "100%" }}>
                <input ref={inputRef} type="text" value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  onKeyDown={(e) => { if (e.key === "Enter") handleSubmit(); }}
                  placeholder={`Ask me a question about ${school.name} students.`}
                  style={{
                    width: "100%", padding: "18px 24px", fontFamily: FONT, fontSize: "15px",
                    color: "#f0eef4", background: "rgba(255,255,255,0.04)",
                    border: "1px solid rgba(255,255,255,0.10)", borderRadius: "16px",
                    outline: "none", transition: "border-color 0.2s, box-shadow 0.2s",
                  }}
                  onFocus={(e) => { e.currentTarget.style.borderColor = `${school.brandColorLight}35`; e.currentTarget.style.boxShadow = `0 0 0 3px ${school.brandColorLight}15`; }}
                  onBlur={(e) => { e.currentTarget.style.borderColor = "rgba(255,255,255,0.10)"; e.currentTarget.style.boxShadow = "none"; }}
                />
              </div>
              <div style={{ display: "flex", flexWrap: "wrap", gap: "10px", justifyContent: "center" }}>
                {SUGGESTIONS.map((s) => (
                  <button key={s} onClick={() => handleChip(s)}
                    style={{
                      fontFamily: FONT, fontSize: "13px", color: "rgba(255,255,255,0.55)",
                      background: "transparent", border: `1px solid ${school.brandColorLight}35`,
                      borderRadius: "100px", padding: "8px 18px", cursor: "pointer",
                      transition: "background 0.15s, color 0.15s, border-color 0.15s",
                    }}
                    onMouseEnter={(e) => { const el = e.currentTarget as HTMLElement; el.style.background = `${school.brandColorLight}15`; el.style.borderColor = `${school.brandColorLight}40`; el.style.color = school.brandColorLight; }}
                    onMouseLeave={(e) => { const el = e.currentTarget as HTMLElement; el.style.background = "transparent"; el.style.borderColor = `${school.brandColorLight}35`; el.style.color = "rgba(255,255,255,0.55)"; }}
                  >{s}</button>
                ))}
              </div>
            </div>

            {/* Student list (browsable) */}
            <div style={{ marginTop: "16px" }}>
              <p style={{ fontFamily: FONT, fontSize: "13px", color: "rgba(255,255,255,0.35)", marginBottom: "12px" }}>
                {students.length.toLocaleString()} students
              </p>
              <StudentList
                students={defaultStudents} cap={100} school={school}
                expandedUuids={expandedUuids} studentDetails={studentDetails}
                loadingUuids={loadingUuids}
                onExpand={handleExpand}
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
                placeholder={`Ask me a question about ${school.name} students.`}
                style={{
                  flex: 1, padding: "14px 20px", fontFamily: FONT, fontSize: "14px",
                  color: "#f0eef4", background: "rgba(255,255,255,0.04)",
                  border: "1px solid rgba(255,255,255,0.10)", borderRadius: "12px",
                  outline: "none", transition: "border-color 0.2s, box-shadow 0.2s",
                }}
                onFocus={(e) => { e.currentTarget.style.borderColor = `${school.brandColorLight}35`; e.currentTarget.style.boxShadow = `0 0 0 3px ${school.brandColorLight}15`; }}
                onBlur={(e) => { e.currentTarget.style.borderColor = "rgba(255,255,255,0.10)"; e.currentTarget.style.boxShadow = "none"; }}
              />
              <button onClick={handleReset}
                style={{ fontFamily: FONT, fontSize: "12px", color: "rgba(255,255,255,0.4)", background: "none", border: "none", cursor: "pointer", padding: "8px", transition: "color 0.15s" }}
                onMouseEnter={(e) => { (e.currentTarget as HTMLElement).style.color = "rgba(255,255,255,0.8)"; }}
                onMouseLeave={(e) => { (e.currentTarget as HTMLElement).style.color = "rgba(255,255,255,0.4)"; }}
              >Clear</button>
            </div>

            {queryLoading && (
              <div style={{ display: "flex", justifyContent: "center", paddingTop: "40px" }}>
                <RisingSun style={{ width: "64px", height: "auto", opacity: 0.4 }} />
              </div>
            )}

            {!queryLoading && queryMessage && (
              <p style={{ fontFamily: FONT, fontSize: "14px", color: "rgba(255,255,255,0.5)" }}>
                {queryMessage}
              </p>
            )}

            {!queryLoading && (
              <StudentList
                students={results} cap={200} school={school}
                expandedUuids={expandedUuids} studentDetails={studentDetails}
                loadingUuids={loadingUuids}
                onExpand={handleExpand}
              />
            )}
          </motion.div>
        )}
      </div>
    </div>
  );
}
