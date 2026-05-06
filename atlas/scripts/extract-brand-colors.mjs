/**
 * Layered brand-color extraction pipeline.
 *
 *   header thumb (1280×600)
 *     → crop top-left logo region (320×120)
 *     → bucket non-neutral pixels by quantized HSL
 *     → pick the most-populous bucket → raw brand RGB
 *     → neon transform (HSL lift) → display hex
 *
 * Why crop instead of analyzing the whole header: hero photos, cookie
 * banners, multi-color CTAs, and band+nav layered headers all add noise
 * to a "find the dominant color" pass. The logo, by contrast, is a
 * deliberate institutional surface — whatever color appears there is
 * the one the institution chose to represent itself.
 *
 * Why algorithmic instead of vision: the algorithm is deterministic
 * (same input → same output every run), explainable (we can point at
 * the cropped pixels and show the histogram), and cheap. Vision is
 * useful for edge-case adjudication but it's the wrong primary tool
 * for a sweep we want to re-run as colleges enter FEATURED.
 *
 * Inputs:
 *   public/brand-audit/captures.json — homepage URL + thumb path per id
 *   public/brand-audit/thumbs/*.png  — 1280×600 captures
 *
 * Outputs:
 *   public/brand-audit/logos/*.png   — 320×120 logo crops, for the audit UI
 *   public/brand-audit/analyzed.json — { id, hex_raw, hex_neon, source, confidence }
 */
import sharp from "sharp";
import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const ATLAS_ROOT = path.resolve(__dirname, "..");
const AUDIT_DIR = path.join(ATLAS_ROOT, "public", "brand-audit");
const THUMBS_DIR = path.join(AUDIT_DIR, "thumbs");
const LOGOS_DIR = path.join(AUDIT_DIR, "logos");

// Default fallback crop when no per-college bbox is provided.
// CCC homepages put the institutional mark in the top-left within the
// first ~280 × 100 px. A bit of generous padding (320 × 120) catches
// cases where there's a thin top accent strip with the logo below it.
//
// In practice we override this with vision-identified bboxes from
// `logo-bboxes.json`, which catches per-college logo placement
// (offsets, taglines below the wordmark, etc.) much better than a
// fixed crop. The default only kicks in when bbox data is missing.
const DEFAULT_LOGO_CROP = { left: 0, top: 0, width: 320, height: 120 };

// HSL filters for "non-neutral, non-extreme" pixels.
// Tuned permissively: many CCC logos are wordmarks where the brand color
// is dark-on-white (Foothill scarlet on white card, Reedley navy text
// with a slim accent strip). A strict 0.20 saturation / 0.07 lightness
// floor strips those pixels and the algorithm reports "no signal." We
// want to catch dark navy (#001f3f, L ≈ 0.12) and muted brand colors
// while still excluding actual neutrals.
const MIN_L = 0.04;
const MAX_L = 0.96;
const MIN_S = 0.10;

// HSL bucket sizes (smaller = finer).
const HUE_BUCKETS = 24;          // 15° per bucket
const SAT_BUCKETS = 5;
const LGT_BUCKETS = 5;

// ── Color math ──────────────────────────────────────────────────────────

function rgbToHsl(r, g, b) {
  r /= 255; g /= 255; b /= 255;
  const max = Math.max(r, g, b), min = Math.min(r, g, b);
  const l = (max + min) / 2;
  let h = 0, s = 0;
  if (max !== min) {
    const d = max - min;
    s = l > 0.5 ? d / (2 - max - min) : d / (max + min);
    switch (max) {
      case r: h = (g - b) / d + (g < b ? 6 : 0); break;
      case g: h = (b - r) / d + 2; break;
      case b: h = (r - g) / d + 4; break;
    }
    h /= 6;
  }
  return [h, s, l];
}

function hslToRgb(h, s, l) {
  if (s === 0) {
    const v = Math.round(l * 255);
    return [v, v, v];
  }
  const q = l < 0.5 ? l * (1 + s) : l + s - l * s;
  const p = 2 * l - q;
  const f = (t) => {
    if (t < 0) t += 1;
    if (t > 1) t -= 1;
    if (t < 1 / 6) return p + (q - p) * 6 * t;
    if (t < 1 / 2) return q;
    if (t < 2 / 3) return p + (q - p) * (2 / 3 - t) * 6;
    return p;
  };
  return [
    Math.round(f(h + 1 / 3) * 255),
    Math.round(f(h) * 255),
    Math.round(f(h - 1 / 3) * 255),
  ];
}

function rgbToHex([r, g, b]) {
  return "#" + [r, g, b].map((x) => x.toString(16).padStart(2, "0")).join("");
}

// Neon transform: lift the brand color so it reads cleanly on the navy
// Kallipolis background without losing its hue. Conservative — leaves
// already-saturated colors alone, only opens up muted/dark ones.
function neonTransform([r, g, b]) {
  let [h, s, l] = rgbToHsl(r, g, b);
  // Saturation: floor at 0.65 (boost muted colors only)
  if (s < 0.65) s = Math.min(0.65 + (0.65 - s) * 0.5, 0.85);
  // Lightness: clamp to [0.42, 0.62] band — readable on dark, not white-out
  if (l < 0.42) l = 0.42;
  else if (l > 0.62) l = 0.62;
  return hslToRgb(h, s, l);
}

// ── Dominant-color extraction ───────────────────────────────────────────

async function extractDominantFromCrop(thumbPath, logoPath, crop) {
  // Save the crop as an artifact for the audit UI, and load raw pixels.
  await sharp(thumbPath).extract(crop).png().toFile(logoPath);
  const { data, info } = await sharp(thumbPath)
    .extract(crop)
    .raw()
    .toBuffer({ resolveWithObject: true });

  const ch = info.channels;
  const buckets = new Map();
  let nonNeutralCount = 0;

  for (let i = 0; i < data.length; i += ch) {
    const r = data[i], g = data[i + 1], b = data[i + 2];
    const [h, s, l] = rgbToHsl(r, g, b);
    if (l < MIN_L || l > MAX_L) continue;
    if (s < MIN_S) continue;
    nonNeutralCount++;

    const hb = Math.min(HUE_BUCKETS - 1, Math.floor(h * HUE_BUCKETS));
    const sb = Math.min(SAT_BUCKETS - 1, Math.floor(s * SAT_BUCKETS));
    const lb = Math.min(LGT_BUCKETS - 1, Math.floor(l * LGT_BUCKETS));
    const key = `${hb}-${sb}-${lb}`;
    let entry = buckets.get(key);
    if (!entry) {
      entry = { count: 0, r: 0, g: 0, b: 0 };
      buckets.set(key, entry);
    }
    entry.count++;
    entry.r += r; entry.g += g; entry.b += b;
  }

  if (buckets.size === 0 || nonNeutralCount < 80) {
    // Logo crop is essentially a white/black/gray void — no brand signal.
    return { rgb: null, confidence: "low", source: "logo crop", note: `Only ${nonNeutralCount} non-neutral pixels found in logo crop.` };
  }

  // Top bucket by frequency. Tie-break by saturation×count.
  const sorted = [...buckets.values()].sort((a, b) => b.count - a.count);
  const top = sorted[0];
  const rgb = [
    Math.round(top.r / top.count),
    Math.round(top.g / top.count),
    Math.round(top.b / top.count),
  ];
  // Confidence: high if top bucket > 25% of all non-neutral pixels;
  // medium if 10-25%; low otherwise.
  const dominance = top.count / nonNeutralCount;
  const confidence = dominance > 0.25 ? "high" : dominance > 0.10 ? "medium" : "low";
  return {
    rgb,
    confidence,
    source: "logo crop dominant cluster",
    dominance: Math.round(dominance * 100) / 100,
    nonNeutralCount,
  };
}

// ── Main ────────────────────────────────────────────────────────────────

async function readBboxes() {
  // logo-bboxes.json is produced by the vision-pass agent. Format:
  //   { "entries": [ { "id", "bbox": {x, y, width, height}, "confidence", "note" }, ... ] }
  // Missing/null bbox falls back to DEFAULT_LOGO_CROP.
  const p = path.join(AUDIT_DIR, "logo-bboxes.json");
  try {
    const j = JSON.parse(await fs.readFile(p, "utf-8"));
    const map = new Map();
    for (const e of j.entries ?? []) {
      if (e.bbox && e.bbox.width > 0 && e.bbox.height > 0) {
        map.set(e.id, {
          left: Math.round(e.bbox.x),
          top: Math.round(e.bbox.y),
          width: Math.round(e.bbox.width),
          height: Math.round(e.bbox.height),
          confidence: e.confidence ?? null,
        });
      }
    }
    return map;
  } catch {
    return new Map();
  }
}

async function main() {
  await fs.mkdir(LOGOS_DIR, { recursive: true });
  const captures = JSON.parse(await fs.readFile(path.join(AUDIT_DIR, "captures.json"), "utf-8"));
  const bboxes = await readBboxes();

  console.log(`Extracting brand colors for ${captures.captures.length} colleges (${bboxes.size} bboxes loaded)...\n`);
  const entries = [];

  for (const cap of captures.captures) {
    if (cap.status !== "ok") {
      entries.push({
        id: cap.id,
        hex_raw: null,
        hex_neon: null,
        source: "no capture",
        confidence: "low",
        note: cap.error ?? "Capture missing.",
      });
      console.log(`  ✗ ${cap.id} — no capture (${cap.error ?? "?"})`);
      continue;
    }

    const thumbPath = path.join(THUMBS_DIR, `${cap.id}.png`);
    const logoPath = path.join(LOGOS_DIR, `${cap.id}.png`);

    const bbox = bboxes.get(cap.id);
    const crop = bbox
      ? { left: bbox.left, top: bbox.top, width: bbox.width, height: bbox.height }
      : DEFAULT_LOGO_CROP;
    const cropTag = bbox ? `bbox(${bbox.confidence ?? "?"})` : "default";

    try {
      const result = await extractDominantFromCrop(thumbPath, logoPath, crop);
      if (!result.rgb) {
        entries.push({
          id: cap.id,
          hex_raw: null,
          hex_neon: null,
          source: result.source,
          crop_source: cropTag,
          crop,
          confidence: "low",
          note: result.note,
        });
        console.log(`  ⚠ ${cap.id.padEnd(16)} no signal — ${result.note}`);
        continue;
      }
      const neonRgb = neonTransform(result.rgb);
      const hex_raw = rgbToHex(result.rgb);
      const hex_neon = rgbToHex(neonRgb);
      entries.push({
        id: cap.id,
        hex_raw,
        hex_neon,
        source: result.source,
        crop_source: cropTag,
        crop,
        confidence: result.confidence,
        dominance: result.dominance,
        non_neutral_pixels: result.nonNeutralCount,
      });
      console.log(`  ✓ ${cap.id.padEnd(16)} ${cropTag.padEnd(14)} raw=${hex_raw}  neon=${hex_neon}  dom=${(result.dominance * 100).toFixed(0)}%`);
    } catch (err) {
      entries.push({
        id: cap.id,
        hex_raw: null,
        hex_neon: null,
        source: "extraction error",
        confidence: "low",
        note: err instanceof Error ? err.message : String(err),
      });
      console.log(`  ✗ ${cap.id.padEnd(16)} ${err.message}`);
    }
  }

  await fs.writeFile(
    path.join(AUDIT_DIR, "analyzed.json"),
    JSON.stringify({
      method: "logo-crop-bucket-then-neon-transform",
      default_logo_crop: DEFAULT_LOGO_CROP,
      generated_at: new Date().toISOString(),
      entries,
    }, null, 2),
  );

  console.log(`\nWrote ${entries.length} entries → public/brand-audit/analyzed.json`);
}

main().catch((err) => { console.error(err); process.exit(1); });
