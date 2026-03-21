export type College = {
  id: string;
  name: string;
  district: string;
  regionId: string;
  lat: number;
  lng: number;
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
    collegeCount: 9,
  },
  {
    id: "greater-sacramento",
    name: "Greater Sacramento",
    labelCenter: [-121.0, 39.2],
    zoomCenter: [-121.0, 39.2],
    scale: 8000,
    counties: ["Butte", "Glenn", "Colusa", "Plumas", "Sierra", "Nevada", "Placer", "El Dorado", "Yolo", "Sacramento", "Alpine"],
    collegeCount: 14,
  },
  {
    id: "bay-area",
    name: "Bay Area",
    labelCenter: [-122.1, 37.7],
    zoomCenter: [-122.1, 37.7],
    scale: 11000,
    counties: ["Marin", "Sonoma", "Napa", "Lake", "Mendocino", "Solano", "Contra Costa", "Alameda", "San Francisco", "San Mateo", "Santa Clara", "Santa Cruz"],
    collegeCount: 28,
  },
  {
    id: "central-valley",
    name: "Central Valley",
    labelCenter: [-119.4, 37.3],
    zoomCenter: [-119.4, 37.3],
    scale: 7000,
    counties: ["San Joaquin", "Calaveras", "Tuolumne", "Amador", "Mono", "Stanislaus", "Merced", "Mariposa", "Fresno", "Madera", "Kings", "Tulare"],
    collegeCount: 18,
  },
  {
    id: "central-coast",
    name: "Central Coast",
    labelCenter: [-120.8, 35.6],
    zoomCenter: [-120.8, 35.6],
    scale: 9000,
    counties: ["Monterey", "San Benito", "San Luis Obispo", "Santa Barbara"],
    collegeCount: 7,
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
    collegeCount: 28,
  },
  {
    id: "orange-county",
    name: "Orange County",
    labelCenter: [-117.75, 33.55],
    zoomCenter: [-117.75, 33.55],
    scale: 16000,
    counties: ["Orange"],
    collegeCount: 5,
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
  { id: "redwoods",       name: "College of the Redwoods",         district: "Redwoods CCD",                  regionId: "far-north",         lat: 40.80, lng: -124.16 },
  { id: "shasta",         name: "Shasta College",                  district: "Shasta-Tehama-Trinity JCCD",    regionId: "far-north",         lat: 40.61, lng: -122.37 },
  { id: "lassen",         name: "Lassen College",                  district: "Lassen CCD",                    regionId: "far-north",         lat: 40.44, lng: -120.65 },
  { id: "siskiyous",      name: "College of the Siskiyous",        district: "Siskiyous JCCD",                regionId: "far-north",         lat: 41.48, lng: -122.29 },
  { id: "delnorte",       name: "College of the Redwoods (DN)",    district: "Redwoods CCD",                  regionId: "far-north",         lat: 41.74, lng: -124.20 },
  { id: "featherriver",   name: "Feather River College",           district: "Feather River CCD",             regionId: "far-north",         lat: 39.93, lng: -120.95 },

  // Greater Sacramento
  { id: "butte",          name: "Butte College",                   district: "Butte-Glenn CCD",               regionId: "greater-sacramento", lat: 39.52, lng: -121.65 },
  { id: "sierra",         name: "Sierra College",                  district: "Sierra JCCD",                   regionId: "greater-sacramento", lat: 38.79, lng: -121.20 },
  { id: "saccc",          name: "Sacramento City College",         district: "Los Rios CCD",                  regionId: "greater-sacramento", lat: 38.56, lng: -121.49 },
  { id: "arc",            name: "American River College",          district: "Los Rios CCD",                  regionId: "greater-sacramento", lat: 38.67, lng: -121.37 },
  { id: "cosumnes",       name: "Cosumnes River College",          district: "Los Rios CCD",                  regionId: "greater-sacramento", lat: 38.44, lng: -121.42 },
  { id: "folsom",         name: "Folsom Lake College",             district: "Los Rios CCD",                  regionId: "greater-sacramento", lat: 38.67, lng: -121.17 },
  { id: "nevada",         name: "Nevada Union / Gold Hill",        district: "Nevada-Sierra CCD",             regionId: "greater-sacramento", lat: 39.29, lng: -121.06 },
  { id: "yuba",           name: "Yuba College",                    district: "Yuba CCD",                      regionId: "greater-sacramento", lat: 39.14, lng: -121.62 },

  // Bay Area
  { id: "ccsf",           name: "City College of San Francisco",   district: "San Francisco CCD",             regionId: "bay-area",           lat: 37.72, lng: -122.45 },
  { id: "foothill",       name: "Foothill College",                district: "Foothill-De Anza CCD",          regionId: "bay-area",           lat: 37.36, lng: -122.05 },
  { id: "deanza",         name: "De Anza College",                 district: "Foothill-De Anza CCD",          regionId: "bay-area",           lat: 37.31, lng: -122.04 },
  { id: "skyline",        name: "Skyline College",                 district: "San Mateo CCD",                 regionId: "bay-area",           lat: 37.62, lng: -122.46 },
  { id: "canada",         name: "Cañada College",                  district: "San Mateo CCD",                 regionId: "bay-area",           lat: 37.49, lng: -122.23 },
  { id: "cmc",            name: "College of San Mateo",            district: "San Mateo CCD",                 regionId: "bay-area",           lat: 37.54, lng: -122.32 },
  { id: "laney",          name: "Laney College",                   district: "Peralta CCD",                   regionId: "bay-area",           lat: 37.80, lng: -122.27 },
  { id: "merritt",        name: "Merritt College",                 district: "Peralta CCD",                   regionId: "bay-area",           lat: 37.83, lng: -122.22 },
  { id: "berkeleycc",     name: "Berkeley City College",           district: "Peralta CCD",                   regionId: "bay-area",           lat: 37.87, lng: -122.27 },
  { id: "alameda",        name: "College of Alameda",              district: "Peralta CCD",                   regionId: "bay-area",           lat: 37.77, lng: -122.23 },
  { id: "diablo",         name: "Diablo Valley College",           district: "Contra Costa CCD",              regionId: "bay-area",           lat: 37.96, lng: -122.07 },
  { id: "contracosta",    name: "Contra Costa College",            district: "Contra Costa CCD",              regionId: "bay-area",           lat: 37.97, lng: -122.34 },
  { id: "losmedanos",     name: "Los Medanos College",             district: "Contra Costa CCD",              regionId: "bay-area",           lat: 37.97, lng: -121.78 },
  { id: "cabrillo",       name: "Cabrillo College",                district: "Cabrillo CCD",                  regionId: "bay-area",           lat: 36.98, lng: -121.96 },
  { id: "gavilan",        name: "Gavilan College",                 district: "Gavilan JCCD",                  regionId: "bay-area",           lat: 36.97, lng: -121.54 },
  { id: "evergreen",      name: "Evergreen Valley College",        district: "San Jose-Evergreen CCD",        regionId: "bay-area",           lat: 37.34, lng: -121.80 },
  { id: "sanjosecity",    name: "San Jose City College",           district: "San Jose-Evergreen CCD",        regionId: "bay-area",           lat: 37.31, lng: -121.90 },

  // Central Valley
  { id: "fresno",         name: "Fresno City College",             district: "State Center CCD",              regionId: "central-valley",     lat: 36.73, lng: -119.79 },
  { id: "reedley",        name: "Reedley College",                 district: "State Center CCD",              regionId: "central-valley",     lat: 36.60, lng: -119.45 },
  { id: "clovis",         name: "Clovis Community College",        district: "State Center CCD",              regionId: "central-valley",     lat: 36.83, lng: -119.68 },
  { id: "visalia",        name: "College of the Sequoias",         district: "Sequoias CCD",                  regionId: "central-valley",     lat: 36.32, lng: -119.30 },
  { id: "merced",         name: "Merced College",                  district: "Merced CCD",                    regionId: "central-valley",     lat: 37.35, lng: -120.49 },
  { id: "modesto",        name: "Modesto Junior College",          district: "Yosemite CCD",                  regionId: "central-valley",     lat: 37.65, lng: -121.00 },
  { id: "columbia",       name: "Columbia College",                district: "Yosemite CCD",                  regionId: "central-valley",     lat: 38.04, lng: -120.41 },
  { id: "sanjoquin",      name: "San Joaquin Delta College",       district: "San Joaquin Delta CCD",         regionId: "central-valley",     lat: 37.96, lng: -121.29 },
  { id: "westhill",       name: "West Hills College Coalinga",     district: "West Hills CCD",                regionId: "central-valley",     lat: 36.15, lng: -120.35 },
  { id: "westhillslemo",  name: "West Hills College Lemoore",      district: "West Hills CCD",                regionId: "central-valley",     lat: 36.30, lng: -119.78 },

  // Central Coast
  { id: "cuesta",         name: "Cuesta College",                  district: "San Luis Obispo CCD",           regionId: "central-coast",      lat: 35.32, lng: -120.66 },
  { id: "sbcc",           name: "Santa Barbara City College",      district: "Santa Barbara CCD",             regionId: "central-coast",      lat: 34.43, lng: -119.72 },
  { id: "hancock",        name: "Allan Hancock College",           district: "Allan Hancock JCCD",            regionId: "central-coast",      lat: 34.90, lng: -120.43 },
  { id: "hartnell",       name: "Hartnell College",                district: "Hartnell CCD",                  regionId: "central-coast",      lat: 36.67, lng: -121.63 },
  { id: "montereypen",    name: "Monterey Peninsula College",      district: "Monterey Peninsula CCD",        regionId: "central-coast",      lat: 36.60, lng: -121.87 },
  { id: "cabrillovc",     name: "Ventura College",                 district: "Ventura CCD",                   regionId: "central-coast",      lat: 34.28, lng: -119.22 },
  { id: "oxnard",         name: "Oxnard College",                  district: "Ventura CCD",                   regionId: "central-coast",      lat: 34.22, lng: -119.18 },

  // Inland Empire
  { id: "desert",         name: "College of the Desert",           district: "Desert CCD",                    regionId: "inland-empire",      lat: 33.73, lng: -116.37 },
  { id: "sbvalley",       name: "San Bernardino Valley College",   district: "San Bernardino CCD",            regionId: "inland-empire",      lat: 34.10, lng: -117.29 },
  { id: "crafton",        name: "Crafton Hills College",           district: "San Bernardino CCD",            regionId: "inland-empire",      lat: 34.06, lng: -117.05 },
  { id: "chaffey",        name: "Chaffey College",                 district: "Chaffey CCD",                   regionId: "inland-empire",      lat: 34.10, lng: -117.66 },
  { id: "riverside",      name: "Riverside City College",          district: "Riverside CCD",                 regionId: "inland-empire",      lat: 33.98, lng: -117.37 },
  { id: "norco",          name: "Norco College",                   district: "Riverside CCD",                 regionId: "inland-empire",      lat: 33.93, lng: -117.55 },
  { id: "msjc",           name: "Mt. San Jacinto College",         district: "Mt. San Jacinto CCD",           regionId: "inland-empire",      lat: 33.75, lng: -117.22 },
  { id: "victor",         name: "Victor Valley College",           district: "Victor Valley CCD",             regionId: "inland-empire",      lat: 34.50, lng: -117.29 },
  { id: "barstow",        name: "Barstow Community College",       district: "Barstow CCD",                   regionId: "inland-empire",      lat: 34.90, lng: -117.02 },

  // Los Angeles
  { id: "lacc",           name: "Los Angeles City College",        district: "Los Angeles CCD",               regionId: "los-angeles",        lat: 34.08, lng: -118.31 },
  { id: "lavalley",       name: "Los Angeles Valley College",      district: "Los Angeles CCD",               regionId: "los-angeles",        lat: 34.18, lng: -118.40 },
  { id: "laharbor",       name: "Los Angeles Harbor College",      district: "Los Angeles CCD",               regionId: "los-angeles",        lat: 33.79, lng: -118.29 },
  { id: "lamission",      name: "Los Angeles Mission College",     district: "Los Angeles CCD",               regionId: "los-angeles",        lat: 34.26, lng: -118.42 },
  { id: "lapuente",       name: "East Los Angeles College",        district: "Los Angeles CCD",               regionId: "los-angeles",        lat: 34.02, lng: -118.15 },
  { id: "lasouthwest",    name: "Los Angeles Southwest College",   district: "Los Angeles CCD",               regionId: "los-angeles",        lat: 33.93, lng: -118.30 },
  { id: "latrade",        name: "Los Angeles Trade-Technical",     district: "Los Angeles CCD",               regionId: "los-angeles",        lat: 34.03, lng: -118.27 },
  { id: "lawest",         name: "West Los Angeles College",        district: "Los Angeles CCD",               regionId: "los-angeles",        lat: 33.99, lng: -118.43 },
  { id: "pcc",            name: "Pasadena City College",           district: "Pasadena Area CCD",             regionId: "los-angeles",        lat: 34.15, lng: -118.10 },
  { id: "mtsac",          name: "Mt. San Antonio College",         district: "Mt. San Antonio CCD",           regionId: "los-angeles",        lat: 34.02, lng: -117.85 },
  { id: "longbeach",      name: "Long Beach City College",         district: "Long Beach CCD",                regionId: "los-angeles",        lat: 33.81, lng: -118.18 },
  { id: "elcamino",       name: "El Camino College",               district: "El Camino CCD",                 regionId: "los-angeles",        lat: 33.86, lng: -118.34 },

  // Orange County
  { id: "golden west",    name: "Golden West College",             district: "Coast CCD",                     regionId: "orange-county",      lat: 33.73, lng: -118.00 },
  { id: "orangecoast",    name: "Orange Coast College",            district: "Coast CCD",                     regionId: "orange-county",      lat: 33.65, lng: -117.90 },
  { id: "coastline",      name: "Coastline College",               district: "Coast CCD",                     regionId: "orange-county",      lat: 33.68, lng: -117.86 },
  { id: "fullerton",      name: "Fullerton College",               district: "North Orange County CCD",       regionId: "orange-county",      lat: 33.87, lng: -117.92 },
  { id: "cypress",        name: "Cypress College",                 district: "North Orange County CCD",       regionId: "orange-county",      lat: 33.81, lng: -118.01 },

  // San Diego / Imperial
  { id: "sandiegomesa",   name: "San Diego Mesa College",          district: "San Diego CCD",                 regionId: "san-diego",          lat: 32.80, lng: -117.15 },
  { id: "sandiegocity",   name: "San Diego City College",          district: "San Diego CCD",                 regionId: "san-diego",          lat: 32.71, lng: -117.16 },
  { id: "sandiegomira",   name: "San Diego Miramar College",       district: "San Diego CCD",                 regionId: "san-diego",          lat: 32.90, lng: -117.14 },
  { id: "grossmont",      name: "Grossmont College",               district: "Grossmont-Cuyamaca CCD",        regionId: "san-diego",          lat: 32.80, lng: -116.97 },
  { id: "cuyamaca",       name: "Cuyamaca College",                district: "Grossmont-Cuyamaca CCD",        regionId: "san-diego",          lat: 32.79, lng: -116.97 },
  { id: "palomar",        name: "Palomar College",                 district: "Palomar CCD",                   regionId: "san-diego",          lat: 33.13, lng: -117.06 },
  { id: "miracostacc",    name: "MiraCosta College",               district: "MiraCosta CCD",                 regionId: "san-diego",          lat: 33.15, lng: -117.27 },
  { id: "imperial",       name: "Imperial Valley College",         district: "Imperial CCD",                  regionId: "san-diego",          lat: 32.79, lng: -115.55 },
];
