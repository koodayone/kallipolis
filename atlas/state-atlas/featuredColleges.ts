// Featured colleges loaded into Neo4j with full pipeline output:
// CourseDetails-sourced courses (Data Mart, Fall 2025), TOP4-derived
// program names, synthetic students, PREPARES_FOR / PARTNERSHIP_ALIGNMENT
// / OCCUPATION_PIPELINE / HAS_COMPETENCY edges to the regional
// employer/occupation pool. The set is read by `generateStaticParams`
// for the /[collegeId] routes — only colleges listed here get pre-built
// HTML in the static export, so adding a college here without first
// loading its graph data produces broken pages in production.
//
// Membership criterion: the College node exists in Neo4j with an
// IN_MARKET edge to a Region (114 colleges as of the statewide load).
//
// All 114 are featured. The 5 entries without logoStacked in
// `state-atlas/californiaColleges.ts` (glendale, lapierce, lasouthwest,
// latrade, santiagocyn) still render as colored diamonds via override-
// only configs in `config/collegeAtlasConfigs.ts` — their /logos/<id>.png
// paths 404 harmlessly, but the State Atlas marker is a diamond colored
// by the override, not the logo image.
//
// Two CCC colleges aren't loaded in the graph: Calbright (online-only,
// not in PCF/MCF), and SF Centers (sub-entity of CCSF, not a separate
// college). Redwoods IS loaded under the PCF∩MCF spine — the earlier
// CourseDetails-only spine had to skip it because Redwoods had no
// Fall 2025 sections in Data Mart's term-pinned export, but PCF and
// MCF aren't term-pinned.
//
// Extracted from CaliforniaMap.tsx so server components can import it
// without pulling in the client-only map component.
export const FEATURED_COLLEGES = new Set([
  // North / Far North
  "shasta", "siskiyous", "lassen", "mendocino", "butte", "laketahoe",
  "featherriver", "sierra", "saccc", "americanriver", "cosumnes",
  "folsom", "yuba", "woodland", "columbia", "redwoods",
  // Bay Area
  "foothill", "deanza", "ccsf", "laney", "merritt", "berkeleycc",
  "alameda", "skyline", "canada", "csm", "losmedanos", "diablo",
  "contracosta", "evergreen", "sanjosecity", "marin", "santarosa",
  "napavalley", "solano", "westvalley", "mission", "ohlone", "chabot",
  "laspositas", "cabrillo", "gavilan",
  // Central Valley / Mother Lode
  "sequoias", "merced", "cerrocoso", "reedley", "fresno", "clovis",
  "madera", "modesto", "porterville", "sanjoquin", "taft", "westhill",
  "westhillslemo", "bakersfield",
  // South Central Coast
  // (Ventura College is `cabrillovc` historically — atlas id quirk)
  "sbcc", "oxnard", "allanhancock", "cabrillovc", "moorpark", "hartnell",
  "montereypen", "cuesta",
  // Los Angeles (5 logo-less colleges included — render as diamonds via override colors)
  "compton", "lavalley", "lacity", "mtsac", "elcamino", "lawest",
  "lamission", "laharbor", "longbeach", "santamonica", "pcc",
  "antelopevalley", "canyons", "cerritos", "citrus", "riohondo",
  "lapuente", "glendale", "lapierce", "lasouthwest", "latrade",
  // Orange County (santiagocyn is logo-less, override-only)
  "irvinevalley", "saddleback", "santaana", "orangecoast", "fullerton",
  "cypress", "coastline", "goldenwest", "santiagocyn",
  // Inland Empire / Desert
  "desert", "chaffey", "crafton", "sbvalley", "riverside", "norco",
  "morenovalley", "msjc", "victor", "barstow", "coppermtn", "paloverde",
  // San Diego / Imperial
  "sandiegocity", "sandiegomesa", "sandiegomira", "miracostacc",
  "palomar", "grossmont", "cuyamaca", "southwestern", "imperial",
]);
