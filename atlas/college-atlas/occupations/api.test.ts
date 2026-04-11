/**
 * Tests for the occupations feature's API client — verifies URL
 * construction, response parsing, and error handling for the three
 * exported functions that wrap backend endpoints under /occupations.
 *
 * Follows the fetch-mocking pattern from
 * college-atlas/students/api.test.ts.
 *
 * Coverage:
 *   - getLaborMarketOverview: URL encoding of the college parameter,
 *     successful body parsing, error branch on non-ok response
 *   - getOccupationDetail: URL includes both soc_code and college
 *     encoded (soc codes can contain dashes and periods that should
 *     round-trip through encoding), error branch
 *   - queryOccupations: POST body shape, Content-Type header,
 *     successful body parsing, server error text surfaced in thrown
 *     error, fallback "Query failed" message on empty error body
 */

import { describe, it, expect, afterEach, vi } from "vitest";
import {
  getLaborMarketOverview,
  getOccupationDetail,
  queryOccupations,
} from "./api";

describe("occupations api client", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  describe("getLaborMarketOverview", () => {
    it("hits /occupations/overview with the college query parameter URL-encoded", async () => {
      const mockFetch = vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({ college: "Foothill College", regions: [] }),
      });
      vi.stubGlobal("fetch", mockFetch);

      await getLaborMarketOverview("Foothill College");

      expect(mockFetch).toHaveBeenCalledTimes(1);
      const url = mockFetch.mock.calls[0][0] as string;
      expect(url).toContain("/occupations/overview?college=");
      expect(url).toContain("Foothill%20College");
    });

    it("returns the parsed JSON body on success", async () => {
      const body = {
        college: "foothill",
        regions: [
          {
            region: "Bay Area",
            occupations: [
              {
                soc_code: "15-1252",
                title: "Software Developers",
                description: null,
                annual_wage: 150000,
                employment: 50000,
                growth_rate: 0.25,
                annual_openings: 5000,
                education_level: "Bachelor's",
                matching_skills: 12,
                skills: ["Python", "JavaScript"],
              },
            ],
          },
        ],
      };
      vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: true, json: async () => body }));

      const result = await getLaborMarketOverview("foothill");
      expect(result).toEqual(body);
    });

    it("throws a descriptive error when the response is not ok", async () => {
      vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: false, status: 500, json: async () => ({}) }));
      await expect(getLaborMarketOverview("foothill")).rejects.toThrow("Failed to fetch labor market data");
    });
  });

  describe("getOccupationDetail", () => {
    it("hits /occupations/:soc_code with both soc_code and college encoded", async () => {
      const mockFetch = vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({
          soc_code: "15-1252",
          title: "Software Developers",
          description: null,
          skills: [],
          regions: [],
        }),
      });
      vi.stubGlobal("fetch", mockFetch);

      await getOccupationDetail("15-1252", "Foothill College");

      const url = mockFetch.mock.calls[0][0] as string;
      // SOC codes contain dashes that encodeURIComponent leaves intact.
      expect(url).toContain("/occupations/15-1252");
      expect(url).toContain("college=Foothill%20College");
    });

    it("throws a descriptive error when the response is not ok", async () => {
      vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: false, status: 404, json: async () => ({}) }));
      await expect(getOccupationDetail("99-9999", "foothill")).rejects.toThrow("Failed to fetch occupation detail");
    });
  });

  describe("queryOccupations", () => {
    it("POSTs to /occupations/query with a JSON body containing query and college", async () => {
      const mockFetch = vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({ occupations: [], message: "no results", cypher: null }),
      });
      vi.stubGlobal("fetch", mockFetch);

      await queryOccupations("highest paying occupations", "foothill");

      expect(mockFetch).toHaveBeenCalledTimes(1);
      const [url, init] = mockFetch.mock.calls[0] as [string, RequestInit];
      expect(url).toContain("/occupations/query");
      expect(init.method).toBe("POST");
      expect((init.headers as Record<string, string>)["Content-Type"]).toBe("application/json");

      const parsed = JSON.parse(init.body as string);
      expect(parsed).toEqual({ query: "highest paying occupations", college: "foothill" });
    });

    it("returns the parsed response body on success", async () => {
      const body = {
        occupations: [],
        message: "0 results",
        cypher: null,
      };
      vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: true, json: async () => body }));

      const result = await queryOccupations("test", "foothill");
      expect(result).toEqual(body);
    });

    it("surfaces the server's error text when the response is not ok", async () => {
      vi.stubGlobal("fetch", vi.fn().mockResolvedValue({
        ok: false,
        status: 422,
        text: async () => "Query failed: invalid SOC code format",
      }));

      await expect(queryOccupations("bad", "foothill")).rejects.toThrow("Query failed: invalid SOC code format");
    });

    it("falls back to a generic 'Query failed' message when the body text is empty", async () => {
      vi.stubGlobal("fetch", vi.fn().mockResolvedValue({
        ok: false,
        status: 500,
        text: async () => "",
      }));

      await expect(queryOccupations("bad", "foothill")).rejects.toThrow("Query failed");
    });
  });
});
