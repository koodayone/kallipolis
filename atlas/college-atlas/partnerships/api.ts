import { API_BASE } from "@/api";

// ── Evidence types (composed into OpportunityReport) ───────────────────────

export type ApiOccupationEvidence = {
  title: string;
  soc_code: string | null;
  annual_wage: number | null;
  employment: number | null;
  annual_openings: number | null;
  growth_rate: number | null;
  // CIP codes the BLS/NCES CIP-SOC crosswalk maps to this SOC. Surfaces
  // the second link in the empirical chain (SOC ↔ CIP) so the atlas
  // rendering can attribute the institutional pathway visibly.
  cip_codes?: string[];
};

export type ApiCourseEvidence = {
  code: string;
  name: string;
  description: string;
  learning_outcomes: string[];
  // The TOP6 code this course is institutionally tagged with in the
  // Master Course File. Used by the atlas to render per-course
  // institutional attribution alongside the course code.
  top_code?: string | null;
};

export type ApiDepartmentEvidence = {
  department: string;
  courses: ApiCourseEvidence[];
  // The TOP6 codes this department's PREPARES_FOR-aligned courses
  // route through (typically one TOP6 per department; some span
  // several). Drives the per-department source attribution caption.
  via_top?: string[];
  // The CIPs that mediate the chain Course → TOP6 → CIP → SOC.
  via_cip?: string[];
};

// ── Curriculum Crosswalk pathway (TOP4 × CIP × SOC) ────────────────────────
//
// Powers the hero visualization at the bottom of the Curriculum Alignment
// section: a three-column flow showing the institutional pathway from
// program (TOP) through federal taxonomy (CIP) to occupation (SOC),
// with this college's coverage marked at the TOP layer and the active
// (lit) pathway marked at the CIP layer. SAM-filtered to occupational
// per CCCCO MIS Data Element Dictionary.

export type ApiCrosswalkTop = {
  code: string;                  // 6-digit TOP code, e.g., "070200"
  name: string;                  // 6-digit title, e.g., "Computer Information Systems"
  taught_at_college: boolean;    // true when ≥ 1 course at this college teaches this TOP
  cips: string[];                // CIP codes this TOP bridges to (filtered to those reaching the SOC)
};

export type ApiCrosswalkCip = {
  code: string;                  // e.g., "15.0507"
  title: string;                 // e.g., "Environmental/Environmental Engineering Technology"
  active: boolean;               // true when ≥ 1 taught TOP6 bridges to this CIP
};

export type ApiCurriculumCrosswalk = {
  tops: ApiCrosswalkTop[];
  cips: ApiCrosswalkCip[];
  n_taught: number;              // count of TOP6 codes the college teaches
  n_total: number;               // count of TOP6 codes in the global prep set
  coverage_pct: number;          // 100 * n_taught / n_total, rounded to 1 decimal
};

export type ApiSupplyEstimate = {
  top_code: string;
  top_title: string;
  award_level: string;
  annual_projected_supply: number;
};

export type ApiInstitutionalSources = {
  coe_region: string;
  coe_region_display: string;
  coe_demand_publication: string;
  coe_supply_publication: string;
  top_cip_crosswalk_source: string;
  cip_soc_crosswalk_source: string;
};

export type ApiSwpEvidence = {
  occupations: ApiOccupationEvidence[];
  supply_estimates: ApiSupplyEstimate[];
  total_demand: number;
  total_supply: number;
  gap: number;
  coe_region: string;
  // Institutional attribution: named external publications and
  // crosswalks that author every categorical claim in the artifact.
  // Drives the source caption in the atlas SWP Evidence section.
  sources?: ApiInstitutionalSources;
};

// ── Occupation-centric Partnerships surfaces ───────────────────────────────

export type ApiOpportunityRow = {
  soc_code: string;
  title: string;
  annual_openings: number | null;
  annual_wage: number | null;
  growth_rate: number | null;
  course_count: number;
  employer_count: number;
  // Regional annual openings minus the college's TOP-program projected
  // supply. Drives the per-row gap chip and the within-sector sort.
  // Negative values indicate the college's pipeline outpaces regional
  // demand for the SOC.
  gap: number | null;
  // Two-valued alignment tag driving the row's visual treatment:
  //   "aligned": college has at least one PREPARES_FOR-aligned course
  //              for this SOC. Renders as a normal navigable row.
  //   "gap":     SOC is regionally demanded but the college has NO
  //              aligned curriculum (course_count = 0). Renders dimmed
  //              with a "no current pathway" label — surfaces a
  //              consortia-level workforce opportunity to discuss.
  // Default "aligned" when absent (backward-compat with older caches).
  alignment_status?: "aligned" | "gap";
};

export type ApiSectorEntry = {
  sector: string;
  is_priority: boolean;
  occupations: ApiOpportunityRow[];
};

export type ApiSectorIndex = {
  college: string;
  sectors: ApiSectorEntry[];
};

export type ApiPartnershipOpportunityEmployer = {
  name: string;
  sector: string | null;
  swp_sectors: string[];
  description: string | null;
  website: string | null;
  naics4: string | null;
  naics_title: string | null;
  industry_share: number | null;
  aligned_course_count: number;
};

export type ApiOpportunityReport = {
  college: string;
  sector: string | null;
  // True when the sector is a Strong Workforce Program priority for the
  // college's COE region (per regional consortium designation in PCAH).
  // Drives the "REGIONAL PRIORITY" tag in the report header.
  is_sector_priority: boolean;
  soc_code: string;
  soc_title: string;
  description: string | null;
  regions: string[];
  executive_summary: string;
  occupational_demand: string;
  curriculum_alignment: string;
  partnership_opportunities_narrative: string;
  opportunity_evidence: ApiOccupationEvidence[];
  curriculum_evidence: ApiDepartmentEvidence[];
  curriculum_crosswalk: ApiCurriculumCrosswalk;
  swp_evidence: ApiSwpEvidence;
  partnership_opportunities: ApiPartnershipOpportunityEmployer[];
};

export async function getPartnershipSectors(college: string): Promise<ApiSectorIndex> {
  const res = await fetch(`${API_BASE}/partnerships/sectors?college=${encodeURIComponent(college)}`);
  if (!res.ok) throw new Error("Failed to fetch partnership sectors");
  return res.json();
}

// ── SVAMP aggregated landscape (Silicon Valley Advanced Manufacturing) ─────
//
// Bespoke consortium prototype. Aggregates the partnership machinery across
// five member colleges × twelve advanced manufacturing occupations. Demand
// and the employer set are regional (shared / deduped); supply is
// institutional (summed). Drilling a cell reuses getPartnershipOpportunity
// unchanged.

// Pooled statewide award-cohort wage outcome for a TOP6 program (display-only;
// medians are non-additive — never summed).
export type ApiSvampWage = {
  recipient_type: string;
  wage_before: number | null;
  wage_after_2: number | null;
  wage_after_5: number | null;
  n: number | null;
  window: string;
};

// A TOP6 program (DataMart actuals) preparing for a cell's SOC at a college.
export type ApiSvampProgram = {
  top6: string;
  name: string;
  awards_recent: number;             // actual completions, latest award year
  awards: number[];                  // completions per landscape award_years
  enrollment: (number | null)[];     // per SVAMP term, the enrollment trend
  wages: ApiSvampWage[];
};

export type ApiSvampCell = {
  soc_code: string;
  title: string;
  annual_openings: number | null;
  annual_wage: number | null;
  growth_rate: number | null;
  course_count: number;
  supply: number;
  gap: number;
  awards_recent: number;             // Σ actual awards over this cell's programs
  // Activity coverage over the crosswalking programs (the dual of the Programs
  // cell): covered = enrolled && feeding_awards>0; partial = one; gap = neither.
  enrolled: boolean;
  feeding_awards: number;            // latest-year awards over the SOC's feeding set
  programs: ApiSvampProgram[];
};

export type ApiSvampCollege = {
  name: string;            // backend college name, e.g. "De Anza College"
  cells: ApiSvampCell[];   // one per SVAMP occupation, in scope order
};

export type ApiSvampAggregate = {
  regional_demand_total: number;
  combined_supply_total: number;
  gap: number;
  candidate_employers: number;
  occupations_taught: number;
  combined_awards: number;           // Σ actual awards over distinct scoped programs
  n_colleges: number;
  n_occupations: number;
};

export type ApiSvampLandscape = {
  region: string;
  region_display: string;
  sector: string;          // the leaf-report sector hint ("Advanced Manufacturing")
  is_sector_priority: boolean;
  executive_summary: string;
  award_years: string[];        // sorted YYYY-YYYY axis for every program's awards series
  enrollment_terms: string[];   // chronologically-sorted term axis for every program's enrollment series
  colleges: ApiSvampCollege[];
  aggregate: ApiSvampAggregate;
  // Rule-bearing instances (BACCC, sector-derived SMCCD, smccd-adm) gate the
  // coverage cell on awards: enrollment-only reads as a gap, not "partial". Only
  // the curated SVAMP instance is false (keeps enrolled-OR-awarded coverage).
  coverage_awards_only: boolean;
};

// ── Session cache for the SVAMP getters ─────────────────────────────────────
// The SVAMP payloads are static for a session (the graph changes by deploy,
// not by interaction), but every lens mount refetched them — so each tab
// switch replayed a loading state. Memoizing the in-flight promise makes the
// first visit fetch once and every later transition render instantly; a
// rejected promise is evicted so errors stay retryable.
const _svampCache = new Map<string, Promise<unknown>>();
function svampCached<T>(key: string, make: () => Promise<T>): Promise<T> {
  if (!_svampCache.has(key)) {
    _svampCache.set(key, make().catch((e) => { _svampCache.delete(key); throw e; }));
  }
  return _svampCache.get(key) as Promise<T>;
}

/** Test-only: clear the SVAMP session cache so per-test fetch mocks stay
 *  isolated (a success cached by one test must not satisfy the next). */
export function _resetSvampCacheForTests(): void {
  _svampCache.clear();
}

// ── Occupational clusters (connected-component target clusters) ────────────
// /clusters is the visualization payload (every number); /cluster-supply is the
// school×TOP detail, a SEPARATE endpoint loaded on demand so the map stays light.
export interface ApiClusterOccupation {
  soc: string;
  title: string;
  annual_openings: number;
  annual_wage: number;
  growth_rate: number;
  admitted: boolean;
}
export interface ApiClusterFeeder {
  top6: string;
  name: string;
  awards: number;
  colleges: number;
}
export interface ApiCluster {
  id: string;
  label: string;
  sector_id: string;
  sector_label: string;
  accent: string;
  demand: number;
  supply: number;
  gap: number;
  coverage: number;
  n_colleges: number;
  n_programs: number;
  wage_low: number;
  wage_high: number;
  occupations: ApiClusterOccupation[];
  feeders: ApiClusterFeeder[];
}
export interface ApiClusterMap {
  member: string;
  n_clusters: number;
  n_occupations: number;
  total_demand: number;
  total_supply: number;
  total_gap: number;
  clusters: ApiCluster[];
}
export interface ApiClusterSupplyTuple {
  college: string;
  top6: string;
  program: string;
  awards: number;
}
export interface ApiClusterSupply {
  id: string;
  label: string;
  sector_id: string;
  supply: number;
  tuples: ApiClusterSupplyTuple[];
}
export interface ApiClusterSupplyMap {
  member: string;
  clusters: ApiClusterSupply[];
}

export async function getConsortiumClusters(member = "baccc"): Promise<ApiClusterMap> {
  return svampCached(`clusters:${member}`, async () => {
    const res = await fetch(`${API_BASE}/partnerships/${encodeURIComponent(member)}/clusters`);
    if (!res.ok) throw new Error("Failed to fetch occupational clusters");
    return res.json();
  });
}
export async function getConsortiumClusterSupply(member = "baccc"): Promise<ApiClusterSupplyMap> {
  return svampCached(`cluster-supply:${member}`, async () => {
    const res = await fetch(`${API_BASE}/partnerships/${encodeURIComponent(member)}/cluster-supply`);
    if (!res.ok) throw new Error("Failed to fetch cluster supply");
    return res.json();
  });
}

// The sectors where a member is in a consortium cluster — its real industry
// targets. The school-lens rail hides industries that aren't on this list (they'd
// render an empty dashboard).
export interface ApiMemberClusterSectors {
  member: string;
  sectors: string[];
}
export async function getMemberClusterSectors(member: string): Promise<ApiMemberClusterSectors> {
  return svampCached(`cluster-sectors:${member}`, async () => {
    const res = await fetch(`${API_BASE}/partnerships/${encodeURIComponent(member)}/cluster-sectors`);
    if (!res.ok) throw new Error("Failed to fetch cluster sectors");
    return res.json();
  });
}

export async function getSvampLandscape(instance: string = "svamp"): Promise<ApiSvampLandscape> {
  return svampCached(`${instance}:landscape`, async () => {
    const res = await fetch(`${API_BASE}/partnerships/${instance}`);
    if (!res.ok) throw new Error("Failed to fetch landscape");
    return res.json();
  });
}

// ── SVAMP Programs lens (supply-side, TOP6-centric) ───────────────────────
// One TOP6 in the supply-treemap universe. awards_total / enrollment_total are
// latest-period magnitudes summed across colleges (additive supply); soc_count
// is the crosswalk cardinality (relationship, never demand).
export type ApiSvampTopSummary = {
  top6: string;
  name: string;
  awards_total: number;
  enrollment_total: number;
  n_colleges_offering: number;
  soc_count: number;
};

// Per-(college, TOP) supply coverage — the dual of the occupations grid cell.
// Keyed on activity, not catalog presence: covered = enrolled && awards>0 (full
// pipeline); partial = one signal but not the other; gap = neither. `teaches`
// (≥1 tagged course) is retained as context but no longer gates the cell.
export type ApiProgramCoverageCell = {
  college: string;
  top6: string;
  teaches: boolean;
  enrolled: boolean;
  awards: number;
};
export type ApiProgramCoverageMatrix = {
  colleges: string[];                  // SVAMP college order — matrix columns
  cells: ApiProgramCoverageCell[];     // flat (college × TOP) coverage
};
export type ApiSvampProgramsLandscape = {
  region: string;
  region_display: string;
  sector: string;
  latest_award_year: string | null;
  n_colleges: number;
  tops: ApiSvampTopSummary[];
  matrix: ApiProgramCoverageMatrix | null;   // per-(college, TOP) coverage grid
  // See ApiSvampLandscape.coverage_awards_only — awards-gated coverage cells.
  coverage_awards_only: boolean;
};

// A SOC the TOP feeds; openings are the single regional value (never summed).
export type ApiSvampOccupationDemand = {
  soc_code: string;
  title: string;
  annual_wage: number | null;
  annual_openings: number | null;
};

// One college's supply series for the focused TOP, aligned to the report axes.
export type ApiSvampCollegeSeries = {
  college: string;
  vals: (number | null)[];
};

// One (college, credential-type) awards series — the per-type decomposition of
// awards_by_college (a college's types sum to its flat series each year).
// `award_type` is the DataMart credential-type name verbatim; series arrive in
// credential-weight order (degrees → certificates → noncredit, larger first).
export type ApiSvampAwardTypeSeries = {
  college: string;
  award_type: string;
  vals: (number | null)[];
};

// One (college, credit-family) enrollment series — the per-family decomposition
// of enrollment_by_college (a college's families sum to its flat series each
// term; the flat line is ALL instructional activity, credit + noncredit).
// `credit_type` is the DataMart family verbatim, in fixed order: "Credit -
// Degree Applicable" → "Credit - Not Degree Applicable" → "Non-Credit".
export type ApiSvampEnrollmentCreditSeries = {
  college: string;
  credit_type: string;
  vals: (number | null)[];
};

export type ApiSvampProgramCourse = {
  code: string;
  name: string;
  description: string;
  learning_outcomes: string[];
  top_code: string | null;
};

export type ApiSvampCollegeCourses = {
  college: string;
  courses: ApiSvampProgramCourse[];
};

// TOP-anchored TOP-CIP-SOC pathway (the dual of ApiCurriculumCrosswalk): one
// focused TOP → its bridging CIPs → the SVAMP SOCs it feeds.
export type ApiProgramCrosswalkCip = { code: string; title: string };
export type ApiProgramCrosswalkSoc = {
  code: string;
  title: string;
  cips: string[];           // CIPs (of this TOP) that bridge to this SOC
};
export type ApiProgramCrosswalk = {
  top6: string;
  top_name: string;
  cips: ApiProgramCrosswalkCip[];   // union of bridging CIPs (middle column)
  socs: ApiProgramCrosswalkSoc[];   // relevant SVAMP SOCs (right column)
};

export type ApiSvampProgramReport = {
  top6: string;
  name: string;
  region: string;
  region_display: string;
  sector: string;
  award_years: string[];
  enrollment_terms: string[];
  occupations: ApiSvampOccupationDemand[];      // demand only, per SOC
  enrollment_by_college: ApiSvampCollegeSeries[];
  awards_by_college: ApiSvampCollegeSeries[];
  awards_by_type: ApiSvampAwardTypeSeries[];    // per-(college, credential-type) decomposition
  enrollment_by_credit: ApiSvampEnrollmentCreditSeries[];  // per-(college, credit-family) decomposition
  wages: ApiSvampWage[];
  curriculum_by_college: ApiSvampCollegeCourses[];
  crosswalk: ApiProgramCrosswalk | null;        // TOP-anchored TOP-CIP-SOC pathway
  college: string | null;                       // set ⇒ targeted (college, TOP) slice
};

// The aggregated-occupation report — the dual of ApiSvampProgramReport. One SOC
// read consortium-wide: demand + consortium supply + gap, the 09 feeding
// programs, per-college series + curriculum, and the SOC-anchored crosswalk.
export type ApiSvampOccupationReport = {
  soc_code: string;
  title: string;
  description: string | null;
  occupational_demand: string;
  sector: string;
  region: string;
  region_display: string;
  annual_openings: number | null;
  annual_wage: number | null;
  growth_rate: number | null;
  employment: number | null;
  consortium_supply: number;
  gap: number;
  award_years: string[];
  enrollment_terms: string[];
  feeding_tops: ApiSvampTopSummary[];
  awards_by_college: ApiSvampCollegeSeries[];
  enrollment_by_college: ApiSvampCollegeSeries[];
  curriculum_by_college: ApiSvampCollegeCourses[];
  crosswalk: ApiCurriculumCrosswalk | null;     // SOC-anchored, consortium-union taught
  partnership_opportunities: ApiPartnershipOpportunityEmployer[];
  partnership_opportunities_narrative: string;
};

export async function getSvampPrograms(instance: string = "svamp"): Promise<ApiSvampProgramsLandscape> {
  return svampCached(`${instance}:programs`, async () => {
    const res = await fetch(`${API_BASE}/partnerships/${instance}/programs`);
    if (!res.ok) throw new Error("Failed to fetch programs landscape");
    return res.json();
  });
}

export async function getSvampProgram(top6: string, college?: string, instance: string = "svamp"): Promise<ApiSvampProgramReport> {
  // `college` omitted ⇒ the consortium-aggregated program report; set ⇒ the
  // targeted (college, TOP) slice (single-college series + that college's
  // curriculum; demand, pathway, wage unchanged).
  return svampCached(`${instance}:program:${top6}:${college ?? ""}`, async () => {
    const params = new URLSearchParams();
    if (college) params.set("college", college);
    const qs = params.toString();
    const res = await fetch(
      `${API_BASE}/partnerships/${instance}/program/${encodeURIComponent(top6)}${qs ? `?${qs}` : ""}`,
    );
    if (!res.ok) throw new Error("Failed to fetch program report");
    return res.json();
  });
}

export async function getSvampOccupation(soc: string, college?: string, instance: string = "svamp", includeEmployers: boolean = true): Promise<ApiSvampOccupationReport> {
  // The aggregated (consortium) view of one occupation — demand, consortium
  // supply + gap, the feeding programs, and per-college series + curriculum.
  // `college` scopes ONLY the SOC-anchored crosswalk's taught/active marking
  // to that one member college (the dashboard's college scope — the pathway
  // lights just that school's feeding TOPs); every other field stays
  // consortium. Omitted ⇒ the consortium-union crosswalk.
  //
  // `includeEmployers=false` opts out of the Partnership Opportunities gather —
  // a region-wide employer list (~94% of the payload) that the dashboard
  // occupations lens never renders. The report surfaces keep the default.
  const params = new URLSearchParams();
  if (college) params.set("college", college);
  if (!includeEmployers) params.set("employers", "false");
  const qs = params.toString() ? `?${params.toString()}` : "";
  return svampCached(`${instance}:occupation:${soc}:${college ?? ""}:${includeEmployers ? "e" : "0"}`, async () => {
    const res = await fetch(`${API_BASE}/partnerships/${instance}/occupation/${encodeURIComponent(soc)}${qs}`);
    if (!res.ok) throw new Error("Failed to fetch occupation report");
    return res.json();
  });
}

// SVAMP Employers lens — geocoded Bay-Area advanced manufacturing employers
// hiring for the SVAMP occupations, for the regional employer map.
export type ApiSvampEmployer = {
  name: string;
  display_name: string | null;  // public-facing brand; card falls back to name
  lat: number;
  lng: number;
  sector: string | null;
  naics4: string | null;
  naics_title: string | null;   // authoritative NAICS-4 industry title (matches naics4)
  website: string | null;
  description: string | null;
  socs: string[];          // SVAMP SOCs this employer hires for (curated)
  soc_count: number;
  soc_titles?: Record<string, string>;  // {soc_code: BLS title} for label display
};
export type ApiSvampEmployersResult = {
  region: string;
  region_display: string;
  sector: string;
  employers: ApiSvampEmployer[];
  shown: number;           // plotted (geocoded + in-frame)
  total: number;           // curated candidates (incl. not-yet-geocoded)
};
export async function getSvampEmployers(instance: string = "svamp"): Promise<ApiSvampEmployersResult> {
  return svampCached(`${instance}:employers`, async () => {
    const res = await fetch(`${API_BASE}/partnerships/${instance}/employers`);
    if (!res.ok) throw new Error("Failed to fetch employers");
    return res.json();
  });
}

export async function getPartnershipOpportunity(
  socCode: string,
  college: string,
  sector?: string,
  topPrefix?: string,
  cteOnly?: boolean,
  excludeTops?: string[],
): Promise<ApiOpportunityReport> {
  // `sector` is the click-context sector the user navigated from. When
  // a SOC belongs to multiple PCAH sectors, this preserves the user's
  // mental model — the report renders under the sector they clicked
  // from rather than re-resolving alphabetically. The backend
  // validates the value against the SOC's actual PCAH sectors and
  // ignores it if invalid.
  //
  // `topPrefix` scopes the curriculum pathway to a TOP division (the SVAMP
  // 09-only lens). Omitted for per-college reports ⇒ the backend serves the
  // unscoped cached report unchanged.
  const params = new URLSearchParams({ college });
  if (sector) params.set("sector", sector);
  if (topPrefix) params.set("top_prefix", topPrefix);
  if (cteOnly) params.set("cte_only", "true");
  // Director's-mandate TOP exclusions (the SVAMP lens) — comma-separated.
  if (excludeTops?.length) params.set("exclude_tops", excludeTops.join(","));
  const res = await fetch(
    `${API_BASE}/partnerships/opportunity/${encodeURIComponent(socCode)}?${params.toString()}`,
  );
  if (!res.ok) throw new Error("Failed to fetch partnership opportunity report");
  return res.json();
}
