const BASE =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export type CurriculumAlignment = {
  program_name: string;
  curriculum_name: string;
  relevance_note: string;
};

export type PartnershipProposal = {
  employer_or_sector: string;
  curriculum_alignment: CurriculumAlignment[];
  student_population_relevance: string;
  partnership_type: string;
  rationale: string;
};

export type ProposalList = {
  proposals: PartnershipProposal[];
};

export type ProgramSummary = {
  program_name: string;
  curricula: string[];
};

export type InstitutionSummary = {
  institution_name: string;
  region: string;
  programs: ProgramSummary[];
};

export async function generatePartnerships(): Promise<ProposalList> {
  const res = await fetch(`${BASE}/workflows/partnerships`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
  });
  if (!res.ok) {
    const detail = await res.text();
    throw new Error(`Partnership generation failed: ${detail}`);
  }
  return res.json();
}

export async function streamPartnerships(
  onProposal: (proposal: PartnershipProposal) => void,
  onDone: () => void,
  onError: (error: string) => void,
): Promise<void> {
  const res = await fetch(`${BASE}/workflows/partnerships/stream`, {
    method: "POST",
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
          onProposal(json as PartnershipProposal);
        } catch {
          // Incomplete JSON line, skip
        }
      }
    }
  }
  onDone();
}

export async function getInstitution(institution: string): Promise<InstitutionSummary> {
  const res = await fetch(`${BASE}/ontology/institution?institution=${encodeURIComponent(institution)}`);
  if (!res.ok) throw new Error("Failed to fetch institution data");
  return res.json();
}

export type ApiStudentSummary = {
  uuid: string;
  primary_focus: string;
  courses_completed: number;
  gpa: number;
};

export type ApiStudentEnrollment = {
  course_name: string;
  department: string;
  grade: string;
  term: string;
  status: string;
};

export type ApiStudentDetail = {
  uuid: string;
  primary_focus: string;
  courses_completed: number;
  gpa: number;
  enrollments: ApiStudentEnrollment[];
  skills: string[];
};

export async function getStudents(institution: string): Promise<ApiStudentSummary[]> {
  const res = await fetch(`${BASE}/ontology/students?institution=${encodeURIComponent(institution)}`);
  if (!res.ok) throw new Error("Failed to fetch students");
  return res.json();
}

export async function getStudent(uuid: string, institution: string): Promise<ApiStudentDetail> {
  const res = await fetch(`${BASE}/ontology/students/${uuid}?institution=${encodeURIComponent(institution)}`);
  if (!res.ok) throw new Error("Failed to fetch student");
  return res.json();
}

export type ApiDepartmentSummary = {
  department: string;
  course_count: number;
};

export type ApiCourseSummary = {
  name: string;
  code: string;
  description: string;
  learning_outcomes: string[];
  course_objectives: string[];
  skill_mappings: string[];
};

export async function getDepartments(institution: string): Promise<ApiDepartmentSummary[]> {
  const res = await fetch(`${BASE}/ontology/curricula/departments?institution=${encodeURIComponent(institution)}`);
  if (!res.ok) throw new Error("Failed to fetch departments");
  return res.json();
}

export async function getCourses(department: string, institution: string): Promise<ApiCourseSummary[]> {
  const res = await fetch(`${BASE}/ontology/curricula/courses?department=${encodeURIComponent(department)}&institution=${encodeURIComponent(institution)}`);
  if (!res.ok) throw new Error("Failed to fetch courses");
  return res.json();
}
