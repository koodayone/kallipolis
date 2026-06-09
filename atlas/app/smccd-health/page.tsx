import SvampDashboard from "@/college-atlas/partnerships/SvampDashboard";

// The SMCCD Life Sciences & Health Technology surface — instance #3 of the same
// dashboard engine, parameterized by the `smccd-health` landscape instance.
// Same components as /svamp and /smccd; only the instance differs (member
// colleges, target SOCs, program scope, identity, API id). DRAFT: the
// surrounding layout gates it to local builds.
export default function SmccdHealthPage() {
  return <SvampDashboard instance="smccd-health" />;
}
