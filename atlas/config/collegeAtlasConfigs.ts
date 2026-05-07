import { makeSchoolConfig, SchoolConfig } from "@/config/schoolConfig";
import { CALIFORNIA_COLLEGES } from "@/state-atlas/californiaColleges";
import { COLLEGE_COLORS } from "@/config/collegeColors.generated";

const DEFAULT_BRAND_COLOR = "#1e3a5f";

// Build config for every college that has logo assets
const generatedConfigs = Object.fromEntries(
  CALIFORNIA_COLLEGES
    .filter((c) => c.logoStacked)
    .map((c) => [
      c.id,
      makeSchoolConfig(
        c.name,
        `/logos/${c.id}.png`,
        COLLEGE_COLORS[c.id] ?? DEFAULT_BRAND_COLOR,
      ),
    ])
);

// Manual brand color overrides (survives auto-generation of collegeColors).
//
// Most entries below come from the homepage-logo extraction pipeline at
// `scripts/extract-brand-colors.mjs` — vision identifies a logo bbox, the
// script extracts the dominant non-neutral color cluster, and a neon
// transform lifts it for the dark Kallipolis background. Reviewed via
// the /brand-audit page on 2026-05-06.
//
// The 13 colleges deliberately NOT overridden here (sandiegocity, lassen,
// siskiyous, desert, napavalley, mendocino, csm, merced, cerrocoso,
// lacity, irvinevalley, laketahoe, berkeleycc) keep their existing
// logo-file extracted colors from collegeColors.generated.ts — those
// looked correct in the audit and didn't need replacing.
const COLOR_OVERRIDES: Record<string, string> = {
  // North / Far North
  americanriver: "#f04264",   // ARC red // picked current 2026-05-07
  butte:         "#e2bd5b",   // gold (Roadrunners)
  cosumnes:      "#ff8800",   // picked custom 2026-05-07
  delnorte:      "#b32446",   // picked neon 2026-05-07
  featherriver:  "#2bee77",   // picked current 2026-05-07
  folsom:        "#8121b6",   // picked neon 2026-05-07
  laketahoe:     "#4fd1fd",   // picked current 2026-05-07
  lassen:        "#f07c42",   // picked current 2026-05-07
  mendocino:     "#ffd500",   // picked custom 2026-05-07
  nevada:        "#b92128",   // picked neon 2026-05-07
  redwoods:      "#f04268",   // pre-existing; not in FEATURED yet but kept // picked current 2026-05-07
  saccc:         "#d60043",   // Cardinal red
  shasta:        "#2bee68",   // forest green (Knights) // picked current 2026-05-07
  sierra:        "#f0424b",   // picked current 2026-05-07
  siskiyous:     "#5adcf2",   // picked current 2026-05-07
  woodland:      "#1bbb78",   // picked neon 2026-05-07
  yuba:          "#f8b41b",   // picked neon 2026-05-07

  // Bay Area
  alameda:     "#5ac5f2",   // picked current 2026-05-07
  berkeleycc:  "#4ddfff",   // picked current 2026-05-07
  cabrillo:    "#5acbf2",   // picked current 2026-05-07
  canada:      "#1bbb6e",   // picked neon 2026-05-07
  ccsf:        "#e32526",   // picked neon 2026-05-07
  chabot:      "#f0c142",   // picked current 2026-05-07
  contracosta: "#5acdf2",   // picked current 2026-05-07
  csm:         "#5ad8f2",   // picked current 2026-05-07
  deanza:      "#c21553",   // Mountain Lion cardinal (corrects prior navy drift) // picked neon 2026-05-07
  diablo:      "#27eb00",   // picked custom 2026-05-07
  evergreen:   "#2bee7b",   // picked current 2026-05-07
  foothill:    "#f0425a",   // scarlet (institutional) // picked current 2026-05-07
  gavilan:     "#5ad7f2",   // picked current 2026-05-07
  hartnell:    "#ff3389",   // Hartnell magenta // picked current 2026-05-07
  laney:       "#2bee7d",   // picked current 2026-05-07
  laspositas:  "#f0425a",   // picked current 2026-05-07
  losmedanos:  "#f24740",   // Mustang cardinal (corrects prior navy drift) // picked current 2026-05-07
  marin:       "#ce922a",   // picked neon 2026-05-07
  merritt:     "#5adef2",   // picked current 2026-05-07
  mission:     "#4dd7ff",   // picked current 2026-05-07
  montereypen: "#00b2d6",   // picked neon 2026-05-07
  napavalley:  "#f0bd42",   // picked current 2026-05-07
  ohlone:      "#6bee2b",   // picked current 2026-05-07
  sanjosecity: "#a45af2",   // picked current 2026-05-07
  santarosa:   "#5ad4f2",   // picked current 2026-05-07
  skyline:     "#f24440",   // picked current 2026-05-07
  solano:      "#5ad4f2",   // picked current 2026-05-07
  westvalley:  "#5ad9f2",   // picked current 2026-05-07

  // Central Valley / Mother Lode
  bakersfield:   "#f04255",   // picked current 2026-05-07
  cerrocoso:     "#5abdf2",   // picked current 2026-05-07
  clovis:        "#65ee1b",   // picked custom 2026-05-07
  columbia:      "#d00627",   // picked neon 2026-05-07
  fresno:        "#f04246",   // picked current 2026-05-07
  madera:        "#ce9c26",   // picked neon 2026-05-07
  merced:        "#f3c259",   // picked custom 2026-05-07
  modesto:       "#5ad4f2",   // picked current 2026-05-07
  porterville:   "#f04542",   // picked current 2026-05-07
  reedley:       "#f8933a",   // Tigers orange // picked current 2026-05-07
  sanjoquin:     "#fad538",   // picked current 2026-05-07
  sequoias:      "#8dee2b",   // (overridden again — kept lime per audit) // picked current 2026-05-07
  taft:          "#ebaa1f",   // picked neon 2026-05-07
  westhill:      "#0a95ff",   // picked custom 2026-05-07
  westhillslemo: "#eec681",   // picked custom 2026-05-07

  // South Central Coast
  allanhancock:   "#ffd733",   // Hancock gold (homepage-dominant pixel) // picked current 2026-05-07
  antelopevalley: "#b32354",   // picked neon 2026-05-07
  cabrillovc:     "#f6963c",   // picked current 2026-05-07
  canyons:        "#5ad4f2",   // picked current 2026-05-07
  cuesta:         "#2bee86",   // picked current 2026-05-07
  moorpark:       "#5abaf2",   // picked current 2026-05-07
  oxnard:         "#2bee7f",   // Condors green // picked current 2026-05-07
  sbcc:           "#f0425d",   // SBCC red // picked current 2026-05-07

  // Los Angeles
  cerritos:    "#5ad1f2",   // picked current 2026-05-07
  citrus:      "#ff7b00",   // picked custom 2026-05-07
  compton:     "#f04278",   // Tartar deep red // picked current 2026-05-07
  elcamino:    "#5ad4f2",   // picked current 2026-05-07
  glendale:    "#b2243a",   // picked neon 2026-05-07
  lacity:      "#ff3838",   // picked custom 2026-05-07
  laharbor:    "#ffc52e",   // picked neon 2026-05-07
  lamission:   "#e3e3e3",   // picked custom 2026-05-07
  lapierce:    "#ff0000",   // picked custom 2026-05-07
  lapuente:    "#5eb91d",   // picked neon 2026-05-07
  lasouthwest: "#00a0dd",   // picked neon 2026-05-07
  latrade:     "#be02e3",   // picked custom 2026-05-07
  lavalley:    "#1affcd",   // Monarchs green // picked current 2026-05-07
  lawest:      "#5ac0f2",   // picked current 2026-05-07
  longbeach:   "#f04d42",   // picked current 2026-05-07
  mtsac:       "#fd3561",   // Mountie maroon (corrects prior bright-orange drift) // picked current 2026-05-07
  pcc:         "#f04262",   // picked current 2026-05-07
  riohondo:    "#f9c900",   // picked neon 2026-05-07
  santamonica: "#4fedfc",   // picked current 2026-05-07

  // Orange County
  coastline:    "#5ad4f2",   // picked current 2026-05-07
  cypress:      "#4ed5fe",   // picked current 2026-05-07
  fullerton:    "#5ad4f2",   // picked current 2026-05-07
  goldenwest:   "#2dd100",   // picked custom 2026-05-07
  irvinevalley: "#5ac7f2",   // picked current 2026-05-07
  orangecoast:  "#ffa34d",   // picked custom 2026-05-07
  saddleback:   "#f04273",   // picked current 2026-05-07
  santaana:     "#f04247",   // picked current 2026-05-07
  santiagocyn:  "#29adff",   // picked custom 2026-05-07

  // Inland Empire / Desert
  barstow:      "#007bff",   // picked custom 2026-05-07
  chaffey:      "#d6003f",   // PMS 201-ish (corrects prior muted-pink drift) // picked neon 2026-05-07
  coppermtn:    "#b23b24",   // picked neon 2026-05-07
  crafton:      "#2bee93",   // picked current 2026-05-07
  desert:       "#ffc933",   // picked current 2026-05-07
  morenovalley: "#2cf295",   // picked custom 2026-05-07
  msjc:         "#b6252a",   // picked neon 2026-05-07
  norco:        "#ff2424",   // picked custom 2026-05-07
  paloverde:    "#5ad4f2",   // picked current 2026-05-07
  riverside:    "#f08a42",   // picked current 2026-05-07
  sbvalley:     "#5ae5f2",   // picked current 2026-05-07
  victor:       "#f04258",   // picked current 2026-05-07

  // San Diego / Imperial
  cuyamaca:     "#5ad4f2",   // picked current 2026-05-07
  grossmont:    "#14c2b2",   // picked neon 2026-05-07
  imperial:     "#f04249",   // IVC red // picked current 2026-05-07
  miracostacc:  "#5ac4f2",   // picked current 2026-05-07
  palomar:      "#f0424a",   // picked current 2026-05-07
  sandiegocity: "#f04253",   // picked current 2026-05-07
  sandiegomesa: "#5ad4f2",   // picked current 2026-05-07
  sandiegomira: "#5ae4f2",   // picked current 2026-05-07
  sdcce:        "#a85af2",   // picked current 2026-05-07
  southwestern: "#f04266",   // picked current 2026-05-07

};

const overrideConfigs = Object.fromEntries(
  Object.entries(COLOR_OVERRIDES)
    .filter(([id]) => generatedConfigs[id])
    .map(([id]) => {
      const college = CALIFORNIA_COLLEGES.find((c) => c.id === id)!;
      return [id, makeSchoolConfig(college.name, `/logos/${id}.png`, COLOR_OVERRIDES[id])];
    })
);

export const COLLEGE_ATLAS_CONFIGS: Record<string, SchoolConfig> = {
  ...generatedConfigs,
  ...overrideConfigs,
};

export function getCollegeAtlasConfig(collegeId: string): SchoolConfig | null {
  return COLLEGE_ATLAS_CONFIGS[collegeId] ?? null;
}
