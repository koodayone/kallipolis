"use client";

import { useEffect, useState } from "react";
import { isLandscapeViewable } from "@/college-atlas/partnerships/landscapeInstances";

// Shared client-side gate for a landscape route subtree (dashboard + report).
// A NON-viewable instance — a draft gated out of a production build, or an
// unknown id — redirects to the site root (the State Atlas, the neutral home),
// NOT to any specific landscape. Previously each layout bounced to /svamp, which
// silently shuttled an unrelated consortium's URL onto SVAMP; the root is the
// correct neutral destination. Mirrors the backend routable_specs gate, and
// centralizes the gate logic + fallback target so they live in one place rather
// than being copy-pasted across every landscape layout.
export default function DraftGate({
  id,
  children,
}: {
  id: string;
  children: React.ReactNode;
}) {
  const viewable = isLandscapeViewable(id);
  // Gate on a mounted flag so SSR/prerender output is inert (null) and the
  // client owns the redirect — the static export has no server redirects.
  const [mounted, setMounted] = useState(false);
  useEffect(() => {
    if (!viewable) window.location.replace("/");
    else setMounted(true);
  }, [viewable]);
  return viewable && mounted ? <>{children}</> : null;
}
