import DraftGate from "@/college-atlas/partnerships/DraftGate";

// Draft gate for the /smccd-ecu subtree (dashboard + report) — viewability + the
// neutral redirect target live in the shared DraftGate (see it for the rule).
export default function SmccdEcuLayout({ children }: { children: React.ReactNode }) {
  return <DraftGate id="smccd-ecu">{children}</DraftGate>;
}
