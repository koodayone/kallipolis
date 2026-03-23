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

export async function getInstitution(): Promise<InstitutionSummary> {
  const res = await fetch(`${BASE}/ontology/institution`);
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

export async function getStudents(): Promise<ApiStudentSummary[]> {
  const res = await fetch(`${BASE}/ontology/students`);
  if (!res.ok) throw new Error("Failed to fetch students");
  return res.json();
}

export async function getStudent(uuid: string): Promise<ApiStudentDetail> {
  const res = await fetch(`${BASE}/ontology/students/${uuid}`);
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
  learning_outcomes: string[];
  course_objectives: string[];
  skill_mappings: string[];
};

export async function getDepartments(): Promise<ApiDepartmentSummary[]> {
  const res = await fetch(`${BASE}/ontology/curricula/departments`);
  if (!res.ok) throw new Error("Failed to fetch departments");
  return res.json();
}

export async function getCourses(department: string): Promise<ApiCourseSummary[]> {
  const res = await fetch(`${BASE}/ontology/curricula/courses?department=${encodeURIComponent(department)}`);
  if (!res.ok) throw new Error("Failed to fetch courses");
  return res.json();
}
