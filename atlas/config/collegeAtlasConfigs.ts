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
  redwoods:      "#7B2D3E",   // pre-existing; not in FEATURED yet but kept
  // Homepage-extraction pipeline (2026-05-06):
  shasta:        "#23b350",   // forest green (Knights)
  butte:         "#e2bd5b",   // gold (Roadrunners)
  foothill:      "#b52135",   // scarlet (institutional)
  hartnell:      "#d6005a",   // Hartnell magenta
  losmedanos:    "#c8150e",   // Mustang cardinal (corrects prior navy drift)
  deanza:        "#d0061b",   // Mountain Lion cardinal (corrects prior navy drift)
  americanriver: "#cf2a4a",   // ARC red
  saccc:         "#d60043",   // Cardinal red
  sequoias:      "#84dd29",   // (overridden again — kept lime per audit)
  reedley:       "#f89742",   // Tigers orange
  sbcc:          "#ba1c34",   // SBCC red
  oxnard:        "#24b261",   // Condors green
  allanhancock:  "#ffcd00",   // Hancock gold (homepage-dominant pixel)
  compton:       "#c1154a",   // Tartar deep red
  lavalley:      "#00d6a7",   // Monarchs green
  mtsac:         "#d50231",   // Mountie maroon (corrects prior bright-orange drift)
  chaffey:       "#bd1a3e",   // PMS 201-ish (corrects prior muted-pink drift)
  imperial:      "#d1232a",   // IVC red
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
