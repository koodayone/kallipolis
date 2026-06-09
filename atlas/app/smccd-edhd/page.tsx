import SvampDashboard from "@/college-atlas/partnerships/SvampDashboard";

// Education & Human Development — a sector-derived member×sector instance of the dashboard engine,
// parameterized by the `smccd-edhd` landscape instance. DRAFT: the layout gates it
// to local builds.
export default function SmccdEdhdPage() {
  return <SvampDashboard instance="smccd-edhd" />;
}
