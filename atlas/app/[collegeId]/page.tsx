// Server shell for the college atlas home page. Exposes the route's
// static params so the static export build knows which college slugs
// to prerender — layout-level generateStaticParams is evaluated for the
// layout only, so each page needs its own export alongside the client
// rendering it wraps.

import { FEATURED_COLLEGES } from "@/state-atlas/featuredColleges";
import HomeClientPage from "./HomeClientPage";

export async function generateStaticParams() {
  return Array.from(FEATURED_COLLEGES).map((collegeId) => ({ collegeId }));
}

export default function Page() {
  return <HomeClientPage />;
}
