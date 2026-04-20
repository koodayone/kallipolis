// Central helper for preview-mode detection.
//
// Convention: `NEXT_PUBLIC_AUTH_ENABLED` defaults to auth-on. Only an explicit
// "false" opts into preview mode. This keeps local dev working without
// additional env setup; preview is enabled by the Cloudflare Pages env.
export const PREVIEW_MODE =
  process.env.NEXT_PUBLIC_AUTH_ENABLED === "false";
