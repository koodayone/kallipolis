import { API_BASE } from "@/api";

/**
 * Shared anonymous analytics sender. One path through which both the route-level
 * page-view beacon and in-page view tracking (e.g. the SVAMP report's lens /
 * selection changes, encoded in the URL) report — so the analytics record is
 * always just the URL of the view.
 *
 * Honors Do Not Track, dedupes consecutive identical paths, and uses sendBeacon
 * (which survives tab close) with a keepalive-fetch fallback.
 */

function doNotTrack(): boolean {
  if (typeof navigator === "undefined") return false;
  // Legacy signals across browsers; "1"/"yes" mean enabled.
  const v =
    navigator.doNotTrack ??
    (typeof window !== "undefined" ? (window as unknown as { doNotTrack?: string }).doNotTrack : undefined) ??
    (navigator as unknown as { msDoNotTrack?: string }).msDoNotTrack;
  return v === "1" || v === "yes";
}

let lastPath = "";

/** Fire a page/view beacon for `path` (a path+query string). No-op under Do Not
 * Track, on the server, or when `path` repeats the last reported path. */
export function trackView(path: string): void {
  if (typeof window === "undefined") return;
  if (doNotTrack()) return;
  if (path === lastPath) return;
  lastPath = path;

  const payload = JSON.stringify({
    path,
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
}
