import { DomainKey } from "@/lib/atlasScene";
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
      <DomainHeader domain={domain} onBack={onBack} />
      <main>
        {domain === "government" && <GovernmentView />}
        {domain === "college" && <CollegeView />}
        {domain === "industry" && <IndustryView />}
      </main>
    </div>
  );
}
