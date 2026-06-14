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
// (sectors.py). All 11 sectors are PUBLISHED — the full member×sector rail ships
// in preview; `adm` is the canonical Advanced Manufacturing surface (/smccd
// redirects here, replacing the retired curated 12-SOC view). `unassigned` is
// omitted (residual catch-all). Mirror the backend published flags (landscape.py).
const SMCCD_COLLEGE_IDS = ["csm", "skyline", "canada"];
const SMCCD_SECTORS: { id: string; label: string; short: string; accent: string; published: boolean }[] = [
  { id: "adm",           label: "Advanced Manufacturing",                 short: "SMCCD Mfg",           accent: "#d9544d", published: true },
  { id: "biotech",       label: "Life Sciences / Biotech",                short: "SMCCD Biotech",       accent: "#2bb3a3", published: true },
  { id: "health",        label: "Health",                                 short: "SMCCD Health",        accent: "#3fb27f", published: true },
  { id: "business",      label: "Business & Entrepreneurship",            short: "SMCCD Business",      accent: "#c9a84c", published: true },
  { id: "atl",           label: "Advanced Transportation & Logistics",    short: "SMCCD Transport",     accent: "#c98a3a", published: true },
  { id: "public_safety", label: "Public Safety",                          short: "SMCCD Safety",        accent: "#5e6a9d", published: true },
  { id: "retail",        label: "Retail, Hospitality & Tourism",          short: "SMCCD Retail",        accent: "#d06a9b", published: true },
  { id: "ict",           label: "ICT / Digital Media",                    short: "SMCCD ICT",           accent: "#5a9bd4", published: true },
  { id: "agwet",         label: "Ag, Water & Environmental Technologies", short: "SMCCD Ag/Env",        accent: "#6fae54", published: true },
  { id: "edhd",          label: "Education & Human Development",          short: "SMCCD Education",     accent: "#b06fd0", published: true },
  { id: "ecu",           label: "Energy, Construction & Utilities",       short: "SMCCD Energy",        accent: "#d08a3a", published: true },
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

// BACCC — the Bay Area Community College Consortium: the same 11-sector rail
// over all 26 Bay colleges (the consortium-level join). Same sector metadata as
// SMCCD (id/label/accent — the SWP priority sectors are shared); only the member
// (26 colleges) and identity differ. The coverage matrix flips to vertical
// headers at this column count (CoverageMatrix), the one rendering change the
// 26-wide join needs. Mirrors landscape.py's BACCC registry.
const BACCC_COLLEGE_IDS = ["berkeleycc", "cabrillo", "canada", "chabot", "ccsf", "alameda", "marin", "csm", "contracosta", "deanza", "diablo", "evergreen", "foothill", "gavilan", "laney", "laspositas", "losmedanos", "merritt", "mission", "napavalley", "ohlone", "sanjosecity", "santarosa", "skyline", "solano", "westvalley"];
const BACCC_SECTORS = SMCCD_SECTORS.map((s) => ({ ...s, short: s.short.replace("SMCCD", "BACCC") }));
const bacccSectorInstances: Record<string, LandscapeInstance> = Object.fromEntries(
  BACCC_SECTORS.map((s) => [
    `baccc-${s.id}`,
    {
      id: `baccc-${s.id}`,
      name: `Bay Area Community College Consortium — ${s.label}`,
      shortTitle: s.short,
      accent: s.accent,
      collegeIds: BACCC_COLLEGE_IDS,
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
  // The bare `baccc` id is intentionally absent — /baccc redirects to /baccc-adm.
  ...bacccSectorInstances,
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

// Generated instances (any college/district at /landscape/<member>/<sector>)
// have no pinned row; a route client registers their identity (built from the
// backend landscape index) before rendering, so the many landscapeInstance()
// call sites in the dashboard + report resolve correctly instead of falling back
// to SVAMP. Client-side only; pinned ids never touch it.
const _generated = new Map<string, LandscapeInstance>();

/** Register a generated instance's identity so landscapeInstance() resolves it. */
export function registerGeneratedInstance(inst: LandscapeInstance): void {
  _generated.set(inst.id, inst);
}

/** The instance for an id: a pinned row, a registered generated instance, else
 *  the SVAMP fallback. */
export function landscapeInstance(id: string): LandscapeInstance {
  return LANDSCAPE_INSTANCES[id] ?? _generated.get(id) ?? LANDSCAPE_INSTANCES.svamp;
}

export type SectorTab = { instanceId: string; sectorId: string; label: string; accent: string; published: boolean };

// Curatorial rail order — the district's priority / tech-forward industries
// (Energy·Construction, Advanced Manufacturing, Biotech, Transportation) occupy
// the visual CENTER of the switcher (the most prominent position); the rest
// flank outward. Deliberate placement, NOT the canonical SMCCD_SECTORS order.
export const RAIL_ORDER = ["retail", "edhd", "health", "ecu", "adm", "biotech", "atl", "ict", "business", "public_safety", "agwet"];

/** Sibling sector instances of a member-set landscape, in CURATORIAL rail order
 *  (priority industries centered) — the data behind the industry switcher.
 *  "smccd-*" → the 11 SMCCD sectors; any other instance → [] (no rail). */
export function memberSectors(instanceId: string): SectorTab[] {
  const member =
    instanceId.startsWith("smccd-") ? { prefix: "smccd", table: SMCCD_SECTORS } :
    instanceId.startsWith("baccc-") ? { prefix: "baccc", table: BACCC_SECTORS } :
    null;
  if (!member) return [];
  const byId = new Map(member.table.map((s) => [s.id, s]));
  return RAIL_ORDER
    .map((id) => byId.get(id))
    .filter((s): s is { id: string; label: string; short: string; accent: string; published: boolean } => !!s)
    .map((s) => ({
      instanceId: `${member.prefix}-${s.id}`,
      sectorId: s.id,
      label: s.label,
      accent: s.accent,
      published: s.published,
    }));
}
