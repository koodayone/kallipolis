import CollegeView from "@/components/domains/CollegeView";
import { schoolConfig } from "@/lib/schoolConfig";

export default function CollegePage() {
  return <CollegeView school={schoolConfig} />;
}
