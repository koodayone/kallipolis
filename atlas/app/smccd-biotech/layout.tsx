import DraftGate from "@/college-atlas/partnerships/DraftGate";

// Draft gate for the /smccd-biotech subtree (dashboard + report) — viewability + the
// neutral redirect target live in the shared DraftGate (see it for the rule).
export default function SmccdBiotechLayout({ children }: { children: React.ReactNode }) {
  return <DraftGate id="smccd-biotech">{children}</DraftGate>;
}
