// Curated partnership proposals shipped with the atlas bundle for preview
// mode. These seeds are the demonstration substrate the partnership Manage
// Mode reads when no real saves exist (preview mode disables Save).
//
// Keyed by college *display name* to match the lookup convention used by
// PartnershipsView (which passes `school.name` through to localStorage and
// API calls — the same key drives seeded reads).
//
// Regeneration procedure: see ./README.md. The schema must match
// PROPOSAL_SCHEMA_VERSION from savedProposals.ts — the Vitest suite fails
// the build if a seeded entry drifts.
//
// **Empty pending regeneration.** The schema bump from v8 to v9 (four-section
// artifact + SwpEvidence, no engagement_type/partnership_type) invalidated
// the prior seed set. Until the seed pipeline runs against the new artifact
// shape, preview mode shows no cached examples — live generation still
// works (auth-gated). Run the regeneration procedure in README.md to
// repopulate.

import type { SavedProposal } from "@/college-atlas/partnerships/savedProposals";
import { CALIFORNIA_COLLEGES } from "@/state-atlas/californiaColleges";
import { FEATURED_COLLEGES } from "@/state-atlas/featuredColleges";

const FEATURED_NAMES = CALIFORNIA_COLLEGES.filter((c) =>
  FEATURED_COLLEGES.has(c.id),
).map((c) => c.name);

const SEEDED_BY_NAME: Record<string, SavedProposal[]> = {};

// Keyed by college display name. Auto-fills any featured college that
// lacks a seeded entry with an empty array so downstream lookups never
// return undefined for a valid college.
export const SEEDED_PARTNERSHIPS: Record<string, SavedProposal[]> = {
  ...Object.fromEntries(FEATURED_NAMES.map((name) => [name, [] as SavedProposal[]])),
  ...SEEDED_BY_NAME,
};

export function getSeededProposals(collegeName: string): SavedProposal[] {
  return SEEDED_PARTNERSHIPS[collegeName] ?? [];
}
