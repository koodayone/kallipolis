"use client";

import { useState, useEffect, useCallback, useRef, memo, useMemo } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { SchoolConfig } from "@/lib/schoolConfig";
import { getStudents, getStudent, queryStudents } from "@/lib/api";
import type { ApiStudentSummary, ApiStudentDetail } from "@/lib/api";
import type { StudentSummary, StudentDetail } from "@/lib/students/types";
import EntityScrollList from "@/components/ui/EntityScrollList";
import type { Column } from "@/components/ui/EntityScrollList";
import QueryShell, { findScrollParent } from "@/components/ui/QueryShell";

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

const STUDENT_COLUMNS: Column[] = [
  { label: "Student", width: "110px" },
  { label: "Primary Focus", width: "1fr" },
  { label: "Courses", width: "90px" },
  { label: "GPA", width: "60px" },
];

const SUGGESTIONS = [
  "Students with highest GPA",
  "Computer Science students",
  "Who has Programming skills?",
  "Students with more than 15 courses",
  "Biology students with GPA above 3.0",
];

type Props = { school: SchoolConfig; onBack: () => void };

export default function StudentsView({ school, onBack }: Props) {
  const rootRef = useRef<HTMLDivElement>(null);
  const [students, setStudents] = useState<StudentSummary[]>([]);
  const [expandedUuids, setExpandedUuids] = useState<Set<string>>(new Set());
  const [studentDetails, setStudentDetails] = useState<Record<string, StudentDetail>>({});
  const [loadingUuids, setLoadingUuids] = useState<Set<string>>(new Set());

  const defaultStudents = useMemo(
    () => [...students].sort((a, b) => b.coursesCompleted - a.coursesCompleted),
    [students],
  );

  const loadInitialData = useCallback(async () => {
    const data = await getStudents(school.name);
    setStudents(data.map(mapSummary));
  }, [school.name]);

  const queryFn = useCallback(async (query: string, college: string) => {
    const resp = await queryStudents(query, college);
    return { items: resp.students.map(mapSummary), message: resp.message };
  }, []);

  const onQueryStart = useCallback(() => { setExpandedUuids(new Set()); }, []);
  const onReset = useCallback(() => { setExpandedUuids(new Set()); }, []);

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

  const renderStudentRow = useCallback((student: StudentSummary, i: number) => (
    <StudentRow student={student} i={i} school={school}
      expandedUuids={expandedUuids} studentDetails={studentDetails}
      loadingUuids={loadingUuids} onExpand={handleExpand} />
  ), [school, expandedUuids, studentDetails, loadingUuids, handleExpand]);

  const studentKeyExtractor = useCallback((s: StudentSummary) => s.uuid, []);

  const renderInitialContent = useCallback(() => (
    <div style={{ marginTop: "16px" }}>
      <p style={{ fontFamily: FONT, fontSize: "13px", color: "rgba(255,255,255,0.35)", marginBottom: "12px" }}>
        {students.length.toLocaleString()} students
      </p>
      <EntityScrollList
        items={defaultStudents} initialCap={100} batchSize={100}
        columns={STUDENT_COLUMNS} renderRow={renderStudentRow}
        keyExtractor={studentKeyExtractor} entityName="students" school={school}
      />
    </div>
  ), [students.length, defaultStudents, renderStudentRow, studentKeyExtractor, school]);

  const renderResultsContent = useCallback((results: StudentSummary[]) => (
    <EntityScrollList
      items={results} initialCap={200} batchSize={100}
      columns={STUDENT_COLUMNS} renderRow={renderStudentRow}
      keyExtractor={studentKeyExtractor} entityName="students" school={school}
    />
  ), [renderStudentRow, studentKeyExtractor, school]);

  return (
    <QueryShell<StudentSummary>
      school={school} onBack={onBack} parentShape="cube"
      placeholder={`Ask me a question about ${school.name} students.`}
      suggestions={SUGGESTIONS} queryFn={queryFn} loadInitialData={loadInitialData}
      renderInitialContent={renderInitialContent} renderResultsContent={renderResultsContent}
      onQueryStart={onQueryStart} onReset={onReset} rootRef={rootRef}
    />
  );
}

/* ── Student Row ───────────────────────────────────────────────────────── */

const StudentRow = memo(function StudentRow({ student, i, school, expandedUuids, studentDetails, loadingUuids, onExpand }: {
  student: StudentSummary; i: number; school: SchoolConfig;
  expandedUuids: Set<string>; studentDetails: Record<string, StudentDetail>;
  loadingUuids: Set<string>; onExpand: (student: StudentSummary) => void;
}) {
  const isOpen = expandedUuids.has(student.uuid);
  const detail = studentDetails[student.uuid];
  const isLoading = loadingUuids.has(student.uuid);
  const [tab, setTab] = useState<"history" | "skills">("history");
  const hasMounted = useRef(false);
  useEffect(() => { hasMounted.current = true; }, []);
  return (
    <div>
      <motion.button
        initial={hasMounted.current ? false : { opacity: 0, y: 6 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.2, delay: hasMounted.current ? 0 : Math.min(i * 0.01, 0.2) }}
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
                      <button key={t} onClick={(e) => { e.stopPropagation(); setTab(t); }}
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
});
