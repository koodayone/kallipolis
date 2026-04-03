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

export type StudentQueryResponse = {
  students: ApiStudentSummary[];
  message: string;
  cypher: string | null;
};

export async function queryStudents(query: string, college: string): Promise<StudentQueryResponse> {
  const res = await fetch(`${BASE}/ontology/students/query`, {
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

export type CourseQueryResponse = {
  courses: ApiCourseSummary[];
  message: string;
  cypher: string | null;
};

export async function queryCourses(query: string, college: string): Promise<CourseQueryResponse> {
  const res = await fetch(`${BASE}/ontology/courses/query`, {
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

// ── Labor Market ────────────────────────────────────────────────────────────

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
  description: string | null;
  occupations: string[];
  matching_skills: number;
  skills: string[];
};

export type ApiEmployerDetail = {
  name: string;
  sector: string | null;
  description: string | null;
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

export async function getEmployerOccupations(employer: string): Promise<{ occupations: Array<{ title: string; annual_wage: number | null }> }> {
  const res = await fetch(`${BASE}/labor-market/partnership-landscape/occupations?employer=${encodeURIComponent(employer)}`);
  if (!res.ok) throw new Error("Failed to fetch employer occupations");
  return res.json();
}

export type EmployerQueryResponse = {
  employers: ApiEmployerMatch[];
  message: string;
  cypher: string | null;
};

export async function queryEmployers(query: string, college: string): Promise<EmployerQueryResponse> {
  const res = await fetch(`${BASE}/labor-market/employers/query`, {
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

export type OccupationQueryResponse = {
  occupations: ApiOccupationMatch[];
  message: string;
  cypher: string | null;
};

export async function queryOccupations(query: string, college: string): Promise<OccupationQueryResponse> {
  const res = await fetch(`${BASE}/labor-market/occupations/query`, {
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

// ── Partnership Landscape ──────────────────────────────────────────────────

export type ApiPartnershipOpportunity = {
  name: string;
  sector: string | null;
  description: string | null;
  alignment_score: number;
  gap_count: number;
  pipeline_size: number | null;
  top_occupation: string | null;
  top_wage: number | null;
  aligned_skills: string[];
  gap_skills: string[];
};

export type ApiPartnershipLandscape = {
  college: string;
  opportunities: ApiPartnershipOpportunity[];
};

export type PartnershipQueryResponse = {
  opportunities: ApiPartnershipOpportunity[];
  message: string;
  cypher: string | null;
};

export async function getPartnershipLandscape(college: string): Promise<ApiPartnershipLandscape> {
  const res = await fetch(`${BASE}/labor-market/partnership-landscape?college=${encodeURIComponent(college)}`);
  if (!res.ok) throw new Error("Failed to fetch partnership landscape");
  return res.json();
}

export async function getEmployerPipeline(employer: string, college: string): Promise<{ pipeline_size: number }> {
  const res = await fetch(`${BASE}/labor-market/partnership-landscape/pipeline?employer=${encodeURIComponent(employer)}&college=${encodeURIComponent(college)}`);
  if (!res.ok) throw new Error("Failed to fetch pipeline data");
  return res.json();
}

export async function queryPartnerships(query: string, college: string): Promise<PartnershipQueryResponse> {
  const res = await fetch(`${BASE}/labor-market/partnerships/query`, {
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

// ── Targeted Proposal ──────────────────────────────────────────────────────

export type ApiOccupationEvidence = {
  title: string;
  soc_code: string | null;
  annual_wage: number | null;
  employment: number | null;
  annual_openings: number | null;
  growth_rate: number | null;
};

export type ApiCourseEvidence = {
  code: string;
  name: string;
  skills: string[];
};

export type ApiDepartmentEvidence = {
  department: string;
  courses: ApiCourseEvidence[];
  aligned_skills: string[];
};

export type ApiStudentSummaryEvidence = {
  uuid: string;
  display_number: number;
  primary_focus: string;
  courses_completed: number;
  gpa: number;
  matching_skills: number;
};

export type ApiStudentEvidence = {
  total_students: number;
  students_with_3plus_courses: number;
  top_students: ApiStudentSummaryEvidence[];
};

export type ApiProposalJustification = {
  curriculum_composition: string;
  curriculum_evidence: ApiDepartmentEvidence[];
  student_composition: string;
  student_evidence: ApiStudentEvidence;
};

export type ApiTargetedProposal = {
  employer: string;
  sector: string | null;
  partnership_type: string;
  selected_occupation: string;
  selected_soc_code: string | null;
  opportunity: string;
  opportunity_evidence: ApiOccupationEvidence[];
  justification: ApiProposalJustification;
  roadmap: string;
};

// Legacy types — used by SWP pipeline only
export type ApiAlignmentDetail = {
  department: string;
  course_code: string;
  course_name: string;
  skill: string;
};

export type ApiSkillGapDetail = {
  skill: string;
  required_by: string[];
  recommended_action: string;
};

export type ApiPipelineStats = {
  total_students: number;
  students_with_3plus_courses: number;
  top_skills: string[];
};

export type ApiEconomicImpact = {
  occupations: Array<{ title: string; annual_wage: number | null; employment: number | null }>;
  aggregate_employment: number | null;
};

export async function streamTargetedProposal(
  employer: string,
  college: string,
  onProposal: (proposal: ApiTargetedProposal) => void,
  onDone: () => void,
  onError: (error: string) => void,
  engagementType: string,
): Promise<void> {
  const res = await fetch(`${BASE}/workflows/partnerships/targeted/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ employer, college, engagement_type: engagementType }),
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
          onProposal(json as ApiTargetedProposal);
        } catch {
          // Incomplete JSON line, skip
        }
      }
    }
  }
  onDone();
}


/* ── SWP Types & Functions ──────────────────────────────────────────── */

export type ApiLmiOccupation = {
  soc_code: string;
  title: string;
  annual_wage: number | null;
  employment: number | null;
  growth_rate: number | null;
  annual_openings: number | null;
  education_level: string | null;
  region: string;
};

export type ApiSupplyEstimate = {
  top_code: string;
  top_title: string;
  department: string;
  estimated_annual_completions: number;
};

export type ApiLmiContext = {
  occupations: ApiLmiOccupation[];
  supply_estimates: ApiSupplyEstimate[];
  total_demand: number;
  total_supply: number;
  gap: number;
  gap_eligible: boolean;
};

export type ApiSwpSection = {
  key: string;
  title: string;
  content: string;
  char_limit: number | null;
};

export type ApiSwpProject = {
  employer: string;
  college: string;
  partnership_type: string;
  sections: ApiSwpSection[];
  lmi_context: ApiLmiContext;
  goal: string;
  metrics: string[];
};

export type SwpProjectRequest = {
  employer: string;
  college: string;
  partnership_type: string;
  executive_summary: string;
  curriculum_alignment: ApiAlignmentDetail[];
  skill_gaps: ApiSkillGapDetail[];
  student_pipeline: ApiPipelineStats;
  economic_impact: ApiEconomicImpact;
  project_framing: string;
  goal: string;
  metrics: string[];
  apprenticeship: boolean;
  work_based_learning: boolean;
  workforce_training_type?: string;
};

export async function getSwpLmiContext(
  employer: string,
  college: string,
): Promise<ApiLmiContext> {
  const res = await fetch(`${BASE}/workflows/swp/lmi-context`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ employer, college }),
  });
  if (!res.ok) throw new Error("Failed to fetch LMI context");
  return res.json();
}

export async function streamSwpProject(
  req: SwpProjectRequest,
  onLmi: (lmi: ApiLmiContext) => void,
  onSection: (section: ApiSwpSection) => void,
  onDone: () => void,
  onError: (error: string) => void,
): Promise<void> {
  const res = await fetch(`${BASE}/workflows/swp/project/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req),
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
          const parsed = JSON.parse(line.slice(6));
          if (parsed.done) { onDone(); return; }
          if (parsed.error) { onError(parsed.error); return; }
          if (parsed.type === "lmi") {
            onLmi(parsed.lmi_context as ApiLmiContext);
          } else if (parsed.type === "section") {
            onSection(parsed.section as ApiSwpSection);
          }
        } catch {
          // Incomplete JSON line, skip
        }
      }
    }
  }
  onDone();
}
