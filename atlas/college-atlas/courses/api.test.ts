/**
 * Tests for the courses feature's API client — verifies URL
 * construction, response parsing, and error handling for the three
 * exported functions that wrap backend endpoints under /courses.
 *
 * Follows the fetch-mocking pattern established in
 * college-atlas/students/api.test.ts: vi.stubGlobal injects a mock
 * fetch, tests inspect the URL and request init, and afterEach
 * restores the global with vi.unstubAllGlobals().
 *
 * Coverage:
 *   - getDepartments: URL encoding of college, successful body parsing,
 *     error branch on non-ok response
 *   - getCourses: URL includes department and college both encoded,
 *     error branch
 *   - queryCourses: POST body shape, Content-Type header, successful
 *     body parsing, server error text surfaced in thrown error,
 *     fallback "Query failed" message on empty error body
 */

import { describe, it, expect, afterEach, vi } from "vitest";
import {
  getDepartments,
  getCourses,
  queryCourses,
} from "./api";

describe("courses api client", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  describe("getDepartments", () => {
    it("hits /courses/departments with the college query parameter URL-encoded", async () => {
      const mockFetch = vi.fn().mockResolvedValue({
        ok: true,
        json: async () => [],
      });
      vi.stubGlobal("fetch", mockFetch);

      await getDepartments("Foothill College");

      expect(mockFetch).toHaveBeenCalledTimes(1);
      const url = mockFetch.mock.calls[0][0] as string;
      expect(url).toContain("/courses/departments?college=");
      expect(url).toContain("Foothill%20College");
    });

    it("returns the parsed JSON body on success", async () => {
      const body = [
        { department: "Business", course_count: 42 },
        { department: "Nursing", course_count: 31 },
      ];
      vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: true, json: async () => body }));

      const result = await getDepartments("foothill");
      expect(result).toEqual(body);
    });

    it("throws a descriptive error when the response is not ok", async () => {
      vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: false, status: 500, json: async () => ({}) }));

      await expect(getDepartments("foothill")).rejects.toThrow("Failed to fetch departments");
    });
  });

  describe("getCourses", () => {
    it("hits /courses/ with department and college both URL-encoded", async () => {
      const mockFetch = vi.fn().mockResolvedValue({
        ok: true,
        json: async () => [],
      });
      vi.stubGlobal("fetch", mockFetch);

      await getCourses("Business & Management", "Foothill College");

      const url = mockFetch.mock.calls[0][0] as string;
      expect(url).toContain("/courses/");
      expect(url).toContain("department=Business%20%26%20Management");
      expect(url).toContain("college=Foothill%20College");
    });

    it("throws a descriptive error when the response is not ok", async () => {
      vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: false, status: 404, json: async () => ({}) }));
      await expect(getCourses("Biology", "foothill")).rejects.toThrow("Failed to fetch courses");
    });
  });

  describe("queryCourses", () => {
    it("POSTs to /courses/query with a JSON body containing query and college", async () => {
      const mockFetch = vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({ courses: [], message: "no results", cypher: null }),
      });
      vi.stubGlobal("fetch", mockFetch);

      await queryCourses("courses developing machine learning skills", "foothill");

      expect(mockFetch).toHaveBeenCalledTimes(1);
      const [url, init] = mockFetch.mock.calls[0] as [string, RequestInit];
      expect(url).toContain("/courses/query");
      expect(init.method).toBe("POST");
      expect((init.headers as Record<string, string>)["Content-Type"]).toBe("application/json");

      const parsed = JSON.parse(init.body as string);
      expect(parsed).toEqual({ query: "courses developing machine learning skills", college: "foothill" });
    });

    it("returns the parsed response body on success", async () => {
      const body = {
        courses: [{
          name: "Intro to ML",
          code: "CS 101",
          description: "Fundamentals of machine learning",
          learning_outcomes: [],
          course_objectives: [],
          skill_mappings: ["Machine Learning"],
        }],
        message: "1 result",
        cypher: "MATCH (c:Course) RETURN c LIMIT 1",
      };
      vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: true, json: async () => body }));

      const result = await queryCourses("test", "foothill");
      expect(result).toEqual(body);
    });

    it("surfaces the server's error text when the response is not ok", async () => {
      vi.stubGlobal("fetch", vi.fn().mockResolvedValue({
        ok: false,
        status: 422,
        text: async () => "Query failed: ambiguous skill match",
      }));

      await expect(queryCourses("bad", "foothill")).rejects.toThrow("Query failed: ambiguous skill match");
    });

    it("falls back to a generic 'Query failed' message when the body text is empty", async () => {
      vi.stubGlobal("fetch", vi.fn().mockResolvedValue({
        ok: false,
        status: 500,
        text: async () => "",
      }));

      await expect(queryCourses("bad", "foothill")).rejects.toThrow("Query failed");
    });
  });
});
