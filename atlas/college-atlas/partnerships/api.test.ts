/**
 * Tests for the partnerships SVAMP program API client — URL construction for
 * getLandscapeProgram, which gained an optional `college` parameter for the
 * targeted (college × TOP) view (Phase 1 of the lens-grammar synthesis).
 *
 * Follows the fetch-mocking pattern from college-atlas/occupations/api.test.ts.
 *
 * Coverage:
 *   - getLandscapeProgram(top6): hits /partnerships/svamp/program/{top6} with no
 *     query string (the consortium-aggregated view)
 *   - getLandscapeProgram(top6, college): appends ?college=<value> (the targeted
 *     slice), with the college name carried into the query
 *   - error branch throws on a non-ok response
 */

import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";
import { getLandscapeProgram, getLandscapeOccupation, _resetSvampCacheForTests } from "./api";

describe("partnerships svamp program api client", () => {
  beforeEach(() => {
    // The SVAMP getters session-cache their promises; reset per test so each
    // test's fetch mock is actually exercised.
    _resetSvampCacheForTests();
  });
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("aggregated view: no college query string", async () => {
    const mockFetch = vi.fn().mockResolvedValue({ ok: true, json: async () => ({}) });
    vi.stubGlobal("fetch", mockFetch);

    await getLandscapeProgram("094800");

    const url = mockFetch.mock.calls[0][0] as string;
    expect(url).toContain("/partnerships/svamp/program/094800");
    expect(url).not.toContain("?");
  });

  it("targeted view: appends the college query parameter", async () => {
    const mockFetch = vi.fn().mockResolvedValue({ ok: true, json: async () => ({}) });
    vi.stubGlobal("fetch", mockFetch);

    await getLandscapeProgram("094800", "De Anza College");

    const url = mockFetch.mock.calls[0][0] as string;
    expect(url).toContain("/partnerships/svamp/program/094800?");
    expect(url).toContain("college=De");
    expect(url).toContain("Anza");
  });

  it("throws on a non-ok response", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: false }));
    await expect(getLandscapeProgram("094800")).rejects.toThrow();
  });

  it("getLandscapeOccupation hits /svamp/occupation/{soc} with the SOC encoded", async () => {
    const mockFetch = vi.fn().mockResolvedValue({ ok: true, json: async () => ({}) });
    vi.stubGlobal("fetch", mockFetch);

    await getLandscapeOccupation("17-3027");

    const url = mockFetch.mock.calls[0][0] as string;
    expect(url).toContain("/partnerships/svamp/occupation/17-3027");
  });
});
