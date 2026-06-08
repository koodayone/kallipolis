"use client";

import { useEffect, useState } from "react";
import { isLandscapeViewable } from "@/college-atlas/partnerships/landscapeInstances";

// Draft-instance gate for the whole /smccd subtree (dashboard + report). SMCCD
// is unpublished — its DataMart data isn't in prod yet — so in a production
// build (the static export that ships to prod) this renders nothing and
// bounces to the published consortium, while local `next dev` shows it for
// iteration. One gate here covers every /smccd/* route. Mirrors the backend's
// routable_specs gate; flip landscapeInstances `published` to retire both.
export default function SmccdLayout({ children }: { children: React.ReactNode }) {
  const viewable = isLandscapeViewable("smccd");
  // Gate on a mounted flag so SSR/prerender output is inert (null) and the
  // client owns the redirect — the static export has no server redirects.
  const [mounted, setMounted] = useState(false);
  useEffect(() => {
    if (!viewable) window.location.replace("/svamp");
    else setMounted(true);
  }, [viewable]);
  return viewable && mounted ? <>{children}</> : null;
}
