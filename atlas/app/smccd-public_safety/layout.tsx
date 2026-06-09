import DraftGate from "@/college-atlas/partnerships/DraftGate";

// Draft gate for the /smccd-public_safety subtree (dashboard + report) — viewability + the
// neutral redirect target live in the shared DraftGate (see it for the rule).
export default function SmccdPublicSafetyLayout({ children }: { children: React.ReactNode }) {
  return <DraftGate id="smccd-public_safety">{children}</DraftGate>;
}
