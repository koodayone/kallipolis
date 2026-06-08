import SvampDashboard from "@/college-atlas/partnerships/SvampDashboard";

// The SMCCD aggregated-landscape surface (San Mateo CCD — Advanced
// Manufacturing): instance #2 of the same dashboard engine, parameterized by
// the `smccd` landscape instance. Same components as /svamp; only the instance
// differs (member colleges, identity, API id).
export default function SmccdPage() {
  return <SvampDashboard instance="smccd" />;
}
