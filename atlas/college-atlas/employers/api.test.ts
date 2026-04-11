/**
 * Tests for the employers feature's API client — verifies URL
 * construction, response parsing, and error handling for the three
 * exported functions that wrap backend endpoints under /employers.
 *
 * Follows the fetch-mocking pattern from
 * college-atlas/students/api.test.ts.
 *
 * Coverage:
 *   - getEmployers: URL encoding of the college parameter, successful
 *     body parsing, error branch on non-ok response
 *   - getEmployerDetail: URL includes both employer name and college
 *     encoded (employer names can contain spaces, ampersands, and
 *     punctuation that must round-trip), error branch
 *   - queryEmployers: POST body shape, Content-Type header,
 *     successful body parsing, server error text surfaced in thrown
 *     error, fallback "Query failed" message on empty error body
 */

import { describe, it, expect, afterEach, vi } from "vitest";
import {
  getEmployers,
  getEmployerDetail,
  queryEmployers,
} from "./api";

describe("employers api client", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  describe("getEmployers", () => {
    it("hits /employers/ with the college query parameter URL-encoded", async () => {
      const mockFetch = vi.fn().mockResolvedValue({
        ok: true,
        json: async () => [],
      });
      vi.stubGlobal("fetch", mockFetch);

      await getEmployers("Foothill College");

      expect(mockFetch).toHaveBeenCalledTimes(1);
      const url = mockFetch.mock.calls[0][0] as string;
      expect(url).toContain("/employers/?college=");
      expect(url).toContain("Foothill%20College");
    });

    it("returns the parsed JSON body on success", async () => {
      const body = [
        {
          name: "Kaiser Permanente",
          sector: "Healthcare",
          description: "Integrated managed care consortium",
          website: "https://about.kaiserpermanente.org",
          occupations: ["Registered Nurses", "Medical Assistants"],
          matching_skills: 8,
          skills: ["Patient Care", "Medical Records"],
        },
      ];
      vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: true, json: async () => body }));

      const result = await getEmployers("foothill");
      expect(result).toEqual(body);
    });

    it("throws a descriptive error when the response is not ok", async () => {
      vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: false, status: 500, json: async () => ({}) }));
      await expect(getEmployers("foothill")).rejects.toThrow("Failed to fetch employers");
    });
  });

  describe("getEmployerDetail", () => {
    it("hits /employers/:name with an ampersand and spaces in the employer name encoded", async () => {
      const mockFetch = vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({
          name: "AT&T Services",
          sector: null,
          description: null,
          website: null,
          regions: [],
          occupations: [],
        }),
      });
      vi.stubGlobal("fetch", mockFetch);

      await getEmployerDetail("AT&T Services", "Foothill College");

      const url = mockFetch.mock.calls[0][0] as string;
      // Ampersand is reserved and must be encoded as %26 to not be
      // parsed as a query-string delimiter.
      expect(url).toContain("/employers/AT%26T%20Services");
      expect(url).toContain("college=Foothill%20College");
    });

    it("throws a descriptive error when the response is not ok", async () => {
      vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: false, status: 404, json: async () => ({}) }));
      await expect(getEmployerDetail("Nonexistent Corp", "foothill")).rejects.toThrow("Failed to fetch employer detail");
    });
  });

  describe("queryEmployers", () => {
    it("POSTs to /employers/query with a JSON body containing query and college", async () => {
      const mockFetch = vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({ employers: [], message: "no results", cypher: null }),
      });
      vi.stubGlobal("fetch", mockFetch);

      await queryEmployers("healthcare employers", "foothill");

      expect(mockFetch).toHaveBeenCalledTimes(1);
      const [url, init] = mockFetch.mock.calls[0] as [string, RequestInit];
      expect(url).toContain("/employers/query");
      expect(init.method).toBe("POST");
      expect((init.headers as Record<string, string>)["Content-Type"]).toBe("application/json");

      const parsed = JSON.parse(init.body as string);
      expect(parsed).toEqual({ query: "healthcare employers", college: "foothill" });
    });

    it("returns the parsed response body on success", async () => {
      const body = {
        employers: [],
        message: "0 results",
        cypher: null,
      };
      vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: true, json: async () => body }));

      const result = await queryEmployers("test", "foothill");
      expect(result).toEqual(body);
    });

    it("surfaces the server's error text when the response is not ok", async () => {
      vi.stubGlobal("fetch", vi.fn().mockResolvedValue({
        ok: false,
        status: 422,
        text: async () => "Query failed: unknown sector",
      }));

      await expect(queryEmployers("bad", "foothill")).rejects.toThrow("Query failed: unknown sector");
    });

    it("falls back to a generic 'Query failed' message when the body text is empty", async () => {
      vi.stubGlobal("fetch", vi.fn().mockResolvedValue({
        ok: false,
        status: 500,
        text: async () => "",
      }));

      await expect(queryEmployers("bad", "foothill")).rejects.toThrow("Query failed");
    });
  });
});
