/**
 * SVAMP report view ⇄ URL anchoring.
 *
 * Each surface lives at one route (the dashboard at /svamp — the root —
 * and the report at /svamp/report); its view (lens + selection) is
 * client-side state.
 * Encoding that state in the URL query makes any view shareable and
 * refresh-stable, and — since each change re-stamps the URL and fires the
 * analytics beacon — makes the analytics record *be* the shareable URL.
 * Deliberately uses window.location + history.replaceState rather than
 * reactive useSearchParams, which avoids the static-export (output: "export")
 * Suspense/prerender pitfalls.
 *
 * Contract (query params, both surfaces):
 *   lens    = programs | occupations | employers   (absent ⇒ programs default)
 *   soc     = SOC code            (occupations lens)
 *   top     = TOP6 code           (programs lens)
 *   college = college id          (targeted view; presence ⇒ targeted). Shared
 *             by the occupations and programs lenses — safe because only the
 *             active lens writes it (the parent's occupations effect is guarded
 *             on lens; ProgramsLens only exists while the programs lens is
 *             active), and switchLens clears it on every lens change.
 *   emp     = employer name       (employers lens; URL-encoded)
 *   panel   = expanded panel id   (dashboard only; e.g. programs.coverage —
 *             a Grafana-style full-viewport panel view, shareable like any
 *             other view state. The report ignores it.)
 */

import { trackView } from "@/analytics";

export type LandscapeParamKey = "lens" | "soc" | "college" | "top" | "emp" | "panel";
const KEYS: LandscapeParamKey[] = ["lens", "soc", "college", "top", "emp", "panel"];

export type LandscapeParams = Partial<Record<LandscapeParamKey, string>>;

/** Read the SVAMP view params from the current URL. Client-only ({} on server). */
export function readLandscapeParams(): LandscapeParams {
  if (typeof window === "undefined") return {};
  const sp = new URLSearchParams(window.location.search);
  const out: LandscapeParams = {};
  for (const k of KEYS) {
    const v = sp.get(k);
    if (v) out[k] = v;
  }
  return out;
}

/**
 * Patch the SVAMP view params on the URL and report the new view.
 *
 * `patch` keys: a string sets the param; null/"" deletes it; a key omitted from
 * `patch` is left untouched (so each owner — parent lens, programs child,
 * employers child — writes only its own slice). Switching lens passes the
 * cross-lens keys as null to clear them.
 *
 * Uses history.replaceState (no new history entries — back exits the report),
 * then fires the analytics beacon with the resulting URL.
 */
export function writeLandscapeParams(patch: Partial<Record<LandscapeParamKey, string | null>>): void {
  if (typeof window === "undefined") return;
  const sp = new URLSearchParams(window.location.search);
  for (const k of KEYS) {
    if (!(k in patch)) continue;            // omitted ⇒ leave as-is
    const v = patch[k];
    if (v) sp.set(k, v);
    else sp.delete(k);                       // null/"" ⇒ delete
  }
  const qs = sp.toString();
  const url = qs ? `${window.location.pathname}?${qs}` : window.location.pathname;
  window.history.replaceState(null, "", url);
  trackView(url);
}
