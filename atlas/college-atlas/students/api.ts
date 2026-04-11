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

export async function getStudents(college: string): Promise<ApiStudentSummary[]> {
  const res = await fetch(`${API_BASE}/students?college=${encodeURIComponent(college)}`);
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
    const detail = await res.text();
    throw new Error(detail || "Query failed");
  }
  return res.json();
}
