"use client";

import { useEffect } from "react";

// Legacy alias — the dashboard moved to the root (/svamp, decided 2026-06-07
// once the responsive re-architecture removed its viewport gate). Shared
// /svamp/dashboard links redirect there with the selection params intact, so
// the analytics record stays one URL per view. Client-side replace because
// the static export has no server redirects.
export default function SvampDashboardLegacyRedirect() {
  useEffect(() => {
    window.location.replace(`/svamp${window.location.search}`);
  }, []);
  return null;
}
