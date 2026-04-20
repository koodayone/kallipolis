import { FEATURED_COLLEGES } from "@/state-atlas/featuredColleges";
import ClientPage from "./ClientPage";

export async function generateStaticParams() {
  return Array.from(FEATURED_COLLEGES).map((collegeId) => ({ collegeId }));
}

export default function Page() {
  return <ClientPage />;
}
