import LandscapeDashboard from "@/college-atlas/partnerships/LandscapeDashboard";

// Public Safety — a sector-derived member×sector instance of the dashboard engine,
// parameterized by the `smccd-public_safety` landscape instance. DRAFT: the layout gates it
// to local builds.
export default function SmccdPublicSafetyPage() {
  return <LandscapeDashboard instance="smccd-public_safety" />;
}
