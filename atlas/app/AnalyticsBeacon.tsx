"use client";

import { useEffect, useRef } from "react";
import { usePathname } from "next/navigation";
import { API_BASE } from "@/api";

/**
 * Fires a page-view beacon on every route change.
 * Captures path, query params, and referrer; the backend captures IP server-side.
 * Uses sendBeacon for reliability (fires even on tab close).
 */
export default function AnalyticsBeacon() {
  const pathname = usePathname();
  const lastUrl = useRef("");

  useEffect(() => {
    const search = window.location.search;
    const fullPath = search ? `${pathname}${search}` : pathname;
    if (fullPath === lastUrl.current) return;
    lastUrl.current = fullPath;

    const payload = JSON.stringify({
      path: fullPath,
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
