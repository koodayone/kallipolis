import { DomainKey } from "@/lib/atlasScene";
import { SchoolConfig } from "@/lib/schoolConfig";
import DomainHeader from "./DomainHeader";
import GovernmentView from "./GovernmentView";
import CollegeView from "./CollegeView";
import IndustryView from "./IndustryView";

type Props = {
  domain: DomainKey;
  onBack: () => void;
  school: SchoolConfig;
};

export default function DomainView({ domain, onBack, school }: Props) {
  return (
    <div style={{ minHeight: "100vh" }}>
      <DomainHeader domain={domain} onBack={onBack} school={school} />
      <main>
        {domain === "government" && <GovernmentView school={school} />}
        {domain === "college" && <CollegeView school={school} />}
        {domain === "industry" && <IndustryView school={school} />}
      </main>
    </div>
  );
}
