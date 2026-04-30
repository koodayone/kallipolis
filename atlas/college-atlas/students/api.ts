import { API_BASE } from "@/api";

export type ApiStudentSummary = {
  uuid: string;
  primary_focus: string;
  courses_completed: number;
  gpa: number;
};

export type ApiStudentEnrollment = {
  course_code: string;
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

export type StudentQueryResponse = {
  students: ApiStudentSummary[];
  message: string;
  cypher: string | null;
};

export type StudentSummaryPage = {
  students: ApiStudentSummary[];
  total_count: number;
  has_more: boolean;
};

// Default page size the atlas requests on initial load. Generous enough
// that the browse and search views see most of the population without
// pagination controls; small enough to keep the JSON payload under 100KB
// even for the largest colleges (~14K students at Foothill).
export const STUDENTS_DEFAULT_LIMIT = 500;

export async function getStudents(
  college: string,
  limit: number = STUDENTS_DEFAULT_LIMIT,
  offset: number = 0,
): Promise<StudentSummaryPage> {
  const url = `${API_BASE}/students/?college=${encodeURIComponent(college)}&limit=${limit}&offset=${offset}`;
  const res = await fetch(url);
  if (!res.ok) throw new Error("Failed to fetch students");
  return res.json();
}

export async function getStudent(uuid: string, college: string): Promise<ApiStudentDetail> {
  const res = await fetch(`${API_BASE}/students/${uuid}?college=${encodeURIComponent(college)}`);
  if (!res.ok) throw new Error("Failed to fetch student");
  return res.json();
}

export async function queryStudents(query: string, college: string): Promise<StudentQueryResponse> {
  const res = await fetch(`${API_BASE}/students/query`, {
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
