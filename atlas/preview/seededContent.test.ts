/**
 * Covers:
 *   - atlas/preview/seededPartnerships.ts
 *   - atlas/preview/seededSwpProjects.ts
 *
 * Guards the schema contract between seeded preview content and the
 * runtime save types. If PROPOSAL_SCHEMA_VERSION bumps, every seeded
 * partnership must be regenerated (see atlas/preview/README.md); this
 * test fails the build until the seeds catch up.
 *
 * Also verifies SWP seeds reference partnership seeds by id — a stale
 * partnershipId would silently break the Manage Mode link-back.
 */

import { describe, it, expect } from "vitest";
import { SEEDED_PARTNERSHIPS } from "./seededPartnerships";
import { SEEDED_SWP_PROJECTS } from "./seededSwpProjects";
import { PROPOSAL_SCHEMA_VERSION } from "@/college-atlas/partnerships/savedProposals";

describe("seeded partnerships", () => {
  it("every seeded partnership carries the current PROPOSAL_SCHEMA_VERSION", () => {
    for (const [collegeName, partnerships] of Object.entries(SEEDED_PARTNERSHIPS)) {
      for (const p of partnerships) {
        expect(
          p.schemaVersion,
          `seeded partnership for "${collegeName}" (id=${p.id}) is on schema v${p.schemaVersion}, expected v${PROPOSAL_SCHEMA_VERSION}`,
        ).toBe(PROPOSAL_SCHEMA_VERSION);
      }
    }
  });

  it("every seeded partnership has a stable slug id (no random UUID)", () => {
    for (const [collegeName, partnerships] of Object.entries(SEEDED_PARTNERSHIPS)) {
      for (const p of partnerships) {
        expect(
          p.id.startsWith("seed-"),
          `seeded partnership for "${collegeName}" uses id "${p.id}"; expected stable slug prefixed with "seed-"`,
        ).toBe(true);
      }
    }
  });
});

describe("seeded SWP projects", () => {
  it("every seeded SWP project references a seeded partnership id for the same college", () => {
    for (const [collegeName, swpProjects] of Object.entries(SEEDED_SWP_PROJECTS)) {
      const partnershipIds = new Set(
        (SEEDED_PARTNERSHIPS[collegeName] ?? []).map((p) => p.id),
      );
      for (const s of swpProjects) {
        expect(
          partnershipIds.has(s.partnershipId),
          `seeded SWP for "${collegeName}" (id=${s.id}) references partnershipId "${s.partnershipId}" which is not in SEEDED_PARTNERSHIPS for that college`,
        ).toBe(true);
      }
    }
  });
});
