import MemberRedirect from "./MemberRedirect";
import { fetchLandscapeIndex } from "@/college-atlas/partnerships/landscapeIndex";

// Member-root route: /landscape/<member> bounces to the member's flagship sector
// (see MemberRedirect), so a member id alone is a valid entry point — the rail
// then handles industry switching. generateStaticParams enumerates the distinct
// members from the backend index at build time.
export async function generateStaticParams() {
  const index = await fetchLandscapeIndex();
  return [...new Set(index.map((e) => e.member_id))].map((member) => ({ member }));
}

export default function MemberRootPage() {
  return <MemberRedirect />;
}
