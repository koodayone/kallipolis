/**
 * Tests for the strong-workforce feature's API client — the single
 * exported function streamSwpProject that POSTs an SwpProjectRequest
 * to /strong-workforce/project/stream and consumes the SSE response
 * frame by frame.
 *
 * Uses the same SSE-mock pattern as college-atlas/partnerships/api.test.ts:
 * a helper builds a Response with a ReadableStream-like body that
 * yields pre-encoded SSE frames, so assertions can verify that the
 * stream parser correctly routes {type: "lmi"} frames to onLmi,
 * {type: "section"} frames to onSection, and {done: true} to onDone.
 *
 * Coverage:
 *   - POST body shape: URL, method, Content-Type, and the full
 *     SwpProjectRequest payload round-trip through JSON
 *   - Non-ok response invokes onError and none of the success
 *     callbacks
 *   - An "lmi" frame dispatches onLmi with the parsed lmi_context
 *   - A "section" frame dispatches onSection with the parsed section
 *   - A {"done": true} frame dispatches onDone once
 *   - An {"error": "..."} frame dispatches onError with the message
 */

import { describe, it, expect, afterEach, vi } from "vitest";
import {
  streamSwpProject,
  type SwpProjectRequest,
  type ApiLmiContext,
  type ApiSwpSection,
} from "./api";

function sseResponse(chunks: string[]) {
  const encoder = new TextEncoder();
  let i = 0;
  return {
    ok: true,
    body: {
      getReader: () => ({
        read: async () => {
          if (i >= chunks.length) return { done: true, value: undefined };
          const value = encoder.encode(chunks[i++]);
          return { done: false, value };
        },
      }),
    },
  };
}

const baseRequest: SwpProjectRequest = {
  employer: "Kaiser Permanente",
  college: "foothill",
  partnership_type: "Internship Pipeline",
  selected_occupation: "Registered Nurses",
  selected_soc_code: "29-1141",
  core_skills: ["Patient Care"],
  gap_skill: "EHR",
  opportunity: "Paid internships for nursing students",
  opportunity_evidence: [],
  curriculum_composition: "",
  curriculum_evidence: [],
  student_composition: "",
  student_evidence: {
    total_in_program: 0,
    with_all_core_skills: 0,
    top_students: [],
  },
  roadmap: "",
  goal: "Workforce",
  metrics: ["Employed in Field of Study"],
  apprenticeship: false,
  work_based_learning: true,
};

describe("strong-workforce api client", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  describe("streamSwpProject", () => {
    it("POSTs to /strong-workforce/project/stream with the full request body", async () => {
      const mockFetch = vi.fn().mockResolvedValue(sseResponse([]));
      vi.stubGlobal("fetch", mockFetch);

      await streamSwpProject(baseRequest, () => {}, () => {}, () => {}, () => {});

      const [url, init] = mockFetch.mock.calls[0] as [string, RequestInit];
      expect(url).toContain("/strong-workforce/project/stream");
      expect(init.method).toBe("POST");
      expect((init.headers as Record<string, string>)["Content-Type"]).toBe("application/json");

      const parsed = JSON.parse(init.body as string);
      expect(parsed).toEqual(baseRequest);
    });

    it("calls onError and none of the success callbacks when the response is not ok", async () => {
      vi.stubGlobal("fetch", vi.fn().mockResolvedValue({
        ok: false,
        text: async () => "backend unreachable",
      }));

      const onLmi = vi.fn();
      const onSection = vi.fn();
      const onDone = vi.fn();
      const onError = vi.fn();

      await streamSwpProject(baseRequest, onLmi, onSection, onDone, onError);

      expect(onLmi).not.toHaveBeenCalled();
      expect(onSection).not.toHaveBeenCalled();
      expect(onDone).not.toHaveBeenCalled();
      expect(onError).toHaveBeenCalledWith("backend unreachable");
    });

    it("dispatches onLmi when an 'lmi' frame arrives", async () => {
      const lmiContext = {
        occupations: [],
        supply_estimates: [],
        department_enrollments: [],
        total_demand: 100,
        total_supply: 50,
        gap: 50,
        gap_eligible: true,
      } as ApiLmiContext;

      vi.stubGlobal("fetch", vi.fn().mockResolvedValue(sseResponse([
        `data: ${JSON.stringify({ type: "lmi", lmi_context: lmiContext })}\n\n`,
      ])));

      const onLmi = vi.fn();
      const onSection = vi.fn();
      const onDone = vi.fn();
      const onError = vi.fn();

      await streamSwpProject(baseRequest, onLmi, onSection, onDone, onError);

      expect(onLmi).toHaveBeenCalledTimes(1);
      expect(onLmi).toHaveBeenCalledWith(lmiContext);
      expect(onSection).not.toHaveBeenCalled();
    });

    it("dispatches onSection when a 'section' frame arrives", async () => {
      const section = {
        key: "executive_summary",
        title: "Executive Summary",
        content: "...",
        char_limit: 2000,
      } as ApiSwpSection;

      vi.stubGlobal("fetch", vi.fn().mockResolvedValue(sseResponse([
        `data: ${JSON.stringify({ type: "section", section })}\n\n`,
      ])));

      const onLmi = vi.fn();
      const onSection = vi.fn();
      const onDone = vi.fn();
      const onError = vi.fn();

      await streamSwpProject(baseRequest, onLmi, onSection, onDone, onError);

      expect(onSection).toHaveBeenCalledTimes(1);
      expect(onSection).toHaveBeenCalledWith(section);
      expect(onLmi).not.toHaveBeenCalled();
    });

    it("dispatches onDone when a {\"done\": true} frame arrives", async () => {
      vi.stubGlobal("fetch", vi.fn().mockResolvedValue(sseResponse([
        `data: {"done": true}\n\n`,
      ])));

      const onLmi = vi.fn();
      const onSection = vi.fn();
      const onDone = vi.fn();
      const onError = vi.fn();

      await streamSwpProject(baseRequest, onLmi, onSection, onDone, onError);

      expect(onDone).toHaveBeenCalledTimes(1);
      expect(onError).not.toHaveBeenCalled();
    });

    it("dispatches onError when an error frame arrives mid-stream", async () => {
      vi.stubGlobal("fetch", vi.fn().mockResolvedValue(sseResponse([
        `data: {"error": "LLM generation failed"}\n\n`,
      ])));

      const onLmi = vi.fn();
      const onSection = vi.fn();
      const onDone = vi.fn();
      const onError = vi.fn();

      await streamSwpProject(baseRequest, onLmi, onSection, onDone, onError);

      expect(onError).toHaveBeenCalledWith("LLM generation failed");
      expect(onDone).not.toHaveBeenCalled();
    });
  });
});
