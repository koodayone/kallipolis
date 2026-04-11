"use client";

import { useState, useCallback, useRef, useMemo } from "react";
import { SchoolConfig } from "@/lib/schoolConfig";
import { getStudents, getStudent, queryStudents } from "@/lib/api";
import type { ApiStudentSummary, ApiStudentDetail } from "@/lib/api";
import type { StudentSummary, StudentDetail } from "@/lib/students/types";
import EntityScrollList from "@/components/ui/EntityScrollList";
import type { Column } from "@/components/ui/EntityScrollList";
import QueryShell, { findScrollParent } from "@/components/ui/QueryShell";
import StudentRow from "@/components/shared/StudentRow";

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
    enrollments: api.enrollments.map((e) => ({ courseCode: e.course_code || "", courseName: e.course_name, department: e.department, grade: e.grade, term: e.term, status: e.status })),
    skills: api.skills,
  };
}

const STUDENT_COLUMNS: Column[] = [
  { label: "Student", width: "110px" },
  { label: "Primary Focus", width: "1fr" },
  { label: "Courses", width: "90px" },
  { label: "GPA", width: "60px" },
];

const EXAMPLES = [
  "Students with the highest GPA",
  "Who has skills aligned with healthcare roles?",
  "Students with the most completed courses",
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
    <StudentRow
      key={student.uuid}
      student={student}
      index={i}
      brandColor={school.brandColorLight}
      isOpen={expandedUuids.has(student.uuid)}
      onToggle={() => handleExpand(student)}
      detail={studentDetails[student.uuid] ?? null}
      isLoading={loadingUuids.has(student.uuid)}
    />
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
      school={school} onBack={onBack}
      placeholder={`Ask me a question about ${school.name} students.`}
      examples={EXAMPLES} queryFn={queryFn} loadInitialData={loadInitialData}
      renderInitialContent={renderInitialContent} renderResultsContent={renderResultsContent}
      onQueryStart={onQueryStart} onReset={onReset} rootRef={rootRef}
    />
  );
}
