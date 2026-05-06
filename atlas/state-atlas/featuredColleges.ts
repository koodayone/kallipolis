// Featured colleges loaded into prod Neo4j with full pipeline output:
// catalog-extracted courses, TOP4-derived program names, synthetic
// students, PREPARES_FOR edges to the regional employer/occupation
// pool. The set is read by `generateStaticParams` for the /[collegeId]
// routes — only colleges listed here get pre-built HTML in the static
// export, so adding a college here without first loading its graph
// data produces broken pages in production.
//
// Extracted from CaliforniaMap.tsx so server components can import it
// without pulling in the client-only map component.
export const FEATURED_COLLEGES = new Set([
  // North / Far North
  "shasta", "siskiyous", "lassen", "mendocino", "butte", "laketahoe",
  // Bay Area
  "foothill", "berkeleycc", "napavalley", "hartnell",
  "csm", "losmedanos", "deanza",
  // Greater Sacramento
  "americanriver",
  // Central Valley / Mother Lode
  "saccc", "sequoias", "merced", "cerrocoso",
  "reedley",
  // South Central Coast
  "sbcc", "oxnard", "allanhancock",
  // Los Angeles
  "compton", "lavalley",
  "lacity", "mtsac",
  // Orange County
  "irvinevalley",
  // Inland Empire / Desert
  "desert",
  "chaffey",
  // San Diego / Imperial
  "sandiegocity", "imperial",
]);
