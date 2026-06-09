import DraftGate from "@/college-atlas/partnerships/DraftGate";

// Draft gate for the /smccd-health subtree (dashboard + report) — viewability + the
// neutral redirect target live in the shared DraftGate (see it for the rule).
export default function SmccdHealthLayout({ children }: { children: React.ReactNode }) {
  return <DraftGate id="smccd-health">{children}</DraftGate>;
}
