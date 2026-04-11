import { API_BASE } from "@/api";

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

export type CourseQueryResponse = {
  courses: ApiCourseSummary[];
  message: string;
  cypher: string | null;
};

export async function getDepartments(college: string): Promise<ApiDepartmentSummary[]> {
  const res = await fetch(`${API_BASE}/courses/departments?college=${encodeURIComponent(college)}`);
  if (!res.ok) throw new Error("Failed to fetch departments");
  return res.json();
}

export async function getCourses(department: string, college: string): Promise<ApiCourseSummary[]> {
  const res = await fetch(`${API_BASE}/courses/?department=${encodeURIComponent(department)}&college=${encodeURIComponent(college)}`);
  if (!res.ok) throw new Error("Failed to fetch courses");
  return res.json();
}

export async function queryCourses(query: string, college: string): Promise<CourseQueryResponse> {
  const res = await fetch(`${API_BASE}/courses/query`, {
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
