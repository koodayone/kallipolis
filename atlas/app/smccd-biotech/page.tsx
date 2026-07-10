import LandscapeDashboard from "@/college-atlas/partnerships/LandscapeDashboard";

// The SMCCD Life Sciences / Biotech surface — a sector-derived member×sector
// instance of the same dashboard engine, parameterized by the `smccd-biotech`
// landscape instance. Same components as the other landscapes; only the
// instance differs (member colleges, sector SOC set, identity, API id). DRAFT:
// the surrounding layout gates it to local builds.
export default function SmccdBiotechPage() {
  return <LandscapeDashboard instance="smccd-biotech" />;
}
