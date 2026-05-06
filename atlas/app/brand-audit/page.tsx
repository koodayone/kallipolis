/**
 * /brand-audit — internal review page for the brand-color extraction
 * pipeline. Lists every featured college with:
 *   - the captured top-of-homepage screenshot
 *   - the brand color the vision-analysis step picked from that screenshot
 *   - the brand color the State Atlas currently renders (from logo
 *     extraction + manual overrides)
 *   - a small diamond rendered with the proposed color so the user can
 *     see what would actually appear on the State Atlas
 *   - a clickable link out to the source homepage
 *
 * The pipeline that produces the inputs:
 *   1. scripts/extract-brand-headers.mjs  → public/brand-audit/captures.json
 *   2. vision-analysis sub-agent           → public/brand-audit/analyzed.json
 *   This page merges the two at request time. Both files are static under
 *   /public/ so they're easy to inspect or hand-edit when iterating.
 */
import { promises as fs } from "node:fs";
import path from "node:path";
import { CALIFORNIA_COLLEGES } from "@/state-atlas/californiaColleges";
import { getCollegeAtlasConfig } from "@/config/collegeAtlasConfigs";

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

type Row = {
  id: string;
  name: string;
  url: string;
  thumb?: string;
  logoCrop?: string;        // /brand-audit/logos/{id}.png
  status: string;
  error?: string | null;
  currentHex: string | null;
  rawHex: string | null;
  neonHex: string | null;
  proposedSource: string | null;
  confidence: string | null;
  dominance: number | null;
  note: string | null;
  delta: number;            // 0..1, RGB distance, used to surface drifts first
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

async function loadRows(): Promise<{ rows: Row[]; generatedAt: string | null; analyzedCount: number }> {
  const root = path.resolve(process.cwd(), "public", "brand-audit");
  const captures = await readJsonOrEmpty<{ generated_at: string; captures: Capture[] }>(
    path.join(root, "captures.json"),
    { generated_at: "", captures: [] },
  );
  const analyzed = await readJsonOrEmpty<{ entries: Analyzed[] }>(
    path.join(root, "analyzed.json"),
    { entries: [] },
  );
  const analyzedById = new Map(analyzed.entries.map((e) => [e.id, e]));
  const collegeById = new Map(CALIFORNIA_COLLEGES.map((c) => [c.id, c]));

  const rows: Row[] = captures.captures.map((cap) => {
    const a = analyzedById.get(cap.id);
    const college = collegeById.get(cap.id);
    const currentHex = getCollegeAtlasConfig(cap.id)?.brandColorNeon ?? null;
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
      proposedSource: a?.source ?? null,
      confidence: a?.confidence ?? null,
      dominance: a?.dominance ?? null,
      note: a?.note ?? null,
      delta,
    };
  });

  // Drifts first (largest delta), then unanalyzed, then close matches.
  rows.sort((x, y) => {
    if (x.delta < 0 && y.delta >= 0) return -1; // unanalyzed → top so user notices
    if (y.delta < 0 && x.delta >= 0) return 1;
    return y.delta - x.delta;
  });

  return { rows, generatedAt: captures.generated_at || null, analyzedCount: analyzed.entries.length };
}

export default async function BrandAuditPage() {
  const { rows, generatedAt, analyzedCount } = await loadRows();

  return (
    <div className="domain-scroll" style={{ background: "#060d1f", color: "#fff", minHeight: "100vh", padding: "32px 40px 80px" }}>
      <header style={{ display: "flex", alignItems: "baseline", gap: 24, marginBottom: 32 }}>
        <h1 style={{ fontFamily: "var(--font-days-one), sans-serif", fontSize: 28, margin: 0 }}>
          Brand Color Audit
        </h1>
        <span style={{ fontFamily: "var(--font-inter), sans-serif", fontSize: 12, color: "rgba(255,255,255,0.45)", letterSpacing: "0.08em", textTransform: "uppercase" }}>
          {rows.length} colleges · {analyzedCount} analyzed
          {generatedAt ? ` · captured ${new Date(generatedAt).toLocaleString()}` : ""}
        </span>
      </header>

      <p style={{ fontFamily: "var(--font-inter), sans-serif", fontSize: 13, color: "rgba(255,255,255,0.6)", maxWidth: 720, lineHeight: 1.55, marginTop: 0, marginBottom: 32 }}>
        Each card pairs the live homepage header against the brand color the State Atlas currently renders and the
        color extracted by vision analysis of that header. Cards are sorted by drift (biggest disagreement first).
        Click any thumbnail to open the source homepage.
      </p>

      <div style={{
        display: "grid",
        gridTemplateColumns: "repeat(auto-fill, minmax(380px, 1fr))",
        gap: 24,
      }}>
        {rows.map((row) => (
          <Card key={row.id} row={row} />
        ))}
      </div>
    </div>
  );
}

function Card({ row }: { row: Row }) {
  const driftBucket =
    row.delta < 0 ? "pending" :
    row.delta < 0.05 ? "match" :
    row.delta < 0.18 ? "near" :
    "drift";
  const driftLabel = {
    pending: "Pending analysis",
    match: "Match",
    near: "Near",
    drift: "Drift",
  }[driftBucket];
  const driftColor = {
    pending: "rgba(255,255,255,0.35)",
    match: "rgba(120, 200, 140, 0.85)",
    near: "rgba(220, 180, 90, 0.85)",
    drift: "rgba(220, 100, 100, 0.95)",
  }[driftBucket];

  return (
    <div style={{
      borderRadius: 8,
      overflow: "hidden",
      background: "rgba(255,255,255,0.03)",
      border: "1px solid rgba(255,255,255,0.08)",
      display: "flex",
      flexDirection: "column",
    }}>
      {/* Header thumbnail (clickable to source) */}
      <a
        href={row.url}
        target="_blank"
        rel="noreferrer noopener"
        style={{ display: "block", position: "relative", aspectRatio: "1280 / 600", background: "#0a1428" }}
        title={`Open ${row.name} homepage`}
      >
        {row.thumb ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={row.thumb}
            alt={`Header of ${row.name}`}
            style={{ width: "100%", height: "100%", objectFit: "cover", objectPosition: "top" }}
          />
        ) : (
          <div style={{ display: "flex", alignItems: "center", justifyContent: "center", height: "100%", fontFamily: "var(--font-inter), sans-serif", fontSize: 12, color: "rgba(255,255,255,0.4)" }}>
            No capture {row.error ? `· ${row.error}` : ""}
          </div>
        )}
      </a>

      {/* Logo crop — exact pixels the algorithm read for color extraction */}
      {row.logoCrop && row.thumb && (
        <div style={{ borderTop: "1px solid rgba(255,255,255,0.06)", padding: "8px 18px", display: "flex", alignItems: "center", gap: 12, background: "rgba(0,0,0,0.25)" }}>
          <span style={{ fontFamily: "var(--font-inter), sans-serif", fontSize: 9, fontWeight: 700, letterSpacing: "0.14em", textTransform: "uppercase", color: "rgba(255,255,255,0.5)", flexShrink: 0 }}>
            Logo crop
          </span>
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src={row.logoCrop}
            alt={`Logo region read for ${row.name}`}
            style={{ height: 36, border: "1px solid rgba(255,255,255,0.1)", background: "#fff" }}
          />
          {row.dominance !== null && (
            <span style={{ fontFamily: "var(--font-inter), sans-serif", fontSize: 10, color: "rgba(255,255,255,0.45)", marginLeft: "auto" }}>
              {Math.round(row.dominance * 100)}% dominance
            </span>
          )}
        </div>
      )}

      {/* Body */}
      <div style={{ padding: "16px 18px", display: "flex", flexDirection: "column", gap: 12 }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 10 }}>
          <div style={{ display: "flex", flexDirection: "column", gap: 4, minWidth: 0, flex: 1 }}>
            <span style={{ fontFamily: "var(--font-inter), sans-serif", fontSize: 14, fontWeight: 600, color: "#fff", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
              {row.name}
            </span>
            <a
              href={row.url}
              target="_blank"
              rel="noreferrer noopener"
              style={{ fontFamily: "var(--font-inter), sans-serif", fontSize: 11, color: "rgba(255,255,255,0.4)", textDecoration: "none", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}
            >
              {row.url.replace(/^https?:\/\//, "").replace(/\/$/, "")} ↗
            </a>
          </div>
          <span style={{
            fontFamily: "var(--font-inter), sans-serif",
            fontSize: 9,
            fontWeight: 700,
            letterSpacing: "0.14em",
            textTransform: "uppercase",
            padding: "3px 8px",
            borderRadius: 999,
            background: "rgba(255,255,255,0.04)",
            color: driftColor,
            border: `1px solid ${driftColor}`,
            flexShrink: 0,
            whiteSpace: "nowrap",
          }}>
            {driftLabel}
          </span>
        </div>

        {/* Color comparison — three swatches: current (logo extraction),
            raw (logo-crop dominant cluster), neon (raw → HSL lift) */}
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 10 }}>
          <Swatch label="Current" hex={row.currentHex} sub="from logo file" />
          <Swatch label="Raw" hex={row.rawHex} sub={row.proposedSource ?? "—"} />
          <Swatch label="Neon" hex={row.neonHex} sub="HSL lift" />
        </div>

        {/* Sample diamond on dark — what the user would see in the State Atlas */}
        <div style={{ display: "flex", alignItems: "center", gap: 14, padding: "10px 12px", background: "#060d1f", border: "1px solid rgba(255,255,255,0.05)", borderRadius: 4 }}>
          <span style={{ fontFamily: "var(--font-inter), sans-serif", fontSize: 10, color: "rgba(255,255,255,0.4)", letterSpacing: "0.1em", textTransform: "uppercase" }}>
            Sample
          </span>
          <SampleDiamond hex={row.neonHex} />
          <span style={{ fontFamily: "var(--font-inter), sans-serif", fontSize: 10, color: "rgba(255,255,255,0.4)" }}>
            proposed
          </span>
          <SampleDiamond hex={row.currentHex} />
          <span style={{ fontFamily: "var(--font-inter), sans-serif", fontSize: 10, color: "rgba(255,255,255,0.4)" }}>
            current
          </span>
        </div>

        {row.note && (
          <span style={{ fontFamily: "var(--font-inter), sans-serif", fontSize: 11, color: "rgba(220, 180, 90, 0.85)", lineHeight: 1.5 }}>
            {row.note}
          </span>
        )}
      </div>
    </div>
  );
}

function Swatch({ label, hex, sub }: { label: string; hex: string | null; sub: string }) {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
      <span style={{ fontFamily: "var(--font-inter), sans-serif", fontSize: 9, fontWeight: 700, letterSpacing: "0.14em", textTransform: "uppercase", color: "rgba(255,255,255,0.5)" }}>
        {label}
      </span>
      <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
        <div style={{
          width: 32,
          height: 32,
          borderRadius: 4,
          background: hex ?? "transparent",
          border: hex ? "1px solid rgba(255,255,255,0.12)" : "1px dashed rgba(255,255,255,0.18)",
          flexShrink: 0,
        }} />
        <div style={{ display: "flex", flexDirection: "column", minWidth: 0 }}>
          <span style={{ fontFamily: "var(--font-mono), Menlo, monospace", fontSize: 11, color: "#fff" }}>
            {hex ?? "—"}
          </span>
          <span style={{ fontFamily: "var(--font-inter), sans-serif", fontSize: 10, color: "rgba(255,255,255,0.4)", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
            {sub}
          </span>
        </div>
      </div>
    </div>
  );
}

function SampleDiamond({ hex }: { hex: string | null }) {
  if (!hex) return <span style={{ width: 14, height: 14, display: "inline-block", border: "1px dashed rgba(255,255,255,0.2)", transform: "rotate(45deg)" }} />;
  return (
    <span style={{
      width: 14,
      height: 14,
      display: "inline-block",
      background: hex,
      transform: "rotate(45deg)",
      boxShadow: `0 0 6px ${hex}55`,
    }} />
  );
}
