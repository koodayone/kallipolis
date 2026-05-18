"use client";

import { useEffect, useRef } from "react";
import { usePathname } from "next/navigation";
import { API_BASE } from "@/api";

/**
 * Fires a page-view beacon on every route change.
 * Captures path and referrer; the backend captures IP server-side.
 * Uses sendBeacon for reliability (fires even on tab close).
 */
export default function AnalyticsBeacon() {
  const pathname = usePathname();
  const lastPath = useRef("");

  useEffect(() => {
    if (pathname === lastPath.current) return;
    lastPath.current = pathname;

    const payload = JSON.stringify({
      path: pathname,
      referrer: document.referrer,
      site: "atlas",
    });

    if (navigator.sendBeacon) {
      navigator.sendBeacon(
        `${API_BASE}/analytics/beacon`,
        new Blob([payload], { type: "application/json" }),
      );
    } else {
      fetch(`${API_BASE}/analytics/beacon`, {
        method: "POST",
        body: payload,
        headers: { "Content-Type": "application/json" },
        keepalive: true,
      }).catch(() => {});
    }
  }, [pathname]);

  return null;
}
