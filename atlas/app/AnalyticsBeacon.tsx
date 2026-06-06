"use client";

import { useEffect } from "react";
import { usePathname } from "next/navigation";
import { trackView } from "@/analytics";

/**
 * Fires a page-view beacon on every route change.
 * Captures path + query params; the backend captures IP server-side.
 * Dedupe, Do-Not-Track suppression, and sendBeacon delivery live in trackView
 * (shared with the SVAMP report's in-page view tracking).
 */
export default function AnalyticsBeacon() {
  const pathname = usePathname();

  useEffect(() => {
    const search = window.location.search;
    trackView(search ? `${pathname}${search}` : pathname);
  }, [pathname]);

  return null;
}
