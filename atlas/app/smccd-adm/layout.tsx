import DraftGate from "@/college-atlas/partnerships/DraftGate";

// Draft gate for the /smccd-adm subtree (dashboard + report) — viewability + the
// neutral redirect target live in the shared DraftGate (see it for the rule).
export default function SmccdAdmLayout({ children }: { children: React.ReactNode }) {
  return <DraftGate id="smccd-adm">{children}</DraftGate>;
}
