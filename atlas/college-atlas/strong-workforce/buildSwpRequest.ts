import type { SavedProposal } from "@/college-atlas/partnerships/savedProposals";
import type { SwpProjectRequest } from "@/college-atlas/strong-workforce/api";

// Per-engagement-type defaults for the four fields the SWP builder needs
// that aren't on the partnership proposal itself: the Chancellor's
// Office "goal" category, the associated success metrics, and whether
// the partnership is structured as an apprenticeship or work-based
// learning arrangement. These come from SWP compliance conventions and
// are baked in here so the UI doesn't have to ask the user about
// every field for every engagement type.
export type SwpDefaults = {
  goal: string;
  metrics: string[];
  apprenticeship: boolean;
  wbl: boolean;
};

const PARTNERSHIP_DEFAULTS: Record<string, SwpDefaults> = {
  internship:          { goal: "Workforce",  metrics: ["Employed in Field of Study", "Median Annual Earnings"], apprenticeship: false, wbl: true },
  apprenticeship:      { goal: "Workforce",  metrics: ["Employed in Field of Study", "Attained a Living Wage", "Job Closely Related to Field of Study"], apprenticeship: true, wbl: true },
  curriculum_codesign: { goal: "Completion", metrics: ["Completed a Degree or Certificate"], apprenticeship: false, wbl: false },
  hiring_mou:          { goal: "Workforce",  metrics: ["Employed in Field of Study", "Attained a Living Wage"], apprenticeship: false, wbl: false },
  advisory_board:      { goal: "Completion", metrics: ["Completed a Degree or Certificate"], apprenticeship: false, wbl: false },
};

const FALLBACK_DEFAULTS: SwpDefaults = {
  goal: "Workforce",
  metrics: ["Employed in Field of Study"],
  apprenticeship: false,
  wbl: false,
};

// Transform a SavedProposal into a SwpProjectRequest ready for the
// /strong-workforce/project/stream endpoint, applying the per-engagement
// defaults from PARTNERSHIP_DEFAULTS. Pure function — no React, no I/O,
// unit-testable in isolation once the atlas has a test harness.
export function buildSwpRequest(
  saved: SavedProposal,
  college: string,
): { req: SwpProjectRequest; defaults: SwpDefaults } {
  const defaults = PARTNERSHIP_DEFAULTS[saved.engagementType] ?? FALLBACK_DEFAULTS;
  const p = saved.proposal;

  const req: SwpProjectRequest = {
    employer: p.employer,
    college,
    partnership_type: p.partnership_type,
    selected_occupation: p.selected_occupation,
    selected_soc_code: p.selected_soc_code ?? null,
    core_skills: p.core_skills,
    gap_skill: p.gap_skill,
    opportunity: p.opportunity,
    opportunity_evidence: p.opportunity_evidence,
    curriculum_composition: p.justification.curriculum_composition,
    curriculum_evidence: p.justification.curriculum_evidence,
    student_composition: p.justification.student_composition,
    student_evidence: p.justification.student_evidence,
    roadmap: p.roadmap,
    goal: defaults.goal,
    metrics: defaults.metrics,
    apprenticeship: defaults.apprenticeship,
    work_based_learning: defaults.wbl,
  };

  return { req, defaults };
}
