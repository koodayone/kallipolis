"use client";

import { useEffect, useRef } from "react";
import { usePathname, useSearchParams } from "next/navigation";

const BEACON_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "https://api.kallipolis.us";

/**
 * Fires a page-view beacon on every route change.
 * Captures path, query params, and referrer; the backend captures IP server-side.
 * Uses sendBeacon for reliability (fires even on tab close).
 */
export default function AnalyticsBeacon({ site }: { site: "app" | "atlas" }) {
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const lastUrl = useRef("");

  useEffect(() => {
    const search = searchParams.toString();
    const fullPath = search ? `${pathname}?${search}` : pathname;
    if (fullPath === lastUrl.current) return;
    lastUrl.current = fullPath;

    const payload = JSON.stringify({
      path: fullPath,
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
  }, [pathname, searchParams, site]);

  return null;
}
