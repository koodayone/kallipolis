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

export async function getPrograms(): Promise<ProgramSummary[]> {
  const res = await fetch(`${BASE}/ontology/programs`);
  if (!res.ok) throw new Error("Failed to fetch programs");
  return res.json();
}
