import LandscapeClient from "./LandscapeClient";
import { landscapeRouteParams } from "@/college-atlas/partnerships/landscapeIndex";

// Generated member×sector landscapes (any college/district the catalog
// publishes). generateStaticParams enumerates the live instances from the
// backend index at build time; the static export pre-renders an inert "Loading…"
// shell per instance (the dashboard mounts client-side), so the build stays
// cheap even at full catalog size. Un-listed paths 404 (no SPA fallback) —
// the same posture as the curated /[collegeId] routes. Pinned instances
// (/svamp, /smccd-*) keep their own flat routes; this namespace is additive.
export async function generateStaticParams() {
  return landscapeRouteParams();
}

export default function LandscapePage() {
  return <LandscapeClient />;
}
