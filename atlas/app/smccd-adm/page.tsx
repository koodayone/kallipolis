import SvampDashboard from "@/college-atlas/partnerships/SvampDashboard";

// Advanced Manufacturing — the canonical SMCCD Advanced Manufacturing surface (sector-derived,
// 49 middle-skill SOCs), parameterized by the `smccd-adm` landscape instance.
// PUBLISHED. /smccd redirects here.
export default function SmccdAdmPage() {
  return <SvampDashboard instance="smccd-adm" />;
}
