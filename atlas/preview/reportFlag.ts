// Lightweight feedback capture for preview-mode Flag actions. POSTs a
// structured record to NEXT_PUBLIC_FLAG_ENDPOINT (Formspree in production)
// so prospect reactions become an attributable signal for pilot
// conversations. Returns success/failure silently; the UI should treat
// a best-effort send as sufficient.

type FlagPayload = {
  collegeId: string;
  artifactKind: "partnership" | "swp";
  artifactId: string;
  reason?: string;
  snapshot: unknown;
};

export async function reportFlag(payload: FlagPayload): Promise<boolean> {
  const endpoint = process.env.NEXT_PUBLIC_FLAG_ENDPOINT;
  if (!endpoint) return false;

  try {
    const res = await fetch(endpoint, {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "application/json" },
      body: JSON.stringify({
        ...payload,
        userAgent: typeof navigator !== "undefined" ? navigator.userAgent : null,
        timestamp: new Date().toISOString(),
      }),
    });
    return res.ok;
  } catch {
    return false;
  }
}
