"use client";

import { useEffect, useRef } from "react";
import { usePathname } from "next/navigation";

const BEACON_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "https://api.kallipolis.us";

/**
 * Fires a page-view beacon on every route change.
 * Captures path and referrer; the backend captures IP server-side.
 * Uses sendBeacon for reliability (fires even on tab close).
 */
export default function AnalyticsBeacon({ site }: { site: "app" | "atlas" }) {
  const pathname = usePathname();
  const lastPath = useRef("");

  useEffect(() => {
    if (pathname === lastPath.current) return;
    lastPath.current = pathname;

    const payload = JSON.stringify({
      path: pathname,
      referrer: document.referrer,
      site,
    });

    if (navigator.sendBeacon) {
      navigator.sendBeacon(
        `${BEACON_URL}/analytics/beacon`,
        new Blob([payload], { type: "application/json" }),
      );
    } else {
      fetch(`${BEACON_URL}/analytics/beacon`, {
        method: "POST",
        body: payload,
        headers: { "Content-Type": "application/json" },
        keepalive: true,
      }).catch(() => {});
    }
  }, [pathname, site]);

  return null;
}
