import { makeSchoolConfig, schoolConfig, SchoolConfig } from "./schoolConfig";
import { CALIFORNIA_COLLEGES } from "./californiaColleges";
import { COLLEGE_COLORS } from "./collegeColors.generated";

const DEFAULT_BRAND_COLOR = "#1e3a5f";

// Build config for every college that has logo assets
const generatedConfigs = Object.fromEntries(
  CALIFORNIA_COLLEGES
    .filter((c) => c.logoStacked)
    .map((c) => [
      c.id,
      makeSchoolConfig(
        c.name,
        c.logoStacked!,
        COLLEGE_COLORS[c.id] ?? DEFAULT_BRAND_COLOR,
        c.logoLongform,
      ),
    ])
);

export const COLLEGE_ATLAS_CONFIGS: Record<string, SchoolConfig> = {
  ...generatedConfigs,
  // Foothill overrides with its real hand-tuned brand color
  foothill: schoolConfig,
};

export function getCollegeAtlasConfig(collegeId: string): SchoolConfig | null {
  return COLLEGE_ATLAS_CONFIGS[collegeId] ?? null;
}
