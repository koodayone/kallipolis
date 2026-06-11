import ReportClient from "./ReportClient";
import { fetchLandscapeIndex } from "@/college-atlas/partnerships/landscapeIndex";

// Report route for generated member×sector landscapes (the narrative surface the
// masthead REPORT toggle links to). generateStaticParams enumerates the live
// instances from the backend index at build time, mirroring the dashboard route.
export async function generateStaticParams() {
  const index = await fetchLandscapeIndex();
  return index.map((e) => ({ member: e.member_id, sector: e.sector_id }));
}

export default function GeneratedReportPage() {
  return <ReportClient />;
}
