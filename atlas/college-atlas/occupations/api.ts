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
  aligned_course_count: number;
  aligned_department_count: number;
  // "aligned" — college has at least one PREPARES_FOR-aligned course
  // "gap"     — SOC is regionally demanded and CTE-reachable, but no
  //             aligned curriculum at this college. Drives row dim +
  //             "no curriculum at <college>" detail message. Optional
  //             for backward-compat with older API responses.
  alignment_status?: "aligned" | "gap";
};

export type ApiRegionOverview = {
  region: string;
  occupations: ApiOccupationMatch[];
};

export type ApiLaborMarketOverview = {
  college: string;
  regions: ApiRegionOverview[];
};

export type ApiCourseAlignment = {
  code: string;
  name: string;
  department: string;
  via_top: string | null;
};

export type ApiCipMatch = {
  code: string;
  title: string;
};

export type ApiTopAlignmentGroup = {
  top_code: string;
  top_title: string;
  // True if the college teaches at least one PREPARES_FOR course under
  // this TOP6 for this SOC. False = system pathway TOP, not currently
  // taught at this college (untaught — curriculum-development surface).
  // Optional for backward-compat with older API responses; defaults to
  // taught in the renderer.
  taught?: boolean;
  courses: ApiCourseAlignment[];
  // Federal CIPs (NCES CIP-SOC) bridging this TOP6 to the SOC. Drives
  // the per-TOP CIP rail. Optional for backward-compat.
  cips?: ApiCipMatch[];
};

export type ApiOccupationDetail = {
  soc_code: string;
  title: string;
  description: string | null;
  education_level: string | null;
  aligned_top_groups: ApiTopAlignmentGroup[];
  aligned_course_count: number;
  aligned_program_area_count: number;
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
    const body = await res.json().catch(() => null);
    throw new Error(body?.detail || "Query failed");
  }
  return res.json();
}
