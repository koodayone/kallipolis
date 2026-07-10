import LandscapeDashboard from "@/college-atlas/partnerships/LandscapeDashboard";

// Energy, Construction & Utilities — a sector-derived member×sector instance of the dashboard engine,
// parameterized by the `smccd-ecu` landscape instance. DRAFT: the layout gates it
// to local builds.
export default function SmccdEcuPage() {
  return <LandscapeDashboard instance="smccd-ecu" />;
}
