// Client for the backend landscape index (`GET /partnerships/landscapes`) — the
// live (member × sector) catalog for the generated `/landscape/[member]/[sector]`
// route. Generated instances have no `landscapeInstances.ts` row, so their
// identity (name, accent, per-college configs) is built from the index entry,
// which the backend composes from the member catalog. The pinned instances keep
// their hand-authored rows; this is only for the generated long tail.

import { API_BASE } from "@/api";
import { getCollegeAtlasConfig } from "@/config/collegeAtlasConfigs";
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

// Generated landscapes are served by SPA fallback (see public/_redirects), NOT by
// pre-rendering every instance. Pre-rendering the full catalog emitted ~3,000
// pages × several files each and blew past Cloudflare Pages' 20,000-file deploy
// limit — the deploy validation hard-failed even though the build succeeded. So
// the build pre-renders exactly ONE sentinel shell per route (foothill·AM); the
// _redirects splat serves that shell for any /landscape/<member>/<sector> miss,
// and the client renders the real instance from the live URL (parseLandscapePath
// + the index fetch). The deploy stays O(1) in pages; the catalog stays complete.
// `output: export` also ERRORS on a dynamic route whose generateStaticParams
// returns [] — the constant sentinel keeps it non-empty and decouples the build
// from backend availability entirely (no build-time fetch).
const SENTINEL = { member: "foothill", sector: "adm" };

/** Sentinel-only params for the generated dashboard + report routes. The full
 *  catalog is reached at runtime via SPA fallback, not pre-rendered. */
export async function landscapeRouteParams(): Promise<{ member: string; sector: string }[]> {
  return [SENTINEL];
}

/** Sentinel-only param for the member-root route. */
export async function memberRouteParams(): Promise<{ member: string }[]> {
  return [{ member: SENTINEL.member }];
}

/** (member, sector) parsed from a `/landscape/<member>/<sector>[/report]`
 *  pathname. Generated routes are SPA-fallback-served — one sentinel shell stands
 *  in for every instance — so the rendered identity must come from the live URL,
 *  not the route params baked into the sentinel's static HTML (which would always
 *  read `foothill/adm`). Trailing/leading slashes tolerated. */
export function parseLandscapePath(pathname: string): { member: string; sector: string } {
  const parts = pathname.replace(/^\/+|\/+$/g, "").split("/"); // ["landscape", member, sector, "report"?]
  return { member: parts[1] ?? "", sector: parts[2] ?? "" };
}

/** Resolve a college NAME to its single-college landscape `member_id`, over the
 *  live index. The frontend `collegeId` and the backend `member_id` diverge for a
 *  chunk of colleges (`sandiegomesa`→`sdmesa`), so the join is on the college NAME
 *  (`SchoolConfig.name` == the backend `member_label`), not the id — a fuzzy id
 *  match is unsafe (it collapses San Diego Mesa/Miramar/City onto one member).
 *  Exact label match first, then a `+ " College"` fallback for the handful of
 *  config names that omit the suffix the backend label carries (e.g. "Los Angeles
 *  Trade-Technical"). Restricted to `member_kind === "college"` so a name can never
 *  resolve to a district or consortium. Null when the college has no landscape. */
export function memberIdForCollegeName(
  name: string,
  entries: LandscapeIndexEntry[],
): string | null {
  const colleges = entries.filter((e) => e.member_kind === "college");
  const exact = colleges.find((e) => e.member_label === name);
  if (exact) return exact.member_id;
  const suffixed = colleges.find((e) => e.member_label === `${name} College`);
  return suffixed?.member_id ?? null;
}

/** Resolve a frontend `collegeId` to its landscape `member_id` via the name-join
 *  above (the `collegeId → SchoolConfig.name → member_label → member_id` chain).
 *  The redirect at `/[collegeId]/partnerships` uses this to bounce to
 *  `/landscape/<member>`. Null when the id is unknown or the college has no landscape. */
export function memberIdForCollege(
  collegeId: string,
  entries: LandscapeIndexEntry[],
): string | null {
  const name = getCollegeAtlasConfig(collegeId)?.name;
  return name ? memberIdForCollegeName(name, entries) : null;
}

/** Flagship-first sector order: land on Advanced Manufacturing where present, then
 *  the other priority (CTE-core / tech-forward) sectors, before the broader-access
 *  industries. Mirrors the backend's member×sector priority. */
export const DEFAULT_SECTOR_PRIORITY = [
  "adm", "biotech", "ecu", "atl", "ict", "health", "business", "public_safety", "edhd", "agwet", "retail",
];

/** The sector a member-root or college redirect lands on: the first sector in
 *  priority order the member is actually live in, else its first live sector, else
 *  null (no landscape). Shared by MemberRedirect and the /[collegeId]/partnerships
 *  redirect so the landing sector never drifts between the two entry points. */
export function flagshipSectorFor(memberId: string, entries: LandscapeIndexEntry[]): string | null {
  const live = new Set(entries.filter((e) => e.member_id === memberId).map((e) => e.sector_id));
  return DEFAULT_SECTOR_PRIORITY.find((s) => live.has(s)) ?? [...live][0] ?? null;
}

/** Build a LandscapeInstance for a generated instance from its index entry —
 *  the identity LandscapeDashboard/LandscapeReport consume (name, accent, collegeIds). */
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
