/**
 * /brand-audit — interactive brand-color picker for every California
 * Community College in CALIFORNIA_COLLEGES. Each card shows:
 *   - the captured top-of-homepage screenshot
 *   - the logo-region crop the algorithm read pixels from
 *   - four clickable color candidates: Current (live in atlas),
 *     Generated (logo-file extracted), Raw (homepage logo dominant
 *     cluster), Neon (raw → HSL lift)
 *   - a custom #rrggbb input
 *   - the currently-picked hex with a Clear button
 *
 * Picks persist to public/brand-audit/picks.json via /api/brand-picks
 * (Node-runtime, dev-only). A follow-up tool reads picks.json and
 * promotes selections into config/collegeAtlasConfigs.ts COLOR_OVERRIDES.
 *
 * Pipeline that produces the inputs:
 *   1. scripts/extract-brand-headers.mjs  → public/brand-audit/captures.json + thumbs/*.png
 *   2. vision-analysis sub-agent + scripts/extract-brand-colors.mjs
 *      → public/brand-audit/{logo-bboxes,analyzed}.json + logos/*.png
 */
import { promises as fs } from "node:fs";
import path from "node:path";
import { CALIFORNIA_COLLEGES } from "@/state-atlas/californiaColleges";
import { getCollegeAtlasConfig } from "@/config/collegeAtlasConfigs";
import { COLLEGE_COLORS } from "@/config/collegeColors.generated";
import PickerCard, { type PickerRow } from "./PickerCard";

// Force dynamic so the page reads picks.json on every request and the
// picker reflects the latest state. The export-static deploy still works
// because Cloudflare's Next adapter will fall back to runtime rendering
// for routes that opt out of static.
export const dynamic = "force-dynamic";

type Capture = {
  id: string;
  url: string;
  finalUrl?: string | null;
  thumb?: string;
  status: string;
  error?: string | null;
};

type Analyzed = {
  id: string;
  hex_raw: string | null;
  hex_neon: string | null;
  source: string;
  confidence: "high" | "medium" | "low";
  dominance?: number;
  non_neutral_pixels?: number;
  note?: string;
};

type PicksFile = {
  version: 1;
  updated_at: string;
  picks: Record<string, { hex: string; source: string; updated_at: string }>;
};

async function readJsonOrEmpty<T>(p: string, fallback: T): Promise<T> {
  try {
    const raw = await fs.readFile(p, "utf-8");
    return JSON.parse(raw) as T;
  } catch {
    return fallback;
  }
}

function hexToRgb(hex: string): [number, number, number] | null {
  const m = /^#?([0-9a-f]{6})$/i.exec(hex.trim());
  if (!m) return null;
  const n = parseInt(m[1], 16);
  return [(n >> 16) & 0xff, (n >> 8) & 0xff, n & 0xff];
}

function rgbDistance(a: string, b: string): number {
  const ra = hexToRgb(a), rb = hexToRgb(b);
  if (!ra || !rb) return 1;
  const dr = ra[0] - rb[0], dg = ra[1] - rb[1], db = ra[2] - rb[2];
  return Math.sqrt(dr * dr + dg * dg + db * db) / Math.sqrt(3 * 255 * 255);
}

async function loadRows(): Promise<{ rows: PickerRow[]; picks: PicksFile["picks"]; generatedAt: string | null; analyzedCount: number }> {
  const root = path.resolve(process.cwd(), "public", "brand-audit");
  const captures = await readJsonOrEmpty<{ generated_at: string; captures: Capture[] }>(
    path.join(root, "captures.json"),
    { generated_at: "", captures: [] },
  );
  const analyzed = await readJsonOrEmpty<{ entries: Analyzed[] }>(
    path.join(root, "analyzed.json"),
    { entries: [] },
  );
  const picksFile = await readJsonOrEmpty<PicksFile>(
    path.join(root, "picks.json"),
    { version: 1, updated_at: "", picks: {} },
  );
  const analyzedById = new Map(analyzed.entries.map((e) => [e.id, e]));
  const collegeById = new Map(CALIFORNIA_COLLEGES.map((c) => [c.id, c]));

  const rows: PickerRow[] = captures.captures.map((cap) => {
    const a = analyzedById.get(cap.id);
    const college = collegeById.get(cap.id);
    const currentHex = getCollegeAtlasConfig(cap.id)?.brandColorNeon ?? null;
    const generatedHex = COLLEGE_COLORS[cap.id] ?? null;
    const rawHex = a?.hex_raw ?? null;
    const neonHex = a?.hex_neon ?? null;
    const delta =
      currentHex && neonHex ? rgbDistance(currentHex, neonHex) : -1;

    return {
      id: cap.id,
      name: college?.name ?? cap.id,
      url: cap.finalUrl ?? cap.url,
      thumb: cap.thumb,
      logoCrop: `/brand-audit/logos/${cap.id}.png`,
      status: cap.status,
      error: cap.error ?? null,
      currentHex,
      rawHex,
      neonHex,
      generatedHex,
      proposedSource: a?.source ?? null,
      confidence: a?.confidence ?? null,
      dominance: a?.dominance ?? null,
      note: a?.note ?? null,
      delta,
    };
  });

  // Already-picked → after un-picked. Inside un-picked, drift first,
  // then unanalyzed, then matches.
  rows.sort((x, y) => {
    const xPicked = x.id in picksFile.picks ? 1 : 0;
    const yPicked = y.id in picksFile.picks ? 1 : 0;
    if (xPicked !== yPicked) return xPicked - yPicked;
    if (x.delta < 0 && y.delta >= 0) return -1;
    if (y.delta < 0 && x.delta >= 0) return 1;
    return y.delta - x.delta;
  });

  return {
    rows,
    picks: picksFile.picks,
    generatedAt: captures.generated_at || null,
    analyzedCount: analyzed.entries.length,
  };
}

export default async function BrandAuditPage() {
  const { rows, picks, generatedAt, analyzedCount } = await loadRows();
  const pickedCount = Object.keys(picks).length;

  return (
    <div className="domain-scroll" style={{ background: "#060d1f", color: "#fff", minHeight: "100vh", padding: "32px 40px 80px" }}>
      <header style={{ display: "flex", alignItems: "baseline", gap: 24, marginBottom: 16, flexWrap: "wrap" }}>
        <h1 style={{ fontFamily: "var(--font-days-one), sans-serif", fontSize: 28, margin: 0 }}>
          Brand Color Picker
        </h1>
        <span style={{ fontFamily: "var(--font-inter), sans-serif", fontSize: 12, color: "rgba(255,255,255,0.45)", letterSpacing: "0.08em", textTransform: "uppercase" }}>
          {rows.length} colleges · {analyzedCount} analyzed · {pickedCount} picked
          {generatedAt ? ` · captured ${new Date(generatedAt).toLocaleString()}` : ""}
        </span>
      </header>

      <p style={{ fontFamily: "var(--font-inter), sans-serif", fontSize: 13, color: "rgba(255,255,255,0.6)", maxWidth: 760, lineHeight: 1.55, marginTop: 0, marginBottom: 32 }}>
        Click a swatch below each card to choose that color for that college. The pick persists to{" "}
        <code style={{ background: "rgba(255,255,255,0.06)", padding: "2px 6px", borderRadius: 3 }}>
          atlas/public/brand-audit/picks.json
        </code>
        . When you&apos;re done, tell Claude &ldquo;promote picks&rdquo; and the selections get written into{" "}
        <code style={{ background: "rgba(255,255,255,0.06)", padding: "2px 6px", borderRadius: 3 }}>
          COLOR_OVERRIDES
        </code>{" "}
        in <code style={{ background: "rgba(255,255,255,0.06)", padding: "2px 6px", borderRadius: 3 }}>collegeAtlasConfigs.ts</code>.
        Picked cards float to the bottom; un-picked drifts surface first.
      </p>

      <div style={{
        display: "grid",
        gridTemplateColumns: "repeat(auto-fill, minmax(380px, 1fr))",
        gap: 24,
      }}>
        {rows.map((row) => (
          <PickerCard
            key={row.id}
            row={row}
            initialPick={picks[row.id] ?? null}
          />
        ))}
      </div>
    </div>
  );
}
