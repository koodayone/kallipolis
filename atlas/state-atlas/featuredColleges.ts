// MVP scope: one anchor college per CCC regional consortium. The State Atlas
// surfaces the eight consortia as first-class units; each consortium is
// represented on the map by a single college whose College Atlas is
// production-ready. The set will expand (and eventually dissolve into the
// full college list) as additional institutions reach that bar.
//
// Extracted from CaliforniaMap.tsx so server components (notably
// generateStaticParams for /[collegeId] routes) can import it without
// pulling in the client-only map component.
export const FEATURED_COLLEGES = new Set([
  "shasta",        // North / Far North
  "foothill",      // Bay Area
  "sequoias",      // Central Valley / Mother Lode
  "oxnard",        // South Central Coast
  "compton",       // Los Angeles
  "irvinevalley",  // Orange County
  "desert",        // Inland Empire / Desert
  "sandiegocity",  // San Diego / Imperial
]);
