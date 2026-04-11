/**
 * Tests for the students feature's API client — verifies URL
 * construction, response parsing, and error handling for the three
 * exported functions that wrap backend endpoints under /students.
 *
 * The fetch global is stubbed with vi.stubGlobal so assertions can
 * inspect the URL and request init without hitting a real backend.
 * This mocking pattern is the template the other five feature
 * api.test.ts files will follow when they are added.
 *
 * Coverage:
 *   - getStudents: URL encoding of the college parameter, successful
 *     body parsing, error branch on non-ok response
 *   - getStudent: URL includes both uuid and college, error branch
 *   - queryStudents: POST body shape, Content-Type header, successful
 *     body parsing, server error text surfaced in thrown error,
 *     fallback "Query failed" message on empty error body
 */

import { describe, it, expect, afterEach, vi } from "vitest";
import {
  getStudents,
  getStudent,
  queryStudents,
} from "./api";

// Each test stubs the global fetch with a fresh mock so assertions
// are isolated. The `vi.stubGlobal` API restores automatically after
// each test when paired with `vi.unstubAllGlobals()` in afterEach.

describe("students api client", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  describe("getStudents", () => {
    it("hits /students with the college query parameter URL-encoded", async () => {
      const mockFetch = vi.fn().mockResolvedValue({
        ok: true,
        json: async () => [],
      });
      vi.stubGlobal("fetch", mockFetch);

      await getStudents("Foothill College");

      expect(mockFetch).toHaveBeenCalledTimes(1);
      const url = mockFetch.mock.calls[0][0] as string;
      expect(url).toContain("/students?college=");
      expect(url).toContain("Foothill%20College");
    });

    it("returns the parsed JSON body on success", async () => {
      const body = [
        { uuid: "u1", primary_focus: "Business", courses_completed: 12, gpa: 3.4 },
        { uuid: "u2", primary_focus: "Nursing", courses_completed: 18, gpa: 3.8 },
      ];
      vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: true, json: async () => body }));

      const result = await getStudents("foothill");
      expect(result).toEqual(body);
    });

    it("throws a descriptive error when the response is not ok", async () => {
      vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: false, status: 500, json: async () => ({}) }));

      await expect(getStudents("foothill")).rejects.toThrow("Failed to fetch students");
    });
  });

  describe("getStudent", () => {
    it("hits /students/:uuid with both uuid and college encoded", async () => {
      const mockFetch = vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({
          uuid: "abc-123",
          primary_focus: "Business",
          courses_completed: 10,
          gpa: 3.2,
          enrollments: [],
          skills: [],
        }),
      });
      vi.stubGlobal("fetch", mockFetch);

      await getStudent("abc-123", "Foothill College");

      const url = mockFetch.mock.calls[0][0] as string;
      expect(url).toContain("/students/abc-123");
      expect(url).toContain("college=Foothill%20College");
    });

    it("throws a descriptive error when the response is not ok", async () => {
      vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: false, status: 404, json: async () => ({}) }));
      await expect(getStudent("missing", "foothill")).rejects.toThrow("Failed to fetch student");
    });
  });

  describe("queryStudents", () => {
    it("POSTs to /students/query with a JSON body containing query and college", async () => {
      const mockFetch = vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({ students: [], message: "no results", cypher: null }),
      });
      vi.stubGlobal("fetch", mockFetch);

      await queryStudents("students with highest GPA", "foothill");

      expect(mockFetch).toHaveBeenCalledTimes(1);
      const [url, init] = mockFetch.mock.calls[0] as [string, RequestInit];
      expect(url).toContain("/students/query");
      expect(init.method).toBe("POST");
      expect((init.headers as Record<string, string>)["Content-Type"]).toBe("application/json");

      const parsed = JSON.parse(init.body as string);
      expect(parsed).toEqual({ query: "students with highest GPA", college: "foothill" });
    });

    it("returns the parsed response body on success", async () => {
      const body = {
        students: [{ uuid: "u1", primary_focus: "Business", courses_completed: 12, gpa: 3.4 }],
        message: "1 result",
        cypher: "MATCH (s:Student) RETURN s LIMIT 1",
      };
      vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: true, json: async () => body }));

      const result = await queryStudents("test", "foothill");
      expect(result).toEqual(body);
    });

    it("surfaces the server's error text when the response is not ok", async () => {
      vi.stubGlobal("fetch", vi.fn().mockResolvedValue({
        ok: false,
        status: 422,
        text: async () => "Query failed: invalid Cypher",
      }));

      await expect(queryStudents("bad query", "foothill")).rejects.toThrow("Query failed: invalid Cypher");
    });

    it("falls back to a generic 'Query failed' message when the body text is empty", async () => {
      vi.stubGlobal("fetch", vi.fn().mockResolvedValue({
        ok: false,
        status: 500,
        text: async () => "",
      }));

      await expect(queryStudents("bad query", "foothill")).rejects.toThrow("Query failed");
    });
  });
});
