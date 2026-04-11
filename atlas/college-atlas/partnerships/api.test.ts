/**
 * Tests for the partnerships feature's API client — verifies URL
 * construction, response parsing, and error handling for the four
 * simple-fetch endpoints plus basic streaming behavior for
 * streamTargetedProposal.
 *
 * Simple endpoints follow the fetch-mocking pattern from
 * college-atlas/students/api.test.ts. The streaming test builds a
 * ReadableStream-like mock whose body yields pre-encoded SSE frames,
 * so assertions can verify that the SSE parser correctly dispatches
 * onProposal / onDone / onError callbacks. The streamSwpProject
 * function in strong-workforce uses the same SSE format; its tests
 * can follow this pattern.
 *
 * Coverage:
 *   - getPartnershipLandscape: URL encoding, body parsing, error branch
 *   - getEmployerPipeline: URL includes both employer and college
 *     encoded, body parsing, error branch
 *   - getEmployerOccupations: URL encoding of employer parameter,
 *     body parsing, error branch
 *   - queryPartnerships: POST body shape, error text surfaced, fallback
 *     "Query failed" on empty body
 *   - streamTargetedProposal: POST body shape, non-ok response calls
 *     onError not onProposal, successful frames dispatch onProposal
 *     then {"done":true} dispatches onDone, error frame dispatches
 *     onError
 */

import { describe, it, expect, afterEach, vi } from "vitest";
import {
  getPartnershipLandscape,
  getEmployerPipeline,
  getEmployerOccupations,
  queryPartnerships,
  streamTargetedProposal,
  type ApiTargetedProposal,
} from "./api";

// Helper: build a mock Response whose body is a ReadableStream that
// yields the given UTF-8 chunks, each decoded and parsed by the SSE
// reader inside streamTargetedProposal. The chunks must already be
// formatted as SSE frames (e.g., "data: {...}\n\n").
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

describe("partnerships api client", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  describe("getPartnershipLandscape", () => {
    it("hits /partnerships/landscape with the college query parameter URL-encoded", async () => {
      const mockFetch = vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({ college: "Foothill College", opportunities: [] }),
      });
      vi.stubGlobal("fetch", mockFetch);

      await getPartnershipLandscape("Foothill College");

      const url = mockFetch.mock.calls[0][0] as string;
      expect(url).toContain("/partnerships/landscape?college=");
      expect(url).toContain("Foothill%20College");
    });

    it("returns the parsed body on success", async () => {
      const body = {
        college: "foothill",
        opportunities: [
          {
            name: "Kaiser",
            sector: "Healthcare",
            description: null,
            alignment_score: 0.87,
            gap_count: 2,
            pipeline_size: 24,
            top_occupation: "Registered Nurses",
            top_wage: 130000,
            aligned_skills: ["Patient Care"],
            gap_skills: ["EHR"],
          },
        ],
      };
      vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: true, json: async () => body }));

      const result = await getPartnershipLandscape("foothill");
      expect(result).toEqual(body);
    });

    it("throws a descriptive error when the response is not ok", async () => {
      vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: false, status: 500, json: async () => ({}) }));
      await expect(getPartnershipLandscape("foothill")).rejects.toThrow("Failed to fetch partnership landscape");
    });
  });

  describe("getEmployerPipeline", () => {
    it("hits /partnerships/employer-pipeline with employer and college both encoded", async () => {
      const mockFetch = vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({ pipeline_size: 42 }),
      });
      vi.stubGlobal("fetch", mockFetch);

      await getEmployerPipeline("AT&T Services", "Foothill College");

      const url = mockFetch.mock.calls[0][0] as string;
      expect(url).toContain("/partnerships/employer-pipeline");
      expect(url).toContain("employer=AT%26T%20Services");
      expect(url).toContain("college=Foothill%20College");
    });

    it("returns the parsed body on success", async () => {
      vi.stubGlobal("fetch", vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({ pipeline_size: 17 }),
      }));
      const result = await getEmployerPipeline("Kaiser", "foothill");
      expect(result).toEqual({ pipeline_size: 17 });
    });

    it("throws a descriptive error when the response is not ok", async () => {
      vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: false, status: 500, json: async () => ({}) }));
      await expect(getEmployerPipeline("Kaiser", "foothill")).rejects.toThrow("Failed to fetch pipeline data");
    });
  });

  describe("getEmployerOccupations", () => {
    it("hits /partnerships/employer-occupations with employer encoded", async () => {
      const mockFetch = vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({ occupations: [] }),
      });
      vi.stubGlobal("fetch", mockFetch);

      await getEmployerOccupations("Kaiser Permanente");

      const url = mockFetch.mock.calls[0][0] as string;
      expect(url).toContain("/partnerships/employer-occupations?employer=");
      expect(url).toContain("Kaiser%20Permanente");
    });

    it("returns the parsed body on success", async () => {
      const body = {
        occupations: [
          { title: "Registered Nurses", annual_wage: 130000 },
          { title: "Medical Assistants", annual_wage: 55000 },
        ],
      };
      vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: true, json: async () => body }));

      const result = await getEmployerOccupations("Kaiser");
      expect(result).toEqual(body);
    });

    it("throws a descriptive error when the response is not ok", async () => {
      vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: false, status: 404, json: async () => ({}) }));
      await expect(getEmployerOccupations("Nonexistent")).rejects.toThrow("Failed to fetch employer occupations");
    });
  });

  describe("queryPartnerships", () => {
    it("POSTs to /partnerships/query with a JSON body containing query and college", async () => {
      const mockFetch = vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({ opportunities: [], message: "no results", cypher: null }),
      });
      vi.stubGlobal("fetch", mockFetch);

      await queryPartnerships("healthcare partnerships", "foothill");

      const [url, init] = mockFetch.mock.calls[0] as [string, RequestInit];
      expect(url).toContain("/partnerships/query");
      expect(init.method).toBe("POST");
      expect((init.headers as Record<string, string>)["Content-Type"]).toBe("application/json");

      const parsed = JSON.parse(init.body as string);
      expect(parsed).toEqual({ query: "healthcare partnerships", college: "foothill" });
    });

    it("surfaces the server's error text when the response is not ok", async () => {
      vi.stubGlobal("fetch", vi.fn().mockResolvedValue({
        ok: false,
        status: 422,
        text: async () => "Query failed: no alignment found",
      }));

      await expect(queryPartnerships("bad", "foothill")).rejects.toThrow("Query failed: no alignment found");
    });

    it("falls back to a generic 'Query failed' message when the body text is empty", async () => {
      vi.stubGlobal("fetch", vi.fn().mockResolvedValue({
        ok: false,
        status: 500,
        text: async () => "",
      }));

      await expect(queryPartnerships("bad", "foothill")).rejects.toThrow("Query failed");
    });
  });

  describe("streamTargetedProposal", () => {
    it("POSTs to /partnerships/targeted/stream with employer, college, and engagement_type", async () => {
      const mockFetch = vi.fn().mockResolvedValue(sseResponse([]));
      vi.stubGlobal("fetch", mockFetch);

      await streamTargetedProposal(
        "Kaiser",
        "foothill",
        () => {},
        () => {},
        () => {},
        "internship",
      );

      const [url, init] = mockFetch.mock.calls[0] as [string, RequestInit];
      expect(url).toContain("/partnerships/targeted/stream");
      expect(init.method).toBe("POST");

      const parsed = JSON.parse(init.body as string);
      expect(parsed).toEqual({
        employer: "Kaiser",
        college: "foothill",
        engagement_type: "internship",
      });
    });

    it("calls onError and does not call onProposal when the response is not ok", async () => {
      vi.stubGlobal("fetch", vi.fn().mockResolvedValue({
        ok: false,
        text: async () => "upstream error",
      }));

      const onProposal = vi.fn();
      const onDone = vi.fn();
      const onError = vi.fn();

      await streamTargetedProposal("Kaiser", "foothill", onProposal, onDone, onError, "internship");

      expect(onProposal).not.toHaveBeenCalled();
      expect(onDone).not.toHaveBeenCalled();
      expect(onError).toHaveBeenCalledWith("upstream error");
    });

    it("dispatches onProposal for data frames and onDone when the stream reports done", async () => {
      const proposal = { employer: "Kaiser", partnership_type: "Internship Pipeline" } as unknown as ApiTargetedProposal;
      vi.stubGlobal("fetch", vi.fn().mockResolvedValue(sseResponse([
        `data: ${JSON.stringify(proposal)}\n\n`,
        `data: {"done": true}\n\n`,
      ])));

      const onProposal = vi.fn();
      const onDone = vi.fn();
      const onError = vi.fn();

      await streamTargetedProposal("Kaiser", "foothill", onProposal, onDone, onError, "internship");

      expect(onProposal).toHaveBeenCalledTimes(1);
      expect(onProposal).toHaveBeenCalledWith(proposal);
      expect(onDone).toHaveBeenCalledTimes(1);
      expect(onError).not.toHaveBeenCalled();
    });

    it("dispatches onError when an error frame arrives mid-stream", async () => {
      vi.stubGlobal("fetch", vi.fn().mockResolvedValue(sseResponse([
        `data: {"error": "generation failed"}\n\n`,
      ])));

      const onProposal = vi.fn();
      const onDone = vi.fn();
      const onError = vi.fn();

      await streamTargetedProposal("Kaiser", "foothill", onProposal, onDone, onError, "internship");

      expect(onError).toHaveBeenCalledWith("generation failed");
      expect(onProposal).not.toHaveBeenCalled();
      expect(onDone).not.toHaveBeenCalled();
    });
  });
});
