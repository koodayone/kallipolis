import { API_BASE } from "@/api";
import type {
  ApiOccupationEvidence,
  ApiDepartmentEvidence,
  ApiStudentEvidence,
} from "@/college-atlas/partnerships/api";

export type ApiLmiOccupation = {
  soc_code: string;
  title: string;
  annual_wage: number | null;
  employment: number | null;
  growth_rate: number | null;
  annual_openings: number | null;
  education_level: string | null;
  region: string;
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

export type ApiLmiContext = {
  occupations: ApiLmiOccupation[];
  supply_estimates: ApiSupplyEstimate[];
  department_enrollments: ApiDepartmentEnrollment[];
  total_demand: number;
  total_supply: number;
  gap: number;
  gap_eligible: boolean;
};

export type ApiSwpSection = {
  key: string;
  title: string;
  content: string;
  char_limit: number | null;
};

export type ApiSwpProject = {
  employer: string;
  college: string;
  partnership_type: string;
  sections: ApiSwpSection[];
  lmi_context: ApiLmiContext;
  goal: string;
  metrics: string[];
};

export type SwpProjectRequest = {
  employer: string;
  college: string;
  partnership_type: string;
  selected_occupation: string;
  selected_soc_code: string | null;
  core_skills: string[];
  gap_skill: string;
  opportunity: string;
  opportunity_evidence: ApiOccupationEvidence[];
  curriculum_composition: string;
  curriculum_evidence: ApiDepartmentEvidence[];
  student_composition: string;
  student_evidence: ApiStudentEvidence;
  roadmap: string;
  goal: string;
  metrics: string[];
  apprenticeship: boolean;
  work_based_learning: boolean;
};

export async function streamSwpProject(
  req: SwpProjectRequest,
  onLmi: (lmi: ApiLmiContext) => void,
  onSection: (section: ApiSwpSection) => void,
  onDone: () => void,
  onError: (error: string) => void,
): Promise<void> {
  const res = await fetch(`${API_BASE}/strong-workforce/project/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req),
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
          const parsed = JSON.parse(line.slice(6));
          if (parsed.done) { onDone(); return; }
          if (parsed.error) { onError(parsed.error); return; }
          if (parsed.type === "lmi") {
            onLmi(parsed.lmi_context as ApiLmiContext);
          } else if (parsed.type === "section") {
            onSection(parsed.section as ApiSwpSection);
          }
        } catch {
          // Incomplete JSON line, skip
        }
      }
    }
  }
  onDone();
}
