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

// ── Curriculum Crosswalk pathway (TOP4 × CIP × SOC) ────────────────────────
//
// Powers the hero visualization at the bottom of the Curriculum Alignment
// section: a three-column flow showing the institutional pathway from
// program (TOP) through federal taxonomy (CIP) to occupation (SOC),
// with this college's coverage marked at the TOP layer and the active
// (lit) pathway marked at the CIP layer. SAM-filtered to occupational
// per CCCCO MIS Data Element Dictionary.

export type ApiCrosswalkTop = {
  code: string;                  // 6-digit TOP code, e.g., "070200"
  name: string;                  // 6-digit title, e.g., "Computer Information Systems"
  taught_at_college: boolean;    // true when ≥ 1 course at this college teaches this TOP
  cips: string[];                // CIP codes this TOP bridges to (filtered to those reaching the SOC)
};

export type ApiCrosswalkCip = {
  code: string;                  // e.g., "15.0507"
  title: string;                 // e.g., "Environmental/Environmental Engineering Technology"
  active: boolean;               // true when ≥ 1 taught TOP6 bridges to this CIP
};

export type ApiCurriculumCrosswalk = {
  tops: ApiCrosswalkTop[];
  cips: ApiCrosswalkCip[];
  n_taught: number;              // count of TOP6 codes the college teaches
  n_total: number;               // count of TOP6 codes in the global prep set
  coverage_pct: number;          // 100 * n_taught / n_total, rounded to 1 decimal
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
  // Two-valued alignment tag driving the row's visual treatment:
  //   "aligned": college has at least one PREPARES_FOR-aligned course
  //              for this SOC. Renders as a normal navigable row.
  //   "gap":     SOC is regionally demanded but the college has NO
  //              aligned curriculum (course_count = 0). Renders dimmed
  //              with a "no current pathway" label — surfaces a
  //              consortia-level workforce opportunity to discuss.
  // Default "aligned" when absent (backward-compat with older caches).
  alignment_status?: "aligned" | "gap";
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
  curriculum_crosswalk: ApiCurriculumCrosswalk;
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
  sector?: string,
): Promise<ApiOpportunityReport> {
  // `sector` is the click-context sector the user navigated from. When
  // a SOC belongs to multiple PCAH sectors, this preserves the user's
  // mental model — the report renders under the sector they clicked
  // from rather than re-resolving alphabetically. The backend
  // validates the value against the SOC's actual PCAH sectors and
  // ignores it if invalid.
  const params = new URLSearchParams({ college });
  if (sector) params.set("sector", sector);
  const res = await fetch(
    `${API_BASE}/partnerships/opportunity/${encodeURIComponent(socCode)}?${params.toString()}`,
  );
  if (!res.ok) throw new Error("Failed to fetch partnership opportunity report");
  return res.json();
}
