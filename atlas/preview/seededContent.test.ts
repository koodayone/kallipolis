/**
 * Coverage:
 *   - atlas/preview/seededPartnerships.ts schema-version invariant
 *   - atlas/preview/seededPartnerships.ts stable-slug id invariant
 *
 * Guards the schema contract between seeded preview content and the
 * runtime save types. If PROPOSAL_SCHEMA_VERSION bumps, every seeded
 * partnership must be regenerated (see atlas/preview/README.md); this
 * test fails the build until the seeds catch up.
 */

import { describe, it, expect } from "vitest";
import { SEEDED_PARTNERSHIPS } from "./seededPartnerships";
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
