import SvampDashboard from "@/college-atlas/partnerships/SvampDashboard";
import { LayoutLabProvider } from "@/college-atlas/partnerships/LayoutLab";

// Layout lab — the real dashboard with its band gaps as drag handles and a
// pinned readout of the live weight/height manifest, for discovering the
// ideal default proportions. Sibling of /svamp/concepts; delete together
// once the defaults settle.
export default function SvampLayoutLabPage() {
  return (
    <LayoutLabProvider>
      <SvampDashboard />
    </LayoutLabProvider>
  );
}
