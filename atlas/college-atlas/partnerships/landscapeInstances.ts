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

export const LANDSCAPE_INSTANCES: Record<string, LandscapeInstance> = {
  svamp: {
    id: "svamp",
    name: "Silicon Valley Advanced Manufacturing Partnership",
    shortTitle: "SVAMP",
    accent: "#ff5a5a",
    collegeIds: ["deanza", "evergreen", "foothill", "mission", "ohlone"],
    published: true,
  },
  smccd: {
    id: "smccd",
    name: "SMCCD - Advanced Manufacturing",
    shortTitle: "SMCCD",
    accent: "#8b6fd0",
    collegeIds: ["csm", "skyline", "canada"],
    // DRAFT: SMCCD's DataMart data isn't in prod Neo4j yet (confirmed
    // 2026-06-07). Gated from the public build; flip to true once it lands.
    published: false,
  },
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
