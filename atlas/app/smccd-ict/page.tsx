import SvampDashboard from "@/college-atlas/partnerships/SvampDashboard";

// ICT / Digital Media — a sector-derived member×sector instance of the dashboard engine,
// parameterized by the `smccd-ict` landscape instance. DRAFT: the layout gates it
// to local builds.
export default function SmccdIctPage() {
  return <SvampDashboard instance="smccd-ict" />;
}
