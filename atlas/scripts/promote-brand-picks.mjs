/**
 * promote-brand-picks.mjs — read public/brand-audit/picks.json and rewrite
 * the COLOR_OVERRIDES block in config/collegeAtlasConfigs.ts to include
 * each picked hex.
 *
 * Behavior:
 *   - Existing entries already in COLOR_OVERRIDES that are also in picks
 *     get UPDATED to the picked hex (existing comment retained).
 *   - Entries in picks but not in COLOR_OVERRIDES get APPENDED, sorted
 *     by region (matched against californiaColleges.ts).
 *   - Existing overrides not in picks are preserved as-is.
 *   - Picks with hex === existing collegeColors.generated value get
 *     SKIPPED (no override needed; the auto-generated default already
 *     matches).
 *
 * Run from atlas/:  node scripts/promote-brand-picks.mjs
 */
import { promises as fs } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ATLAS_ROOT = path.resolve(__dirname, "..");

const PICKS_PATH = path.join(ATLAS_ROOT, "public", "brand-audit", "picks.json");
const CONFIG_PATH = path.join(ATLAS_ROOT, "config", "collegeAtlasConfigs.ts");
const GENERATED_PATH = path.join(ATLAS_ROOT, "config", "collegeColors.generated.ts");
const COLLEGES_PATH = path.join(ATLAS_ROOT, "state-atlas", "californiaColleges.ts");

const REGION_LABEL = {
  "north-far-north": "North / Far North",
  "bay-area": "Bay Area",
  "central-valley-mother-lode": "Central Valley / Mother Lode",
  "south-central-coast": "South Central Coast",
  "los-angeles": "Los Angeles",
  "orange-county": "Orange County",
  "inland-empire-desert": "Inland Empire / Desert",
  "san-diego-imperial": "San Diego / Imperial",
};
const REGION_ORDER = Object.keys(REGION_LABEL);

async function main() {
  const picks = JSON.parse(await fs.readFile(PICKS_PATH, "utf-8"));
  const generated = await fs.readFile(GENERATED_PATH, "utf-8");
  const colleges = await fs.readFile(COLLEGES_PATH, "utf-8");
  let cfg = await fs.readFile(CONFIG_PATH, "utf-8");

  // Parse existing generated map
  const genMap = {};
  for (const m of generated.matchAll(/"(\w+)":\s*"(#[0-9a-fA-F]+)"/g)) {
    genMap[m[1]] = m[2].toLowerCase();
  }

  // Parse collegeId → name + regionId
  const sliced = colleges.slice(colleges.indexOf("CALIFORNIA_COLLEGES"));
  const meta = {};
  for (const m of sliced.matchAll(/\{\s*id:\s*"(\w+)"[^}]*name:\s*"([^"]+)"[^}]*regionId:\s*"([^"]+)"/g)) {
    meta[m[1]] = { name: m[2], regionId: m[3] };
  }

  // Parse existing COLOR_OVERRIDES
  const ovMatch = cfg.match(/(const COLOR_OVERRIDES: Record<string, string> = \{)([\s\S]*?)(\n\};)/);
  if (!ovMatch) throw new Error("COLOR_OVERRIDES block not found");
  const overrideLines = ovMatch[2];
  // Build existing-by-id (preserve original lines for comment retention)
  const existingMap = new Map();
  for (const m of overrideLines.matchAll(/^(\s+)(\w+):\s*"(#[0-9a-fA-F]+)",(\s*\/\/.*)?$/gm)) {
    existingMap.set(m[2], { indent: m[1], hex: m[3], comment: m[4] ?? "" });
  }

  // Determine final per-id state: pick overrides existing if pick differs from generated
  // and is meaningful; existing overrides not in picks are kept.
  const finalById = new Map();
  for (const [id, info] of existingMap) {
    finalById.set(id, { hex: info.hex, comment: info.comment, kept: true });
  }
  const promoted = [];
  const skipped = [];
  for (const [id, p] of Object.entries(picks.picks ?? {})) {
    const hex = p.hex.toLowerCase();
    const gen = genMap[id];
    if (gen === hex) {
      skipped.push({ id, reason: "matches generated default" });
      continue;
    }
    const prev = existingMap.get(id);
    if (prev && prev.hex.toLowerCase() === hex) {
      skipped.push({ id, reason: "already overridden to same value" });
      continue;
    }
    const note = `// picked ${p.source} ${new Date(p.updated_at).toISOString().slice(0, 10)}`;
    finalById.set(id, {
      hex,
      comment: prev ? `   ${prev.comment.trim()} ${note}`.replace(/^\s*\/\/\s*\/\//, "//") : `  ${note}`,
      kept: false,
    });
    promoted.push({ id, hex, prev: prev?.hex ?? null });
  }

  // Group by region for output, fall back to "(unsorted)" if id not in meta
  const byRegion = Object.fromEntries(REGION_ORDER.map((r) => [r, []]));
  byRegion["(unsorted)"] = [];
  for (const [id, info] of finalById) {
    const m = meta[id];
    const region = (m && byRegion[m.regionId]) ? m.regionId : "(unsorted)";
    byRegion[region].push({ id, ...info });
  }

  // Sort within each region by id
  for (const region of Object.keys(byRegion)) {
    byRegion[region].sort((a, b) => a.id.localeCompare(b.id));
  }

  // Compute padding per region
  const lines = [];
  for (const region of [...REGION_ORDER, "(unsorted)"]) {
    const entries = byRegion[region];
    if (!entries.length) continue;
    const label = region === "(unsorted)" ? "Other / unsorted" : REGION_LABEL[region];
    lines.push(`  // ${label}`);
    const pad = Math.max(...entries.map((e) => e.id.length));
    for (const e of entries) {
      const c = (e.comment ?? "").trim();
      const commentPart = c ? `   ${c.startsWith("//") ? c : "// " + c}` : "";
      lines.push(`  ${(e.id + ":").padEnd(pad + 2)}"${e.hex}",${commentPart}`);
    }
    lines.push("");
  }
  while (lines.length && lines[lines.length - 1] === "") lines.pop();

  const newBody = "\n" + lines.join("\n") + "\n";
  cfg = cfg.replace(ovMatch[0], `${ovMatch[1]}${newBody}${ovMatch[3]}`);
  await fs.writeFile(CONFIG_PATH, cfg, "utf-8");

  console.log(`Promoted ${promoted.length} picks into COLOR_OVERRIDES.`);
  for (const p of promoted) console.log(`  + ${p.id}  ${p.prev ?? "(new)"} → ${p.hex}`);
  if (skipped.length) {
    console.log(`\nSkipped ${skipped.length}:`);
    for (const s of skipped) console.log(`  · ${s.id}  (${s.reason})`);
  }
  console.log(`\nTotal entries in COLOR_OVERRIDES now: ${finalById.size}`);
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
