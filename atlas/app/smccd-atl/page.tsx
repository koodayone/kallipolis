import SvampDashboard from "@/college-atlas/partnerships/SvampDashboard";

// Advanced Transportation & Logistics — a sector-derived member×sector instance of the dashboard engine,
// parameterized by the `smccd-atl` landscape instance. DRAFT: the layout gates it
// to local builds.
export default function SmccdAtlPage() {
  return <SvampDashboard instance="smccd-atl" />;
}
