"use client";

import { useState, useEffect, useCallback, useRef, memo, useMemo } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { SchoolConfig } from "@/config/schoolConfig";
import { getDepartments, getCourses, queryCourses } from "@/college-atlas/courses/api";
import type { ApiDepartmentSummary, ApiCourseSummary } from "@/college-atlas/courses/api";
import type { DepartmentSummary, CourseSummary } from "@/college-atlas/courses/types";
import CourseOccupationsCallout from "@/college-atlas/courses/CourseOccupationsCallout";
import EntityScrollList from "@/ui/EntityScrollList";
import type { Column } from "@/ui/EntityScrollList";
import QueryShell, { findScrollParent } from "@/ui/QueryShell";
import DepartmentRow from "@/college-atlas/courses/DepartmentRow";
import ColumnHeaders from "@/ui/ColumnHeaders";

const FONT = "var(--font-inter), Inter, system-ui, sans-serif";

function mapDept(api: ApiDepartmentSummary): DepartmentSummary {
  return { department: api.department, courseCount: api.course_count };
}

function mapCourse(api: ApiCourseSummary): CourseSummary {
  return {
    name: api.name, code: api.code, description: api.description,
    learningOutcomes: api.learning_outcomes, courseObjectives: api.course_objectives,
    topCode: api.top_code ?? null,
  };
}

const COURSE_COLUMNS: Column[] = [
  { label: "Code", width: "100px" },
  { label: "Name", width: "1fr" },
];

// Per-college CTE-leaning department substituted into the
// "in the 'X' department" example. Each value is a department name
// that exists at the school, so the example returns real records
// rather than the empty set the previous numeric example produced for
// some colleges. Mirrors the students FOCUS_BY_COLLEGE pattern.
const DEPT_BY_COLLEGE: Record<string, string> = {
  "Shasta College": "early childhood education",
  "Foothill College": "accounting",
  "College of the Sequoias": "child development",
  "Oxnard College": "fire technology",
  "Compton College": "nursing",
  "Irvine Valley College": "accounting",
  "College of the Desert": "nursing",
  "San Diego City College": "business",
};

const DEPT_DEFAULT = "business";

// Example queries shown as suggestions. Each demonstrates one supported
// query shape — bare-noun department search, the column-name "in the
// 'X' department" form, the institutional TOP-SOC bridge, and a fixed-
// keyword flag. Slot 3 substitutes a per-college CTE-flavored department
// to guarantee non-zero results across schools.
function buildExamples(schoolName: string): string[] {
  const dept = DEPT_BY_COLLEGE[schoolName] ?? DEPT_DEFAULT;
  return [
    "Courses in 'computer science'",
    "Courses that prepare for 'nursing' occupations",
    `Courses in the '${dept}' department`,
    "Career and technical education courses",
  ];
}

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

  // Eager-load every subdiscipline's courses after the initial dept-summary
  // load lands. Powers client-side substring search on `course.name` /
  // `course.code` without a backend round-trip per keystroke. Browser
  // concurrency limits naturally throttle the parallel `getCourses` fan-out
  // (~6-10 in flight at a time); for our largest college (SBCC, ~120 depts)
  // the full preload completes in seconds. `ensureCoursesLoaded` dedupes so
  // re-firing is harmless.
  useEffect(() => {
    if (departments.length === 0) return;
    departments.forEach((d) => { ensureCoursesLoaded(d.department); });
    // ensureCoursesLoaded is stable per school; effect re-runs on dept-list change.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [departments]);

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

  const deptCoursesMapRef = useRef(deptCoursesMap);
  deptCoursesMapRef.current = deptCoursesMap;
  const loadingDeptsRef = useRef(loadingDepts);
  loadingDeptsRef.current = loadingDepts;

  const ensureCoursesLoaded = useCallback(async (dept: string) => {
    if (deptCoursesMapRef.current[dept] || loadingDeptsRef.current.has(dept)) return;
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
  }, [school.name]);

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
        {departments.length} programs · {totalCourses.toLocaleString()} courses
      </p>
      <DepartmentList
        departments={departments} school={school}
        expandedDepts={expandedDepts} deptCoursesMap={deptCoursesMap}
        loadingDepts={loadingDepts}
        onDeptExpand={handleDeptExpand}
      />
    </div>
  ), [departments, totalCourses, school, expandedDepts, deptCoursesMap, loadingDepts, handleDeptExpand]);

  const renderSearchContent = useCallback((q: string) => {
    const lower = q.toLowerCase();
    // Course-centric filter. A subdiscipline shows up in results when:
    //   (a) its NAME contains the query — show all its courses, or
    //   (b) any of its COURSES has a name or code containing the query —
    //       show only those matching courses.
    // The subdiscipline-name match is the secondary signal so that typing
    // "math" surfaces the Mathematics subdiscipline and its courses, while
    // typing "calculus" surfaces only the calculus courses (regardless of
    // which subdiscipline they sit under).
    const filteredDepts: DepartmentSummary[] = [];
    const filteredCoursesMap: Record<string, CourseSummary[]> = {};
    let totalMatchedCourses = 0;
    for (const dept of departments) {
      const deptMatches = dept.department.toLowerCase().includes(lower);
      const deptCourses = deptCoursesMap[dept.department] ?? [];
      const matchingCourses = deptMatches
        ? deptCourses
        : deptCourses.filter(c =>
            c.name.toLowerCase().includes(lower) ||
            c.code.toLowerCase().includes(lower)
          );
      // Skip subdisciplines that contribute nothing. If the subdiscipline
      // name matches but its courses haven't loaded yet, we keep it so it
      // surfaces under partial-load (count will fill in once courses arrive).
      const courseCount = deptMatches && deptCourses.length === 0
        ? dept.courseCount
        : matchingCourses.length;
      if (matchingCourses.length === 0 && !deptMatches) continue;
      filteredDepts.push({ department: dept.department, courseCount });
      filteredCoursesMap[dept.department] = matchingCourses;
      totalMatchedCourses += matchingCourses.length;
    }
    if (filteredDepts.length === 0) {
      return (
        <p style={{ fontFamily: FONT, fontSize: "14px", color: "rgba(255,255,255,0.35)", padding: "40px 0", textAlign: "center" }}>
          No courses match &ldquo;{q}&rdquo;.
        </p>
      );
    }
    const allExpanded = new Set(filteredDepts.map(d => d.department));
    return (
      <div style={{ marginTop: "16px" }}>
        <SearchDepartmentLoader departments={filteredDepts} ensureLoaded={ensureCoursesLoaded} />
        <p style={{ fontFamily: FONT, fontSize: "13px", color: "rgba(255,255,255,0.35)", marginBottom: "12px" }}>
          {totalMatchedCourses.toLocaleString()} course{totalMatchedCourses !== 1 ? "s" : ""} in {filteredDepts.length} program{filteredDepts.length !== 1 ? "s" : ""} matching &ldquo;{q}&rdquo;
        </p>
        <DepartmentList
          departments={filteredDepts} school={school}
          expandedDepts={allExpanded} deptCoursesMap={filteredCoursesMap}
          loadingDepts={loadingDepts}
          onDeptExpand={handleDeptExpand}
        />
      </div>
    );
  }, [departments, school, deptCoursesMap, loadingDepts, handleDeptExpand, ensureCoursesLoaded]);

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
      school={school} formName="Courses" onBack={onBack}
      placeholder={`Ask me a question about ${school.name} courses.`}
      examples={buildExamples(school.name)} queryFn={queryFn} loadInitialData={loadInitialData}
      renderInitialContent={renderInitialContent} renderResultsContent={renderResultsContent}
      renderSearchContent={renderSearchContent}
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
  const topCode = course.topCode;
  const topCodeDisplay = topCode && /^\d{6}$/.test(topCode)
    ? `${topCode.slice(0, 4)}.${topCode.slice(4, 6)}`
    : topCode;
  return (
    <div>
      <motion.button
        initial={hasMounted.current ? false : { opacity: 0, y: 6 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.2, delay: hasMounted.current ? 0 : Math.min(i * 0.01, 0.2) }}
        onClick={() => onToggle(course.code)}
        style={{
          width: "100%", textAlign: "left",
          display: "grid", gridTemplateColumns: "24px 100px 1fr",
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
              {topCodeDisplay && (
                <div>
                  <span style={{ fontFamily: FONT, fontSize: "10px", fontWeight: 600, letterSpacing: "0.1em", textTransform: "uppercase", color: school.brandColorLight, opacity: 0.6, display: "block", marginBottom: "8px" }}>
                    TOP Code
                  </span>
                  <span style={{ fontFamily: "var(--font-mono), ui-monospace, SFMono-Regular, monospace", fontSize: "12px", color: "rgba(255,255,255,0.6)" }}>
                    {topCodeDisplay}
                  </span>
                </div>
              )}
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
              <CourseOccupationsCallout
                courseCode={course.code}
                collegeName={school.name}
                brandColor={school.brandColorLight}
              />
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
});

/* ── Search auto-loader ──────────────────────────────────────────────── */

function SearchDepartmentLoader({ departments, ensureLoaded }: {
  departments: DepartmentSummary[];
  ensureLoaded: (dept: string) => Promise<void>;
}) {
  const key = useMemo(() => departments.map(d => d.department).join("\0"), [departments]);
  useEffect(() => {
    departments.forEach(d => ensureLoaded(d.department));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [key, ensureLoaded]);
  return null;
}

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
        columns={[{ label: "Program (TOP4)", width: "1fr" }, { label: "Courses", width: "auto", align: "right" }]}
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
