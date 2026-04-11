/**
 * Tests for buildSwpRequest — the pure helper that transforms a
 * SavedProposal plus its engagement type into an SwpProjectRequest
 * ready for the /strong-workforce/project/stream backend endpoint.
 *
 * Coverage:
 *   - Engagement-type default lookup: all five recognized types
 *     (internship, apprenticeship, curriculum_codesign, hiring_mou,
 *     advisory_board) and the fallback for unrecognized types
 *   - Field passthrough from proposal into request
 *   - Flattening of the proposal's nested justification object
 *   - College argument takes precedence over SavedProposal.collegeId
 *   - Null selected_soc_code is preserved, not coerced to "null"
 */

import { describe, it, expect } from "vitest";
import { buildSwpRequest } from "./buildSwpRequest";
import type { SavedProposal } from "@/college-atlas/partnerships/savedProposals";
import type { ApiTargetedProposal } from "@/college-atlas/partnerships/api";

// Build a minimal SavedProposal fixture. The fields not tested explicitly
// below are still required by the type, so they get harmless placeholder
// values. Keep this helper local to the test file — other test files
// should build their own fixtures to stay decoupled from each other.
function makeSavedProposal(overrides: {
  engagementType: string;
  employer?: string;
  partnership_type?: string;
}): SavedProposal {
  const proposal: ApiTargetedProposal = {
    employer: overrides.employer ?? "Acme Corp",
    sector: "Advanced Manufacturing",
    partnership_type: overrides.partnership_type ?? "Internship Pipeline",
    selected_occupation: "Industrial Engineer",
    selected_soc_code: "17-2112",
    core_skills: ["CAD", "Process Control"],
    gap_skill: "Lean Six Sigma",
    regions: ["Bay Area"],
    opportunity: "Paid internships for advanced manufacturing students",
    opportunity_evidence: [],
    justification: {
      curriculum_composition: "Four courses aligned on process control and CAD.",
      curriculum_evidence: [],
      student_composition: "24 students currently on track.",
      student_evidence: {
        total_in_program: 24,
        with_all_core_skills: 18,
        top_students: [],
      },
    },
    roadmap: "Spring 2026 cohort start.",
  };

  return {
    id: "test-id",
    proposal,
    engagementType: overrides.engagementType,
    collegeId: "foothill",
    savedAt: new Date().toISOString(),
    status: "saved",
    schemaVersion: 8,
  };
}

describe("buildSwpRequest", () => {
  describe("engagement-type defaults", () => {
    it("applies internship defaults: Workforce goal, WBL true, apprenticeship false", () => {
      const saved = makeSavedProposal({ engagementType: "internship" });
      const { req, defaults } = buildSwpRequest(saved, "foothill");

      expect(defaults.goal).toBe("Workforce");
      expect(defaults.apprenticeship).toBe(false);
      expect(defaults.wbl).toBe(true);
      expect(defaults.metrics).toContain("Employed in Field of Study");
      expect(req.goal).toBe("Workforce");
      expect(req.work_based_learning).toBe(true);
      expect(req.apprenticeship).toBe(false);
    });

    it("applies apprenticeship defaults: both apprenticeship and WBL true", () => {
      const saved = makeSavedProposal({ engagementType: "apprenticeship" });
      const { defaults } = buildSwpRequest(saved, "foothill");

      expect(defaults.apprenticeship).toBe(true);
      expect(defaults.wbl).toBe(true);
      expect(defaults.goal).toBe("Workforce");
      expect(defaults.metrics).toContain("Attained a Living Wage");
    });

    it("applies curriculum_codesign defaults: Completion goal, neither apprenticeship nor WBL", () => {
      const saved = makeSavedProposal({ engagementType: "curriculum_codesign" });
      const { defaults } = buildSwpRequest(saved, "foothill");

      expect(defaults.goal).toBe("Completion");
      expect(defaults.apprenticeship).toBe(false);
      expect(defaults.wbl).toBe(false);
      expect(defaults.metrics).toEqual(["Completed a Degree or Certificate"]);
    });

    it("applies hiring_mou defaults: Workforce goal, neither apprenticeship nor WBL", () => {
      const saved = makeSavedProposal({ engagementType: "hiring_mou" });
      const { defaults } = buildSwpRequest(saved, "foothill");

      expect(defaults.goal).toBe("Workforce");
      expect(defaults.apprenticeship).toBe(false);
      expect(defaults.wbl).toBe(false);
      expect(defaults.metrics).toContain("Attained a Living Wage");
    });

    it("applies advisory_board defaults: Completion goal, single metric", () => {
      const saved = makeSavedProposal({ engagementType: "advisory_board" });
      const { defaults } = buildSwpRequest(saved, "foothill");

      expect(defaults.goal).toBe("Completion");
      expect(defaults.metrics).toEqual(["Completed a Degree or Certificate"]);
    });

    it("falls back to a Workforce default when the engagement type is unrecognized", () => {
      const saved = makeSavedProposal({ engagementType: "something-novel" });
      const { defaults } = buildSwpRequest(saved, "foothill");

      expect(defaults.goal).toBe("Workforce");
      expect(defaults.metrics).toEqual(["Employed in Field of Study"]);
      expect(defaults.apprenticeship).toBe(false);
      expect(defaults.wbl).toBe(false);
    });
  });

  describe("request payload construction", () => {
    it("passes through proposal fields verbatim into the request", () => {
      const saved = makeSavedProposal({
        engagementType: "internship",
        employer: "Tesla",
        partnership_type: "Curriculum Co-Design",
      });
      const { req } = buildSwpRequest(saved, "foothill");

      expect(req.employer).toBe("Tesla");
      expect(req.college).toBe("foothill");
      expect(req.partnership_type).toBe("Curriculum Co-Design");
      expect(req.selected_occupation).toBe("Industrial Engineer");
      expect(req.selected_soc_code).toBe("17-2112");
      expect(req.core_skills).toEqual(["CAD", "Process Control"]);
      expect(req.gap_skill).toBe("Lean Six Sigma");
      expect(req.opportunity).toBe("Paid internships for advanced manufacturing students");
      expect(req.roadmap).toBe("Spring 2026 cohort start.");
    });

    it("flattens the proposal's nested justification into the top-level request", () => {
      const saved = makeSavedProposal({ engagementType: "internship" });
      const { req } = buildSwpRequest(saved, "foothill");

      // The proposal wraps curriculum/student composition inside `justification`;
      // the request expects them flat. This is the one non-trivial transformation
      // the helper does, so it's worth an explicit assertion.
      expect(req.curriculum_composition).toBe(saved.proposal.justification.curriculum_composition);
      expect(req.curriculum_evidence).toBe(saved.proposal.justification.curriculum_evidence);
      expect(req.student_composition).toBe(saved.proposal.justification.student_composition);
      expect(req.student_evidence).toBe(saved.proposal.justification.student_evidence);
    });

    it("sets college from the argument, not from the saved proposal's collegeId", () => {
      // The SavedProposal.collegeId is the identifier the proposal was originally
      // scoped to, which for historical reasons may differ from the current session.
      // The SwpProjectRequest.college must come from the caller to avoid drift.
      const saved = makeSavedProposal({ engagementType: "internship" });
      const { req } = buildSwpRequest(saved, "laney");

      expect(req.college).toBe("laney");
      expect(saved.collegeId).toBe("foothill"); // unchanged on the input
    });

    it("handles null selected_soc_code without coercing it to the string 'null'", () => {
      const saved = makeSavedProposal({ engagementType: "internship" });
      saved.proposal.selected_soc_code = null;

      const { req } = buildSwpRequest(saved, "foothill");
      expect(req.selected_soc_code).toBeNull();
    });
  });
});
