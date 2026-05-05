import { API_BASE } from "@/api";

export type ApiEmployerMatch = {
  name: string;
  sector: string | null;
  swp_sectors: string[];
  priority_sectors_matched: string[];
  description: string | null;
  website: string | null;
  occupations: string[];
  aligned_course_count: number;
};

export type ApiAlignedCourse = {
  code: string;
  name: string;
  department: string;
  via_top: string | null;
};

export type ApiTopAlignmentGroup = {
  top_code: string;
  top_title: string;
  courses: ApiAlignedCourse[];
};

export type ApiEmployerDetail = {
  name: string;
  sector: string | null;
  swp_sectors: string[];
  priority_sectors_matched: string[];
  description: string | null;
  website: string | null;
  naics4: string | null;
  naics_title: string | null;
  regions: string[];
  occupations: Array<{
    title: string;
    soc_code: string;
    description: string | null;
    annual_wage: number | null;
    aligned_top_groups: ApiTopAlignmentGroup[];
    aligned_course_count: number;
    aligned_program_area_count: number;
    industry_share: number | null;
  }>;
};

export type EmployerQueryResponse = {
  employers: ApiEmployerMatch[];
  message: string;
  cypher: string | null;
};

export async function getEmployers(college: string): Promise<ApiEmployerMatch[]> {
  const res = await fetch(`${API_BASE}/employers/?college=${encodeURIComponent(college)}`);
  if (!res.ok) throw new Error("Failed to fetch employers");
  return res.json();
}

export async function getEmployerDetail(name: string, college: string): Promise<ApiEmployerDetail> {
  const res = await fetch(`${API_BASE}/employers/${encodeURIComponent(name)}?college=${encodeURIComponent(college)}`);
  if (!res.ok) throw new Error("Failed to fetch employer detail");
  return res.json();
}

export async function queryEmployers(query: string, college: string): Promise<EmployerQueryResponse> {
  const res = await fetch(`${API_BASE}/employers/query`, {
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
