"use client";

import { useState, useEffect, useCallback, useRef, memo } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { SchoolConfig } from "@/lib/schoolConfig";
import { getDepartments, getCourses, queryCourses } from "@/lib/api";
import type { ApiDepartmentSummary, ApiCourseSummary } from "@/lib/api";
import type { DepartmentSummary, CourseSummary } from "@/lib/curricula/types";
import EntityScrollList from "@/components/ui/EntityScrollList";
import type { Column } from "@/components/ui/EntityScrollList";
import QueryShell, { findScrollParent } from "@/components/ui/QueryShell";
import DepartmentRow from "@/components/shared/DepartmentRow";
import ColumnHeaders from "@/components/shared/ColumnHeaders";

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

const COURSE_COLUMNS: Column[] = [
  { label: "Code", width: "auto" },
  { label: "Name", width: "1fr" },
];

const EXAMPLES = [
  "Courses that develop the most in-demand skills",
  "Transferable courses in our largest departments",
  "What courses build Critical Thinking skills?",
];

type Props = { school: SchoolConfig; onBack: () => void };

export default function CoursesView({ school, onBack }: Props) {
  const rootRef = useRef<HTMLDivElement>(null);
  const [departments, setDepartments] = useState<DepartmentSummary[]>([]);
  const [expandedDepts, setExpandedDepts] = useState<Set<string>>(new Set());
  const [deptCoursesMap, setDeptCoursesMap] = useState<Record<string, CourseSummary[]>>({});
  const [loadingDepts, setLoadingDepts] = useState<Set<string>>(new Set());
  const [expandedCourses, setExpandedCourses] = useState<Set<string>>(new Set());

  const loadInitialData = useCallback(async () => {
    const data = await getDepartments(school.name);
    setDepartments(data.map(mapDept).sort((a, b) => a.department.localeCompare(b.department)));
  }, [school.name]);

  const queryFn = useCallback(async (query: string, college: string) => {
    const resp = await queryCourses(query, college);
    return { items: resp.courses.map(mapCourse), message: resp.message };
  }, []);

  const onQueryStart = useCallback(() => { setExpandedCourses(new Set()); }, []);
  const onReset = useCallback(() => {
    setExpandedDepts(new Set());
    setExpandedCourses(new Set());
  }, []);

  const preserveScroll = useCallback(() => {
    const scrollEl = findScrollParent(rootRef.current);
    const saved = scrollEl?.scrollTop ?? 0;
    requestAnimationFrame(() => { if (scrollEl) scrollEl.scrollTop = saved; });
  }, []);

  const handleDeptExpand = useCallback(async (dept: string) => {
    preserveScroll();
    if (expandedDepts.has(dept)) {
      setExpandedDepts((prev) => { const next = new Set(prev); next.delete(dept); return next; });
      return;
    }
    setExpandedDepts((prev) => new Set(prev).add(dept));
    if (!deptCoursesMap[dept]) {
      setLoadingDepts((prev) => new Set(prev).add(dept));
      try {
        const data = await getCourses(dept, school.name);
        setDeptCoursesMap((prev) => ({
          ...prev,
          [dept]: data.map(mapCourse).sort((a, b) => {
            const numA = parseInt((a.code.match(/(\d+)/) || ["0"])[0]);
            const numB = parseInt((b.code.match(/(\d+)/) || ["0"])[0]);
            return numA - numB || a.code.localeCompare(b.code);
          }),
        }));
      } catch {}
      finally { setLoadingDepts((prev) => { const next = new Set(prev); next.delete(dept); return next; }); }
    }
  }, [expandedDepts, deptCoursesMap, school.name, preserveScroll]);

  const toggleCourse = useCallback((code: string) => {
    preserveScroll();
    setExpandedCourses((prev) => { const next = new Set(prev); if (next.has(code)) next.delete(code); else next.add(code); return next; });
  }, [preserveScroll]);

  const totalCourses = departments.reduce((sum, d) => sum + d.courseCount, 0);

  const renderCourseRow = useCallback((course: CourseSummary, i: number) => (
    <CourseResultRow course={course} i={i} school={school}
      expandedCourses={expandedCourses} onToggle={toggleCourse} />
  ), [school, expandedCourses, toggleCourse]);

  const courseKeyExtractor = useCallback((c: CourseSummary) => c.code, []);

  const renderInitialContent = useCallback(() => (
    <div style={{ marginTop: "16px" }}>
      <p style={{ fontFamily: FONT, fontSize: "13px", color: "rgba(255,255,255,0.35)", marginBottom: "12px" }}>
        {departments.length} departments · {totalCourses.toLocaleString()} courses
      </p>
      <DepartmentList
        departments={departments} school={school}
        expandedDepts={expandedDepts} deptCoursesMap={deptCoursesMap}
        loadingDepts={loadingDepts}
        onDeptExpand={handleDeptExpand}
      />
    </div>
  ), [departments, totalCourses, school, expandedDepts, deptCoursesMap, loadingDepts, expandedCourses, handleDeptExpand, toggleCourse]);

  const renderResultsContent = useCallback((results: CourseSummary[]) => (
    results.length > 0 ? (
      <EntityScrollList
        items={results} initialCap={100} batchSize={100}
        columns={COURSE_COLUMNS} renderRow={renderCourseRow}
        keyExtractor={courseKeyExtractor} entityName="courses" school={school}
      />
    ) : null
  ), [renderCourseRow, courseKeyExtractor, school]);

  return (
    <QueryShell<CourseSummary>
      school={school} onBack={onBack} parentShape="cube"
      placeholder={`Ask me a question about ${school.name} courses.`}
      examples={EXAMPLES} queryFn={queryFn} loadInitialData={loadInitialData}
      renderInitialContent={renderInitialContent} renderResultsContent={renderResultsContent}
      onQueryStart={onQueryStart} onReset={onReset} rootRef={rootRef}
    />
  );
}

/* ── Course Result Row (for query results) ────────────────────────────── */

const CourseResultRow = memo(function CourseResultRow({ course, i, school, expandedCourses, onToggle }: {
  course: CourseSummary; i: number; school: SchoolConfig;
  expandedCourses: Set<string>; onToggle: (code: string) => void;
}) {
  const isOpen = expandedCourses.has(course.code);
  const hasMounted = useRef(false);
  useEffect(() => { hasMounted.current = true; }, []);
  return (
    <div>
      <motion.button
        initial={hasMounted.current ? false : { opacity: 0, y: 6 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.2, delay: hasMounted.current ? 0 : Math.min(i * 0.01, 0.2) }}
        onClick={() => onToggle(course.code)}
        style={{
          width: "100%", textAlign: "left",
          display: "grid", gridTemplateColumns: "24px auto 1fr",
          padding: "14px 16px", gap: "12px", alignItems: "center",
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
        <span style={{ fontFamily: FONT, fontSize: "12px", fontWeight: 600, color: school.brandColorLight, flexShrink: 0 }}>
          {course.code}
        </span>
        <span style={{ fontFamily: FONT, fontSize: "14px", fontWeight: 500, color: "rgba(255,255,255,0.85)" }}>
          {course.name}
        </span>
      </motion.button>

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
              padding: "16px 16px 20px 52px",
              background: "rgba(255,255,255,0.03)",
              display: "flex", flexDirection: "column", gap: "16px",
            }}>
              {course.description && (
                <div>
                  <span style={{ fontFamily: FONT, fontSize: "10px", fontWeight: 600, letterSpacing: "0.1em", textTransform: "uppercase", color: school.brandColorLight, opacity: 0.6, display: "block", marginBottom: "8px" }}>
                    Description
                  </span>
                  <p style={{ fontFamily: FONT, fontSize: "13px", color: "rgba(255,255,255,0.6)", lineHeight: 1.6, margin: 0 }}>
                    {course.description}
                  </p>
                </div>
              )}
              {course.learningOutcomes.length > 0 && (
                <div>
                  <span style={{ fontFamily: FONT, fontSize: "10px", fontWeight: 600, letterSpacing: "0.1em", textTransform: "uppercase", color: school.brandColorLight, opacity: 0.6, display: "block", marginBottom: "8px" }}>
                    Learning Outcomes
                  </span>
                  <ul style={{ margin: 0, paddingLeft: "16px", display: "flex", flexDirection: "column", gap: "4px" }}>
                    {course.learningOutcomes.map((o) => (
                      <li key={o} style={{ fontFamily: FONT, fontSize: "12px", color: "rgba(255,255,255,0.6)", lineHeight: 1.5 }}>{o}</li>
                    ))}
                  </ul>
                </div>
              )}
              {course.learningOutcomes.length === 0 && course.courseObjectives.length > 0 && (
                <div>
                  <span style={{ fontFamily: FONT, fontSize: "10px", fontWeight: 600, letterSpacing: "0.1em", textTransform: "uppercase", color: school.brandColorLight, opacity: 0.6, display: "block", marginBottom: "8px" }}>
                    Course Objectives
                  </span>
                  <ul style={{ margin: 0, paddingLeft: "16px", display: "flex", flexDirection: "column", gap: "4px" }}>
                    {course.courseObjectives.map((o) => (
                      <li key={o} style={{ fontFamily: FONT, fontSize: "12px", color: "rgba(255,255,255,0.6)", lineHeight: 1.5 }}>{o}</li>
                    ))}
                  </ul>
                </div>
              )}
              {course.skillMappings.length > 0 && (
                <div>
                  <span style={{ fontFamily: FONT, fontSize: "10px", fontWeight: 600, letterSpacing: "0.1em", textTransform: "uppercase", color: school.brandColorLight, opacity: 0.6, display: "block", marginBottom: "8px" }}>
                    Derived Skills
                  </span>
                  <div style={{ display: "flex", flexWrap: "wrap", gap: "6px" }}>
                    {course.skillMappings.map((skill) => (
                      <span key={skill} style={{
                        padding: "5px 12px", background: "rgba(255,255,255,0.02)",
                        border: `1px solid ${school.brandColorLight}60`, borderRadius: "6px",
                        fontFamily: FONT, fontSize: "12px", fontWeight: 500, color: school.brandColorLight,
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
});

/* ── Department List ──────────────────────────────────────────────────── */

function DepartmentList({
  departments, school, expandedDepts, deptCoursesMap, loadingDepts,
  onDeptExpand,
}: {
  departments: DepartmentSummary[];
  school: SchoolConfig;
  expandedDepts: Set<string>;
  deptCoursesMap: Record<string, CourseSummary[]>;
  loadingDepts: Set<string>;
  onDeptExpand: (dept: string) => void;
}) {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "2px" }}>
      <ColumnHeaders
        columns={[{ label: "Department", width: "1fr" }, { label: "Courses", width: "auto", align: "right" }]}
        gridTemplateColumns="24px 1fr auto"
        brandColor={school.brandColorLight}
      />
      {departments.map((dept, i) => (
        <DepartmentRow
          key={dept.department}
          department={dept.department}
          courseCount={dept.courseCount}
          index={i}
          brandColor={school.brandColorLight}
          schoolName={school.name}
          isOpen={expandedDepts.has(dept.department)}
          onToggle={() => onDeptExpand(dept.department)}
          courses={deptCoursesMap[dept.department] ?? null}
          isLoading={loadingDepts.has(dept.department)}
        />
      ))}
      {departments.length === 0 && (
        <p style={{ fontFamily: FONT, fontSize: "14px", color: "rgba(255,255,255,0.35)", padding: "40px 0", textAlign: "center" }}>
          No departments match that query. Try a different question.
        </p>
      )}
    </div>
  );
}
