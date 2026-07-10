import LandscapeDashboard from "@/college-atlas/partnerships/LandscapeDashboard";

// Ag, Water & Environmental Technologies — a sector-derived member×sector instance of the dashboard engine,
// parameterized by the `smccd-agwet` landscape instance. DRAFT: the layout gates it
// to local builds.
export default function SmccdAgwetPage() {
  return <LandscapeDashboard instance="smccd-agwet" />;
}
