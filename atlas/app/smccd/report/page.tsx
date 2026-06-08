import ClientPage from "./ClientPage";

// The SMCCD report — instance #2's narrative surface, mirroring /svamp/report.
// The dashboard owns the root (/smccd); this is its descent, one click away via
// SurfaceNav with the selection preserved through the shared svampUrl params.
export default function SmccdReportPage() {
  return <ClientPage />;
}
