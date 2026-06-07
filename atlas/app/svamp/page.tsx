import SvampDashboard from "@/college-atlas/partnerships/SvampDashboard";

// The root SVAMP surface is the dashboard (decided 2026-06-07, after the
// responsive re-architecture removed its viewport gate — it now renders at
// every width). The report is the citeable, narrated descent at
// /svamp/report, one click away with the selection intact (the two surfaces
// share the svampUrl vocabulary).
export default function SvampPage() {
  return <SvampDashboard />;
}
