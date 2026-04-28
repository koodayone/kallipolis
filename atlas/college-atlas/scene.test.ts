/**
 * Tests for the College Atlas scene vocabulary — the FormKey set and
 * the FORM_URL_SLUGS map that connect the five-form layout to the
 * route URLs under /[collegeId]/<form-slug>.
 *
 * These tests guard the one-hop mapping between FormKey, FORM_NAMES,
 * and FORM_URL_SLUGS so a future refactor cannot silently break URL
 * generation for any form.
 *
 * Coverage:
 *   - ALL_FORM_KEYS and FORM_NAMES cover the same five forms
 *   - Every FormKey in ALL_FORM_KEYS has a FORM_URL_SLUGS entry
 *   - All slugs are kebab-case (no underscores, no uppercase)
 *   - All slugs round-trip with their FormKey (identity mapping)
 *   - Every slug is unique so every form produces a distinct route
 */

import { describe, it, expect } from "vitest";
import { ALL_FORM_KEYS, FORM_NAMES, FORM_URL_SLUGS, type FormKey } from "./scene";

describe("college-atlas scene vocabulary", () => {
  it("ALL_FORM_KEYS and FORM_NAMES cover the same five forms", () => {
    const keysFromAll = new Set(ALL_FORM_KEYS);
    const keysFromNames = new Set(Object.keys(FORM_NAMES) as FormKey[]);
    expect(keysFromAll).toEqual(keysFromNames);
    expect(keysFromAll.size).toBe(5);
  });

  it("FORM_URL_SLUGS has an entry for every FormKey in ALL_FORM_KEYS", () => {
    // This guards the one-hop URL mapping. If a future refactor adds a form
    // to ALL_FORM_KEYS without adding its slug, generating a route URL for
    // that form would silently produce "undefined" in the path.
    for (const key of ALL_FORM_KEYS) {
      expect(FORM_URL_SLUGS[key]).toBeDefined();
      expect(typeof FORM_URL_SLUGS[key]).toBe("string");
      expect(FORM_URL_SLUGS[key].length).toBeGreaterThan(0);
    }
  });

  it("all URL slugs are kebab-case (no underscores, no uppercase)", () => {
    // Kebab-case is the convention that keeps the URL aligned with backend
    // route prefixes and the docs. All five FormKeys are single words, so
    // every slug is the identity transform.
    for (const key of ALL_FORM_KEYS) {
      const slug = FORM_URL_SLUGS[key];
      expect(slug).not.toMatch(/[_A-Z]/);
      expect(slug).toMatch(/^[a-z][a-z-]*$/);
    }
  });

  it("every slug equals its FormKey (no transformation needed for single-word keys)", () => {
    for (const key of ALL_FORM_KEYS) {
      expect(FORM_URL_SLUGS[key]).toBe(key);
    }
  });

  it("all slugs are unique so every form produces a distinct route", () => {
    const slugs = Object.values(FORM_URL_SLUGS);
    const unique = new Set(slugs);
    expect(unique.size).toBe(slugs.length);
  });
});
