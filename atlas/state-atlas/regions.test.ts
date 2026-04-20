/**
 * Tests for CALIFORNIA_REGIONS — the eight California Community Colleges
 * Strong Workforce Program regional consortia that partition California's
 * 58 counties and group the state's community colleges.
 *
 * These invariants guard the data that drives the State Atlas hover
 * affordance. Regional membership is institutionally load-bearing — it
 * determines which consortium a college belongs to for SWP funding —
 * and the tests make drift in the region set, the county partition, or
 * the college-to-region assignments loud instead of silent.
 *
 * Coverage:
 *   - CALIFORNIA_REGIONS contains exactly the 8 CCC consortia IDs
 *   - every California county appears in exactly one region's counties[]
 *   - all 58 California counties are covered by the union of region counties
 *   - every College.regionId resolves to a Region in CALIFORNIA_REGIONS
 *   - each Region.collegeCount equals the count of colleges with that regionId
 *   - COUNTY_TO_REGION indexes every county to its owning region
 *   - FEATURED_COLLEGES has exactly one anchor per consortium (MVP scope)
 */

import { describe, it, expect } from "vitest";
import {
  CALIFORNIA_REGIONS,
  CALIFORNIA_COLLEGES,
  COUNTY_TO_REGION,
} from "./californiaColleges";
import { FEATURED_COLLEGES } from "./CaliforniaMap";

const CALIFORNIA_COUNTIES = [
  "Alameda", "Alpine", "Amador", "Butte", "Calaveras", "Colusa", "Contra Costa",
  "Del Norte", "El Dorado", "Fresno", "Glenn", "Humboldt", "Imperial", "Inyo",
  "Kern", "Kings", "Lake", "Lassen", "Los Angeles", "Madera", "Marin", "Mariposa",
  "Mendocino", "Merced", "Modoc", "Mono", "Monterey", "Napa", "Nevada", "Orange",
  "Placer", "Plumas", "Riverside", "Sacramento", "San Benito", "San Bernardino",
  "San Diego", "San Francisco", "San Joaquin", "San Luis Obispo", "San Mateo",
  "Santa Barbara", "Santa Clara", "Santa Cruz", "Shasta", "Sierra", "Siskiyou",
  "Solano", "Sonoma", "Stanislaus", "Sutter", "Tehama", "Trinity", "Tulare",
  "Tuolumne", "Ventura", "Yolo", "Yuba",
];

describe("CALIFORNIA_REGIONS", () => {
  it("contains exactly the 8 CCC regional consortia", () => {
    expect(CALIFORNIA_REGIONS.map((r) => r.id).sort()).toEqual([
      "bay-area",
      "central-valley-mother-lode",
      "inland-empire-desert",
      "los-angeles",
      "north-far-north",
      "orange-county",
      "san-diego-imperial",
      "south-central-coast",
    ]);
  });

  it("covers all 58 California counties across regions", () => {
    const all = CALIFORNIA_REGIONS.flatMap((r) => r.counties).sort();
    expect(all).toEqual([...CALIFORNIA_COUNTIES].sort());
    expect(all).toHaveLength(58);
  });

  it("assigns each county to exactly one region", () => {
    const seen = new Map<string, string>();
    for (const region of CALIFORNIA_REGIONS) {
      for (const county of region.counties) {
        const prior = seen.get(county);
        if (prior) {
          throw new Error(
            `County "${county}" appears in both "${prior}" and "${region.id}"`,
          );
        }
        seen.set(county, region.id);
      }
    }
    expect(seen.size).toBe(58);
  });
});

describe("CALIFORNIA_COLLEGES region assignments", () => {
  const regionIds = new Set(CALIFORNIA_REGIONS.map((r) => r.id));

  it("resolves every college's regionId to a known region", () => {
    const orphans = CALIFORNIA_COLLEGES
      .filter((c) => !regionIds.has(c.regionId))
      .map((c) => ({ id: c.id, regionId: c.regionId }));
    expect(orphans).toEqual([]);
  });

  it("matches each Region.collegeCount to the count of its colleges", () => {
    for (const region of CALIFORNIA_REGIONS) {
      const actual = CALIFORNIA_COLLEGES.filter(
        (c) => c.regionId === region.id,
      ).length;
      expect({ id: region.id, count: region.collegeCount }).toEqual({
        id: region.id,
        count: actual,
      });
    }
  });
});

describe("FEATURED_COLLEGES (MVP anchor set)", () => {
  const regionIds = CALIFORNIA_REGIONS.map((r) => r.id);
  const byId = new Map(CALIFORNIA_COLLEGES.map((c) => [c.id, c]));

  it("contains exactly 8 anchor colleges, one per consortium", () => {
    expect(FEATURED_COLLEGES.size).toBe(8);
  });

  it("resolves every featured college id to a real college", () => {
    for (const id of FEATURED_COLLEGES) {
      expect(byId.get(id), `featured id "${id}" is not in CALIFORNIA_COLLEGES`).toBeDefined();
    }
  });

  it("covers every consortium exactly once", () => {
    const featuredRegions = Array.from(FEATURED_COLLEGES)
      .map((id) => byId.get(id)!.regionId)
      .sort();
    expect(featuredRegions).toEqual([...regionIds].sort());
  });
});

describe("COUNTY_TO_REGION", () => {
  it("indexes every California county", () => {
    for (const county of CALIFORNIA_COUNTIES) {
      expect(COUNTY_TO_REGION[county]?.id).toBeTruthy();
    }
  });

  it("resolves each county to the region whose counties[] contains it", () => {
    for (const county of CALIFORNIA_COUNTIES) {
      const region = COUNTY_TO_REGION[county];
      expect(region.counties).toContain(county);
    }
  });
});
