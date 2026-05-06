/**
 * Capture the top ~600 px of every featured college's homepage.
 *
 * Output:
 *   atlas/public/brand-audit/thumbs/{id}.png  — header screenshot per college
 *   atlas/public/brand-audit/captures.json    — index file consumed by the
 *                                                /brand-audit page and by the
 *                                                follow-up vision-analysis
 *                                                step that picks the actual
 *                                                brand hex per college.
 *
 * Why "top 600 px" rather than "the whole page": the brand surface is the
 * header band + logo + a sliver of hero context. 600 px is enough to catch
 * the band, the logo at full size, and any thin accent strip above it,
 * without dragging in editorial photography that would distract the
 * downstream vision analysis.
 *
 * Run from the atlas/ directory:  node scripts/extract-brand-headers.mjs
 */
import { chromium } from "playwright";
import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { HOMEPAGES } from "./college-homepages.mjs";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const ATLAS_ROOT = path.resolve(__dirname, "..");
const THUMBS_DIR = path.join(ATLAS_ROOT, "public", "brand-audit", "thumbs");
const INDEX_PATH = path.join(ATLAS_ROOT, "public", "brand-audit", "captures.json");

const VIEWPORT = { width: 1280, height: 900 };
const CAPTURE_HEIGHT = 600;
const NAV_TIMEOUT_MS = 30_000;

async function ensureDir(p) {
  await fs.mkdir(p, { recursive: true });
}

async function captureOne(browser, id, url) {
  const context = await browser.newContext({
    viewport: VIEWPORT,
    userAgent:
      "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36",
  });
  const page = await context.newPage();
  const out = { id, url, status: "ok", error: null, finalUrl: null };

  try {
    const resp = await page.goto(url, { waitUntil: "domcontentloaded", timeout: NAV_TIMEOUT_MS });
    out.finalUrl = page.url();
    if (!resp || resp.status() >= 400) {
      out.status = "http_error";
      out.error = `HTTP ${resp ? resp.status() : "no-response"}`;
    } else {
      // Give late-rendered headers a beat to settle (lazy CSS, font swaps).
      await page.waitForTimeout(800);
      const thumbPath = path.join(THUMBS_DIR, `${id}.png`);
      await page.screenshot({
        path: thumbPath,
        clip: { x: 0, y: 0, width: VIEWPORT.width, height: CAPTURE_HEIGHT },
      });
      out.thumb = `/brand-audit/thumbs/${id}.png`;
    }
  } catch (err) {
    out.status = "error";
    out.error = err instanceof Error ? err.message : String(err);
  } finally {
    await context.close();
  }

  return out;
}

async function main() {
  await ensureDir(THUMBS_DIR);
  const entries = Object.entries(HOMEPAGES);
  console.log(`Capturing ${entries.length} homepages...\n`);

  const browser = await chromium.launch({ headless: true });
  const captures = [];

  // Sequential to avoid hammering shared infrastructure (Los Rios, Peralta,
  // etc. host multiple colleges on overlapping CDNs) and to keep memory
  // bounded. Total wall time is ~30s for 31 sites.
  for (const [id, url] of entries) {
    const t0 = Date.now();
    const r = await captureOne(browser, id, url);
    const ms = Date.now() - t0;
    if (r.status === "ok") {
      console.log(`  ✓ ${id.padEnd(16)} ${ms}ms  ${url}`);
    } else {
      console.log(`  ✗ ${id.padEnd(16)} ${ms}ms  ${r.error}  (${url})`);
    }
    captures.push(r);
  }

  await browser.close();

  await fs.writeFile(INDEX_PATH, JSON.stringify({ generated_at: new Date().toISOString(), captures }, null, 2));

  const ok = captures.filter((c) => c.status === "ok").length;
  console.log(`\n${ok}/${captures.length} captured. Index → ${path.relative(ATLAS_ROOT, INDEX_PATH)}`);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
