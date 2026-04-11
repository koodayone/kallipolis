import { API_BASE } from "@/api";

export type ApiEmployerMatch = {
  name: string;
  sector: string | null;
  description: string | null;
  website: string | null;
  occupations: string[];
  matching_skills: number;
  skills: string[];
};

export type ApiEmployerDetail = {
  name: string;
  sector: string | null;
  description: string | null;
  website: string | null;
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
    const detail = await res.text();
    throw new Error(detail || "Query failed");
  }
  return res.json();
}
