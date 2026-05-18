"use client";

import { Suspense, useEffect, useRef } from "react";
import { usePathname, useSearchParams } from "next/navigation";
import { API_BASE } from "@/api";

function BeaconInner() {
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
  }, [pathname, searchParams]);

  return null;
}

/**
 * Fires a page-view beacon on every route change.
 * Captures path, query params, and referrer; the backend captures IP server-side.
 * Uses sendBeacon for reliability (fires even on tab close).
 *
 * Wrapped in Suspense because useSearchParams requires it during
 * static prerendering (Next.js App Router).
 */
export default function AnalyticsBeacon() {
  return (
    <Suspense fallback={null}>
      <BeaconInner />
    </Suspense>
  );
}
