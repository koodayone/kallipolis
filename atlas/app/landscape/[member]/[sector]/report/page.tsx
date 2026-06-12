import ReportClient from "./ReportClient";
import { landscapeRouteParams } from "@/college-atlas/partnerships/landscapeIndex";

// Report route for generated member×sector landscapes (the narrative surface the
// masthead REPORT toggle links to). generateStaticParams enumerates the live
// instances from the backend index at build time, mirroring the dashboard route.
export async function generateStaticParams() {
  return landscapeRouteParams();
}

export default function GeneratedReportPage() {
  return <ReportClient />;
}
