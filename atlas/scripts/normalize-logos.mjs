/**
 * normalize-logos.mjs
 *
 * Reads raw college logos from /public, normalizes them to a consistent
 * format (144px height, white background, PNG), and outputs to /public/logos/.
 *
 * Run automatically via predev / prebuild npm hooks (after color extraction).
 */

import sharp from "sharp";
import { readFileSync, mkdirSync, existsSync } from "fs";
import { join, dirname } from "path";
import { fileURLToPath } from "url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const PUBLIC_DIR = join(__dirname, "../public");
const OUTPUT_DIR = join(PUBLIC_DIR, "logos");
const TARGET_HEIGHT = 144; // 2x retina (displayed at 72px)
const MAX_WIDTH = 480;
const PADDING = 8;

// Parse californiaColleges.ts to extract college entries with logos
function getCollegesWithLogos() {
  const src = readFileSync(
    join(__dirname, "../lib/californiaColleges.ts"),
    "utf8",
  );
  const entries = [];
  const re =
    /id:\s*"([^"]+)".*?logoStacked:\s*"([^"]+)"/g;
  let match;
  while ((match = re.exec(src)) !== null) {
    entries.push({ id: match[1], logoPath: match[2] });
  }
  return entries;
}

async function normalizeLogo(id, srcPath) {
  const fullPath = join(PUBLIC_DIR, srcPath);
  if (!existsSync(fullPath)) {
    console.warn(`  ⚠ Missing: ${srcPath}`);
    return false;
  }

  try {
    // Read and rasterize (SVGs get density-based rasterization)
    let img = sharp(fullPath, { density: 300 });
    const meta = await img.metadata();

    // Calculate target dimensions preserving aspect ratio
    const contentHeight = TARGET_HEIGHT - PADDING * 2;
    const scale = contentHeight / (meta.height || contentHeight);
    let contentWidth = Math.round((meta.width || contentHeight) * scale);

    // Cap width
    if (contentWidth > MAX_WIDTH - PADDING * 2) {
      contentWidth = MAX_WIDTH - PADDING * 2;
    }

    // Resize the logo content
    img = sharp(fullPath, { density: 300 }).resize(contentWidth, contentHeight, {
      fit: "inside",
      withoutEnlargement: false,
    });

    // Get the resized buffer
    const resizedBuf = await img.png().toBuffer();
    const resizedMeta = await sharp(resizedBuf).metadata();

    // Create white canvas and composite the logo centered
    const canvasWidth = (resizedMeta.width || contentWidth) + PADDING * 2;
    const canvasHeight = TARGET_HEIGHT;

    const output = await sharp({
      create: {
        width: canvasWidth,
        height: canvasHeight,
        channels: 4,
        background: { r: 255, g: 255, b: 255, alpha: 1 },
      },
    })
      .composite([
        {
          input: resizedBuf,
          gravity: "centre",
        },
      ])
      .png()
      .toBuffer();

    const outPath = join(OUTPUT_DIR, `${id}.png`);
    await sharp(output).toFile(outPath);
    return true;
  } catch (err) {
    console.warn(`  ⚠ Failed ${id}: ${err.message}`);
    return false;
  }
}

async function main() {
  // Ensure output directory exists
  mkdirSync(OUTPUT_DIR, { recursive: true });

  const colleges = getCollegesWithLogos();
  console.log(`Normalizing ${colleges.length} logos...`);

  let success = 0;
  let failed = 0;

  for (const { id, logoPath } of colleges) {
    const ok = await normalizeLogo(id, logoPath);
    if (ok) {
      success++;
      console.log(`  ${id}: ✓`);
    } else {
      failed++;
    }
  }

  console.log(
    `\nNormalized ${success} logos → public/logos/ (${failed} failed)`,
  );
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
