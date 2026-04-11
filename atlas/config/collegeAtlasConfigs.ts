import { makeSchoolConfig, schoolConfig, SchoolConfig } from "@/config/schoolConfig";
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

// Manual brand color overrides (survives auto-generation of collegeColors)
const COLOR_OVERRIDES: Record<string, string> = {
  shasta: "#3A6F3A",
  redwoods: "#7B2D3E",
  sequoias: "#84be00",
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
  // Foothill overrides with its real hand-tuned brand color
  foothill: schoolConfig,
};

export function getCollegeAtlasConfig(collegeId: string): SchoolConfig | null {
  return COLLEGE_ATLAS_CONFIGS[collegeId] ?? null;
}
