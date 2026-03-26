const BASE =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export type CurriculumAlignment = {
  department_name: string;
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

export type CollegeDepartment = {
  department_name: string;
  curricula: string[];
};

export type CollegeSummary = {
  college_name: string;
  region: string;
  departments: CollegeDepartment[];
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

export async function getCollege(college: string): Promise<CollegeSummary> {
  const res = await fetch(`${BASE}/ontology/college?college=${encodeURIComponent(college)}`);
  if (!res.ok) throw new Error("Failed to fetch college data");
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

export async function getStudents(college: string): Promise<ApiStudentSummary[]> {
  const res = await fetch(`${BASE}/ontology/students?college=${encodeURIComponent(college)}`);
  if (!res.ok) throw new Error("Failed to fetch students");
  return res.json();
}

export async function getStudent(uuid: string, college: string): Promise<ApiStudentDetail> {
  const res = await fetch(`${BASE}/ontology/students/${uuid}?college=${encodeURIComponent(college)}`);
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

export async function getDepartments(college: string): Promise<ApiDepartmentSummary[]> {
  const res = await fetch(`${BASE}/ontology/courses/departments?college=${encodeURIComponent(college)}`);
  if (!res.ok) throw new Error("Failed to fetch departments");
  return res.json();
}

export async function getCourses(department: string, college: string): Promise<ApiCourseSummary[]> {
  const res = await fetch(`${BASE}/ontology/courses/list?department=${encodeURIComponent(department)}&college=${encodeURIComponent(college)}`);
  if (!res.ok) throw new Error("Failed to fetch courses");
  return res.json();
}

// ── Labor Market ────────────────────────────────────────────────────────────

export type ApiOccupationMatch = {
  soc_code: string;
  title: string;
  description: string | null;
  annual_wage: number | null;
  employment: number | null;
  matching_skills: number;
  skills: string[];
};

export type ApiRegionOverview = {
  region: string;
  occupations: ApiOccupationMatch[];
};

export type ApiLaborMarketOverview = {
  college: string;
  regions: ApiRegionOverview[];
};

export type ApiSkillDetail = {
  skill: string;
  developed: boolean;
  courses: Array<{ code: string; name: string }>;
};

export type ApiOccupationDetail = {
  soc_code: string;
  title: string;
  description: string | null;
  annual_wage: number | null;
  skills: ApiSkillDetail[];
  regions: Array<{ region: string; employment: number }>;
};

export async function getLaborMarketOverview(college: string): Promise<ApiLaborMarketOverview> {
  const res = await fetch(`${BASE}/labor-market/overview?college=${encodeURIComponent(college)}`);
  if (!res.ok) throw new Error("Failed to fetch labor market data");
  return res.json();
}

export async function getOccupationDetail(socCode: string, college: string): Promise<ApiOccupationDetail> {
  const res = await fetch(`${BASE}/labor-market/occupation/${encodeURIComponent(socCode)}?college=${encodeURIComponent(college)}`);
  if (!res.ok) throw new Error("Failed to fetch occupation detail");
  return res.json();
}

// ── Employers ───────────────────────────────────────────────────────────────

export type ApiEmployerMatch = {
  name: string;
  sector: string | null;
  occupations: string[];
  matching_skills: number;
  skills: string[];
};

export type ApiEmployerDetail = {
  name: string;
  sector: string | null;
  regions: string[];
  occupations: Array<{
    title: string;
    soc_code: string;
    annual_wage: number | null;
    skills: Array<{
      skill: string;
      developed: boolean;
      courses: Array<{ code: string; name: string }>;
    }>;
  }>;
};

export async function getEmployers(college: string): Promise<ApiEmployerMatch[]> {
  const res = await fetch(`${BASE}/labor-market/employers?college=${encodeURIComponent(college)}`);
  if (!res.ok) throw new Error("Failed to fetch employers");
  return res.json();
}

export async function getEmployerDetail(name: string, college: string): Promise<ApiEmployerDetail> {
  const res = await fetch(`${BASE}/labor-market/employer/${encodeURIComponent(name)}?college=${encodeURIComponent(college)}`);
  if (!res.ok) throw new Error("Failed to fetch employer detail");
  return res.json();
}
