import SvampDashboard from "@/college-atlas/partnerships/SvampDashboard";

// Retail, Hospitality & Tourism — a sector-derived member×sector instance of the dashboard engine,
// parameterized by the `smccd-retail` landscape instance. DRAFT: the layout gates it
// to local builds.
export default function SmccdRetailPage() {
  return <SvampDashboard instance="smccd-retail" />;
}
