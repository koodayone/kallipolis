// Client for the backend landscape index (`GET /partnerships/landscapes`) — the
// live (member × sector) catalog for the generated `/landscape/[member]/[sector]`
// route. Generated instances have no `landscapeInstances.ts` row, so their
// identity (name, accent, per-college configs) is built from the index entry,
// which the backend composes from the member catalog. The pinned instances keep
// their hand-authored rows; this is only for the generated long tail.

import { API_BASE } from "@/api";
import type { LandscapeInstance } from "@/college-atlas/partnerships/landscapeInstances";

export type LandscapeIndexEntry = {
  id: string;            // "{member}-{sector}"
  member_id: string;
  member_label: string;
  member_kind: string;   // college | district | region | consortium
  colleges: string[];    // college-config ids the member aggregates over
  sector_id: string;
  sector_label: string;
  accent: string;        // sector accent (scope color)
  region: string | null;
};

let _cache: Promise<LandscapeIndexEntry[]> | null = null;

/** The live landscape catalog. Cached per page load; `[]` on any failure so a
 *  build or render never hard-fails on the index being unavailable. */
export function fetchLandscapeIndex(): Promise<LandscapeIndexEntry[]> {
  if (_cache) return _cache;
  _cache = (async () => {
    try {
      const res = await fetch(`${API_BASE}/partnerships/landscapes`);
      if (!res.ok) return [];
      const data = await res.json();
      return (data?.instances ?? []) as LandscapeIndexEntry[];
    } catch {
      return [];
    }
  })();
  return _cache;
}

// Build-resilience sentinel: `output: export` ERRORS on a dynamic route whose
// generateStaticParams returns []. The route params come from a build-time fetch
// of the backend index, which is empty if the backend isn't deployed yet (or is
// briefly down). Emitting one real, stable (member, sector) keeps the build from
// failing in that window — a rebuild once the index is live pre-renders the full
// set, and even the sentinel page resolves correctly at runtime via the client
// index fetch. Foothill·AM is a reliably-live comprehensive instance.
const SENTINEL = { member: "foothill", sector: "adm" };

/** (member, sector) params for the generated dashboard + report routes,
 *  guaranteed non-empty (see SENTINEL). */
export async function landscapeRouteParams(): Promise<{ member: string; sector: string }[]> {
  const idx = await fetchLandscapeIndex();
  const params = idx.map((e) => ({ member: e.member_id, sector: e.sector_id }));
  return params.length ? params : [SENTINEL];
}

/** Distinct-member params for the member-root route, guaranteed non-empty. */
export async function memberRouteParams(): Promise<{ member: string }[]> {
  const idx = await fetchLandscapeIndex();
  const members = [...new Set(idx.map((e) => e.member_id))].map((member) => ({ member }));
  return members.length ? members : [{ member: SENTINEL.member }];
}

/** Build a LandscapeInstance for a generated instance from its index entry —
 *  the identity SvampDashboard/SvampView consume (name, accent, collegeIds). */
export function generatedInstance(entry: LandscapeIndexEntry): LandscapeInstance {
  return {
    id: entry.id,
    name: `${entry.member_label} — ${entry.sector_label}`,
    shortTitle: entry.member_label,
    accent: entry.accent,
    collegeIds: entry.colleges,
    published: true,
  };
}
