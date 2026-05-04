"use client";

import { useState, useCallback, useRef, useMemo } from "react";
import { SchoolConfig } from "@/config/schoolConfig";
import { getStudents, getStudent, queryStudents } from "@/college-atlas/students/api";
import type { ApiStudentSummary, ApiStudentDetail } from "@/college-atlas/students/api";
import type { StudentSummary, StudentDetail } from "@/college-atlas/students/types";
import EntityScrollList from "@/ui/EntityScrollList";
import type { Column } from "@/ui/EntityScrollList";
import QueryShell, { findScrollParent } from "@/ui/QueryShell";
import StudentRow from "@/college-atlas/students/StudentRow";

const FONT = "var(--font-inter), Inter, system-ui, sans-serif";

function mapSummary(api: ApiStudentSummary, index: number): StudentSummary {
  return { uuid: api.uuid, displayNumber: index + 1, primaryFocus: api.primary_focus, coursesCompleted: api.courses_completed, gpa: api.gpa };
}

function mapDetail(api: ApiStudentDetail, displayNumber: number): StudentDetail {
  return {
    uuid: api.uuid, displayNumber, primaryFocus: api.primary_focus,
    coursesCompleted: api.courses_completed, gpa: api.gpa,
    enrollments: api.enrollments.map((e) => ({ courseCode: e.course_code || "", courseName: e.course_name, department: e.department, grade: e.grade, term: e.term, status: e.status })),
    occupationAlignment: api.occupation_alignment.map((a) => ({
      socCode: a.soc_code,
      title: a.title,
      matchedCourseCount: a.matched_course_count,
      matchedTopGroups: a.matched_top_groups.map((g) => ({
        topCode: g.top_code,
        topTitle: g.top_title,
        courses: g.courses.map((c) => ({ code: c.code, name: c.name })),
      })),
    })),
  };
}

const STUDENT_COLUMNS: Column[] = [
  { label: "Student", width: "110px" },
  { label: "Primary Focus", width: "1fr" },
  { label: "Courses", width: "90px" },
  { label: "GPA", width: "60px" },
];

// Per-college CTE-leaning primary_focus value substituted into the
// "specializing in X" examples. The student table's most prominent
// column IS Primary Focus, so anchoring example queries on it gives the
// user a query whose subject they can already see in the result set.
// Each value is a real, populated program at that school — guaranteeing
// non-zero results. Map mirrors the eval's PER_COLLEGE_OVERRIDES in
// backend/tests/integration/test_example_queries.py.
const FOCUS_BY_COLLEGE: Record<string, string> = {
  "Shasta College": "early childhood education",
  "Foothill College": "accounting",
  "College of the Sequoias": "child development",
  "Oxnard College": "fire technology",
  "Compton College": "nursing",
  "Irvine Valley College": "accounting",
  "College of the Desert": "health sciences",
  "San Diego City College": "cybersecurity and data analytics",
};

const FOCUS_DEFAULT = "construction technology";

// Example queries shown as suggestions. All four lean on the visible
// columns of the student table (Primary Focus, GPA, Courses) and avoid
// skill filters, which are detail-pane-only and have sparser per-school
// coverage that produced empty results in earlier iterations. Slots 1
// and 3 substitute a per-college CTE-flavored primary_focus value, but
// use different surface phrasings ("specializing in X" vs "with primary
// focus X") to teach users two synonyms — the column-name form nudges
// toward referencing the actual table header. Slots 2 and 4 are numeric
// thresholds, universal across schools. Quoted slots are substitutable.
function buildExamples(schoolName: string): string[] {
  const focus = FOCUS_BY_COLLEGE[schoolName] ?? FOCUS_DEFAULT;
  return [
    `Students specializing in '${focus}'`,
    "Students with GPA above 3.5",
    `Students with primary focus '${focus}' and GPA above 3.5`,
    "Students who completed more than 20 courses",
  ];
}

type Props = { school: SchoolConfig; onBack: () => void };

export default function StudentsView({ school, onBack }: Props) {
  const rootRef = useRef<HTMLDivElement>(null);
  const [students, setStudents] = useState<StudentSummary[]>([]);
  const [totalCount, setTotalCount] = useState<number>(0);
  const [expandedUuids, setExpandedUuids] = useState<Set<string>>(new Set());
  const [studentDetails, setStudentDetails] = useState<Record<string, StudentDetail>>({});
  const [loadingUuids, setLoadingUuids] = useState<Set<string>>(new Set());

  const defaultStudents = useMemo(
    () => [...students].sort((a, b) => b.coursesCompleted - a.coursesCompleted),
    [students],
  );

  const loadInitialData = useCallback(async () => {
    const page = await getStudents(school.name);
    setStudents(page.students.map(mapSummary));
    setTotalCount(page.total_count);
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

  const renderInitialContent = useCallback(() => {
    const showingPartial = totalCount > students.length;
    const countText = showingPartial
      ? `Showing top ${students.length.toLocaleString()} of ${totalCount.toLocaleString()} students by courses completed`
      : `${totalCount.toLocaleString()} students`;
    return (
      <div style={{ marginTop: "16px" }}>
        <p style={{ fontFamily: FONT, fontSize: "13px", color: "rgba(255,255,255,0.35)", marginBottom: "12px" }}>
          {countText}
        </p>
        <EntityScrollList
          items={defaultStudents} initialCap={100} batchSize={100}
          columns={STUDENT_COLUMNS} renderRow={renderStudentRow}
          keyExtractor={studentKeyExtractor} entityName="students" school={school}
        />
      </div>
    );
  }, [students.length, totalCount, defaultStudents, renderStudentRow, studentKeyExtractor, school]);

  const renderSearchContent = useCallback((q: string) => {
    const lower = q.toLowerCase();
    const filtered = defaultStudents.filter(s =>
      s.primaryFocus.toLowerCase().includes(lower)
    );
    if (filtered.length === 0) {
      return (
        <p style={{ fontFamily: FONT, fontSize: "14px", color: "rgba(255,255,255,0.35)", padding: "40px 0", textAlign: "center" }}>
          No results found.
        </p>
      );
    }
    return (
      <div style={{ marginTop: "16px" }}>
        <p style={{ fontFamily: FONT, fontSize: "13px", color: "rgba(255,255,255,0.35)", marginBottom: "12px" }}>
          {filtered.length.toLocaleString()} student{filtered.length !== 1 ? "s" : ""}
        </p>
        <EntityScrollList
          items={filtered} initialCap={100} batchSize={100}
          columns={STUDENT_COLUMNS} renderRow={renderStudentRow}
          keyExtractor={studentKeyExtractor} entityName="students" school={school}
        />
      </div>
    );
  }, [defaultStudents, renderStudentRow, studentKeyExtractor, school]);

  const renderResultsContent = useCallback((results: StudentSummary[]) => (
    <EntityScrollList
      items={results} initialCap={200} batchSize={100}
      columns={STUDENT_COLUMNS} renderRow={renderStudentRow}
      keyExtractor={studentKeyExtractor} entityName="students" school={school}
    />
  ), [renderStudentRow, studentKeyExtractor, school]);

  return (
    <QueryShell<StudentSummary>
      school={school} formName="Students" onBack={onBack}
      placeholder={`Ask me a question about ${school.name} students.`}
      examples={buildExamples(school.name)} queryFn={queryFn} loadInitialData={loadInitialData}
      renderInitialContent={renderInitialContent} renderResultsContent={renderResultsContent}
      renderSearchContent={renderSearchContent}
      onQueryStart={onQueryStart} onReset={onReset} rootRef={rootRef}
    />
  );
}
