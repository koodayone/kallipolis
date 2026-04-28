import { API_BASE } from "@/api";

export type ApiPartnershipOpportunity = {
  name: string;
  sector: string | null;
  // Multi-sector tagging used for grouping in the partnerships Build mode.
  // priority_sectors_matched is the intersection with the college's region's
  // priority sectors — flags the green dot on the sector header.
  swp_sectors: string[];
  priority_sectors_matched: string[];
  description: string | null;
  // Employer homepage URL — surfaced in the partnership picker.
  website: string | null;
  alignment_score: number;
  gap_count: number;
  pipeline_size: number | null;
  top_occupation: string | null;
  top_wage: number | null;
  aligned_skills: string[];
  gap_skills: string[];
};

export type ApiPartnershipLandscape = {
  college: string;
  opportunities: ApiPartnershipOpportunity[];
};

export type PartnershipQueryResponse = {
  opportunities: ApiPartnershipOpportunity[];
  message: string;
  cypher: string | null;
};

// ── Proposal evidence types ────────────────────────────────────────────────

export type ApiOccupationEvidence = {
  title: string;
  soc_code: string | null;
  annual_wage: number | null;
  employment: number | null;
  annual_openings: number | null;
  growth_rate: number | null;
};

export type ApiCourseEvidence = {
  code: string;
  name: string;
  description: string;
  learning_outcomes: string[];
  skills: string[];
};

export type ApiDepartmentEvidence = {
  department: string;
  courses: ApiCourseEvidence[];
  aligned_skills: string[];
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
  matching_skills: number;
  enrollments: ApiStudentEnrollmentEvidence[];
  relevant_skills: string[];
};

export type ApiStudentEvidence = {
  total_in_program: number;
  with_all_core_skills: number;
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

export type ApiSwpEvidence = {
  occupations: ApiOccupationEvidence[];
  supply_estimates: ApiSupplyEstimate[];
  department_enrollments: ApiDepartmentEnrollment[];
  total_demand: number;
  total_supply: number;
  gap: number;
  coe_region: string;
};

export type ApiTargetedProposal = {
  employer: string;
  sector: string | null;
  selected_occupation: string;
  selected_soc_code: string | null;
  core_skills: string[];
  regions: string[];
  // Four narrative sections
  executive_summary: string;
  occupational_demand: string;
  curriculum_alignment: string;
  student_impact: string;
  // Evidence blocks
  opportunity_evidence: ApiOccupationEvidence[];
  curriculum_evidence: ApiDepartmentEvidence[];
  student_evidence: ApiStudentEvidence;
  swp_evidence: ApiSwpEvidence;
};

// ── Landscape endpoints ────────────────────────────────────────────────────

export async function getPartnershipLandscape(college: string): Promise<ApiPartnershipLandscape> {
  const res = await fetch(`${API_BASE}/partnerships/landscape?college=${encodeURIComponent(college)}`);
  if (!res.ok) throw new Error("Failed to fetch partnership landscape");
  return res.json();
}

export async function getEmployerPipeline(employer: string, college: string): Promise<{ pipeline_size: number }> {
  const res = await fetch(`${API_BASE}/partnerships/employer-pipeline?employer=${encodeURIComponent(employer)}&college=${encodeURIComponent(college)}`);
  if (!res.ok) throw new Error("Failed to fetch pipeline data");
  return res.json();
}

// Occupation card in the picker: title, SOC, regional demand fields, plus
// the curriculum-alignment signal so the coordinator can see at-a-glance how
// well the college's curriculum already covers each role's required skills.
export type ApiEmployerOccupation = {
  title: string;
  soc_code: string;
  annual_wage: number | null;
  annual_openings: number | null;
  growth_rate: number | null;
  core_skills_developed_count: number;
  core_skills_total_count: number;
  course_count: number;
};

export type ApiEmployerOccupationsResponse = {
  coe_region: string;
  occupations: ApiEmployerOccupation[];
};

export async function getEmployerOccupations(
  employer: string,
  college: string,
): Promise<ApiEmployerOccupationsResponse> {
  const res = await fetch(
    `${API_BASE}/partnerships/employer-occupations?employer=${encodeURIComponent(employer)}&college=${encodeURIComponent(college)}`,
  );
  if (!res.ok) throw new Error("Failed to fetch employer occupations");
  return res.json();
}

export async function queryPartnerships(query: string, college: string): Promise<PartnershipQueryResponse> {
  const res = await fetch(`${API_BASE}/partnerships/query`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query, college }),
  });
  if (!res.ok) {
    const body = await res.json().catch(() => null);
    throw new Error(body?.detail || "Query failed");
  }
  return res.json();
}

// ── Targeted proposal stream ───────────────────────────────────────────────

export async function streamTargetedProposal(
  employer: string,
  college: string,
  onProposal: (proposal: ApiTargetedProposal) => void,
  onDone: () => void,
  onError: (error: string) => void,
  selectedOccupationSoc?: string,
): Promise<void> {
  // Only include the SOC field when the coordinator has chosen one. Sending
  // `selected_occupation_soc: null` would defeat the optional-Pydantic
  // pattern; omitting the field is what triggers the legacy auto-selection
  // path on the backend.
  const body: Record<string, string> = { employer, college };
  if (selectedOccupationSoc) {
    body.selected_occupation_soc = selectedOccupationSoc;
  }
  const res = await fetch(`${API_BASE}/partnerships/targeted/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    onError(await res.text());
    return;
  }
  const reader = res.body!.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });

    const lines = buffer.split("\n");
    buffer = lines.pop() || "";
    for (const line of lines) {
      if (line.startsWith("data: ")) {
        try {
          const json = JSON.parse(line.slice(6));
          if (json.done) { onDone(); return; }
          if (json.error) { onError(json.error); return; }
          onProposal(json as ApiTargetedProposal);
        } catch {
          // Incomplete JSON line, skip
        }
      }
    }
  }
  onDone();
}
