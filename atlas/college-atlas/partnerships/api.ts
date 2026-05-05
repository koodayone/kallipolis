import { API_BASE } from "@/api";

// ── Evidence types (composed into OpportunityReport) ───────────────────────

export type ApiOccupationEvidence = {
  title: string;
  soc_code: string | null;
  annual_wage: number | null;
  employment: number | null;
  annual_openings: number | null;
  growth_rate: number | null;
  // CIP codes the BLS/NCES CIP-SOC crosswalk maps to this SOC. Surfaces
  // the second link in the empirical chain (SOC ↔ CIP) so the atlas
  // rendering can attribute the institutional pathway visibly.
  cip_codes?: string[];
};

export type ApiCourseEvidence = {
  code: string;
  name: string;
  description: string;
  learning_outcomes: string[];
  // The TOP6 code this course is institutionally tagged with in the
  // Master Course File. Used by the atlas to render per-course
  // institutional attribution alongside the course code.
  top_code?: string | null;
};

export type ApiDepartmentEvidence = {
  department: string;
  courses: ApiCourseEvidence[];
  // The TOP6 codes this department's PREPARES_FOR-aligned courses
  // route through (typically one TOP6 per department; some span
  // several). Drives the per-department source attribution caption.
  via_top?: string[];
  // The CIPs that mediate the chain Course → TOP6 → CIP → SOC.
  via_cip?: string[];
};

export type ApiStudentEnrollmentEvidence = {
  code: string;
  name: string;
  grade: string;
  term: string;
};

export type ApiStudentSummaryEvidence = {
  uuid: string;
  display_number: number;
  primary_focus: string;
  courses_completed: number;
  gpa: number;
  enrollments: ApiStudentEnrollmentEvidence[];
};

export type ApiStudentEvidence = {
  total_in_program: number;
  total_in_aligned_departments: number;
  top_students: ApiStudentSummaryEvidence[];
};

export type ApiSupplyEstimate = {
  top_code: string;
  top_title: string;
  award_level: string;
  annual_projected_supply: number;
};

export type ApiDepartmentEnrollment = {
  department: string;
  student_count: number;
};

export type ApiInstitutionalSources = {
  coe_region: string;
  coe_region_display: string;
  coe_demand_publication: string;
  coe_supply_publication: string;
  top_cip_crosswalk_source: string;
  cip_soc_crosswalk_source: string;
};

export type ApiSwpEvidence = {
  occupations: ApiOccupationEvidence[];
  supply_estimates: ApiSupplyEstimate[];
  department_enrollments: ApiDepartmentEnrollment[];
  total_demand: number;
  total_supply: number;
  gap: number;
  coe_region: string;
  // Institutional attribution: named external publications and
  // crosswalks that author every categorical claim in the artifact.
  // Drives the source caption in the atlas SWP Evidence section.
  sources?: ApiInstitutionalSources;
};

// ── Occupation-centric Partnerships surfaces ───────────────────────────────

export type ApiOpportunityRow = {
  soc_code: string;
  title: string;
  annual_openings: number | null;
  annual_wage: number | null;
  growth_rate: number | null;
  course_count: number;
  student_count: number;
  employer_count: number;
  // Regional annual openings minus the college's TOP-program projected
  // supply. Drives the per-row gap chip and the within-sector sort.
  // Negative values indicate the college's pipeline outpaces regional
  // demand for the SOC.
  gap: number | null;
};

export type ApiSectorEntry = {
  sector: string;
  is_priority: boolean;
  occupations: ApiOpportunityRow[];
};

export type ApiSectorIndex = {
  college: string;
  sectors: ApiSectorEntry[];
};

export type ApiPartnershipOpportunityEmployer = {
  name: string;
  sector: string | null;
  swp_sectors: string[];
  description: string | null;
  website: string | null;
  naics4: string | null;
  naics_title: string | null;
  industry_share: number | null;
  aligned_course_count: number;
};

export type ApiOpportunityReport = {
  college: string;
  sector: string | null;
  // True when the sector is a Strong Workforce Program priority for the
  // college's COE region (per regional consortium designation in PCAH).
  // Drives the "REGIONAL PRIORITY" tag in the report header.
  is_sector_priority: boolean;
  soc_code: string;
  soc_title: string;
  description: string | null;
  regions: string[];
  executive_summary: string;
  occupational_demand: string;
  curriculum_alignment: string;
  student_impact: string;
  partnership_opportunities_narrative: string;
  opportunity_evidence: ApiOccupationEvidence[];
  curriculum_evidence: ApiDepartmentEvidence[];
  student_evidence: ApiStudentEvidence;
  swp_evidence: ApiSwpEvidence;
  partnership_opportunities: ApiPartnershipOpportunityEmployer[];
};

export async function getPartnershipSectors(college: string): Promise<ApiSectorIndex> {
  const res = await fetch(`${API_BASE}/partnerships/sectors?college=${encodeURIComponent(college)}`);
  if (!res.ok) throw new Error("Failed to fetch partnership sectors");
  return res.json();
}

export async function getPartnershipOpportunity(
  socCode: string,
  college: string,
): Promise<ApiOpportunityReport> {
  const res = await fetch(
    `${API_BASE}/partnerships/opportunity/${encodeURIComponent(socCode)}?college=${encodeURIComponent(college)}`,
  );
  if (!res.ok) throw new Error("Failed to fetch partnership opportunity report");
  return res.json();
}
