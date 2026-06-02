"use client";

import { useState, useEffect, useMemo } from "react";
import { motion } from "framer-motion";
import { SchoolConfig } from "@/config/schoolConfig";
import {
  getPartnershipOpportunity,
  type ApiOpportunityReport,
  type ApiPartnershipOpportunityEmployer,
} from "@/college-atlas/partnerships/api";
import OccupationRow, {
  type OccupationData,
  type OccupationDetail,
} from "@/college-atlas/occupations/OccupationRow";
import DepartmentRow, { type CourseItem } from "@/college-atlas/courses/DepartmentRow";
import CurriculumPathway from "@/college-atlas/partnerships/CurriculumPathway";
import StudentRow, {
  type StudentData,
  type StudentDetailData,
} from "@/college-atlas/students/StudentRow";
import AtlasHeader from "@/ui/AtlasHeader";
import KallipolisBrand from "@/ui/KallipolisBrand";
import RisingSun from "@/ui/RisingSun";
import { FONT, MONO, ReportHeader, Section, Prose } from "@/college-atlas/partnerships/reportChrome";

type Props = {
  school: SchoolConfig;
  socCode: string;
  // Click-context sector — the partnerships-listing tab the user
  // navigated from. Forwarded to the backend so SOCs that belong to
  // multiple PCAH sectors render under the user's chosen lens rather
  // than the alphabetical default. Undefined for deep-links / back-
  // navigation; backend falls back to the alphabetical sector then.
  sector?: string;
  onBack: () => void;
};

export default function OpportunityReport({ school, socCode, sector, onBack }: Props) {
  return (
    <div>
      <AtlasHeader
        school={school}
        onBack={onBack}
        title={school.name}
        rightSlot={<KallipolisBrand />}
      />
      <div style={{ maxWidth: "880px", margin: "0 auto", padding: "32px 40px 80px" }}>
        <OpportunityReportBody school={school} socCode={socCode} sector={sector} />
      </div>
    </div>
  );
}

/* ── Embeddable body — fetch + render, no header/overlay chrome ───────────
   Used full (with Executive Summary) by the routed report above, and
   embedded (executive summary suppressed, eyebrow dropped) inside the SVAMP
   aggregated landscape so a selection renders inline without a page load. */
export function OpportunityReportBody({
  school, socCode, sector, hideExecutiveSummary = false, embedded = false,
}: {
  school: SchoolConfig;
  socCode: string;
  sector?: string;
  hideExecutiveSummary?: boolean;
  embedded?: boolean;
}) {
  const [report, setReport] = useState<ApiOpportunityReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!socCode) return;
    setLoading(true);
    setError(null);
    getPartnershipOpportunity(socCode, school.name, sector)
      .then(setReport)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [socCode, school.name, sector]);

  if (loading) {
    return (
      <div style={{ display: "flex", justifyContent: "center", paddingTop: "80px" }}>
        <RisingSun style={{ width: "90px", height: "auto", opacity: 0.4 }} />
      </div>
    );
  }
  if (error) {
    return (
      <p style={{ fontFamily: FONT, fontSize: "14px", color: "#f87171", padding: "40px 0", textAlign: "center" }}>
        {error}
      </p>
    );
  }
  if (!report) return null;
  return (
    <ReportBody report={report} school={school} hideExecutiveSummary={hideExecutiveSummary} embedded={embedded} />
  );
}

/* ── Report Body ───────────────────────────────────────────────────────── */

function ReportBody({
  report, school, hideExecutiveSummary = false, embedded = false,
}: {
  report: ApiOpportunityReport;
  school: SchoolConfig;
  hideExecutiveSummary?: boolean;
  embedded?: boolean;
}) {
  const brandColor = school.brandColorLight;

  // ── Synthesize component-shaped data from the report's evidence ───────
  // Each reused feature-view component (OccupationRow, DepartmentRow,
  // StudentRow) takes its own typed input. The OpportunityReport
  // already carries the underlying material; here we project it into
  // each component's expected shape so the visual idiom matches the
  // rest of the product without duplicating component logic.

  const occData = useMemo<OccupationData>(() => {
    const ev = report.opportunity_evidence[0];
    return {
      title: report.soc_title,
      soc_code: report.soc_code,
      annual_wage: ev?.annual_wage ?? null,
      employment: ev?.employment ?? null,
      growth_rate: ev?.growth_rate ?? null,
      annual_openings: ev?.annual_openings ?? null,
      description: report.description ?? null,
    };
  }, [report]);

  const occDetail = useMemo<OccupationDetail>(() => {
    const ev = report.opportunity_evidence[0];
    return {
      soc_code: report.soc_code,
      title: report.soc_title,
      description: report.description ?? null,
      // Curriculum Alignment is suppressed via hideCurriculumAlignment.
      // Pass an empty list here so the OccupationRow detail shape is
      // satisfied without the inner section rendering.
      aligned_top_groups: [],
      aligned_course_count: 0,
      aligned_program_area_count: 0,
      regions: report.regions.map((region) => ({
        region,
        employment: ev?.employment ?? 0,
        annual_wage: ev?.annual_wage ?? null,
        growth_rate: ev?.growth_rate ?? null,
        annual_openings: ev?.annual_openings ?? null,
      })),
    };
  }, [report]);

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
    >
      {/* Title block — Option C: magazine-style super-title.
          Document type is the dominant element ("PARTNERSHIP LANDSCAPE
          REPORT"), with a brand-tinted hairline divider, then the SOC
          title, then the SOC + sector eyebrow demoted to a footer
          classifier. A "REGIONAL PRIORITY" segment appears in the
          eyebrow when the sector is one of the college's COE region's
          Strong Workforce Program priority sectors.

          (Region subtitle and standalone Description section removed
          per product feedback; the description now lives inside the
          OccupationRow expansion below.) */}
      {/* Title block — Option C: magazine-style super-title. Document type
          is dominant ("PARTNERSHIP LANDSCAPE REPORT"), then the SOC title,
          then the SOC + sector eyebrow demoted to a footer classifier.
          (Region subtitle and standalone Description removed per product
          feedback; the description now lives in the OccupationRow expansion.) */}
      <ReportHeader eyebrow={embedded ? school.name : "Partnership Landscape Report"} title={report.soc_title} accent={brandColor}>
        <span style={{ color: brandColor, opacity: 0.55 }}>
          SOC {report.soc_code}
        </span>
        {report.sector && (
          <>
            <span style={{ color: "rgba(255,255,255,0.25)", margin: "0 8px" }}>·</span>
            <span style={{ color: "rgba(255,255,255,0.80)", letterSpacing: "0.08em" }}>
              {report.sector}
            </span>
          </>
        )}
        {report.is_sector_priority && (
          <>
            <span style={{ color: "rgba(255,255,255,0.25)", margin: "0 8px" }}>·</span>
            <span style={{ color: brandColor, letterSpacing: "0.1em", fontWeight: 600 }}>
              Regional Priority Sector
            </span>
          </>
        )}
      </ReportHeader>

      {/* Executive summary — suppressed when embedded (the SVAMP page's own
          consortium summary already frames the document). */}
      {!hideExecutiveSummary && (
        <Section title="Executive Summary" brandColor={brandColor}>
          <Prose>{report.executive_summary}</Prose>
        </Section>
      )}

      {/* Occupational Demand — Centers of Excellence narrative
          (wage, openings, current regional employment, 5-year
          projected growth) followed by the OccupationRow accordion
          as its supporting evidence. The inner Curriculum Alignment
          block is suppressed because the report has its own dedicated
          section for that below. The structural supply/demand evidence
          (table, workforce gap viz, sources) appears further down in
          the Labor Market Information section. The row defaults to
          collapsed for visual consistency with the other accordion
          rows in the report (Curriculum Alignment, Student Impact,
          Partnership Opportunities all start collapsed). */}
      <Section title="Occupational Demand" brandColor={brandColor}>
        <Prose>{report.occupational_demand}</Prose>
        <div style={{ marginTop: "16px" }}>
          <OccupationRowWrapper
            occData={occData}
            occDetail={occDetail}
            brandColor={brandColor}
            regions={report.regions}
            collegeName={school.name}
          />
        </div>
      </Section>

      {/* Curriculum Alignment — two-part section:
          (1) Specific evidence: per-department accordion of the actual
              courses at this college that institutionally prepare for
              the SOC. Builds trust with course-level concreteness.
          (2) Contextual zoom-out: the CurriculumPathway hero
              visualization, framing this college's specific coverage
              against the full TOP × CIP institutional prep set. The
              headline metric ("N of M TOP groups supporting SOC X")
              naturally introduces the wider view.
          The reading order is specific → contextual, which is more
          credible than the reverse: a coordinator first sees the
          concrete courses they know exist, then sees where those sit
          in the broader institutional crosswalk. */}
      <Section title="Curriculum Alignment" brandColor={brandColor}>
        {report.curriculum_evidence.length === 0 ? (
          <Prose>
            No departments at {school.name} have institutionally aligned curriculum for this
            occupation. The crosswalk below shows the system-wide TOP × CIP pathway that
            prepares students for this occupation — a workforce gap at this college that
            consortia partners may already address.
          </Prose>
        ) : (
          <>
            <Prose>{report.curriculum_alignment}</Prose>
            <div style={{ marginTop: "16px", display: "flex", flexDirection: "column", gap: "2px" }}>
              {report.curriculum_evidence.map((dept, i) => {
                const courses: CourseItem[] = dept.courses.map((c) => ({
                  code: c.code,
                  name: c.name,
                  description: c.description,
                  learningOutcomes: c.learning_outcomes,
                  topCode: c.top_code ?? null,
                }));
                return (
                  <DepartmentRowWrapper
                    key={dept.department}
                    department={dept.department}
                    courseCount={dept.courses.length}
                    index={i}
                    brandColor={brandColor}
                    courses={courses}
                    schoolName={school.name}
                    socFilter={report.soc_code}
                  />
                );
              })}
            </div>
          </>
        )}

        {/* Contextual zoom-out: TOP × CIP × SOC institutional pathway.
            Rendered regardless of whether the college has aligned
            curriculum — for gap rows (curriculum_evidence empty),
            the visualization shows the institutional pathway with all
            TOPs dimmed, which is the workforce-gap signal worth
            seeing. The guard against empty `tops` is defensive
            against SOCs with no PREPARES_FOR materialization anywhere
            in the system (rare but possible). */}
        {report.curriculum_crosswalk &&
          report.curriculum_crosswalk.tops.length > 0 && (
            <CurriculumPathway
              crosswalk={report.curriculum_crosswalk}
              collegeName={school.name}
              socCode={report.soc_code}
              socTitle={report.soc_title}
              brandColor={brandColor}
            />
          )}
      </Section>

      {/* Student Impact — narrative + headline metric callout +
          top students rendered via StudentRow with the Competency
          Profile tab suppressed. */}
      <Section title="Student Impact" brandColor={brandColor}>
        <Prose>{report.student_impact}</Prose>

        {/* Headline callout — the integrative figure for the section.
            Mirrors the "STUDENTS IN ALIGNED PROGRAMS" callout the
            previous artifact carried at the top of the student block. */}
        <div style={{
          marginTop: "16px",
          background: "rgba(255,255,255,0.03)",
          border: "1px solid rgba(255,255,255,0.06)",
          borderRadius: "8px",
          padding: "20px",
          textAlign: "center",
        }}>
          <div style={{
            fontFamily: FONT, fontSize: "28px", fontWeight: 700,
            color: "rgba(255,255,255,0.95)",
            letterSpacing: "-0.005em",
            fontVariantNumeric: "tabular-nums",
          }}>
            {report.student_evidence.total_in_aligned_departments.toLocaleString()}
          </div>
          <div style={{
            marginTop: "6px",
            fontFamily: FONT, fontSize: "10px", fontWeight: 600,
            letterSpacing: "0.12em", textTransform: "uppercase",
            color: "rgba(255,255,255,0.45)",
          }}>
            Students in Aligned Programs
          </div>
        </div>

        {/* Top students table — column header strip + StudentRow list.
            Backend ranks students by count of TOP4-aligned course
            enrollments at this college, then GPA. Edge case: if no
            student at the college has any TOP4-aligned enrollment,
            the list is empty and the report honestly says so. The
            unified empty state covers both "no aligned departments at
            all" and "aligned departments exist but no TOP4 student
            enrollments" — same operational meaning from the reader's
            perspective. */}
        {report.student_evidence.top_students.length === 0 && (
          <p style={{ fontFamily: FONT, fontSize: "13px", color: "rgba(255,255,255,0.45)", marginTop: "16px", lineHeight: 1.55 }}>
            No students at {school.name} have coursework that aligns with SOC {report.soc_code}&rsquo;s preparation pathway.
          </p>
        )}
        {report.student_evidence.top_students.length > 0 && (
          <div style={{ marginTop: "20px" }}>
            <div style={{
              display: "grid", gridTemplateColumns: "24px 110px 1fr 90px 60px", minWidth: "500px",
              padding: "10px 16px", gap: "10px", alignItems: "center",
              borderBottom: "1px solid rgba(255,255,255,0.05)",
            }}>
              <span />
              <ColHead brandColor={brandColor}>Student</ColHead>
              <ColHead brandColor={brandColor}>Primary Focus</ColHead>
              <ColHead brandColor={brandColor}>Courses</ColHead>
              <ColHead brandColor={brandColor}>GPA</ColHead>
            </div>
            <div style={{ display: "flex", flexDirection: "column", gap: "2px" }}>
              {report.student_evidence.top_students.map((s, i) => {
                const studentData: StudentData = {
                  uuid: s.uuid,
                  displayNumber: s.display_number,
                  primaryFocus: s.primary_focus,
                  coursesCompleted: s.courses_completed,
                  gpa: s.gpa,
                };
                const detail: StudentDetailData = {
                  enrollments: s.enrollments.map((e) => ({
                    courseCode: e.code,
                    courseName: e.name,
                    department: "",
                    grade: e.grade,
                    term: e.term,
                    status: "",
                  })),
                  occupationAlignment: [],
                };
                return (
                  <StudentRowWrapper
                    key={s.uuid}
                    student={studentData}
                    index={i}
                    brandColor={brandColor}
                    detail={detail}
                  />
                );
              })}
            </div>
          </div>
        )}

        {/* Methodology footnote — synthetic-data attribution for the
            entire Student Impact section. Always rendered (even in the
            empty-state case) because the absence of aligned students is
            itself a property of the synthetic layer. The wording
            doubles as the upgrade conversation hook for partnership
            data sharing — naming "anonymized" pre-empts the FERPA
            objection coordinators surface first. */}
        <p style={{
          fontFamily: FONT,
          fontSize: "11px",
          color: "rgba(255,255,255,0.4)",
          fontStyle: "italic",
          marginTop: "20px",
          paddingTop: "14px",
          borderTop: "1px solid rgba(255,255,255,0.05)",
          lineHeight: 1.55,
        }}>
          Profiles above are synthetic — calibrated to CCCCO DataMart Fall 2025 grade distributions. Live anonymized MIS data from your institution would render real student records.
        </p>
      </Section>

      {/* Labor Market Information — narrative + demand table +
          openings/supply gap visualization + institutional sources. */}
      <LaborMarketInformation report={report} brandColor={brandColor} />

      {/* Partnership Opportunities — candidate employer set */}
      <Section title="Partnership Opportunities" brandColor={brandColor}>
        <Prose>{report.partnership_opportunities_narrative}</Prose>
        {report.partnership_opportunities.length > 0 && (
          <div style={{ marginTop: "16px", display: "flex", flexDirection: "column", gap: "2px" }}>
            {report.partnership_opportunities.map((emp, i) => (
              <PartnerEmployerRow
                key={emp.name}
                emp={emp}
                index={i}
                brandColor={brandColor}
              />
            ))}
          </div>
        )}
      </Section>
    </motion.div>
  );
}

/* ── OccupationRow wrapper to manage local open state ─────────────────── */

function OccupationRowWrapper({
  occData, occDetail, brandColor, regions, collegeName,
}: {
  occData: OccupationData;
  occDetail: OccupationDetail;
  brandColor: string;
  regions: string[];
  collegeName: string;
}) {
  const [isOpen, setIsOpen] = useState(false);
  return (
    <OccupationRow
      occ={occData}
      index={0}
      brandColor={brandColor}
      isOpen={isOpen}
      onToggle={() => setIsOpen((o) => !o)}
      detail={occDetail}
      regionNames={regions}
      collegeName={collegeName}
      hideCurriculumAlignment
    />
  );
}

/* ── DepartmentRow wrapper to manage local open state ─────────────────── */

function DepartmentRowWrapper({
  department, courseCount, index, brandColor, courses, schoolName, socFilter,
}: {
  department: string;
  courseCount: number;
  index: number;
  brandColor: string;
  courses: CourseItem[];
  schoolName: string;
  socFilter: string;
}) {
  const [isOpen, setIsOpen] = useState(false);
  return (
    <DepartmentRow
      department={department}
      courseCount={courseCount}
      index={index}
      brandColor={brandColor}
      isOpen={isOpen}
      onToggle={() => setIsOpen((o) => !o)}
      courses={courses}
      schoolName={schoolName}
      hideOccupationPathways
      socFilter={socFilter}
    />
  );
}

/* ── StudentRow wrapper to manage local open state ────────────────────── */

function StudentRowWrapper({
  student, index, brandColor, detail,
}: {
  student: StudentData;
  index: number;
  brandColor: string;
  detail: StudentDetailData;
}) {
  const [isOpen, setIsOpen] = useState(false);
  return (
    <StudentRow
      student={student}
      index={index}
      brandColor={brandColor}
      isOpen={isOpen}
      onToggle={() => setIsOpen((o) => !o)}
      detail={detail}
      hideCompetencyProfile
    />
  );
}

/* ── Labor Market Information section ─────────────────────────────────── */

function LaborMarketInformation({
  report, brandColor,
}: { report: ApiOpportunityReport; brandColor: string }) {
  const swp = report.swp_evidence;
  const totalDemand = swp.total_demand;
  const totalSupply = swp.total_supply;
  const gap = swp.gap;
  const regionDisplay = swp.sources?.coe_region_display || swp.coe_region;
  const sources = swp.sources;

  // The supply CSV publishes only positive values (min 0.33; zero rows
  // never appear). Absence of a supply estimate means COE didn't publish
  // a projection for this (college, TOP) combination — not a measured
  // zero. The prose discriminates so we don't dress data absence as a
  // measurement.
  const hasPublishedSupply = swp.supply_estimates.length > 0;
  const supplyRounded = Math.round(totalSupply);
  const gapRounded = Math.round(gap);

  return (
    <Section title="Labor Market Information" brandColor={brandColor}>
      <Prose>
        According to the Centers of Excellence, SOC {report.soc_code} demands{" "}
        {totalDemand.toLocaleString()} annual{" "}
        {totalDemand === 1 ? "opening" : "openings"} in the {regionDisplay} region.{" "}
        {hasPublishedSupply ? (
          gapRounded > 0 ? (
            <>
              On the supply side, {report.college} is projected to support{" "}
              {supplyRounded.toLocaleString()} annual program{" "}
              {supplyRounded === 1 ? "completion" : "completions"} for the related TOP codes,
              leaving a workforce gap of {gapRounded.toLocaleString()} annual{" "}
              {gapRounded === 1 ? "opening" : "openings"}.
            </>
          ) : (
            <>
              On the supply side, {report.college} is projected to support{" "}
              {supplyRounded.toLocaleString()} annual program{" "}
              {supplyRounded === 1 ? "completion" : "completions"} for the related TOP codes,
              matching or exceeding projected regional demand.
            </>
          )
        ) : (
          <>
            On the supply side, no projected program completions are published for the related
            TOP codes at {report.college}, so the workforce gap is not quantified for this pathway.
          </>
        )}
      </Prose>

      {/* Demand table */}
      {swp.occupations.length > 0 && (
        <div style={{ marginTop: "20px" }}>
          <span style={{
            fontFamily: FONT, fontSize: "12px", fontWeight: 600,
            color: "rgba(255,255,255,0.7)",
            display: "block", marginBottom: "10px",
          }}>
            Demand: regional annual openings by SOC
          </span>
          <div style={{
            background: "rgba(255,255,255,0.025)",
            border: "1px solid rgba(255,255,255,0.06)",
            borderRadius: "8px",
            padding: "10px 16px",
          }}>
            <div style={{
              display: "grid", gridTemplateColumns: "90px 1fr 110px 130px",
              gap: "12px", padding: "6px 0",
              borderBottom: "1px solid rgba(255,255,255,0.05)",
            }}>
              <ColHead brandColor={brandColor}>SOC</ColHead>
              <ColHead brandColor={brandColor}>Occupation</ColHead>
              <ColHead brandColor={brandColor} align="right">Wage</ColHead>
              <ColHead brandColor={brandColor} align="right">Annual openings</ColHead>
            </div>
            {swp.occupations.map((o) => (
              <div
                key={o.soc_code ?? o.title}
                style={{
                  display: "grid", gridTemplateColumns: "90px 1fr 110px 130px",
                  gap: "12px", padding: "10px 0",
                  alignItems: "baseline",
                }}
              >
                <span style={{ fontFamily: MONO, fontSize: "12px", color: "rgba(255,255,255,0.55)" }}>
                  {o.soc_code ?? "—"}
                </span>
                <span style={{ fontFamily: FONT, fontSize: "13px", color: "rgba(255,255,255,0.78)" }}>
                  {o.title}
                </span>
                <span style={{ fontFamily: FONT, fontSize: "13px", color: "rgba(255,255,255,0.7)", textAlign: "right", fontVariantNumeric: "tabular-nums" }}>
                  {o.annual_wage != null ? `$${o.annual_wage.toLocaleString()}` : "—"}
                </span>
                <span style={{ fontFamily: FONT, fontSize: "13px", color: "rgba(255,255,255,0.7)", textAlign: "right", fontVariantNumeric: "tabular-nums" }}>
                  {o.annual_openings != null ? o.annual_openings.toLocaleString() : "—"}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Supply sub-table — only renders when COE publishes at least one
          projected-completions row for the related TOP codes at this
          college. Absence is handled by the prose ("does not publish
          projected program completions"); we don't show an empty table. */}
      {swp.supply_estimates.length > 0 && (
        <div style={{ marginTop: "20px" }}>
          <span style={{
            fontFamily: FONT, fontSize: "12px", fontWeight: 600,
            color: "rgba(255,255,255,0.7)",
            display: "block", marginBottom: "10px",
          }}>
            Supply: projected annual program completions by TOP
          </span>
          <div style={{
            background: "rgba(255,255,255,0.025)",
            border: "1px solid rgba(255,255,255,0.06)",
            borderRadius: "8px",
            padding: "10px 16px",
          }}>
            <div style={{
              display: "grid", gridTemplateColumns: "80px 1fr 200px 110px",
              gap: "12px", padding: "6px 0",
              borderBottom: "1px solid rgba(255,255,255,0.05)",
            }}>
              <ColHead brandColor={brandColor}>TOP</ColHead>
              <ColHead brandColor={brandColor}>Program</ColHead>
              <ColHead brandColor={brandColor}>Award</ColHead>
              <ColHead brandColor={brandColor} align="right">Annual supply</ColHead>
            </div>
            {swp.supply_estimates.map((s, i) => (
              <div
                key={`${s.top_code}-${s.award_level}-${i}`}
                style={{
                  display: "grid", gridTemplateColumns: "80px 1fr 200px 110px",
                  gap: "12px", padding: "10px 0",
                  alignItems: "baseline",
                }}
              >
                <span style={{ fontFamily: MONO, fontSize: "12px", color: "rgba(255,255,255,0.55)" }}>
                  {s.top_code}
                </span>
                <span style={{ fontFamily: FONT, fontSize: "13px", color: "rgba(255,255,255,0.78)" }}>
                  {s.top_title}
                </span>
                <span style={{ fontFamily: FONT, fontSize: "13px", color: "rgba(255,255,255,0.6)" }}>
                  {s.award_level}
                </span>
                <span style={{ fontFamily: FONT, fontSize: "13px", color: "rgba(255,255,255,0.7)", textAlign: "right", fontVariantNumeric: "tabular-nums" }}>
                  {s.annual_projected_supply.toFixed(1)}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Workforce gap visualization */}
      <WorkforceGapVisualization
        totalDemand={totalDemand}
        totalSupply={totalSupply}
        gap={gap}
        brandColor={brandColor}
      />

      {/* Sources — quiet trailer, four institutional authorities,
          read as attribution rather than emphasis. */}
      {sources && (
        <div style={{
          marginTop: "28px",
          display: "flex", alignItems: "baseline", gap: "12px",
          fontFamily: FONT, fontSize: "11px",
          color: "rgba(255,255,255,0.45)", lineHeight: 1.6,
        }}>
          <span style={{
            fontSize: "10px", fontWeight: 600, letterSpacing: "0.1em",
            textTransform: "uppercase", color: "rgba(255,255,255,0.5)",
            flexShrink: 0,
          }}>
            Sources
          </span>
          <span>Centers of Excellence for Labor Market Research, California Community Colleges Chancellor&rsquo;s Office, Bureau of Labor Statistics, National Center for Education Statistics.</span>
        </div>
      )}
    </Section>
  );
}

/* ── Workforce Gap visualization ──────────────────────────────────────── */
//
// Two horizontal bars of equal lane length: the Openings lane is rendered
// at full width (the demand reference); the Supply lane fills proportionally
// within the same lane width. The gap callout overlays the supply terminus,
// making the integrative figure visually unmistakable.
//
// Surplus case (gap < 0): supply visually exceeds the demand reference. We
// clamp the supply width to 100% so layout stays stable, and surface the
// negative gap as a neutral text callout — the artifact still answers
// "what's the gap?" honestly.

function WorkforceGapVisualization({
  totalDemand, totalSupply, gap, brandColor,
}: {
  totalDemand: number;
  totalSupply: number;
  gap: number;
  brandColor: string;
}) {
  // Bar widths as percentages of the lane.
  const supplyPct = totalDemand > 0
    ? Math.min(100, (totalSupply / totalDemand) * 100)
    : (totalSupply > 0 ? 100 : 0);
  const surplus = gap < 0;
  const gapDisplay = `${gap >= 0 ? "+" : "−"}${Math.abs(Math.round(gap)).toLocaleString()}`;

  // Shared grid template — label column / bar lane / value column. The gap
  // underline + callout below align with the supply lane by reusing it.
  const grid = "80px 1fr 70px";

  return (
    <div style={{ marginTop: "20px" }}>
      {/* Openings row — full-width neutral bar, the demand reference. */}
      <div style={{
        display: "grid", gridTemplateColumns: grid,
        alignItems: "center", gap: "12px", marginBottom: "8px",
      }}>
        <span style={{
          fontFamily: FONT, fontSize: "10px", fontWeight: 600,
          letterSpacing: "0.1em", textTransform: "uppercase",
          color: "rgba(255,255,255,0.45)",
        }}>
          Openings
        </span>
        <div style={{
          position: "relative", height: "16px",
          background: "rgba(255,255,255,0.04)", borderRadius: "4px",
          overflow: "hidden",
        }}>
          <div style={{
            position: "absolute", inset: 0,
            background: "rgba(255,255,255,0.18)", borderRadius: "4px",
          }} />
        </div>
        <span style={{
          fontFamily: FONT, fontSize: "13px", fontWeight: 500,
          color: "rgba(255,255,255,0.78)", textAlign: "right",
          fontVariantNumeric: "tabular-nums",
        }}>
          {totalDemand.toLocaleString()}
        </span>
      </div>

      {/* Supply row — brand-tinted bar with soft glow. */}
      <div style={{
        display: "grid", gridTemplateColumns: grid,
        alignItems: "center", gap: "12px",
      }}>
        <span style={{
          fontFamily: FONT, fontSize: "10px", fontWeight: 600,
          letterSpacing: "0.1em", textTransform: "uppercase",
          color: `${brandColor}cc`,
        }}>
          Supply
        </span>
        <div style={{
          position: "relative", height: "16px",
          background: "rgba(255,255,255,0.04)", borderRadius: "4px",
          overflow: "hidden",
        }}>
          <div style={{
            position: "absolute", top: 0, left: 0, bottom: 0,
            width: `${supplyPct}%`,
            background: brandColor,
            borderRadius: supplyPct >= 100 ? "4px" : "4px 0 0 4px",
            boxShadow: `0 0 12px ${brandColor}30`,
            transition: "width 0.4s ease-out",
          }} />
        </div>
        <span style={{
          fontFamily: FONT, fontSize: "13px", fontWeight: 700,
          color: brandColor, textAlign: "right",
          fontVariantNumeric: "tabular-nums",
        }}>
          {Math.round(totalSupply).toLocaleString()}
        </span>
      </div>

      {/* Gap underline + callout — anchored to the gap region (left:
          supplyPct% to right: 0). The 2px brand-tinted line marks the
          unmet portion of the demand lane; the WORKFORCE GAP callout
          sits centered beneath it. Surplus and full-coverage cases fall
          through to the neutral text fallback below. */}
      {!surplus && supplyPct < 100 && (
        <div style={{
          display: "grid", gridTemplateColumns: grid,
          gap: "12px", marginTop: "6px",
        }}>
          <span />
          <div style={{ position: "relative", minHeight: "60px" }}>
            <div style={{
              position: "absolute",
              left: `${supplyPct}%`,
              right: 0,
              top: 0,
              display: "flex", flexDirection: "column", alignItems: "center",
            }}>
              <div style={{
                width: "100%", height: "2px",
                background: `${brandColor}40`, borderRadius: "1px",
              }} />
              <div style={{ marginTop: "8px", textAlign: "center" }}>
                <div style={{
                  fontFamily: FONT, fontSize: "10px", fontWeight: 600,
                  letterSpacing: "0.12em", textTransform: "uppercase",
                  color: `${brandColor}cc`,
                  marginBottom: "2px",
                }}>
                  Workforce Gap
                </div>
                <div style={{
                  fontFamily: FONT, fontSize: "20px", fontWeight: 700,
                  color: brandColor,
                  filter: `drop-shadow(0 0 10px ${brandColor}50)`,
                  lineHeight: 1, fontVariantNumeric: "tabular-nums",
                }}>
                  {gapDisplay}
                </div>
              </div>
            </div>
          </div>
          <span />
        </div>
      )}

      {(surplus || supplyPct >= 100) && (
        <div style={{
          marginTop: "14px", paddingTop: "10px",
          borderTop: "1px solid rgba(255,255,255,0.06)",
          fontFamily: FONT, fontSize: "12px",
          color: "rgba(255,255,255,0.55)",
          textAlign: "center", fontVariantNumeric: "tabular-nums",
        }}>
          Workforce gap:{" "}
          <span style={{ fontWeight: 600, color: "rgba(255,255,255,0.75)" }}>
            {gapDisplay}
          </span>
          {surplus && (
            <span style={{ marginLeft: "8px", color: "rgba(255,255,255,0.4)", fontStyle: "italic" }}>
              (supply exceeds demand)
            </span>
          )}
        </div>
      )}
    </div>
  );
}

/* ── Partnership Opportunity employer row ─────────────────────────────── */

function PartnerEmployerRow({
  emp, index: _index, brandColor,
}: {
  emp: ApiPartnershipOpportunityEmployer;
  index: number;
  brandColor: string;
}) {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div>
      <button
        onClick={() => setIsOpen((o) => !o)}
        style={{
          width: "100%", textAlign: "left",
          display: "flex", alignItems: "center", gap: "12px",
          padding: "12px 16px",
          background: isOpen ? "rgba(255,255,255,0.06)" : "rgba(255,255,255,0.03)",
          border: "none",
          borderBottom: "1px solid rgba(255,255,255,0.05)",
          cursor: "pointer", transition: "background 0.15s",
        }}
        onMouseEnter={(e) => { if (!isOpen) (e.currentTarget as HTMLElement).style.background = "rgba(255,255,255,0.05)"; }}
        onMouseLeave={(e) => { if (!isOpen) (e.currentTarget as HTMLElement).style.background = "rgba(255,255,255,0.03)"; }}
      >
        <svg width="10" height="10" viewBox="0 0 12 12" fill="none"
          style={{ transform: isOpen ? "rotate(90deg)" : "rotate(0deg)", transition: "transform 0.2s", flexShrink: 0 }}>
          <path d="M4 2l4 4-4 4" stroke="rgba(255,255,255,0.3)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
        <span style={{ fontFamily: FONT, fontSize: "13px", color: "rgba(255,255,255,0.82)", flex: 1 }}>
          {emp.name}
        </span>
        <span style={{ display: "inline-flex", alignItems: "baseline", gap: "8px", flexShrink: 0 }}>
          {emp.naics4 && (
            <span style={{ fontFamily: MONO, fontSize: "11px", color: "rgba(255,255,255,0.4)", whiteSpace: "nowrap" }}>
              NAICS {emp.naics4}
            </span>
          )}
          <span style={{ fontFamily: FONT, fontSize: "11px", color: "rgba(255,255,255,0.25)" }}>·</span>
          <span style={{
            fontFamily: FONT, fontSize: "12px",
            color: brandColor, opacity: 0.85,
            whiteSpace: "nowrap", minWidth: "110px", textAlign: "right",
          }}>
            {emp.industry_share != null ? `${emp.industry_share.toFixed(2)}% of industry` : "—"}
          </span>
        </span>
      </button>

      {isOpen && (
        <div style={{
          background: "rgba(255,255,255,0.025)",
          padding: "16px 20px 18px 38px",
          borderBottom: "1px solid rgba(255,255,255,0.04)",
          display: "flex", flexDirection: "column", gap: "14px",
        }}>
          {emp.naics4 && (
            <div style={{ display: "flex", alignItems: "baseline", gap: "10px", flexWrap: "wrap" }}>
              <span style={{ fontFamily: MONO, fontSize: "11px", fontWeight: 500, letterSpacing: "0.05em", color: "rgba(255,255,255,0.4)", fontVariantNumeric: "tabular-nums" }}>
                NAICS {emp.naics4}
              </span>
              {emp.naics_title && (
                <>
                  <span style={{ fontFamily: FONT, fontSize: "11px", color: "rgba(255,255,255,0.3)" }}>·</span>
                  <span style={{ fontFamily: FONT, fontSize: "11px", color: "rgba(255,255,255,0.7)" }}>
                    {emp.naics_title}
                  </span>
                </>
              )}
            </div>
          )}

          {emp.description && (
            <div>
              <span style={{
                fontFamily: FONT, fontSize: "10px", fontWeight: 600,
                letterSpacing: "0.1em", textTransform: "uppercase",
                color: brandColor, opacity: 0.7,
                display: "block", marginBottom: "8px",
              }}>
                Description
              </span>
              <p style={{ fontFamily: FONT, fontSize: "12px", color: "rgba(255,255,255,0.65)", lineHeight: 1.6, margin: 0 }}>
                {emp.description}
              </p>
            </div>
          )}

          {emp.website && (
            <a
              href={emp.website}
              target="_blank"
              rel="noopener noreferrer"
              style={{
                display: "inline-flex", alignItems: "center", gap: "6px",
                padding: "5px 12px", borderRadius: "100px",
                fontFamily: FONT, fontSize: "11px", fontWeight: 600,
                letterSpacing: "0.07em", textTransform: "uppercase",
                color: "rgba(255,255,255,0.55)",
                background: "transparent",
                border: "1px solid rgba(255,255,255,0.14)",
                textDecoration: "none",
                width: "fit-content",
                transition: "border-color 0.15s, color 0.15s",
              }}
              onMouseEnter={(e) => {
                const el = e.currentTarget as HTMLElement;
                el.style.borderColor = `${brandColor}66`;
                el.style.color = brandColor;
              }}
              onMouseLeave={(e) => {
                const el = e.currentTarget as HTMLElement;
                el.style.borderColor = "rgba(255,255,255,0.14)";
                el.style.color = "rgba(255,255,255,0.55)";
              }}
              onClick={(e) => e.stopPropagation()}
            >
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" style={{ stroke: "currentColor" }} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="12" cy="12" r="10" /><path d="M2 12h20" /><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z" />
              </svg>
              Employer Home Page
            </a>
          )}

        </div>
      )}
    </div>
  );
}

/* ── Section primitives ───────────────────────────────────────────────── */

function ColHead({ brandColor, align, children }: {
  brandColor: string;
  align?: "left" | "right";
  children: React.ReactNode;
}) {
  return (
    <span style={{
      fontFamily: FONT, fontSize: "10px", fontWeight: 600,
      letterSpacing: "0.08em", textTransform: "uppercase",
      color: brandColor, opacity: 0.55,
      textAlign: align ?? "left",
    }}>
      {children}
    </span>
  );
}

