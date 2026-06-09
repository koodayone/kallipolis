// Frontend registry of aggregated-landscape instances — the presentation-side
// mirror of the backend's partnerships/landscape.py REGISTRY. Each instance is
// a bespoke surface (SVAMP, SMCCD, …) rendered by the same SvampDashboard /
// SvampView components, parameterized by `instance`.
//
// The backend spec is the canonical source for scope (colleges, SOCs, program
// division) and identity; this registry holds only what the frontend needs to
// render: the API/route id, the masthead identity, the brand accent, and the
// college-config ids (whose `.name` matches the backend college names the
// landscape endpoint returns). Keep `name`/`accent` in sync with the backend
// spec — they intentionally restate it for the masthead.

export type LandscapeInstance = {
  id: string;          // API id + route segment: /<id>, /partnerships/<id>/*
  name: string;        // masthead title (matches the backend spec name)
  shortTitle: string;  // compact masthead label (narrow viewports)
  accent: string;      // consortium brand accent
  collegeIds: string[]; // college-config ids, display order; .name == backend name
  published: boolean;  // false ⇒ DRAFT: viewable only outside a prod build
                       // (mirrors the backend spec.published gate)
};

// The SMCCD member set's sector views — a `member × sector` row, one per priority
// sector the district has CTE programs in (mirrors landscape.py). Generated from
// this table so the row stays in sync; name/accent restate the backend sector
// (sectors.py). `adm` is PUBLISHED — the canonical SMCCD Advanced Manufacturing
// surface (/smccd redirects here, replacing the retired curated 12-SOC view); the
// rest are DRAFT (local-only). `unassigned` is omitted (residual catch-all).
const SMCCD_COLLEGE_IDS = ["csm", "skyline", "canada"];
const SMCCD_SECTORS: { id: string; label: string; short: string; accent: string; published: boolean }[] = [
  { id: "adm",           label: "Advanced Manufacturing",                 short: "SMCCD Mfg",           accent: "#d9544d", published: true },
  { id: "biotech",       label: "Life Sciences / Biotech",                short: "SMCCD Biotech",       accent: "#2bb3a3", published: false },
  { id: "health",        label: "Health",                                 short: "SMCCD Health",        accent: "#3fb27f", published: false },
  { id: "business",      label: "Business & Entrepreneurship",            short: "SMCCD Business",      accent: "#c9a84c", published: false },
  { id: "atl",           label: "Advanced Transportation & Logistics",    short: "SMCCD Transport",     accent: "#c98a3a", published: false },
  { id: "public_safety", label: "Public Safety",                          short: "SMCCD Safety",        accent: "#5e6a9d", published: false },
  { id: "retail",        label: "Retail, Hospitality & Tourism",          short: "SMCCD Retail",        accent: "#d06a9b", published: false },
  { id: "ict",           label: "ICT / Digital Media",                    short: "SMCCD ICT",           accent: "#5a9bd4", published: false },
  { id: "agwet",         label: "Ag, Water & Environmental Technologies", short: "SMCCD Ag/Env",        accent: "#6fae54", published: false },
  { id: "edhd",          label: "Education & Human Development",          short: "SMCCD Education",     accent: "#b06fd0", published: false },
  { id: "ecu",           label: "Energy, Construction & Utilities",       short: "SMCCD Energy",        accent: "#d08a3a", published: false },
];

const smccdSectorInstances: Record<string, LandscapeInstance> = Object.fromEntries(
  SMCCD_SECTORS.map((s) => [
    `smccd-${s.id}`,
    {
      id: `smccd-${s.id}`,
      name: `San Mateo County CCD — ${s.label}`,
      shortTitle: s.short,
      accent: s.accent,
      collegeIds: SMCCD_COLLEGE_IDS,
      published: s.published,
    },
  ]),
);

export const LANDSCAPE_INSTANCES: Record<string, LandscapeInstance> = {
  svamp: {
    id: "svamp",
    name: "Silicon Valley Advanced Manufacturing Partnership",
    shortTitle: "SVAMP",
    accent: "#ff5a5a",
    collegeIds: ["deanza", "evergreen", "foothill", "mission", "ohlone"],
    published: true,
  },
  // The bare `smccd` id is intentionally absent — /smccd redirects to /smccd-adm.
  ...smccdSectorInstances,
};

// Draft (unpublished) instances render only OUTSIDE a production build — local
// `next dev` (NODE_ENV !== "production") shows them for iteration; the static
// export that ships to prod gates them. The mirror of the backend's
// KALLIPOLIS_DRAFT_LANDSCAPES gate, keyed on the build's own NODE_ENV so no
// extra env var is needed.
export const DRAFT_LANDSCAPES_ENABLED = process.env.NODE_ENV !== "production";

/** Whether an instance's surface may render in THIS build — published always,
 *  draft only when DRAFT_LANDSCAPES_ENABLED. Unknown id ⇒ false. */
export function isLandscapeViewable(id: string): boolean {
  const inst = LANDSCAPE_INSTANCES[id];
  return !!inst && (inst.published || DRAFT_LANDSCAPES_ENABLED);
}

/** The instance for an id, falling back to SVAMP for an unknown id. */
export function landscapeInstance(id: string): LandscapeInstance {
  return LANDSCAPE_INSTANCES[id] ?? LANDSCAPE_INSTANCES.svamp;
}
