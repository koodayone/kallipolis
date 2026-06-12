import MemberRedirect from "./MemberRedirect";
import { memberRouteParams } from "@/college-atlas/partnerships/landscapeIndex";

// Member-root route: /landscape/<member> bounces to the member's flagship sector
// (see MemberRedirect), so a member id alone is a valid entry point — the rail
// then handles industry switching. generateStaticParams enumerates the distinct
// members from the backend index at build time.
export async function generateStaticParams() {
  return memberRouteParams();
}

export default function MemberRootPage() {
  return <MemberRedirect />;
}
