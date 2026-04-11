import { API_BASE } from "@/api";

export type ApiOccupationMatch = {
  soc_code: string;
  title: string;
  description: string | null;
  annual_wage: number | null;
  employment: number | null;
  growth_rate: number | null;
  annual_openings: number | null;
  education_level: string | null;
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
  skills: ApiSkillDetail[];
  regions: Array<{
    region: string;
    employment: number;
    annual_wage: number | null;
    growth_rate: number | null;
    annual_openings: number | null;
    education_level: string | null;
  }>;
};

export type OccupationQueryResponse = {
  occupations: ApiOccupationMatch[];
  message: string;
  cypher: string | null;
};

export async function getLaborMarketOverview(college: string): Promise<ApiLaborMarketOverview> {
  const res = await fetch(`${API_BASE}/occupations/overview?college=${encodeURIComponent(college)}`);
  if (!res.ok) throw new Error("Failed to fetch labor market data");
  return res.json();
}

export async function getOccupationDetail(socCode: string, college: string): Promise<ApiOccupationDetail> {
  const res = await fetch(`${API_BASE}/occupations/${encodeURIComponent(socCode)}?college=${encodeURIComponent(college)}`);
  if (!res.ok) throw new Error("Failed to fetch occupation detail");
  return res.json();
}

export async function queryOccupations(query: string, college: string): Promise<OccupationQueryResponse> {
  const res = await fetch(`${API_BASE}/occupations/query`, {
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
