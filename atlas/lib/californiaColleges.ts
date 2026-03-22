export type College = {
  id: string;
  name: string;
  district: string;
  regionId: string;
  lat: number;
  lng: number;
  logoStacked?: string;   // e.g. "/foothill-logo.png"
  logoLongform?: string;  // e.g. "/foothill-logo-long.png"
};

export type Region = {
  id: string;
  name: string;
  labelCenter: [number, number]; // [lng, lat] — label position on state map
  zoomCenter: [number, number];  // [lng, lat] — projection center when zoomed into region
  scale: number;                 // projectionConfig.scale for this region
  counties: string[];            // must match GeoJSON properties.name exactly
  collegeCount: number;          // total in real dataset
};

export const CALIFORNIA_REGIONS: Region[] = [
  {
    id: "far-north",
    name: "Far North",
    labelCenter: [-122.0, 40.9],
    zoomCenter: [-121.5, 40.5],
    scale: 7000,
    counties: ["Del Norte", "Siskiyou", "Modoc", "Trinity", "Humboldt", "Shasta", "Lassen", "Tehama"],
    collegeCount: 6,
  },
  {
    id: "greater-sacramento",
    name: "Greater Sacramento",
    labelCenter: [-121.0, 39.2],
    zoomCenter: [-121.0, 39.2],
    scale: 8000,
    counties: ["Butte", "Glenn", "Colusa", "Plumas", "Sierra", "Nevada", "Placer", "El Dorado", "Yolo", "Sacramento", "Alpine", "Sutter", "Yuba"],
    collegeCount: 10,
  },
  {
    id: "bay-area",
    name: "Bay Area",
    labelCenter: [-122.1, 37.7],
    zoomCenter: [-122.1, 37.7],
    scale: 11000,
    counties: ["Marin", "Sonoma", "Napa", "Lake", "Mendocino", "Solano", "Contra Costa", "Alameda", "San Francisco", "San Mateo", "Santa Clara", "Santa Cruz"],
    collegeCount: 27,
  },
  {
    id: "central-valley",
    name: "Central Valley",
    labelCenter: [-119.4, 37.3],
    zoomCenter: [-119.4, 37.3],
    scale: 7000,
    counties: ["San Joaquin", "Calaveras", "Tuolumne", "Amador", "Mono", "Stanislaus", "Merced", "Mariposa", "Fresno", "Madera", "Kings", "Tulare", "Kern", "Inyo"],
    collegeCount: 15,
  },
  {
    id: "central-coast",
    name: "Central Coast",
    labelCenter: [-120.8, 35.6],
    zoomCenter: [-120.8, 35.6],
    scale: 9000,
    counties: ["Monterey", "San Benito", "San Luis Obispo", "Santa Barbara", "Ventura"],
    collegeCount: 8,
  },
  {
    id: "inland-empire",
    name: "Inland Empire",
    labelCenter: [-116.2, 34.7],
    zoomCenter: [-116.2, 34.7],
    scale: 9000,
    counties: ["San Bernardino", "Riverside"],
    collegeCount: 12,
  },
  {
    id: "los-angeles",
    name: "Los Angeles",
    labelCenter: [-118.5, 34.3],
    zoomCenter: [-118.5, 34.3],
    scale: 13000,
    counties: ["Los Angeles"],
    collegeCount: 21,
  },
  {
    id: "orange-county",
    name: "Orange County",
    labelCenter: [-117.75, 33.55],
    zoomCenter: [-117.75, 33.55],
    scale: 16000,
    counties: ["Orange"],
    collegeCount: 9,
  },
  {
    id: "san-diego",
    name: "San Diego / Imperial",
    labelCenter: [-116.0, 33.0],
    zoomCenter: [-116.0, 33.0],
    scale: 9000,
    counties: ["San Diego", "Imperial"],
    collegeCount: 10,
  },
];

// Fast county → region lookup
export const COUNTY_TO_REGION: Record<string, Region> = {};
for (const region of CALIFORNIA_REGIONS) {
  for (const county of region.counties) {
    COUNTY_TO_REGION[county] = region;
  }
}

// ~80 colleges across all 9 regions with accurate lat/lng
export const CALIFORNIA_COLLEGES: College[] = [
  // Far North
  { id: "redwoods",       name: "College of the Redwoods",         district: "Redwoods CCD",                  regionId: "far-north",         lat: 40.80, lng: -124.16, logoStacked: "/redwoods-logo.svg",       logoLongform: "/redwoods-logo.svg" },
  { id: "shasta",         name: "Shasta College",                  district: "Shasta-Tehama-Trinity JCCD",    regionId: "far-north",         lat: 40.61, lng: -122.37, logoStacked: "/shasta-logo.svg",         logoLongform: "/shasta-logo.svg" },
  { id: "lassen",         name: "Lassen College",                  district: "Lassen CCD",                    regionId: "far-north",         lat: 40.44, lng: -120.65, logoStacked: "/lassen-logo.jpg",          logoLongform: "/lassen-logo.jpg" },
  { id: "siskiyous",      name: "College of the Siskiyous",        district: "Siskiyous JCCD",                regionId: "far-north",         lat: 41.48, lng: -122.29, logoStacked: "/siskiyous-logo.png",       logoLongform: "/siskiyous-logo.png" },
  { id: "delnorte",       name: "College of the Redwoods (DN)",    district: "Redwoods CCD",                  regionId: "far-north",         lat: 41.74, lng: -124.20, logoStacked: "/redwoods-logo.svg",        logoLongform: "/redwoods-logo.svg" },
  { id: "featherriver",   name: "Feather River College",           district: "Feather River CCD",             regionId: "far-north",         lat: 39.93, lng: -120.95, logoStacked: "/featherriver-logo.svg",    logoLongform: "/featherriver-logo.svg" },

  // Greater Sacramento
  { id: "butte",          name: "Butte College",                   district: "Butte-Glenn CCD",               regionId: "greater-sacramento", lat: 39.52, lng: -121.65, logoStacked: "/butte-logo.svg",           logoLongform: "/butte-logo.svg" },
  { id: "sierra",         name: "Sierra College",                  district: "Sierra JCCD",                   regionId: "greater-sacramento", lat: 38.79, lng: -121.20, logoStacked: "/sierra-logo.png",          logoLongform: "/sierra-logo.png" },
  { id: "saccc",          name: "Sacramento City College",         district: "Los Rios CCD",                  regionId: "greater-sacramento", lat: 38.56, lng: -121.49, logoStacked: "/saccc-logo.svg",           logoLongform: "/saccc-logo.svg" },
  { id: "arc",            name: "American River College",          district: "Los Rios CCD",                  regionId: "greater-sacramento", lat: 38.67, lng: -121.37, logoStacked: "/arc-logo.svg",             logoLongform: "/arc-logo.svg" },
  { id: "cosumnes",       name: "Cosumnes River College",          district: "Los Rios CCD",                  regionId: "greater-sacramento", lat: 38.44, lng: -121.42, logoStacked: "/cosumnes-logo.svg",        logoLongform: "/cosumnes-logo.svg" },
  { id: "folsom",         name: "Folsom Lake College",             district: "Los Rios CCD",                  regionId: "greater-sacramento", lat: 38.67, lng: -121.17, logoStacked: "/folsom-logo.svg",          logoLongform: "/folsom-logo.svg" },
  { id: "nevada",         name: "Nevada Union / Gold Hill",        district: "Nevada-Sierra CCD",             regionId: "greater-sacramento", lat: 39.29, lng: -121.06 },
  { id: "yuba",           name: "Yuba College",                    district: "Yuba CCD",                      regionId: "greater-sacramento", lat: 39.14, lng: -121.62, logoStacked: "/yuba-logo.png",            logoLongform: "/yuba-logo.png" },
  { id: "woodland",       name: "Woodland Community College",      district: "Yuba CCD",                      regionId: "greater-sacramento", lat: 38.66, lng: -121.73, logoStacked: "/woodland-logo.svg",        logoLongform: "/woodland-logo.svg" },
  { id: "laketahoe",      name: "Lake Tahoe Community College",    district: "Lake Tahoe CCD",                regionId: "greater-sacramento", lat: 38.93, lng: -119.97, logoStacked: "/laketahoe-logo.png",      logoLongform: "/laketahoe-logo.png" },

  // Bay Area
  { id: "ccsf",        name: "City College of San Francisco", district: "San Francisco CCD",          regionId: "bay-area", lat: 37.72, lng: -122.45, logoStacked: "/ccsf-logo.png",        logoLongform: "/ccsf-logo-long.png" },
  { id: "foothill",    name: "Foothill College",              district: "Foothill-De Anza CCD",       regionId: "bay-area", lat: 37.36, lng: -122.05, logoStacked: "/foothill-logo.png",     logoLongform: "/foothill-logo-long.png" },
  { id: "deanza",      name: "De Anza College",               district: "Foothill-De Anza CCD",       regionId: "bay-area", lat: 37.31, lng: -122.04, logoStacked: "/deanza-logo.svg",       logoLongform: "/deanza-logo.svg" },
  { id: "skyline",     name: "Skyline College",               district: "San Mateo CCD",              regionId: "bay-area", lat: 37.62, lng: -122.46, logoStacked: "/skyline-logo.png",      logoLongform: "/skyline-logo-long.png" },
  { id: "canada",      name: "Cañada College",                district: "San Mateo CCD",              regionId: "bay-area", lat: 37.49, lng: -122.23, logoStacked: "/canada-logo.png",       logoLongform: "/canada-logo.png" },
  { id: "cmc",         name: "College of San Mateo",          district: "San Mateo CCD",              regionId: "bay-area", lat: 37.54, lng: -122.32, logoStacked: "/cmc-logo.jpg",          logoLongform: "/cmc-logo-long.jpg" },
  { id: "laney",       name: "Laney College",                 district: "Peralta CCD",                regionId: "bay-area", lat: 37.80, lng: -122.27, logoStacked: "/laney-logo.svg",        logoLongform: "/laney-logo-long.svg" },
  { id: "merritt",     name: "Merritt College",               district: "Peralta CCD",                regionId: "bay-area", lat: 37.83, lng: -122.22, logoStacked: "/merritt-logo.png",      logoLongform: "/merritt-logo.png" },
  { id: "berkeleycc",  name: "Berkeley City College",         district: "Peralta CCD",                regionId: "bay-area", lat: 37.87, lng: -122.27, logoStacked: "/berkeleycc-logo.png",   logoLongform: "/berkeleycc-logo.png" },
  { id: "alameda",     name: "College of Alameda",            district: "Peralta CCD",                regionId: "bay-area", lat: 37.77, lng: -122.23, logoStacked: "/alameda-logo.png",      logoLongform: "/alameda-logo.png" },
  { id: "diablo",      name: "Diablo Valley College",         district: "Contra Costa CCD",           regionId: "bay-area", lat: 37.96, lng: -122.07, logoStacked: "/diablo-logo.svg",       logoLongform: "/diablo-logo.svg" },
  { id: "contracosta", name: "Contra Costa College",          district: "Contra Costa CCD",           regionId: "bay-area", lat: 37.97, lng: -122.34, logoStacked: "/contracosta-logo.png",  logoLongform: "/contracosta-logo.png" },
  { id: "losmedanos",  name: "Los Medanos College",           district: "Contra Costa CCD",           regionId: "bay-area", lat: 37.97, lng: -121.78, logoStacked: "/losmedanos-logo.svg",   logoLongform: "/losmedanos-logo.svg" },
  { id: "cabrillo",    name: "Cabrillo College",              district: "Cabrillo CCD",               regionId: "bay-area", lat: 36.98, lng: -121.96, logoStacked: "/cabrillo-logo.png",     logoLongform: "/cabrillo-logo.png" },
  { id: "gavilan",     name: "Gavilan College",               district: "Gavilan JCCD",               regionId: "bay-area", lat: 36.97, lng: -121.54, logoStacked: "/gavilan-logo.png",      logoLongform: "/gavilan-logo.png" },
  { id: "evergreen",   name: "Evergreen Valley College",      district: "San Jose-Evergreen CCD",     regionId: "bay-area", lat: 37.34, lng: -121.80, logoStacked: "/evergreen-logo.png",    logoLongform: "/evergreen-logo-long.png" },
  { id: "sanjosecity", name: "San Jose City College",         district: "San Jose-Evergreen CCD",     regionId: "bay-area", lat: 37.31, lng: -121.90, logoStacked: "/sanjosecity-logo.svg",  logoLongform: "/sanjosecity-logo.svg" },
  { id: "marin",      name: "College of Marin",              district: "Marin CCD",                  regionId: "bay-area", lat: 37.96, lng: -122.55, logoStacked: "/marin-logo.svg",         logoLongform: "/marin-logo.svg" },
  { id: "santarosa",  name: "Santa Rosa Junior College",     district: "Sonoma County JCCD",          regionId: "bay-area", lat: 38.46, lng: -122.72, logoStacked: "/santarosa-logo.png",    logoLongform: "/santarosa-logo.png" },
  { id: "napavalley", name: "Napa Valley College",           district: "Napa Valley CCD",             regionId: "bay-area", lat: 38.27, lng: -122.27, logoStacked: "/napavalley-logo.svg",   logoLongform: "/napavalley-logo.svg" },
  { id: "mendocino",  name: "Mendocino College",             district: "Mendocino-Lake CCD",          regionId: "bay-area", lat: 39.19, lng: -123.23, logoStacked: "/mendocino-logo.png",    logoLongform: "/mendocino-logo.png" },
  { id: "solano",     name: "Solano Community College",      district: "Solano CCD",                  regionId: "bay-area", lat: 38.24, lng: -122.12, logoStacked: "/solano-logo.svg",       logoLongform: "/solano-logo.svg" },
  { id: "mission",    name: "Mission College",               district: "West Valley-Mission CCD",     regionId: "bay-area", lat: 37.39, lng: -121.98, logoStacked: "/mission-logo.png",      logoLongform: "/mission-logo.png" },
  { id: "westvalley", name: "West Valley College",           district: "West Valley-Mission CCD",     regionId: "bay-area", lat: 37.26, lng: -122.01, logoStacked: "/westvalley-logo.svg",   logoLongform: "/westvalley-logo.svg" },
  { id: "ohlone",     name: "Ohlone College",                district: "Ohlone CCD",                  regionId: "bay-area", lat: 37.53, lng: -121.91, logoStacked: "/ohlone-logo.png",       logoLongform: "/ohlone-logo.png" },
  { id: "chabot",     name: "Chabot College",                district: "Chabot-Las Positas CCD",      regionId: "bay-area", lat: 37.64, lng: -122.11, logoStacked: "/chabot-logo.png",       logoLongform: "/chabot-logo.png" },
  { id: "laspositas", name: "Las Positas College",           district: "Chabot-Las Positas CCD",      regionId: "bay-area", lat: 37.71, lng: -121.80, logoStacked: "/laspositas-logo.png",   logoLongform: "/laspositas-logo.png" },

  // Central Valley
  { id: "fresno",         name: "Fresno City College",             district: "State Center CCD",              regionId: "central-valley",     lat: 36.73, lng: -119.79, logoStacked: "/fresno-logo.png",          logoLongform: "/fresno-logo.png" },
  { id: "reedley",        name: "Reedley College",                 district: "State Center CCD",              regionId: "central-valley",     lat: 36.60, lng: -119.45, logoStacked: "/reedley-logo.png",         logoLongform: "/reedley-logo.png" },
  { id: "clovis",         name: "Clovis Community College",        district: "State Center CCD",              regionId: "central-valley",     lat: 36.83, lng: -119.68, logoStacked: "/clovis-logo.png",          logoLongform: "/clovis-logo.png" },
  { id: "visalia",        name: "College of the Sequoias",         district: "Sequoias CCD",                  regionId: "central-valley",     lat: 36.32, lng: -119.30, logoStacked: "/visalia-logo.png",         logoLongform: "/visalia-logo.png" },
  { id: "merced",         name: "Merced College",                  district: "Merced CCD",                    regionId: "central-valley",     lat: 37.35, lng: -120.49, logoStacked: "/merced-logo.png",          logoLongform: "/merced-logo.png" },
  { id: "modesto",        name: "Modesto Junior College",          district: "Yosemite CCD",                  regionId: "central-valley",     lat: 37.65, lng: -121.00, logoStacked: "/modesto-logo.svg",         logoLongform: "/modesto-logo.svg" },
  { id: "columbia",       name: "Columbia College",                district: "Yosemite CCD",                  regionId: "central-valley",     lat: 38.04, lng: -120.41, logoStacked: "/columbia-logo.png",        logoLongform: "/columbia-logo.png" },
  { id: "sanjoquin",      name: "San Joaquin Delta College",       district: "San Joaquin Delta CCD",         regionId: "central-valley",     lat: 37.96, lng: -121.29, logoStacked: "/sanjoquin-logo.jpg",       logoLongform: "/sanjoquin-logo.jpg" },
  { id: "westhill",       name: "West Hills College Coalinga",     district: "West Hills CCD",                regionId: "central-valley",     lat: 36.15, lng: -120.35, logoStacked: "/westhill-logo.svg",        logoLongform: "/westhill-logo.svg" },
  { id: "westhillslemo",  name: "West Hills College Lemoore",      district: "West Hills CCD",                regionId: "central-valley",     lat: 36.30, lng: -119.78, logoStacked: "/westhillslemo-logo.svg",   logoLongform: "/westhillslemo-logo.svg" },
  { id: "bakersfield",   name: "Bakersfield College",              district: "Kern CCD",                      regionId: "central-valley",     lat: 35.41, lng: -118.97, logoStacked: "/bakersfield-logo.png",    logoLongform: "/bakersfield-logo.png" },
  { id: "cerrocoso",     name: "Cerro Coso Community College",     district: "Kern CCD",                      regionId: "central-valley",     lat: 35.57, lng: -117.66, logoStacked: "/cerrocoso-logo.png",      logoLongform: "/cerrocoso-logo.png" },
  { id: "porterville",   name: "Porterville College",              district: "Kern CCD",                      regionId: "central-valley",     lat: 36.05, lng: -119.01, logoStacked: "/porterville-logo.png",    logoLongform: "/porterville-logo.png" },
  { id: "taft",          name: "Taft College",                     district: "West Kern CCD",                 regionId: "central-valley",     lat: 35.14, lng: -119.46, logoStacked: "/taft-logo.png",            logoLongform: "/taft-logo.png" },
  { id: "madera",        name: "Madera Community College",         district: "State Center CCD",              regionId: "central-valley",     lat: 36.96, lng: -120.06, logoStacked: "/madera-logo.png",          logoLongform: "/madera-logo.png" },

  // Central Coast
  { id: "cuesta",         name: "Cuesta College",                  district: "San Luis Obispo CCD",           regionId: "central-coast",      lat: 35.32, lng: -120.66, logoStacked: "/cuesta-logo.png",          logoLongform: "/cuesta-logo.png" },
  { id: "sbcc",           name: "Santa Barbara City College",      district: "Santa Barbara CCD",             regionId: "central-coast",      lat: 34.43, lng: -119.72, logoStacked: "/sbcc-logo.png",            logoLongform: "/sbcc-logo.png" },
  { id: "hancock",        name: "Allan Hancock College",           district: "Allan Hancock JCCD",            regionId: "central-coast",      lat: 34.90, lng: -120.43, logoStacked: "/hancock-logo.png",         logoLongform: "/hancock-logo.png" },
  { id: "hartnell",       name: "Hartnell College",                district: "Hartnell CCD",                  regionId: "central-coast",      lat: 36.67, lng: -121.63, logoStacked: "/hartnell-logo.svg",        logoLongform: "/hartnell-logo.svg" },
  { id: "montereypen",    name: "Monterey Peninsula College",      district: "Monterey Peninsula CCD",        regionId: "central-coast",      lat: 36.60, lng: -121.87, logoStacked: "/montereypen-logo.png",     logoLongform: "/montereypen-logo.png" },
  { id: "cabrillovc",     name: "Ventura College",                 district: "Ventura CCD",                   regionId: "central-coast",      lat: 34.28, lng: -119.22, logoStacked: "/cabrillovc-logo.png",      logoLongform: "/cabrillovc-logo.png" },
  { id: "oxnard",         name: "Oxnard College",                  district: "Ventura CCD",                   regionId: "central-coast",      lat: 34.22, lng: -119.18, logoStacked: "/oxnard-logo.png",          logoLongform: "/oxnard-logo.png" },
  { id: "moorpark",       name: "Moorpark College",                district: "Ventura CCD",                   regionId: "central-coast",      lat: 34.28, lng: -118.88, logoStacked: "/moorpark-logo.png",        logoLongform: "/moorpark-logo.png" },

  // Inland Empire
  { id: "desert",         name: "College of the Desert",           district: "Desert CCD",                    regionId: "inland-empire",      lat: 33.73, lng: -116.37, logoStacked: "/desert-logo.png",          logoLongform: "/desert-logo.png" },
  { id: "sbvalley",       name: "San Bernardino Valley College",   district: "San Bernardino CCD",            regionId: "inland-empire",      lat: 34.10, lng: -117.29, logoStacked: "/sbvalley-logo.png",        logoLongform: "/sbvalley-logo.png" },
  { id: "crafton",        name: "Crafton Hills College",           district: "San Bernardino CCD",            regionId: "inland-empire",      lat: 34.06, lng: -117.05, logoStacked: "/crafton-logo.png",         logoLongform: "/crafton-logo.png" },
  { id: "chaffey",        name: "Chaffey College",                 district: "Chaffey CCD",                   regionId: "inland-empire",      lat: 34.10, lng: -117.66, logoStacked: "/chaffey-logo.svg",         logoLongform: "/chaffey-logo.svg" },
  { id: "riverside",      name: "Riverside City College",          district: "Riverside CCD",                 regionId: "inland-empire",      lat: 33.98, lng: -117.37, logoStacked: "/riverside-logo.svg",       logoLongform: "/riverside-logo.svg" },
  { id: "norco",          name: "Norco College",                   district: "Riverside CCD",                 regionId: "inland-empire",      lat: 33.93, lng: -117.55, logoStacked: "/norco-logo.png",           logoLongform: "/norco-logo.png" },
  { id: "msjc",           name: "Mt. San Jacinto College",         district: "Mt. San Jacinto CCD",           regionId: "inland-empire",      lat: 33.75, lng: -117.22, logoStacked: "/msjc-logo.png",            logoLongform: "/msjc-logo.png" },
  { id: "victor",         name: "Victor Valley College",           district: "Victor Valley CCD",             regionId: "inland-empire",      lat: 34.50, lng: -117.29, logoStacked: "/victor-logo.svg",          logoLongform: "/victor-logo.svg" },
  { id: "barstow",        name: "Barstow Community College",       district: "Barstow CCD",                   regionId: "inland-empire",      lat: 34.90, lng: -117.02, logoStacked: "/barstow-logo.svg",         logoLongform: "/barstow-logo.svg" },
  { id: "morenovalley",  name: "Moreno Valley College",           district: "Riverside CCD",                 regionId: "inland-empire",      lat: 33.89, lng: -117.20, logoStacked: "/morenovalley-logo.svg",   logoLongform: "/morenovalley-logo.svg" },
  { id: "paloverde",     name: "Palo Verde College",              district: "Palo Verde CCD",                regionId: "inland-empire",      lat: 33.66, lng: -114.65, logoStacked: "/paloverde-logo.png",      logoLongform: "/paloverde-logo.png" },
  { id: "coppermtn",     name: "Copper Mountain College",         district: "Copper Mountain CCD",           regionId: "inland-empire",      lat: 34.14, lng: -116.22, logoStacked: "/coppermtn-logo.svg",      logoLongform: "/coppermtn-logo.svg" },

  // Los Angeles
  { id: "lacc",           name: "Los Angeles City College",        district: "Los Angeles CCD",               regionId: "los-angeles",        lat: 34.08, lng: -118.31, logoStacked: "/lacc-logo.png",            logoLongform: "/lacc-logo.png" },
  { id: "lavalley",       name: "Los Angeles Valley College",      district: "Los Angeles CCD",               regionId: "los-angeles",        lat: 34.18, lng: -118.40, logoStacked: "/lavalley-logo.png",        logoLongform: "/lavalley-logo.png" },
  { id: "laharbor",       name: "Los Angeles Harbor College",      district: "Los Angeles CCD",               regionId: "los-angeles",        lat: 33.79, lng: -118.29, logoStacked: "/laharbor-logo.gif",        logoLongform: "/laharbor-logo.gif" },
  { id: "lamission",      name: "Los Angeles Mission College",     district: "Los Angeles CCD",               regionId: "los-angeles",        lat: 34.26, lng: -118.42, logoStacked: "/lamission-logo.png",       logoLongform: "/lamission-logo.png" },
  { id: "lapuente",       name: "East Los Angeles College",        district: "Los Angeles CCD",               regionId: "los-angeles",        lat: 34.02, lng: -118.15, logoStacked: "/lapuente-logo.jpg",        logoLongform: "/lapuente-logo.jpg" },
  { id: "lasouthwest",    name: "Los Angeles Southwest College",   district: "Los Angeles CCD",               regionId: "los-angeles",        lat: 33.93, lng: -118.30 },
  { id: "latrade",        name: "Los Angeles Trade-Technical",     district: "Los Angeles CCD",               regionId: "los-angeles",        lat: 34.03, lng: -118.27 },
  { id: "lawest",         name: "West Los Angeles College",        district: "Los Angeles CCD",               regionId: "los-angeles",        lat: 33.99, lng: -118.43, logoStacked: "/lawest-logo.png",          logoLongform: "/lawest-logo.png" },
  { id: "pcc",            name: "Pasadena City College",           district: "Pasadena Area CCD",             regionId: "los-angeles",        lat: 34.15, lng: -118.10, logoStacked: "/pcc-logo.png",             logoLongform: "/pcc-logo.png" },
  { id: "mtsac",          name: "Mt. San Antonio College",         district: "Mt. San Antonio CCD",           regionId: "los-angeles",        lat: 34.02, lng: -117.85, logoStacked: "/mtsac-logo.png",           logoLongform: "/mtsac-logo.svg" },
  { id: "longbeach",      name: "Long Beach City College",         district: "Long Beach CCD",                regionId: "los-angeles",        lat: 33.81, lng: -118.18, logoStacked: "/longbeach-logo.svg",       logoLongform: "/longbeach-logo.svg" },
  { id: "elcamino",       name: "El Camino College",               district: "El Camino CCD",                 regionId: "los-angeles",        lat: 33.86, lng: -118.34, logoStacked: "/elcamino-logo.svg",        logoLongform: "/elcamino-logo.svg" },
  { id: "santamonica",   name: "Santa Monica College",            district: "Santa Monica CCD",              regionId: "los-angeles",        lat: 34.02, lng: -118.47, logoStacked: "/santamonica-logo.svg",    logoLongform: "/santamonica-logo.svg" },
  { id: "glendale",      name: "Glendale Community College",      district: "Glendale CCD",                  regionId: "los-angeles",        lat: 34.17, lng: -118.22 },
  { id: "citrus",        name: "Citrus College",                  district: "Citrus CCD",                    regionId: "los-angeles",        lat: 34.13, lng: -117.88, logoStacked: "/citrus-logo.svg",          logoLongform: "/citrus-logo.svg" },
  { id: "riohondo",      name: "Rio Hondo College",               district: "Rio Hondo CCD",                 regionId: "los-angeles",        lat: 34.02, lng: -118.04, logoStacked: "/riohondo-logo.png",        logoLongform: "/riohondo-logo.png" },
  { id: "cerritos",      name: "Cerritos College",                district: "Cerritos CCD",                  regionId: "los-angeles",        lat: 33.89, lng: -118.09, logoStacked: "/cerritos-logo.svg",        logoLongform: "/cerritos-logo.svg" },
  { id: "compton",       name: "Compton College",                 district: "Compton CCD",                   regionId: "los-angeles",        lat: 33.87, lng: -118.21, logoStacked: "/compton-logo.png",         logoLongform: "/compton-logo.png" },
  { id: "lapierce",      name: "Los Angeles Pierce College",      district: "Los Angeles CCD",               regionId: "los-angeles",        lat: 34.18, lng: -118.58 },
  { id: "antelopevalley", name: "Antelope Valley College",        district: "Antelope Valley CCD",           regionId: "los-angeles",        lat: 34.68, lng: -118.19, logoStacked: "/antelopevalley-logo.svg", logoLongform: "/antelopevalley-logo.svg" },
  { id: "canyons",       name: "College of the Canyons",          district: "Santa Clarita CCD",             regionId: "los-angeles",        lat: 34.40, lng: -118.57, logoStacked: "/canyons-logo.webp",        logoLongform: "/canyons-logo.webp" },

  // Orange County
  { id: "goldenwest",     name: "Golden West College",             district: "Coast CCD",                     regionId: "orange-county",      lat: 33.73, lng: -118.00, logoStacked: "/goldenwest-logo.png",      logoLongform: "/goldenwest-logo.png" },
  { id: "orangecoast",    name: "Orange Coast College",            district: "Coast CCD",                     regionId: "orange-county",      lat: 33.65, lng: -117.90, logoStacked: "/orangecoast-logo.png",     logoLongform: "/orangecoast-logo.png" },
  { id: "coastline",      name: "Coastline College",               district: "Coast CCD",                     regionId: "orange-county",      lat: 33.68, lng: -117.86, logoStacked: "/coastline-logo.png",       logoLongform: "/coastline-logo.png" },
  { id: "fullerton",      name: "Fullerton College",               district: "North Orange County CCD",       regionId: "orange-county",      lat: 33.87, lng: -117.92, logoStacked: "/fullerton-logo.svg",       logoLongform: "/fullerton-logo.svg" },
  { id: "cypress",        name: "Cypress College",                 district: "North Orange County CCD",       regionId: "orange-county",      lat: 33.81, lng: -118.01, logoStacked: "/cypress-logo.png",         logoLongform: "/cypress-logo.png" },
  { id: "santaana",      name: "Santa Ana College",               district: "Rancho Santiago CCD",           regionId: "orange-county",      lat: 33.75, lng: -117.87, logoStacked: "/santaana-logo.png",        logoLongform: "/santaana-logo.png" },
  { id: "santiagocyn",   name: "Santiago Canyon College",         district: "Rancho Santiago CCD",           regionId: "orange-county",      lat: 33.79, lng: -117.74 },
  { id: "saddleback",    name: "Saddleback College",              district: "South Orange County CCD",       regionId: "orange-county",      lat: 33.55, lng: -117.66, logoStacked: "/saddleback-logo.svg",     logoLongform: "/saddleback-logo.svg" },
  { id: "irvinevalley",  name: "Irvine Valley College",           district: "South Orange County CCD",       regionId: "orange-county",      lat: 33.69, lng: -117.83, logoStacked: "/irvinevalley-logo.svg",   logoLongform: "/irvinevalley-logo.svg" },

  // San Diego / Imperial
  { id: "sandiegomesa",   name: "San Diego Mesa College",          district: "San Diego CCD",                 regionId: "san-diego",          lat: 32.80, lng: -117.15, logoStacked: "/sandiegomesa-logo.png",    logoLongform: "/sandiegomesa-logo.png" },
  { id: "sandiegocity",   name: "San Diego City College",          district: "San Diego CCD",                 regionId: "san-diego",          lat: 32.71, lng: -117.16, logoStacked: "/sandiegocity-logo.png",    logoLongform: "/sandiegocity-logo-long.png" },
  { id: "sandiegomira",   name: "San Diego Miramar College",       district: "San Diego CCD",                 regionId: "san-diego",          lat: 32.90, lng: -117.14, logoStacked: "/sandiegomira-logo.svg",    logoLongform: "/sandiegomira-logo.svg" },
  { id: "grossmont",      name: "Grossmont College",               district: "Grossmont-Cuyamaca CCD",        regionId: "san-diego",          lat: 32.80, lng: -116.97, logoStacked: "/grossmont-logo.svg",       logoLongform: "/grossmont-logo.svg" },
  { id: "cuyamaca",       name: "Cuyamaca College",                district: "Grossmont-Cuyamaca CCD",        regionId: "san-diego",          lat: 32.79, lng: -116.97, logoStacked: "/cuyamaca-logo.svg",        logoLongform: "/cuyamaca-logo.svg" },
  { id: "palomar",        name: "Palomar College",                 district: "Palomar CCD",                   regionId: "san-diego",          lat: 33.13, lng: -117.06, logoStacked: "/palomar-logo.png",         logoLongform: "/palomar-logo-long.png" },
  { id: "miracostacc",    name: "MiraCosta College",               district: "MiraCosta CCD",                 regionId: "san-diego",          lat: 33.15, lng: -117.27, logoStacked: "/miracostacc-logo.svg",     logoLongform: "/miracostacc-logo.svg" },
  { id: "imperial",       name: "Imperial Valley College",         district: "Imperial CCD",                  regionId: "san-diego",          lat: 32.79, lng: -115.55, logoStacked: "/imperial-logo.png",        logoLongform: "/imperial-logo.png" },
  { id: "southwestern",  name: "Southwestern College",            district: "Southwestern CCD",              regionId: "san-diego",          lat: 32.64, lng: -117.00, logoStacked: "/southwestern-logo.png",   logoLongform: "/southwestern-logo.png" },
  { id: "sdcce",         name: "SD College of Continuing Ed",     district: "San Diego CCD",                 regionId: "san-diego",          lat: 32.70, lng: -117.11, logoStacked: "/sdcce-logo.webp",          logoLongform: "/sdcce-logo.webp" },
];
