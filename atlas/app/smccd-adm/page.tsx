import LandscapeDashboard from "@/college-atlas/partnerships/LandscapeDashboard";

// Advanced Manufacturing — the canonical SMCCD Advanced Manufacturing surface (sector-derived,
// 49 middle-skill SOCs), parameterized by the `smccd-adm` landscape instance.
// PUBLISHED. /smccd redirects here.
export default function SmccdAdmPage() {
  return <LandscapeDashboard instance="smccd-adm" />;
}
