import { DomainKey } from "@/lib/atlasScene";
import { schoolConfig } from "@/lib/schoolConfig";
import DomainHeader from "./DomainHeader";
import GovernmentView from "./GovernmentView";
import CollegeView from "./CollegeView";
import IndustryView from "./IndustryView";

type Props = {
  domain: DomainKey;
  onBack: () => void;
};

export default function DomainView({ domain, onBack }: Props) {
  return (
    <div style={{ minHeight: "100vh" }}>
      <DomainHeader domain={domain} onBack={onBack} school={schoolConfig} />
      <main>
        {domain === "government" && <GovernmentView school={schoolConfig} />}
        {domain === "college" && <CollegeView school={schoolConfig} />}
        {domain === "industry" && <IndustryView />}
      </main>
    </div>
  );
}
