import { FEATURED_COLLEGES } from "@/state-atlas/featuredColleges";
import ReportClient from "./ReportClient";

// Report surface for the single-college in-place landscape — the narrative dual
// of /[collegeId]/partnerships, the target of the masthead REPORT toggle (SurfaceNav
// is path-relative, so on /[collegeId]/partnerships it points here). Statically
// pre-rendered per featured college, mirroring the dashboard route; the selected
// sector rides ?sector= (preserved across the toggle).
export async function generateStaticParams() {
  return Array.from(FEATURED_COLLEGES).map((collegeId) => ({ collegeId }));
}

export default function Page() {
  return <ReportClient />;
}
