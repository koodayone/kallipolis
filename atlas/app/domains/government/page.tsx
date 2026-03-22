import GovernmentView from "@/components/domains/GovernmentView";
import { schoolConfig } from "@/lib/schoolConfig";

export default function GovernmentPage() {
  return <GovernmentView school={schoolConfig} />;
}
