import { API_BASE } from "@/api";

export type ApiPartnershipOpportunity = {
  name: string;
  sector: string | null;
  description: string | null;
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

// ── Proposal evidence types (also consumed by strong-workforce) ─────────────

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

export type ApiProposalJustification = {
  curriculum_composition: string;
  curriculum_evidence: ApiDepartmentEvidence[];
  student_composition: string;
  student_evidence: ApiStudentEvidence;
};

export type ApiAgendaTopic = {
  topic: string;
  rationale: string;
};

export type ApiTargetedProposal = {
  employer: string;
  sector: string | null;
  partnership_type: string;
  selected_occupation: string;
  selected_soc_code: string | null;
  core_skills: string[];
  gap_skill: string;
  regions: string[];
  opportunity: string;
  opportunity_evidence: ApiOccupationEvidence[];
  justification: ApiProposalJustification;
  roadmap: string;
  selected_occupations?: string[];
  advisory_thesis?: string;
  agenda_topics?: ApiAgendaTopic[];
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

export async function getEmployerOccupations(employer: string): Promise<{ occupations: Array<{ title: string; annual_wage: number | null }> }> {
  const res = await fetch(`${API_BASE}/partnerships/employer-occupations?employer=${encodeURIComponent(employer)}`);
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
    const detail = await res.text();
    throw new Error(detail || "Query failed");
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
  engagementType: string,
): Promise<void> {
  const res = await fetch(`${API_BASE}/partnerships/targeted/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ employer, college, engagement_type: engagementType }),
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
