import SvampDashboard from "@/college-atlas/partnerships/SvampDashboard";

// Business & Entrepreneurship — a sector-derived member×sector instance of the dashboard engine,
// parameterized by the `smccd-business` landscape instance. DRAFT: the layout gates it
// to local builds.
export default function SmccdBusinessPage() {
  return <SvampDashboard instance="smccd-business" />;
}
